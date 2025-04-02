from sqlalchemy import select
import uuid
from api_v1.Public.schemas import UserBase
from fastapi import HTTPException, Header
from core.models.Users import AuthRole, User
from core.models import Instrument
from sqlalchemy.ext.asyncio import AsyncSession


def is_admin_user(user: UserBase) -> bool:
    if user.role != AuthRole.ADMIN:
        raise HTTPException(status_code=405, detail="Method is not allowed")
    return True


async def get_user_by_id(
    user_id: uuid.UUID,
    session: AsyncSession
) -> User:
    query = select(User).filter(User.id == user_id)
    user = await session.scalar(query)
    if not user:
        raise HTTPException(status_code=404, detail="Cant find user with this user_id")
    return user


async def get_instrument_by_ticker(
    ticker: str,
    session: AsyncSession
) -> Instrument:
    query = select(Instrument).filter(Instrument.ticker == ticker)
    instrument = await session.scalar(query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Cant find instrument with this ticker")
    return instrument

