from fastapi import APIRouter, HTTPException, Depends
import httpx
from auth_check import api_key_header
from config import settings
from schemas.instruments_DTO import Instrument_Base
from httpx_helper import httpx_helper

router = APIRouter(prefix=settings.api.v1.prefix)

@router.get("/public/instrument", tags=['public'])
async def list_instruments(client: httpx.AsyncClient = Depends(httpx_helper.client_getter)):
    try:
        response = await client.get(f"{settings.urls.balances}/v1/public/instrument", timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен")
    return response.json()

@router.post("/public/instrument", tags=['public'])
async def create_instrument(
    data: Instrument_Base,
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter),
    requester_info: tuple[str, str] = Depends(api_key_header)
):
    user_name, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа")
    try:
        response = await client.post(
            f"{settings.urls.balances}/v1/public/instrument", 
            json=data.model_dump(),
            timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен")
    return response.json()