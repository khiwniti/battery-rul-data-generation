"""
Location Model
Represents data center locations across Thailand
"""
import uuid
from typing import List
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from . import Base, TimestampMixin


class Location(Base, TimestampMixin):
    """
    Data center location in Thailand

    Attributes:
        location_id: Unique identifier (e.g., DC-CNX-01)
        name: Display name (e.g., "Chiangmai DC 01")
        region: Thai region (northern, northeastern, central, eastern, southern)
        city: City name (e.g., "Chiangmai", "Bangkok")
        latitude: GPS coordinate
        longitude: GPS coordinate
        temp_offset_c: Regional temperature offset from baseline (-2.0 to +1.5°C)
        humidity_offset_pct: Regional humidity offset (0 to +15%)
        power_outage_frequency_per_year: Expected outage count (2-8/year)
    """
    __tablename__ = "location"

    location_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        nullable=False,
        comment="Location identifier (DC-CNX-01)"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Location display name"
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Thai region: northern, northeastern, central, eastern, southern"
    )

    city: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="City name"
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="GPS latitude"
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="GPS longitude"
    )

    temp_offset_c: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Regional temperature offset from baseline (°C)"
    )

    humidity_offset_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Regional humidity offset (%)"
    )

    power_outage_frequency_per_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Expected power outages per year"
    )

    # Relationships
    battery_systems: Mapped[List["BatterySystem"]] = relationship(
        "BatterySystem",
        back_populates="location",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Location(location_id='{self.location_id}', name='{self.name}', region='{self.region}')>"
