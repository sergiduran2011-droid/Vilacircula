"""Add Google identity to citizen profiles.

Revision ID: 20261014184000
Revises: 20261004120000
Create Date: 2026-10-14 18:40:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261014184000"
down_revision = "20261004120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("profiles")}
    indexes = {index["name"] for index in inspector.get_indexes("profiles")}
    if "google_sub" not in columns:
        op.add_column("profiles", sa.Column("google_sub", sa.Text(), nullable=True))
    if "profiles_google_sub_idx" not in indexes:
        op.create_index("profiles_google_sub_idx", "profiles", ["google_sub"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("profiles")}
    columns = {column["name"] for column in inspector.get_columns("profiles")}
    if "profiles_google_sub_idx" in indexes:
        op.drop_index("profiles_google_sub_idx", table_name="profiles")
    if "google_sub" in columns:
        op.drop_column("profiles", "google_sub")
