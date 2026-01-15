"""Add resilient configuration models."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b6e2a7c1f4b9"
down_revision = "925498b15ac8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capability_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("inputs", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("outputs", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("guarantees", postgresql.JSONB(), nullable=True),
        sa.Column("constraints", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "processing_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("capability_contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["capability_contract_id"], ["capability_contracts.id"], name="fk_stage_contract"
        ),
    )
    op.create_index("idx_processing_stage_order", "processing_stages", ["order"])

    op.create_table(
        "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capability_contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["stage_id"], ["processing_stages.id"], name="fk_module_stage"),
        sa.ForeignKeyConstraint(
            ["capability_contract_id"], ["capability_contracts.id"], name="fk_module_contract"
        ),
    )
    op.create_index("idx_modules_stage", "modules", ["stage_id"])
    op.create_index("idx_modules_status", "modules", ["status"])

    op.create_table(
        "module_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
    )
    op.create_index("idx_module_config_status", "module_configurations", ["status"])

    op.create_table(
        "module_selections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("config_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("settings", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["config_id"], ["module_configurations.id"], name="fk_selection_config"),
        sa.ForeignKeyConstraint(["stage_id"], ["processing_stages.id"], name="fk_selection_stage"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_selection_module"),
    )
    op.create_index("idx_module_selection_stage", "module_selections", ["stage_id"])

    op.create_table(
        "fallback_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fallback_module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_conditions", postgresql.JSONB(), nullable=True),
        sa.Column("actions", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["stage_id"], ["processing_stages.id"], name="fk_fallback_stage"),
        sa.ForeignKeyConstraint(["fallback_module_id"], ["modules.id"], name="fk_fallback_module"),
    )

    op.create_table(
        "configuration_change_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("config_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("result", sa.String(length=60), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["config_id"], ["module_configurations.id"], name="fk_event_config"),
    )


def downgrade() -> None:
    op.drop_table("configuration_change_events")
    op.drop_table("fallback_policies")
    op.drop_index("idx_module_selection_stage", table_name="module_selections")
    op.drop_table("module_selections")
    op.drop_index("idx_module_config_status", table_name="module_configurations")
    op.drop_table("module_configurations")
    op.drop_index("idx_modules_status", table_name="modules")
    op.drop_index("idx_modules_stage", table_name="modules")
    op.drop_table("modules")
    op.drop_index("idx_processing_stage_order", table_name="processing_stages")
    op.drop_table("processing_stages")
    op.drop_table("capability_contracts")
