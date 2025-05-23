from fastapi import APIRouter, Depends, HTTPException
import httpx
from httpx_helper import httpx_helper
from schemas.users_DTO import NewUser
from config import settings
import uuid
from producers.user_delete_producer import publish_message
from auth_check import api_key_header
from fastapi import Request
router = APIRouter(prefix=settings.api.v1.prefix)

@router.post("/public/register", tags=['public'])
async def register_user(request: Request, client: httpx.AsyncClient = Depends(httpx_helper.client_getter)):
    raw_data = await request.json()
    print("RAW DATA:", raw_data)  # или логируй
    # try:
    #     # register_response = await client.post(
    #     #     f"{settings.urls.users}/v1/public/register",
    #     #     json=data.model_dump(mode="json"),
    #     #     timeout=5.0
    #     # )
    #     # register_response.raise_for_status()
    #     # user_data = register_response.json()
    #     # user_id = user_data['id']
    #     # if user_id is None:
    #     #     raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")
    #     # balance_response = await client.post(
    #     #     f"{settings.urls.balances}/v1/admin/balance/init",
    #     #     params={"user_id": user_id},
    #     #     timeout=5.0
    #     # )
    #     # balance_response.raise_for_status()
    # except httpx.RequestError:
    #     raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")
    # except httpx.HTTPStatusError as e:
    #     raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    # return user_data


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
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис Пользователей временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    await publish_message(user_id)
    return response.json()
