"""create telemetry table

Revision ID: 002
Revises: ba8c10eaf4ef
Create Date: 2025-11-30 08:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = 'ba8c10eaf4ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create telemetry table with standard PostgreSQL indexing
    Note: TimescaleDB removed for Railway compatibility
    """

    # Create telemetry table
    op.create_table(
        'telemetry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('battery_id', sa.String(length=50), nullable=False, comment='Battery identifier'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, comment='Measurement timestamp'),
        sa.Column('voltage', sa.Float(), nullable=False, comment='Battery voltage (V)'),
        sa.Column('current', sa.Float(), nullable=True, comment='Battery current (A) - negative=discharge'),
        sa.Column('temperature', sa.Float(), nullable=False, comment='Battery temperature (°C)'),
        sa.Column('internal_resistance', sa.Float(), nullable=True, comment='Internal resistance (mΩ)'),
        sa.Column('soc_pct', sa.Float(), nullable=True, comment='State of Charge (%)'),
        sa.Column('soh_pct', sa.Float(), nullable=True, comment='State of Health (%)'),
        sa.ForeignKeyConstraint(['battery_id'], ['battery.battery_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for query performance
    op.create_index('ix_telemetry_battery_id', 'telemetry', ['battery_id'])
    op.create_index('ix_telemetry_timestamp', 'telemetry', ['timestamp'], postgresql_using='brin')  # BRIN index for time-series
    op.create_index('ix_telemetry_battery_timestamp', 'telemetry', ['battery_id', 'timestamp'])

    # Create materialized view for hourly statistics (manual refresh)
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_hourly AS
        SELECT
            battery_id,
            date_trunc('hour', timestamp) AS hour,
            AVG(voltage) AS voltage_avg,
            MIN(voltage) AS voltage_min,
            MAX(voltage) AS voltage_max,
            AVG(temperature) AS temperature_avg,
            MAX(temperature) AS temperature_max,
            AVG(internal_resistance) AS resistance_avg,
            COUNT(*) AS sample_count
        FROM telemetry
        GROUP BY battery_id, date_trunc('hour', timestamp);
    """)

    # Create index on the materialized view
    op.execute("""
        CREATE UNIQUE INDEX ix_telemetry_hourly_battery_hour
        ON telemetry_hourly (battery_id, hour);
    """)


def downgrade() -> None:
    """Drop telemetry table and materialized view"""

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS telemetry_hourly CASCADE;")

    # Drop telemetry table
    op.drop_table('telemetry')
