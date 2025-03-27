from typing import List
from fastapi import (APIRouter, Depends,)
from core.database import db_helper
from .schemas import (UserBase, NewUser,)
from sqlalchemy.ext.asyncio import AsyncSession
from .service import (get_all_users, create_user, api_key_header, get_user,)


router = APIRouter()


@router.get("/", response_model=List[UserBase])
async def get_users(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    users = await get_all_users(session)
    return users


@router.post("/register", response_model=UserBase)
async def register_user(
    data: NewUser,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    user = await create_user(session=session, data=data)
    return user


@router.get("/profile", response_model=UserBase)
async def get_curent_user(
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    """
        send the secret key
        e.g {"authorization":" TOKEN secret_key"}
    """
    user = await get_user(session, authorization)
    return user

    