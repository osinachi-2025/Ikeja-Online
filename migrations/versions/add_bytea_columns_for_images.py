"""Add BYTEA columns for image storage

Revision ID: add_bytea_columns
Revises: e517eeaf1e67
Create Date: 2024-04-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_bytea_columns'
down_revision = 'e517eeaf1e67'
branch_labels = None
depends_on = None


def upgrade():
    """Add BYTEA columns to product_images and vendors tables"""
    
    # Add columns to product_images table
    op.add_column('product_images', 
        sa.Column('image_data', sa.LargeBinary(), nullable=True)
    )
    op.add_column('product_images',
        sa.Column('mime_type', sa.String(50), nullable=True, server_default='image/jpeg')
    )
    op.add_column('product_images',
        sa.Column('filename', sa.String(255), nullable=True)
    )
    
    # Make image_url nullable (since we now use image_data)
    op.alter_column('product_images', 'image_url',
        existing_type=sa.String(255),
        nullable=True,
        existing_nullable=False
    )
    
    # Add columns to vendors table
    op.add_column('vendors',
        sa.Column('logo_data', sa.LargeBinary(), nullable=True)
    )
    op.add_column('vendors',
        sa.Column('logo_mime_type', sa.String(50), nullable=True, server_default='image/jpeg')
    )


def downgrade():
    """Revert BYTEA columns"""
    
    # Remove columns from vendors table
    op.drop_column('vendors', 'logo_mime_type')
    op.drop_column('vendors', 'logo_data')
    
    # Revert image_url to NOT NULL (if no data migration occurred)
    op.alter_column('product_images', 'image_url',
        existing_type=sa.String(255),
        nullable=False,
        existing_nullable=True
    )
    
    # Remove columns from product_images table
    op.drop_column('product_images', 'filename')
    op.drop_column('product_images', 'mime_type')
    op.drop_column('product_images', 'image_data')
