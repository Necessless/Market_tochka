from typing import Sequence
from fastapi import (APIRouter, Depends,)
from database import db_helper
import uuid
from .schemas import NewUser
from .schemas import UserBase, UserRegister
from sqlalchemy.ext.asyncio import AsyncSession
from .service import get_all_users, create_user, get_user, service_delete_user
from config import settings


router = APIRouter(tags=["public"], prefix=settings.api.v1.prefix)


@router.get("/", response_model=Sequence[UserBase])
async def get_users(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    users = await get_all_users(session)
    return users


@router.post("/public/register", response_model=UserRegister)
async def register_user(
    data: NewUser,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    user = await create_user(session=session, data=data)
    return user


@router.get("/profile", response_model=UserBase)
async def get_current_user(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    """
        send the secret key
        e.g {"authorization":" TOKEN secret_key"}
    """
    user = await get_user(session=session, name=user_name)
    return user


@router.delete("/admin/user/{user_id}", tags=["user"], response_model=UserRegister)
async def delete_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(db_helper.session_getter),
    ):
    res = await service_delete_user(user_id, session)
    return res





    