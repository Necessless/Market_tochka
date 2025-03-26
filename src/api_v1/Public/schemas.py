from pydantic import BaseModel
from core.models.Users import AuthRole

class UserBase(BaseModel):
    name: str
    role: AuthRole
    api_key: str

class UserGet(UserBase):
    id: int

class UserCreate(UserBase):
    pass