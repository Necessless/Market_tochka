from typing import List
from sqlalchemy import func, select
from .schemas import L2OrderBook, OrderBook, BalanceDTODirection, BaseBalanceDTO, GetBalanceDTO
import uuid
from models.orders import Order_Type, OrderStatus, Order,Direction
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import (
    find_orders_for_market_transaction, 
    find_orders_for_limit_transaction,
)
from database import db_helper
from fastapi import HTTPException
from producers.balance_producer import producer as balance_producer
from producers.get_balance_producer import producer as balance_get_producer
from saga_manager import manager
import asyncio


async def handle_order_creation(
        order_info: Order,
    ):
    # 1 проверить баланс рублей если покупка или баланс тикера если продажа
    # 2 заморозить количество на балансе
    # 3 находим ордеры для выполнения ордера
    # 4 производим транзакции 
    # 5 меняем статус ордера и сохраняем
    async with db_helper.async_session_factory() as session:
        async with session.begin():
            try:
                if order_info.price:
                    orders_for_transaction = await find_orders_for_limit_transaction(order_info, session)
                    if orders_for_transaction:
                        success = await make_limit_transactions(order_info, orders_for_transaction, session=session)
                        if not success:
                            print("Откат транзакций, ошибка в саге")
                            await session.rollback()
                            return
                else:
                    orders_for_transaction = await find_orders_for_market_transaction(order_info, session)#3
                    if not orders_for_transaction or sum([order.quantity for order in orders_for_transaction]) < order_info.quantity:
                        print("Cancelling market order")
                        order_info.status = OrderStatus.CANCELLED
                        print(order_info.id)
                        await session.merge(order_info)
                    else:
                        await make_market_transactions(order_info, orders_for_transaction,session=session)#4,5
            except Exception as e:
                print(f"[ERROR] Ошибка при создании ордера: {str(e)}")


async def get_balance_by_ticker(
    user_id: uuid.UUID,
    ticker: str
):
    corr_id = str(uuid.uuid4())
    user = str(user_id)
    return await balance_get_producer.call(GetBalanceDTO(user_id=user, ticker=ticker, correlation_id=corr_id))


def check_balance_for_market_buy(balance: int, price: int, amount: int):
    if balance < price * amount:
        return False
    return True


async def make_transaction_messages(
    direction: Direction,
    seller_id: uuid.UUID,
    buyer_id: uuid.UUID,
    order_ticker: str,
    order_type: Order_Type,
    amount: int,
    price: int
):
    try:
        correlation_id = str(uuid.uuid4())
        manager.register(correlation_id, operation_count=4)
        data_seller_add = BaseBalanceDTO(
            user_id=str(seller_id),
            ticker="RUB",
            amount=amount * price,
            direction=BalanceDTODirection.DEPOSIT,
            correlation_id=correlation_id,
            sub_id=1
        )

        data_seller_remove = BaseBalanceDTO(
            user_id=str(seller_id),
            ticker=order_ticker,
            amount=amount,
            direction=BalanceDTODirection.REMOVE,
            correlation_id=correlation_id,
            sub_id=2
        )   
        if direction == Direction.SELL or (direction == Direction.BUY and order_type == Order_Type.LIMIT):
            data_buyer_add = BaseBalanceDTO(user_id= str(buyer_id), ticker=order_ticker, amount=amount, direction=BalanceDTODirection.DEPOSIT, correlation_id=correlation_id, sub_id=3, price=price)
            data_buyer_remove = BaseBalanceDTO(user_id=str(buyer_id), ticker="RUB", amount=amount*price, direction=BalanceDTODirection.REMOVE, correlation_id=correlation_id, sub_id=4)
        else:
            data_buyer_add = BaseBalanceDTO(user_id=str(buyer_id), ticker=order_ticker, amount=amount, direction=BalanceDTODirection.DEPOSIT, correlation_id=correlation_id, sub_id=3, price=price)
            data_buyer_remove = BaseBalanceDTO(user_id=str(buyer_id), ticker="RUB", amount=amount*price, direction=BalanceDTODirection.WITHDRAW, correlation_id=correlation_id, sub_id=4, price=price)
        messages = [data_seller_add, data_seller_remove, data_buyer_add, data_buyer_remove]
        tasks = [balance_producer.publish_message(msg) for msg in messages]
        await asyncio.gather(*tasks)

        result = await manager.wait_for_all(correlation_id, timeout=10)
        if result is None:
            print(f"TIMEOUT: Сага {correlation_id} не завершилась вовремя")
            return False
            
        elif result is False:
            print(f"FAILED: Сага {correlation_id} провалилась")
            failed_ops = manager.get_failed_operations(correlation_id)
            successful_ops = manager.get_successful_operations(correlation_id)
            print(f"Провалившиеся операции: {failed_ops}")
            print(f"Успешные операции для отката: {successful_ops}")
            
            # if successful_ops:
            #     asyncio.create_task(compensate_saga(correlation_id, successful_ops))
            # else:
            manager.cleanup(correlation_id)
            return False
            
        else:
            print(f"SUCCESS: Сага {correlation_id} успешно завершена")
            manager.cleanup(correlation_id)
            return True
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке сообщений в брокер: {str(e)}")
        return False


async def make_limit_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession
):
    try:
        return_tasks = []
        quantity = order.quantity
        direction = order.direction
        i = 0
        while quantity != 0 and i != len(orders_for_transaction):
            curr_order = orders_for_transaction[i]
            amount_to_order = min(quantity, curr_order.quantity)
            price = curr_order.price
            if (direction == Direction.SELL and order.price < curr_order.price):
                price = order.price
                curr_order.reserved_value -= price * amount_to_order
            if (direction == Direction.BUY and order.price > curr_order.price):
                price = curr_order.price
                order.reserved_value -= price * amount_to_order
            saga_data = await make_transaction_messages(
                direction=order.direction,
                seller_id=curr_order.user_id if order.direction == Direction.BUY else order.user_id,
                buyer_id=curr_order.user_id if order.direction == Direction.SELL else order.user_id,
                order_ticker=order.instrument_ticker,
                order_type=order.order_type,
                amount=amount_to_order, 
                price=curr_order.price
            )
            if (saga_data == False):
                print(F"Сага провалилась для ордера:{order.id}")
                return False
            
            quantity -= amount_to_order
            curr_order.quantity -= amount_to_order
            curr_order.status = OrderStatus.PARTIALLY_EXECUTED
            if curr_order.quantity == 0:
                curr_order.filled = 1
                curr_order.status = OrderStatus.EXECUTED
                if curr_order.reserved_value and curr_order.reserved_value > 0:
                    print("ВОЗВРАЩАЕМ НА БАЛАНС ОСТАТОК")
                    return_tasks.append((curr_order.reserved_value, curr_order.user_id, "RUB"))
            i += 1
            session.add(curr_order)
        print("NO")
        order.quantity = quantity
        order.status = OrderStatus.PARTIALLY_EXECUTED
        if quantity == 0:
            order.status = OrderStatus.EXECUTED
            order.filled = 1
            if curr_order.reserved_value and order.reserved_value > 0:
                print("ВОЗВРАЩАЕМ НА БАЛАНС ОСТАТОК")
                return_tasks.append((order.reserved_value, order.user_id, "RUB"))
        await session.merge(order)
        await session.commit()
        for amount, uid, ticker in return_tasks:
            await return_to_balance(amount, user_id=uid, ticker=ticker)
            return_tasks.clear()
        return True
    except Exception as e:
        return_tasks.clear()
        print(f"[ERROR] Ошибка в make_limit_transactions: {str(e)}")
        return False


async def make_market_transactions(
        order: Order,
        orders_for_transaction: List[Order],
        session: AsyncSession
) -> None: 
    try:
        quantity = order.quantity
        balance_rub = await get_balance_by_ticker(ticker="RUB", user_id=order.user_id)
        i = 0
        while quantity != 0 and i != len(orders_for_transaction):
            curr_order = orders_for_transaction[i]
            amount_to_order = min(quantity, curr_order.quantity)
            if order.direction == Direction.BUY:
                if not check_balance_for_market_buy(balance_rub['available'], curr_order.price, amount_to_order):
                    order.status = OrderStatus.CANCELLED
                    break 
            saga_data = await make_transaction_messages(
                direction=order.direction,
                seller_id=curr_order.user_id if order.direction == Direction.BUY else order.user_id,
                buyer_id=curr_order.user_id if order.direction == Direction.SELL else order.user_id,
                order_ticker=order.instrument_ticker,
                order_type=order.order_type,
                amount=amount_to_order, 
                price=curr_order.price
            )
            if (saga_data == False):
                print(F"Сага провалилась для ордера:{order.id}")
                return 
            quantity -= amount_to_order
            curr_order.reserved_value -= curr_order.price * amount_to_order
            curr_order.quantity -= amount_to_order
            curr_order.status = OrderStatus.PARTIALLY_EXECUTED
            if curr_order.quantity == 0:
                curr_order.filled = 1
                curr_order.status = OrderStatus.EXECUTED
                if curr_order.reserved_value and curr_order.reserved_value > 0:
                    await return_to_balance(curr_order.reserved_value, user_id=curr_order.user_id, ticker="RUB")
            i += 1
            session.add(curr_order)
        order.quantity = quantity
        order.status = OrderStatus.EXECUTED
        order.filled = 1 
        await session.merge(order)
    except Exception as e:
        print(f"[ERROR] Ошибка в make_market_transactions: {str(e)}")


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


async def return_to_balance(amount: int, user_id: uuid.UUID, ticker: str):
    corr_id = str(uuid.uuid4())
    data = BaseBalanceDTO(ticker=ticker, user_id=str(user_id), amount=amount, direction=BalanceDTODirection.UNFREEZE, correlation_id=corr_id, sub_id=-1)
    await balance_producer.publish_message(data)
    

async def service_get_orderbook(
        ticker: str,
        limit: int,
        session: AsyncSession
) -> OrderBook:
    query_ask = (
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
    query_bid = (
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


async def handle_user_delete(user_id: uuid.UUID):
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
