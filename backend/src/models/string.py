"""
String Model
Represents a battery string (series connection of batteries)
"""
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String as SQLString, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from . import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .battery_system import BatterySystem
    from .battery import Battery


class String(Base, UUIDMixin, TimestampMixin):
    """
    Battery string (series connection of batteries)

    Attributes:
        string_id: Human-readable string identifier (e.g., DC-CNX-01-UPS-01-STR-01)
        system_id: Foreign key to battery system (UUID)
        position: String position within system (1, 2, 3, ...)
        batteries_count: Number of batteries in string (typically 24)
        nominal_voltage_v: Nominal string voltage (24 batteries × 12V = 288V)
    """
    __tablename__ = "string"

    string_id: Mapped[str] = mapped_column(
        SQLString(40),
        nullable=False,
        unique=True,
        index=True,
        comment="String identifier (DC-CNX-01-UPS-01-STR-01)"
    )

    system_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("battery_system.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Battery system foreign key"
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="String position within system"
    )

    batteries_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
        comment="Number of batteries in series"
    )

    nominal_voltage_v: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=288.0,
        comment="Nominal string voltage (V)"
    )

    # Relationships
    battery_system: Mapped["BatterySystem"] = relationship(
        "BatterySystem",
        back_populates="strings"
    )

    batteries: Mapped[List["Battery"]] = relationship(
        "Battery",
        back_populates="string",
        cascade="all, delete-orphan",
        order_by="Battery.position"
    )

    def __repr__(self) -> str:
        return f"<String(string_id='{self.string_id}', position={self.position}, batteries={self.batteries_count})>"
