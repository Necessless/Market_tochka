from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Balance


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
    balance = result.scalar_one_or_none()
    return balance


