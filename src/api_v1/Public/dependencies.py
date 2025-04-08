from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Balance
from .schemas import Balance_one_instrument


async def get_balance_for_user_by_ticker(
        user_name: str,
        ticker: str,
        session: AsyncSession
) -> Balance | None:
    query = (
        select(Balance)
        .filter(Balance.user_name == user_name, Balance.instrument_ticker == ticker)
    )
    result = await session.execute(query)
    balance = result.scalar()
    return balance
