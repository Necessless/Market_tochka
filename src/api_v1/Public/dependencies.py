from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Balance
from .schemas import Balance_one_instrument


async def get_balance_for_user_by_ticker(
        user_name: str,
        ticker: str,
        session: AsyncSession
) -> Balance_one_instrument:
    query = (
        select(Balance.available, Balance.reserved)
        .filter(Balance.user_name == user_name, Balance.instrument_ticker == ticker)
    )
    result = await session.execute(query)
    if not result: 
        return Balance_one_instrument(
            available=0,
            reserved=0
        )
    return Balance_one_instrument(
        available=result[0],
        reserved=result[1]
    )
