"""
Telemetry Model (TimescaleDB Hypertable)
Stores time-series battery sensor data
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from . import Base


class Telemetry(Base):
    """
    Battery telemetry time-series data (TimescaleDB hypertable)

    This table will be converted to a TimescaleDB hypertable partitioned by timestamp.
    Designed for high-frequency sensor data (5-second sampling = 17,280 records/day per battery)

    Attributes:
        id: UUID primary key
        battery_id: Foreign key to battery (indexed)
        timestamp: Measurement timestamp (hypertable partition key)
        voltage: Battery voltage (V) - typical range 11.5-14.5V
        current: Battery current (A) - negative=discharge, positive=charge
        temperature: Battery temperature (°C) - typical range 20-50°C
        internal_resistance: Internal resistance (mΩ) - increases with age
        soc_pct: State of Charge (%) - calculated or measured
        soh_pct: State of Health (%) - calculated from capacity fade
    """
    __tablename__ = "telemetry"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    battery_id: Mapped[str] = mapped_column(
        ForeignKey("battery.battery_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Battery identifier"
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Measurement timestamp (partition key)"
    )

    voltage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Battery voltage (V)"
    )

    current: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Battery current (A) - negative=discharge"
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Battery temperature (°C)"
    )

    internal_resistance: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Internal resistance (mΩ)"
    )

    soc_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="State of Charge (%)"
    )

    soh_pct: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="State of Health (%)"
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index(
            "ix_telemetry_battery_timestamp",
            "battery_id",
            "timestamp",
            postgresql_using="btree"
        ),
        Index(
            "ix_telemetry_timestamp_battery",
            "timestamp",
            "battery_id",
            postgresql_using="btree"
        ),
    )

    def __repr__(self) -> str:
        return f"<Telemetry(battery_id='{self.battery_id}', timestamp='{self.timestamp}', voltage={self.voltage:.2f}V, temp={self.temperature:.1f}°C)>"
