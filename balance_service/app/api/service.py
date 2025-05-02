from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import User
from core.schemas.Users_DTO import UserRegister
from app.schemas import Ok
from core.schemas.Instruments_DTO import Instrument_Base
from ..schemas.balance_DTO import Deposit_Withdraw_Instrument_V1
from core.models import Instrument, Balance
from .dependencies import get_user_by_id, get_instrument_by_ticker
from user_service.app.api.auth import create_token




async def create_instrument(
        name: str,
        ticker: str,
        session: AsyncSession
) -> Instrument_Base:
    instrument = Instrument(name=name, ticker=ticker)
    session.add(instrument)
    await session.commit()
    return Instrument_Base(
        name=instrument.name,
        ticker=instrument.ticker
    )


async def service_delete_instrument(
        ticker: str,
        session: AsyncSession
) -> Ok:
    result = await get_instrument_by_ticker(ticker=ticker, session=session)
    await session.delete(result)
    await session.commit()
    return Ok()


async def service_balance_deposit(
        data: Deposit_Withdraw_Instrument_V1,
        session: AsyncSession
) -> Ok:
    user = await get_user_by_id(data.user_id, session)
    instrument = await get_instrument_by_ticker(ticker=data.ticker, session=session)
    statement = (
        insert(Balance)
        .values(user_name=user.name, instrument_ticker=instrument.ticker, _available=data.amount)
        .on_conflict_do_update(index_elements=["user_name", "instrument_ticker"], set_={"available": Balance._available + data.amount})
    )
    await session.execute(statement)
    await session.commit()
    return Ok()


async def service_balance_withdraw(
        data: Deposit_Withdraw_Instrument_V1,
        session: AsyncSession
) -> Ok:
    user = await get_user_by_id(data.user_id, session)
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

async def get_balance_for_user(
        session: AsyncSession,
        name: str
) -> Dict[str, int]:
    # query = text("""WITH balance AS (SELECT available, reserved, instrument_ticker
    #     FROM public.users_balance
    #     WHERE user_name = :name
    #     ),
    #     instrument AS (SELECT ticker FROM public.instruments)
    #     SELECT instrument.ticker, COALESCE(balance.available,0), COALESCE(balance.reserved,0)
    #     FROM balance
    #     RIGHT JOIN instrument
    #     ON instrument.ticker = balance.instrument_ticker;
    # """) raw sql запрос на всякий случай
    statement_balance = select(Balance).filter(Balance.user_name == name)
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
