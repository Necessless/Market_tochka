from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Balance


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