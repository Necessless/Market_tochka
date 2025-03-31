from pydantic import BaseModel, Field


class Instrument(BaseModel):
    name: str = Field()
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
