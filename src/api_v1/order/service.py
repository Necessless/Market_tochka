from .schemas import Order_Body
from core.models import User, Order
from core.models.orders import Order_Type, OrderStatus
from sqlalchemy.ext.asyncio import AsyncSession
from api_v1.admin.dependencies import get_instrument_by_ticker
from .dependencies import find_order_for_transaction
from fastapi import HTTPException

async def service_create_order(
        data: Order_Body,   
        user: User,
        session: AsyncSession
):
    instrument = await get_instrument_by_ticker(data.ticker, session)
    if data.price:
        order_type = Order_Type.LIMIT
    else:
        order_type = Order_Type.MARKET
    order = Order(
        user_id=user.id,
        direction=data.direction, 
        instrument_ticker=instrument.ticker, 
        quantity=data.qty, 
        price=data.price, 
        order_type=order_type
        )
    orders_for_transaction = await find_order_for_transaction(order, session)
    if order.order_type == Order_Type.MARKET and not orders_for_transaction:
        order.status = OrderStatus.CANCELLED
        session.add(order)
        await session.commit()
        raise HTTPException(status_code=422, detail="No any limit orders. Market order declined")
    session.add(order)
    transaction = await make_transaction(order, orders_for_transaction, session)
    return transaction