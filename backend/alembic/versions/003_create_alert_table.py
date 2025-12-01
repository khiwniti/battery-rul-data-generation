"""Create alert table

Revision ID: 003
Revises: 002
Create Date: 2025-11-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create alert table with indexes"""

    op.create_table(
        'alert',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('alert_id', sa.String(50), unique=True, nullable=False, index=True,
                  comment='Human-readable alert identifier (ALT-{battery_id}-{timestamp})'),
        sa.Column('battery_id', sa.String(50), sa.ForeignKey('battery.battery_id', ondelete='CASCADE'),
                  nullable=False, index=True, comment='Battery that triggered this alert'),

        # Alert details
        sa.Column('alert_type', sa.String(30), nullable=False, index=True, comment='Type of alert'),
        sa.Column('severity', sa.String(20), nullable=False, index=True,
                  comment='Severity level: info, warning, critical'),
        sa.Column('message', sa.String(500), nullable=False, comment='Human-readable alert message'),

        # Threshold details
        sa.Column('threshold_value', sa.Float(), nullable=True, comment='Threshold value that was violated'),
        sa.Column('actual_value', sa.Float(), nullable=True, comment='Actual measured value'),

        # Alert metadata
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False, index=True,
                  comment='When the alert was triggered'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True,
                  comment='When the alert condition was resolved'),

        # Acknowledgment workflow
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False, index=True,
                  comment='Whether the alert has been acknowledged by a user'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True,
                  comment='When the alert was acknowledged'),
        sa.Column('acknowledged_by', sa.String(100), nullable=True,
                  comment='User ID who acknowledged the alert'),
        sa.Column('acknowledgment_note', sa.String(1000), nullable=True,
                  comment='Notes added during acknowledgment'),

        # Standard timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create composite indexes for efficient queries
    op.create_index(
        'ix_alert_battery_triggered',
        'alert',
        ['battery_id', 'triggered_at'],
    )

    op.create_index(
        'ix_alert_severity_triggered',
        'alert',
        ['severity', 'triggered_at'],
    )

    op.create_index(
        'ix_alert_active',
        'alert',
        ['is_acknowledged', 'resolved_at'],
    )

    op.create_index(
        'ix_alert_type_severity',
        'alert',
        ['alert_type', 'severity'],
    )

    # Create trigger to auto-update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_alert_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER alert_updated_at_trigger
        BEFORE UPDATE ON alert
        FOR EACH ROW
        EXECUTE FUNCTION update_alert_updated_at();
    """)


def downgrade() -> None:
    """Drop alert table and related objects"""

    op.execute("DROP TRIGGER IF EXISTS alert_updated_at_trigger ON alert;")
    op.execute("DROP FUNCTION IF EXISTS update_alert_updated_at();")

    op.drop_index('ix_alert_type_severity', table_name='alert')
    op.drop_index('ix_alert_active', table_name='alert')
    op.drop_index('ix_alert_severity_triggered', table_name='alert')
    op.drop_index('ix_alert_battery_triggered', table_name='alert')

    op.drop_table('alert')
