from sqlalchemy import  select
from fastapi import APIRouter, Depends
from .schemas import Order_Body_POST
from core.models import Order
from api_v1.Public.auth import api_key_header
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from api_v1.Public.service import get_user
from .dependencies import serialize_orders
from .service import service_create_market_order, service_create_limit_order


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



@router.post("/")
async def create_order(
    data: Order_Body_POST,
    user_name: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    user = await get_user(session, user_name)
    if not data.price:
        order = await service_create_market_order(data, user, session)
    else:
        order = await service_create_limit_order(data, user, session)
    return order
