from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import db_helper
from uuid import UUID
from .dependencies import is_admin_user
from api_v1.Public.auth import api_key_header
from api_v1.Public.service import get_user
from api_v1.Public.schemas import UserBase
from .schemas import Instrument_Base, Ok, Deposit_Withdraw_Instrument_V1
from .service import (
    service_delete_user,
    create_instrument,
    service_delete_instrument,
    service_balance_deposit,
    service_balance_withdraw,
)

router = APIRouter(tags=["admin"])


@router.delete("/user/{user_id}", tags=["user"], response_model=UserBase)
async def delete_user(
    user_id: UUID,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        res = await service_delete_user(user_id, session)
        return res


@router.post("/instrument", response_model=Instrument_Base)
async def post_instrument(
    data: Instrument_Base,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        instrument = await create_instrument(data.name, data.ticker, session)
        return instrument


@router.delete("/instrument/{ticker}", response_model=Ok)
async def delete_instrument(
    ticker: str,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        result = await service_delete_instrument(ticker, session)
        return result


@router.post("/balance/deposit", tags=["balance"], response_model=Ok)
async def balance_deposit(
    data: Deposit_Withdraw_Instrument_V1,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> Ok:
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        result = await service_balance_deposit(data, session)
        return result
    raise HTTPException(status_code=405, detail="method not allowed")


@router.post("/balance/withdraw", tags=["balance"], response_model=Ok)
async def balance_withdraw(
    data: Deposit_Withdraw_Instrument_V1,
    authorization: str = Depends(api_key_header),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> Ok:
    curr_user = await get_user(session, authorization)
    if is_admin_user(curr_user):
        result = await service_balance_withdraw(data, session)
        return result
    raise HTTPException(status_code=405, detail="method not allowed")
