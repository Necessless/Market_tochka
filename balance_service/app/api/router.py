import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from database import db_helper
from config import settings
from typing import Sequence
from models import Transaction, Balance, Instrument
from schemas.balance_DTO import Instrument_Base, Deposit_Withdraw_Instrument_V1, Validate_Balance, Transaction_Post
from schemas.responses import Ok 
from .service import (
    get_instrument_by_ticker,
    get_balance_for_user
)
from sqlalchemy import exc

router = APIRouter(tags=["admin"], prefix=settings.api.v1.prefix)


@router.post("/admin/instrument")
async def add_instrument(
    data: Instrument_Base,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    async with session.begin():
        try:
            instrument = Instrument(name=data.name, ticker=data.ticker)
            session.add(instrument)
        except exc.IntegrityError:
            raise HTTPException(status_code=409, detail="This ticker already exists")
    return Instrument_Base(
        name=instrument.name,
        ticker=instrument.ticker
    )

@router.post("/admin/check-instrument")
async def check_instrument_existance(
    ticker: str,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    print(ticker)
    query = select(Instrument).filter(Instrument.ticker == ticker)
    result = await session.scalar(query)
    print(result)
    if not result:
        raise HTTPException(status_code=404, detail="This ticker is not exists")
    


@router.delete("/admin/instrument/{ticker}", response_model=Ok)
async def delete_instrument(
    ticker: str,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    result = await get_instrument_by_ticker(ticker=ticker, session=session)
    await session.delete(result)
    await session.commit()
    return Ok()

@router.get("/balance/{user_id}")
async def get_balance(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    result = await get_balance_for_user(session=session, id=user_id)
    return result

@router.get("/balance_ticker/{user_id}/{ticker}")
async def get_balance_by_ticker(
    user_id: uuid.UUID,
    ticker: str,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    query = select(Balance).filter(Balance.user_id == user_id, Balance.instrument_ticker == ticker)
    result = await session.scalar(query)
    return result

@router.post("/balance/validate_balance")
async def validate_and_freeze_balance_for_operation(
    data: Validate_Balance,
    session: AsyncSession = Depends(db_helper.session_getter),
):

    query = select(Balance).filter(Balance.instrument_ticker == data.ticker, Balance.user_id == data.user_id)
    result = await session.scalar(query)
    if not result or result.available < data.amount:
        raise HTTPException(status_code=409, detail = "Insufficient ammount of funds on balance")

    if data.freeze_balance == True:
        result.available_to_reserved(data.amount)
        session.add(result)
        await session.commit()
    return result

@router.post("/balance/remove_from_reserved")
async def remove_from_reserved(
    data: Deposit_Withdraw_Instrument_V1,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    print(data.ticker, data.user_id)
    query = select(Balance).filter(Balance.instrument_ticker == data.ticker, Balance.user_id == data.user_id)
    result = await session.scalar(query)
    if not result:
        raise HTTPException(status_code=404, detail="Balance is not found for unfreeze")
    result.remove_from_reserved(data.amount)
    session.add(result)
    await session.commit()
    return result


@router.post("/balance/return_balance")
async def unfreeze_balance(
    data: Validate_Balance,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    query = select(Balance).filter(Balance.instrument_ticker == data.ticker, Balance.user_id == data.user_id)
    result = await session.scalar(query)
    if not result:
        raise HTTPException(status_code=404, detail="Balance is not found for unfreeze")
    result.reserved_to_available(data.amount)
    session.add(result)
    await session.commit()
    return result

@router.post("/admin/balance/deposit", tags=["balance"])
async def balance_deposit(
    data: Deposit_Withdraw_Instrument_V1,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    print("SDADAD")
    instrument = await get_instrument_by_ticker(ticker=data.ticker, session=session)
    statement = (
        insert(Balance)
        .values(user_id=data.user_id, instrument_ticker=instrument.ticker, _available=data.amount)
        .on_conflict_do_update(index_elements=["user_id", "instrument_ticker"], set_={"available": Balance._available + data.amount})
    )
    await session.execute(statement)
    await session.commit()
    return Ok()
 

@router.post("/admin/balance/withdraw", tags=["balance"])
async def balance_withdraw(
    data: Deposit_Withdraw_Instrument_V1,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    query = select(Balance).filter(Balance.user_id == data.user_id, Balance.instrument_ticker == data.ticker)
    balance = await session.scalar(query)
    if not balance:
        raise HTTPException(status_code=404, detail="Instrument with this ticker is not found in user's wallet or user id is not correct")
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

@router.post("/admin/balance/init", tags=["balance"])
async def init_balance_for_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    print(user_id)
    balance = Balance(user_id=user_id, instrument_ticker="RUB")
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

@router.post("/transaction")
async def create_transaction(
        data: Transaction_Post,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    try:
        transaction = Transaction(
            instrument_ticker=data.instrument_ticker, 
            amount=data.amount,
            price=data.price,
        )
        session.add(transaction)
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot create transaction with this ticker, price and amount")
    await session.commit()
    