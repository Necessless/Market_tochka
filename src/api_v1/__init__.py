from fastapi import APIRouter
from core.config import settings
from .Public.router import router as public_router

router = APIRouter(prefix=settings.api.v1.prefix)
router.include_router(public_router, prefix=settings.api.v1.public)
@router.get("/")
async def test():
    return {"message": "router is working"}