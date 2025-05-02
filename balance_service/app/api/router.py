from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import db_helper
from uuid import UUID
from user_service.app.api.auth import api_key_header
from .dependencies import get_user
from core.schemas.Users_DTO import UserRegister
from core.schemas.Instruments_DTO import Instrument_Base
from core.schemas.Responses import Ok
from ..schemas.balance_DTO import Deposit_Withdraw_Instrument_V1
from .service import (
    service_delete_user,
    create_instrument,
    service_delete_instrument,
    service_balance_deposit,
    service_balance_withdraw,
)

router = APIRouter(tags=["admin"])





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


@router.get("/instrument", response_model=Sequence[Instrument_Base])
async def get_all_instruments(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Instrument).order_by(Instrument.ticker)
    result = await session.scalars(query)
    return result.all()


@router.get("/transactions/{ticker}")
async def get_transactions_history(
    ticker: str,
    limit: int = Query(default=10),
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Transaction).filter(Transaction.instrument_ticker == ticker).limit(limit)
    result = await session.scalars(query)
    return result.all()
    