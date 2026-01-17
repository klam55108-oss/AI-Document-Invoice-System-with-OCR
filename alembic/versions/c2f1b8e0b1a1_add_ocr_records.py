"""Add OCR result and comparison tables.

Revision ID: c2f1b8e0b1a1
Revises: b6e2a7c1f4b9
Create Date: 2026-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c2f1b8e0b1a1"
down_revision: Union[str, None] = "b6e2a7c1f4b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add OCR results and comparisons."""
    op.create_table(
        "ocr_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("input_id", sa.String(length=512), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extracted_fields", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_ocr_results_input", "ocr_results", ["input_id"])
    op.create_index("idx_ocr_results_provider", "ocr_results", ["provider_id"])
    op.create_index("idx_ocr_results_status", "ocr_results", ["status"])

    op.create_table(
        "ocr_comparisons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("input_id", sa.String(length=512), nullable=False),
        sa.Column("provider_a_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_b_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["provider_a_result_id"],
            ["ocr_results.id"],
            name="fk_ocr_comparison_result_a",
        ),
        sa.ForeignKeyConstraint(
            ["provider_b_result_id"],
            ["ocr_results.id"],
            name="fk_ocr_comparison_result_b",
        ),
    )
    op.create_index("idx_ocr_comparisons_input", "ocr_comparisons", ["input_id"])
    op.create_index("idx_ocr_comparisons_created", "ocr_comparisons", ["created_at"])


def downgrade() -> None:
    """Drop OCR results and comparisons."""
    op.drop_index("idx_ocr_comparisons_created", table_name="ocr_comparisons")
    op.drop_index("idx_ocr_comparisons_input", table_name="ocr_comparisons")
    op.drop_table("ocr_comparisons")

    op.drop_index("idx_ocr_results_status", table_name="ocr_results")
    op.drop_index("idx_ocr_results_provider", table_name="ocr_results")
    op.drop_index("idx_ocr_results_input", table_name="ocr_results")
    op.drop_table("ocr_results")
