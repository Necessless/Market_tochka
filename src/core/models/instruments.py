from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List



class Instrument(Base):
    __tablename__ = "instruments"

    name: Mapped[str] = mapped_column(unique=True)
    ticker: Mapped[str] = mapped_column(unique=True)
    owners: Mapped[List["User"]] = relationship(
        back_populates="instruments",
        secondary="users_balances"
    )