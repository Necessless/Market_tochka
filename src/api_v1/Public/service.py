from sqlalchemy import select
from typing import Sequence
from core.models import User
from sqlalchemy.ext.asyncio import AsyncSession 


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    statement = select(User).order_by(User.id)
    result = await session.scalars(statement)
    return result.all()