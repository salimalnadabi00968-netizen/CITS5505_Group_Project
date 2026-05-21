"""add check-in browse indexes

Revision ID: bc4fb32dae9f
Revises: 48aac9de597d
Create Date: 2026-05-15 19:24:39.594252

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'bc4fb32dae9f'
down_revision = '48aac9de597d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_check_in_category', 'check_in', ['category'], unique=False)
    op.create_index('ix_check_in_created_at', 'check_in', ['created_at'], unique=False)


def downgrade():
    op.drop_index('ix_check_in_created_at', table_name='check_in')
    op.drop_index('ix_check_in_category', table_name='check_in')
