from typing import Dict
import uuid
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, select, func
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.responses import Ok
from schemas.balance_DTO import Deposit_Withdraw_Instrument_V1, Transaction_Post, Validate_Balance
from models import Instrument, Balance, Transaction
from database import db_helper


async def get_balance_for_user_by_ticker(user_id: str, ticker: str):
    async with db_helper.async_session_factory() as session:
        query = select(Balance).filter(Balance.user_id == user_id, Balance.instrument_ticker == ticker)
        result = await session.scalar(query)
        return result


async def get_instrument_by_ticker(
    ticker: str,
    session: AsyncSession
) -> Instrument:
    query = select(Instrument).filter(Instrument.ticker == ticker)
    instrument = await session.scalar(query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Cant find instrument with this ticker")
    return instrument


async def deposit_on_balance(data: Deposit_Withdraw_Instrument_V1) -> Ok:
    async with db_helper.async_session_factory() as session:
        instrument = await get_instrument_by_ticker(ticker=data.ticker, session=session)
        statement = (
            insert(Balance)
            .values(user_id=data.user_id, instrument_ticker=instrument.ticker, _available=data.amount)
            .on_conflict_do_update(index_elements=["user_id", "instrument_ticker"], set_={"available": Balance._available + data.amount})
        )
        if data.price != 0:
            await service_create_transaction(data=Transaction_Post(instrument_ticker=data.ticker, amount=data.amount, price=data.price))
        await session.execute(statement)
        await session.commit()
    return Ok()


async def withdraw_from_balance(data: Deposit_Withdraw_Instrument_V1) -> Ok:
    async with db_helper.async_session_factory() as session:
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
        if data.price != 0:
            await service_create_transaction(data=Transaction_Post(instrument_ticker=data.ticker, amount=data.amount, price=data.price))
        await session.commit()
    return Ok()
    

async def service_unfreeze_balance(data: Validate_Balance):
    async with db_helper.async_session_factory() as session:
        query = select(Balance).filter(Balance.instrument_ticker == data.ticker, Balance.user_id == data.user_id)
        result = await session.scalar(query)
        if not result:
            raise HTTPException(status_code=404, detail="Balance is not found for unfreeze")
        result.reserved_to_available(data.amount)
        session.add(result)
        await session.commit()
        return result


async def get_balance_for_user(
        session: AsyncSession,
        id: uuid.UUID
) -> Dict[str, int]:
    statement_balance = select(Balance).filter(Balance.user_id == id)
    statement_instrument = select(Instrument)
    statement_balance = statement_balance.cte('balance')
    statement_instrument = statement_instrument.cte('instrument')
    statement = (
        select(statement_instrument.c.ticker, func.coalesce(statement_balance.c.available,0), func.coalesce(statement_balance.c.reserved,0))
        .select_from(statement_instrument)
        .outerjoin(statement_balance, statement_instrument.c.ticker == statement_balance.c.instrument_ticker)
    )
    result = await session.execute(statement)
    balances = result.all()
    if not result:
        raise HTTPException(status_code=404, detail="User is not exists")
    return {ticker: available + reserved for ticker, available, reserved in balances}


async def handle_user_delete(user_id: str):
    async with db_helper.async_session_factory() as session:
        print(user_id)
        statement = delete(Balance).filter(Balance.user_id == user_id)
        await session.execute(statement)
        await session.commit()


async def service_remove_from_reserved(
    data: Deposit_Withdraw_Instrument_V1
):
    async with db_helper.async_session_factory() as session:
        query = select(Balance).filter(Balance.instrument_ticker == data.ticker, Balance.user_id == data.user_id)
        result = await session.scalar(query)
        if not result:
            raise HTTPException(status_code=404, detail="Balance is not found for unfreeze")
        result.remove_from_reserved(data.amount)
        session.add(result)
        await session.commit()
        return result


async def handle_ticker_delete(ticker: str):
    async with db_helper.async_session_factory() as session:
        statement = delete(Balance).filter(Balance.instrument_ticker == ticker)
        statement_trans = delete(Transaction).filter(Transaction.instrument_ticker == ticker)
        await session.execute(statement)
        await session.execute(statement_trans)
        await session.commit()
    

async def service_create_transaction(data: Transaction_Post):
    async with db_helper.async_session_factory() as session:
        try:
            transaction = Transaction(
                instrument_ticker=data.instrument_ticker, 
                amount=data.amount,
                price=data.price,
            )
            session.add(transaction)
            await session.commit()
        except Exception:
            raise HTTPException(status_code=400, detail="Cannot create transaction with this ticker, price and amount")
        