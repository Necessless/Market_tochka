from pydantic import BaseModel, Field
import uuid


class Instrument_Base(BaseModel):
    name: str = Field()
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")


class Deposit_Instrument_V1(BaseModel):
    user_id: uuid.UUID
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
    amount: int = Field(gt=0)


class Ok(BaseModel):
    success: bool = Field(default=True)