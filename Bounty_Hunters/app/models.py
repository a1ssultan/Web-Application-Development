from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WantedCriminal(Base):
    __tablename__ = "wanted_criminals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100))  # real name may be unknown
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    reward: Mapped[int] = mapped_column(Integer, nullable=False)
    # Last known location: exact coordinates or a text note
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_note: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    armed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_crew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escape_master: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    hunts: Mapped[list["HuntLog"]] = relationship(back_populates="criminal", cascade="all, delete-orphan")


class HuntLog(Base):
    __tablename__ = "hunt_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("wanted_criminals.id", ondelete="CASCADE"), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    # Set by the database on insert, never by the client
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    criminal: Mapped[WantedCriminal] = relationship(back_populates="hunts")
