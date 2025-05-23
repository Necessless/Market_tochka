from enum import Enum
import uuid
from pydantic import BaseModel, Field, field_validator


class AuthRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 



class UserRegister(UserBase):
    api_key: str 

    
class NewUser(BaseModel):
    name: str = Field(min_length=3)
    role: AuthRole = Field(default=AuthRole.USER)
    @field_validator("role", mode='before')
    def normalize_role(cls, v):
        if isinstance(v, str):
            v = v.strip().upper()
        return v
