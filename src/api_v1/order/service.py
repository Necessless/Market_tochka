from .schemas import Order_Body
from core.models import User, Order
from core.models.orders import Order_Type, OrderStatus, Direction
from sqlalchemy.ext.asyncio import AsyncSession
from api_v1.admin.dependencies import get_instrument_by_ticker
from .dependencies import find_orders_for_market_transaction, make_market_transactions, find_orders_for_limit_transaction, make_limit_transactions
from fastapi import HTTPException
from api_v1.Public.dependencies import get_balance_for_user_by_ticker


async def validate_balance(
        data: Order_Body,
        user: User,
        session: AsyncSession
) -> None:
    if data.direction == Direction.SELL:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
        if balance.available < data.qty:
            raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to buy")
    else:
        balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
        if balance.available < data.qty:
            raise HTTPException(status_code=400, detail="Insufficient funds(RUB) on balance to buy")
    return 
    

async def service_create_market_order(
        data: Order_Body,   
        user: User,
        session: AsyncSession
) -> Order:
    await validate_balance(data, user, session)
    instrument = await get_instrument_by_ticker(data.ticker, session) #проверяем существование инструмента
    order = Order(
        user_id=user.id,
        direction=data.direction, 
        instrument_ticker=instrument.ticker, 
        quantity=data.qty, 
        price=data.price, 
        order_type=Order_Type.MARKET
        )
    orders_for_transaction = await find_orders_for_market_transaction(order, session)
    print("AAAAAAAAAAAAAAAAAAAAAAAAAA")
    print(orders_for_transaction)
    if not orders_for_transaction or (sum(order.quantity for order in orders_for_transaction) < order.quantity):
        order.status = OrderStatus.CANCELLED
        session.add(order)
        await session.commit()
        raise HTTPException(status_code=422, detail="Not enough limit orders for this amount. Market order declined")
    await make_market_transactions(order, orders_for_transaction, session)
    order.status = OrderStatus.EXECUTED
    session.add(order)
    await session.commit()
    return order


async def service_create_limit_order(
        data: Order_Body,   
        user: User,
        session: AsyncSession
) -> Order:
    await validate_balance(data, user, session)
    instrument = await get_instrument_by_ticker(data.ticker, session)
    order = Order(
        user_id=user.id,
        direction=data.direction, 
        instrument_ticker=instrument.ticker, 
        quantity=data.qty, 
        price=data.price, 
        order_type=Order_Type.LIMIT
        )
    orders_for_transaction = await find_orders_for_limit_transaction(order, session)
    if orders_for_transaction:
        await make_limit_transactions(order, orders_for_transaction, session)
        await session.commit()
    else:
        session.add(order)
        await session.commit()
    return order