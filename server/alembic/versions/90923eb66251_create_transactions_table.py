"""Create transactions table

Revision ID: 90923eb66251
Revises: dd3ccd919425
Create Date: 2024-02-02 15:36:35.566223

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "90923eb66251"
down_revision: Union[str, None] = "dd3ccd919425"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),  # Adjust as needed
        sa.Column("note", sa.String(), nullable=True),  # Adjust as needed
        sa.Column(
            "category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
    )


def downgrade():
    op.drop_table("transactions")
