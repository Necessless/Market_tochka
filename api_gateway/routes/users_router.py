from fastapi import APIRouter, HTTPException
import httpx
from schemas.users_DTO import NewUser, UserRegister


router = APIRouter(tags=["public"])

@router.post("/register", response_model=UserRegister)
async def register_user(data: NewUser):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.USERS_SERVICE_URL}/internal/register",
                json=data.dict(),
                timeout=5.0
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Сервис Пользователей недоступен")

    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()