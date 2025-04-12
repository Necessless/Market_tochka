from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from typing import Sequence, Dict
from core.models import User, Balance, Instrument, Order
from core.models.orders import Order_Type, OrderStatus, Direction
from .schemas import UserBase, NewUser, UserRegister, OrderBook, L2OrderBook
from sqlalchemy.ext.asyncio import AsyncSession 
from .auth import (
    create_token
)


async def get_user(
        session: AsyncSession,
        name: str,
) -> UserBase:
    query = select(User).where(User.name == name)
    user = await session.scalar(query)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Wrong Authentication token"
            )
    return UserBase(
        id=user.id,
        name=user.name,
        role=user.role,
    )


async def create_user(
        session: AsyncSession,
        data: NewUser
) -> UserRegister:
    to_encrypt = {"name": data.name}
    token = create_token(to_encrypt)
    user = User(name=data.name, role=data.role)
    session.add(user)
    await session.commit()
    return UserRegister(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=token
    )


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    query = select(User).order_by(User.id)
    result = await session.scalars(query)
    return result.all()


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


async def service_get_orderbook(
        ticker: str,
        limit: int,
        session: AsyncSession
) -> OrderBook:
    query_ask = (
        select(func.sum(Order.quantity), Order.price)
        .filter(
            Order.instrument_ticker == ticker,
            Order.direction == Direction.BUY,
            Order.order_type == Order_Type.LIMIT,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED])
        )
        .group_by(Order.price)
        .order_by(Order.price.desc())
        .limit(limit)
    )
    query_bid = (
        select(func.sum(Order.quantity), Order.price)
        .filter(
            Order.instrument_ticker == ticker,
            Order.direction == Direction.SELL,
            Order.order_type == Order_Type.LIMIT,
            ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED])
        )
        .group_by(Order.price)
        .order_by(Order.price.asc())
        .limit(limit)
    )
    res_ask = await session.execute(query_ask)
    res_bid = await session.execute(query_bid)

    res_ask = res_ask.all()
    res_bid = res_bid.all()
    
    res_ask = [L2OrderBook(price=price, qty=qty) for qty, price in res_ask]
    res_bid = [L2OrderBook(price=price, qty=qty) for qty, price in res_bid]

    return OrderBook(
        bid_levels=res_bid,
        ask_levels=res_ask
    )