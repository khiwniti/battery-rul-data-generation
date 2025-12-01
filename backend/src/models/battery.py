"""
Battery Model
Represents individual VRLA battery (jar)
"""
import uuid
from typing import TYPE_CHECKING, Optional
from datetime import date
from sqlalchemy import String, Integer, ForeignKey, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from . import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .string import String as BatteryString
    from .alert import Alert


class Battery(Base, UUIDMixin, TimestampMixin):
    """
    Individual VRLA battery (jar)

    Attributes:
        battery_id: Human-readable battery identifier (e.g., BAT-DC-CNX-01-UPS-01-STR-01-001)
        string_id: Foreign key to battery string (UUID)
        serial_number: Manufacturer serial number
        position: Position within string (1-24)
        manufacturer: Battery manufacturer (e.g., CSB)
        model: Battery model (e.g., HX12-120)
        nominal_voltage_v: Nominal voltage per jar (12V)
        nominal_capacity_ah: Nominal capacity (120Ah)
        installed_date: Date battery was installed
        warranty_months: Warranty period in months (typically 36-60)
    """
    __tablename__ = "battery"

    battery_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Battery identifier (BAT-DC-CNX-01-UPS-01-STR-01-001)"
    )

    string_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("string.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Battery string foreign key"
    )

    serial_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
        comment="Manufacturer serial number"
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position within string (1-24)"
    )

    manufacturer: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CSB",
        comment="Battery manufacturer"
    )

    model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="HX12-120",
        comment="Battery model number"
    )

    nominal_voltage_v: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=12.0,
        comment="Nominal voltage per jar (V)"
    )

    nominal_capacity_ah: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=120.0,
        comment="Nominal capacity (Ah)"
    )

    installed_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Installation date"
    )

    warranty_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="Warranty period (months)"
    )

    # Optional: Track replacement
    replaced_battery_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Battery ID this unit replaced"
    )

    # Relationships
    string: Mapped["BatteryString"] = relationship(
        "String",
        back_populates="batteries"
    )

    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="battery",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Battery(battery_id='{self.battery_id}', serial='{self.serial_number}', position={self.position})>"

    @property
    def age_days(self) -> int:
        """Calculate battery age in days"""
        from datetime import date as date_type
        return (date_type.today() - self.installed_date).days

    @property
    def is_in_warranty(self) -> bool:
        """Check if battery is still under warranty"""
        warranty_days = self.warranty_months * 30
        return self.age_days <= warranty_days
