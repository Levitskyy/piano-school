"""Снапшот тарифа в заказе.

Revision ID: a7c3e9b1d4f2
Revises: f1a2b3c4d5e6
Create Date: 2026-11-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7c3e9b1d4f2"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "purchase_orders",
        sa.Column("offer_title", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "purchase_orders",
        sa.Column("lessons_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "purchase_orders",
        sa.Column("validity_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "purchase_orders",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("purchase_orders", "duration_minutes")
    op.drop_column("purchase_orders", "validity_days")
    op.drop_column("purchase_orders", "lessons_count")
    op.drop_column("purchase_orders", "offer_title")
