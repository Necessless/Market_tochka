from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from .schemas import Order_Body_POST, Create_Order_Response
from core.models import Order
from core.schemas.Responses import Ok
from user_service.app.api.auth import api_key_header
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from .dependencies import get_user
import uuid
from .dependencies import serialize_orders
from .service import (
    service_create_market_order,
    service_create_limit_order,
    service_retrieve_order,
    service_cancel_order
)


router = APIRouter(tags=["order"])


@router.get("/")
async def get_list_of_orders(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Order).order_by(Order.timestamp)
    result = await session.scalars(query)
    orders = result.all()
    serialized_orders = serialize_orders(orders)
    return serialized_orders


@router.post("/", response_model=Create_Order_Response)
async def create_order(
    data: Order_Body_POST,
    user_name: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    async with session.begin():
        user = await get_user(session, user_name)
        if not data.price:
            order = await service_create_market_order(data, user, session)
        else:
            order = await service_create_limit_order(data, user, session)
    if not order:
        raise HTTPException(status_code=422, detail="Cant create Order")
    return Create_Order_Response(
        order_id=order.id
    )


@router.get("/{order_id}")
async def retrieve_order(
    order_id: uuid.UUID,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    order = await service_retrieve_order(order_id=order_id, session=session)
    serialized_order = serialize_orders([order])[0]
    return serialized_order


@router.delete("/{order_id}", response_model=Ok)
async def cancel_order(
    order_id: uuid.UUID,
    user_name: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    result = await service_cancel_order(user_name=user_name, order_id=order_id, session=session)
    await session.commit()
    return result
    

@router.get("/orderbook/{ticker}", response_model=OrderBook)
async def get_orderbook(
    ticker: str, 
    limit: int = Query(default=10),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    orderbook = await service_get_orderbook(ticker=ticker, limit=limit, session=session)
    return orderbook