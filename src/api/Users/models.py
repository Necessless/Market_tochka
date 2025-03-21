from sqlalchemy.orm import Mapped, mapped_column
from src.core.models import Base

class User(Base):
    __tablename__ = "Users"

    username: Mapped[str] = mapped_column(unique=True)