"""Initial schema: invoices, extracted_data, validation_results, processing_jobs

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    # pgqueuer extension not available in current PostgreSQL image - enable when installed
    # op.execute('CREATE EXTENSION IF NOT EXISTS pgqueuer;')
    
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_name', sa.String(256), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.String(10), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('processing_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('encrypted_file_path', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index('idx_invoices_file_hash', 'invoices', ['file_hash'])
    op.create_index('idx_invoices_status', 'invoices', ['processing_status'])
    op.create_index('idx_invoices_created_at', 'invoices', ['created_at'])
    
    # Create extracted_data table
    op.create_table(
        'extracted_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_name', sa.String(256), nullable=True),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('tax_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True, server_default='USD'),
        sa.Column('line_items', postgresql.JSONB(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extraction_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('invoice_id'),
    )
    op.create_index('idx_extracted_data_invoice_id', 'extracted_data', ['invoice_id'])
    op.create_index('idx_extracted_data_vendor', 'extracted_data', ['vendor_name'])
    op.create_index('idx_extracted_data_date', 'extracted_data', ['invoice_date'])
    
    # Create validation_results table
    op.create_table(
        'validation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_name', sa.String(100), nullable=False),
        sa.Column('rule_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('expected_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('actual_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('tolerance', sa.Numeric(10, 4), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_validation_results_invoice_id', 'validation_results', ['invoice_id'])
    op.create_index('idx_validation_results_status', 'validation_results', ['status'])
    op.create_index('idx_validation_results_rule', 'validation_results', ['rule_name'])
    
    # Create processing_jobs table
    op.create_table(
        'processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('execution_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('job_metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_processing_jobs_invoice_id', 'processing_jobs', ['invoice_id'])
    op.create_index('idx_processing_jobs_status', 'processing_jobs', ['status'])
    op.create_index('idx_processing_jobs_type', 'processing_jobs', ['job_type'])


def downgrade() -> None:
    op.drop_table('processing_jobs')
    op.drop_table('validation_results')
    op.drop_table('extracted_data')
    op.drop_table('invoices')
    # op.execute('DROP EXTENSION IF EXISTS pgqueuer;')
    op.execute('DROP EXTENSION IF EXISTS vector;')

