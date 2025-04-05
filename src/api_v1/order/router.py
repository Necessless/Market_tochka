from fastapi import APIRouter, Depends
from .schemas import Order_Body, Create_Order_Response
from api_v1.Public.auth import api_key_header
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from api_v1.Public.service import get_user
from api_v1.Public.dependencies import get_balance_for_user_by_ticker
from .service import service_create_market_order, service_create_limit_order


router = APIRouter(tags=["order"])


@router.post("/",)
async def create_order(
    data: Order_Body,
    user_name: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    user = await get_user(session, user_name)
    if not data.price:
        order = await service_create_market_order(data, user, session)
    else:
        order = await service_create_limit_order(data, user, session)
    return order
