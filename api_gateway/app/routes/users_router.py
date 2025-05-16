from fastapi import APIRouter, Depends, HTTPException
import httpx
from httpx_helper import httpx_helper
from schemas.users_DTO import NewUser
from config import settings
import uuid
from auth_check import api_key_header

router = APIRouter(prefix=settings.api.v1.prefix)

@router.post("/public/register", tags=['public'])
async def register_user(data: NewUser, client: httpx.AsyncClient = Depends(httpx_helper.client_getter)):
    try:
        response = await client.post(
            f"{settings.urls.users}/v1/public/register",
            json=data.model_dump(mode="json"),
            timeout=5.0
        )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")
    return response.json()


@router.delete("/admin/user/{user_id}", tags=['user', 'admin'])
async def delete_user(
    user_id: uuid.UUID,
    requester_info: tuple[str, str] = Depends(api_key_header),
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter)
):
    req_id, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа")
    try:
        log = {"requester_id": req_id, "requester_role": role, "userid_to_delete": user_id}
        print(log)
        response = await client.delete(
            f"{settings.urls.users}/v1/admin/user/{user_id}",
            timeout=5.0
        )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")
    return response.json()
