from fastapi import APIRouter, Depends, HTTPException
from schemas.orders_DTO import Order_Body_POST
from auth_check import api_key_header
from httpx_helper import httpx_helper
import httpx
from config import settings

router = APIRouter(prefix=settings.api.v1.prefix)


@router.post("/order")
async def create_order(
    order_info: Order_Body_POST,
    requester_info: tuple[str, str] = Depends(api_key_header),
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter)
):
    if order_info.ticker == "RUB":
        raise HTTPException(status_code=409, detail="You cannot make orders RUB-RUB")
    req_id, role = requester_info
    order_info.user_id = req_id
    try:
        response = await client.post(
            f"{settings.urls.orders}/v1/order",
            json=order_info.model_dump(mode="json"),
            timeout=5.0
        )
        response.raise_for_status()
        print(response)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис Ордеров временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return response.json()