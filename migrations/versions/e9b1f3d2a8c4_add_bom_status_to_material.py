"""add bom_status to material

Revision ID: e9b1f3d2a8c4
Revises: c6a64c110b8f
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa

revision = 'e9b1f3d2a8c4'
down_revision = 'c6a64c110b8f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('materials', sa.Column('bom_status', sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column('materials', 'bom_status')
