from typing import List, Sequence
from fastapi import HTTPException, Depends
from database import db_helper
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Market_Order_Body_GET, Market_Order_GET, Limit_Order_Body_GET, Limit_Order_GET, Order_Body_POST
from models import Order
from models.orders import Direction, Order_Type, OrderStatus

async def find_orders_for_market_transaction(
        order: Order,
        session: AsyncSession
) -> Sequence[Order]:
    if order.direction == Direction.SELL:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.BUY,
            Order.order_type == Order_Type.LIMIT,
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
            Order.price > 0,
            Order.filled == 0,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.asc())
    orders = await session.scalars(query)
    return orders.all()


async def find_orders_for_limit_transaction(
        order: Order,
        session: AsyncSession 
) -> Sequence[Order]:
    if order.direction == Direction.SELL:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.BUY,
            Order.order_type == Order_Type.LIMIT,
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
            Order.price <= order.price,
            Order.filled == 0,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.asc())
    orders = await session.scalars(query)
    return orders.all()


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
    