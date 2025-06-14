from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid
from enum import Enum


class Instrument_Base(BaseModel):
    name: str = Field()
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")


class Validate_Balance(BaseModel):
    ticker: str
    user_id: uuid.UUID
    amount: int
    freeze_balance: Optional[bool] = Field(default=False)


class Transaction_Post(BaseModel):
    instrument_ticker: str
    amount: int
    price: int


class BalanceDTODirection(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    REMOVE = "REMOVE"
    UNFREEZE = "UNFREEZE"


class Deposit_Withdraw_Instrument_V1(BaseModel):
    user_id: uuid.UUID
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
    amount: int = Field(gt=0)
    direction: BalanceDTODirection = Field(default=BalanceDTODirection.DEPOSIT)
    price: Optional[int] = Field(default=0)


class TransactionSchema(BaseModel):
    ticker: str = Field(..., alias="instrument_ticker")
    amount: int
    price: int
    timestamp: datetime

    model_config = {
        "from_attributes": True,  
        "populate_by_name": True  
    }