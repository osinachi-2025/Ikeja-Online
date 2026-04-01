from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passwordhash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Roles', backref=db.backref('users', lazy=True))
    
    
class Vendors (db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_name = db.Column(db.String(100), unique=True, nullable=True)
    store_description = db.Column(db.String(255), nullable=True)
    store_slug = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('Users', backref=db.backref('vendors', uselist=False))
    

class Customers (db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    default_address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('Users', backref=db.backref('customers', uselist=False))
    

class Categories (db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    
class Products (db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, inactive, out_of_stock
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vendor = db.relationship('Vendors', backref=db.backref('products', lazy=True))
    category = db.relationship('Categories', backref=db.backref('products', lazy=True))
    
    
class Product_Images (db.Model):
    __tablename__ = 'product_images'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Products', backref=db.backref('images', lazy=True))
    
class Carts(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customers', backref=db.backref('cart', uselist=False))
    
class Cart_Items(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cart = db.relationship('Carts', backref=db.backref('items', lazy=True))
    product = db.relationship('Products', backref=db.backref('cart_items', lazy=True))
    

class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)  # Unique order reference
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    shipping_status = db.Column(db.String(20), default='pending')  # pending, shipped, en_route, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customers', backref=db.backref('orders', lazy=True))
    
    
class Order_Items(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Orders', backref=db.backref('items', lazy=True))
    product = db.relationship('Products', backref=db.backref('order_items', lazy=True))
    
    
class Payments(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # e.g., credit_card, paypal
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Orders', backref=db.backref('payment', uselist=False)) 
    
    
class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Products', backref=db.backref('reviews', lazy=True))
    customer = db.relationship('Customers', backref=db.backref('reviews', lazy=True))
    
    
class Wishlists(db.Model):
    __tablename__ = 'wishlists'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customers', backref=db.backref('wishlist', uselist=False))
    
    
class Wishlist_Items(db.Model):
    __tablename__ = 'wishlist_items'
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    wishlist = db.relationship('Wishlists', backref=db.backref('items', lazy=True))
    product = db.relationship('Products', backref=db.backref('wishlist_items', lazy=True))


class Wallet(db.Model):
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, unique=True)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer = db.relationship('Customers', backref=db.backref('wallet', uselist=False))


class Deposits(db.Model):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reference_number = db.Column(db.String(100), unique=True, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_method = db.Column(db.String(50), default='paystack')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    customer = db.relationship('Customers', backref=db.backref('deposits', lazy=True))


class VendorWallet(db.Model):
    __tablename__ = 'vendor_wallets'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False, unique=True)
    balance = db.Column(db.Float, default=0.0)
    total_earned = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vendor = db.relationship('Vendors', backref=db.backref('wallet', uselist=False))


class VendorWalletTransaction(db.Model):
    __tablename__ = 'vendor_wallet_transactions'
    id = db.Column(db.Integer, primary_key=True)
    vendor_wallet_id = db.Column(db.Integer, db.ForeignKey('vendor_wallets.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # credit (from order), debit (withdrawal), deposit
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)  # Order ID or withdrawal ID
    status = db.Column(db.String(20), default='completed')  # completed, pending, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vendor_wallet = db.relationship('VendorWallet', backref=db.backref('transactions', lazy=True))


class VendorWithdrawal(db.Model):
    __tablename__ = 'vendor_withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    bank_account_name = db.Column(db.String(100), nullable=False)
    bank_account_number = db.Column(db.String(20), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    vendor = db.relationship('Vendors', backref=db.backref('withdrawals', lazy=True))


class VendorDeposit(db.Model):
    __tablename__ = 'vendor_deposits'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reference_number = db.Column(db.String(100), unique=True, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_method = db.Column(db.String(50), default='paystack')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    vendor = db.relationship('Vendors', backref=db.backref('deposits', lazy=True))


class CustomerWalletTransaction(db.Model):
    __tablename__ = 'customer_wallet_transactions'
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # debit, credit
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)  # Order ID or payment reference
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    wallet = db.relationship('Wallet', backref=db.backref('transactions', lazy=True))


class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), default='payment')  # payment, refund, withdrawal
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vendor = db.relationship('Vendors', backref=db.backref('wallet_transactions', lazy=True))
    order = db.relationship('Orders', backref=db.backref('wallet_transactions', lazy=True))