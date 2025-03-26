from typing import List
from fastapi import (APIRouter, Depends,)
from core.config import settings
from core.database import db_helper
from .schemas import UserGet
from sqlalchemy.ext.asyncio import AsyncSession
from .service import get_all_users

router = APIRouter()


@router.get("/", response_model=List[UserGet])
async def get_users(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    users = await get_all_users(session)
    return users
    