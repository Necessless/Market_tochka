from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.Users import User
from api_v1.Public.schemas import UserBase
from .schemas import Instrument_Base, Ok, Deposit_Instrument_V1
from core.models import Instrument, Balance
from .dependencies import get_user_by_id, get_instrument_by_ticker


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
) -> Instrument_Base:
    instrument = Instrument(name=name, ticker=ticker)
    session.add(instrument)
    await session.commit()
    return Instrument_Base(
        name=instrument.name,
        ticker=instrument.ticker
    )


async def service_delete_instrument(
        ticker: str,
        session: AsyncSession
) -> Ok:
    result = await get_instrument_by_ticker(ticker=ticker, session=session)
    await session.delete(result)
    await session.commit()
    return Ok()


async def service_balance_deposit(
        data: Deposit_Instrument_V1,
        session: AsyncSession
) -> Ok:
    user = await get_user_by_id(data.user_id, session)
    instrument = await get_instrument_by_ticker(ticker=data.ticker, session=session)
    statement = (
        insert(Balance)
        .values(user_name=user.name, instrument_ticker=instrument.ticker, quantity=data.amount)
        .on_conflict_do_update(index_elements=["user_name", "instrument_ticker"], set_={"quantity": Balance.quantity + data.amount})
    )
    await session.execute(statement)
    await session.commit()
    return Ok()
