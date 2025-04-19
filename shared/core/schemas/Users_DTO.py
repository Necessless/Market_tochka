import uuid
from pydantic import BaseModel
from core.models.Users import AuthRole


class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 


class UserRegister(UserBase):
    api_key: str 