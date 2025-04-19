from pydantic import Field, BaseModel


class Ok(BaseModel):
    success: bool = Field(default=True)