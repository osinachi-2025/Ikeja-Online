"""
Migration script to migrate existing filesystem images to PostgreSQL BYTEA storage.

Usage: python migrate_images_to_db.py

This script will:
1. Read all image files from static/uploads/products/
2. Convert them to binary data
3. Store them in the database
4. Optionally delete the old files after backup
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Product_Images, Products, Vendors
from werkzeug.utils import secure_filename


def get_mime_type(filename):
    """Determine MIME type from filename extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpeg'
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def migrate_product_images():
    """Migrate product images from filesystem to database"""
    print("Starting product images migration...")
    
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'products')
    
    if not os.path.exists(upload_folder):
        print(f"Upload folder not found: {upload_folder}")
        return
    
    migrated_count = 0
    error_count = 0
    
    with app.app_context():
        # Get all product images with image_url but no image_data
        images = Product_Images.query.filter(
            Product_Images.image_url.isnot(None),
            Product_Images.image_data.is_(None)
        ).all()
        
        print(f"Found {len(images)} images to migrate")
        
        for idx, image in enumerate(images, 1):
            try:
                # Extract filename from image_url
                # image_url format: /static/uploads/products/filename
                filename = os.path.basename(image.image_url)
                filepath = os.path.join(upload_folder, filename)
                
                if not os.path.exists(filepath):
                    print(f"[{idx}/{len(images)}] ❌ File not found: {filename}")
                    error_count += 1
                    continue
                
                # Read file as binary
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                
                # Update image record with binary data
                image.image_data = image_data
                image.mime_type = get_mime_type(filename)
                image.filename = secure_filename(filename)
                
                db.session.commit()
                
                print(f"[{idx}/{len(images)}] ✓ Migrated: {filename}")
                migrated_count += 1
                
            except Exception as e:
                db.session.rollback()
                print(f"[{idx}/{len(images)}] ❌ Error migrating {image.image_url}: {str(e)}")
                error_count += 1
                continue
        
        print(f"\nProduct images migration complete!")
        print(f"  ✓ Successfully migrated: {migrated_count}")
        print(f"  ❌ Errors: {error_count}")


def migrate_vendor_logos():
    """Migrate vendor logos from filesystem to database"""
    print("\nStarting vendor logos migration...")
    
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'vendors')
    
    if not os.path.exists(upload_folder):
        print(f"Upload folder not found: {upload_folder}")
        return
    
    migrated_count = 0
    error_count = 0
    
    with app.app_context():
        # Get all vendors with logo_url but no logo_data
        vendors = Vendors.query.filter(
            Vendors.logo_url.isnot(None),
            Vendors.logo_data.is_(None)
        ).all()
        
        print(f"Found {len(vendors)} vendor logos to migrate")
        
        for idx, vendor in enumerate(vendors, 1):
            try:
                # Extract filename from logo_url
                # logo_url format: /static/uploads/vendors/filename
                filename = os.path.basename(vendor.logo_url)
                filepath = os.path.join(upload_folder, filename)
                
                if not os.path.exists(filepath):
                    print(f"[{idx}/{len(vendors)}] ❌ File not found: {filename}")
                    error_count += 1
                    continue
                
                # Read file as binary
                with open(filepath, 'rb') as f:
                    logo_data = f.read()
                
                # Update vendor record with binary data
                vendor.logo_data = logo_data
                vendor.logo_mime_type = get_mime_type(filename)
                
                db.session.commit()
                
                print(f"[{idx}/{len(vendors)}] ✓ Migrated: {filename}")
                migrated_count += 1
                
            except Exception as e:
                db.session.rollback()
                print(f"[{idx}/{len(vendors)}] ❌ Error migrating logo for vendor {vendor.id}: {str(e)}")
                error_count += 1
                continue
        
        print(f"\nVendor logos migration complete!")
        print(f"  ✓ Successfully migrated: {migrated_count}")
        print(f"  ❌ Errors: {error_count}")


def backup_original_files():
    """Create a backup of original files before migration"""
    print("\nCreating backup of original files...")
    
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup products
    products_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'products')
    if os.path.exists(products_dir):
        import shutil
        backup_products = os.path.join(backup_dir, 'products_backup')
        if os.path.exists(backup_products):
            shutil.rmtree(backup_products)
        shutil.copytree(products_dir, backup_products)
        print(f"✓ Backed up product images to: {backup_products}")
    
    # Backup vendors
    vendors_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'vendors')
    if os.path.exists(vendors_dir):
        import shutil
        backup_vendors = os.path.join(backup_dir, 'vendors_backup')
        if os.path.exists(backup_vendors):
            shutil.rmtree(backup_vendors)
        shutil.copytree(vendors_dir, backup_vendors)
        print(f"✓ Backed up vendor logos to: {backup_vendors}")


if __name__ == '__main__':
    print("=" * 60)
    print("Image Migration Script - Filesystem to PostgreSQL BYTEA")
    print("=" * 60)
    
    # Create backup
    try:
        backup_original_files()
    except Exception as e:
        print(f"Warning: Could not create backup: {str(e)}")
    
    # Migrate images
    migrate_product_images()
    
    # Migrate logos
    migrate_vendor_logos()
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Verify that images are displaying correctly")
    print("2. Check the database for binary data in BYTEA columns")
    print("3. Once verified, you can optionally delete the filesystem files:")
    print("   rm -rf static/uploads/products/*")
    print("   rm -rf static/uploads/vendors/*")
    print("   (Backup files are stored in static/uploads/backup/)")
