from sqlalchemy import select
from .schemas import Order_Body_POST
from core.models import User, Order
import uuid
from core.models.orders import Order_Type, OrderStatus
from sqlalchemy.ext.asyncio import AsyncSession
from api_v1.admin.dependencies import get_instrument_by_ticker
from .dependencies import (
    validate_and_return_limit_balance, 
    validate_and_return_market_balance,
    find_orders_for_market_transaction, 
    make_market_transactions, 
    find_orders_for_limit_transaction,
    make_limit_transactions,
    reserve_sum_on_balance,
    serialize_orders,
)
from fastapi import HTTPException


async def service_create_market_order(
        data: Order_Body_POST,   
        user: User,
        session: AsyncSession
) -> Order:
    instrument = await get_instrument_by_ticker(data.ticker, session) #проверяем существование инструмента
    balance = await validate_and_return_market_balance(data, user, session) #получаем или создаем баланс 
    order = Order(
        user_id=user.id,
        direction=data.direction, 
        instrument_ticker=instrument.ticker, 
        quantity=data.qty, 
        price=data.price, 
        order_type=Order_Type.MARKET
        )
    try:
        async with session.begin_nested():
            orders_for_transaction = await find_orders_for_market_transaction(order, session)
            if not orders_for_transaction or (sum(order.quantity for order in orders_for_transaction) < order.quantity):
                raise HTTPException(status_code=422, detail="Not enough limit orders for this amount. Market order declined")
            await make_market_transactions(order, orders_for_transaction, session, balance, user)
            order.status = OrderStatus.EXECUTED
            session.add(order)
    except HTTPException as e:
        order.status = OrderStatus.CANCELLED
        session.add(order)
        raise e
    return order


async def service_create_limit_order(
        data: Order_Body_POST,   
        user: User,
        session: AsyncSession
) -> Order:
    balance = await validate_and_return_limit_balance(data, user, session)
    instrument = await get_instrument_by_ticker(data.ticker, session)
    order = Order(
        user_id=user.id,
        direction=data.direction, 
        instrument_ticker=instrument.ticker, 
        quantity=data.qty, 
        price=data.price, 
        order_type=Order_Type.LIMIT
        )
    async with session.begin_nested():
        balance = await reserve_sum_on_balance(order=order, session=session, balance=balance)
        orders_for_transaction = await find_orders_for_limit_transaction(order, session)
        if orders_for_transaction:
            await make_limit_transactions(order, orders_for_transaction, session, balance, user)
        else:
            session.add(order)
    return order


async def service_retrieve_order(
        order_id: uuid.UUID,
        session: AsyncSession
):
    query = select(Order).filter(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="order with this id not found")
    serialized_order = serialize_orders([order])[0]
    return serialized_order