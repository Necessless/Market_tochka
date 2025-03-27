from pydantic import BaseModel, Field
from core.models.Users import AuthRole
from sqlalchemy.dialects.postgresql import UUID
import uuid 


class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 
    api_key: str 


class NewUser(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: AuthRole = Field(default=AuthRole.USER)