"""003 — feedback table

Stores question_hash (SHA-256, not the raw query) + thumbs rating.
No PII is stored — consistent with the privacy notice.

Revision ID: 003
Revises: 002
Create Date: 2025-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question_hash", sa.String(64), nullable=False, index=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feedback")
