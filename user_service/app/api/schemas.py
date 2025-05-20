from pydantic import BaseModel, Field
from models.Users import AuthRole
from typing import List
import uuid

class NewUser(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: AuthRole = Field(default=AuthRole.USER)


class Balance_one_instrument(BaseModel):
    available: int 
    reserved: int




class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 


class UserRegister(UserBase):
    api_key: str 