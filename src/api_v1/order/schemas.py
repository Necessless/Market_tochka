from pydantic import BaseModel, Field
from core.models.orders import Direction, OrderStatus
import uuid
from sqlalchemy import DateTime


class Market_Order_Body(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field(ge=1)


class Limit_Order_Body(Market_Order_Body):
    price: int = Field(gt=0)


class Market_Order_GET(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    user_id: uuid.UUID
    timestamp: DateTime
    body: Market_Order_Body


class Limit_Order_GET(Market_Order_GET):
    body: Limit_Order_Body
    filled: int