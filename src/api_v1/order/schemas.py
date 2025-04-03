from typing import Optional
from pydantic import BaseModel, Field
from core.models.orders import Direction, OrderStatus
import uuid
import datetime
from api_v1.admin.schemas import Ok

class Order_Body(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field(ge=1)
    price: Optional[int] = Field(default=None, gt=0)


class Market_Order_GET(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    user_id: uuid.UUID
    timestamp: datetime.datetime
    body: Order_Body


class Limit_Order_GET(Market_Order_GET):
    filled: int


class Create_Order_Response(Ok):
    order_id: uuid.UUID