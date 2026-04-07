from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort, flash, session, make_response, g, after_this_request, current_app,send_file
from flask_migrate import Migrate
import requests
import resend
from io import BytesIO
from flask_cors import CORS
from models import db, Roles, Users, Vendors, Customers, Categories, Products, Product_Images, Orders, Order_Items, Reviews, Payments, Wishlists, Wishlist_Items, Wallet, Deposits, VendorWallet, WalletTransaction, CustomerWalletTransaction, VendorWalletTransaction, VendorWithdrawal, VendorDeposit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import os
from slugify import slugify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ikeja_online.db'
app.config['SECRET_KEY'] = 'Hackeye@1999SecretKey'
app.config['JWT_SECRET_KEY'] = '89421a71f05092d8311486c018417e22'
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['TEST_PUBLIC_KEY'] = 'pk_test_0796eb2919d007e2cf058300da852181a60418d0'
app.config['TEST_SECRET_KEY'] = 'sk_test_8fea2fcf8335cb9211c11b03ae81d79f7c9a165c'
app.config['RESEND_API_KEY'] = os.getenv('RESEND_API_KEY', 're_934p2bp1_ESLnDfgtAcAof3MTn9rCQBHE')
app.config['RESEND_URL'] = 'https://api.resend.com/emails'

# Enable CORS
CORS(app, supports_credentials=True)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  

VENDOR_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'vendors')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VENDOR_UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VENDOR_UPLOAD_FOLDER'] = VENDOR_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)


def send_email(to_email, subject, html_content):
    """Send email using Resend API"""
    try:
        headers = {
            "Authorization": f'Bearer {RESEND_API_KEY}',
            "Content-Type": "application/json"
        }
        
        payload ={
            "from": "Ikeja Online <noreply@localhost:5000>",
            "to": to_email,
            "subject": subject,
            "html": html_content
        }
        
        response = requests.post(RESEND_URL, json=payload, headers=headers)
        
        return response.json()
    
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return None

# Initialize database and default data
def init_db():
    """Initialize database with default roles and categories"""
    with app.app_context():
        db.create_all()
        
        # Initialize default roles if they don't exist
        if not Roles.query.filter_by(name='super_admin').first():
            super_admin_role = Roles(name='super_admin', description='Super Administrator account with full control')
            db.session.add(super_admin_role)
        
        if not Roles.query.filter_by(name='vendor').first():
            vendor_role = Roles(name='vendor', description='Vendor account for selling products')
            db.session.add(vendor_role)
        
        if not Roles.query.filter_by(name='customer').first():
            customer_role = Roles(name='customer', description='Customer account for buying products')
            db.session.add(customer_role)
        
        db.session.commit()
        
        # Initialize default categories if none exist
        if Categories.query.count() == 0:
            default_categories = [
                {'name': 'Laptops', 'slug': 'laptops'},
                {'name': 'Desktops', 'slug': 'desktops'},
                {'name': 'Tablets', 'slug': 'tablets'},
                {'name': 'Monitors', 'slug': 'monitors'},
                {'name': 'Keyboards', 'slug': 'keyboards'},
                {'name': 'Mouse', 'slug': 'mouse'},
                {'name': 'Components(GPU,CPU,RAM)', 'slug': 'components-gpu-cpu-ram'},
                {'name': 'Phones', 'slug': 'phones'},
                {'name': 'Smart Watches', 'slug': 'smart-watches'},
                {'name': 'Fitness Trackers', 'slug': 'fitness-trackers'},
                {'name': 'Tools & Hardware', 'slug': 'tools-hardware'},
                {'name': 'Headphones', 'slug': 'headphones'},
                {'name': 'Audio Equipment', 'slug': 'audio-equipment'},
                {'name': 'Cameras', 'slug': 'cameras'},
                {'name': 'Drones', 'slug': 'drones'},
                {'name': 'Printers & Scanners', 'slug': 'printers-scanners'},
                {'name': 'Networking Equipment', 'slug': 'networking-equipment'},
                {'name': 'Software & Games', 'slug': 'software-games'},
                {'name': 'Office Electronics', 'slug': 'office-electronics'},
                {'name': 'Wearable Technology', 'slug': 'wearable-technology'},
                {'name': 'Smart Home Devices', 'slug': 'smart-home-devices'},
                {'name': 'Virtual Reality (VR)', 'slug': 'virtual-reality-vr'},
                {'name': 'Augmented Reality (AR)', 'slug': 'augmented-reality-ar'},
                {'name': '3D Printing', 'slug': '3d-printing'},
                {'name': 'Automotive Electronics', 'slug': 'automotive-electronics'},
                {'name': 'Gaming Consoles', 'slug': 'gaming-consoles'},
                {'name': 'Streaming Devices', 'slug': 'streaming-devices'},
                {'name': 'Power Banks & Chargers', 'slug': 'power-banks-chargers'},
                {'name': 'Other Electronics', 'slug': 'other-electronics'}
            ]
            
            for cat in default_categories:
                category = Categories(name=cat['name'], slug=cat['slug'])
                db.session.add(category)
            
            db.session.commit()

# Register function to initialize database when app starts
@app.before_request
def initialize_database():
    """Initialize database on first request"""
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

# Also initialize when app context is available
with app.app_context():
    init_db()

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({
        'error': 'Invalid Token',
        'message': 'The token has expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid Token',
        'message': 'Invalid token. ' + str(error)
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Missing Authorization header. Use format: "Authorization: Bearer <token>"'
    }), 401

@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    return {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Image handling utilities for BYTEA storage
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

def save_image_to_db(file, product_id=None, is_primary=False):
    """Save uploaded file as binary data to database"""
    try:
        # Validate file exists and is allowed
        if not file:
            print("Error: File is None")
            return None
            
        if not file.filename:
            print("Error: File has no filename")
            return None
            
        if not allowed_file(file.filename):
            print(f"Error: File type not allowed: {file.filename}")
            return None
        
        # Read file content as binary
        try:
            file.seek(0)
            image_data = file.read()
        except Exception as e:
            print(f"Error reading file data: {str(e)}")
            return None
        
        if not image_data:
            print("Error: No data read from file")
            return None
        
        # Check file size
        if len(image_data) > MAX_FILE_SIZE:
            print(f"Error: File size {len(image_data)} exceeds maximum {MAX_FILE_SIZE}")
            return None
        
        # Determine MIME type
        mime_type = get_mime_type(file.filename)
        
        # Create Product_Images record with binary data
        product_image = Product_Images(
            product_id=product_id,
            image_data=image_data,
            mime_type=mime_type,
            filename=secure_filename(file.filename),
            is_primary=is_primary
        )
        
        print(f"Successfully created Product_Images object for {file.filename}")
        return product_image
    except Exception as e:
        print(f"Error saving image to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_vendor_logo_to_db(file, vendor):
    """Save vendor logo as binary data to database"""
    try:
        if not file:
            print("Error: File is None")
            return False
            
        if not file.filename:
            print("Error: File has no filename")
            return False
            
        if not allowed_file(file.filename):
            print(f"Error: File type not allowed: {file.filename}")
            return False
        
        # Read file content as binary
        try:
            file.seek(0)
            logo_data = file.read()
        except Exception as e:
            print(f"Error reading file data: {str(e)}")
            return False
        
        if not logo_data:
            print("Error: No data read from file")
            return False
        
        # Check file size
        if len(logo_data) > MAX_FILE_SIZE:
            print(f"Error: File size {len(logo_data)} exceeds maximum {MAX_FILE_SIZE}")
            return False
        
        # Determine MIME type
        mime_type = get_mime_type(file.filename)
        
        # Update vendor logo in database
        vendor.logo_data = logo_data
        vendor.logo_mime_type = mime_type
        
        print(f"Successfully saved vendor logo: {file.filename}")
        return True
    except Exception as e:
        print(f"Error saving vendor logo to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')

def home():
    return render_template('/home/home.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # Get form data
        role = request.form.get('role', 'customer').lower()
        first_name = request.form.get('firstname', '').strip()
        last_name = request.form.get('lastname', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        store_name = request.form.get('store', '').strip()
        category = request.form.get('vendor_class', '').strip()

        # Validation
        if not all([first_name, last_name, email, password]):
            return render_template('/auth/register.html', error='All fields are required')
        
        if password != confirm_password:
            return render_template('/auth/register.html', error='Passwords do not match')
        
        if len(password) < 8:
            return render_template('/auth/register.html', error='Password must be at least 8 characters')
        
        # Check if email already exists
        if Users.query.filter_by(email=email).first():
            return render_template('/auth/register.html', error='Email already registered')
        
        # Get role from database
        role_obj = Roles.query.filter_by(name=role).first()
        if not role_obj:
            return render_template('/auth/register.html', error=f'Invalid role: {role}')
        
        try:
            # Create password hash
            password_hash = generate_password_hash(password)
            
            # Create new user
            new_user = Users(
                first_name=first_name,
                last_name=last_name,
                email=email,
                passwordhash=password_hash,
                role_id=role_obj.id
            )
            
            db.session.add(new_user)
            db.session.flush()
            
            # Create vendor or customer profile
            if role == 'vendor':
                # Use store_name as store_slug if both are provided
                store_slug = (store_name.lower().replace(' ', '-') if store_name else f"vendor-{new_user.id}")
                
                if store_name and Vendors.query.filter_by(store_name=store_name).first():
                    db.session.rollback()
                    return render_template('/auth/register.html', error='Store name already exists')
                
                if Vendors.query.filter_by(store_slug=store_slug).first():
                    db.session.rollback()
                    return render_template('/auth/register.html', error='Store slug already exists')
                
                vendor = Vendors(
                    user_id=new_user.id,
                    store_name=store_name if store_name else None,
                    store_slug=store_slug
                )
                db.session.add(vendor)
                
            elif role == 'customer':
                customer = Customers(user_id=new_user.id)
                db.session.add(customer)
            
            db.session.commit()
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f'Registration failed: {str(e)}')
    
    return render_template('/auth/register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            return render_template('/auth/login.html', error='Email and password are required')
        
        # Find user by email
        user = Users.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.passwordhash, password):
            return render_template('/auth/login.html', error='Invalid email or password')
        
        try:
            # Create JWT token (identity must be a string)
            access_token = create_access_token(identity=str(user.id))
            
            # Return token as JSON
            return jsonify({
                'success': True,
                'access_token': access_token,
                'user_id': user.id,
                'role': user.role.name,
                'first_name': user.first_name,
                'last_name': user.last_name
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Login failed: {str(e)}'}), 500
    
    return render_template('/auth/login.html')


@app.route('/vendor/dashboard')
def vendor_dashboard():
    # Check if token is in localStorage (frontend will handle this)
    # No JWT required for page load since token is stored client-side
    return render_template('/vendor/vendor_dashboard.html')


@app.route('/vendor/orders')
def vendor_orders():
    # Vendor orders page
    return render_template('/vendor/vendor_orders.html')


@app.route('/add-product', methods=['GET'])
def add_product_page():
    # Client-side will check for token in localStorage
    # Get all categories to pass to template
    categories = Categories.query.all()
    
    return render_template('/vendor/add_product.html', categories=categories)


@app.route('/edit-product/<int:product_id>', methods=['GET'])
def edit_product_page(product_id):
    # Client-side will check for token in localStorage
    # Get all categories to pass to template
    categories = Categories.query.all()
    
    return render_template('/vendor/edit_product.html', categories=categories, product_id=product_id)


@app.route('/my-products', methods=['GET'])
def my_products_page():
    # Client-side will check for token in localStorage and load products via API
    return render_template('/vendor/my_products.html')


@app.route('/api/add-product', methods=['POST'])
@jwt_required()
def add_product_api():
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    
    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can add products'}), 403
    
    vendor = Vendors.query.filter_by(user_id=user_id).first()
    if not vendor:
        return jsonify({'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
    
    try:
        # Get form data
        category_id = request.form.get('category_id', type=int)
        product_name = request.form.get('product_name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        status = request.form.get('status', 'active')
        
        # Validation
        if not all([category_id, product_name, description, price, stock_quantity]):
            return jsonify({'error': 'Bad Request', 'message': 'All fields are required'}), 400
        
        if price <= 0:
            return jsonify({'error': 'Bad Request', 'message': 'Price must be greater than 0'}), 400
        
        if stock_quantity < 0:
            return jsonify({'error': 'Bad Request', 'message': 'Stock quantity cannot be negative'}), 400
        
        # Check if category exists
        category = Categories.query.get(category_id)
        if not category:
            return jsonify({'error': 'Not Found', 'message': 'Category not found'}), 404
        
        # Check if product name already exists for this vendor
        existing_product = Products.query.filter_by(
            vendor_id=vendor.id,
            name=product_name
        ).first()
        
        if existing_product:
            return jsonify({'error': 'Conflict', 'message': 'You already have a product with this name'}), 409
        
        # Generate slug
        slug = slugify(product_name)
        
        # Check if slug already exists
        counter = 1
        original_slug = slug
        while Products.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Create new product
        new_product = Products(
            vendor_id=vendor.id,
            category_id=category_id,
            name=product_name,
            slug=slug,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            status=status
        )
        
        db.session.add(new_product)
        db.session.flush()  # Flush to get the product ID
        
        # Handle image uploads - now using BYTEA storage
        files = request.files.getlist('product_images')
        
        print(f"DEBUG: Received {len(files)} files")
        for i, f in enumerate(files):
            print(f"DEBUG: File {i}: name='{f.filename}', size={len(f.read()) if f else 0}")
            f.seek(0)  # Reset file pointer
        
        if not files or files[0].filename == '':
            db.session.rollback()
            return jsonify({'error': 'Bad Request', 'message': 'At least one product image is required'}), 400
        
        image_count = 0
        errors = []
        for index, file in enumerate(files):
            if file and file.filename:
                try:
                    print(f"DEBUG: Processing image {index}: {file.filename}")
                    # Save image as binary data to database
                    product_image = save_image_to_db(
                        file,
                        product_id=new_product.id,
                        is_primary=(index == 0)
                    )
                    
                    if product_image:
                        db.session.add(product_image)
                        image_count += 1
                        print(f"DEBUG: Successfully added image {index}")
                    else:
                        error_msg = f"Failed to process image {index}: {file.filename}"
                        print(f"DEBUG: {error_msg}")
                        errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Error processing image {index}: {str(e)}"
                    print(f"DEBUG: {error_msg}")
                    errors.append(error_msg)
                    continue
            else:
                print(f"DEBUG: Skipping file {index} - file is None or has no filename")
        
        if image_count == 0:
            db.session.rollback()
            error_details = '; '.join(errors) if errors else 'No valid images were provided'
            print(f"DEBUG: Image upload failed - {error_details}")
            return jsonify({'error': 'Bad Request', 'message': f'No valid images were uploaded. {error_details}'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product added successfully',
            'product_id': new_product.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding product: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': f'Failed to add product: {str(e)}'}), 500


# GET all products for a vendor
@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_vendor_products():
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        if user.role.name != 'vendor':
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Only vendors can access their products'}), 403
        
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
        
        products = Products.query.filter_by(vendor_id=vendor.id).all()
        
        products_data = []
        for product in products:
            try:
                product_dict = {
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'description': product.description,
                    'price': product.price,
                    'stock_quantity': product.stock_quantity,
                    'status': product.status,
                    'created_at': product.created_at.isoformat(),
                    'category_id': product.category_id,
                    'category_name': product.category.name if product.category else 'Uncategorized',
                    'images': [{'id': img.id, 'url': f'/api/product-image/{img.id}', 'is_primary': img.is_primary} for img in product.images]
                }
                products_data.append(product_dict)
            except Exception as e:
                print(f"Error processing product {product.id}: {str(e)}")
                continue
        
        return jsonify({'success': True, 'products': products_data}), 200
    
    except Exception as e:
        print(f"Error in get_vendor_products: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': f'Failed to fetch products: {str(e)}'}), 500


# GET a specific product
@app.route('/api/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    
    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can access products'}), 403
    
    vendor = Vendors.query.filter_by(user_id=user_id).first()
    if not vendor:
        return jsonify({'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
    
    product = Products.query.filter_by(id=product_id, vendor_id=vendor.id).first()
    if not product:
        return jsonify({'error': 'Not Found', 'message': 'Product not found'}), 404
    
    product_dict = {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'price': product.price,
        'stock_quantity': product.stock_quantity,
        'status': product.status,
        'created_at': product.created_at.isoformat(),
        'category_id': product.category_id,
        'category_name': product.category.name,
        'images': [{'id': img.id, 'url': f'/api/product-image/{img.id}', 'is_primary': img.is_primary} for img in product.images]
    }
    
    return jsonify({'success': True, 'product': product_dict}), 200


# UPDATE a product
@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    
    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can update products'}), 403
    
    vendor = Vendors.query.filter_by(user_id=user_id).first()
    if not vendor:
        return jsonify({'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
    
    product = Products.query.filter_by(id=product_id, vendor_id=vendor.id).first()
    if not product:
        return jsonify({'error': 'Not Found', 'message': 'Product not found'}), 404
    
    try:
        # Get form data
        product_name = request.form.get('product_name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        status = request.form.get('status', 'active')
        category_id = request.form.get('category_id', type=int)
        
        # Validate
        if not all([product_name, description, price, stock_quantity is not None, category_id]):
            return jsonify({'error': 'Bad Request', 'message': 'All fields are required'}), 400
        
        if price <= 0:
            return jsonify({'error': 'Bad Request', 'message': 'Price must be greater than 0'}), 400
        
        if stock_quantity < 0:
            return jsonify({'error': 'Bad Request', 'message': 'Stock quantity cannot be negative'}), 400
        
        # Check if category exists
        category = Categories.query.get(category_id)
        if not category:
            return jsonify({'error': 'Not Found', 'message': 'Category not found'}), 404
        
        # Check if product name already exists for this vendor (excluding current product)
        existing_product = Products.query.filter_by(
            vendor_id=vendor.id,
            name=product_name
        ).filter(Products.id != product_id).first()
        
        if existing_product:
            return jsonify({'error': 'Conflict', 'message': 'You already have a product with this name'}), 409
        
        # Update product
        product.name = product_name
        product.description = description
        product.price = price
        product.stock_quantity = stock_quantity
        product.status = status
        product.category_id = category_id
        
        # Handle image uploads if provided - now using BYTEA storage
        files = request.files.getlist('product_images')
        if files and files[0].filename != '':
            print(f"DEBUG: Update - Received {len(files)} files")
            for i, f in enumerate(files):
                print(f"DEBUG: Update - File {i}: name='{f.filename}', size={len(f.read()) if f else 0}")
                f.seek(0)  # Reset file pointer
            
            # Delete existing images from database
            for image in product.images:
                db.session.delete(image)
            
            # Add new images as binary data
            image_count = 0
            errors = []
            for index, file in enumerate(files):
                if file and file.filename:
                    try:
                        print(f"DEBUG: Update - Processing image {index}: {file.filename}")
                        # Save image as binary data to database
                        product_image = save_image_to_db(
                            file,
                            product_id=product.id,
                            is_primary=(index == 0)
                        )
                        
                        if product_image:
                            db.session.add(product_image)
                            image_count += 1
                            print(f"DEBUG: Update - Successfully added image {index}")
                        else:
                            error_msg = f"Failed to process image {index}: {file.filename}"
                            print(f"DEBUG: Update - {error_msg}")
                            errors.append(error_msg)
                    except Exception as e:
                        error_msg = f"Error processing image {index}: {str(e)}"
                        print(f"DEBUG: Update - {error_msg}")
                        errors.append(error_msg)
                        continue
            
            if image_count == 0:
                error_details = '; '.join(errors) if errors else 'No valid images were provided'
                print(f"DEBUG: Update - Image upload failed: {error_details}")
                return jsonify({'error': 'Bad Request', 'message': f'No valid images were uploaded. {error_details}'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'product_id': product.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating product: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': f'Failed to update product: {str(e)}'}), 500


# DELETE a product
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    
    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can delete products'}), 403
    
    vendor = Vendors.query.filter_by(user_id=user_id).first()
    if not vendor:
        return jsonify({'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
    
    product = Products.query.filter_by(id=product_id, vendor_id=vendor.id).first()
    if not product:
        return jsonify({'error': 'Not Found', 'message': 'Product not found'}), 404
    
    try:
        # Delete product images from filesystem
        for image in product.images:
            try:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(image.image_url))
                if os.path.exists(image_path):
                    os.remove(image_path)
            except:
                pass
        
        # Delete product and related records
        Product_Images.query.filter_by(product_id=product.id).delete()
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': f'Failed to delete product: {str(e)}'}), 500


# SERVE product images from BYTEA database
@app.route('/api/product-image/<int:image_id>', methods=['GET'])
def get_product_image(image_id):
    """Retrieve and serve product image from database (BYTEA)"""
    try:
        product_image = Product_Images.query.get(image_id)
        
        if not product_image:
            abort(404)
        
        # Use binary data from database if available, fallback to URL
        if product_image.image_data:
            response = make_response(product_image.image_data)
            response.headers['Content-Type'] = product_image.mime_type
            response.headers['Content-Disposition'] = f'inline; filename={product_image.filename}'
            return response
        elif product_image.image_url:
            # Fallback for backward compatibility with file-based storage
            return redirect(product_image.image_url)
        else:
            abort(404)
    
    except Exception as e:
        print(f"Error retrieving image: {str(e)}")
        abort(500)


@app.route('/api/product-images/<int:product_id>', methods=['GET'])
def get_product_images(product_id):
    """Get all images for a product as JSON with image IDs for retrieval"""
    try:
        product = Products.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Not Found', 'message': 'Product not found'}), 404
        
        images = Product_Images.query.filter_by(product_id=product_id).all()
        
        images_data = []
        for img in images:
            images_data.append({
                'id': img.id,
                'url': f'/api/product-image/{img.id}',  # URL to retrieve binary data
                'filename': img.filename,
                'mime_type': img.mime_type,
                'is_primary': img.is_primary,
                'created_at': img.created_at.isoformat()
            })
        
        return jsonify({'images': images_data}), 200
    
    except Exception as e:
        print(f"Error getting product images: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500


# SERVE vendor logos from BYTEA database
@app.route('/api/vendor-logo/<int:vendor_id>', methods=['GET'])
def get_vendor_logo(vendor_id):
    """Retrieve and serve vendor logo from database (BYTEA)"""
    try:
        vendor = Vendors.query.get(vendor_id)
        
        if not vendor:
            abort(404)
        
        # Use binary data from database if available, fallback to URL
        if vendor.logo_data:
            response = make_response(vendor.logo_data)
            response.headers['Content-Type'] = vendor.logo_mime_type
            response.headers['Content-Disposition'] = f'inline; filename=logo'
            return response
        elif vendor.logo_url:
            # Fallback for backward compatibility with file-based storage
            return redirect(vendor.logo_url)
        else:
            abort(404)
    
    except Exception as e:
        print(f"Error retrieving vendor logo: {str(e)}")
        abort(500)


@app.route('/customer/dashboard')
def customer_dashboard():
    # Client-side will check for token in localStorage
    return render_template('/customer/customer_dashboard.html')


@app.route('/customer/my-orders')
def customer_my_orders():
    # Client-side will check for token in localStorage
    return render_template('/customer/my_orders.html')


@app.route('/api/pay/<int:order_id>', methods=['POST'])
@jwt_required()
def initialize_payment(order_id):
    """Initialize payment for an order using Paystack"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized: Only customers can pay for orders'}), 403
        
        # Verify order exists and belongs to customer
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        if order.customer.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized: This order does not belong to you'}), 403
        
        # Prevent paying for already paid or cancelled orders
        if order.status not in ['pending', 'processing']:
            return jsonify({'success': False, 'message': f'Cannot pay for order with status: {order.status}'}), 400
        
        # Initialize Paystack payment
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        # Generate unique reference
        reference = f"ORD-{order.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Build callback URL
        callback_url = url_for('payment_callback', _external=True)
        
        data = {
            'email': user.email,
            'amount': int(order.total_amount * 100),  # Convert to kobo (1 Naira = 100 Kobo)
            'metadata': {
                'order_id': order.id,
                'customer_id': order.customer.id,
                'customer_name': f"{user.first_name} {user.last_name}"
            },
            'reference': reference,
            'callback_url': callback_url
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response_data = response.json()
        
        print(f"Paystack response status: {response.status_code}")
        print(f"Paystack response data: {response_data}")
        
        if response.status_code == 200 and response_data.get('status'):
            # Store payment record with pending status
            payment = Payments(
                order_id=order.id,
                amount=order.total_amount,
                payment_method='paystack',
                transaction_id=response_data['data']['reference'],
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment initialized successfully',
                'authorization_url': response_data['data']['authorization_url'],
                'access_code': response_data['data']['access_code'],
                'reference': response_data['data']['reference']
            }), 200
        else:
            error_msg = response_data.get('message', 'Payment initialization failed')
            print(f"Paystack error: {error_msg}")
            print(f"Full response: {response_data}")
            return jsonify({
                'success': False,
                'message': 'Payment initialization failed',
                'details': error_msg,
                'response_code': response.status_code
            }), 400
            
    except requests.exceptions.Timeout:
        print(f"Timeout connecting to Paystack for order {order_id}")
        return jsonify({'success': False, 'message': 'Payment service timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        print(f"Request error initializing payment: {str(e)}")
        return jsonify({'success': False, 'message': 'Payment service error. Please try again.'}), 503
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
@app.route('/api/verify-payment/<reference>', methods=['GET'])
@jwt_required()
def verify_payment(reference):
    """Verify payment status with Paystack and update order"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not reference:
            return jsonify({'success': False, 'message': 'Reference number is required'}), 400
        
        # Verify with Paystack
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': 'Payment verification failed',
                'details': response_data.get('message', 'No details provided')
            }), 400
        
        # Check if payment was successful
        if not response_data.get('status') or response_data['data']['status'] != 'success':
            return jsonify({
                'success': False,
                'message': 'Payment not successful',
                'status': response_data['data'].get('status', 'unknown')
            }), 400
        
        # Get order from metadata
        metadata = response_data['data'].get('metadata', {})
        order_id = metadata.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'message': 'Order information not found in payment'}), 400
        
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Verify order belongs to customer
        if order.customer.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized: Order does not belong to you'}), 403
        
        # Update payment record
        payment = Payments.query.filter_by(transaction_id=reference).first()
        if payment:
            payment.status = 'completed'
        else:
            # Create payment record if it doesn't exist
            payment = Payments(
                order_id=order.id,
                amount=order.total_amount,
                payment_method='paystack',
                transaction_id=reference,
                status='completed'
            )
            db.session.add(payment)
        
        # Update order status to completed (payment received successfully)
        order.status = 'completed'
        
        # Distribute funds to vendors
        order_items = Order_Items.query.filter_by(order_id=order.id).all()
        
        for item in order_items:
            product = item.product
            vendor = product.vendor
            vendor_amount = item.price_at_purchase * item.quantity
            
            # Get or create vendor wallet
            vendor_wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
            if not vendor_wallet:
                vendor_wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
                db.session.add(vendor_wallet)
                db.session.flush()
            
            # Add amount to vendor wallet
            vendor_wallet.balance += vendor_amount
            vendor_wallet.total_earned += vendor_amount
            vendor_wallet.updated_at = datetime.utcnow()
            
            # Create wallet transaction records
            transaction = WalletTransaction(
                vendor_id=vendor.id,
                order_id=order.id,
                amount=vendor_amount,
                transaction_type='payment',
                status='completed'
            )
            db.session.add(transaction)
            
            # Also create VendorWalletTransaction for transaction history
            vendor_transaction = VendorWalletTransaction(
                vendor_wallet_id=vendor_wallet.id,
                transaction_type='credit',
                amount=vendor_amount,
                description=f'Payment from order {order.reference_number}',
                reference_id=order.id,
                status='completed'
            )
            db.session.add(vendor_transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully',
            'order_id': order.id,
            'reference_number': order.reference_number,
            'amount': response_data['data']['amount'] / 100,
            'status': 'success'
        }), 200
        
    except requests.exceptions.Timeout:
        print(f"Timeout verifying payment: {reference}")
        return jsonify({'success': False, 'message': 'Payment service timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        print(f"Request error verifying payment: {str(e)}")
        return jsonify({'success': False, 'message': 'Payment service error. Please try again.'}), 503
    except Exception as e:
        db.session.rollback()
        print(f"Error verifying payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/payment-callback')
def payment_callback():
    """Handle Paystack payment callback - verify and update order status"""
    reference = request.args.get('reference')
    
    if not reference:
        return redirect(url_for('customer_my_orders'))
    
    try:
        # Verify payment with Paystack
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        print(f"Paystack callback verification - Status: {response.status_code}")
        print(f"Payment status: {response_data.get('data', {}).get('status')}")
        
        # Check if payment was successful
        if (response.status_code == 200 and 
            response_data.get('status') and 
            response_data['data'].get('status') == 'success'):
            
            # Get order information from metadata
            metadata = response_data['data'].get('metadata', {})
            order_id = metadata.get('order_id')
            
            if order_id:
                order = Orders.query.get(order_id)
                if order:
                    # Update payment record
                    payment = Payments.query.filter_by(transaction_id=reference).first()
                    if payment:
                        payment.status = 'completed'
                    else:
                        # Create payment record if it doesn't exist
                        payment = Payments(
                            order_id=order_id,
                            amount=order.total_amount,
                            payment_method='paystack',
                            transaction_id=reference,
                            status='completed'
                        )
                        db.session.add(payment)
                    
                    # Update order status to completed (payment received successfully)
                    order.status = 'completed'
                    
                    # Distribute funds to vendors
                    order_items = Order_Items.query.filter_by(order_id=order.id).all()
                    
                    for item in order_items:
                        product = item.product
                        vendor = product.vendor
                        vendor_amount = item.price_at_purchase * item.quantity
                        
                        # Get or create vendor wallet
                        vendor_wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
                        if not vendor_wallet:
                            vendor_wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
                            db.session.add(vendor_wallet)
                            db.session.flush()
                        
                        # Add amount to vendor wallet
                        vendor_wallet.balance += vendor_amount
                        vendor_wallet.total_earned += vendor_amount
                        vendor_wallet.updated_at = datetime.utcnow()
                        
                        # Create wallet transaction record
                        transaction = WalletTransaction(
                            vendor_id=vendor.id,
                            order_id=order.id,
                            amount=vendor_amount,
                            transaction_type='payment',
                            status='completed'
                        )
                        db.session.add(transaction)
                        
                        # Also create VendorWalletTransaction for transaction history
                        vendor_transaction = VendorWalletTransaction(
                            vendor_wallet_id=vendor_wallet.id,
                            transaction_type='credit',
                            amount=vendor_amount,
                            description=f'Payment from order {order.reference_number}',
                            reference_id=order.id,
                            status='completed'
                        )
                        db.session.add(vendor_transaction)
                    
                    db.session.commit()
                    print(f"Order {order_id} updated to completed status and vendor payments distributed")
        else:
            print(f"Payment verification failed: {response_data.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error in payment callback: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Always redirect to my-orders page with reference for frontend notification
    return redirect(url_for('customer_my_orders', payment_ref=reference))


# Deposit Routes
@app.route('/customer/deposit')
def deposit_page():
    """Display deposit form"""
    return render_template('/customer/deposit.html')


@app.route('/customer/deposit-status')
def deposit_status():
    """Display deposit history and status"""
    return render_template('/customer/deposit_status.html')


@app.route('/api/wallet', methods=['GET'])
@jwt_required()
def get_wallet():
    """Get customer's wallet balance"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Get or create wallet
        wallet = Wallet.query.filter_by(customer_id=customer.id).first()
        if not wallet:
            wallet = Wallet(customer_id=customer.id, balance=0.0)
            db.session.add(wallet)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'balance': wallet.balance,
            'customer_id': customer.id
        }), 200
        
    except Exception as e:
        print(f"Error getting wallet: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/deposit/initialize', methods=['POST'])
@jwt_required()
def initialize_deposit():
    """Initialize deposit payment with Paystack"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized: Only customers can deposit'}), 403
        
        data = request.get_json()
        amount = data.get('amount')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Create deposit record
        reference = f"DEP-{customer.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        deposit = Deposits(
            customer_id=customer.id,
            amount=amount,
            reference_number=reference,
            status='pending'
        )
        db.session.add(deposit)
        db.session.commit()
        
        # Initialize Paystack payment
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        callback_url = url_for('deposit_callback', _external=True)
        
        data_payload = {
            'email': user.email,
            'amount': int(amount * 100),  # Convert to kobo
            'metadata': {
                'deposit_id': deposit.id,
                'customer_id': customer.id,
                'customer_name': f"{user.first_name} {user.last_name}",
                'type': 'deposit'
            },
            'reference': reference,
            'callback_url': callback_url
        }
        
        response = requests.post(url, json=data_payload, headers=headers, timeout=10)
        response_data = response.json()
        
        print(f"Paystack deposit response status: {response.status_code}")
        print(f"Paystack deposit response data: {response_data}")
        
        if response.status_code == 200 and response_data.get('status'):
            # Update deposit with transaction reference
            deposit.transaction_id = response_data['data']['reference']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Deposit initialized successfully',
                'authorization_url': response_data['data']['authorization_url'],
                'access_code': response_data['data']['access_code'],
                'reference': response_data['data']['reference']
            }), 200
        else:
            error_msg = response_data.get('message', 'Deposit initialization failed')
            print(f"Paystack error: {error_msg}")
            
            # Mark deposit as failed
            deposit.status = 'failed'
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': 'Deposit initialization failed',
                'details': error_msg
            }), 400
            
    except requests.exceptions.Timeout:
        print(f"Timeout connecting to Paystack for deposit")
        return jsonify({'success': False, 'message': 'Payment service timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        print(f"Request error initializing deposit: {str(e)}")
        return jsonify({'success': False, 'message': 'Payment service error. Please try again.'}), 503
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing deposit: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/deposit/verify/<reference>', methods=['GET'])
@jwt_required()
def verify_deposit(reference):
    """Verify deposit payment and add funds to wallet"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not reference:
            return jsonify({'success': False, 'message': 'Reference number is required'}), 400
        
        # Verify with Paystack
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': 'Deposit verification failed',
                'details': response_data.get('message', 'No details provided')
            }), 400
        
        # Check if payment was successful
        if not response_data.get('status') or response_data['data']['status'] != 'success':
            return jsonify({
                'success': False,
                'message': 'Deposit not successful',
                'status': response_data['data'].get('status', 'unknown')
            }), 400
        
        # Get deposit from reference
        deposit = Deposits.query.filter_by(reference_number=reference).first()
        
        if not deposit:
            return jsonify({'success': False, 'message': 'Deposit record not found'}), 404
        
        # Verify deposit belongs to logged-in user
        if deposit.customer.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized: This deposit does not belong to you'}), 403
        
        # Update deposit status
        deposit.status = 'completed'
        deposit.completed_at = datetime.utcnow()
        deposit.transaction_id = response_data['data']['reference']
        
        # Get or create wallet
        wallet = Wallet.query.filter_by(customer_id=deposit.customer_id).first()
        if not wallet:
            wallet = Wallet(customer_id=deposit.customer_id, balance=0.0)
            db.session.add(wallet)
        
        # Add amount to wallet
        wallet.balance += deposit.amount
        wallet.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deposit completed successfully',
            'amount': deposit.amount,
            'new_balance': wallet.balance,
            'reference': reference
        }), 200
        
    except requests.exceptions.Timeout:
        print(f"Timeout verifying deposit")
        return jsonify({'success': False, 'message': 'Verification timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        print(f"Request error verifying deposit: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification error. Please try again.'}), 503
    except Exception as e:
        db.session.rollback()
        print(f"Error verifying deposit: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/deposit-callback')
def deposit_callback():
    """Paystack callback for deposit verification (for redirects with reference)"""
    try:
        reference = request.args.get('reference')
        if not reference:
            flash('No payment reference provided', 'error')
            return redirect(url_for('customer_dashboard'))
        
        # Verify with Paystack
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        print(f"Paystack deposit callback verification - Status: {response.status_code}")
        print(f"Deposit status: {response_data.get('data', {}).get('status')}")
        
        # Check if payment was successful
        if (response.status_code == 200 and 
            response_data.get('status') and 
            response_data['data'].get('status') == 'success'):
            
            # Get deposit information from reference
            deposit = Deposits.query.filter_by(reference_number=reference).first()
            
            if deposit:
                # Update deposit status
                deposit.status = 'completed'
                deposit.completed_at = datetime.utcnow()
                
                # Get or create wallet
                wallet = Wallet.query.filter_by(customer_id=deposit.customer_id).first()
                if not wallet:
                    wallet = Wallet(customer_id=deposit.customer_id, balance=0.0)
                    db.session.add(wallet)
                
                # Add amount to wallet
                wallet.balance += deposit.amount
                wallet.updated_at = datetime.utcnow()
                
                db.session.commit()
                print(f"Deposit {deposit.id} completed - Balance updated")
                flash(f'Deposit of ₦{deposit.amount:,.2f} completed successfully!', 'success')
            else:
                print(f"Deposit not found for reference: {reference}")
                flash('Deposit completed but record not found', 'warning')
        else:
            print(f"Deposit verification failed: {response_data.get('message', 'Unknown error')}")
            flash('Deposit verification failed', 'error')
            
    except Exception as e:
        print(f"Error in deposit callback: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error processing deposit', 'error')
    
    # Always redirect to customer dashboard
    return redirect(url_for('customer_dashboard'))


@app.route('/api/customer/deposits', methods=['GET'])
@jwt_required()
def get_customer_deposits():
    """Get all deposits for current customer"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Get all deposits for this customer, ordered by newest first
        deposits = Deposits.query.filter_by(customer_id=customer.id).order_by(Deposits.created_at.desc()).all()
        
        deposits_list = [
            {
                'id': deposit.id,
                'amount': deposit.amount,
                'reference_number': deposit.reference_number,
                'status': deposit.status,
                'payment_method': deposit.payment_method,
                'created_at': deposit.created_at.isoformat() if deposit.created_at else None,
                'completed_at': deposit.completed_at.isoformat() if deposit.completed_at else None,
            }
            for deposit in deposits
        ]
        
        return jsonify({
            'success': True,
            'deposits': deposits_list
        }), 200
        
    except Exception as e:
        print(f"Error getting customer deposits: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/stats', methods=['GET'])
@jwt_required()
def get_customer_stats():
    """Get customer statistics including spending and wishlist count"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Get all completed orders for this customer
        completed_orders = Orders.query.filter_by(customer_id=customer.id).all()
        
        # Calculate total spent (only completed/paid orders)
        total_spent = 0.0
        for order in completed_orders:
            payment = Payments.query.filter_by(order_id=order.id).first()
            if payment and payment.status == 'completed':
                total_spent += order.total_amount
        
        # Get wishlist count
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        wishlist_count = 0
        if wishlist:
            wishlist_count = Wishlist_Items.query.filter_by(wishlist_id=wishlist.id).count()
        
        # Get total orders count
        total_orders_count = len([o for o in completed_orders if Payments.query.filter_by(order_id=o.id, status='completed').first()])
        
        return jsonify({
            'success': True,
            'stats': {
                'total_spent': float(total_spent),
                'wishlist_count': wishlist_count,
                'total_orders': total_orders_count
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting customer stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/pay-with-wallet/<int:order_id>', methods=['POST'])
@jwt_required()
def pay_with_wallet(order_id):
    """Pay for an order using wallet balance"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized: Only customers can make payments'}), 403
        
        # Get customer
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Get order
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Verify order belongs to customer
        if order.customer.user_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized: This order does not belong to you'}), 403
        
        # Check if order status allows payment
        if order.status not in ['pending', 'processing']:
            return jsonify({'success': False, 'message': f'Cannot pay for order with status: {order.status}'}), 400
        
        # Get customer wallet
        wallet = Wallet.query.filter_by(customer_id=customer.id).first()
        if not wallet:
            wallet = Wallet(customer_id=customer.id, balance=0.0)
            db.session.add(wallet)
            db.session.commit()
        
        # Check if wallet has sufficient balance
        if wallet.balance < order.total_amount:
            return jsonify({
                'success': False,
                'message': f'Insufficient wallet balance. Required: ₦{order.total_amount:.2f}, Available: ₦{wallet.balance:.2f}'
            }), 400
        
        # Deduct amount from customer wallet
        wallet.balance -= order.total_amount
        wallet.updated_at = datetime.utcnow()
        
        # Update order status
        order.status = 'completed'
        
        # Create payment record
        payment = Payments(
            order_id=order.id,
            amount=order.total_amount,
            payment_method='wallet',
            transaction_id=f"WALLET-{order.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            status='completed'
        )
        db.session.add(payment)
        
        # Distribute funds to vendors
        order_items = Order_Items.query.filter_by(order_id=order.id).all()
        
        for item in order_items:
            product = item.product
            vendor = product.vendor
            vendor_amount = item.price_at_purchase * item.quantity
            
            # Get or create vendor wallet
            vendor_wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
            if not vendor_wallet:
                vendor_wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
                db.session.add(vendor_wallet)
                db.session.flush()
            
            # Add amount to vendor wallet
            vendor_wallet.balance += vendor_amount
            vendor_wallet.total_earned += vendor_amount
            vendor_wallet.updated_at = datetime.utcnow()
            
            # Create wallet transaction record
            transaction = WalletTransaction(
                vendor_id=vendor.id,
                order_id=order.id,
                amount=vendor_amount,
                transaction_type='payment',
                status='completed'
            )
            db.session.add(transaction)
            
            # Also create VendorWalletTransaction for transaction history
            vendor_transaction = VendorWalletTransaction(
                vendor_wallet_id=vendor_wallet.id,
                transaction_type='credit',
                amount=vendor_amount,
                description=f'Payment from order {order.reference_number}',
                reference_id=order.id,
                status='completed'
            )
            db.session.add(vendor_transaction)
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment successful',
            'order_id': order.id,
            'amount_paid': order.total_amount,
            'remaining_balance': wallet.balance,
            'status': 'completed'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing wallet payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/customer/get-products', methods=['GET'])
@jwt_required()
def get_products():
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)

    if not user or user.role.name != 'customer':
        return jsonify({'error': 'Unauthorized', 'message': 'Only customers can access products'}), 403

    # Only get active products with stock > 0
    products = Products.query.filter_by(status='active').filter(Products.stock_quantity > 0).all()
    product_list = []
    for product in products:
        # Safely get vendor store name, handling both missing vendor and missing store_name
        store_name = 'Unknown Vendor'
        if product.vendor and product.vendor.store_name:
            store_name = product.vendor.store_name
        
        # Get primary image if available, otherwise first image
        image_url = None
        if product.images:
            primary_image = next((img.id for img in product.images if img.is_primary), None)
            image_id = primary_image or (product.images[0].id if product.images else None)
            if image_id:
                image_url = f'/api/product-image/{image_id}'
        
        product_dict = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'image': image_url,
            'images': [f'/api/product-image/{image.id}' for image in product.images],
            'store_name': store_name
        }
        product_list.append(product_dict)

    return jsonify({'products': product_list}), 200


    
@app.route('/vendor/dashboard/vendor-settings', methods=['POST'])
@jwt_required()
def vendor_settings():
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    
    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can access settings'}), 403
    
    vendor = Vendors.query.filter_by(user_id=user_id).first()
    if not vendor:
        return jsonify({'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
    
    try:
        # Get form data
        store_name = request.form.get('store_name', '').strip()
        store_description = request.form.get('store_description', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        # Validate store name uniqueness
        if store_name and Vendors.query.filter(Vendors.store_name == store_name, Vendors.id != vendor.id).first():
            return jsonify({'error': 'Conflict', 'message': 'Store name already exists'}), 409
        
        # Update vendor profile
        vendor.store_name = store_name if store_name else vendor.store_name
        vendor.store_description = store_description if store_description else vendor.store_description
        vendor.phone = phone if phone else vendor.phone
        vendor.address = address if address else vendor.address
        
        logo_file = request.files.get('logo')
        if logo_file and allowed_file(logo_file.filename):
            # Save logo as binary data to database
            if save_vendor_logo_to_db(logo_file, vendor):
                print("Logo saved to database successfully")
            else:
                print("Failed to save logo to database")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile Settings updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating settings: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': f'Failed to update settings: {str(e)}'}), 500

@app.route('/vendor/dashboard/get-vendor-settings', methods=['GET'])
@jwt_required()
def get_vendor_settings():
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)
    
    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can access settings'}), 403
    
    vendor = Vendors.query.filter_by(user_id=user_id).first()
    if not vendor:
        return jsonify({'error': 'Not Found', 'message': 'Vendor profile not found'}), 404
    
    return jsonify({
        'vendor': {
            'id': vendor.id,
            'store_name': vendor.store_name,
            'store_description': vendor.store_description,
            'phone': vendor.phone,
            'address': vendor.address,
            'logo_url': f'/api/vendor-logo/{vendor.id}' if vendor.logo_data or vendor.logo_url else None
        }
    }), 200

@app.route('/vendor/dashboard/get-vendor-settings-page')
def get_vendor_settings_page():
    # Client-side will check for token in localStorage
    # Frontend will validate authentication before showing sensitive data
    return render_template('/vendor/vendor-settings.html')


@app.route('/api/vendor/wallet', methods=['GET'])
@jwt_required()
def get_vendor_wallet():
    """Get vendor's wallet balance and earnings"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized: Only vendors can access this'}), 403
        
        # Get vendor
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor profile not found'}), 404
        
        # Get or create vendor wallet
        wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
        if not wallet:
            wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
            db.session.add(wallet)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'wallet': {
                'id': wallet.id,
                'balance': wallet.balance,
                'total_earned': wallet.total_earned,
                'vendor_id': vendor.id,
                'store_name': vendor.store_name
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor wallet: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/stats', methods=['GET'])
@jwt_required()
def get_vendor_stats():
    """Get vendor dashboard statistics"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized: Only vendors can access this'}), 403
        
        # Get vendor
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor profile not found'}), 404
        
        # Get vendor's products
        vendor_products = Products.query.filter_by(vendor_id=vendor.id).all()
        product_ids = [p.id for p in vendor_products]
        
        # Calculate statistics
        total_products = len(vendor_products)
        
        # Get all orders containing vendor's products
        if product_ids:
            orders = db.session.query(Orders).join(
                Order_Items, Orders.id == Order_Items.order_id
            ).filter(Order_Items.product_id.in_(product_ids)).distinct().all()
        else:
            orders = []
        
        # Filter for paid orders only
        paid_orders = []
        total_revenue = 0.0
        
        for order in orders:
            payment = Payments.query.filter_by(order_id=order.id).first()
            if payment and payment.status == 'completed':
                paid_orders.append(order)
                
                # Calculate this vendor's portion of the order
                vendor_order_items = Order_Items.query.filter(
                    Order_Items.order_id == order.id,
                    Order_Items.product_id.in_(product_ids)
                ).all()
                
                for item in vendor_order_items:
                    total_revenue += item.price_at_purchase * item.quantity
        
        total_orders = len(paid_orders)
        
        # Get or create vendor wallet
        wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
        if not wallet:
            wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
            db.session.add(wallet)
            db.session.flush()
        
        # Calculate total deposits (completed deposits only)
        completed_deposits = VendorDeposit.query.filter_by(
            vendor_id=vendor.id,
            status='completed'
        ).all()
        total_deposits = sum(d.amount for d in completed_deposits)
        
        # Sync wallet to ensure it has correct earned revenue
        # total_earned should only reflect revenue from sales
        if wallet.total_earned != total_revenue:
            wallet.total_earned = total_revenue
            wallet.updated_at = datetime.utcnow()
        
        # Balance should equal earned revenue + deposits
        expected_balance = total_revenue + total_deposits
        if wallet.balance != expected_balance:
            wallet.balance = expected_balance
            wallet.updated_at = datetime.utcnow()
        
        db.session.commit()
        print(f"Synced vendor {vendor.id} wallet: total_earned={total_revenue}, deposits={total_deposits}, balance={expected_balance}")
        
        wallet_balance = wallet.balance
        wallet_earned = wallet.total_earned
        
        return jsonify({
            'success': True,
            'stats': {
                'total_products': total_products,
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'total_deposits': float(total_deposits),
                'wallet_balance': float(wallet_balance),
                'total_earned': float(wallet_earned)
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/wallet/transactions', methods=['GET'])
@jwt_required()
def get_vendor_wallet_transactions():
    """Get vendor's wallet transaction history"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized: Only vendors can access this'}), 403
        
        # Get vendor
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor profile not found'}), 404
        
        # Get vendor wallet
        wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
        if not wallet:
            return jsonify({'success': True, 'transactions': []}), 200
        
        # Get transactions for this vendor's wallet
        transactions = VendorWalletTransaction.query.filter_by(vendor_wallet_id=wallet.id).order_by(VendorWalletTransaction.created_at.asc()).all()
        
        # Calculate running balance and extract order reference
        running_balance = 0.0
        transactions_list = []
        
        for t in transactions:
            # Determine action description
            if t.transaction_type == 'credit':
                action = 'Added to balance'
            elif t.transaction_type == 'debit':
                action = 'Withdrawn from balance'
            else:
                action = 'Deposit'
            
            # Extract order reference from description if it contains order info
            order_ref = None
            if 'order' in t.description.lower():
                # Try to extract order reference from description like "Payment from order ORD-1-20260331120000"
                parts = t.description.split()
                for i, part in enumerate(parts):
                    if part.lower() == 'order' and i + 1 < len(parts):
                        order_ref = parts[i + 1]
                        break
            
            # Update running balance
            if t.transaction_type == 'credit':
                running_balance += t.amount
            elif t.transaction_type == 'debit':
                running_balance -= t.amount
            
            transactions_list.append({
                'id': t.id,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'status': t.status,
                'description': t.description,
                'action': action,
                'order_reference': order_ref,
                'reference_id': t.reference_id,
                'running_balance': running_balance,
                'created_at': t.created_at.isoformat() if t.created_at else None,
            })
        
        # Reverse to show most recent first
        transactions_list.reverse()
        
        return jsonify({
            'success': True,
            'transactions': transactions_list
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor transactions: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/deposit', methods=['POST'])
@jwt_required()
def vendor_deposit():
    """Initiate vendor wallet deposit with Paystack"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        data = request.get_json()
        amount = data.get('amount')
        
        if not amount or amount < 1:
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400
        
        # Create deposit record
        reference = f"VENDOR-DEPOSIT-{vendor.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        deposit = VendorDeposit(
            vendor_id=vendor.id,
            amount=amount,
            reference_number=reference,
            status='pending'
        )
        db.session.add(deposit)
        db.session.commit()
        
        # Prepare Paystack payment
        headers = {
            "Authorization": f"Bearer {app.config['TEST_SECRET_KEY']}",
            "Content-Type": "application/json"
        }
        
        # Build callback URL
        callback_url = url_for('vendor_deposit_callback', _external=True)
        
        payload = {
            "amount": int(amount * 100),  # Convert to kobo
            "email": user.email,
            "reference": reference,
            "metadata": {
                "vendor_id": vendor.id,
                "deposit_id": deposit.id,
                "type": "vendor_deposit"
            },
            "callback_url": callback_url
        }
        
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers
        )
        
        result = response.json()
        
        if result.get('status'):
            deposit.transaction_id = result['data']['reference']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'authorization_url': result['data']['authorization_url'],
                'access_code': result['data']['access_code'],
                'reference': reference
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to initialize payment'}), 400
            
    except Exception as e:
        print(f"Error processing vendor deposit: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/withdrawal', methods=['POST'])
@jwt_required()
def vendor_withdrawal():
    """Request vendor wallet withdrawal"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        data = request.get_json()
        amount = data.get('amount')
        bank_name = data.get('bank_name')
        account_number = data.get('account_number')
        account_name = data.get('bank_account_name')
        
        if not amount or amount < 1:
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400
        
        if not all([bank_name, account_number, account_name]):
            return jsonify({'success': False, 'message': 'Missing bank details'}), 400
        
        # Get vendor wallet
        wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
        if not wallet:
            return jsonify({'success': False, 'message': 'Wallet not found'}), 404
        
        # Check balance
        if wallet.balance < amount:
            return jsonify({
                'success': False,
                'message': 'Insufficient wallet balance',
                'current_balance': wallet.balance,
                'requested_amount': amount,
                'shortfall': amount - wallet.balance
            }), 400
        
        # Create withdrawal request
        withdrawal = VendorWithdrawal(
            vendor_id=vendor.id,
            amount=amount,
            bank_name=bank_name,
            account_number=account_number,
            bank_account_name=account_name,
            status='pending'
        )
        db.session.add(withdrawal)
        
        # Deduct from wallet
        wallet.balance -= amount
        
        # Create transaction record
        transaction = VendorWalletTransaction(
            vendor_wallet_id=wallet.id,
            transaction_type='debit',
            amount=amount,
            description=f'Withdrawal request to {bank_name}',
            reference_id=withdrawal.id,
            status='pending'
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal request submitted',
            'withdrawal_id': withdrawal.id,
            'new_balance': wallet.balance
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing withdrawal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/deposit/verify/<reference>', methods=['GET'])
@jwt_required()
def verify_vendor_deposit(reference):
    """Verify vendor deposit payment with Paystack"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not reference:
            return jsonify({'success': False, 'message': 'Reference number is required'}), 400
        
        # Verify with Paystack
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': 'Deposit verification failed',
                'details': response_data.get('message', 'No details provided')
            }), 400
        
        # Check if payment was successful
        if not response_data.get('status') or response_data['data']['status'] != 'success':
            return jsonify({
                'success': False,
                'message': 'Deposit not successful',
                'status': response_data['data'].get('status', 'unknown')
            }), 400
        
        # Get deposit from reference
        deposit = VendorDeposit.query.filter_by(reference_number=reference).first()
        
        if not deposit:
            return jsonify({'success': False, 'message': 'Deposit record not found'}), 404
        
        # Verify deposit belongs to current vendor
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if deposit.vendor_id != vendor.id:
            return jsonify({'success': False, 'message': 'Unauthorized: This deposit does not belong to you'}), 403
        
        # Update deposit status
        deposit.status = 'completed'
        deposit.completed_at = datetime.utcnow()
        deposit.transaction_id = response_data['data']['reference']
        
        # Get or create vendor wallet
        wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
        if not wallet:
            wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
            db.session.add(wallet)
            db.session.flush()
        
        # Add deposit amount to wallet balance
        wallet.balance += deposit.amount
        wallet.updated_at = datetime.utcnow()
        
        # Create transaction record
        vendor_transaction = VendorWalletTransaction(
            vendor_wallet_id=wallet.id,
            transaction_type='credit',
            amount=deposit.amount,
            description=f'Deposit via Paystack: {reference}',
            reference_id=deposit.id,
            status='completed'
        )
        db.session.add(vendor_transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deposit verified successfully',
            'amount': deposit.amount,
            'new_balance': wallet.balance,
            'reference': reference
        }), 200
        
    except requests.exceptions.Timeout:
        print(f"Timeout verifying vendor deposit: {reference}")
        return jsonify({'success': False, 'message': 'Verification timeout. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        print(f"Request error verifying vendor deposit: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification service error. Please try again.'}), 503
    except Exception as e:
        db.session.rollback()
        print(f"Error verifying vendor deposit: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/vendor-deposit-callback')
def vendor_deposit_callback():
    """Handle Paystack vendor deposit callback"""
    reference = request.args.get('reference')
    
    if not reference:
        return redirect(url_for('vendor_dashboard'))
    
    try:
        # Verify payment with Paystack
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        print(f"Paystack vendor deposit callback verification - Status: {response.status_code}")
        print(f"Deposit status: {response_data.get('data', {}).get('status')}")
        
        # Check if payment was successful
        if (response.status_code == 200 and 
            response_data.get('status') and 
            response_data['data'].get('status') == 'success'):
            
            # Get deposit information from reference
            deposit = VendorDeposit.query.filter_by(reference_number=reference).first()
            
            if deposit:
                # Update deposit status
                deposit.status = 'completed'
                deposit.completed_at = datetime.utcnow()
                
                # Get or create vendor wallet
                wallet = VendorWallet.query.filter_by(vendor_id=deposit.vendor_id).first()
                if not wallet:
                    wallet = VendorWallet(vendor_id=deposit.vendor_id, balance=0.0, total_earned=0.0)
                    db.session.add(wallet)
                    db.session.flush()
                
                # Add deposit amount to wallet balance
                wallet.balance += deposit.amount
                wallet.updated_at = datetime.utcnow()
                
                # Create transaction record
                vendor_transaction = VendorWalletTransaction(
                    vendor_wallet_id=wallet.id,
                    transaction_type='credit',
                    amount=deposit.amount,
                    description=f'Deposit via Paystack: {reference}',
                    reference_id=deposit.id,
                    status='completed'
                )
                db.session.add(vendor_transaction)
                
                db.session.commit()
                print(f"Vendor Deposit {deposit.id} completed - Balance updated")
                flash(f'Deposit of ₦{deposit.amount:,.2f} completed successfully!', 'success')
            else:
                print(f"Vendor deposit not found for reference: {reference}")
                flash('Deposit completed but record not found', 'warning')
        else:
            print(f"Vendor deposit verification failed: {response_data.get('message', 'Unknown error')}")
            flash('Deposit verification failed', 'error')
            
    except Exception as e:
        print(f"Error in vendor deposit callback: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error processing deposit', 'error')
    
    # Always redirect to vendor dashboard
    return redirect(url_for('vendor_dashboard'))


@app.route('/api/vendor/transactions', methods=['GET'])
@jwt_required()
def get_vendor_transactions():
    """Get vendor's wallet transactions history"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized: Only vendors can access this'}), 403
        
        # Get vendor
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor profile not found'}), 404
        
        # Get transactions for this vendor
        transactions = WalletTransaction.query.filter_by(vendor_id=vendor.id).order_by(WalletTransaction.created_at.desc()).all()
        
        transactions_list = [
            {
                'id': t.id,
                'amount': t.amount,
                'type': t.transaction_type,
                'status': t.status,
                'order_id': t.order_id,
                'created_at': t.created_at.isoformat() if t.created_at else None,
            }
            for t in transactions
        ]
        
        return jsonify({
            'success': True,
            'transactions': transactions_list
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor transactions: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/orders', methods=['GET'])
@jwt_required()
def get_vendor_orders():
    """Get all orders for vendor's products"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        # Get all products from this vendor
        vendor_products = Products.query.filter_by(vendor_id=vendor.id).all()
        product_ids = [p.id for p in vendor_products]
        
        print(f"Vendor {vendor.id} has {len(product_ids)} products")
        
        if not product_ids:
            return jsonify({'success': True, 'orders': []}), 200
        
        # Get all orders containing these products
        orders = db.session.query(Orders).join(
            Order_Items, Orders.id == Order_Items.order_id
        ).filter(Order_Items.product_id.in_(product_ids)).distinct().order_by(Orders.created_at.desc()).all()
        
        print(f"Found {len(orders)} orders for vendor {vendor.id}")
        
        orders_list = []
        for order in orders:
            try:
                # Get payment info
                payment = Payments.query.filter_by(order_id=order.id).first()
                payment_status = payment.status if payment else 'pending'
                payment_method = payment.payment_method if payment else None
                
                # Get customer info
                customer = Customers.query.filter_by(id=order.customer_id).first()
                customer_user = Users.query.filter_by(id=customer.user_id).first() if customer else None
                
                order_data = {
                    'id': order.id,
                    'reference_number': order.reference_number,
                    'customer_id': order.customer_id,
                    'customer_name': f"{customer_user.first_name} {customer_user.last_name}" if customer_user else 'Unknown',
                    'customer_email': customer_user.email if customer_user else 'unknown@email.com',
                    'total_amount': float(order.total_amount),
                    'status': order.status or 'pending',
                    'shipping_status': order.shipping_status or 'pending',
                    'payment_status': payment_status,
                    'payment_method': payment_method,
                    'created_at': order.created_at.isoformat() if order.created_at else None
                }
                orders_list.append(order_data)
                print(f"Added order {order.id} to list")
            except Exception as order_error:
                print(f"Error processing order {order.id}: {str(order_error)}")
                continue
        
        print(f"Returning {len(orders_list)} orders")
        return jsonify({
            'success': True,
            'orders': orders_list
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_vendor_order_details(order_id):
    """Get detailed information about a specific order"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        # Get the order
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Verify vendor owns products in this order
        order_items = Order_Items.query.filter_by(order_id=order_id).all()
        vendor_product_ids = [p.id for p in Products.query.filter_by(vendor_id=vendor.id).all()]
        
        has_vendor_product = any(item.product_id in vendor_product_ids for item in order_items)
        if not has_vendor_product:
            return jsonify({'success': False, 'message': 'Unauthorized: Order does not contain your products'}), 403
        
        # Get customer info
        customer = Customers.query.filter_by(id=order.customer_id).first()
        customer_user = Users.query.filter_by(id=customer.user_id).first() if customer else None
        
        # Get payment info
        payment = Payments.query.filter_by(order_id=order.id).first()
        payment_status = payment.status if payment else 'pending'
        payment_method = payment.payment_method if payment else None
        payment_amount = float(payment.amount) if payment else 0.0
        
        # Get order items with vendor's products
        items = []
        vendor_total = 0
        for item in order_items:
            product = Products.query.get(item.product_id)
            # Only show items from this vendor
            if product and product.vendor_id == vendor.id:
                item_total = float(item.price) * item.quantity
                vendor_total += item_total
                items.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': item_total
                })
        
        return jsonify({'success': True,
            'order': {
                'id': order.id,
                'reference_number': order.reference_number,
                'customer_name': f"{customer_user.first_name} {customer_user.last_name}" if customer_user else 'Unknown',
                'customer_email': customer_user.email if customer_user else 'unknown@email.com',
                'total_amount': float(order.total_amount),
                'subtotal': float(order.total_amount),
                'status': order.status or 'pending',
                'payment_status': payment_status,
                'payment_method': payment_method,
                'payment_amount': payment_amount,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'items': items,
                'vendor_total': vendor_total
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor order details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/vendor/orders/<int:order_id>/shipping-status', methods=['PUT'])
@jwt_required()
def update_shipping_status(order_id):
    """Update shipping status for an order"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'vendor':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        vendor = Vendors.query.filter_by(user_id=user_id).first()
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        # Get the order
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Verify vendor owns products in this order
        order_items = Order_Items.query.filter_by(order_id=order_id).all()
        vendor_product_ids = [p.id for p in Products.query.filter_by(vendor_id=vendor.id).all()]
        has_vendor_product = any(item.product_id in vendor_product_ids for item in order_items)
        
        if not has_vendor_product:
            return jsonify({'success': False, 'message': 'Unauthorized: Order does not contain your products'}), 403
        
        # Get the new shipping status from request
        data = request.get_json()
        new_status = data.get('shipping_status')
        
        # Validate status
        valid_statuses = ['pending', 'shipped', 'en_route', 'delivered']
        if not new_status or new_status not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid shipping status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Update the shipping status
        order.shipping_status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Shipping status updated to {new_status}',
            'shipping_status': order.shipping_status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating shipping status: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


    return redirect(url_for('login'))


@app.route('/browse-products')
def browse_Allproducts():
    # Client-side will check for token in localStorage
    return render_template('/customer/browse_products.html')


@app.route('/categories')
def view_all_categories():
    # Guest-accessible categories page
    return render_template('/categories/all_categories.html')


@app.route('/product/<int:product_id>')
def view_product_details(product_id):
    # Guest-accessible product details page
    return render_template('/product_details.html')


@app.route('/api/product-details/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    """Get product details - public endpoint"""
    try:
        product = Products.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get vendor store name
        store_name = 'Unknown Vendor'
        if product.vendor and product.vendor.store_name:
            store_name = product.vendor.store_name
        
        # Get primary image if available
        image_url = None
        if product.images:
            primary_image = next((img.id for img in product.images if img.is_primary), None)
            image_id = primary_image or (product.images[0].id if product.images else None)
            if image_id:
                image_url = f'/api/product-image/{image_id}'
        
        product_dict = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'description': product.description,
            'price': product.price,
            'stock_quantity': product.stock_quantity,
            'status': product.status,
            'category_name': product.category.name if product.category else 'Uncategorized',
            'category_id': product.category_id,
            'store_name': store_name,
            'image': image_url,
            'created_at': product.created_at.isoformat()
        }
        
        return jsonify({'success': True, 'product': product_dict}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/check-roles', methods=['GET'])
def check_roles():
    """Check available roles in database"""
    try:
        roles = Roles.query.all()
        roles_data = [{'id': r.id, 'name': r.name, 'description': r.description} for r in roles]
        return jsonify({'success': True, 'roles': roles_data, 'role_count': len(roles_data)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/init-first-admin', methods=['POST'])
def init_first_admin():
    """Create first super admin user - only if no super admin exists"""
    try:
        # Ensure database is initialized
        init_db()
        
        # Check if super admin already exists
        super_admin = Users.query.join(Roles).filter(Roles.name == 'super_admin').first()
        if super_admin:
            return jsonify({'success': False, 'message': 'Super admin already exists', 'admin_email': super_admin.email}), 409
        
        # Get form data - handle both form-data and JSON
        if request.is_json:
            data = request.get_json()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
        else:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
        
        # Debug logging
        print(f"DEBUG: Received data - first_name: '{first_name}', last_name: '{last_name}', email: '{email}', password_length: {len(password)}")
        
        # Validation with detailed error messages
        if not first_name:
            return jsonify({'success': False, 'message': 'first_name is required', 'received': {'first_name': first_name}}), 400
        
        if not last_name:
            return jsonify({'success': False, 'message': 'last_name is required', 'received': {'last_name': last_name}}), 400
        
        if not email:
            return jsonify({'success': False, 'message': 'email is required', 'received': {'email': email}}), 400
        
        if not password:
            return jsonify({'success': False, 'message': 'password is required', 'received': {'password': password}}), 400
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        # Check if email already exists
        if Users.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 409
        
        # Get super admin role
        super_admin_role = Roles.query.filter_by(name='super_admin').first()
        if not super_admin_role:
            print("ERROR: Super admin role not found! Available roles:")
            for role in Roles.query.all():
                print(f"  - {role.name}")
            return jsonify({
                'success': False, 
                'message': 'Super admin role not found in database. Please restart the application.',
                'available_roles': [r.name for r in Roles.query.all()]
            }), 500
        
        # Create new super admin
        password_hash = generate_password_hash(password)
        new_admin = Users(
            first_name=first_name,
            last_name=last_name,
            email=email,
            passwordhash=password_hash,
            role_id=super_admin_role.id
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        print(f"SUCCESS: Super admin created with email: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Super admin created successfully',
            'admin_id': new_admin.id,
            'email': new_admin.email,
            'role_id': super_admin_role.id
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating super admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/admin/dashboard')
def admin_dashboard():
    # Client-side will check for token in localStorage
    return render_template('/admin/admin_dashboard.html')


@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    """Get admin statistics"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Only super admins can access this'}), 403
        
        stats = {
            'total_users': Users.query.count(),
            'total_vendors': Vendors.query.count(),
            'total_customers': Customers.query.count(),
            'total_products': Products.query.count(),
            'total_categories': Categories.query.count(),
            'total_orders': Orders.query.count(),
            'total_revenue': db.session.query(db.func.sum(Orders.total_amount)).scalar() or 0
        }
        
        return jsonify({'success': True, 'stats': stats}), 200
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': f'Failed to fetch stats: {str(e)}'}), 500


@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    """Get all users with their roles"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        users = Users.query.all()
        users_data = []
        
        for u in users:
            user_dict = {
                'id': u.id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'role': u.role.name,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat()
            }
            users_data.append(user_dict)
        
        return jsonify({'success': True, 'users': users_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/admin/vendors', methods=['GET'])
@jwt_required()
def admin_get_vendors():
    """Get all vendors with their information"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        vendors = Vendors.query.all()
        vendors_data = []
        
        for v in vendors:
            vendor_dict = {
                'id': v.id,
                'store_name': v.store_name or 'Not Set',
                'user_name': f"{v.user.first_name} {v.user.last_name}",
                'user_email': v.user.email,
                'store_description': v.store_description,
                'phone': v.phone,
                'address': v.address,
                'product_count': len(v.products),
                'created_at': v.created_at.isoformat()
            }
            vendors_data.append(vendor_dict)
        
        return jsonify({'success': True, 'vendors': vendors_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/admin/categories', methods=['GET'])
@jwt_required()
def admin_get_categories():
    """Get all categories with product count"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        categories = Categories.query.all()
        categories_data = []
        
        for c in categories:
            cat_dict = {
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
                'product_count': len(c.products),
                'created_at': c.created_at.isoformat()
            }
            categories_data.append(cat_dict)
        
        return jsonify({'success': True, 'categories': categories_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@jwt_required()
def admin_toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    try:
        admin_id = int(get_jwt_identity())
        admin = Users.query.get(admin_id)
        
        if not admin or admin.role.name != 'super_admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        user = Users.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User status updated to {user.is_active}',
            'is_active': user.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/browse-products')
def browse_products():
    # Client-side will check for token in localStorage
    return render_template('/customer/browse_products.html')


@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = Categories.query.all()
        
        if not categories:
            print("Warning: No categories found in database")
        
        categories_data = []
        for category in categories:
            # Count only active products with stock > 0
            active_product_count = Products.query.filter_by(
                category_id=category.id,
                status='active'
            ).filter(Products.stock_quantity > 0).count()
            
            cat_dict = {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'product_count': active_product_count
            }
            categories_data.append(cat_dict)
        
        return jsonify({'success': True, 'categories': categories_data}), 200
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': f'Failed to fetch categories: {str(e)}'}), 500


@app.route('/api/init-categories', methods=['POST'])
def init_categories_endpoint():
    """Manually initialize or reset categories - for debugging"""
    try:
        # Check if categories already exist
        existing_count = Categories.query.count()
        
        if existing_count > 0:
            return jsonify({
                'success': True, 
                'message': f'Categories already exist ({existing_count} categories found)',
                'category_count': existing_count
            }), 200
        
        # Initialize categories
        default_categories = [
            {'name': 'Laptops', 'slug': 'laptops'},
            {'name': 'Desktops', 'slug': 'desktops'},
            {'name': 'Tablets', 'slug': 'tablets'},
            {'name': 'Monitors', 'slug': 'monitors'},
            {'name': 'Keyboards', 'slug': 'keyboards'},
            {'name': 'Mouse', 'slug': 'mouse'},
            {'name': 'Components(GPU,CPU,RAM)', 'slug': 'components-gpu-cpu-ram'},
            {'name': 'Phones', 'slug': 'phones'},
            {'name': 'Smart Watches', 'slug': 'smart-watches'},
            {'name': 'Fitness Trackers', 'slug': 'fitness-trackers'},
            {'name': 'Tools & Hardware', 'slug': 'tools-hardware'},
            {'name': 'Headphones', 'slug': 'headphones'},
            {'name': 'Audio Equipment', 'slug': 'audio-equipment'},
            {'name': 'Cameras', 'slug': 'cameras'},
            {'name': 'Drones', 'slug': 'drones'},
            {'name': 'Printers & Scanners', 'slug': 'printers-scanners'},
            {'name': 'Networking Equipment', 'slug': 'networking-equipment'},
            {'name': 'Software & Games', 'slug': 'software-games'},
            {'name': 'Office Electronics', 'slug': 'office-electronics'},
            {'name': 'Wearable Technology', 'slug': 'wearable-technology'},
            {'name': 'Smart Home Devices', 'slug': 'smart-home-devices'},
            {'name': 'Virtual Reality (VR)', 'slug': 'virtual-reality-vr'},
            {'name': 'Augmented Reality (AR)', 'slug': 'augmented-reality-ar'},
            {'name': '3D Printing', 'slug': '3d-printing'},
            {'name': 'Automotive Electronics', 'slug': 'automotive-electronics'},
            {'name': 'Gaming Consoles', 'slug': 'gaming-consoles'},
            {'name': 'Streaming Devices', 'slug': 'streaming-devices'},
            {'name': 'Power Banks & Chargers', 'slug': 'power-banks-chargers'},
            {'name': 'Other Electronics', 'slug': 'other-electronics'}
        ]
        
        for cat in default_categories:
            if not Categories.query.filter_by(slug=cat['slug']).first():
                category = Categories(name=cat['name'], slug=cat['slug'])
                db.session.add(category)
        
        db.session.commit()
        
        new_count = Categories.query.count()
        return jsonify({
            'success': True,
            'message': f'Categories initialized successfully',
            'category_count': new_count
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing categories: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': f'Failed to initialize categories: {str(e)}'}), 500


@app.route('/api/products-by-category/<int:category_id>', methods=['GET'])
def get_products_by_category(category_id):
    try:
        category = Categories.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Category not found'}), 404
        
        # Only get active products with stock > 0
        products = Products.query.filter_by(category_id=category_id, status='active').filter(Products.stock_quantity > 0).all()
        
        product_list = []
        for product in products:
            # Safely get vendor store name
            store_name = 'Unknown Vendor'
            if product.vendor and product.vendor.store_name:
                store_name = product.vendor.store_name
            
            # Get primary image if available
            image_url = None
            if product.images:
                primary_image = next((img.id for img in product.images if img.is_primary), None)
                image_id = primary_image or (product.images[0].id if product.images else None)
                if image_id:
                    image_url = f'/api/product-image/{image_id}'
            
            product_dict = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock_quantity': product.stock_quantity,
                'image': image_url,
                'store_name': store_name
            }
            product_list.append(product_dict)
        
        return jsonify({'success': True, 'category': category.name, 'products': product_list}), 200
    except Exception as e:
        print(f"Error fetching products by category: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': f'Failed to fetch products: {str(e)}'}), 500


# Customer Settings Routes
@app.route('/customer-settings')
def customer_settings():
    """Render customer settings page"""
    # Client-side will check for token in localStorage
    return render_template('/customer/customer-settings.html')


@app.route('/customer/settings', methods=['GET'])
@jwt_required()
def get_customer_settings():
    """Get current customer settings (phone and address)"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'error': 'Unauthorized', 'message': 'Only customers can access settings'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        return jsonify({
            'phone': customer.phone or '',
            'address': customer.default_address or ''
        }), 200
    except Exception as e:
        print(f"Error fetching customer settings: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': 'Failed to fetch settings'}), 500


@app.route('/customer/update-phone', methods=['POST'])
@jwt_required()
def update_customer_phone():
    """Update customer phone number"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'error': 'Unauthorized', 'message': 'Only customers can update settings'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get phone from JSON request
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        # Validation
        if not phone:
            return jsonify({'message': 'Phone number is required'}), 400
        
        # Basic phone validation (should not be less than 7 characters)
        if len(phone) < 7:
            return jsonify({'message': 'Phone number must be at least 7 characters long'}), 400
        
        # Update phone
        customer.phone = phone
        db.session.commit()
        
        return jsonify({
            'message': 'Phone number updated successfully',
            'phone': customer.phone
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating phone number: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': 'Failed to update phone number'}), 500


@app.route('/customer/update-address', methods=['POST'])
@jwt_required()
def update_customer_address():
    """Update customer billing address"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'error': 'Unauthorized', 'message': 'Only customers can update settings'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get address from JSON request
        data = request.get_json()
        address = data.get('address', '').strip()
        
        # Validation
        if not address:
            return jsonify({'message': 'Address is required'}), 400
        
        if len(address) < 10:
            return jsonify({'message': 'Address must be at least 10 characters long'}), 400
        
        if len(address) > 255:
            return jsonify({'message': 'Address must not exceed 255 characters'}), 400
        
        # Update address
        customer.default_address = address
        db.session.commit()
        
        return jsonify({
            'message': 'Billing address updated successfully',
            'address': customer.default_address
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating billing address: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': 'Failed to update billing address'}), 500


# JWT Error Handlers
@app.errorhandler(401)
def unauthorized(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized', 'message': 'Missing or invalid authorization token'}), 401
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not have permission to access this resource'}), 403
    return redirect(url_for('login'))


# ========== WISHLIST ROUTES ==========

@app.route('/api/wishlist/add', methods=['POST'])
@jwt_required()
def add_to_wishlist():
    """Add product to wishlist"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Only customers can use wishlist'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get product ID from request
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'success': False, 'message': 'product_id is required'}), 400
        
        # Check if product exists
        product = Products.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Product not found'}), 404
        
        # Get or create customer's wishlist
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        if not wishlist:
            wishlist = Wishlists(customer_id=customer.id)
            db.session.add(wishlist)
            db.session.flush()  # Get the wishlist ID
        
        # Check if item already in wishlist
        existing_item = Wishlist_Items.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        if existing_item:
            return jsonify({'success': False, 'message': 'Item already in wishlist'}), 409
        
        # Add item to wishlist
        wishlist_item = Wishlist_Items(wishlist_id=wishlist.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{product.name} added to wishlist',
            'product_id': product_id
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding to wishlist: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/wishlist/remove/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_wishlist(product_id):
    """Remove product from wishlist"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get customer's wishlist
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        if not wishlist:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Wishlist not found'}), 404
        
        # Find and delete the item
        item = Wishlist_Items.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        if not item:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Item not in wishlist'}), 404
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from wishlist',
            'product_id': product_id
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error removing from wishlist: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/wishlist', methods=['GET'])
@jwt_required()
def get_wishlist():
    """Get all items in customer's wishlist"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get customer's wishlist
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        
        if not wishlist:
            return jsonify({'success': True, 'items': []}), 200
        
        # Get all wishlist items
        items_data = []
        for item in wishlist.items:
            product = item.product
            store_name = 'Unknown Vendor'
            if product.vendor and product.vendor.store_name:
                store_name = product.vendor.store_name
            
            # Get primary image
            image_url = '/static/uploads/products/placeholder.png'
            if product.images:
                primary_image = next((img for img in product.images if img.is_primary), None)
                if primary_image:
                    image_url = primary_image.image_url
                elif product.images:
                    image_url = product.images[0].image_url
            
            item_dict = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'image': image_url,
                'store_name': store_name,
                'added_date': item.created_at.isoformat()
            }
            items_data.append(item_dict)
        
        return jsonify({
            'success': True,
            'items': items_data,
            'count': len(items_data)
        }), 200
    except Exception as e:
        print(f"Error fetching wishlist: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/wishlist/check/<int:product_id>', methods=['GET'])
@jwt_required()
def check_in_wishlist(product_id):
    """Check if product is in customer's wishlist"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'in_wishlist': False}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': True, 'in_wishlist': False}), 200
        
        # Get customer's wishlist
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        
        if not wishlist:
            return jsonify({'success': True, 'in_wishlist': False}), 200
        
        # Check if item exists
        item = Wishlist_Items.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        
        return jsonify({
            'success': True,
            'in_wishlist': item is not None,
            'product_id': product_id
        }), 200
    except Exception as e:
        print(f"Error checking wishlist: {str(e)}")
        return jsonify({'success': False, 'in_wishlist': False}), 500


@app.route('/api/wishlist/clear', methods=['POST'])
@jwt_required()
def clear_wishlist():
    """Clear all items from customer's wishlist"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get customer's wishlist
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        
        if wishlist:
            # Delete all items in the wishlist
            Wishlist_Items.query.filter_by(wishlist_id=wishlist.id).delete()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Wishlist cleared successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing wishlist: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


# ========== CHECKOUT & ORDER ROUTES ==========

def generate_order_reference():
    """Generate a unique reference number for an order"""
    import random
    import string
    from datetime import datetime
    
    # Format: ORD-YYYYMMDD-XXXXXX (e.g., ORD-20260327-A1B2C3)
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{date_str}-{random_str}"


@app.route('/api/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Create an order from cart items"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Only customers can checkout'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get cart items from request
        data = request.get_json()
        items = data.get('items', [])
        
        if not items or len(items) == 0:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Validate cart items and calculate total
        total_amount = 0
        order_items = []
        
        for item in items:
            product_id = item.get('product_id') or item.get('id')
            quantity = item.get('quantity', 1)
            
            if not product_id or quantity <= 0:
                return jsonify({'success': False, 'message': 'Invalid item in cart'}), 400
            
            # Get product from database
            product = Products.query.get(product_id)
            if not product:
                return jsonify({'success': False, 'message': f'Product {product_id} not found'}), 404
            
            # Check stock
            if product.stock_quantity < quantity:
                return jsonify({
                    'success': False, 
                    'message': f'{product.name} has insufficient stock'
                }), 400
            
            item_total = product.price * quantity
            total_amount += item_total
            
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price_at_purchase': product.price
            })
        
        # Generate unique reference number
        reference_number = generate_order_reference()
        
        # Verify uniqueness (very unlikely but just in case)
        while Orders.query.filter_by(reference_number=reference_number).first():
            reference_number = generate_order_reference()
        
        # Create order
        order = Orders(
            customer_id=customer.id,
            reference_number=reference_number,
            total_amount=total_amount,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID without committing
        
        # Create order items
        for item in order_items:
            order_item = Order_Items(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                price_at_purchase=item['price_at_purchase']
            )
            db.session.add(order_item)
            
            # Update product stock
            item['product'].stock_quantity -= item['quantity']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order': {
                'id': order.id,
                'reference_number': order.reference_number,
                'customer_name': f"{user.first_name} {user.last_name}",
                'customer_email': user.email,
                'total_amount': order.total_amount,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'items_count': len(order_items)
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error during checkout: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/checkout-and-pay', methods=['POST'])
@jwt_required()
def checkout_and_pay():
    """Create an order and immediately initialize Paystack payment"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Only customers can checkout'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found', 'message': 'Customer profile not found'}), 404
        
        # Get cart items from request
        data = request.get_json()
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'paystack').lower()
        
        # Validate payment method
        valid_payment_methods = ['paystack', 'bank-transfer', 'wallet']
        if payment_method not in valid_payment_methods:
            return jsonify({'success': False, 'message': f'Invalid payment method. Supported methods: {", ".join(valid_payment_methods)}'}), 400
        
        # Currently, Paystack and Wallet are supported
        if payment_method not in ['paystack', 'wallet']:
            return jsonify({'success': False, 'message': f'{payment_method} payment method is coming soon'}), 400
        
        if not items or len(items) == 0:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Validate cart items and calculate total
        total_amount = 0
        order_items = []
        
        for item in items:
            product_id = item.get('product_id') or item.get('id')
            quantity = item.get('quantity', 1)
            
            if not product_id or quantity <= 0:
                return jsonify({'success': False, 'message': 'Invalid item in cart'}), 400
            
            # Get product from database
            product = Products.query.get(product_id)
            if not product:
                return jsonify({'success': False, 'message': f'Product {product_id} not found'}), 404
            
            # Check stock
            if product.stock_quantity < quantity:
                return jsonify({
                    'success': False, 
                    'message': f'{product.name} has insufficient stock (available: {product.stock_quantity}, requested: {quantity})'
                }), 400
            
            item_total = product.price * quantity
            total_amount += item_total
            
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price_at_purchase': product.price
            })
        
        # Generate unique reference number
        reference_number = generate_order_reference()
        
        # Verify uniqueness (very unlikely but just in case)
        while Orders.query.filter_by(reference_number=reference_number).first():
            reference_number = generate_order_reference()
        
        # Create order
        order = Orders(
            customer_id=customer.id,
            reference_number=reference_number,
            total_amount=total_amount,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID without committing
        
        # Create order items
        for item in order_items:
            order_item = Order_Items(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                price_at_purchase=item['price_at_purchase']
            )
            db.session.add(order_item)
            
            # Update product stock
            item['product'].stock_quantity -= item['quantity']
        
        db.session.commit()
        
        # ===== Handle payment based on payment method =====
        if payment_method == 'wallet':
            # Process wallet payment
            return process_wallet_payment(order, user, customer)
        else:
            # Process Paystack payment (default)
            return process_paystack_payment(order, user)
    
    except Exception as e:
        db.session.rollback()
        print(f"Error during checkout-and-pay: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


def process_wallet_payment(order, user, customer):
    """Process payment using customer wallet"""
    try:
        # Get or create wallet
        wallet = Wallet.query.filter_by(customer_id=customer.id).first()
        if not wallet:
            wallet = Wallet(customer_id=customer.id, balance=0.0)
            db.session.add(wallet)
            db.session.commit()
        
        # Check if wallet has sufficient balance
        if wallet.balance < order.total_amount:
            return jsonify({
                'success': False,
                'message': 'Insufficient wallet balance',
                'current_balance': wallet.balance,
                'required_amount': order.total_amount,
                'shortfall': order.total_amount - wallet.balance
            }), 400
        
        # Deduct from wallet
        wallet.balance -= order.total_amount
        
        # Create payment record
        payment = Payments(
            order_id=order.id,
            amount=order.total_amount,
            payment_method='wallet',
            transaction_id=f"WALLET-{order.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            status='completed'
        )
        db.session.add(payment)
        
        # Update order status to paid
        order.status = 'paid'
        
        # Create wallet transaction record
        wallet_transaction = CustomerWalletTransaction(
            wallet_id=wallet.id,
            transaction_type='debit',
            amount=order.total_amount,
            description=f'Order payment: {order.reference_number}',
            reference_id=order.id,
            status='completed'
        )
        db.session.add(wallet_transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment completed using wallet',
            'payment_method': 'wallet',
            'order': {
                'id': order.id,
                'reference_number': order.reference_number,
                'total_amount': order.total_amount,
                'status': order.status
            },
            'wallet': {
                'previous_balance': wallet.balance + order.total_amount,
                'new_balance': wallet.balance,
                'amount_deducted': order.total_amount
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing wallet payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error processing wallet payment', 'error': str(e)}), 500


def process_paystack_payment(order, user):
    """Process payment using Paystack"""
    try:
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        # Generate unique payment reference
        payment_reference = f"ORD-{order.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Build callback URL
        callback_url = url_for('payment_callback', _external=True)
        
        paystack_data = {
            'email': user.email,
            'amount': int(order.total_amount * 100),  # Convert to kobo
            'metadata': {
                'order_id': order.id,
                'customer_id': order.customer.id,
                'customer_name': f"{user.first_name} {user.last_name}"
            },
            'reference': payment_reference,
            'callback_url': callback_url
        }
        
        response = requests.post(paystack_url, json=paystack_data, headers=headers, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status'):
            # Store payment record with pending status
            payment = Payments(
                order_id=order.id,
                amount=order.total_amount,
                payment_method='paystack',
                transaction_id=response_data['data']['reference'],
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Order created and payment initialized',
                'authorization_url': response_data['data']['authorization_url'],
                'order': {
                    'id': order.id,
                    'reference_number': order.reference_number,
                    'total_amount': order.total_amount,
                    'status': order.status
                }
            }), 200
        else:
            error_msg = response_data.get('message', 'Payment initialization failed')
            # Order was created but payment init failed
            return jsonify({
                'success': False,
                'message': 'Order created but payment initialization failed',
                'details': error_msg,
                'order': {
                    'id': order.id,
                    'reference_number': order.reference_number
                }
            }), 400
            
    except requests.exceptions.Timeout:
        # Order was created but payment init timed out
        return jsonify({
            'success': False, 
            'message': 'Payment service timeout. Order created but payment not initialized. Please try paying from your orders page.',
            'order': {
                'id': order.id,
                'reference_number': order.reference_number
            }
        }), 504
    except requests.exceptions.RequestException as e:
        # Order was created but payment service error
        return jsonify({
            'success': False, 
            'message': 'Payment service error. Order created but payment not initialized. Please try paying from your orders page.',
            'order': {
                'id': order.id,
                'reference_number': order.reference_number
            }
        }), 503
    except Exception as e:
        db.session.rollback()
        print(f"Error during paystack payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_customer_orders():
    """Get all orders for the current customer"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found'}), 404
        
        # Get all orders for this customer
        orders = Orders.query.filter_by(customer_id=customer.id).order_by(Orders.created_at.desc()).all()
        
        orders_data = []
        for order in orders:
            # Get payment status
            payment = Payments.query.filter_by(order_id=order.id).first()
            payment_status = payment.status if payment else 'pending'
            
            order_dict = {
                'id': order.id,
                'reference_number': order.reference_number,
                'total_amount': order.total_amount,
                'status': order.status,
                'shipping_status': order.shipping_status or 'pending',
                'payment_status': payment_status,
                'created_at': order.created_at.isoformat(),
                'items': []
            }
            
            # Add order items
            for item in order.items:
                item_dict = {
                    'product_id': item.product_id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price_at_purchase': item.price_at_purchase,
                    'total': item.quantity * item.price_at_purchase
                }
                order_dict['items'].append(item_dict)
            
            orders_data.append(order_dict)
        
        return jsonify({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data)
        }), 200
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


@app.route('/api/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """Get details of a specific order"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Not Found'}), 404
        
        # Get order
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Verify customer owns this order
        if order.customer_id != customer.id:
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'You do not own this order'}), 403
        
        # Build order details
        order_dict = {
            'id': order.id,
            'reference_number': order.reference_number,
            'customer_name': f"{user.first_name} {user.last_name}",
            'customer_email': user.email,
            'total_amount': order.total_amount,
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'items': []
        }
        
        # Add order items
        for item in order.items:
            item_dict = {
                'product_id': item.product_id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price_at_purchase': item.price_at_purchase,
                'total': item.quantity * item.price_at_purchase
            }
            order_dict['items'].append(item_dict)
        
        return jsonify({
            'success': True,
            'order': order_dict
        }), 200
    except Exception as e:
        print(f"Error fetching order details: {str(e)}")
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)