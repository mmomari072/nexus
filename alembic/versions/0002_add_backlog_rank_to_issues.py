"""Add backlog_rank field for prioritization.

Revision ID: 0002_add_backlog_rank
Revises:
Create Date: 2026-05-18 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_backlog_rank"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "issues",
        sa.Column(
            "backlog_rank",
            sa.Float(),
            nullable=True,
            comment="Fractional ordering key for backlog prioritization. Lower = higher priority.",
        ),
    )
    op.create_index("ix_issues_backlog_rank", "issues", ["backlog_rank"])

    # Initialize backlog_rank for existing rows: use issue_number * 1000.0 or rowid * 1000.0
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE issues
            SET backlog_rank = CAST(COALESCE(issue_number, rowid) AS REAL) * 1000.0
            WHERE backlog_rank IS NULL
        """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_issues_backlog_rank")
    op.drop_column("issues", "backlog_rank")
