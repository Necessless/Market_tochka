from pydantic import BaseModel, Field
from core.models.Users import AuthRole
import uuid 
from typing import List


class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 


class UserRegister(UserBase):
    api_key: str 


class NewUser(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: AuthRole = Field(default=AuthRole.USER)


class Balance_one_instrument(BaseModel):
    available: int 
    reserved: int


class L2OrderBook(BaseModel):
    price: int = Field(ge=0)
    qty: int = Field(ge=0)

class OrderBook(BaseModel):
    bid_levels: List[L2OrderBook]
    ask_levels: List[L2OrderBook]