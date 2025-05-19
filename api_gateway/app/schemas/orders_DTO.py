from enum import Enum
import uuid 
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"


class Order_Type(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"



class Order_Body_POST(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field(ge=1)
    user_id: Optional[uuid.UUID]= Field(default=None)
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
    timestamp: datetime
    body: Market_Order_Body_GET


class Limit_Order_GET(Market_Order_GET):
    filled: int
    body: Limit_Order_Body_GET