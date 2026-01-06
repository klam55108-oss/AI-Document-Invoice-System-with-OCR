"""Add upload_metadata field to invoices table

Revision ID: 003_upload_metadata
Revises: 002_dashboard_indexes
Create Date: 2026-01-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_upload_metadata'
down_revision: Union[str, None] = '002_dashboard_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add upload_metadata JSONB column and indexes to invoices table."""
    # Add upload_metadata JSONB column
    op.add_column(
        'invoices',
        sa.Column('upload_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Add GIN index on upload_metadata for efficient JSONB queries
    op.create_index(
        'idx_invoices_upload_metadata',
        'invoices',
        ['upload_metadata'],
        unique=False,
        postgresql_using='gin',
    )
    
    # Add index on upload_metadata->>'subfolder' for filtering by subfolder
    op.execute(
        sa.text("CREATE INDEX idx_invoices_subfolder ON invoices ((upload_metadata->>'subfolder'))")
    )
    
    # Add index on upload_metadata->>'group' for filtering by group
    op.execute(
        sa.text("CREATE INDEX idx_invoices_upload_group ON invoices ((upload_metadata->>'group'))")
    )


def downgrade() -> None:
    """Remove upload_metadata column and indexes."""
    # Drop indexes
    op.drop_index('idx_invoices_upload_group', table_name='invoices')
    op.drop_index('idx_invoices_subfolder', table_name='invoices')
    op.drop_index('idx_invoices_upload_metadata', table_name='invoices')
    
    # Drop column
    op.drop_column('invoices', 'upload_metadata')

