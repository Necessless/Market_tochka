from typing import List, Optional
from pydantic import BaseModel, Field
from models.orders import Direction, OrderStatus
import uuid
import datetime
from enum import Enum


class OrderBodyPOST(BaseModel):
    direction: Direction
    ticker: str
    qty: int 
    user_id: uuid.UUID
    price: Optional[int] 


class MarketOrderBodyGET(BaseModel):
    direction: Direction
    ticker: str
    qty: int = Field()


class LimitOrderBodyGET(MarketOrderBodyGET):
    price: Optional[int] = Field(default=None, gt=0)


class MarketOrderGET(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    user_id: uuid.UUID
    timestamp: datetime.datetime
    body: MarketOrderBodyGET


class LimitOrderGET(MarketOrderGET):
    filled: int
    body: LimitOrderBodyGET


class Ok(BaseModel):
    success: bool = True


class CreateOrderResponse(Ok):
    order_id: uuid.UUID


class ValidateBalance(BaseModel):
    ticker: str
    user_id: uuid.UUID
    amount: int
    freeze_balance: Optional[bool] = Field(default=False)


class Balance(BaseModel):
    user_id: uuid.UUID
    instrument_ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
    available: int 
    reserved: int


class L2OrderBook(BaseModel):
    price: int = Field(ge=0)
    qty: int = Field(ge=0)


class OrderBook(BaseModel):
    bid_levels: List[L2OrderBook]
    ask_levels: List[L2OrderBook]


class OrderCancel(BaseModel):
    req_id: uuid.UUID
    order_id: uuid.UUID
    role: str


class BalanceDTODirection(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    REMOVE = "REMOVE"
    UNFREEZE = "UNFREEZE"


class BaseBalanceDTO(BaseModel):
    user_id: str
    ticker: str
    amount: int
    direction: BalanceDTODirection
    correlation_id: str
    sub_id: int


class GetBalanceDTO(BaseModel):
    user_id: str
    ticker: str
    correlation_id: str
