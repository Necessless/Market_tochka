from pydantic import BaseModel, Field


class Instrument_POST(BaseModel):
    name: str = Field(min_length=3)
    ticker: str = Field(min_length=3, pattern=r"^[A-Z]{2,10}$")
