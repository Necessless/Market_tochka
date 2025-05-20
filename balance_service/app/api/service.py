from typing import Dict
import uuid
from sqlalchemy import delete, select, func
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.responses import Ok
from schemas.balance_DTO import Instrument_Base
from schemas.balance_DTO import Deposit_Withdraw_Instrument_V1
from models import Instrument, Balance, Transaction
from database import db_helper


async def get_instrument_by_ticker(
    ticker: str,
    session: AsyncSession
) -> Instrument:
    query = select(Instrument).filter(Instrument.ticker == ticker)
    instrument = await session.scalar(query)
    if not instrument:
        raise HTTPException(status_code=404, detail="Cant find instrument with this ticker")
    return instrument


async def get_balance_for_user(
        session: AsyncSession,
        id: uuid.UUID
) -> Dict[str, int]:
    print(id)
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
    print(balances)
    if not result:
        raise HTTPException(status_code=404, detail="User is not exists")
    return {ticker: available + reserved for ticker, available, reserved in balances}


async def handle_user_delete(user_id: str):
    async with db_helper.async_session_factory() as session:
        print(user_id)
        statement = delete(Balance).filter(Balance.user_id == user_id)
        await session.execute(statement)
        await session.commit()


async def handle_ticker_delete(ticker: str):
    async with db_helper.async_session_factory() as session:
        statement = delete(Balance).filter(Balance.instrument_ticker == ticker)
        statement_trans = delete(Transaction).filter(Transaction.instrument_ticker == ticker)
        await session.execute(statement)
        await session.execute(statement_trans)
        await session.commit()
    