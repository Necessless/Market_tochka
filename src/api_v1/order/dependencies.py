from typing import List, Optional, Sequence
from fastapi import HTTPException
from sqlalchemy import select
from core.models import Order, Transaction
from core.models.orders import Direction, OrderStatus, Order_Type
from sqlalchemy.ext.asyncio import AsyncSession


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


async def make_market_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession
) -> None:
    quantity = order.quantity
    i = 0
    while quantity != 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        if curr_order.quantity > quantity:
            curr_order.quantity -= quantity
            quantity = 0
            curr_order.status = OrderStatus.PARTIALLY_EXECUTED
            await create_transaction(
                instrument_ticker=order.instrument_ticker,
                amount=order.quantity,
                price=curr_order.price,
                session=session
            )
        elif curr_order.quantity == quantity:
            curr_order.quantity = 0 
            quantity = 0
            await create_transaction(
                instrument_ticker=order.instrument_ticker,
                amount=order.quantity,
                price=curr_order.price,
                session=session
            )
        else:
            quantity -= curr_order.quantity
            await create_transaction(
                instrument_ticker=order.instrument_ticker,
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