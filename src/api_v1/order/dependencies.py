from typing import List, Sequence
from fastapi import HTTPException
from sqlalchemy import select
from api_v1.Public.dependencies import get_balance_for_user_by_ticker
from core.models import Order, Transaction, User, Balance
from core.models.orders import Direction, OrderStatus, Order_Type
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Market_Order_Body_GET, Market_Order_GET, Limit_Order_Body_GET, Limit_Order_GET, Order_Body_POST


async def validate_limit_balance(
        data: Order_Body_POST,
        user: User,
        session: AsyncSession
) -> None:
    if data.direction == Direction.SELL:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        if balance.available < data.qty:
            raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to sell")
    else:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
        if balance.available < (data.qty * data.price):
            raise HTTPException(status_code=400, detail="Insufficient funds(RUB) on balance to buy")
    return 


async def validate_and_return_market_balance(
        data: Order_Body_POST,
        user: User,
        session: AsyncSession
) -> Balance:
    if data.direction == Direction.SELL:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        if balance is None or balance.available < data.qty:
            raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to sell")
    else:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        print(balance)
        if not balance:
            balance = Balance(
                user_name=user.name,
                instrument_ticker=data.ticker,
                available=0
            )
        print(balance)
        session.add(balance)
    return balance


async def add_remove_market_balance(
        balance_instr: Balance,
        balance_rub: Balance,
        direction: Direction,
        amount: int,
        price: int,
        session: AsyncSession
) -> None:
    if direction == Direction.SELL:
        balance_instr.available -= amount
        balance_rub.available += (amount * price)
    else:
        balance_instr.available += amount
        balance_rub.available -= (amount * price)
    session.add(balance_instr)
    session.add(balance_rub)
    return 


async def reserve_sum_on_balance(
        user: User, 
        order: Order,
        session: AsyncSession
) -> Balance:
    if order.direction == Direction.SELL:
        query = select(Balance).filter(Balance.instrument_ticker == order.instrument_ticker, Balance.user_name == user.name)
        balance = await session.scalar(query)
        balance.reserved += order.quantity
        session.add(balance)
    else:
        query = select(Balance).filter(Balance.instrument_ticker == "RUB", Balance.user_name == user.name)
        balance = await session.scalar(query)
        balance.reserved += (order.quantity * order.price)
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
        await session.rollback()
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
        amount: int, 
        order: Order,
        session: AsyncSession
) -> None:
    if balance < (amount * price):
        order.status = OrderStatus.CANCELLED
        session.add(order)
        await session.commit()
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
        order.status = OrderStatus.CANCELLED
        session.add(order)
        await session.commit()
        raise HTTPException(status_code=400, detail="No any rubbles on balance")
    i = 0
    while quantity != 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        if curr_order.quantity > quantity:
            if order.direction == Direction.BUY:
                await check_balance_for_market_buy(balance_rub.available, curr_order.price, quantity, order, session)
            curr_order.quantity -= quantity
            quantity = 0
            curr_order.status = OrderStatus.PARTIALLY_EXECUTED
            await create_transaction(
                instrument_ticker=order.instrument_ticker,
                amount=order.quantity,
                price=curr_order.price,
                session=session
            )
            await add_remove_market_balance(
                balance_instr=balance_instr,
                balance_rub=balance_rub,
                direction=order.direction,
                amount=order.quantity,
                price=curr_order.price,
                session=session
            )
        elif curr_order.quantity == quantity:
            if order.direction == Direction.BUY:
                await check_balance_for_market_buy(balance_rub.available, curr_order.price, quantity, order, session)
            curr_order.quantity = 0 
            quantity = 0
            await create_transaction(
                instrument_ticker=order.instrument_ticker,
                amount=order.quantity,
                price=curr_order.price,
                session=session
            )
            await add_remove_market_balance(
                balance_instr=balance_instr,
                balance_rub=balance_rub,
                direction=order.direction,
                amount=order.quantity,
                price=curr_order.price,
                session=session
            )
        else:
            if order.direction == Direction.BUY:
                await check_balance_for_market_buy(balance_rub.available, curr_order.price, curr_order.price, order, session)
            quantity -= curr_order.quantity
            await create_transaction(
                instrument_ticker=order.instrument_ticker,
                amount=curr_order.quantity,
                price=curr_order.price,
                session=session
            )
            await add_remove_market_balance(
                balance_instr=balance_instr,
                balance_rub=balance_rub,
                direction=order.direction,
                amount=curr_order.quantity,
                price=curr_order.price,
                session=session
            )
            curr_order.quantity = 0

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
    quantity = order.quantity
    i = 0 
    while quantity > 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        if curr_order.quantity < quantity:
            quantity -= curr_order.quantity
            await create_transaction(
                instrument_ticker=order.instrument_ticker, 
                amount=curr_order.quantity,
                price=curr_order.price,
                session=session
            )
            await add_remove_balance(
                balance_instr=balance_instr,
                direction=order.direction,
                user_name=user.name,
                amount=curr_order.quantity,
                price=curr_order.price,
                session=session
            )
            order.status = OrderStatus.PARTIALLY_EXECUTED
            curr_order.quantity = 0
        elif curr_order.quantity >= quantity:
            curr_order.quantity -= quantity
            await create_transaction(
                instrument_ticker=order.instrument_ticker, 
                amount=quantity,
                price=curr_order.price,
                session=session
            )
            await add_remove_balance(
                balance_instr=balance_instr,
                direction=order.direction,
                user_name=user.name,
                amount=quantity,
                price=curr_order.price,
                session=session
            )
            quantity = 0 
            order.status = OrderStatus.EXECUTED
            order.filled = 1

        if curr_order.quantity == 0:
            curr_order.status = OrderStatus.EXECUTED
            curr_order.filled = 1
        elif quantity == 0 and curr_order.quantity > 0:
            curr_order.status = OrderStatus.PARTIALLY_EXECUTED
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
    
