"""catch up on manual schema changes

Revision ID: 8496979e0bb7
Revises: 7acfa5fb3d92
Create Date: 2026-05-08 13:13:17.791667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8496979e0bb7'
down_revision = '7acfa5fb3d92'
branch_labels = None
depends_on = None


def upgrade():
    # Baseline marker — schema already matches models via manual ALTER TABLE scripts.
    pass


def downgrade():
    pass
