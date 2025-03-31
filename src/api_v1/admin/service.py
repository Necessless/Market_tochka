from sqlalchemy import select
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.Users import User
from api_v1.Public.schemas import UserBase
from .schemas import Instrument as instrument_schema, Ok
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
) -> instrument_schema:
    instrument = Instrument(name=name, ticker=ticker)
    session.add(instrument)
    await session.commit()
    return instrument_schema(
        name=instrument.name,
        ticker=instrument.ticker
    )


async def service_delete_instrument(
        ticker: str,
        session: AsyncSession
) -> Ok:
    query = select(Instrument).filter(Instrument.ticker == ticker)
    result = await session.scalar(query)
    if result:
        await session.delete(result)
        await session.commit()
        return Ok()
    raise HTTPException(status_code=404, detail="instrument with this ticker is not found")