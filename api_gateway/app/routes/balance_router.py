from fastapi import APIRouter, HTTPException
import httpx
from config import settings

router = APIRouter(prefix=settings.api.v1.prefix)

@router.get("/public/instrument", tags=['public'])
async def list_instruments():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.urls.balances}/v1/public/instrument", timeout=5.0)
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")
        return response.json()