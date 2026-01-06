"""Add indexes for dashboard improvements

Revision ID: 002_dashboard_indexes
Revises: 001_initial
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_dashboard_indexes'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for dashboard filtering and analytics."""
    # Add indexes for extracted_data table to support filtering and analytics
    op.create_index(
        'idx_extracted_data_total_amount',
        'extracted_data',
        ['total_amount'],
        unique=False,
    )
    op.create_index(
        'idx_extracted_data_confidence',
        'extracted_data',
        ['extraction_confidence'],
        unique=False,
    )


def downgrade() -> None:
    """Remove dashboard indexes."""
    op.drop_index('idx_extracted_data_confidence', table_name='extracted_data')
    op.drop_index('idx_extracted_data_total_amount', table_name='extracted_data')

