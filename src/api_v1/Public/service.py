from fastapi import HTTPException, Header
from sqlalchemy import select
from typing import Sequence
from core.models import User
from .schemas import UserCreate, UserGet
from sqlalchemy.ext.asyncio import AsyncSession 
from .auth import (
    generate_api_key,
    hash_api_key,
)


async def get_user(
        session: AsyncSession,
        token: str
) -> UserGet:
    hashed_token = hash_api_key(token)
    statement = select(User).where(User.api_key==hashed_token)
    user = await session.scalar(statement)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="User with this Api key is not exists"
            )
    return UserGet(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=user.api_key
    )


async def create_user(
        session: AsyncSession,
        data: UserCreate
) -> UserGet:
    public_key = generate_api_key()
    private_key = hash_api_key(public_key)
    user = User(name=data.name, role=data.role, api_key=private_key)
    session.add(user)
    await session.commit()
    return UserGet(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=public_key
    )

def api_key_header(authorization: str = Header(...)):
    if not authorization.startswith("TOKEN "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    return token

async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    statement = select(User).order_by(User.id)
    result = await session.scalars(statement)
    return result.all()