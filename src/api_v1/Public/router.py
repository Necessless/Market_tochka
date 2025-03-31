from typing import List
from fastapi import (APIRouter, Depends,)
from sqlalchemy import select
from core.database import db_helper
from core.models import Instrument
from .schemas import (UserBase, NewUser,)
from api_v1.admin.schemas import Instrument as instrument_get
from sqlalchemy.ext.asyncio import AsyncSession
from .service import (get_all_users, create_user, get_user,)
from .dependencies import api_key_header


router = APIRouter(tags=["public"])


@router.get("/", response_model=List[UserBase])
async def get_users(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    users = await get_all_users(session)
    return users


@router.post("/register", response_model=UserBase)
async def register_user(
    data: NewUser,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    user = await create_user(session=session, data=data)
    return user


@router.get("/profile", response_model=UserBase)
async def get_current_user(
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    """
        send the secret key
        e.g {"authorization":" TOKEN secret_key"}
    """
    user = await get_user(session, authorization)
    return user


@router.get("/instrument", response_model=List[instrument_get])
async def get_all_instruments(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> instrument_get:
    query = select(Instrument).order_by(Instrument.ticker)
    result = await session.scalars(query)
    return result.all()