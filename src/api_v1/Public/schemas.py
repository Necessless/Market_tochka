from pydantic import BaseModel, Field
from core.models.Users import AuthRole
import uuid 
from typing import List, Dict
from core.models import Instrument

class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 


class UserRegister(UserBase):
    api_key: str 


class NewUser(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: AuthRole = Field(default=AuthRole.USER)


class Instrument_Public(BaseModel):
    balance: Dict[str, int] 


class Balance(BaseModel):
    instruments: List[Instrument_Public]