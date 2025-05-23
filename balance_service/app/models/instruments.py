from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List



class Instrument(Base):
    __tablename__ = "instruments"

    id = None
    
    ticker: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="instrument")