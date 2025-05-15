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
    except httpx.HTTPStatusError as e:
        raise HTTPException(e)
    return response.json()


@router.post("/admin/instrument", tags=['admin'])
async def create_instrument(
    data: Instrument_Base,
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter),
    requester_info: tuple[str, str] = Depends(api_key_header)
):
    user_id, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа")
    try:
        response = await client.post(
            f"{settings.urls.balances}/v1/admin/instrument", 
            json=data.model_dump(),
            timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(e)
    return response.json()

@router.delete("/admin/instrument/{ticker}", tags=['admin'])
async def delete_instrument(
    ticker: str,
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter),
    requester_info: tuple[str, str] = Depends(api_key_header)
):
    req_id, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа")
    try:
        response = await client.delete(
            f"{settings.urls.balances}/v1/admin/instrument/{ticker}",
            timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(e)
    return response.json()

@router.get("/balance", tags=['balance'])
async def get_balance(
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter),
    requester_info: tuple[str, str] = Depends(api_key_header)
):
    req_id, role = requester_info
    try:
        response = await client.get(
            f"{settings.urls.balances}/v1/balance/{req_id}",
            timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(e)
    return response.json()