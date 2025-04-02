from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from .Public.schemas import Balance_Public
from .Public.service import get_balance_for_user
from core.config import settings
from .Public.auth import api_key_header
from .Public.router import router as public_router
from .admin.router import router as admin_router
from typing import Dict


router = APIRouter(prefix=settings.api.v1.prefix)
router.include_router(public_router, prefix=settings.api.public)
router.include_router(admin_router, prefix=settings.api.admin)


@router.get("/")
async def test():
    return {"message": "router api_V1 is working"}

@router.get("/balance", tags=["balance"])
async def get_balance(
    user_name: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter)
) -> Dict[str, int]:
    wallet = await get_balance_for_user(session, user_name)
    return wallet