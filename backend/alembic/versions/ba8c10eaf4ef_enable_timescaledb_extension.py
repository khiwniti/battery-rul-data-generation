"""enable timescaledb extension (skipped for Railway compatibility)

Revision ID: ba8c10eaf4ef
Revises: 001
Create Date: 2025-11-30 09:58:29.966691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba8c10eaf4ef'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enable TimescaleDB extension (skipped - not available on Railway)

    Note: This migration is kept in the chain for compatibility but does nothing.
    TimescaleDB features have been removed in favor of standard PostgreSQL.
    """
    pass


def downgrade() -> None:
    """No-op downgrade"""
    pass
