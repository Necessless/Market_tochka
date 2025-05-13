from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from database import db_helper
from config import settings
from typing import Sequence
from models import Transaction, Balance, Instrument
from schemas.balance_DTO import Instrument_Base, Deposit_Withdraw_Instrument_V1
from schemas.responses import Ok 
from .service import (
    get_instrument_by_ticker,
)

router = APIRouter(tags=["admin"], prefix=settings.api.v1.prefix)


@router.post("/public/instrument", response_model=Instrument_Base)
async def add_instrument(
    data: Instrument_Base,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    instrument = Instrument(name=data.name, ticker=data.ticker)
    session.add(instrument)
    await session.commit()
    return Instrument_Base(
        name=instrument.name,
        ticker=instrument.ticker
    )
    


@router.delete("/instrument/{ticker}", response_model=Ok)
async def delete_instrument(
    ticker: str,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    result = await get_instrument_by_ticker(ticker=ticker, session=session)
    await session.delete(result)
    await session.commit()
    return Ok()



@router.post("/balance/deposit", tags=["balance"], response_model=Ok)
async def balance_deposit(
    data: Deposit_Withdraw_Instrument_V1,
    session: AsyncSession = Depends(db_helper.session_getter),
) -> Ok:
    # user = await get_user_by_id(data.user_id, session)
    instrument = await get_instrument_by_ticker(ticker=data.ticker, session=session)
    statement = (
        insert(Balance)
        .values(user_name=user.name, instrument_ticker=instrument.ticker, _available=data.amount)
        .on_conflict_do_update(index_elements=["user_name", "instrument_ticker"], set_={"available": Balance._available + data.amount})
    )
    await session.execute(statement)
    await session.commit()
    return Ok()
 

@router.post("/balance/withdraw", tags=["balance"], response_model=Ok)
async def balance_withdraw(
    data: Deposit_Withdraw_Instrument_V1,
    session: AsyncSession = Depends(db_helper.session_getter),
) -> Ok:
    # user = await get_user_by_id(data.user_id, session)
    query = select(Balance).filter(Balance.user_name == user.name, Balance.instrument_ticker == data.ticker)
    balance = await session.scalar(query)
    if not balance:
        raise HTTPException(status_code=404, detail="Instrument with this ticker is not found in user's wallet")
    new_quantity = balance.available - data.amount
    if new_quantity == 0 and balance.reserved == 0:
        await session.delete(balance)
    elif new_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    else:
        balance.available = new_quantity
        session.add(balance)
    await session.commit()
    return Ok()



@router.get("/public/instrument", response_model=Sequence[Instrument_Base])
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
    