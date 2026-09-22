"""add student projects JSON field

Revision ID: 7f2a1e9d4c8b
Revises: 3b83150ce9e9
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f2a1e9d4c8b"
down_revision: Union[str, Sequence[str], None] = "3b83150ce9e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("students", sa.Column("projects", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("students", "projects")
