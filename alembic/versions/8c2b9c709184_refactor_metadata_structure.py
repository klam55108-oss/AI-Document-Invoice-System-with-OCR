"""refactor metadata structure

Revision ID: 8c2b9c709184
Revises: 003_upload_metadata
Create Date: 2026-01-06 14:04:13.598011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8c2b9c709184'
down_revision: Union[str, Sequence[str], None] = '003_upload_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to invoices
    op.add_column('invoices', sa.Column('storage_path', sa.String(length=512), nullable=True))
    op.add_column('invoices', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('invoices', sa.Column('group', sa.String(length=100), nullable=True))
    op.add_column('invoices', sa.Column('job_id', sa.UUID(), nullable=True))
    
    # Migrate data: populate storage_path and group from file_path
    # e.g. 'grok/9.png' -> group='grok', storage_path='9.png' (or keep full path in storage_path if preferred)
    # The user suggested grok and jimeng are groups.
    op.execute("UPDATE invoices SET storage_path = file_path")
    op.execute("UPDATE invoices SET \"group\" = split_part(file_path, '/', 1) WHERE file_path LIKE '%/%'")
    
    # Make storage_path nullable=False AFTER population
    op.alter_column('invoices', 'storage_path', existing_type=sa.String(length=512), nullable=False)

    # Manage indexes
    op.drop_index(op.f('idx_extracted_data_invoice_id'), table_name='extracted_data')
    try:
        op.drop_index('idx_invoices_file_hash', table_name='invoices')
    except Exception:
        pass
    try:
        op.drop_index('idx_invoices_subfolder', table_name='invoices')
        op.drop_index('idx_invoices_upload_group', table_name='invoices')
        op.drop_index('idx_invoices_upload_metadata', table_name='invoices')
    except Exception:
        pass

    op.create_index(op.f('ix_invoices_category'), 'invoices', ['category'], unique=False)
    op.create_index(op.f('ix_invoices_file_hash'), 'invoices', ['file_hash'], unique=False)
    op.create_index(op.f('ix_invoices_group'), 'invoices', ['group'], unique=False)
    op.create_index(op.f('ix_invoices_job_id'), 'invoices', ['job_id'], unique=False)
    
    # Drop old column
    op.drop_column('invoices', 'file_path')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('invoices', sa.Column('file_path', sa.String(length=512), nullable=True))
    op.execute("UPDATE invoices SET file_path = storage_path")
    op.alter_column('invoices', 'file_path', existing_type=sa.String(length=512), nullable=False)
    
    op.drop_index(op.f('ix_invoices_job_id'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_group'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_file_hash'), table_name='invoices')
    op.drop_index(op.f('ix_invoices_category'), table_name='invoices')
    
    op.create_index(op.f('idx_invoices_upload_metadata'), 'invoices', ['upload_metadata'], unique=False, postgresql_using='gin')
    op.create_index(op.f('idx_invoices_upload_group'), 'invoices', [sa.literal_column("(upload_metadata ->> 'group'::text)")], unique=False)
    op.create_index(op.f('idx_invoices_subfolder'), 'invoices', [sa.literal_column("(upload_metadata ->> 'subfolder'::text)")], unique=False)
    op.create_index(op.f('idx_invoices_file_hash'), 'invoices', ['file_hash'], unique=False)
    op.create_index(op.f('idx_extracted_data_invoice_id'), 'extracted_data', ['invoice_id'], unique=False)

    op.drop_column('invoices', 'job_id')
    op.drop_column('invoices', 'group')
    op.drop_column('invoices', 'category')
    op.drop_column('invoices', 'storage_path')
    # ### end Alembic commands ###
