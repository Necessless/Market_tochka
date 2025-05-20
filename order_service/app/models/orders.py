from .base import Base
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, DateTime, func


class Direction(str,Enum):
    BUY = "BUY"
    SELL = "SELL"


class Order_Type(str,Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str,Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.NEW)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
        )
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now())
    direction: Mapped[Direction] = mapped_column()
    instrument_ticker: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] 
    price: Mapped[int] = mapped_column(nullable=True)
    filled: Mapped[int] = mapped_column(default=0)
    order_type: Mapped[Order_Type] 
    reserved_value: Mapped[int] = mapped_column(default=0)

    def as_dict(self):
        result = {
            "id": str(self.id),
            "status": self.status.value,
            "user_id": str(self.user_id),
            "direction": self.direction.value,
            "instrument_ticker": self.instrument_ticker,
            "quantity": self.quantity,
            "price": self.price,
            "filled": self.filled,
            "order_type": self.order_type.value,
            "reserved_value": self.reserved_value
        }
        return result