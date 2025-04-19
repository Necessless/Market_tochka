from pydantic import Field, BaseModel


class Instrument_Base(BaseModel):
    name: str = Field()
    ticker: str = Field(pattern=r"^[A-Z]{2,10}$")
