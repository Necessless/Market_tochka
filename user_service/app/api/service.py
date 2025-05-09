from fastapi import HTTPException
from sqlalchemy import select
import uuid
from typing import Sequence
from models import User
from .schemas import NewUser
from sqlalchemy.ext.asyncio import AsyncSession 
from .auth import (
    create_token
)
from .schemas import UserBase, UserRegister


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
        role=user.role.value,
        api_key=token
    )


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    query = select(User).order_by(User.id)
    result = await session.scalars(query)
    return result.all()


async def service_delete_user(
        user_id: uuid.UUID,
        session: AsyncSession
) -> UserRegister:
    statement = select(User).filter(User.id == user_id)
    user_to_delete = await session.scalar(statement)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User with this id not found")
    to_encrypt = {"name": user_to_delete.name}
    token = create_token(to_encrypt)
    await session.delete(user_to_delete)
    await session.commit()
    return UserRegister(
        id=user_to_delete.id,
        role=user_to_delete.role,
        name=user_to_delete.name,
        api_key=token
    )