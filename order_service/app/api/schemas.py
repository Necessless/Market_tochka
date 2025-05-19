from typing import Optional
from pydantic import BaseModel, Field
from models.orders import Direction, OrderStatus
import uuid
import datetime


class Order_Body_POST(BaseModel):
    direction: Direction
    ticker: str
    qty: int 
    user_id: uuid.UUID
    price: Optional[int] 


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

class Ok(BaseModel):
    success: bool = True

class Create_Order_Response(Ok):
    order_id: uuid.UUID

class Validate_Balance(BaseModel):
    ticker: str
    user_id: uuid.UUID
    amount: int
    freeze_balance: bool

class Balance(BaseModel):
    user_id: uuid.UUID
    instrument_ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
    available: int 
    reserved: int