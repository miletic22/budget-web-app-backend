"""Create categories table

Revision ID: dd3ccd919425
Revises: d3b1b95487d8
Create Date: 2024-02-02 15:34:50.356083

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd3ccd919425"
down_revision: Union[str, None] = "d3b1b95487d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("reference_number", sa.Integer(), nullable=True),  # Adjust as needed
        sa.Column("name", sa.String(), nullable=True),  # Adjust as needed
        sa.Column("amount", sa.Integer(), nullable=True),  # Adjust as needed
        sa.Column(
            "budget_id", sa.Integer(), sa.ForeignKey("budgets.id"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"]),
    )


def downgrade() -> None:
    op.drop_constraint("categories_budget_id_fkey", "categories", type_="foreignkey")
    op.drop_table("categories")
