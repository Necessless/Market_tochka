from typing import List
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint
import uuid



class Balance(Base):
    __tablename__ = "users_balance"

    id = None

    user_name: Mapped[str] = mapped_column(
        ForeignKey("Users.name", ondelete="CASCADE"),
        primary_key=True
    )
    instrument_ticker: Mapped[str] = mapped_column(
        ForeignKey("instruments.ticker", ondelete="CASCADE"), 
        primary_key=True
    )
    quantity: Mapped[int]
