from fastapi import APIRouter, HTTPException
import httpx
from schemas.users_DTO import NewUser, UserRegister
from config import settings

router = APIRouter(tags=["public"])

@router.post("/register")
async def register_user(data: NewUser):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.urls.users}/register",
                json=data.dict(),
                timeout=5.0
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Сервис Пользователей недоступен")

    return response.json()