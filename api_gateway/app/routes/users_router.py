from fastapi import APIRouter, Depends, HTTPException
import httpx
from schemas.users_DTO import NewUser
from config import settings
import uuid
from auth_check import api_key_header

router = APIRouter()

@router.post("/public/register", tags=['public'])
async def register_user(data: NewUser):
    async with httpx.AsyncClient() as client:
        try:
            user = {"name": data.name, "role":data.role.value}
            response = await client.post(
                f"{settings.urls.users}/register",
                json=user,
                timeout=5.0
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")

    return response.json()


@router.delete("/admin/user/{user_id}", tags=['user', 'admin'])
async def delete_user(
    user_id: uuid.UUID,
    requester_info: tuple[str, str] = Depends(api_key_header)
    ):
    user_name, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Method allowed only for admin users")
    async with httpx.AsyncClient() as client:
        try:
            log = {"requester": user_name, "requester_role": role, "userid_to_delete": user_id}
            print(log)
            response = await client.delete(
                f"{settings.urls.users}/admin/user/{user_id}",
                timeout=5.0
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")
    return response.json()
