"""promo codes and purchase orders

Revision ID: 5c1d2e3f4a5b
Revises: 9b144360886d
Create Date: 2026-11-22 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '5c1d2e3f4a5b'
down_revision: str | Sequence[str] | None = '9b144360886d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('promo_codes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_promo_codes'))
    )
    op.create_index(op.f('ix_promo_codes_code'), 'promo_codes', ['code'], unique=True)
    op.create_table('purchase_orders',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('offer_id', sa.Uuid(), nullable=False),
    sa.Column('slot_id', sa.Uuid(), nullable=False),
    sa.Column('promo_code_id', sa.Uuid(), nullable=True),
    sa.Column('price_minor', sa.Integer(), nullable=False),
    sa.Column('discount_minor', sa.Integer(), nullable=False),
    sa.Column('total_minor', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('yookassa_payment_id', sa.String(length=64), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['offer_id'], ['individual_lesson_offers.id'], name=op.f('fk_purchase_orders_offer_id_individual_lesson_offers'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], name=op.f('fk_purchase_orders_promo_code_id_promo_codes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['slot_id'], ['lesson_slots.id'], name=op.f('fk_purchase_orders_slot_id_lesson_slots'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_purchase_orders_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_purchase_orders')),
    sa.UniqueConstraint('yookassa_payment_id', name=op.f('uq_purchase_orders_yookassa_payment_id'))
    )
    op.create_index(op.f('ix_purchase_orders_offer_id'), 'purchase_orders', ['offer_id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_promo_code_id'), 'purchase_orders', ['promo_code_id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_slot_id'), 'purchase_orders', ['slot_id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_status'), 'purchase_orders', ['status'], unique=False)
    op.create_index(op.f('ix_purchase_orders_user_id'), 'purchase_orders', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_purchase_orders_user_id'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_status'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_slot_id'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_promo_code_id'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_offer_id'), table_name='purchase_orders')
    op.drop_table('purchase_orders')
    op.drop_index(op.f('ix_promo_codes_code'), table_name='promo_codes')
    op.drop_table('promo_codes')
