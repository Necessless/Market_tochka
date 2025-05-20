from typing import List
from sqlalchemy import delete, select
from .schemas import Order_Body_POST, Ok, Market_Order_GET, Limit_Order_GET, Validate_Balance, Balance
import uuid
from models.orders import Order_Type, OrderStatus, Order,Direction
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import (
    find_orders_for_market_transaction, 
    find_orders_for_limit_transaction,
)
from database import db_helper
from config import settings
import httpx 
from fastapi import HTTPException

async def handle_order_creation(
        order_info: Order,
    ):
    # 1 проверить баланс рублей если покупка или баланс тикера если продажа
    # 2 заморозить количество на балансе
    # 3 находим ордеры для выполнения ордера
    # 4 производим транзакции 
    # 5 меняем статус ордера и сохраняем
    async with db_helper.async_session_factory() as session:
        async with httpx.AsyncClient(timeout=5.0) as client:
            async with session.begin():
                print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
                if order_info.price:
                    orders_for_transaction = await find_orders_for_limit_transaction(order_info, session)
                    if orders_for_transaction:
                        await make_limit_transactions(order_info, orders_for_transaction, session=session, client=client)
                else:
                    orders_for_transaction = await find_orders_for_market_transaction(order_info, session)#3
                    if not orders_for_transaction or sum([order.quantity for order in orders_for_transaction]) < order_info.quantity:
                        order_info.status = OrderStatus.CANCELLED
                        session.add(order_info)
                    else:
                        await make_market_transactions(order_info, orders_for_transaction,session=session,client=client)#4,5
    
async def get_balance_by_ticker(
        user_id: uuid.UUID,
        ticker: str, 
        client: httpx.AsyncClient
):
    try:
        response = await client.get(url=f"{settings.urls.balances}/v1/balance_ticker/{user_id}/{ticker}")
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return response.json()
    
def check_balance_for_market_buy(balance:int, price: int, amount:int):
    if balance < price * amount:
        return False
    return True

async def create_transaction_request(ticker:str, amount: int, price: int, client: httpx.AsyncClient):
    try:
        data = {"instrument_ticker": ticker, "amount": amount, "price": price}
        response = await client.post(url=f"{settings.urls.balances}/v1/transaction", json=data, timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    return True

async def add_remove_balance(
    direction: Direction,
    seller_id: uuid.UUID,
    buyer_id: uuid.UUID,
    order_ticker: str,
    order_type: Order_Type,
    amount: int,
    price:int,
    client: httpx.AsyncClient
):
    try:
        data_seller_add= {"user_id": str(seller_id), "ticker": "RUB", "amount": amount * price}
        data_seller_remove= {"user_id": str(seller_id), "ticker": order_ticker, "amount": amount}
        print("START")
        print(order_ticker)
        deposit_seller_request = await client.post(url=f"{settings.urls.balances}/v1/admin/balance/deposit", json=data_seller_add, timeout=5.0)
        deposit_seller_request.raise_for_status()
        withdraw_seller_request = await client.post(url=f"{settings.urls.balances}/v1/balance/remove_from_reserved", json=data_seller_remove, timeout=5.0)
        withdraw_seller_request.raise_for_status()
        if direction == Direction.SELL or (direction == Direction.BUY and order_type == Order_Type.LIMIT):
            data_buyer_add = {"user_id": str(buyer_id), "ticker": order_ticker, "amount": amount}
            data_buyer_remove = {"user_id": str(buyer_id), "ticker": "RUB", "amount": amount*price}
            deposit_buyer_request = await client.post(url=f"{settings.urls.balances}/v1/admin/balance/deposit", json=data_buyer_add, timeout=5.0)
            withdraw_buyer_request= await client.post(url=f"{settings.urls.balances}/v1/balance/remove_from_reserved", json=data_buyer_remove, timeout=5.0)
        else:
            data_buyer_add = {"user_id": str(buyer_id), "ticker": order_ticker, "amount": amount}
            data_buyer_remove = {"user_id": str(buyer_id), "ticker": "RUB", "amount": amount*price}
            deposit_buyer_request = await client.post(url=f"{settings.urls.balances}/v1/admin/balance/deposit", json=data_buyer_add, timeout=5.0)
            withdraw_buyer_request = await client.post(url=f"{settings.urls.balances}/v1/admin/balance/withdraw", json=data_buyer_remove, timeout=5.0)
        deposit_buyer_request.raise_for_status()
        withdraw_buyer_request.raise_for_status()
        print("END")
        await create_transaction_request(ticker=order_ticker,amount=amount, price=price, client=client)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен, не удалось создать транзакции")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))

#TODO: ДОДЕЛАТЬ РЕАЛИЗАЦИЮ ОРДЕРОВ, ТАКЖЕ НЕ ЗАБЫТЬ СДЕЛАТЬ ТАК, ЧТОБЫ У ДРУГИХ ПОЛЬЗОВАТЕЛЕЙ БЫЛО ДВИЖЕНИЕ СРЕДСТВ НА БАЛАНСЕ
async def make_limit_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession,
        client: httpx.AsyncClient
):
    print("ALGORITHM")
    quantity = order.quantity
    direction = order.direction
    i = 0
    print("LO")
    while quantity != 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        amount_to_order = min(quantity, curr_order.quantity)
        print("YES")
        await add_remove_balance(
            direction=direction,
            seller_id=curr_order.user_id if direction == Direction.BUY else order.user_id,
            buyer_id=curr_order.user_id if direction == Direction.SELL else order.user_id,
            order_ticker = order.instrument_ticker,
            order_type = order.order_type,
            amount=amount_to_order, 
            price=curr_order.price,
            client=client
        )
        quantity -= amount_to_order
        curr_order.quantity -= amount_to_order
        curr_order.status = OrderStatus.PARTIALLY_EXECUTED
        if curr_order.quantity == 0:
            curr_order.filled = 1
            curr_order.status = OrderStatus.EXECUTED
        i += 1
        session.add(curr_order)
    print("NO")
    order.quantity = quantity
    order.status = OrderStatus.PARTIALLY_EXECUTED
    if quantity == 0:
        order.status = OrderStatus.EXECUTED
        order.filled = 1
    session.add(order)


async def make_market_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession,
        client: httpx.AsyncClient
) -> None: 
    quantity = order.quantity
    print("TRAAAANS")
    balance_rub = await get_balance_by_ticker(ticker="RUB", user_id=order.user_id, client=client)
    i = 0
    while quantity != 0 and i != len(orders_for_transaction):
        curr_order = orders_for_transaction[i]
        amount_to_order = min(quantity, curr_order.quantity)
        if order.direction == Direction.BUY:
            if not check_balance_for_market_buy(balance_rub.available, curr_order.price, amount_to_order):
                order.status = OrderStatus.CANCELLED
                session.add(order)
                return 
        await add_remove_balance(
            direction=order.direction,
            seller_id=curr_order.user_id if order.direction == Direction.BUY else order.user_id,
            buyer_id=curr_order.user_id if order.direction == Direction.SELL else order.user_id,
            order_ticker = order.instrument_ticker,
            order_type = order.order_type,
            amount=amount_to_order, 
            price=curr_order.price,
            client=client
        )
        quantity -= amount_to_order
        curr_order.quantity -= amount_to_order
        curr_order.status = OrderStatus.PARTIALLY_EXECUTED
        if curr_order.quantity == 0:
            curr_order.filled = 1
            curr_order.status = OrderStatus.EXECUTED
        i += 1
        session.add(curr_order)
    order.quantity = quantity
    order.status = OrderStatus.EXECUTED
    order.filled = 1 
    session.add(order)

async def service_retrieve_order(
        order_id: uuid.UUID,
        session: AsyncSession
) -> Order:
    query = select(Order).filter(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="order with this id not found")
    return order


# async def service_cancel_order(
#     user_name: str,
#     order_id: uuid.UUID,
#     session: AsyncSession
# ) -> Ok:
#     user = await get_user(session=session, name=user_name)
#     order = await service_retrieve_order(order_id=order_id, session=session)
#     validate_user_for_order_cancel(user, order)
#     balance_instr = await get_balance_for_user_by_ticker(user_name=user_name, ticker=order.instrument_ticker, session=session)
#     balance_rub = await get_balance_for_user_by_ticker(user_name=user_name, ticker="RUB", session=session)
#     order.status = OrderStatus.CANCELLED
#     session.add(order)
#     await add_remove_balance(
#         balance_instr=balance_instr,
#         balance_rub=balance_rub,
#         order=order,
#         amount=order.quantity,
#         price=order.price,
#         session=session
#     )
#     return Ok()


# async def service_get_orderbook(
#         ticker: str,
#         limit: int,
#         session: AsyncSession
# ) -> OrderBook:
#     query_ask = (
#         select(func.sum(Order.quantity), Order.price)
#         .filter(
#             Order.instrument_ticker == ticker,
#             Order.direction == Direction.BUY,
#             Order.order_type == Order_Type.LIMIT,
#             ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED])
#         )
#         .group_by(Order.price)
#         .order_by(Order.price.desc())
#         .limit(limit)
#     )
#     query_bid = (
#         select(func.sum(Order.quantity), Order.price)
#         .filter(
#             Order.instrument_ticker == ticker,
#             Order.direction == Direction.SELL,
#             Order.order_type == Order_Type.LIMIT,
#             ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED])
#         )
#         .group_by(Order.price)
#         .order_by(Order.price.asc())
#         .limit(limit)
#     )
#     res_ask = await session.execute(query_ask)
#     res_bid = await session.execute(query_bid)

#     res_ask = res_ask.all()
#     res_bid = res_bid.all()
    
#     res_ask = [L2OrderBook(price=price, qty=qty) for qty, price in res_ask]
#     res_bid = [L2OrderBook(price=price, qty=qty) for qty, price in res_bid]

#     return OrderBook(
#         bid_levels=res_bid,
#         ask_levels=res_ask
#     )
async def handle_user_delete(user_id: uuid.UUID):
    print(user_id)
    async with db_helper.async_session_factory() as session:
        query = select(Order).where(Order.user_id == user_id, ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]))
        orders = await session.scalars(query)
        for order in orders.all():
            order.status = OrderStatus.CANCELLED
            session.add(order)
        await session.commit()


async def handle_ticker_delete(ticker: str):
    async with db_helper.async_session_factory() as session:
        query = select(Order).where(Order.instrument_ticker == ticker, ~Order.status.in_([OrderStatus.CANCELLED, OrderStatus.EXECUTED]))
        orders = await session.scalars(query)
        for order in orders.all():
            order.status = OrderStatus.CANCELLED
            session.add(order)
        await session.commit()