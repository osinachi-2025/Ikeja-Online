# Quick Setup Guide - BYTEA Image Storage

## ⚡ 5-Minute Setup

### Step 1: Apply Database Migration
```bash
# Activate virtual environment (if not already)
source ikeja-online/Scripts/activate  # Linux/Mac
# or
ikeja-online\Scripts\Activate.ps1  # Windows PowerShell

# Apply the migration
flask db upgrade
```

### Step 2: (Optional) Migrate Existing Images
If you have existing images on the filesystem:
```bash
python migrate_images_to_db.py
```

This will:
- ✓ Read all image files from `static/uploads/`
- ✓ Convert to binary and store in database
- ✓ Create backup in `static/uploads/backup/`
- ✓ Take 2-5 minutes depending on image count

### Step 3: Test Image Upload
1. Open your vendor dashboard
2. Upload a new product with images
3. Images should be stored in database (not filesystem)
4. Verify in API response: images now use `/api/product-image/<id>` URLs

### Step 4: Deploy to Render
```bash
# Push to your repository
git add .
git commit -m "Add BYTEA image storage for Render PostgreSQL"
git push origin main

# Render will automatically:
# 1. Build the app
# 2. Run migrations
# 3. Deploy with new image storage
```

---

## ✅ Verification Checklist

### Local Testing
- [ ] Database migration completed successfully
- [ ] New product images upload and display
- [ ] Vendor logo changes work
- [ ] Old images (if any) migrated correctly
- [ ] API endpoints return correct image data

### Production (Render)
- [ ] Environment variable `DATABASE_URL` is set
- [ ] PostgreSQL database is accessible
- [ ] Migrations ran without errors
- [ ] Images upload and display correctly
- [ ] Check Render logs for any errors

### Database Check
```sql
-- Verify columns exist
\d product_images
\d vendors

-- Check for migrated data
SELECT COUNT(*) FROM product_images WHERE image_data IS NOT NULL;
SELECT COUNT(*) FROM vendors WHERE logo_data IS NOT NULL;
```

---

## 📊 Key Changes Summary

### What Changed
| Item | Before | After |
|------|--------|-------|
| Image Storage | Filesystem `/static/uploads/` | PostgreSQL BYTEA |
| Image URL | `/static/uploads/products/file.jpg` | `/api/product-image/42` |
| Database Size | ~10MB (metadata only) | +Size of all images |
| Render Compatibility | ⚠️ Ephemeral filesystem | ✅ Persistent database |
| Backup Strategy | Manual file backup | ✓ With DB backup |

### No Breaking Changes
- ✓ Old image URLs still work (fallback)
- ✓ Frontend needs no changes (API endpoints handle it)
- ✓ Backward compatible code
- ✓ Gradual migration possible

---

## 🆘 Quick Troubleshooting

### Images not uploading?
```
1. Check: flask db status
2. Verify BYTEA columns exist: SELECT image_data FROM product_images LIMIT 1
3. Check app logs for errors
4. Ensure multipart/form-data support in API
```

### Old images not migrated?
```bash
# Re-run migration script
python migrate_images_to_db.py

# Check backup exists
ls -la static/uploads/backup/
```

### Images show broken on Render?
```
1. Check: https://your-app.render.com/api/product-image/1
2. Verify DATABASE_URL environment variable
3. Check PostgreSQL connection
4. View Render logs for errors
```

### Database too large?
```sql
-- Check image storage usage
SELECT 
    COUNT(*) as total_images,
    SUM(pg_column_size(image_data)) / (1024.0 * 1024.0) as size_mb
FROM product_images;
```

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `models.py` | Updated with BYTEA columns |
| `app.py` | New image retrieval endpoints |
| `BYTEA_IMAGE_STORAGE.md` | Full documentation |
| `migrate_images_to_db.py` | Migration script for existing images |
| `migrations/versions/add_bytea_columns_for_images.py` | Database migration |

---

## 🔗 API Endpoints Reference

### Upload Images
```bash
POST /api/add-product
Content-Type: multipart/form-data

# Images stored as BYTEA automatically
```

### Retrieve Image
```bash
GET /api/product-image/{image_id}
# Returns: Binary image data with correct Content-Type

# HTML:
<img src="/api/product-image/42" />
```

### Get All Product Images
```bash
GET /api/product-images/{product_id}
# Returns: JSON list with image metadata
```

### Get Vendor Logo
```bash
GET /api/vendor-logo/{vendor_id}
# Returns: Binary logo data

# HTML:
<img src="/api/vendor-logo/5" />
```

---

## 💡 Tips for Success

1. **Start Local** - Test migration on your local database first
2. **Backup** - Migration script creates backup automatically
3. **Monitor** - Check database size after migration
4. **Cache** - Consider adding cache headers for performance
5. **Monitor Queries** - Watch for slow image queries in Render

---

## 📞 Need Help?

### Check Logs
```bash
# Local debug
FLASK_ENV=development FLASK_DEBUG=1 python app.py

# Render logs
# https://render.com/docs/viewing-logs
```

### Verify Setup
```python
# In Python shell
from app import app, db
from models import Product_Images
with app.app_context():
    img = Product_Images.query.first()
    print(f"Image has data: {bool(img.image_data)}")
    print(f"MIME type: {img.mime_type}")
```

---

## 🎉 Done!

Your app is now configured to use PostgreSQL BYTEA for image storage.

**Next:** Upload a new product and verify images are served from the database!
