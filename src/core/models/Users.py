from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from core.models.base import Base

class AuthRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "Users"

    name: Mapped[str] = mapped_column(unique=True)
    role: Mapped[AuthRole] = mapped_column()
    api_key: Mapped[str] = mapped_column(unique=True)