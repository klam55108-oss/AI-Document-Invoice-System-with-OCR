"""add_per_field_confidence_tracking

Revision ID: 925498b15ac8
Revises: 8c2b9c709184
Create Date: 2026-01-07 13:08:59.891913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '925498b15ac8'
down_revision: Union[str, Sequence[str], None] = '8c2b9c709184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add per-field confidence tracking and metadata columns."""
    
    # T006: Add 7 confidence columns to extracted_data table
    op.add_column('extracted_data', 
        sa.Column('vendor_name_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('invoice_number_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('invoice_date_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('total_amount_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('subtotal_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('tax_amount_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('currency_confidence', sa.Numeric(3, 2), nullable=True))
    
    # T007-T008: Add JSONB metadata columns to invoices table
    op.add_column('invoices', sa.Column('file_preview_metadata', postgresql.JSONB(), nullable=True))
    op.add_column('invoices', sa.Column('processing_metadata', postgresql.JSONB(), nullable=True))
    
    # T009: Add CHECK constraints for confidence range validation (0.0-1.0)
    op.create_check_constraint(
        'check_vendor_conf_range',
        'extracted_data',
        'vendor_name_confidence IS NULL OR (vendor_name_confidence >= 0 AND vendor_name_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_invoice_num_conf_range',
        'extracted_data',
        'invoice_number_confidence IS NULL OR (invoice_number_confidence >= 0 AND invoice_number_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_invoice_date_conf_range',
        'extracted_data',
        'invoice_date_confidence IS NULL OR (invoice_date_confidence >= 0 AND invoice_date_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_total_conf_range',
        'extracted_data',
        'total_amount_confidence IS NULL OR (total_amount_confidence >= 0 AND total_amount_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_subtotal_conf_range',
        'extracted_data',
        'subtotal_confidence IS NULL OR (subtotal_confidence >= 0 AND subtotal_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_tax_conf_range',
        'extracted_data',
        'tax_amount_confidence IS NULL OR (tax_amount_confidence >= 0 AND tax_amount_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_currency_conf_range',
        'extracted_data',
        'currency_confidence IS NULL OR (currency_confidence >= 0 AND currency_confidence <= 1)'
    )
    
    # T010-T012: Create indexes for filtering and sorting by confidence
    op.create_index('idx_extracted_data_vendor_conf', 'extracted_data', ['vendor_name_confidence'])
    op.create_index('idx_extracted_data_invoice_num_conf', 'extracted_data', ['invoice_number_confidence'])
    op.create_index('idx_extracted_data_total_conf', 'extracted_data', ['total_amount_confidence'])
    
    # T013: Create expression index for low-confidence filtering
    op.execute("""
        CREATE INDEX idx_extracted_data_low_confidence ON extracted_data(
            (COALESCE(vendor_name_confidence, 0) + COALESCE(invoice_number_confidence, 0) + COALESCE(total_amount_confidence, 0))
        )
    """)
    
    # T014: Create index for batch ID lookup
    op.execute("""
        CREATE INDEX idx_invoices_batch_id ON invoices((processing_metadata->>'parallel_batch_id'))
    """)


def downgrade() -> None:
    """Downgrade schema: Remove per-field confidence tracking and metadata columns."""
    
    # Drop indexes
    op.drop_index('idx_invoices_batch_id', 'invoices')
    op.drop_index('idx_extracted_data_low_confidence', 'extracted_data')
    op.drop_index('idx_extracted_data_total_conf', 'extracted_data')
    op.drop_index('idx_extracted_data_invoice_num_conf', 'extracted_data')
    op.drop_index('idx_extracted_data_vendor_conf', 'extracted_data')
    
    # Drop constraints
    op.drop_constraint('check_currency_conf_range', 'extracted_data')
    op.drop_constraint('check_tax_conf_range', 'extracted_data')
    op.drop_constraint('check_subtotal_conf_range', 'extracted_data')
    op.drop_constraint('check_total_conf_range', 'extracted_data')
    op.drop_constraint('check_invoice_date_conf_range', 'extracted_data')
    op.drop_constraint('check_invoice_num_conf_range', 'extracted_data')
    op.drop_constraint('check_vendor_conf_range', 'extracted_data')
    
    # Drop columns from invoices
    op.drop_column('invoices', 'processing_metadata')
    op.drop_column('invoices', 'file_preview_metadata')
    
    # Drop columns from extracted_data
    op.drop_column('extracted_data', 'currency_confidence')
    op.drop_column('extracted_data', 'tax_amount_confidence')
    op.drop_column('extracted_data', 'subtotal_confidence')
    op.drop_column('extracted_data', 'total_amount_confidence')
    op.drop_column('extracted_data', 'invoice_date_confidence')
    op.drop_column('extracted_data', 'invoice_number_confidence')
    op.drop_column('extracted_data', 'vendor_name_confidence')
