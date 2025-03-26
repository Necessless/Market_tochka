from pydantic import BaseModel, Field
from core.models.Users import AuthRole

class UserBase(BaseModel):
    name: str 
    role: AuthRole 
    api_key: str 

class UserGet(UserBase):
    id: int

class UserCreate(UserBase):
    pass

class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: AuthRole = Field(default=AuthRole.USER)