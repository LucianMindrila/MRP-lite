"""add address to supplier

Revision ID: a1c4e7b2f9d0
Revises: 6d3c2d4d8c1f
Create Date: 2026-06-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c4e7b2f9d0'
down_revision = '6d3c2d4d8c1f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        batch_op.drop_column('address')
