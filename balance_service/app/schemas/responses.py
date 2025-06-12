from pydantic import BaseModel, Field


class Ok(BaseModel):
    success: bool = True


class Transaction_Response(BaseModel):
    correlation_id: str
    sub_id: int
    success: bool
    message: str = Field(default="None")


class BalanceGetResponse(BaseModel):
    available: int
    correlation_id: str