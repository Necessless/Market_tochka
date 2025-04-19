from pydantic import BaseModel, Field
import uuid


class Deposit_Withdraw_Instrument_V1(BaseModel):
    user_id: uuid.UUID
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
    amount: int = Field(gt=0)

