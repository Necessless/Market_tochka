from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from uuid import UUID
from .dependencies import is_admin_user
from api_v1.Public.dependencies import api_key_header
from api_v1.Public.service import get_user
from api_v1.Public.schemas import UserBase
from .schemas import Instrument, Ok
from .service import (
    service_delete_user,
    create_instrument, 
    service_delete_instrument, 
    )

router = APIRouter(tags=["admin"])

@router.delete("/user/{user_id}", response_model=UserBase)
async def delete_user(
    user_id: UUID,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        res = await service_delete_user(user_id, session)
        return res


@router.post("/instrument", response_model=Instrument)
async def post_instrument(
    data: Instrument,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        instrument = await create_instrument(data.name, data.ticker, session)
        return instrument


@router.delete("/instrument/{ticker}", response_model=Ok)
async def delete_instrument(
    ticker: str,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        instrument = await service_delete_instrument(ticker, session)
        return instrument
