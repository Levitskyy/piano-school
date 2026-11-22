"""confirmed booking slot uniqueness

Revision ID: a1b2c3d4e5f6
Revises: 7f3a1c9d2b4e
Create Date: 2026-11-22 16:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = '7f3a1c9d2b4e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        'uq_lesson_bookings_slot_id', 'lesson_bookings', type_='unique'
    )
    op.create_index(
        'uq_lesson_bookings_confirmed_slot_id',
        'lesson_bookings',
        ['slot_id'],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed'"),
    )


def downgrade() -> None:
    op.drop_index(
        'uq_lesson_bookings_confirmed_slot_id', table_name='lesson_bookings'
    )
    op.create_unique_constraint(
        'uq_lesson_bookings_slot_id', 'lesson_bookings', ['slot_id']
    )
