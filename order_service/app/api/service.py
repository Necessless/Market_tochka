from sqlalchemy import select
from .schemas import Order_Body_POST, Ok
from core.models import User, Order
import uuid
from order_service.models.orders import Order_Type, OrderStatus
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import (
    validate_and_return_limit_balance, 
    validate_and_return_market_balance,
    find_orders_for_market_transaction, 
    make_market_transactions, 
    find_orders_for_limit_transaction,
    make_limit_transactions,
    reserve_sum_on_balance,
    validate_user_for_order_cancel,
    add_remove_balance,
    get_balance_for_user_by_ticker,
    get_instrument_by_ticker,
    get_user,
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
) -> Order:
    query = select(Order).filter(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="order with this id not found")
    return order


async def service_cancel_order(
    user_name: str,
    order_id: uuid.UUID,
    session: AsyncSession
) -> Ok:
    user = await get_user(session=session, name=user_name)
    order = await service_retrieve_order(order_id=order_id, session=session)
    validate_user_for_order_cancel(user, order)
    balance_instr = await get_balance_for_user_by_ticker(user_name=user_name, ticker=order.instrument_ticker, session=session)
    balance_rub = await get_balance_for_user_by_ticker(user_name=user_name, ticker="RUB", session=session)
    order.status = OrderStatus.CANCELLED
    session.add(order)
    await add_remove_balance(
        balance_instr=balance_instr,
        balance_rub=balance_rub,
        order=order,
        amount=order.quantity,
        price=order.price,
        session=session
    )
    return Ok()


async def service_get_orderbook(
        ticker: str,
        limit: int,
        session: AsyncSession
) -> OrderBook:
    query_ask = (
        select(func.sum(Order.quantity), Order.price)
        .filter(
            Order.instrument_ticker == ticker,
            Order.direction == Direction.BUY,
            Order.order_type == Order_Type.LIMIT,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED])
        )
        .group_by(Order.price)
        .order_by(Order.price.desc())
        .limit(limit)
    )
    query_bid = (
        select(func.sum(Order.quantity), Order.price)
        .filter(
            Order.instrument_ticker == ticker,
            Order.direction == Direction.SELL,
            Order.order_type == Order_Type.LIMIT,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED])
        )
        .group_by(Order.price)
        .order_by(Order.price.asc())
        .limit(limit)
    )
    res_ask = await session.execute(query_ask)
    res_bid = await session.execute(query_bid)

    res_ask = res_ask.all()
    res_bid = res_bid.all()
    
    res_ask = [L2OrderBook(price=price, qty=qty) for qty, price in res_ask]
    res_bid = [L2OrderBook(price=price, qty=qty) for qty, price in res_bid]

    return OrderBook(
        bid_levels=res_bid,
        ask_levels=res_ask
    )