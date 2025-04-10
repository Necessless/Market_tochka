from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.models.base import Base
from typing import List


class AuthRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "Users"

    name: Mapped[str] = mapped_column(unique=True)
    role: Mapped[AuthRole] = mapped_column()
    instruments: Mapped[List["Instrument"]] = relationship(
        back_populates="owners", 
        secondary="users_balance"
        )
    orders: Mapped[List["Order"]] = relationship(back_populates="user")