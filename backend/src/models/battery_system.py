"""
Battery System Model
Represents UPS and Rectifier systems at a location
"""
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from . import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .location import Location
    from .string import String as BatteryString


class SystemType(str, enum.Enum):
    """Battery system type enum"""
    UPS = "UPS"
    RECTIFIER = "RECTIFIER"
    HYBRID = "HYBRID"


class BatterySystem(Base, UUIDMixin, TimestampMixin):
    """
    Battery system (UPS or Rectifier) at a data center

    Attributes:
        system_id: Human-readable system identifier (e.g., DC-CNX-01-UPS-01)
        location_id: Foreign key to location
        system_type: UPS, RECTIFIER, or HYBRID
        manufacturer: Equipment manufacturer (e.g., APC, Emerson)
        model: Equipment model number
        rated_capacity_kva: System capacity in kVA
        strings_count: Number of battery strings in system
    """
    __tablename__ = "battery_system"

    system_id: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
        comment="System identifier (DC-CNX-01-UPS-01)"
    )

    location_id: Mapped[str] = mapped_column(
        ForeignKey("location.location_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Location foreign key"
    )

    system_type: Mapped[SystemType] = mapped_column(
        Enum(SystemType, native_enum=False),
        nullable=False,
        comment="System type: UPS, RECTIFIER, HYBRID"
    )

    manufacturer: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Equipment manufacturer"
    )

    model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Equipment model number"
    )

    rated_capacity_kva: Mapped[float] = mapped_column(
        nullable=False,
        comment="System rated capacity (kVA)"
    )

    strings_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of battery strings"
    )

    # Relationships
    location: Mapped["Location"] = relationship(
        "Location",
        back_populates="battery_systems"
    )

    strings: Mapped[List["BatteryString"]] = relationship(
        "String",
        back_populates="battery_system",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<BatterySystem(system_id='{self.system_id}', type='{self.system_type}', location='{self.location_id}')>"
