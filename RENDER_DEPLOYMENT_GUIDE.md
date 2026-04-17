# Render Deployment Guide for Ikeja Online Backend

## Issues Fixed

The following issues were identified and fixed to enable deployment on Render:

### 1. **PRAGMA Syntax Error** ❌ FIXED
**Problem:** SQLite's `PRAGMA` commands don't work with PostgreSQL, causing:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.SyntaxError) syntax error at or near "PRAGMA"
```

**Solution:** Updated `ensure_order_schema()` function to be database-agnostic:
- Detects database type (PostgreSQL vs SQLite)
- Uses `PRAGMA table_info()` for SQLite
- Uses `information_schema` for PostgreSQL
- Located in: `app.py` (lines ~825-885)

### 2. **Database URL Format** ❌ FIXED
**Problem:** Render's PostgreSQL URL uses `postgresql://` but SQLAlchemy needs `postgresql+psycopg2://`

**Solution:** Added automatic URL conversion in `app.py`:
```python
if db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
```

### 3. **Requirements File Name** ❌ FIXED
**Problem:** `render.yaml` was looking for `requirements.txt` but file is named `requirement.txt`

**Solution:** Updated `render.yaml` buildCommand to use `requirement.txt`

### 4. **Environment Variables in .env** ❌ FIXED
**Problem:** JWT configuration stored as Python strings (`['headers']`, etc.) instead of proper values

**Solution:** Cleaned up `.env` file to remove invalid syntax

## Step-by-Step Deployment to Render

### Step 1: Prepare Your Repository
```bash
git add .
git commit -m "Fix PostgreSQL compatibility and Render deployment issues"
git push origin main
```

### Step 2: Create PostgreSQL Database on Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "PostgreSQL"
3. Fill in the form:
   - Name: `ikeja-online-postgres`
   - Database: `ikeja_online`
   - User: `ikeja_user`
4. Click "Create Database"
5. Copy the connection string (you'll need this in Step 4)

### Step 3: Deploy Web Service
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Fill in the form:
   - Name: `ikeja-online-backend`
   - Environment: Python
   - Python Version: 3.11
   - Build Command: `pip install -r requirement.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 wsgi:app`
   - Plan: Free (or paid if you prefer)

### Step 4: Set Environment Variables
In the Render web service settings, add these environment variables:

```
DATABASE_URL=<PostgreSQL connection string from Step 2>
SECRET_KEY=Hackeye@Josh1999SecretKey
JWT_SECRET_KEY=89421a71f05092d8311486c018417e22
TEST_PUBLIC_KEY=pk_test_0796eb2919d007e2cf058300da852181a60418d0
TEST_SECRET_KEY=sk_test_8fea2fcf8335cb9211c11b03ae81d79f7c9a165c
CLOUDINARY_CLOUD_NAME=dfe6zaubb
CLOUDINARY_API_KEY=573682293696917
CLOUDINARY_API_SECRET=YevIXnx1yDCRteyrVSnTEukmkd0
GMAIL_EMAIL=chibuikemclinic@gmail.com
GMAIL_PASSWORD=bkgr yndz vukl zeas
SUPER_ADMIN_EMAIL=admin@ikejaonline.com
SUPER_ADMIN_PASSWORD=Hackeye@Josh1999AdminPassword
SUPER_ADMIN_FIRST_NAME=Admin
SUPER_ADMIN_LAST_NAME=IkejaOnline
FLASK_ENV=production
FLASK_APP=app.py
```

⚠️ **IMPORTANT:** Never commit sensitive keys to GitHub. Use Render's environment variable management.

### Step 5: Connect Database
After creating the PostgreSQL service:
1. In your web service settings, go to "Environment"
2. Add the `DATABASE_URL` from your PostgreSQL instance
3. The service will automatically detect and use it

### Step 6: Deploy
1. Click "Create Web Service"
2. Render will automatically deploy from your GitHub repository
3. Watch the logs for any errors

## Verification

After deployment:

1. **Check Logs:**
   - Go to your Render service dashboard
   - Click "Logs" to monitor deployment
   - Look for `[DB-MIGRATION] Applied:` messages indicating successful database setup

2. **Test Health Endpoint:**
   - Visit `https://your-app-url.render.com/` (adjust based on routes)
   - Should return your API response

3. **Test Admin Login:**
   - Visit `/login` endpoint
   - Use the super admin credentials from `.env`

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Check that `requirement.txt` is in the root directory and all imports are correct

### Issue: "Database connection failed"
**Solution:** Verify the `DATABASE_URL` environment variable is set correctly in Render dashboard

### Issue: "PRAGMA table_info" error
**Solution:** This should be fixed now, but ensure you're using the latest code from the repository

### Issue: Static files not serving
**Solution:** Render doesn't persist uploaded files. Configure Cloudinary for file storage instead.

### Issue: Migrations failing
**Solution:** The app now runs migrations automatically on startup via `wsgi.py`. If issues persist, check logs for specific SQL errors.

## Database Migrations with Flask-Migrate

To manually run migrations in production:

1. SSH into your Render service (if available on paid plan)
2. Run: `flask db upgrade`
3. This will apply all pending migrations

## Important Notes

✅ **SQLite** is fine for development (uses local `ikeja_online.db`)
✅ **PostgreSQL** is required for production (Render doesn't persist files)
✅ **Both databases** are now fully supported by the codebase
✅ Database type is detected automatically - no code changes needed

## Security Reminders

🔒 Never commit `.env` file to GitHub
🔒 Use strong, unique values for `SECRET_KEY` and `JWT_SECRET_KEY` in production
🔒 Keep Gmail app password separate from regular password
🔒 Rotate API keys periodically

## Files Modified

- `app.py` - Fixed PRAGMA issue, added database URL conversion
- `wsgi.py` - Updated database initialization
- `render.yaml` - Fixed build command
- `.env` - Cleaned up environment variables
- `requirement.txt` - Already has `psycopg2` for PostgreSQL

---

**Need Help?**
- Check Render's documentation: https://render.com/docs
- Review logs in Render dashboard for detailed error messages
- Verify all environment variables are set correctly
