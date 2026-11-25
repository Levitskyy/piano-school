"""Поддержка Prodamus в заказах.

Revision ID: f1a2b3c4d5e6
Revises: d4e5f6a7b8c9
Create Date: 2026-11-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "purchase_orders",
        sa.Column(
            "provider",
            sa.String(length=16),
            nullable=False,
            server_default="yookassa",
        ),
    )
    op.alter_column("purchase_orders", "provider", server_default=None)
    op.create_index("ix_purchase_orders_provider", "purchase_orders", ["provider"])

    op.alter_column(
        "purchase_orders",
        "yookassa_payment_id",
        new_column_name="provider_payment_id",
    )


def downgrade() -> None:
    op.alter_column(
        "purchase_orders",
        "provider_payment_id",
        new_column_name="yookassa_payment_id",
    )
    op.drop_index("ix_purchase_orders_provider", table_name="purchase_orders")
    op.drop_column("purchase_orders", "provider")
