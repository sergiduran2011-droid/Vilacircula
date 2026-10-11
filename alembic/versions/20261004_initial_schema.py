"""Initial schema for VilaCircula.

Revision ID: 20261004120000
Revises: 
Create Date: 2026-10-04 12:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20261004120000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("school", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="150"),
        sa.Column("contribution", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_profiles_username"), "profiles", ["username"], unique=True)

    op.create_table(
        "merchants",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("initials", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("is_demo", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("offer", sa.Text(), nullable=False),
        sa.Column("reward", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "cashier_users",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("merchant_id", sa.Text(), nullable=False),
        sa.Column("must_change_password", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("subject_type", sa.Text(), nullable=False),
        sa.Column("profile_id", sa.Text(), nullable=True),
        sa.Column("cashier_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["cashier_id"], ["cashier_users.id"]),
    )
    op.create_index("ix_auth_sessions_profile_id", "auth_sessions", ["profile_id"], unique=False)

    op.create_table(
        "login_attempts",
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("client_ip", sa.Text(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_started_at", sa.Text(), nullable=False),
        sa.Column("locked_until", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("username", "client_ip"),
    )

    op.create_table(
        "coupons",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("profile_id", sa.Text(), nullable=False),
        sa.Column("merchant_id", sa.Text(), nullable=True),
        sa.Column("reward_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("store", sa.Text(), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("redeemed_at", sa.Text(), nullable=True),
        sa.Column("redeemed_by", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["redeemed_by"], ["cashier_users.id"]),
    )
    op.create_index("ix_coupons_profile_id", "coupons", ["profile_id"], unique=False)

    op.create_table(
        "coupon_validations",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("coupon_id", sa.Text(), nullable=False),
        sa.Column("profile_id", sa.Text(), nullable=False),
        sa.Column("merchant_id", sa.Text(), nullable=True),
        sa.Column("cashier_id", sa.Text(), nullable=True),
        sa.Column("validated_at", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["cashier_id"], ["cashier_users.id"]),
    )
    op.create_index("ix_coupon_validations_cashier_id", "coupon_validations", ["cashier_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("target_type", sa.Text(), nullable=True),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "point_events",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("profile_id", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("merchant", sa.Text(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
    )
    op.create_index("ix_point_events_profile_created", "point_events", ["profile_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_point_events_profile_created", table_name="point_events")
    op.drop_table("point_events")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_coupon_validations_cashier_id", table_name="coupon_validations")
    op.drop_table("coupon_validations")
    op.drop_index("ix_coupons_profile_id", table_name="coupons")
    op.drop_table("coupons")
    op.drop_index("ix_auth_sessions_profile_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("cashier_users")
    op.drop_table("merchants")
    op.drop_index(op.f("ix_profiles_username"), table_name="profiles")
    op.drop_table("profiles")
    op.drop_table("login_attempts")
