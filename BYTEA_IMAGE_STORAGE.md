# PostgreSQL BYTEA Image Storage Setup

## Overview
This document explains how your Ikeja Online backend has been configured to store product images and vendor logos as binary data (BYTEA) in PostgreSQL instead of storing them on the filesystem.

### Benefits of BYTEA Storage
✅ **Render-friendly** - No dependency on ephemeral filesystem  
✅ **Database backup** - Images backed up with database  
✅ **Scalable** - Works with containerized deployment  
✅ **Secure** - Binary data is encrypted in transit  
✅ **Centralized** - All data in one PostgreSQL database  

---

## Architecture

### Database Models

#### Product_Images Table
```python
- id (Integer, PK)
- product_id (Foreign Key)
- image_url (String, optional) - Kept for backward compatibility
- image_data (LargeBinary/BYTEA) - NEW: Binary image data
- mime_type (String) - Image MIME type (e.g., image/jpeg)
- filename (String) - Original filename with extension
- is_primary (Boolean) - Whether this is the primary image
- created_at (DateTime)
```

#### Vendors Table (Updated)
```python
- logo_url (String, optional) - Kept for backward compatibility
- logo_data (LargeBinary/BYTEA) - NEW: Binary logo data
- logo_mime_type (String) - Logo MIME type
```

---

## API Endpoints

### 1. Upload Product Images
**POST** `/api/add-product`
- Still uses `multipart/form-data` with file uploads
- Images are automatically converted to binary and stored in BYTEA
- Returns product_id on success

### 2. Retrieve Product Image
**GET** `/api/product-image/<image_id>`
- Returns binary image data with correct Content-Type header
- Automatically serves as `image/jpeg`, `image/png`, etc.
- Example: `<img src="/api/product-image/42" />`

### 3. Get All Images for Product
**GET** `/api/product-images/<product_id>`
- Returns JSON list of all images for a product
- Response format:
```json
{
  "images": [
    {
      "id": 42,
      "url": "/api/product-image/42",
      "filename": "gadget-1-0.jpeg",
      "mime_type": "image/jpeg",
      "is_primary": true,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### 4. Get Vendor Logo
**GET** `/api/vendor-logo/<vendor_id>`
- Returns binary logo data
- Automatically serves with correct Content-Type
- Example: `<img src="/api/vendor-logo/5" />`

---

## Setup Instructions

### Step 1: Update Database Schema
You'll need to create a migration to add the BYTEA columns:

```bash
# Generate migration
flask db migrate -m "Add BYTEA columns for image storage"

# Apply migration
flask db upgrade
```

Or manually run SQL:
```sql
-- Product Images
ALTER TABLE product_images 
ADD COLUMN image_data BYTEA,
ADD COLUMN mime_type VARCHAR(50) DEFAULT 'image/jpeg',
ADD COLUMN filename VARCHAR(255),
ALTER COLUMN image_url DROP NOT NULL;

-- Vendors
ALTER TABLE vendors
ADD COLUMN logo_data BYTEA,
ADD COLUMN logo_mime_type VARCHAR(50) DEFAULT 'image/jpeg';
```

### Step 2: Migrate Existing Images (Optional)
If you have existing images on the filesystem:

```bash
python migrate_images_to_db.py
```

This script will:
- ✓ Read all existing image files
- ✓ Convert them to binary
- ✓ Store in database BYTEA columns
- ✓ Create backup in `static/uploads/backup/`

### Step 3: Update Frontend
Images are automatically served through the API endpoints. Update your image HTML:

**Old (filesystem):**
```html
<img src="/static/uploads/products/product-1-image.jpg" />
```

**New (database):**
```html
<img src="/api/product-image/42" />
```

The API endpoints are already configured to return the correct image data.

### Step 4: Environment Configuration
Ensure your PostgreSQL connection string is set:

```bash
# .env file
DATABASE_URL=postgresql://user:password@host:port/database
```

For Render:
```
postgresql://ikeja_user:password@your-render-db.onrender.com:5432/ikeja_online
```

---

## Rendering Images in Frontend

### JavaScript Example
```javascript
// Get product and display images
fetch('/api/product-images/42')
  .then(r => r.json())
  .then(data => {
    data.images.forEach(img => {
      const imgElement = document.createElement('img');
      imgElement.src = img.url; // /api/product-image/42
      imgElement.alt = img.filename;
      container.appendChild(imgElement);
    });
  });
```

### HTML Direct Link
```html
<!-- Primary image -->
<img src="/api/product-image/42" alt="Product Image">

<!-- Vendor logo -->
<img src="/api/vendor-logo/5" alt="Store Logo">
```

---

## File Upload Flow

### Current Implementation
1. **Upload** → File received as multipart/form-data
2. **Processing** → `save_image_to_db()` function converts to binary
3. **Storage** → Binary data stored in BYTEA column
4. **Serving** → `/api/product-image/<id>` endpoint retrieves and serves with correct MIME type

### File Size Limits
- Max file size: 5MB (configurable in `app.py`)
- Supported formats: PNG, JPG, JPEG, GIF, WebP

---

## Backward Compatibility

The system maintains backward compatibility:
- Old `image_url` column still exists
- New `image_data` column is primary
- Image retrieval endpoints support both:
  1. First checks for `image_data` (BYTEA)
  2. Falls back to `image_url` (for existing data)

This allows a gradual migration without breaking existing functionality.

---

## Database Storage Considerations

### BYTEA vs URL Storage
| Aspect | BYTEA | URL |
|--------|-------|-----|
| Storage Location | Database | Filesystem |
| Backup | ✓ With DB | ✗ Separate |
| Render Compatible | ✓ Yes | ✗ Ephemeral |
| Query Speed | ○ Slower | ✓ Faster |
| Redundancy | ✓ DB replicas | ✗ Need separate |
| Max Size | ~2GB/column | Filesystem limit |

### Performance Optimization
For best performance with images:
1. **Index by product_id** (included in models)
2. **Lazy load** images in lists
3. **Cache** frequently accessed images
4. **Compress** large images before upload

---

## Troubleshooting

### Issue: Images not displaying
```
Check:
1. Run migration: python migrate_images_to_db.py
2. Verify BYTEA columns exist: SELECT image_data FROM product_images LIMIT 1;
3. Check API endpoint: curl http://localhost:5000/api/product-image/1
4. Verify image ID exists
```

### Issue: Out of memory on image upload
```
Solution:
- Reduce MAX_FILE_SIZE in app.py
- Compress images before upload
- Implement image resizing on server
```

### Issue: Images work locally but not on Render
```
Check:
1. DATABASE_URL environment variable set
2. PostgreSQL connection string correct
3. BYTEA columns created in production database
4. Run migration on production database
```

### Issue: Slow image loading
```
Solution:
1. Add database indexes
2. Implement image caching headers
3. Use CDN for images
4. Resize images to smaller dimensions
```

---

## Monitoring

### Check Storage Usage
```sql
-- Product images size
SELECT 
    SUM(pg_column_size(image_data)) / (1024.0 * 1024.0) AS size_mb
FROM product_images;

-- Vendor logos size  
SELECT 
    SUM(pg_column_size(logo_data)) / (1024.0 * 1024.0) AS size_mb
FROM vendors;

-- Database size
SELECT pg_size_pretty(pg_database_size('ikeja_online'));
```

### Monitor Image Counts
```sql
SELECT COUNT(*) FROM product_images WHERE image_data IS NOT NULL;
SELECT COUNT(*) FROM vendors WHERE logo_data IS NOT NULL;
```

---

## Migration Steps for Production

### 1. Pre-migration
```bash
# Backup database
pg_dump DATABASE_URL > backup.sql

# Test locally first
python migrate_images_to_db.py
```

### 2. Production Migration
```bash
# On Render PostgreSQL console
# Run migration script
# Or execute SQL manually for new columns
```

### 3. Verify
```bash
# Check all images migrated
SELECT COUNT(*) FROM product_images WHERE image_data IS NOT NULL;

# Verify image retrieval
curl https://your-app.render.com/api/product-image/1
```

### 4. Cleanup (Optional)
```bash
# After verifying everything works, optionally delete old files
rm -rf static/uploads/products/*
rm -rf static/uploads/vendors/*

# Keep backup
# kept in static/uploads/backup/
```

---

## Code Utilities

### `get_mime_type(filename)`
Determines MIME type based on file extension
- Returns: `image/jpeg`, `image/png`, `image/gif`, `image/webp`

### `save_image_to_db(file, product_id, is_primary)`
Saves file as binary data to database
- Input: File object, product ID, is primary flag
- Returns: Product_Images object or None

### `save_vendor_logo_to_db(file, vendor)`
Saves vendor logo as binary data
- Input: File object, vendor object
- Returns: Boolean success/failure

---

## Future Enhancements

### Recommended Features
1. **Image Compression** - Auto-compress large uploads
2. **Thumbnails** - Generate and store thumbnail BYTEA
3. **Image Optimization** - Convert to WebP for better compression
4. **CDN Integration** - Serve images through CloudFlare or similar
5. **Caching** - Add Redis caching layer for frequently accessed images

### Implementation Notes
```python
# Image compression example
from PIL import Image
from io import BytesIO

img = Image.open(BytesIO(image_data))
img.thumbnail((800, 600))
output = BytesIO()
img.save(output, format='JPEG', quality=85)
image_data = output.getvalue()
```

---

## Support & Resources

- **PostgreSQL BYTEA Docs**: https://www.postgresql.org/docs/current/datatype-binary.html
- **Flask File Upload**: https://flask.palletsprojects.com/en/2.3.x/patterns/fileuploads/
- **Render PostgreSQL**: https://render.com/docs/postgresql

---

## Summary

Your Ikeja Online backend is now configured to:
✅ Store all images as binary BYTEA in PostgreSQL
✅ Serve images through API endpoints with correct MIME types
✅ Support both product images and vendor logos
✅ Maintain backward compatibility with filesystem storage
✅ Scale seamlessly on Render without ephemeral filesystem concerns

**Key URLs:**
- Product Image: `/api/product-image/<image_id>`
- Vendor Logo: `/api/vendor-logo/<vendor_id>`
- All Product Images: `/api/product-images/<product_id>`
