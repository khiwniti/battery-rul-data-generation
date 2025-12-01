"""
Alert Model
Tracks battery health alerts and anomalies
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import Base, UUIDMixin, TimestampMixin


class AlertType(str, enum.Enum):
    """Alert type enumeration"""
    VOLTAGE_LOW = "voltage_low"
    VOLTAGE_HIGH = "voltage_high"
    TEMPERATURE_HIGH = "temperature_high"
    CURRENT_HIGH = "current_high"
    RIPPLE_HIGH = "ripple_high"
    RESISTANCE_DRIFT = "resistance_drift"
    SOH_DEGRADED = "soh_degraded"
    RUL_WARNING = "rul_warning"
    RUL_CRITICAL = "rul_critical"
    ANOMALY_DETECTED = "anomaly_detected"
    CONNECTION_LOST = "connection_lost"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(Base, UUIDMixin, TimestampMixin):
    """
    Alert Model

    Tracks battery health alerts, threshold violations, and ML-detected anomalies.
    Supports acknowledgment workflow for maintenance teams.
    """
    __tablename__ = "alert"

    # Alert identification
    alert_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-readable alert identifier (ALT-{battery_id}-{timestamp})",
    )

    # Battery relationship
    battery_id: Mapped[str] = mapped_column(
        ForeignKey("battery.battery_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Battery that triggered this alert",
    )

    # Alert details
    alert_type: Mapped[AlertType] = mapped_column(
        SQLEnum(AlertType, native_enum=False, length=30),
        nullable=False,
        index=True,
        comment="Type of alert",
    )

    severity: Mapped[AlertSeverity] = mapped_column(
        SQLEnum(AlertSeverity, native_enum=False, length=20),
        nullable=False,
        index=True,
        comment="Severity level: info, warning, critical",
    )

    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Human-readable alert message",
    )

    # Threshold details
    threshold_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Threshold value that was violated",
    )

    actual_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Actual measured value",
    )

    # Alert metadata
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the alert was triggered",
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the alert condition was resolved",
    )

    # Acknowledgment workflow
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the alert has been acknowledged by a user",
    )

    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the alert was acknowledged",
    )

    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User ID who acknowledged the alert",
    )

    acknowledgment_note: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Notes added during acknowledgment",
    )

    # Relationships
    battery: Mapped["Battery"] = relationship(
        "Battery",
        back_populates="alerts",
        lazy="selectin",
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_alert_battery_triggered", "battery_id", "triggered_at"),
        Index("ix_alert_severity_triggered", "severity", "triggered_at"),
        Index("ix_alert_active", "is_acknowledged", "resolved_at"),
        Index("ix_alert_type_severity", "alert_type", "severity"),
    )

    def __repr__(self) -> str:
        return (
            f"<Alert(alert_id={self.alert_id}, "
            f"battery_id={self.battery_id}, "
            f"type={self.alert_type.value}, "
            f"severity={self.severity.value}, "
            f"acknowledged={self.is_acknowledged})>"
        )

    @property
    def is_active(self) -> bool:
        """Check if alert is still active (not resolved)"""
        return self.resolved_at is None

    @property
    def is_pending(self) -> bool:
        """Check if alert is pending acknowledgment"""
        return not self.is_acknowledged and self.is_active
