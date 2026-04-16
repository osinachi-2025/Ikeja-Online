from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort, flash, session, make_response, g, after_this_request, current_app,send_file
from flask_migrate import Migrate
import requests
from io import BytesIO
from flask_cors import CORS
from models import db, Roles, Users, Vendors, Customers, Categories, Products, Product_Images, Orders, Order_Items, Reviews, Payments, Wishlists, Wishlist_Items, Wallet, Deposits, VendorWallet, WalletTransaction, CustomerWalletTransaction, VendorWalletTransaction, VendorWithdrawal, VendorDeposit, CustomerAddress, DeliveryPreference
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from slugify import slugify
from jwt import ExpiredSignatureError, InvalidTokenError
import base64
import cloudinary
import cloudinary.uploader
import cloudinary.api

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ikeja_online.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'Hackeye@1999SecretKey')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '89421a71f05092d8311486c018417e22')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['TEST_PUBLIC_KEY'] = 'pk_test_0796eb2919d007e2cf058300da852181a60418d0'
app.config['TEST_SECRET_KEY'] = 'sk_test_8fea2fcf8335cb9211c11b03ae81d79f7c9a165c'
app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv('CLOUDINARY_CLOUD_NAME', 'dfe6zaubb')
app.config['CLOUDINARY_API_KEY'] = os.getenv('CLOUDINARY_API_KEY', '573682293696917')
app.config['CLOUDINARY_API_SECRET'] = os.getenv('CLOUDINARY_API_SECRET', 'YevIXnx1yDCRteyrVSnTEukmkd0')

# Gmail SMTP Configuration
app.config['GMAIL_EMAIL'] = os.getenv('GMAIL_EMAIL', 'chibuikemclinic@gmail.com')
app.config['GMAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD', 'bkgr yndz vukl zeas')  # Use Gmail App Password, not regular password

# Enable CORS
CORS(app, supports_credentials=True)

# File upload configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  

VENDOR_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'vendors')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VENDOR_UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VENDOR_UPLOAD_FOLDER'] = VENDOR_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Configure Cloudinary
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

def upload_to_cloudinary(file, folder="ikeja_online", public_id=None):
    """Upload file to Cloudinary and return the URL"""
    try:
        if not file:
            print("Error: File is None")
            return None

        filename = getattr(file, 'filename', None) or getattr(file, 'name', None)
        if not filename:
            print("Error: File has no filename")
            return None

        if not allowed_file(filename):
            print(f"Error: File type not allowed: {filename}")
            return None

        # Check file size
        if hasattr(file, 'seek') and hasattr(file, 'tell'):
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
        else:
            # Fallback for file-like objects without seek/tell
            file_contents = file.read()
            file_size = len(file_contents)
            file = BytesIO(file_contents)
            file.name = filename

        if file_size > MAX_FILE_SIZE:
            print(f"Error: File size {file_size} exceeds maximum {MAX_FILE_SIZE}")
            return None

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            quality="auto"
        )

        print(f"Successfully uploaded to Cloudinary: {upload_result['secure_url']}")
        return upload_result['secure_url']

    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

print(f"[STARTUP] Gmail Configuration:")
print(f"[STARTUP] Email: {app.config['GMAIL_EMAIL']}")
print(f"[STARTUP] Password configured: {'Yes' if app.config['GMAIL_PASSWORD'] != 'your-app-password-here' else 'No (Using default placeholder)'}")

def send_email(to_email, subject, html_content):
    """Send email using Gmail SMTP"""
    try:
        print(f"\n{'='*80}")
        print(f"[EMAIL] ===== ATTEMPTING TO SEND EMAIL VIA GMAIL SMTP =====")
        print(f"[EMAIL] To: {to_email}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Recipient email valid: {bool(to_email and '@' in to_email)}")
        
        # Validate email
        if not to_email or '@' not in to_email:
            print(f"[EMAIL] ✗ ERROR: Invalid email address: {to_email}")
            print(f"{'='*80}\n")
            return None
        
        # Get Gmail credentials
        gmail_email = app.config.get('GMAIL_EMAIL')
        gmail_password = app.config.get('GMAIL_PASSWORD')
        
        if not gmail_email or not gmail_password:
            print(f"[EMAIL] ✗ ERROR: Gmail credentials not configured")
            print(f"{'='*80}\n")
            return None
        
        if gmail_password == 'your-app-password-here':
            print(f"[EMAIL] ✗ ERROR: Please set GMAIL_PASSWORD environment variable")
            print(f"[EMAIL] Note: Use Gmail App Password (not your regular password)")
            print(f"{'='*80}\n")
            return None
        
        print(f"[EMAIL] Gmail Email: {gmail_email}")
        print(f"[EMAIL] Password configured: Yes")
        
        # Create email message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"Ikeja Online <{gmail_email}>"
        message['To'] = to_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        print(f"[EMAIL] ✓ Message object created successfully")
        
        # Send via Gmail SMTP
        print(f"[EMAIL] Connecting to Gmail SMTP server...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        print(f"[EMAIL] ✓ Connected to Gmail SMTP server")
        
        print(f"[EMAIL] Logging in with Gmail credentials...")
        server.login(gmail_email, gmail_password)
        print(f"[EMAIL] ✓ Logged in successfully")
        
        print(f"[EMAIL] Sending email...")
        server.sendmail(gmail_email, to_email, message.as_string())
        server.quit()
        
        print(f"[EMAIL] ✓✓✓ EMAIL SENT SUCCESSFULLY TO {to_email}")
        print(f"{'='*80}\n")
        return {"success": True, "message": "Email sent successfully"}
    
    except Exception as e:
        print(f"[EMAIL] ✗✗✗ EXCEPTION OCCURRED!")
        print(f"[EMAIL] Exception Type: {type(e).__name__}")
        print(f"[EMAIL] Exception Message: {str(e)}")
        import traceback
        print(f"[EMAIL] Full Traceback:")
        traceback.print_exc()
        print(f"{'='*80}\n")
        return None


def generate_email_verification_token(user_id):
    """Generate a JWT token for email verification (valid for 24 hours)"""
    try:
        from datetime import timedelta
        token = create_access_token(
            identity=str(user_id),
            expires_delta=timedelta(hours=24),
            additional_claims={"type": "email_verification"}
        )
        return token
    except Exception as e:
        print(f"[TOKEN] Error generating verification token: {str(e)}")
        return None


def send_verification_email(user_email, user_name, verification_token):
    """Send email verification link to user"""
    try:
        # Create verification link
        verification_url = f"http://localhost:5000/verify-email/{verification_token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">Confirm Your Email Address</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {user_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Thank you for registering with Ikeja Online! Please confirm your email address by clicking the button below:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">Or copy and paste this link in your browser:</p>
                    <p style="color: #FF6B35; font-size: 12px; word-break: break-all; background-color: #f9f9f9; padding: 10px; border-radius: 5px;">
                        {verification_url}
                    </p>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6; margin-top: 20px;">This link will expire in 24 hours.</p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        If you didn't create this account, please ignore this email.<br>
                        <strong>Ikeja Online Support Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(user_email, "Confirm Your Email Address - Ikeja Online", html_content)
    
    except Exception as e:
        print(f"[EMAIL-VERIFICATION] Error sending verification email: {str(e)}")
        return None


# ==================== PASSWORD RESET EMAIL ====================
def send_password_reset_email(user_email, user_name, reset_token):
    """Send password reset link to user"""
    try:
        reset_url = f"http://localhost:5000/reset-password/{reset_token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">Reset Your Password</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {user_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">Or copy and paste this link:</p>
                    <p style="color: #FF6B35; font-size: 12px; word-break: break-all; background-color: #f9f9f9; padding: 10px; border-radius: 5px;">
                        {reset_url}
                    </p>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6; margin-top: 20px;">This link will expire in 1 hour.</p>
                    
                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="color: #856404; font-size: 14px; margin: 0;">
                            <strong>Security Tip:</strong> If you didn't request this, you can safely ignore this email. Your password will remain unchanged.
                        </p>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        <strong>Ikeja Online Support Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(user_email, "Reset Your Password - Ikeja Online", html_content)
    
    except Exception as e:
        print(f"[PASSWORD-RESET] Error sending password reset email: {str(e)}")
        return None


# ==================== ORDER CONFIRMATION EMAIL ====================
def send_order_confirmation_email(customer_email, customer_name, order_ref, items_details, total_amount):
    """Send order confirmation email to customer"""
    try:
        order_tracking_url = f"http://localhost:5000/my-orders/{order_ref}"
        
        items_html = ""
        for item in items_details:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item['product_name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item['quantity']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₦{item['price_at_purchase']:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₦{item['quantity'] * item['price_at_purchase']:,.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">Order Confirmation</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {customer_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Thank you for your order! We're processing your purchase and will send you a shipping notification soon.</p>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #666; margin: 5px 0;"><strong>Order Reference:</strong> {order_ref}</p>
                        <p style="color: #666; margin: 5px 0;"><strong>Order Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    </div>
                    
                    <h3 style="color: #333; margin-top: 25px; margin-bottom: 15px;">Order Items:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background-color: #FF6B35; color: white;">
                                <th style="padding: 10px; text-align: left;">Product</th>
                                <th style="padding: 10px; text-align: center;">Qty</th>
                                <th style="padding: 10px; text-align: right;">Price</th>
                                <th style="padding: 10px; text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div style="text-align: right; margin-top: 20px; border-top: 2px solid #FF6B35; padding-top: 15px;">
                        <h2 style="color: #FF6B35; margin: 0;">Total: ₦{total_amount:,.2f}</h2>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{order_tracking_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Track Your Order
                        </a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        If you have any questions, please contact our support team.<br>
                        <strong>Ikeja Online Support Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(customer_email, f"Order Confirmation - {order_ref}", html_content)
    
    except Exception as e:
        print(f"[ORDER-CONFIRMATION] Error sending order confirmation email: {str(e)}")
        return None


# ==================== ORDER SHIPPED EMAIL ====================
def send_order_shipped_email(customer_email, customer_name, order_ref, tracking_number=None, shipping_status='shipped'):
    """Send order shipping status update to customer"""
    try:
        order_tracking_url = f"http://localhost:5000/my-orders/{order_ref}"
        
        # Define status-specific content
        status_config = {
            'pending': {
                'title': 'Your Order Has Been Received!',
                'heading': 'Order Received & Being Prepared',
                'message': 'Your order has been received and we are preparing it for shipment.',
                'bg_color': '#cce5ff',
                'border_color': '#0066cc',
                'text_color': '#003399',
                'delivery_time': '1-2 business days'
            },
            'shipped': {
                'title': 'Your Order Has Been Shipped!',
                'heading': 'Order Shipped',
                'message': 'Great news! Your order has been shipped and is on its way to you.',
                'bg_color': '#d4edda',
                'border_color': '#28a745',
                'text_color': '#155724',
                'delivery_time': '5-7 business days'
            },
            'en_route': {
                'title': 'Your Order Is On The Way!',
                'heading': 'Order In Transit',
                'message': 'Your order is currently in transit and will be delivered soon.',
                'bg_color': '#ffe5cc',
                'border_color': '#ff9800',
                'text_color': '#cc6600',
                'delivery_time': '1-3 business days'
            },
            'delivered': {
                'title': 'Your Order Has Been Delivered!',
                'heading': 'Order Delivered',
                'message': 'Your order has been successfully delivered. Thank you for your purchase!',
                'bg_color': '#d4edda',
                'border_color': '#28a745',
                'text_color': '#155724',
                'delivery_time': 'Completed'
            }
        }
        
        # Get status config, default to shipped if not found
        config = status_config.get(shipping_status, status_config['shipped'])
        
        tracking_info = ""
        if tracking_number:
            tracking_info = f"""
            <p style="color: #333; font-size: 16px; line-height: 1.6;">
                <strong>Tracking Number:</strong> {tracking_number}
            </p>
            """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">{config['title']}</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {customer_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">{config['message']}</p>
                    
                    <div style="background-color: {config['bg_color']}; border-left: 4px solid {config['border_color']}; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: {config['text_color']}; margin: 5px 0;"><strong>Order Reference:</strong> {order_ref}</p>
                        <p style="color: {config['text_color']}; margin: 5px 0;"><strong>Status:</strong> {shipping_status.replace('_', ' ').title()}</p>
                        {tracking_info}
                    </div>
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">You can track your order status in real-time:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{order_tracking_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            View Order Details
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">
                        Expected delivery: {config['delivery_time']}. Please keep an eye on your shipment status.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        If you have any questions, please contact our support team.<br>
                        <strong>Ikeja Online Support Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(customer_email, f"{config['heading']} - {order_ref}", html_content)
    
    except Exception as e:
        print(f"[ORDER-STATUS] Error sending order status email: {str(e)}")
        return None


# ==================== PAYMENT CONFIRMATION EMAIL ====================
def send_payment_confirmation_email(customer_email, customer_name, order_ref, amount, payment_method):
    """Send payment confirmation email to customer"""
    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #28a745; margin-bottom: 20px;">Payment Confirmed</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {customer_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Your payment has been successfully processed!</p>
                    
                    <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #155724; margin: 5px 0;"><strong>Order Reference:</strong> {order_ref}</p>
                        <p style="color: #155724; margin: 5px 0;"><strong>Amount Paid:</strong> ₦{amount:,.2f}</p>
                        <p style="color: #155724; margin: 5px 0;"><strong>Payment Method:</strong> {payment_method}</p>
                        <p style="color: #155724; margin: 5px 0;"><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y %H:%M:%S')}</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">
                        Your order has been confirmed and will be prepared for shipment shortly. You will receive a shipping notification once your order is dispatched.
                    </p>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6; margin-top: 20px;">
                        <strong>Receipt Reference:</strong> {order_ref}-{datetime.now().strftime('%f')[:6].upper()}
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        If you have any questions about your payment, please contact our support team.<br>
                        <strong>Ikeja Online Support Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(customer_email, f"Payment Confirmation - {order_ref}", html_content)
    
    except Exception as e:
        print(f"[PAYMENT-CONFIRMATION] Error sending payment confirmation email: {str(e)}")
        return None


# ==================== VENDOR PAYOUT EMAIL ====================
def send_vendor_payout_email(vendor_email, vendor_name, payout_amount, payout_method):
    """Send vendor payout/withdrawal confirmation email"""
    try:
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">Payout Processed</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {vendor_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Your payout has been successfully processed and transferred to your account!</p>
                    
                    <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #155724; margin: 5px 0;"><strong>Payout Amount:</strong> ₦{payout_amount:,.2f}</p>
                        <p style="color: #155724; margin: 5px 0;"><strong>Payment Method:</strong> {payout_method}</p>
                        <p style="color: #155724; margin: 5px 0;"><strong>Date Processed:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                        <p style="color: #155724; margin: 5px 0;"><strong>Status:</strong> Completed</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">
                        The funds should appear in your account within 1-2 business days, depending on your bank's processing time.
                    </p>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">
                        Keep this email for your records.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        If you have any questions about your payout, please contact our vendor support team.<br>
                        <strong>Ikeja Online Vendor Support</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(vendor_email, "Payout Processed - Ikeja Online", html_content)
    
    except Exception as e:
        print(f"[VENDOR-PAYOUT] Error sending vendor payout email: {str(e)}")
        return None


# ==================== ACCOUNT CONFIRMATION EMAIL ====================
def send_account_confirmation_email(user_email, user_name, action_type, confirmation_token):
    """Send account confirmation email for sensitive changes"""
    try:
        confirmation_url = f"http://localhost:5000/confirm-action/{confirmation_token}"
        
        action_descriptions = {
            'email_change': 'Email Address Change',
            'password_change': 'Password Change',
            'profile_update': 'Profile Update'
        }
        
        action_desc = action_descriptions.get(action_type, 'Account Update')
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">Confirm {action_desc}</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {user_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">We need you to confirm a recent change to your account. Click the button below to confirm:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{confirmation_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                            Confirm {action_desc}
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">Or copy and paste this link:</p>
                    <p style="color: #FF6B35; font-size: 12px; word-break: break-all; background-color: #f9f9f9; padding: 10px; border-radius: 5px;">
                        {confirmation_url}
                    </p>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6; margin-top: 20px;">This link will expire in 24 hours.</p>
                    
                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <p style="color: #856404; font-size: 14px; margin: 0;">
                            <strong>Security:</strong> If you didn't make this request, please ignore this email and your account will remain unchanged.
                        </p>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        <strong>Ikeja Online Support Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(user_email, f"Confirm {action_desc} - Ikeja Online", html_content)
    
    except Exception as e:
        print(f"[ACCOUNT-CONFIRMATION] Error sending account confirmation email: {str(e)}")
        return None


# ==================== VENDOR PRODUCT ORDERED EMAIL ====================
def send_product_ordered_email(vendor_email, vendor_name, store_name, products_info, order_ref, customer_name, order_total):
    """Send order notification to vendor when their products are ordered"""
    try:
        vendor_dashboard_url = "http://localhost:5000/vendor/dashboard"
        
        # Build product table
        products_html = ""
        vendor_total = 0
        for product in products_info:
            product_total = product['quantity'] * product['price']
            vendor_total += product_total
            products_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{product['product_name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{product['quantity']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₦{product['price']:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₦{product_total:,.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">🎉 New Order for Your Store!</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {vendor_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Great news! You have received a new order from a customer. Here are the details:</p>
                    
                    <div style="background-color: #f0f8ff; border-left: 4px solid #FF6B35; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #333; margin: 5px 0;"><strong>Store:</strong> {store_name if store_name else vendor_name}</p>
                        <p style="color: #333; margin: 5px 0;"><strong>Order Reference:</strong> {order_ref}</p>
                        <p style="color: #333; margin: 5px 0;"><strong>Customer Name:</strong> {customer_name}</p>
                        <p style="color: #333; margin: 5px 0;"><strong>Order Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    </div>
                    
                    <h3 style="color: #333; margin-top: 25px; margin-bottom: 15px;">Order Items:</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #FF6B35;">Product</th>
                                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #FF6B35;">Qty</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #FF6B35;">Price</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #FF6B35;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products_html}
                        </tbody>
                    </table>
                    
                    <div style="background-color: #e8f5e9; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #1b5e20; margin: 5px 0;"><strong>Your Earnings:</strong> ₦{vendor_total:,.2f}</p>
                        <p style="color: #666; font-size: 14px; margin: 5px 0;">Funds will be added to your wallet after order fulfillment.</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6; margin-top: 20px;"><strong>Next Steps:</strong></p>
                    <ul style="color: #666; font-size: 14px; line-height: 1.8;">
                        <li>Review the order details</li>
                        <li>Prepare the items for shipment</li>
                        <li>Update the shipping status when you dispatch the order</li>
                        <li>Include tracking information if available</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{vendor_dashboard_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            View in Vendor Dashboard
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">
                        Please handle this order promptly to ensure customer satisfaction.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        Questions? Contact our support team.<br>
                        <strong>Ikeja Online Seller Support</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(vendor_email, f"New Order Notification - {order_ref}", html_content)
    
    except Exception as e:
        print(f"[VENDOR-ORDER] Error sending vendor product ordered email: {str(e)}")
        return None


# ==================== LOW STOCK ALERT EMAIL ====================
def send_low_stock_alert_email(vendor_email, vendor_name, store_name, low_stock_products):
    """Send low stock alert email to vendor when products fall below 5 units"""
    try:
        vendor_dashboard_url = "http://localhost:5000/vendor/products"
        
        # Build low stock products table
        products_html = ""
        for product in low_stock_products:
            products_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{product['product_name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{product['stock_quantity']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₦{product['price']:,.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF6B35; margin-bottom: 20px;">⚠️ Low Stock Alert!</h2>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hi {vendor_name},</p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Some of your products have low stock levels (below 5 units). Please restock them to avoid losing sales.</p>
                    
                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #856404; margin: 5px 0;"><strong>Store:</strong> {store_name if store_name else vendor_name}</p>
                        <p style="color: #856404; margin: 5px 0;"><strong>Alert Triggered:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                    
                    <h3 style="color: #333; margin-top: 25px; margin-bottom: 15px;">Low Stock Products:</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #FF6B35;">Product Name</th>
                                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #FF6B35;">Current Stock</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #FF6B35;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products_html}
                        </tbody>
                    </table>
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6;"><strong>Why This Matters:</strong></p>
                    <ul style="color: #666; font-size: 14px; line-height: 1.8;">
                        <li>Products with low stock may not appear in search results</li>
                        <li>Customers prefer items with available inventory</li>
                        <li>Running out of stock means losing potential sales</li>
                        <li>Restock these items to maintain customer satisfaction</li>
                    </ul>
                    
                    <div style="background-color: #e8f5e9; border-left: 4px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #1b5e20; margin: 5px 0;"><strong>Action Required:</strong></p>
                        <p style="color: #666; font-size: 14px; margin: 5px 0;">Click the button below to update your product inventory.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{vendor_dashboard_url}" style="display: inline-block; background-color: #FF6B35; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Update Inventory
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">
                        Keep your inventory updated to maximize sales and maintain excellent customer service.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        This is an automated alert from Ikeja Online.<br>
                        <strong>Ikeja Online Seller Support</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(vendor_email, f"Low Stock Alert - {store_name if store_name else vendor_name}", html_content)
    
    except Exception as e:
        print(f"[LOW-STOCK] Error sending low stock alert email: {str(e)}")
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
    """Save uploaded file to Cloudinary and create database record"""
    try:
        # Upload to Cloudinary
        image_url = upload_to_cloudinary(file, folder="ikeja_online/products")

        if not image_url:
            print("Failed to upload image to Cloudinary")
            return None

        # Create Product_Images record with Cloudinary URL
        product_image = Product_Images(
            product_id=product_id,
            image_url=image_url,
            mime_type=get_mime_type(file.filename),
            filename=secure_filename(file.filename),
            is_primary=is_primary
        )

        print(f"Successfully created Product_Images object for {file.filename} with URL: {image_url}")
        return product_image
    except Exception as e:
        print(f"Error saving image to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_vendor_logo_to_db(file, vendor):
    """Save vendor logo to Cloudinary and update database"""
    try:
        # Upload to Cloudinary
        logo_url = upload_to_cloudinary(file, folder="ikeja_online/vendors/logos")

        if not logo_url:
            print("Failed to upload vendor logo to Cloudinary")
            return False

        # Update vendor logo in database
        vendor.logo_url = logo_url
        vendor.logo_data = None  # Clear binary data since we're using URL now
        vendor.logo_mime_type = get_mime_type(file.filename)

        print(f"Successfully saved vendor logo: {file.filename} with URL: {logo_url}")
        return True
    except Exception as e:
        print(f"Error saving vendor logo to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')

def home():
    return render_template('home/home.html')

@app.route('/verify-gmail')
def verify_gmail():
    """Verify Gmail SMTP configuration"""
    try:
        gmail_email = app.config.get('GMAIL_EMAIL')
        gmail_password = app.config.get('GMAIL_PASSWORD')
        
        result = {
            "gmail_email_configured": bool(gmail_email),
            "gmail_email": gmail_email if gmail_email else "Not configured",
            "gmail_password_configured": bool(gmail_password) and gmail_password != 'your-app-password-here'
        }
        
        if not gmail_email or not gmail_password:
            return jsonify({
                **result,
                "status": "ERROR",
                "message": "Gmail email or password is not configured"
            }), 400
        
        if gmail_password == 'your-app-password-here':
            return jsonify({
                **result,
                "status": "ERROR",
                "message": "Gmail password is still using placeholder. Please set GMAIL_PASSWORD environment variable.",
                "note": "Use Gmail App Password (not your regular Gmail password)"
            }), 400
        
        # Try to connect to Gmail SMTP
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
            server.login(gmail_email, gmail_password)
            server.quit()
            result["gmail_connection"] = "Successfully connected and authenticated"
        except Exception as e:
            result["gmail_connection"] = f"ERROR: {str(e)}"
            return jsonify({
                **result,
                "status": "ERROR",
                "message": f"Failed to connect to Gmail SMTP: {str(e)}"
            }), 400
        
        return jsonify({
            **result,
            "status": "SUCCESS",
            "message": "Gmail SMTP is configured correctly and connection successful"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "message": f"Verification failed: {str(e)}"
        }), 500


@app.route('/test-email')
def test_email():
    """Test email sending functionality via Gmail SMTP"""
    try:
        test_email_addr = request.args.get('email', 'test@example.com')
        
        print(f"\n{'='*80}")
        print(f"[TEST-EMAIL] ===== TESTING EMAIL FUNCTIONALITY =====" )
        print(f"[TEST-EMAIL] Test recipient: {test_email_addr}")
        
        # Verify configuration first
        gmail_email = app.config.get('GMAIL_EMAIL')
        gmail_password = app.config.get('GMAIL_PASSWORD')
        
        if not gmail_email or not gmail_password:
            return jsonify({
                'success': False,
                'message': 'Gmail credentials not configured',
                'debug_info': 'Check GMAIL_EMAIL and GMAIL_PASSWORD environment variables'
            }), 500
        
        if gmail_password == 'your-app-password-here':
            return jsonify({
                'success': False,
                'message': 'Gmail password is using placeholder value',
                'debug_info': 'Set GMAIL_PASSWORD environment variable to your Gmail App Password'
            }), 500
        
        print(f"[TEST-EMAIL] Gmail email: {gmail_email}")
        print(f"[TEST-EMAIL] Creating email message...")
        
        # Create test email message
        message = MIMEMultipart('alternative')
        message['Subject'] = 'Test Email - Ikeja Online'
        message['From'] = f"Ikeja Online <{gmail_email}>"
        message['To'] = test_email_addr
        
        html_content = '''<h2>Test Email - Ikeja Online</h2>
        <p>If you received this, email sending is working correctly!</p>
        <p>Timestamp: ''' + datetime.now().isoformat() + '''</p>'''
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        print(f"[TEST-EMAIL] Message created, connecting to Gmail SMTP...")
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        print(f"[TEST-EMAIL] Connected to Gmail SMTP")
        
        server.login(gmail_email, gmail_password)
        print(f"[TEST-EMAIL] Logged in successfully")
        
        print(f"[TEST-EMAIL] Sending test email to {test_email_addr}...")
        server.sendmail(gmail_email, test_email_addr, message.as_string())
        server.quit()
        
        print(f"[TEST-EMAIL] Test email sent successfully")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': True,
            'message': f'Test email sent successfully to {test_email_addr}',
            'debug_info': f'Sent from: {gmail_email}'
        }), 200
        
    except Exception as e:
        print(f"[TEST-EMAIL] EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': False,
            'message': f'Error sending test email: {str(e)}',
            'error_type': type(e).__name__,
            'debug_info': 'Check console logs for full traceback'
        }), 500


@app.route('/verify-email/<token>', methods=['GET'])
@app.route('/verify-email/<token>/', methods=['GET'])
def verify_email(token):
    """Verify user email via link"""
    try:
        # Decode token
        decoded_token = decode_token(token)
        user_id = decoded_token.get('sub')
        token_type = decoded_token.get('type')
        
        # Validate token type
        if token_type != 'email_verification':
            flash('Invalid verification link.', 'danger')
            return redirect(url_for('login'))
        
        # Find user
        user = Users.query.get(int(user_id))
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('login'))
        
        # Check if already verified
        if user.email_verified:
            flash('Email has already been verified. You can now log in.', 'info')
            return redirect(url_for('login'))
        
        # Mark email as verified
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        db.session.commit()
        
        print(f"[EMAIL-VERIFICATION] Email verified for user {user.email}")
        
        flash(f'Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    except ExpiredSignatureError:
        flash('Verification link has expired. Please register again to get a new link.', 'danger')
        return redirect(url_for('register'))
    
    except Exception as e:
        print(f"[EMAIL-VERIFICATION] Error verifying email: {type(e).__name__}: {str(e)}")
        flash(f'Error verifying email: {str(e)}', 'danger')
        return redirect(url_for('login'))


# ==================== PASSWORD RESET ROUTES ====================
@app.route('/forgot-password', methods=['POST', 'GET'])
def forgot_password():
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            return render_template('auth/login.html', error='Email is required')
        
        # Find user by email
        user = Users.query.filter_by(email=email).first()
        
        if user:
            try:
                # Generate reset token (valid for 1 hour)
                from datetime import timedelta
                reset_token = generate_email_verification_token(user.id)  # Reuse token generation
                expires_at = datetime.utcnow() + timedelta(hours=1)
                
                # Store token in database
                user.password_reset_token = reset_token
                user.password_reset_expires = expires_at
                db.session.commit()
                
                # Send reset email
                send_password_reset_email(user.email, user.first_name, reset_token)
                print(f"[PASSWORD-RESET] Reset email sent to {email}")
                
            except Exception as e:
                print(f"[PASSWORD-RESET] Error: {str(e)}")
                db.session.rollback()
        
        # Always show success message for security (don't reveal if email exists)
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    
    return render_template('auth/login.html')


@app.route('/reset-password/<token>', methods=['POST', 'GET'])
@app.route('/reset-password/<token>/', methods=['POST', 'GET'])
def reset_password(token):
    """Handle password reset with token"""
    try:
        # Find user with this reset token
        user = Users.query.filter_by(password_reset_token=token).first()
        
        if not user:
            flash('Invalid password reset link.', 'danger')
            return redirect(url_for('login'))
        
        # Check if token has expired
        if user.password_reset_expires < datetime.utcnow():
            flash('Password reset link has expired. Please request a new one.', 'danger')
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not password or not confirm_password:
                return render_template('auth/reset_password.html', token=token, error='All fields required')
            
            if password != confirm_password:
                return render_template('auth/reset_password.html', token=token, error='Passwords do not match')
            
            if len(password) < 8:
                return render_template('auth/reset_password.html', token=token, error='Password must be at least 8 characters')
            
            # Update password
            user.passwordhash = generate_password_hash(password)
            user.password_reset_token = None
            user.password_reset_expires = None
            db.session.commit()
            
            flash('Password reset successful! You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/reset_password.html', token=token)
        
    except Exception as e:
        print(f"[PASSWORD-RESET] Error: {type(e).__name__}: {str(e)}")
        flash(f'Error resetting password: {str(e)}', 'danger')
        return redirect(url_for('login'))


# ==================== ACCOUNT CONFIRMATION ROUTES ====================
@app.route('/confirm-action/<token>', methods=['GET'])
@app.route('/confirm-action/<token>/', methods=['GET'])
def confirm_action(token):
    """Confirm sensitive account actions"""
    try:
        # Decode token
        decoded_token = decode_token(token)
        user_id = decoded_token.get('sub')
        token_type = decoded_token.get('type')
        action_type = decoded_token.get('action')
        
        # Validate token type
        if token_type != 'account_confirmation':
            flash('Invalid confirmation link.', 'danger')
            return redirect(url_for('login'))
        
        # Find user
        user = Users.query.get(int(user_id))
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('login'))
        
        # Handle based on action type
        if action_type == 'email_change':
            # Update email from stored temporary value (implement based on your needs)
            pass
        elif action_type == 'password_change':
            # Password change confirmed
            pass
        elif action_type == 'profile_update':
            # Profile update confirmed
            pass
        
        flash('Action confirmed successfully!', 'success')
        return redirect(url_for('login'))
        
    except ExpiredSignatureError:
        flash('Confirmation link has expired.', 'danger')
        return redirect(url_for('login'))
    
    except Exception as e:
        print(f"[ACCOUNT-CONFIRMATION] Error: {type(e).__name__}: {str(e)}")
        flash(f'Error confirming action: {str(e)}', 'danger')
        return redirect(url_for('login'))


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
            return render_template('auth/register.html', error='All fields are required')
        
        if password != confirm_password:
            return render_template('auth/register.html', error='Passwords do not match')
        
        if len(password) < 8:
            return render_template('auth/register.html', error='Password must be at least 8 characters')
        
        # Check if email already exists
        if Users.query.filter_by(email=email).first():
            return render_template('auth/register.html', error='Email already registered')
        
        # Get role from database
        role_obj = Roles.query.filter_by(name=role).first()
        if not role_obj:
            return render_template('auth/register.html', error=f'Invalid role: {role}')
        
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
                    return render_template('auth/register.html', error='Store name already exists')
                
                if Vendors.query.filter_by(store_slug=store_slug).first():
                    db.session.rollback()
                    return render_template('auth/register.html', error='Store slug already exists')
                
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
            
            # Send welcome email based on role
            try:
                full_name = f"{first_name} {last_name}"
                
                if role == 'vendor':
                    # Vendor welcome email
                    html_content = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                                <h2 style="color: #FF6B35; margin-bottom: 20px;">Welcome to Ikeja Online, {full_name}!</h2>
                                <p style="color: #333; font-size: 16px; line-height: 1.6;">Thank you for registering as a vendor on Ikeja Online. We're excited to have you join our marketplace.</p>
                                
                                <h3 style="color: #d4af37; margin-top: 20px;">Your Store Information:</h3>
                                <p style="color: #333; background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF6B35;">
                                    <strong>Store Name:</strong> {store_name if store_name else 'To be updated'}<br>
                                    <strong>Email:</strong> {email}
                                </p>
                                
                                <h3 style="color: #d4af37; margin-top: 20px;">Next Steps:</h3>
                                <ol style="color: #333; font-size: 16px; line-height: 1.8;">
                                    <li>Log in to your Ikeja Online vendor dashboard</li>
                                    <li>Complete your store profile</li>
                                    <li>Add your first products</li>
                                    <li>Start selling!</li>
                                </ol>
                                
                                <p style="color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; font-size: 14px;">
                                    If you have any questions, please contact our support team.<br>
                                    <strong>Ikeja Online Support Team</strong>
                                </p>
                            </div>
                        </body>
                    </html>
                    """
                    subject = "Welcome to Ikeja Online - Vendor Registration Complete"
                    
                elif role == 'super_admin':
                    # Admin welcome email
                    html_content = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                                <h2 style="color: #FF6B35; margin-bottom: 20px;">Welcome to Ikeja Online Admin Panel, {full_name}!</h2>
                                <p style="color: #333; font-size: 16px; line-height: 1.6;">Your super admin account has been successfully created on Ikeja Online.</p>
                                
                                <h3 style="color: #d4af37; margin-top: 20px;">Account Details:</h3>
                                <p style="color: #333; background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF6B35;">
                                    <strong>Email:</strong> {email}<br>
                                    <strong>Role:</strong> Super Administrator<br>
                                    <strong>Permissions:</strong> Full System Access
                                </p>
                                
                                <h3 style="color: #d4af37; margin-top: 20px;">Admin Responsibilities:</h3>
                                <ul style="color: #333; font-size: 16px; line-height: 1.8;">
                                    <li>Manage users and vendors</li>
                                    <li>Monitor platform activities</li>
                                    <li>Handle disputes and issues</li>
                                    <li>Manage system configurations</li>
                                </ul>
                                
                                <p style="color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; font-size: 14px;">
                                    <strong>Ikeja Online Admin Team</strong>
                                </p>
                            </div>
                        </body>
                    </html>
                    """
                    subject = "Welcome to Ikeja Online - Admin Account Created"
                    
                else:
                    # Customer welcome email
                    html_content = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                                <h2 style="color: #FF6B35; margin-bottom: 20px;">Welcome to Ikeja Online, {full_name}!</h2>
                                <p style="color: #333; font-size: 16px; line-height: 1.6;">Thank you for registering on Ikeja Online. We're thrilled to have you as part of our community!</p>
                                
                                <h3 style="color: #d4af37; margin-top: 20px;">Your Account Details:</h3>
                                <p style="color: #333; background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF6B35;">
                                    <strong>Email:</strong> {email}<br>
                                    <strong>Account Type:</strong> Customer
                                </p>
                                
                                <h3 style="color: #d4af37; margin-top: 20px;">Get Started:</h3>
                                <ol style="color: #333; font-size: 16px; line-height: 1.8;">
                                    <li>Browse our extensive range of electronics</li>
                                    <li>Add items to your cart</li>
                                    <li>Proceed to checkout securely</li>
                                    <li>Track your orders in real-time</li>
                                </ol>
                                
                                <p style="color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; font-size: 14px;">
                                    If you need assistance, our customer support team is here to help.<br>
                                    <strong>Ikeja Online Customer Support</strong>
                                </p>
                            </div>
                        </body>
                    </html>
                    """
                    subject = "Welcome to Ikeja Online - Registration Complete"
                
                # Send the email
                print(f"\n========== SENDING EMAIL ==========")
                print(f"To: {email}")
                print(f"Subject: {subject}")
                email_result = send_email(email, subject, html_content)
                print(f"Email Result: {email_result}")
                print(f"==================================\n")
                
                # Send verification email
                print(f"\n========== SENDING VERIFICATION EMAIL ==========")
                verification_token = generate_email_verification_token(new_user.id)
                if verification_token:
                    verification_result = send_verification_email(
                        email,
                        first_name,
                        verification_token
                    )
                    print(f"Verification Email Result: {verification_result}")
                else:
                    print(f"Failed to generate verification token")
                print(f"==============================================\n")
                
            except Exception as email_error:
                # Log email error but don't fail registration
                print(f"Error sending emails to {email}: {str(email_error)}")
                import traceback
                traceback.print_exc()
            
            # Flash success message
            flash(f'Registration successful! Check your email to verify your account.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f'Registration failed: {str(e)}')
    
    return render_template('auth/register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            return render_template('auth/login.html', error='Email and password are required')
        
        # Find user by email
        user = Users.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.passwordhash, password):
            return render_template('auth/login.html', error='Invalid email or password')
        
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
    
    return render_template('auth/login.html')


@app.route('/vendor/dashboard')
def vendor_dashboard():
    # Check if token is in localStorage (frontend will handle this)
    # No JWT required for page load since token is stored client-side
    return render_template('vendor/vendor_dashboard.html')


@app.route('/vendor/earnings-summary')
def vendor_earnings_summary():
    # Vendor earnings summary page
    return render_template('dist/includes/vendor/vendor_earnings_summary.html')


@app.route('/vendor/monthly-revenue')
def vendor_monthly_revenue():
    # Vendor monthly revenue page
    return render_template('dist/includes/vendor/vendor_monthly_revenue.html')


@app.route('/vendor/orders')
def vendor_orders():
    # Vendor orders page now uses the dashboard include page
    return render_template('dist/includes/vendor/vendor_orders.html')


@app.route('/vendor/shipping-status')
def vendor_shipping_status():
    # Vendor shipping status page
    return render_template('dist/includes/vendor/vendor_shipping_status.html')


@app.route('/vendor/transactions')
def vendor_transactions():
    # Vendor transaction history page now uses the dashboard include page
    return render_template('dist/includes/vendor/vendor_transactions.html')


@app.route('/vendor/invoices')
def vendor_invoices():
    # Vendor invoices page now uses the dashboard include page
    return render_template('dist/includes/vendor/vendor_invoices.html')


@app.route('/vendor/products')
def vendor_products():
    # Vendor products management page
    return render_template('dist/includes/vendor/vendor_products.html')


@app.route('/vendor/categories')
def vendor_categories():
    # Vendor categories and products page
    return render_template('dist/includes/vendor/vendor_categories.html')


@app.route('/vendor/store-profile')
def vendor_store_profile():
    # Vendor store profile management page
    return render_template('dist/includes/vendor/vendor_store_profile.html')



@app.route('/vendor/login-security')
def vendor_login_security():
    # Vendor login information and password change page
    return render_template('dist/includes/vendor/vendor_login_security.html')


@app.route('/add-product', methods=['GET'])
def add_product_page():
    # Client-side will check for token in localStorage
    # Get all categories to pass to template
    categories = Categories.query.all()
    
    return render_template('dist/includes/vendor/vendor_add_product.html', categories=categories)


@app.route('/edit-product/<int:product_id>', methods=['GET'])
def edit_product_page(product_id):
    # Client-side will check for token in localStorage
    # Get all categories to pass to template
    categories = Categories.query.all()
    
    return render_template('dist/includes/vendor/vendor_edit_product.html', categories=categories, product_id=product_id)


@app.route('/my-products', methods=['GET'])
def my_products_page():
    # Client-side will check for token in localStorage and load products via API
    return render_template('vendor/my_products.html')


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
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # Get paginated products
        products_query = Products.query.filter_by(vendor_id=vendor.id)
        products_pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)
        
        products_data = []
        for product in products_pagination.items:
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
        
        return jsonify({
            'success': True, 
            'products': products_data,
            'pagination': {
                'page': products_pagination.page,
                'per_page': products_pagination.per_page,
                'total': products_pagination.total,
                'pages': products_pagination.pages,
                'has_next': products_pagination.has_next,
                'has_prev': products_pagination.has_prev,
                'next_page': products_pagination.next_num if products_pagination.has_next else None,
                'prev_page': products_pagination.prev_num if products_pagination.has_prev else None
            }
        }), 200
    
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


# SERVE product images from Cloudinary
@app.route('/api/product-image/<int:image_id>', methods=['GET'])
def get_product_image(image_id):
    """Retrieve and serve product image from Cloudinary URL"""
    try:
        product_image = Product_Images.query.get(image_id)

        if not product_image:
            abort(404)

        # Use Cloudinary URL if available
        if product_image.image_url:
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
                'url': img.image_url,  # Direct Cloudinary URL
                'filename': img.filename,
                'mime_type': img.mime_type,
                'is_primary': img.is_primary,
                'created_at': img.created_at.isoformat()
            })
        
        return jsonify({'images': images_data}), 200
    
    except Exception as e:
        print(f"Error getting product images: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500


# SERVE vendor logos from Cloudinary
@app.route('/api/vendor-logo/<int:vendor_id>', methods=['GET'])
def get_vendor_logo(vendor_id):
    """Retrieve and serve vendor logo from Cloudinary URL"""
    try:
        vendor = Vendors.query.get(vendor_id)

        if not vendor:
            abort(404)

        # Use Cloudinary URL if available
        if vendor.logo_url:
            return redirect(vendor.logo_url)
        else:
            abort(404)

    except Exception as e:
        print(f"Error retrieving vendor logo: {str(e)}")
        abort(500)


@app.route('/customer/dashboard')
def customer_dashboard():
    # Redirect to dashboard home
    return redirect(url_for('customer_dashboard_home'))


@app.route('/customer/my-orders')
def customer_my_orders():
    # Client-side will check for token in localStorage
    return render_template('customer/my_orders.html')


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
        # Only distribute funds if payment wasn't already processed
        if order.status != 'completed':
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
        
        # Send payment confirmation email
        try:
            send_payment_confirmation_email(
                user.email,
                user.first_name,
                order.reference_number,
                order.total_amount,
                'Card Payment'
            )
            print(f"[PAYMENT] Payment confirmation email sent to {user.email}")
        except Exception as email_error:
            print(f"[PAYMENT] Error sending payment confirmation email: {str(email_error)}")
        
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
                    # Only distribute funds if payment wasn't already processed
                    if order.status != 'completed':
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
                    
                    # Send order and payment confirmation emails
                    try:
                        customer = order.customer
                        user = customer.user
                        
                        # Prepare items details for email
                        order_items = Order_Items.query.filter_by(order_id=order.id).all()
                        items_details = [
                            {
                                'product_name': item.product.name,
                                'quantity': item.quantity,
                                'price_at_purchase': item.price_at_purchase
                            }
                            for item in order_items
                        ]
                        
                        # Send order confirmation email (if not already sent during checkout)
                        send_order_confirmation_email(
                            user.email,
                            user.first_name,
                            order.reference_number,
                            items_details,
                            order.total_amount
                        )
                        print(f"[PAYMENT-CALLBACK] Order confirmation email sent to {user.email}")
                        
                        # Send payment confirmation email
                        send_payment_confirmation_email(
                            user.email,
                            user.first_name,
                            order.reference_number,
                            order.total_amount,
                            'Card Payment'
                        )
                        print(f"[PAYMENT-CALLBACK] Payment confirmation email sent to {user.email}")
                        
                    except Exception as email_error:
                        print(f"[PAYMENT-CALLBACK] Error sending emails: {str(email_error)}")
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
    return render_template('customer/deposit.html')


@app.route('/customer/deposit-status')
def deposit_status():
    """Display deposit history and status"""
    return render_template('customer/deposit_status.html')


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


@app.route('/api/customer/wallet-transactions', methods=['GET'])
@jwt_required()
def get_customer_wallet_transactions():
    """Get customer's wallet transaction history"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Get wallet
        wallet = Wallet.query.filter_by(customer_id=customer.id).first()
        if not wallet:
            return jsonify({'success': True, 'transactions': [], 'count': 0}), 200
        
        # Get wallet transactions sorted by date (newest first)
        transactions = CustomerWalletTransaction.query.filter_by(
            wallet_id=wallet.id
        ).order_by(CustomerWalletTransaction.created_at.desc()).all()
        
        transactions_data = []
        for transaction in transactions:
            trans_dict = {
                'id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'amount': float(transaction.amount),
                'description': transaction.description or 'Transaction',
                'status': transaction.status,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None
            }
            transactions_data.append(trans_dict)
        
        return jsonify({
            'success': True,
            'transactions': transactions_data,
            'count': len(transactions_data)
        }), 200
    except Exception as e:
        print(f"Error fetching wallet transactions: {str(e)}")
        import traceback
        traceback.print_exc()
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

        # Record wallet transaction for deposit if not already created
        existing_txn = CustomerWalletTransaction.query.filter_by(
            wallet_id=wallet.id,
            transaction_type='credit',
            reference_id=deposit.id
        ).first()
        if not existing_txn:
            wallet_transaction = CustomerWalletTransaction(
                wallet_id=wallet.id,
                transaction_type='credit',
                amount=deposit.amount,
                description=f'Deposit via Paystack: {reference}',
                reference_id=deposit.id,
                status='completed'
            )
            db.session.add(wallet_transaction)
        
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

                # Record wallet transaction for deposit if not already created
                existing_txn = CustomerWalletTransaction.query.filter_by(
                    wallet_id=wallet.id,
                    transaction_type='credit',
                    reference_id=deposit.id
                ).first()
                if not existing_txn:
                    wallet_transaction = CustomerWalletTransaction(
                        wallet_id=wallet.id,
                        transaction_type='credit',
                        amount=deposit.amount,
                        description=f'Deposit via Paystack: {reference}',
                        reference_id=deposit.id,
                        status='completed'
                    )
                    db.session.add(wallet_transaction)
                
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
        
        # Get all completed/paid orders for this customer (single query)
        paid_orders = db.session.query(Orders).join(Payments).filter(
            Orders.customer_id == customer.id,
            Payments.status == 'completed'
        ).all()
        
        # Calculate total spent from paid orders
        total_spent = sum(order.total_amount for order in paid_orders) if paid_orders else 0.0
        total_orders_count = len(paid_orders)
        
        # Get wishlist count
        wishlist = Wishlists.query.filter_by(customer_id=customer.id).first()
        wishlist_count = 0
        if wishlist:
            wishlist_count = Wishlist_Items.query.filter_by(wishlist_id=wishlist.id).count()
        
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


# Customer Address Management API Endpoints

@app.route('/api/customer/addresses', methods=['GET'])
@jwt_required()
def get_customer_addresses():
    """Get all addresses for the current customer"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        addresses = CustomerAddress.query.filter_by(customer_id=customer.id).all()
        
        addresses_data = []
        for address in addresses:
            addr_dict = {
                'id': address.id,
                'label': address.label,
                'address_line1': address.address_line1,
                'address_line2': address.address_line2,
                'city': address.city,
                'state': address.state,
                'postal_code': address.postal_code,
                'country': address.country,
                'phone': address.phone,
                'is_default': address.is_default,
                'created_at': address.created_at.isoformat() if address.created_at else None
            }
            addresses_data.append(addr_dict)
        
        return jsonify({
            'success': True,
            'addresses': addresses_data,
            'count': len(addresses_data)
        }), 200
    except Exception as e:
        print(f"Error fetching addresses: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/addresses', methods=['POST'])
@jwt_required()
def add_customer_address():
    """Add a new address for the current customer"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['address_line1', 'city', 'state', 'postal_code', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # If this is set as default, unset other defaults
        if data.get('is_default', False):
            CustomerAddress.query.filter_by(customer_id=customer.id, is_default=True).update({'is_default': False})
        
        new_address = CustomerAddress(
            customer_id=customer.id,
            label=data.get('label', 'Address'),
            address_line1=data.get('address_line1'),
            address_line2=data.get('address_line2'),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postal_code'),
            country=data.get('country', 'Nigeria'),
            phone=data.get('phone'),
            is_default=data.get('is_default', False)
        )
        
        db.session.add(new_address)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Address added successfully',
            'address_id': new_address.id
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding address: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/addresses/<int:address_id>', methods=['DELETE'])
@jwt_required()
def delete_customer_address(address_id):
    """Delete an address"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        address = CustomerAddress.query.filter_by(id=address_id, customer_id=customer.id).first()
        if not address:
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        db.session.delete(address)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Address deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting address: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/addresses/<int:address_id>/set-default', methods=['POST'])
@jwt_required()
def set_default_address(address_id):
    """Set an address as the default address"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        # Unset all other defaults
        CustomerAddress.query.filter_by(customer_id=customer.id, is_default=True).update({'is_default': False})
        
        # Set this address as default
        address = CustomerAddress.query.filter_by(id=address_id, customer_id=customer.id).first()
        if not address:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        address.is_default = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Default address updated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error setting default address: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/addresses/<int:address_id>', methods=['PUT'])
@jwt_required()
def update_address_api(address_id):
    """Update an existing customer address"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        address = CustomerAddress.query.filter_by(id=address_id, customer_id=customer.id).first()
        if not address:
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        data = request.get_json()
        
        # Update address fields
        address.label = data.get('label', address.label)
        address.address_line1 = data.get('address_line1', address.address_line1)
        address.address_line2 = data.get('address_line2', address.address_line2)
        address.city = data.get('city', address.city)
        address.state = data.get('state', address.state)
        address.postal_code = data.get('postal_code', address.postal_code)
        address.country = data.get('country', address.country)
        address.phone = data.get('phone', address.phone)
        
        # Handle default address change
        if data.get('is_default', False) and not address.is_default:
            CustomerAddress.query.filter_by(customer_id=customer.id, is_default=True).update({'is_default': False})
            address.is_default = True
        elif not data.get('is_default', False):
            address.is_default = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Address updated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating address: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/delivery-preferences', methods=['GET'])
@jwt_required()
def get_delivery_preferences():
    """Get delivery preferences for the current customer"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        preferences = DeliveryPreference.query.filter_by(customer_id=customer.id).first()
        
        if not preferences:
            # Return default preferences if none exist
            return jsonify({
                'success': True,
                'preferences': {
                    'delivery_method': 'standard',
                    'signature_required': False,
                    'leave_at_door': False,
                    'fragile_handling': False,
                    'special_instructions': None
                }
            }), 200
        
        pref_dict = {
            'delivery_method': preferences.delivery_method,
            'signature_required': preferences.signature_required,
            'leave_at_door': preferences.leave_at_door,
            'fragile_handling': preferences.fragile_handling,
            'special_instructions': preferences.special_instructions,
            'created_at': preferences.created_at.isoformat() if preferences.created_at else None
        }
        
        return jsonify({
            'success': True,
            'preferences': pref_dict
        }), 200
    except Exception as e:
        print(f"Error fetching delivery preferences: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/profile', methods=['GET'])
@jwt_required()
def get_customer_profile():
    """Get current customer profile information"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)

        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            # Create customer record if it doesn't exist
            customer = Customers(user_id=user_id, phone='', default_address='')
            db.session.add(customer)
            db.session.commit()

        return jsonify({
            'success': True,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': customer.phone or '',
            'address': customer.default_address or '',
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'profile_image': {
                'url': user.profile_image_url,
                'mime_type': user.profile_image_mime_type,
                'filename': user.profile_image_filename,
                'data': base64.b64encode(user.profile_image_data).decode('utf-8') if user.profile_image_data else None
            } if (user.profile_image_url or user.profile_image_data) else None
        }), 200
    except Exception as e:
        print(f"Error fetching customer profile: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500




@app.route('/api/customer/change-password', methods=['POST'])
@jwt_required()
def change_customer_password():
    """Change customer account password"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)

        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()

        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Both current and new passwords are required'}), 400

        if not check_password_hash(user.passwordhash, current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'New password must be at least 8 characters long'}), 400

        user.passwordhash = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/delivery-preferences', methods=['POST'])
@jwt_required()
def save_delivery_preferences():
    """Save or update delivery preferences for the current customer"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)
        
        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer profile not found'}), 404
        
        data = request.get_json()
        
        preferences = DeliveryPreference.query.filter_by(customer_id=customer.id).first()
        
        if preferences:
            # Update existing preferences
            preferences.delivery_method = data.get('delivery_method', preferences.delivery_method)
            preferences.signature_required = data.get('signature_required', preferences.signature_required)
            preferences.leave_at_door = data.get('leave_at_door', preferences.leave_at_door)
            preferences.fragile_handling = data.get('fragile_handling', preferences.fragile_handling)
            preferences.special_instructions = data.get('special_instructions', preferences.special_instructions)
        else:
            # Create new preferences
            preferences = DeliveryPreference(
                customer_id=customer.id,
                delivery_method=data.get('delivery_method', 'standard'),
                signature_required=data.get('signature_required', False),
                leave_at_door=data.get('leave_at_door', False),
                fragile_handling=data.get('fragile_handling', False),
                special_instructions=data.get('special_instructions')
            )
            db.session.add(preferences)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Delivery preferences saved successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error saving delivery preferences: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/account-settings', methods=['PUT'])
@jwt_required()
def update_customer_account_settings():
    """Update customer account settings"""
    try:
        user_id = int(get_jwt_identity())
        user = Users.query.get(user_id)

        if not user or user.role.name != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            # Create customer record if it doesn't exist
            customer = Customers(user_id=user_id, phone='', default_address='')
            db.session.add(customer)

        data = request.get_json()
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()

        if not first_name or not last_name or not email:
            return jsonify({'success': False, 'message': 'First name, last name, and email are required'}), 400

        existing_user = Users.query.filter(Users.email == email, Users.id != user.id).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email is already in use'}), 400

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        customer.phone = phone or customer.phone
        customer.default_address = address or customer.default_address

        db.session.commit()

        return jsonify({'success': True, 'message': 'Account settings updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating account settings: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/customer/profile-image', methods=['POST'])
@jwt_required()
def upload_customer_profile_image():
    """Upload or update customer profile image to Cloudinary"""
    print("Profile image upload endpoint called")
    try:
        user_id = int(get_jwt_identity())
        print(f"User ID: {user_id}")
        user = Users.query.get(user_id)

        if not user or user.role.name != 'customer':
            print("User not found or not a customer")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        if 'profile_image' not in request.files:
            print("No profile_image in request.files")
            return jsonify({'success': False, 'message': 'No image file provided'}), 400

        file = request.files['profile_image']
        print(f"File received: {file.filename}")
        if file.filename == '':
            print("Empty filename")
            return jsonify({'success': False, 'message': 'No image file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not file or '.' not in file.filename:
            print("Invalid file or no extension")
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400

        extension = file.filename.rsplit('.', 1)[1].lower()
        if extension not in allowed_extensions:
            print(f"Extension not allowed: {extension}")
            return jsonify({'success': False, 'message': 'Only PNG, JPG, JPEG, and GIF files are allowed'}), 400

        # Upload to Cloudinary
        image_url = upload_to_cloudinary(file, folder="ikeja_online/profiles")

        if not image_url:
            print("Failed to upload profile image to Cloudinary")
            return jsonify({'success': False, 'message': 'Failed to upload image'}), 500

        # Update user profile image
        user.profile_image_url = image_url
        user.profile_image_data = None  # Clear binary data since we're using URL now
        user.profile_image_mime_type = f'image/{extension}'
        if extension == 'jpg':
            user.profile_image_mime_type = 'image/jpeg'
        user.profile_image_filename = secure_filename(file.filename)

        db.session.commit()
        print("Profile image updated successfully")

        return jsonify({
            'success': True,
            'message': 'Profile image updated successfully',
            'image': {
                'url': image_url,
                'filename': user.profile_image_filename,
                'mime_type': user.profile_image_mime_type
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading profile image: {str(e)}")
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
        
        # Handle logo removal
        remove_logo = request.form.get('remove_logo')
        if remove_logo == 'true':
            vendor.logo_data = None
            vendor.logo_mime_type = None
            vendor.logo_url = None
            print("Logo removed from database")
        
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
            'message': 'Profile Settings updated successfully',
            'logo_url': vendor.logo_url
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
            'logo_url': vendor.logo_url if vendor.logo_url else (f'/api/vendor-logo/{vendor.id}' if vendor.logo_data else None)
        },
        'user': {
            'email': user.email,
            'username': user.email,  # Using email as username
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    }), 200

@app.route('/vendor/dashboard/change-password', methods=['POST'])
@jwt_required()
def vendor_change_password():
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)

    if not user or user.role.name != 'vendor':
        return jsonify({'error': 'Unauthorized', 'message': 'Only vendors can change password'}), 403

    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        if not current_password or not new_password:
            return jsonify({'error': 'Bad Request', 'message': 'Current password and new password are required'}), 400

        # Verify current password
        if not check_password_hash(user.passwordhash, current_password):
            return jsonify({'error': 'Unauthorized', 'message': 'Current password is incorrect'}), 401

        # Validate new password strength
        if len(new_password) < 8:
            return jsonify({'error': 'Bad Request', 'message': 'New password must be at least 8 characters long'}), 400

        # Password strength validation
        import re
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]', new_password):
            return jsonify({'error': 'Bad Request', 'message': 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'}), 400

        # Update password
        user.passwordhash = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Server Error', 'message': f'Failed to change password: {str(e)}'}), 500

@app.route('/vendor/dashboard/get-vendor-settings-page')
def get_vendor_settings_page():
    # Client-side will check for token in localStorage
    # Frontend will validate authentication before showing sensitive data
    return render_template('vendor/vendor-settings.html')


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


@app.route('/api/vendor/earnings', methods=['GET'])
@jwt_required()
def get_vendor_earnings():
    """Get vendor's earnings summary and history"""
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
            wallet = VendorWallet(vendor_id=vendor.id, balance=0.0, total_earned=0.0)
            db.session.add(wallet)
            db.session.commit()
        
        # Get vendor's products
        products = Products.query.filter_by(vendor_id=vendor.id).all()
        product_ids = [p.id for p in products]
        
        # Calculate earnings from completed orders
        total_earnings = 0.0
        monthly_earnings = 0.0
        product_sales = 0.0
        commissions = 0.0
        refunds = 0.0
        fees = 0.0
        total_orders = 0
        monthly_revenue_map = {}
        completed_order_ids = set()
        
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        earnings_history = []
        
        if product_ids:
            # Get all order items for vendor's products
            order_items = db.session.query(Order_Items).filter(
                Order_Items.product_id.in_(product_ids)
            ).all()
            
            for item in order_items:
                order = Orders.query.get(item.order_id)
                if not order:
                    continue
                    
                payment = Payments.query.filter_by(order_id=order.id).first()
                if not payment or payment.status != 'completed':
                    continue
                
                completed_order_ids.add(order.id)
                
                # Calculate earnings for this item
                item_earnings = item.price_at_purchase * item.quantity
                total_earnings += item_earnings
                product_sales += item_earnings
                
                # Check if this is current month
                if (order.created_at.month == current_month and 
                    order.created_at.year == current_year):
                    monthly_earnings += item_earnings

                order_month = order.created_at.strftime('%Y-%m')
                monthly_revenue_map[order_month] = monthly_revenue_map.get(order_month, 0.0) + item_earnings
                
                # Add to earnings history
                earnings_history.append({
                    'date': order.created_at.isoformat(),
                    'type': 'Sale',
                    'amount': float(item_earnings),
                    'description': f'Sale of {item.product.name} (x{item.quantity})',
                    'status': 'Completed'
                })
        
        total_orders = len(completed_order_ids)
        monthly_revenue = [
            {'month': month, 'revenue': float(amount)}
            for month, amount in sorted(monthly_revenue_map.items())
        ]
        
        # Get pending payout (available balance)
        pending_payout = wallet.balance
        
        # Sort earnings history by date (most recent first)
        earnings_history.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'success': True,
            'earnings': {
                'total_earnings': float(total_earnings),
                'monthly_earnings': float(monthly_earnings),
                'pending_payout': float(pending_payout),
                'product_sales': float(product_sales),
                'commissions': float(commissions),
                'refunds': float(refunds),
                'fees': float(fees),
                'total_orders': total_orders,
                'monthly_revenue': monthly_revenue
            },
            'earnings_history': earnings_history[:50]  # Limit to last 50 entries
        }), 200
        
    except Exception as e:
        print(f"Error getting vendor earnings: {str(e)}")
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
        
        # Send vendor payout email
        try:
            payout_method = f"{bank_name} - {account_number}"
            send_vendor_payout_email(
                user.email,
                vendor.store_name or user.first_name,
                amount,
                payout_method
            )
            print(f"[WITHDRAWAL] Vendor payout email sent to {user.email}")
        except Exception as email_error:
            print(f"[WITHDRAWAL] Error sending vendor payout email: {str(email_error)}")
        
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
        
        # Get vendor wallet
        wallet = VendorWallet.query.filter_by(vendor_id=vendor.id).first()
        if not wallet:
            return jsonify({'success': True, 'transactions': []}), 200
        
        # Get transactions for this vendor's wallet
        transactions = VendorWalletTransaction.query.filter_by(vendor_wallet_id=wallet.id).order_by(VendorWalletTransaction.created_at.desc()).all()
        
        transactions_list = [
            {
                'id': t.id,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'status': t.status,
                'reference_id': t.reference_id,
                'description': t.description,
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
                item_total = float(item.price_at_purchase) * item.quantity
                vendor_total += item_total
                items.append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name,
                    'quantity': item.quantity,
                    'price': float(item.price_at_purchase),
                    'total': item_total
                })
        
        return jsonify({'success': True,
            'order': {
                'id': order.id,
                'reference_number': order.reference_number,
                'customer_name': f"{customer_user.first_name} {customer_user.last_name}" if customer_user else 'Unknown',
                'customer_email': customer_user.email if customer_user else 'unknown@email.com',
                'customer_phone': customer.phone if customer else '',
                'customer_address': customer.default_address if customer else '',
                'delivery_address': customer.default_address if customer else '',
                'total_amount': float(order.total_amount),
                'subtotal': float(order.total_amount),
                'status': order.status or 'pending',
                'payment_status': payment_status,
                'payment_method': payment_method,
                'payment_amount': payment_amount,
                'shipping_status': order.shipping_status or 'pending',
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
        old_status = order.shipping_status
        order.shipping_status = new_status
        db.session.commit()
        
        # Send email for any shipping status change
        if new_status != old_status:
            try:
                tracking_number = data.get('tracking_number', None)
                send_order_shipped_email(
                    order.customer.user.email,
                    order.customer.user.first_name,
                    order.reference_number,
                    tracking_number,
                    new_status
                )
                print(f"[SHIPPING] Order status email sent to {order.customer.user.email} - New status: {new_status}")
            except Exception as email_error:
                print(f"[SHIPPING] Error sending order status email: {str(email_error)}")
        
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
    return render_template('customer/browse_products.html')


@app.route('/categories')
def view_all_categories():
    # Guest-accessible categories page
    return render_template('categories/all_categories.html')


@app.route('/product/<int:product_id>')
def view_product_details(product_id):
    # Guest-accessible product details page
    return render_template('product_details.html')


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
    return render_template('admin/admin_dashboard.html')


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
    return render_template('customer/browse_products.html')


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
                'status': product.status,
                'images': [{'id': img.id, 'url': f'/api/product-image/{img.id}', 'is_primary': img.is_primary} for img in product.images],
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
    return render_template('customer/customer-settings.html')


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
        
        # Check for low stock items and send alerts to vendors
        try:
            vendors_low_stock = {}
            for item in order_items:
                # Check if product stock is now below 5
                if item['product'].stock_quantity < 5:
                    vendor_id = item['product'].vendor_id
                    if vendor_id not in vendors_low_stock:
                        vendors_low_stock[vendor_id] = []
                    vendors_low_stock[vendor_id].append({
                        'product_name': item['product'].name,
                        'stock_quantity': item['product'].stock_quantity,
                        'price': item['product'].price
                    })
            
            # Send low stock alerts to vendors
            for vendor_id, low_stock_products in vendors_low_stock.items():
                vendor = Vendors.query.get(vendor_id)
                if vendor and vendor.user:
                    send_low_stock_alert_email(
                        vendor.user.email,
                        vendor.user.first_name,
                        vendor.store_name or vendor.user.first_name,
                        low_stock_products
                    )
                    print(f"[CHECKOUT] Low stock alert email sent to {vendor.user.email}")
        except Exception as low_stock_error:
            print(f"[CHECKOUT] Error sending low stock alerts: {str(low_stock_error)}")
        
        # Send order confirmation email to customer
        try:
            items_details = [
                {
                    'product_name': item['product'].name,
                    'quantity': item['quantity'],
                    'price_at_purchase': item['price_at_purchase']
                }
                for item in order_items
            ]
            send_order_confirmation_email(
                user.email,
                user.first_name,
                order.reference_number,
                items_details,
                order.total_amount
            )
            print(f"[CHECKOUT] Order confirmation email sent to {user.email}")
        except Exception as email_error:
            print(f"[CHECKOUT] Error sending order confirmation email: {str(email_error)}")
        
        # Send order notification emails to vendors
        try:
            # Group items by vendor
            vendors_orders = {}
            for item in order_items:
                vendor_id = item['product'].vendor_id
                if vendor_id not in vendors_orders:
                    vendors_orders[vendor_id] = []
                vendors_orders[vendor_id].append(item)
            
            # Send email to each vendor
            for vendor_id, vendor_items in vendors_orders.items():
                vendor = Vendors.query.get(vendor_id)
                if vendor and vendor.user:
                    products_info = [
                        {
                            'product_name': item['product'].name,
                            'quantity': item['quantity'],
                            'price': item['price_at_purchase']
                        }
                        for item in vendor_items
                    ]
                    
                    send_product_ordered_email(
                        vendor.user.email,
                        vendor.user.first_name,
                        vendor.store_name or vendor.user.first_name,
                        products_info,
                        order.reference_number,
                        f"{user.first_name} {user.last_name}",
                        order.total_amount
                    )
                    print(f"[CHECKOUT] Vendor order email sent to {vendor.user.email}")
        except Exception as vendor_email_error:
            print(f"[CHECKOUT] Error sending vendor emails: {str(vendor_email_error)}")
        
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
        
        print(f"[GET-ORDER-DETAILS] Fetching order {order_id} for user {user_id}")
        
        if not user or user.role.name != 'customer':
            print(f"[GET-ORDER-DETAILS] Unauthorized: user not found or not a customer")
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get customer record
        customer = Customers.query.filter_by(user_id=user_id).first()
        if not customer:
            print(f"[GET-ORDER-DETAILS] Customer record not found for user {user_id}")
            return jsonify({'success': False, 'error': 'Not Found'}), 404
        
        # Get order
        order = Orders.query.get(order_id)
        if not order:
            print(f"[GET-ORDER-DETAILS] Order {order_id} not found")
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Verify customer owns this order
        if order.customer_id != customer.id:
            print(f"[GET-ORDER-DETAILS] Order {order_id} does not belong to customer {customer.id}")
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'You do not own this order'}), 403
        
        # Build order details
        order_dict = {
            'id': order.id,
            'reference_number': order.reference_number,
            'customer_name': f"{user.first_name} {user.last_name}",
            'customer_email': user.email,
            'customer_phone': customer.phone or 'Not provided',
            'customer_address': customer.default_address or 'Not provided',
            'total_amount': float(order.total_amount),
            'status': order.status or 'pending',
            'payment_status': 'pending',
            'shipping_status': order.shipping_status or 'pending',
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'items': []
        }
        
        # Get payment status
        payment = Payments.query.filter_by(order_id=order.id).first()
        if payment:
            order_dict['payment_status'] = payment.status or 'pending'
        
        # Add order items
        for item in order.items:
            item_dict = {
                'product_id': item.product_id,
                'product_name': item.product.name if item.product else 'Unknown Product',
                'quantity': item.quantity,
                'price_at_purchase': float(item.price_at_purchase),
                'total': float(item.quantity * item.price_at_purchase)
            }
            order_dict['items'].append(item_dict)
        
        print(f"[GET-ORDER-DETAILS] Successfully retrieved order {order_id} with {len(order_dict['items'])} items")
        
        return jsonify({
            'success': True,
            'order': order_dict
        }), 200
    except Exception as e:
        print(f"[GET-ORDER-DETAILS] Error fetching order details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Server Error', 'message': str(e)}), 500

@app.route('/vendor/dashboard/home')
def vendor_dashboard_home():
    return render_template('dist/includes/vendor/vendordashboard_home.html')

@app.route('/customer/dashboard/home')
def customer_dashboard_home():
    return render_template('dist/includes/customer/customerdashboard_home.html')

@app.route('/customer/dashboard/browse-products')
def customer_dashboard_browse_products():
    return render_template('dist/includes/customer/browse_products.html')

@app.route('/customer/dashboard/categories')
def customer_dashboard_categories():
    return render_template('dist/includes/customer/categories.html')

@app.route('/customer/dashboard/wishlist')
def customer_dashboard_wishlist():
    return render_template('dist/includes/customer/wishlist.html')

@app.route('/customer/dashboard/orders')
def customer_dashboard_orders():
    return render_template('dist/includes/customer/customer_orders.html')

@app.route('/customer/dashboard/order-tracking')
def customer_dashboard_order_tracking():
    return render_template('dist/includes/customer/order_tracking.html')

@app.route('/customer/dashboard/order-history')
def customer_dashboard_order_history():
    return render_template('dist/includes/customer/order_history.html')

@app.route('/customer/dashboard/cancel-orders')
def customer_dashboard_cancel_orders():
    return render_template('dist/includes/customer/cancel_orders.html')

@app.route('/customer/dashboard/returns-refunds')
def customer_dashboard_returns_refunds():
    return render_template('dist/includes/customer/returns_refunds.html')

@app.route('/customer/dashboard/transaction-history')
def customer_dashboard_transaction_history():
    return render_template('dist/includes/customer/transaction_history.html')

@app.route('/customer/dashboard/profile-info')
def customer_dashboard_profile_info():
    return render_template('dist/includes/customer/profile_info.html')

@app.route('/customer/dashboard/account-settings')
def customer_dashboard_account_settings():
    return render_template('dist/includes/customer/account_settings.html')

@app.route('/customer/dashboard/security')
def customer_dashboard_security():
    return render_template('dist/includes/customer/security.html')

@app.route('/customer/dashboard/address-book')
def customer_dashboard_address_book():
    return render_template('dist/includes/customer/address_book.html')

@app.route('/customer/dashboard/add-address')
def customer_dashboard_add_address():
    return render_template('dist/includes/customer/add_address.html')

@app.route('/customer/dashboard/delivery-preferences')
def customer_dashboard_delivery_preferences():
    return render_template('dist/includes/customer/delivery_preferences.html')

@app.route('/customer/dashboard/edit-address/<int:address_id>')
def customer_dashboard_edit_address(address_id):
    return render_template('dist/includes/customer/edit_address.html')

@app.route('/testingdashboard')
def testdashboard():
    return render_template('dist/includes/vendor/vendordashboard_home.html')

@app.route('/testingdashboard2')
def testdashboard2():
    return render_template('dist/includes/customerdashboard_home.html')

@app.route('/testingdashboard3')
def testdashboard3():
    return render_template('dist/marketplace-dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
