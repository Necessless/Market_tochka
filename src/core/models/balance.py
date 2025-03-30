from typing import List
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint
import uuid


class Balance(Base):
    __tablename__ = "users_balances"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Users.id", ondelete="CASCADE")
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE"), 
        nullable=True
    )
    quantity: Mapped[int]

    __table_args__ = (UniqueConstraint("user_id", "instrument_id", name="uq_user_instrument"),)
