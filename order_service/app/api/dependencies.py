from typing import List, Sequence
from fastapi import HTTPException
from sqlalchemy import select
from core.schemas.Users_DTO import UserBase
from core.models import Order, Transaction, User, Balance, Instrument
from order_service.models.orders import Direction, OrderStatus, Order_Type
from user_service.models.Users import AuthRole
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Market_Order_Body_GET, Market_Order_GET, Limit_Order_Body_GET, Limit_Order_GET, Order_Body_POST










    






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

