# Email System Implementation Guide - Ikeja Online

## ✅ Phase 1: Implemented (Password, Order, Shipped)

### 1. **Password Reset Email**
**Function:** `send_password_reset_email(user_email, user_name, reset_token)`
**Route:** `/forgot-password` (POST/GET)
**Token Expiry:** 1 hour
**Usage:**
```python
send_password_reset_email(user.email, user.first_name, reset_token)
```
**Template:** `reset_password.html`
**Features:**
- Security warning in email
- 1-hour expiration
- Token stored in database for validation

---

### 2. **Order Confirmation Email**
**Function:** `send_order_confirmation_email(customer_email, customer_name, order_ref, items_details, total_amount)`
**Usage Example:**
```python
items = [
    {
        'product_name': 'Laptop',
        'quantity': 1,
        'price_at_purchase': 150000
    }
]
send_order_confirmation_email(
    'customer@email.com',
    'John Doe',
    'ORD-12345',
    items,
    150000
)
```
**Features:**
- Itemized order details table
- Order reference number
- Total amount breakdown
- Track order button

---

### 3. **Order Shipped Email**
**Function:** `send_order_shipped_email(customer_email, customer_name, order_ref, tracking_number=None)`
**Usage Example:**
```python
send_order_shipped_email(
    'customer@email.com',
    'John Doe',
    'ORD-12345',
    'TRACK-ABC123'
)
```
**Features:**
- Shipping confirmation
- Optional tracking number
- Expected delivery timeframe
- Track order button

---

## ✅ Phase 2: Implemented (Payment, Payout, Account Confirmation)

### 4. **Payment Confirmation Email**
**Function:** `send_payment_confirmation_email(customer_email, customer_name, order_ref, amount, payment_method)`
**Usage Example:**
```python
send_payment_confirmation_email(
    'customer@email.com',
    'John Doe',
    'ORD-12345',
    150000,
    'Credit Card'
)
```
**Features:**
- Payment amount and method
- Timestamp
- Receipt reference number
- Order processing status

---

### 5. **Vendor Payout Email**
**Function:** `send_vendor_payout_email(vendor_email, vendor_name, payout_amount, payout_method)`
**Usage Example:**
```python
send_vendor_payout_email(
    'vendor@email.com',
    'Store Name',
    50000,
    'Bank Transfer'
)
```
**Features:**
- Payout amount
- Payment method
- Processing date
- Delivery timeline (1-2 business days)

---

### 6. **Account Confirmation Email**
**Function:** `send_account_confirmation_email(user_email, user_name, action_type, confirmation_token)`
**Supported Actions:** 
- `email_change` - Email address change
- `password_change` - Password change  
- `profile_update` - Profile update
**Usage Example:**
```python
token = generate_email_verification_token(user.id)  # Returns token
send_account_confirmation_email(
    'user@email.com',
    'John Doe',
    'email_change',
    token
)
```
**Route:** `/confirm-action/<token>`
**Token Expiry:** 24 hours
**Features:**
- Confirmation link with 24-hour expiration
- Security warning
- Action type specified

---

## 🔧 How to Integrate Into Your Existing Routes

### **For Order Confirmation (in checkout/order creation route):**
```python
@app.route('/checkout', methods=['POST'])
def checkout():
    # ... existing code ...
    
    # After order is created and payment processed:
    items_details = [
        {
            'product_name': product.name,
            'quantity': item.quantity,
            'price_at_purchase': item.price_at_purchase
        }
        for item in order.items
    ]
    
    send_order_confirmation_email(
        customer.user.email,
        customer.user.first_name,
        order.reference_number,
        items_details,
        order.total_amount
    )
```

### **For Payment Confirmation (in payment endpoint):**
```python
@app.route('/process-payment', methods=['POST'])
def process_payment():
    # ... payment processing code ...
    
    # After payment success:
    payment = Payments.query.get(payment_id)
    send_payment_confirmation_email(
        order.customer.user.email,
        order.customer.user.first_name,
        order.reference_number,
        payment.amount,
        payment.payment_method
    )
```

### **For Order Shipped (in vendor order update):**
```python
@app.route('/vendor/orders/<order_id>/ship', methods=['POST'])
@jwt_required()
def ship_order(order_id):
    # ... update order status ...
    
    order = Orders.query.get(order_id)
    tracking_number = request.form.get('tracking_number')
    
    send_order_shipped_email(
        order.customer.user.email,
        order.customer.user.first_name,
        order.reference_number,
        tracking_number
    )
```

### **For Vendor Payout (in withdrawal endpoint):**
```python
@app.route('/vendor/wallet/withdraw', methods=['POST'])
@jwt_required()
def withdraw_funds():
    # ... create withdrawal record ...
    
    vendor = Vendors.query.get(vendor_id)
    withdrawal_amount = request.form.get('amount')
    payout_method = request.form.get('method')
    
    send_vendor_payout_email(
        vendor.user.email,
        vendor.user.first_name,
        withdrawal_amount,
        payout_method
    )
```

---

## 📝 Routes Added

1. **`/forgot-password`** (POST/GET) - Password reset request
2. **`/reset-password/<token>`** (POST/GET) - Reset password form & processing
3. **`/confirm-action/<token>`** (GET) - Confirm sensitive account changes

---

## ✨ Email Template Features

All emails include:
- ✅ Professional gradient backgrounds & styling
- ✅ Brand colors (Orange #FF6B35)
- ✅ Security warnings where applicable
- ✅ Call-to-action buttons
- ✅ Responsive design for mobile
- ✅ Clear typography and spacing
- ✅ Footer with Ikeja Online branding

---

## 🔐 Security Features

- **Token Validation:** All tokens validated before action
- **Expiration:** Password reset (1 hour), Email verification (24 hours)
- **Database Storage:** Password reset tokens stored in database
- **SQL Injection Prevention:** Using ORM queries
- **Email Verification:** Account confirmation required for sensitive changes

---

## 📊 Database Changes

Added to `Users` model:
- `password_reset_token` (String, nullable)
- `password_reset_expires` (DateTime, nullable)

Migration applied: ✅ `add_password_reset_fields.py`

---

## 🎯 Next Steps

1. Test password reset flow
2. Integrate emails into order/payment routes
3. Test vendor payout emails
4. Customize email templates with actual branding
5. Consider adding email templates to database for easy management

