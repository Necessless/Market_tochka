from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from .schemas import Order_Body_POST, Create_Order_Response
from models import Order
from models.orders import Order_Type, Direction
from .schemas import Validate_Balance
from sqlalchemy.ext.asyncio import AsyncSession
from database import db_helper
from .dependencies import serialize_orders
from .service import (
    service_retrieve_order,
)
import httpx 
from httpx_helper import httpx_helper
from producers.order_producer import publish_order
from config import settings

router = APIRouter(tags=["order"], prefix=settings.api.v1.prefix)


@router.get("/order")
async def get_list_of_orders(
    session: AsyncSession = Depends(db_helper.session_getter)
):
    query = select(Order).order_by(Order.timestamp)
    result = await session.scalars(query)
    orders = result.all()
    serialized_orders = serialize_orders(orders)
    return serialized_orders

@router.post("/order")
async def create_order(
    order_info: Order_Body_POST,
    session: AsyncSession = Depends(db_helper.session_getter),
    client: httpx.AsyncClient = Depends(httpx_helper.client_getter)
):
    price = order_info.price
    print(order_info)
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
            data = Validate_Balance(ticker = order.instrument_ticker, user_id=order_info.user_id, amount = order.quantity, freeze_balance=freeze)
            response = await client.post(
                url=f"{settings.urls.balances}/v1/balance/validate_balance",
                json=data.model_dump(mode="json"),
                timeout=5.0
            )
            response.raise_for_status()
        elif order.direction == Direction.BUY and order.price:
            data = Validate_Balance(ticker = "RUB", user_id=order.user_id, amount = order.quantity*order.price, freeze_balance=True)
            response = await client.post(
                url=f"{settings.urls.balances}/v1/balance/validate_balance",
                json=data.model_dump(mode="json"),
                timeout=5.0
            )
            response.raise_for_status()
        elif order.direction == Direction.BUY and not order.price:
            data = Validate_Balance(ticker = "RUB", user_id=order.user_id, amount = order.quantity, freeze_balance=False)
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
    await publish_order(order)
    return {"success": True, "order_id": order.id}
    


# @router.get("/{order_id}")
# async def retrieve_order(
#     order_id: uuid.UUID,
#     authorization: str = Depends(api_key_header),
#     session: AsyncSession = Depends(db_helper.session_getter)
# ):
#     order = await service_retrieve_order(order_id=order_id, session=session)
#     serialized_order = serialize_orders([order])[0]
#     return serialized_order


# @router.delete("/{order_id}", response_model=Ok)
# async def cancel_order(
#     order_id: uuid.UUID,
#     session: AsyncSession = Depends(db_helper.session_getter)
# ):
#     result = await service_cancel_order(user_name=user_name, order_id=order_id, session=session)
#     await session.commit()
#     return result
    

