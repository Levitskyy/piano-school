"""reserve promo codes for pending orders

Revision ID: 7f3a1c9d2b4e
Revises: 5c1d2e3f4a5b
Create Date: 2026-11-22 18:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '7f3a1c9d2b4e'
down_revision: str | Sequence[str] | None = '5c1d2e3f4a5b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('promo_codes', sa.Column('reserved_order_id', sa.Uuid(), nullable=True))
    op.create_index(
        op.f('ix_promo_codes_reserved_order_id'),
        'promo_codes',
        ['reserved_order_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_promo_codes_reserved_order_id'), table_name='promo_codes')
    op.drop_column('promo_codes', 'reserved_order_id')
