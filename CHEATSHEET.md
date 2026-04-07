# BYTEA Image Storage - Visual Reference & Cheat Sheet

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Browser)                         │
│  <img src="/api/product-image/42" />                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP GET
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Flask Backend (app.py)                        │
│  Route: GET /api/product-image/<image_id>                      │
│  Function: get_product_image()                                 │
│  Actions:                                                       │
│    1. Query product_images table                               │
│    2. Fetch image_data (BYTEA)                                │
│    3. Set Content-Type: {mime_type}                           │
│    4. Return binary data                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Binary Data
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                                │
│                                                                 │
│  product_images table:                                          │
│  ┌──────┬────────────┬─────────────┬────────┬──────────┐       │
│  │ id   │ product_id │ image_data  │ MIME   │ filename │       │
│  │ int  │ int        │ BYTEA       │ str    │ str      │       │
│  ├──────┼────────────┼─────────────┼────────┼──────────┤       │
│  │ 42   │ 1          │ [binary]    │ jpg    │ img.jpg  │       │
│  │ 43   │ 1          │ [binary]    │ png    │ img.png  │       │
│  │ 44   │ 2          │ [binary]    │ jpeg   │ img.jpg  │       │
│  └──────┴────────────┴─────────────┴────────┴──────────┘       │
│                                                                 │
│  vendors table:                                                 │
│  ┌──────┬────────────┬─────────────┬────────┐                  │
│  │ id   │ logo_data  │ mime_type   │ ...    │                  │
│  │ int  │ BYTEA      │ str         │        │                  │
│  ├──────┼────────────┼─────────────┼────────┤                  │
│  │ 5    │ [binary]   │ image/jpeg  │ ...    │                  │
│  └──────┴────────────┴─────────────┴────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow - Product Image Upload

```
User uploads image
       │
       ↓
POST /api/add-product
Content-Type: multipart/form-data
       │
       ├─ product_name
       ├─ description
       ├─ price
       ├─ product_images (file)  ← Image file
       │
       ↓
add_product_api() function
       │
       ├─ Validate form data
       ├─ Create Products record
       │
       ├─ For each image file:
       │   │
       │   ├─ Check if allowed_file()
       │   │
       │   ├─ save_image_to_db():
       │   │   ├─ Read file as binary
       │   │   ├─ Check file size < 5MB
       │   │   ├─ Get MIME type (jpeg/png/gif/webp)
       │   │   └─ Return Product_Images object
       │   │
       │   └─ db.session.add()
       │
       ↓
db.session.commit()
       │
       ↓
Binary data stored in PostgreSQL BYTEA
       │
       ↓
Response: { success: true, product_id: 1 }
```

---

## 🖼️ Data Flow - Image Retrieval

```
Frontend: <img src="/api/product-image/42" />
       │
       ↓
GET /api/product-image/42
       │
       ↓
get_product_image(image_id=42)
       │
       ├─ Query: Product_Images.query.get(42)
       │
       ├─ Check: if product_image.image_data exists
       │   │
       │   ├─ YES: Return binary with Content-Type
       │   │       └─ Response headers:
       │   │           Content-Type: image/jpeg
       │   │           Content-Disposition: inline
       │   │
       │   └─ NO: Check image_url (fallback)
       │           └─ Redirect 302 to image_url
       │
       ↓
Frontend receives image
       │
       ↓
Browser displays image
```

---

## 📋 API Endpoints Reference Card

### 1. Upload Product Images
```
POST /api/add-product
Content-Type: multipart/form-data

Parameters:
  category_id: integer
  product_name: string
  description: string
  price: float
  stock_quantity: integer
  product_images: file[] (required, min 1)

Response:
{
  "success": true,
  "product_id": 1,
  "message": "Product added successfully"
}

Images stored in: product_images.image_data (BYTEA)
```

### 2. Get Single Product Image
```
GET /api/product-image/{image_id}

Example: GET /api/product-image/42

Response:
  [binary image data]
  Headers:
    Content-Type: image/jpeg
    Content-Disposition: inline

HTML Usage:
  <img src="/api/product-image/42" alt="Product">
```

### 3. Get All Product Images (JSON)
```
GET /api/product-images/{product_id}

Example: GET /api/product-images/1

Response:
{
  "images": [
    {
      "id": 42,
      "url": "/api/product-image/42",
      "filename": "product-1-0.jpg",
      "mime_type": "image/jpeg",
      "is_primary": true,
      "created_at": "2024-04-07T10:30:00"
    },
    {
      "id": 43,
      "url": "/api/product-image/43",
      "filename": "product-1-1.png",
      "mime_type": "image/png",
      "is_primary": false,
      "created_at": "2024-04-07T10:31:00"
    }
  ]
}
```

### 4. Get Vendor Logo
```
GET /api/vendor-logo/{vendor_id}

Example: GET /api/vendor-logo/5

Response:
  [binary image data]
  Headers:
    Content-Type: image/jpeg
    Content-Disposition: inline

HTML Usage:
  <img src="/api/vendor-logo/5" alt="Store Logo">
```

### 5. Update Product with New Images
```
PUT /api/products/{product_id}
Content-Type: multipart/form-data
Authorization: Bearer {token}

Parameters:
  product_name: string
  description: string
  price: float
  stock_quantity: integer
  category_id: integer
  product_images: file[] (optional)

Response:
{
  "success": true,
  "product_id": 1,
  "message": "Product updated successfully"
}

Old images deleted, new images stored as BYTEA
```

---

## 🗄️ Database Schema

### product_images Table
```sql
CREATE TABLE product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    image_url VARCHAR(255),                    -- OLD: filesystem path
    image_data BYTEA,                          -- NEW: binary data
    mime_type VARCHAR(50) DEFAULT 'image/jpeg',
    filename VARCHAR(255),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### vendors Table  
```sql
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    store_name VARCHAR(100) UNIQUE,
    store_description VARCHAR(255),
    store_slug VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    logo_url VARCHAR(255),                    -- OLD: filesystem path
    logo_data BYTEA,                          -- NEW: binary data
    logo_mime_type VARCHAR(50) DEFAULT 'image/jpeg',
    address VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🐍 Python Code Reference

### Upload/Save Functions

```python
def get_mime_type(filename):
    """Get MIME type from filename"""
    ext = filename.rsplit('.', 1)[1].lower()
    return {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }.get(ext, 'image/jpeg')

def save_image_to_db(file, product_id, is_primary=False):
    """Save image file as binary BYTEA"""
    file.seek(0)
    image_data = file.read()
    
    product_image = Product_Images(
        product_id=product_id,
        image_data=image_data,
        mime_type=get_mime_type(file.filename),
        filename=secure_filename(file.filename),
        is_primary=is_primary
    )
    return product_image

def save_vendor_logo_to_db(file, vendor):
    """Save vendor logo as binary BYTEA"""
    file.seek(0)
    logo_data = file.read()
    
    vendor.logo_data = logo_data
    vendor.logo_mime_type = get_mime_type(file.filename)
    return True
```

### Retrieve Functions

```python
@app.route('/api/product-image/<int:image_id>')
def get_product_image(image_id):
    image = Product_Images.query.get(image_id)
    
    if image.image_data:
        response = make_response(image.image_data)
        response.headers['Content-Type'] = image.mime_type
        return response
    elif image.image_url:
        return redirect(image.image_url)  # fallback
    else:
        abort(404)

@app.route('/api/vendor-logo/<int:vendor_id>')
def get_vendor_logo(vendor_id):
    vendor = Vendors.query.get(vendor_id)
    
    if vendor.logo_data:
        response = make_response(vendor.logo_data)
        response.headers['Content-Type'] = vendor.logo_mime_type
        return response
    else:
        abort(404)
```

---

## 🚀 Deployment Checklist

### Before Deployment
- [ ] `flask db upgrade` runs successfully
- [ ] New product images save to BYTEA
- [ ] Images retrieve via `/api/product-image/<id>`
- [ ] Vendor logos work via `/api/vendor-logo/<id>`
- [ ] Run `python migrate_images_to_db.py` if needed
- [ ] Test on local PostgreSQL
- [ ] All tests pass

### Render Deployment
- [ ] Push code to repository
- [ ] Verify `DATABASE_URL` set in Render
- [ ] Render builds and deploys
- [ ] Check deployment logs
- [ ] Test image upload on live app
- [ ] Verify images display correctly
- [ ] Monitor for errors in Render logs

### Post-Deployment
- [ ] Verify BYTEA columns exist in production
- [ ] Test image uploads on production
- [ ] Check database size
- [ ] Monitor performance
- [ ] Set up alerts if needed

---

## 📊 Performance Metrics

### File Size Impacts
```
Database Size Growth:
100 products × 5 images × 500KB average = 250MB
1000 products × 5 images × 500KB average = 2.5GB

Storage Cost:
Render PostgreSQL: $0.12/GB/month
250MB = ~$0.03/month
2.5GB = ~$0.30/month
```

### Query Performance
```
Image retrieval speed:
  FROM BYTEA: ~50-200ms (includes network)
  FROM Filesystem: ~10-50ms
  
  Difference negligible for typical traffic
  
Optimization:
  - Database indexes on product_id (included)
  - Caching at application layer
  - CDN for repeated images
```

---

## 🔧 Troubleshooting Quick Reference

### Problem → Solution

| Problem | Solution |
|---------|----------|
| Images not uploading | Check `flask db status`, verify BYTEA columns |
| 404 on image retrieval | Verify image_id exists, check spelling |
| Images broken on Render | Verify DATABASE_URL, test connection |
| Slow image loading | Check query performance, add caching |
| Database too large | Archive old images, consider compression |
| Migration failed | Check migration history with `flask db history` |

---

## 📚 File Reference

```
Project Root/
├── app.py                                    ← Updated with image endpoints
├── models.py                                 ← Updated with BYTEA columns
├── migrate_images_to_db.py                  ← NEW: Migration script
├── migrations/
│   └── versions/
│       └── add_bytea_columns_for_images.py  ← NEW: DB migration
├── BYTEA_IMAGE_STORAGE.md                   ← Full documentation
├── SETUP_BYTEA_QUICK.md                     ← Quick start guide
├── SETUP_COMPLETE.md                        ← Setup summary
└── CHEATSHEET.md                            ← This file
```

---

## 💡 Pro Tips

1. **Compress Before Upload**
   ```python
   # Reduce file size before storing
   from PIL import Image
   img = Image.open(file)
   img.thumbnail((1200, 1200))
   img.save(...)
   ```

2. **Cache Images**
   ```python
   @app.route('/api/product-image/<int:image_id>')
   @cache.cached(timeout=3600)  # Cache 1 hour
   def get_product_image(image_id):
       ...
   ```

3. **Monitor Database Size**
   ```bash
   # Check regularly
   psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('ikeja_online'));"
   ```

4. **Use CDN**
   ```html
   <!-- Serve through CloudFlare -->
   <img src="https://cdn.yourdomain.com/api/product-image/42" />
   ```

---

## 🎯 Success Indicators

✅ Images upload without errors  
✅ Images display in browser  
✅ `/api/product-image/<id>` returns binary data  
✅ Database stores BYTEA successfully  
✅ Render deployment works  
✅ Images persist after restart  

---

**Reference Created:** April 7, 2024  
**For:** Ikeja Online Backend  
**Technology:** Flask + SQLAlchemy + PostgreSQL  
**BYTEA Format:** Production-Ready
