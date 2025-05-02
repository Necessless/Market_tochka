import uuid
from pydantic import Field


class AuthRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserBase(BaseModel):
    id: uuid.UUID
    name: str 
    role: AuthRole 


class UserRegister(UserBase):
    api_key: str 

    
class NewUser(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    role: AuthRole = Field(default=AuthRole.USER)