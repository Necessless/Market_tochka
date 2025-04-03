from fastapi import APIRouter, Depends
from .schemas import Order_Body, Create_Order_Response
from api_v1.Public.auth import api_key_header
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from api_v1.Public.service import get_user
from .service import service_create_order

router = APIRouter(tags=["order"])


@router.post("/",)
async def create_order(
    data: Order_Body,
    user_name: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    user = await get_user(session, user_name)
    order = await service_create_order(data, user, session)
    return order
