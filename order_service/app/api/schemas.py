from typing import Optional
from pydantic import BaseModel, Field
from order_service.models.orders import Direction, OrderStatus
import uuid
import datetime
from core.schemas.Responses import Ok

class Order_Body_POST(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field(ge=1)
    price: Optional[int] = Field(default=None, gt=0)


class Market_Order_Body_GET(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field()

class Limit_Order_Body_GET(Market_Order_Body_GET):
    price: Optional[int] = Field(default=None, gt=0)

class Market_Order_GET(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    user_id: uuid.UUID
    timestamp: datetime.datetime
    body: Market_Order_Body_GET


class Limit_Order_GET(Market_Order_GET):
    filled: int
    body: Limit_Order_Body_GET


class Create_Order_Response(Ok):
    order_id: uuid.UUID