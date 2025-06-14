from fastapi import APIRouter, HTTPException, Depends, Query
import httpx
from auth_check import api_key_header
from config import settings
from schemas.instruments_DTO import Instrument_Base
from schemas.balance_DTO import Deposit_Withdraw_Instrument_V1
from httpx_helper import httpx_helper
from producers.base_producer import instrument_producer

router = APIRouter(prefix=settings.api.v1.prefix)

@router.get("/public/instrument", tags=['public'])
async def list_instruments(client: httpx.AsyncClient = Depends(httpx_helper.client_getter)):
    try:
        response = await client.get(f"{settings.urls.balances}/v1/public/instrument", timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
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
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
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
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", "Ошибка в сервисе")
        except Exception:
            detail = "Ошибка в сервисе"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    try:
        await instrument_producer.publish_message_instrument(ticker)
    except Exception:
        print("Ошибка при публикации сообщения об удалении инструмента")
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
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return response.json()


@router.post("/admin/balance/deposit", tags=['balance', 'admin'])
async def deposit_to_balance(
    deposit_info: Deposit_Withdraw_Instrument_V1,
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter),
    requester_info: tuple[str, str] = Depends(api_key_header)
):
    req_id, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа")
    user_id = deposit_info.user_id
    try:
        is_user = await client.get(
        f"{settings.urls.users}/v1/user/{user_id}",
        timeout=5.0)
        print("SADAD")
        is_user.raise_for_status()
        response = await client.post(
            f"{settings.urls.balances}/v1/admin/balance/deposit",
            json=deposit_info.model_dump(mode="json"),
            timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return response.json()


@router.post("/admin/balance/withdraw", tags=['balance', 'admin'])
async def withdraw_from_balance(
    withdraw_info: Deposit_Withdraw_Instrument_V1,
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter),
    requester_info: tuple[str, str] = Depends(api_key_header)
):
    req_id, role = requester_info
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа")
    try:
        response = await client.post(
            f"{settings.urls.balances}/v1/admin/balance/withdraw",
            json=withdraw_info.model_dump(mode="json"),
            timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис баланса временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return response.json()

@router.get("/public/transactions/{ticker}", tags=['public'])
async def get_transactions_for_ticker(ticker: str, limit: int = Query(default=10), client: httpx.AsyncClient = Depends(httpx_helper.client_getter)):
    try:
        data = {"limit": limit}
        response = await client.get(url=f"{settings.urls.balances}/v1/public/transactions/{ticker}", params=data, timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис Ордеров временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return response.json()