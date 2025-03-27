from fastapi import APIRouter
from core.config import settings
from .Public.router import router as public_router
from .admin.router import router as admin_router

router = APIRouter(prefix=settings.api.v1.prefix)
router.include_router(public_router, prefix=settings.api.public)
router.include_router(admin_router, prefix=settings.api.admin)


@router.get("/")
async def test():
    return {"message": "router api_V1 is working"}