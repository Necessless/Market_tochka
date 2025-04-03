from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime, func


class Transaction(Base):
    __tablename__ = "instruments_transactions"
    
    instrument_ticker: Mapped[str] = mapped_column(ForeignKey("instruments.ticker", ondelete="CASCADE"))
    instrument: Mapped["Instrument"] = relationship(back_populates="transactions")
    amount: Mapped[int]
    price: Mapped[int]
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())