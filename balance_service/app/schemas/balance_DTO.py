from pydantic import BaseModel, Field
import uuid


class Deposit_Withdraw_Instrument_V1(BaseModel):
    user_id: uuid.UUID
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
    amount: int = Field(gt=0)

class Instrument_Base(BaseModel):
    name: str = Field()
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")

class Validate_Balance(BaseModel):
    ticker: str
    user_id: uuid.UUID
    amount: int
    freeze_balance: bool

class Transaction_Post(BaseModel):
    instrument_ticker: str
    amount: int
    price: int