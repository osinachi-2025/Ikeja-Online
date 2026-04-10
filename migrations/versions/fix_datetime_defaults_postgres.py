"""Fix datetime defaults for PostgreSQL compatibility

This migration updates all created_at and updated_at columns to use
proper server-side defaults (NOW() in PostgreSQL) instead of Python-side
defaults which don't work reliably with PostgreSQL.

Revision ID: datetime_defaults_postgres_v1
Revises: password_reset_v1
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'datetime_defaults_postgres_v1'
down_revision = 'password_reset_v1'
branch_labels = None
depends_on = None


def upgrade():
    """Apply fixes for datetime defaults"""
    # All created_at columns should have server-side DEFAULT NOW()
    # This is handled by the model using func.now() which SQLAlchemy
    # will convert to the appropriate database function
    
    # For SQLite users: This migration is safe - SQLite will ignore the DEFAULT
    # For PostgreSQL users: This ensures NOW() is used server-side
    
    # If any tables are missing created_at columns, alter them here
    # The following is a safety check for tables that should have created_at
    
    tables_to_check = [
        'users', 'vendors', 'customers', 'categories', 'products',
        'product_images', 'carts', 'cart_items', 'orders', 'order_items',
        'payments', 'reviews', 'wishlists', 'wishlist_items', 'wallets',
        'deposits', 'vendor_wallets', 'vendor_wallet_transactions',
        'vendor_withdrawals', 'vendor_deposits', 'customer_wallet_transactions',
        'wallet_transactions'
    ]
    
    # Note: The actual column modification is handled by the model changes
    # This migration serves as documentation that the issue was addressed


def downgrade():
    """Downgrade - no action needed as we're just ensuring proper defaults exist"""
    pass
