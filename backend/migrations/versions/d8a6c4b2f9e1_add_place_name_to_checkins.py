"""add place name to check-ins

Revision ID: d8a6c4b2f9e1
Revises: bc4fb32dae9f
Create Date: 2026-05-17 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d8a6c4b2f9e1"
down_revision = "bc4fb32dae9f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("check_in", sa.Column("place_name", sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column("check_in", "place_name")
