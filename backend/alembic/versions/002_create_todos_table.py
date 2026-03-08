"""Create todos table

Revision ID: 002_create_todos
Revises: 704cc5700735
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "002_create_todos"
down_revision = "704cc5700735"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "todos",
        sa.Column("id", sa.String(8), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("completed", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("todos")
