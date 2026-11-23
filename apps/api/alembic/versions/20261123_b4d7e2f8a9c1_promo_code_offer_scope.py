"""scope promo codes to a lesson offer

Revision ID: b4d7e2f8a9c1
Revises: a1b2c3d4e5f6
Create Date: 2026-11-23 10:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b4d7e2f8a9c1'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('promo_codes', sa.Column('offer_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f('fk_promo_codes_offer_id_individual_lesson_offers'),
        'promo_codes',
        'individual_lesson_offers',
        ['offer_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_index(op.f('ix_promo_codes_offer_id'), 'promo_codes', ['offer_id'], unique=False)
    # Неизвестно, на какой тариф действовали старые коды; применять их ко всем нельзя.
    op.execute('UPDATE promo_codes SET is_active = false WHERE offer_id IS NULL')


def downgrade() -> None:
    op.drop_index(op.f('ix_promo_codes_offer_id'), table_name='promo_codes')
    op.drop_constraint(
        op.f('fk_promo_codes_offer_id_individual_lesson_offers'),
        'promo_codes',
        type_='foreignkey',
    )
    op.drop_column('promo_codes', 'offer_id')
