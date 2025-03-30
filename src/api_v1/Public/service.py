from fastapi import HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Sequence
from core.models import User, Balance, Instrument
from .schemas import UserBase, NewUser, Instrument_Balance
from sqlalchemy.ext.asyncio import AsyncSession 
from .auth import (
    generate_api_key,
    hash_api_key,
)


async def get_user(
        session: AsyncSession,
        token: str
) -> UserBase:
    hashed_token = hash_api_key(token)
    statement = select(User).where(User.api_key==hashed_token)
    user = await session.scalar(statement)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Wrong Authentication token"
            )
    return UserBase(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=user.api_key
    )


async def create_user(
        session: AsyncSession,
        data: NewUser
) -> UserBase:
    public_key = generate_api_key()
    private_key = hash_api_key(public_key)
    user = User(name=data.name, role=data.role, api_key=private_key)
    session.add(user)
    await session.commit()
    return UserBase(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=public_key
    )


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    statement = select(User).order_by(User.id)
    result = await session.scalars(statement)
    return result.all()


async def get_balance_for_user(
        session: AsyncSession,
        token: str
) -> Sequence[User]:
    #ДОПИСАТЬ
    user = await get_user(session, token)
    statement = select(User).options(selectinload(User.instruments))
    result = await session.scalars(statement)
    if not result:
        raise HTTPException(status_code=404, detail="Wallet for this user is not exists")
    return result.all()
