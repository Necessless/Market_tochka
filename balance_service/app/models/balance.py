from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

import uuid

class Balance(Base):
    __tablename__ = "users_balance"

    id = None

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
        )

    instrument_ticker: Mapped[str] = mapped_column(
        ForeignKey("instruments.ticker", ondelete="CASCADE"), 
        primary_key=True
    )

    _available: Mapped[int] = mapped_column("available", default=0)
    _reserved: Mapped[int] = mapped_column("reserved", default=0)

    __table_args__ = (
        UniqueConstraint('user_id', 'instrument_ticker', name='user_ticker_constraint'),
    )

    @property
    def available(self):
        return self._available
    
    @available.setter
    def available(self, value):
        self._available = value

    @property
    def reserved(self):
        return self._reserved

    @reserved.setter
    def reserved(self, value):
        self._reserved = value

    def add_reserved(self, value):
        if value > self._available:
            raise ValueError("Not enough quantity on balance to reserve this amount")
        self._available -= value
        self._reserved += value

    def remove_reserved(self, value):
        if value > self._reserved:
            raise ValueError("Not enough quantity reserved on balance to unreserve this amount")
        self._available += value
        self._reserved -= value