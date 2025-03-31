from fastapi import HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Sequence
from core.models import User, Balance, Instrument
from .schemas import UserBase, NewUser, UserRegister
from sqlalchemy.ext.asyncio import AsyncSession 
from .auth import (
    create_token
)


async def get_user(
        session: AsyncSession,
        name: str,
) -> UserBase:
    
    query = select(User).where(User.name == name)
    user = await session.scalar(query)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Wrong Authentication token"
            )
    return UserBase(
        id=user.id,
        name=user.name,
        role=user.role,
    )


async def create_user(
        session: AsyncSession,
        data: NewUser
) -> UserRegister:
    
    to_encrypt = {"name": data.name}
    token = create_token(to_encrypt)
    user = User(name=data.name, role=data.role)
    session.add(user)
    await session.commit()
    return UserRegister(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=token
    )


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    query = select(User).order_by(User.id)
    result = await session.scalars(query)
    return result.all()


async def get_balance_for_user(
        session: AsyncSession,
        token: str
) -> Sequence[User]:
    #ДОПИСАТЬ
    user = await get_user(session, token)
    query = select(User).options(selectinload(User.instruments))
    result = await session.scalars(query)
    if not result:
        raise HTTPException(status_code=404, detail="Wallet for this user is not exists")
    return result.all()
