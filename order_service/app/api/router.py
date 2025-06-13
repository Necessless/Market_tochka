import uuid
from sqlalchemy import select
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from .schemas import Ok, OrderBodyPOST, OrderCancel
from models import Order
from models.orders import Order_Type, Direction, OrderStatus
from .schemas import ValidateBalance
from sqlalchemy.ext.asyncio import AsyncSession
from database import db_helper
from .dependencies import serialize_orders
from .service import (
    service_retrieve_order,
    service_get_orderbook,
    return_to_balance
)
import httpx 
from httpx_helper import httpx_helper
from producers.order_producer import producer
from config import settings

router = APIRouter(tags=["order"], prefix=settings.api.v1.prefix)


@router.get("/order/{user_id}")
async def get_list_of_orders(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Order).filter(Order.user_id == user_id).order_by(Order.timestamp)
    result = await session.scalars(query)
    orders = result.all()
    serialized_orders = serialize_orders(orders)
    return serialized_orders

@router.post("/order")
async def create_order(
    order_info: OrderBodyPOST,
    session: AsyncSession = Depends(db_helper.session_getter),
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter)
):
    price = order_info.price
    order = Order(instrument_ticker=order_info.ticker, quantity=order_info.qty, price=order_info.price, direction=order_info.direction, user_id=order_info.user_id)
    if price is not None:
        order.order_type = Order_Type.LIMIT
    else:
        order.order_type = Order_Type.MARKET
    try:
        if order.direction == Direction.SELL:
            #1,2
            freeze = True
            if order.price == None:
                freeze = False
            data = ValidateBalance(ticker = order.instrument_ticker, user_id=order_info.user_id, amount = order.quantity, freeze_balance=freeze)
            response = await client.post(
                url=f"{settings.urls.balances}/v1/balance/validate_balance",
                json=data.model_dump(mode="json"),
                timeout=5.0
            )
            response.raise_for_status()
        elif order.direction == Direction.BUY:
            data_tick= {"ticker": order.instrument_ticker}
            response_tick = await client.post(
                url=f"{settings.urls.balances}/v1/admin/check-instrument",
                params=data_tick,
                timeout=5.0
            )
            response_tick.raise_for_status()
            if order.order_type == Order_Type.LIMIT:
                data = ValidateBalance(ticker = "RUB", user_id=order.user_id, amount = order.quantity*order.price, freeze_balance=True)
                response = await client.post(
                    url=f"{settings.urls.balances}/v1/balance/validate_balance",
                    json=data.model_dump(mode="json"),
                    timeout=5.0
                )
                order.reserved_value =  order.quantity*order.price
                response.raise_for_status()
            else:
                data = ValidateBalance(ticker = "RUB", user_id=order.user_id, amount = order.quantity, freeze_balance=False)
                response = await client.post(
                    url=f"{settings.urls.balances}/v1/balance/validate_balance",
                    json=data.model_dump(mode="json"),
                    timeout=5.0
                )
                response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Сервис кошелька временно недоступен")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", "Ошибка в сервисе"))
    session.add(order)
    await session.commit()
    await session.refresh(order)
    await producer.publish_order(order)
    return {"success": True, "order_id": order.id}
    

@router.get("/public/orderbook/{ticker}")
async def get_orderbook(ticker: str, limit: int = Query(default=10), session: AsyncSession = Depends(db_helper.session_getter)):
    result = await service_get_orderbook(ticker, limit, session)
    return result


@router.get("/order/retrieve/{order_id}")
async def retrieve_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    order = await service_retrieve_order(order_id=order_id, session=session)
    serialized_order = serialize_orders([order])[0]
    return serialized_order


@router.post("/order/cancel", response_model=Ok)
async def cancel_order(
    data: OrderCancel,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Order).filter(Order.id == data.order_id)
    order = await session.scalar(query)
    if order is None:
        raise HTTPException(status_code=404, detail="Order with this id is not found")
    if order.status in [OrderStatus.PARTIALLY_EXECUTED, OrderStatus.EXECUTED, OrderStatus.CANCELLED]:
        raise HTTPException(status_code=409, detail="This order is already cancelled or executed")
    if order.order_type == Order_Type.MARKET:
        raise HTTPException(status_code=409, detail="Cannot cancel market order")
    if order.user_id != data.req_id and data.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    order.status = OrderStatus.CANCELLED
    if order.order_type == Order_Type.LIMIT:
        if order.direction == Direction.BUY:
            value_to_return = order.quantity * order.price
            ticker = "RUB"
        else:
            value_to_return = order.quantity
            ticker = order.instrument_ticker
        await return_to_balance(value_to_return, order.user_id, ticker)
    session.add(order)
    await session.commit()
    return Ok()
    

