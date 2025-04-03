from typing import List, Sequence
from sqlalchemy import select
from core.models import Order
from core.models.orders import Direction, OrderStatus
from sqlalchemy.ext.asyncio import AsyncSession


async def find_order_for_transaction(
        order: Order,
        session: AsyncSession
) -> Sequence[Order]:
    if order.direction == Direction.SELL:
        query = select(Order).where(
            Order.instrument_ticker == order.instrument_ticker,
            Order.direction == Direction.BUY,
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
            Order.user_id != order.user_id,
            Order.price > 0,
            Order.filled == 0,
            Order.quantity > 0,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]),
            ).order_by(Order.price.asc())
    orders = await session.scalars(query)
    return orders.all()
    

async def make_transaction(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession
):
    quantity = order.quantity
    while quantity != 0:
        #TO DO ДОПИСАТЬ АЛГОРИТМ ПРОДАЖИ\ПОКУПКИ ЧАСТИЧНОЙ ИЛИ ПОЛНОЙ