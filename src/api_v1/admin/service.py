from sqlalchemy import select
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.Users import User
from api_v1.Public.schemas import UserBase
from .schemas import Instrument_GET_POST
from core.models import Instrument


async def service_delete_user(
        user_id: UUID,
        session: AsyncSession
) -> UserBase:
    statement = select(User).filter(User.id == user_id)
    user_to_delete = await session.scalar(statement)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User with this id not found")
    await session.delete(user_to_delete)
    await session.commit()
    return UserBase(
        id=user_to_delete.id,
        role=user_to_delete.role,
        name=user_to_delete.name,
        api_key=user_to_delete.api_key
    )


async def create_instrument(
        name: str,
        ticker: str,
        session: AsyncSession
) -> Instrument_GET_POST:
    instrument = Instrument(name=name, ticker=ticker)
    session.add(instrument)
    await session.commit()
    return Instrument_GET_POST(
        name=instrument.name,
        ticker=instrument.ticker
    )
