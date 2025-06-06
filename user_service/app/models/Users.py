from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models import Base
from typing import List


class AuthRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "Users"

    name: Mapped[str] = mapped_column()
    role: Mapped[AuthRole] = mapped_column()