from ...shared.core.models.base import Base
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy import ForeignKey, DateTime, func


class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"


class Order_Type(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.NEW)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="orders")
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())
    direction: Mapped[Direction] = mapped_column()
    instrument_ticker: Mapped[str] = mapped_column(ForeignKey("instruments.ticker", ondelete="CASCADE"))
    quantity: Mapped[int] 
    price: Mapped[int] = mapped_column(nullable=True)
    filled: Mapped[int] = mapped_column(default=0)
    order_type: Mapped[Order_Type] 
