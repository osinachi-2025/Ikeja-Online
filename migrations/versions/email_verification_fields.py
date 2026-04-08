"""Add email verification fields to Users model

Revision ID: email_verification_v1
Revises: 
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'email_verification_v1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add email_verified column to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    # Add email_verified_at column to users table
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove email_verified_at column from users table
    op.drop_column('users', 'email_verified_at')
    # Remove email_verified column from users table
    op.drop_column('users', 'email_verified')
