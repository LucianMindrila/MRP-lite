"""add is_archived to product

Revision ID: f2a4c8d1e3b7
Revises: e9b1f3d2a8c4
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a4c8d1e3b7'
down_revision = 'e9b1f3d2a8c4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('is_archived', sa.Boolean(),
                  server_default=sa.false(), nullable=False))


def downgrade():
    op.drop_column('products', 'is_archived')
