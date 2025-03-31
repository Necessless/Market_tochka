from pydantic import BaseModel, Field


class Instrument_Base(BaseModel):
    name: str = Field()
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")


class Ok(BaseModel):
    success: bool = Field(default=True)