from typing import List, Sequence
from fastapi import HTTPException
from sqlalchemy import select
from core.schemas.Users_DTO import UserBase
from core.models import Order, Transaction, User, Balance, Instrument
from core.models.orders import Direction, OrderStatus, Order_Type
from core.models.Users import AuthRole
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Market_Order_Body_GET, Market_Order_GET, Limit_Order_Body_GET, Limit_Order_GET, Order_Body_POST

async def get_balance_for_user_by_ticker(
        user_name: str,
        ticker: str,
        session: AsyncSession
) -> Balance | None:
    query = (
        select(Balance)
        .filter(Balance.user_name == user_name, Balance.instrument_ticker == ticker)
    )
    result = await session.execute(query)
    balance = result.scalar_one_or_none()
    return balance


async def get_instrument_by_ticker(
    ticker: str,
    session: AsyncSession
) -> Instrument:
    query = select(Instrument).filter(Instrument.ticker == ticker)
    instrument = await session.scalar(query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Cant find instrument with this ticker")
    return instrument


async def validate_and_return_limit_balance(
        data: Order_Body_POST,
        user: User,
        session: AsyncSession
) -> Balance:
    if data.ticker == "RUB":
        raise HTTPException(status_code=400, detail="Cant sell or buy Rubbles")
    if data.direction == Direction.SELL:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        if balance is None or balance.available < data.qty:
            raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to sell")
    else:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
        if not balance:
            balance = Balance(
                user_name=user.name,
                instrument_ticker="RUB",
                available=0
            )
            session.add(balance)
        elif balance.available < (data.qty * data.price):
            raise HTTPException(status_code=400, detail="Insufficient funds(RUB) on balance to buy")
    return balance


async def validate_and_return_market_balance(
        data: Order_Body_POST,
        user: User,
        session: AsyncSession
) -> Balance:
    if data.ticker == "RUB":
        raise HTTPException(status_code=400, detail="Cant sell or buy Rubbles")
    if data.direction == Direction.SELL:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        if balance is None or balance.available < data.qty:
            raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to sell")
    else:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        if not balance:
            balance = Balance(
                user_name=user.name,
                instrument_ticker=data.ticker,
                available=0
            )
        session.add(balance)
    return balance


async def add_remove_balance(
        balance_instr: Balance,
        balance_rub: Balance,
        order: Order,
        amount: int,
        price: int,
        session: AsyncSession
) -> None:
    direction = order.direction,
    order_type = order.order_type
    if order.status == OrderStatus.CANCELLED: #если пользователь отменил ордер, и требуется вернуть средства
        if direction == Direction.SELL:
            balance_instr.remove_reserved(amount)
        else:
            balance_rub.remove_reserved(amount*price)
        session.add_all([balance_instr, balance_rub])
        return 
    if direction == Direction.SELL: 
        if order_type == Order_Type.LIMIT:
            balance_instr.reserved -= amount
        else:
            balance_instr.available -= amount
        balance_rub.available += (amount * price)
    else:
        if order_type == Order_Type.LIMIT:
            balance_rub.reserved -= (amount * price)
        else:
            balance_rub.available -= (amount * price)
        balance_instr.available += amount
    session.add_all([balance_instr, balance_rub])
    

async def reserve_sum_on_balance(
        order: Order,
        session: AsyncSession,
        balance: Balance
) -> Balance:
    try:
        if order.direction == Direction.SELL:
            balance.add_reserved(order.quantity)
        else:
            balance.add_reserved(order.quantity * order.price)
    except ValueError:
        raise HTTPException(status_code=400, detail="Not enough available funds on balance, check orders, rest of user's money is reserved")
    session.add(balance)
    return balance


async def create_transaction(
        instrument_ticker: str,
        amount: int,
        price: int,
        session: AsyncSession
) -> None:
    transaction = Transaction(
        instrument_ticker=instrument_ticker, 
        amount=amount,
        price=price,
    )
    if transaction:
        session.add(transaction)
    else:
        raise HTTPException(status_code=400, detail="Cannot create transaction with this ticker, price and amount")


async def find_orders_for_market_transaction(
        order: Order,
        session: AsyncSession
) -> Sequence[Order]:
    if order.direction == Direction.SELL:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.BUY,
            Order.order_type == Order_Type.LIMIT,
            Order.user_id != order.user_id,
            Order.filled == 0,
            Order.price > 0,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.desc())
    else:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.SELL,
            Order.order_type == Order_Type.LIMIT,
            Order.user_id != order.user_id,
            Order.price > 0,
            Order.filled == 0,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.asc())
    orders = await session.scalars(query)
    return orders.all()


async def check_balance_for_market_buy(
        balance: int,
        price: int,
        amount: int
) -> None:
    if balance < (amount * price):
        raise HTTPException(status_code=400, detail="Insufficient funds(RUB) on balance to make buy transaction")
    return 


async def make_market_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession,
        balance_instr: Balance,
        user: User
) -> None: 
    quantity = order.quantity
    balance_rub = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
    if not balance_rub:
        raise HTTPException(status_code=400, detail="No any rubbles on balance")
    i = 0
    while quantity != 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        amount_to_order = min(quantity, curr_order.quantity)
        if order.direction == Direction.BUY:
            await check_balance_for_market_buy(balance_rub.available, curr_order.price, amount_to_order)
        await create_transaction(
            instrument_ticker=order.instrument_ticker,
            amount=amount_to_order,
            price=curr_order.price,
            session=session
        )
        await add_remove_balance(
            balance_instr=balance_instr,
            balance_rub=balance_rub,
            order=order,
            amount=amount_to_order,
            price=curr_order.price,
            session=session
        )
        quantity -= amount_to_order
        curr_order.quantity -= amount_to_order
        curr_order.status = OrderStatus.PARTIALLY_EXECUTED
        if curr_order.quantity == 0:
            curr_order.filled = 1
            curr_order.status = OrderStatus.EXECUTED
        i += 1
        session.add(curr_order)


async def find_orders_for_limit_transaction(
        order: Order,
        session: AsyncSession
) -> Sequence[Order]:
    if order.direction == Direction.SELL:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.BUY,
            Order.order_type == Order_Type.LIMIT,
            Order.user_id != order.user_id,
            Order.filled == 0,
            Order.price >= order.price,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.desc())
    else:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.SELL,
            Order.order_type == Order_Type.LIMIT,
            Order.user_id != order.user_id,
            Order.price <= order.price,
            Order.filled == 0,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.asc())
    orders = await session.scalars(query)
    return orders.all()


async def make_limit_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession,
        balance_instr: Balance,
        user: User
) -> None:
    balance_rub = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
    if not balance_rub:
        raise HTTPException(status_code=400, detail="No any rubbles on balance")
    quantity = order.quantity
    i = 0 
    while quantity > 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        amount_to_transact = min(curr_order.quantity, quantity)
        await create_transaction(
            instrument_ticker=order.instrument_ticker, 
            amount=amount_to_transact,
            price=curr_order.price,
            session=session
        )
        await add_remove_balance(
            balance_instr=balance_instr,
            balance_rub=balance_rub,
            order=order,
            amount=amount_to_transact,
            price=curr_order.price,
            session=session
        )
        quantity -= amount_to_transact
        curr_order.quantity -= amount_to_transact
        order.status = OrderStatus.PARTIALLY_EXECUTED
        curr_order.status = OrderStatus.PARTIALLY_EXECUTED
        if curr_order.quantity == 0:
            curr_order.status = OrderStatus.EXECUTED
            curr_order.filled = 1
        if quantity == 0:
            order.status = OrderStatus.EXECUTED
            order.filled = 1
        session.add(curr_order)
        i += 1
    session.add(order)


def serialize_orders(
        orders: List[Order]
) -> Sequence[Order]:
    result = []
    for order in orders:
        if order.order_type == Order_Type.LIMIT:
            temp = Limit_Order_GET(
                id=order.id,
                status=order.status,
                user_id=order.user_id,
                timestamp=order.timestamp,
                body=Limit_Order_Body_GET(
                    direction=order.direction,
                    ticker=order.instrument_ticker,
                    qty=order.quantity,
                    price=order.price,
                ),
                filled=order.filled
            )
        else:
            temp = Market_Order_GET(
                id=order.id,
                status=order.status,
                user_id=order.user_id,
                timestamp=order.timestamp,
                body=Market_Order_Body_GET(
                    direction=order.direction,
                    ticker=order.instrument_ticker,
                    qty=order.quantity
                )
            )
        result.append(temp)
    return result
    

def validate_user_for_order_cancel(
        user: User,
        order: Order
) -> None:
    if order.user_id != user.id and user.role != AuthRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only owner or admin can cancel order")
    if order.status in [OrderStatus.CANCELLED, OrderStatus.EXECUTED]:
        raise HTTPException(status_code=400, detail=f"Order is already {order.status.value}")
    if order.order_type == Order_Type.MARKET:
        raise HTTPException(status_code=400, detail="Market order cant be cancelled")


async def get_user(
        session: AsyncSession,
        name: str,
) -> UserBase:
    query = select(User).where(User.name == name)
    user = await session.scalar(query)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Wrong Authentication token"
            )
    return UserBase(
        id=user.id,
        name=user.name,
        role=user.role,
    )