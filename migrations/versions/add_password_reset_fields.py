"""Add password reset fields to Users model

Revision ID: password_reset_v1
Revises: email_verification_v1
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'password_reset_v1'
down_revision = 'email_verification_v1'
branch_labels = None
depends_on = None


def upgrade():
    # Add password_reset_token column
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    # Add password_reset_expires column
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))


def downgrade():
    # Remove password_reset_expires column
    op.drop_column('users', 'password_reset_expires')
    # Remove password_reset_token column
    op.drop_column('users', 'password_reset_token')
