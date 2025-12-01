"""create master data tables

Revision ID: 001
Revises:
Create Date: 2025-11-30 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create master data tables: location, battery_system, string, battery, user
    """

    # Create location table
    op.create_table(
        'location',
        sa.Column('location_id', sa.String(length=20), nullable=False, comment='Location identifier (DC-CNX-01)'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Location display name'),
        sa.Column('region', sa.String(length=20), nullable=False, comment='Thai region: northern, northeastern, central, eastern, southern'),
        sa.Column('city', sa.String(length=50), nullable=False, comment='City name'),
        sa.Column('latitude', sa.Float(), nullable=False, comment='GPS latitude'),
        sa.Column('longitude', sa.Float(), nullable=False, comment='GPS longitude'),
        sa.Column('temp_offset_c', sa.Float(), nullable=False, server_default='0.0', comment='Regional temperature offset from baseline (°C)'),
        sa.Column('humidity_offset_pct', sa.Float(), nullable=False, server_default='0.0', comment='Regional humidity offset (%)'),
        sa.Column('power_outage_frequency_per_year', sa.Integer(), nullable=False, server_default='3', comment='Expected power outages per year'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('location_id')
    )

    # Create battery_system table
    op.create_table(
        'battery_system',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('system_id', sa.String(length=30), nullable=False, comment='System identifier (DC-CNX-01-UPS-01)'),
        sa.Column('location_id', sa.String(length=20), nullable=False, comment='Location foreign key'),
        sa.Column('system_type', sa.String(length=20), nullable=False, comment='System type: UPS, RECTIFIER, HYBRID'),
        sa.Column('manufacturer', sa.String(length=50), nullable=False, comment='Equipment manufacturer'),
        sa.Column('model', sa.String(length=50), nullable=False, comment='Equipment model number'),
        sa.Column('rated_capacity_kva', sa.Float(), nullable=False, comment='System rated capacity (kVA)'),
        sa.Column('strings_count', sa.Integer(), nullable=False, server_default='1', comment='Number of battery strings'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['location_id'], ['location.location_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system_id')
    )
    op.create_index('ix_battery_system_system_id', 'battery_system', ['system_id'])
    op.create_index('ix_battery_system_location_id', 'battery_system', ['location_id'])

    # Create string table
    op.create_table(
        'string',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('string_id', sa.String(length=40), nullable=False, comment='String identifier (DC-CNX-01-UPS-01-STR-01)'),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Battery system foreign key'),
        sa.Column('position', sa.Integer(), nullable=False, comment='String position within system'),
        sa.Column('batteries_count', sa.Integer(), nullable=False, server_default='24', comment='Number of batteries in series'),
        sa.Column('nominal_voltage_v', sa.Float(), nullable=False, server_default='288.0', comment='Nominal string voltage (V)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['system_id'], ['battery_system.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('string_id')
    )
    op.create_index('ix_string_string_id', 'string', ['string_id'])
    op.create_index('ix_string_system_id', 'string', ['system_id'])

    # Create battery table
    op.create_table(
        'battery',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('battery_id', sa.String(length=50), nullable=False, comment='Battery identifier (BAT-DC-CNX-01-UPS-01-STR-01-001)'),
        sa.Column('string_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Battery string foreign key'),
        sa.Column('serial_number', sa.String(length=30), nullable=False, comment='Manufacturer serial number'),
        sa.Column('position', sa.Integer(), nullable=False, comment='Position within string (1-24)'),
        sa.Column('manufacturer', sa.String(length=50), nullable=False, server_default='CSB', comment='Battery manufacturer'),
        sa.Column('model', sa.String(length=50), nullable=False, server_default='HX12-120', comment='Battery model number'),
        sa.Column('nominal_voltage_v', sa.Float(), nullable=False, server_default='12.0', comment='Nominal voltage per jar (V)'),
        sa.Column('nominal_capacity_ah', sa.Float(), nullable=False, server_default='120.0', comment='Nominal capacity (Ah)'),
        sa.Column('installed_date', sa.Date(), nullable=False, comment='Installation date'),
        sa.Column('warranty_months', sa.Integer(), nullable=False, server_default='60', comment='Warranty period (months)'),
        sa.Column('replaced_battery_id', sa.String(length=50), nullable=True, comment='Battery ID this unit replaced'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['string_id'], ['string.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('battery_id'),
        sa.UniqueConstraint('serial_number')
    )
    op.create_index('ix_battery_battery_id', 'battery', ['battery_id'])
    op.create_index('ix_battery_string_id', 'battery', ['string_id'])
    op.create_index('ix_battery_serial_number', 'battery', ['serial_number'])

    # Create user table
    op.create_table(
        'user',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(length=50), nullable=False, comment='User identifier (john.doe)'),
        sa.Column('username', sa.String(length=50), nullable=False, comment='Login username'),
        sa.Column('email', sa.String(length=100), nullable=False, comment='Email address'),
        sa.Column('hashed_password', sa.String(length=100), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('full_name', sa.String(length=100), nullable=False, comment='User\'s full name'),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='viewer', comment='User role: admin, engineer, viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Account active status'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='Last login timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_user_user_id', 'user', ['user_id'])
    op.create_index('ix_user_username', 'user', ['username'])
    op.create_index('ix_user_email', 'user', ['email'])


def downgrade() -> None:
    """Drop all master data tables"""
    op.drop_table('user')
    op.drop_table('battery')
    op.drop_table('string')
    op.drop_table('battery_system')
    op.drop_table('location')
