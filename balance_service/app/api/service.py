from typing import Dict
import uuid
from sqlalchemy import select, func
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.responses import Ok
from schemas.balance_DTO import Instrument_Base
from schemas.balance_DTO import Deposit_Withdraw_Instrument_V1
from models import Instrument, Balance, Transaction



# async def get_balance_for_user_by_ticker(
#         user_id: uuid.UUID,
#         ticker: str,
#         session: AsyncSession
# ) -> Balance | None:
#     query = (
#         select(Balance)
#         .filter(Balance.user_id == user_id, Balance.instrument_ticker == ticker)
#     )
#     result = await session.scalar(query)
#     if not result:
#         raise HTTPException()
#     return balance


# async def validate_and_return_limit_balance(
#         data: Order_Body_POST,
#         user: User,
#         session: AsyncSession
# ) -> Balance:
#     if data.ticker == "RUB":
#         raise HTTPException(status_code=400, detail="Cant sell or buy Rubbles")
#     if data.direction == Direction.SELL:
#         balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
#         if balance is None or balance.available < data.qty:
#             raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to sell")
#     else:
#         balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
#         if not balance:
#             balance = Balance(
#                 user_name=user.name,
#                 instrument_ticker="RUB",
#                 available=0
#             )
#             session.add(balance)
#         elif balance.available < (data.qty * data.price):
#             raise HTTPException(status_code=400, detail="Insufficient funds(RUB) on balance to buy")
#     return balance


# async def validate_and_return_market_balance(
#         data: Order_Body_POST,
#         user: User,
#         session: AsyncSession
# ) -> Balance:
#     if data.ticker == "RUB":
#         raise HTTPException(status_code=400, detail="Cant sell or buy Rubbles")
#     if data.direction == Direction.SELL:
#         balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
#         if balance is None or balance.available < data.qty:
#             raise HTTPException(status_code=400, detail=f"Insufficient funds({data.ticker}) on balance to sell")
#     else:
#         balance = await get_balance_for_user_by_ticker(user_name=user.name, ticker=data.ticker, session=session)
#         if not balance:
#             balance = Balance(
#                 user_name=user.name,
#                 instrument_ticker=data.ticker,
#                 available=0
#             )
#         session.add(balance)
#     return balance



# async def add_remove_balance(
#         balance_instr: Balance,
#         balance_rub: Balance,
#         order: Order,
#         amount: int,
#         price: int,
#         session: AsyncSession
# ) -> None:
#     direction = order.direction,
#     order_type = order.order_type
#     if order.status == OrderStatus.CANCELLED: #если пользователь отменил ордер, и требуется вернуть средства
#         if direction == Direction.SELL:
#             balance_instr.remove_reserved(amount)
#         else:
#             balance_rub.remove_reserved(amount*price)
#         session.add_all([balance_instr, balance_rub])
#         return 
#     if direction == Direction.SELL: 
#         if order_type == Order_Type.LIMIT:
#             balance_instr.reserved -= amount
#         else:
#             balance_instr.available -= amount
#         balance_rub.available += (amount * price)
#     else:
#         if order_type == Order_Type.LIMIT:
#             balance_rub.reserved -= (amount * price)
#         else:
#             balance_rub.available -= (amount * price)
#         balance_instr.available += amount
#     session.add_all([balance_instr, balance_rub])



# async def reserve_sum_on_balance(
#         order: Order,
#         session: AsyncSession,
#         balance: Balance
# ) -> Balance:
#     try:
#         if order.direction == Direction.SELL:
#             balance.add_reserved(order.quantity)
#         else:
#             balance.add_reserved(order.quantity * order.price)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Not enough available funds on balance, check orders, rest of user's money is reserved")
#     session.add(balance)
#     return balance



    
# async def check_balance_for_market_buy(
#         balance: int,
#         price: int,
#         amount: int
# ) -> None:
#     if balance < (amount * price):
#         raise HTTPException(status_code=400, detail="Insufficient funds(RUB) on balance to make buy transaction")
#     return 

# async def make_market_transactions(
#         order: Order,
#         orders_for_transaction: List[Order],
#         session: AsyncSession,
#         balance_instr: Balance,
#         user: User
# ) -> None: 
#     quantity = order.quantity
#     balance_rub = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
#     if not balance_rub:
#         raise HTTPException(status_code=400, detail="No any rubbles on balance")
#     i = 0
#     while quantity != 0 and i != len(orders_for_transaction):
#         curr_order = orders_for_transaction[i]
#         amount_to_order = min(quantity, curr_order.quantity)
#         if order.direction == Direction.BUY:
#             await check_balance_for_market_buy(balance_rub.available, curr_order.price, amount_to_order)
#         await create_transaction(
#             instrument_ticker=order.instrument_ticker,
#             amount=amount_to_order,
#             price=curr_order.price,
#             session=session
#         )
#         await add_remove_balance(
#             balance_instr=balance_instr,
#             balance_rub=balance_rub,
#             order=order,
#             amount=amount_to_order,
#             price=curr_order.price,
#             session=session
#         )
#         quantity -= amount_to_order
#         curr_order.quantity -= amount_to_order
#         curr_order.status = OrderStatus.PARTIALLY_EXECUTED
#         if curr_order.quantity == 0:
#             curr_order.filled = 1
#             curr_order.status = OrderStatus.EXECUTED
#         i += 1
#         session.add(curr_order)


# async def make_limit_transactions(
#         order: Order,
#         orders_for_transaction: List[Order],
#         session: AsyncSession,
#         balance_instr: Balance,
#         user: User
# ) -> None:
#     balance_rub = await get_balance_for_user_by_ticker(user_name=user.name, ticker="RUB", session=session)
#     if not balance_rub:
#         raise HTTPException(status_code=400, detail="No any rubbles on balance")
#     quantity = order.quantity
#     i = 0 
#     while quantity > 0 and i != len(orders_for_transaction):
#         curr_order = orders_for_transaction[i]
#         amount_to_transact = min(curr_order.quantity, quantity)
#         await create_transaction(
#             instrument_ticker=order.instrument_ticker, 
#             amount=amount_to_transact,
#             price=curr_order.price,
#             session=session
#         )
#         await add_remove_balance(
#             balance_instr=balance_instr,
#             balance_rub=balance_rub,
#             order=order,
#             amount=amount_to_transact,
#             price=curr_order.price,
#             session=session
#         )
#         quantity -= amount_to_transact
#         curr_order.quantity -= amount_to_transact
#         order.status = OrderStatus.PARTIALLY_EXECUTED
#         curr_order.status = OrderStatus.PARTIALLY_EXECUTED
#         if curr_order.quantity == 0:
#             curr_order.status = OrderStatus.EXECUTED
#             curr_order.filled = 1
#         if quantity == 0:
#             order.status = OrderStatus.EXECUTED
#             order.filled = 1
#         session.add(curr_order)
#         i += 1
#     session.add(order)

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
