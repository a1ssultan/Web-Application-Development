from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Locker(Base):
    __tablename__ = "lockers"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    size: Mapped[str] = mapped_column(String(10), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    rentals: Mapped[list["Rental"]] = relationship(back_populates="locker")


class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(primary_key=True)
    locker_id: Mapped[int] = mapped_column(ForeignKey("lockers.id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="ACTIVE")

    locker: Mapped[Locker] = relationship(back_populates="rentals")
