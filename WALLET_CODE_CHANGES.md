# Wallet Payment - Code Changes Reference

## Overview of Changes

This document lists all the code changes made to implement wallet payment functionality.

---

## Frontend Changes (home.html)

### 1. HTML - Wallet Card (Line ~2027)

**Before:**
```html
<!-- Wallet Payment Method (Future) -->
<div class="payment-method-card" data-method="wallet" style="opacity: 0.6; cursor: not-allowed;">
    <div class="payment-method-icon">
        <i class="fas fa-digital-tachograph"></i>
    </div>
    <h3>Wallet</h3>
    <p>Pay from your Ikeja Online wallet</p>
    <div class="payment-method-features">
        <span><i class="fas fa-check-circle"></i> Instant Checkout</span>
        <span><i class="fas fa-check-circle"></i> Earn Rewards</span>
    </div>
    <div class="coming-soon-badge">Coming Soon</div>
</div>
```

**After:**
```html
<!-- Wallet Payment Method -->
<div class="payment-method-card" data-method="wallet">
    <div class="payment-method-icon">
        <i class="fas fa-wallet"></i>
    </div>
    <h3>Wallet</h3>
    <p>Pay from your Ikeja Online wallet</p>
    <div class="payment-method-features">
        <span><i class="fas fa-check-circle"></i> Instant Checkout</span>
        <span><i class="fas fa-check-circle"></i> Zero Fees</span>
    </div>
    <div id="walletBalanceDisplay" style="margin-top: 8px; font-size: 0.85rem; color: var(--orange); font-weight: 600;">Balance: ₦0.00</div>
</div>
```

**Key Changes:**
- Removed `style="opacity: 0.6; cursor: not-allowed;"`
- Changed icon from `fa-digital-tachograph` to `fa-wallet`
- Removed `coming-soon-badge`
- Added `walletBalanceDisplay` div with real-time balance

---

### 2. HTML - Warning Box (Line ~2050)

**Added New Element:**
```html
<div id="walletWarning" class="payment-info-box" style="display: none; border-left-color: var(--orange); background: rgba(255,107,53,0.1);">
    <i class="fas fa-exclamation-triangle" style="color: var(--orange);"></i>
    <p id="walletWarningText">Your wallet balance is insufficient for this purchase. Please select another payment method or add funds to your wallet.</p>
</div>

<div class="payment-info-box">
    <!-- ... existing security notice ... -->
</div>
```

**Purpose:** Display warning when wallet balance is insufficient

---

### 3. JavaScript - Cart Manager Functions (Line ~2598)

**Added Three New Methods:**

#### A. `loadWalletBalanceForModal()`
```javascript
loadWalletBalanceForModal: async function() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    try {
        const response = await fetch('/api/wallet', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            const balance = parseFloat(data.balance || 0);
            localStorage.setItem('wallet_balance', balance.toString());
            
            // Update wallet balance display in modal
            const balanceDisplay = document.getElementById('walletBalanceDisplay');
            if (balanceDisplay) {
                balanceDisplay.textContent = 'Balance: ₦' + balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            }
            
            // Check if selected payment is wallet and enable/disable button
            if (this.selectedPaymentMethod === 'wallet') {
                const cartTotal = this.cart ? this.cart.getCartTotal() : 0;
                const confirmBtn = document.getElementById('paymentModalConfirmBtn');
                const walletWarning = document.getElementById('walletWarning');
                
                if (balance < cartTotal) {
                    if (walletWarning) {
                        walletWarning.style.display = 'flex';
                    }
                    if (confirmBtn) {
                        confirmBtn.disabled = true;
                        confirmBtn.textContent = 'Insufficient Wallet Balance';
                    }
                } else {
                    if (walletWarning) {
                        walletWarning.style.display = 'none';
                    }
                    if (confirmBtn) {
                        confirmBtn.disabled = false;
                        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Proceed with Payment';
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error loading wallet balance:', error);
    }
},
```

**Purpose:** Fetch and display wallet balance, validate payment capability

---

#### B. Updated `selectPaymentMethod()`
```javascript
selectPaymentMethod: function(method) {
    const cards = document.querySelectorAll('.payment-method-card');
    const confirmBtn = document.getElementById('paymentModalConfirmBtn');
    const walletWarning = document.getElementById('walletWarning');
    
    cards.forEach(card => {
        if (card.dataset.method === method && !card.style.opacity) {
            card.classList.add('selected');
            this.selectedPaymentMethod = method;
            if (confirmBtn) {
                confirmBtn.disabled = false;
            }
            
            // If wallet is selected, check balance
            if (method === 'wallet') {
                const cartTotal = this.cart ? this.cart.getCartTotal() : 0;
                const walletBalance = parseFloat(localStorage.getItem('wallet_balance') || '0');
                
                if (walletBalance < cartTotal) {
                    // Show warning
                    if (walletWarning) {
                        walletWarning.style.display = 'flex';
                    }
                    confirmBtn.disabled = true;
                    confirmBtn.textContent = 'Insufficient Wallet Balance';
                } else {
                    // Hide warning
                    if (walletWarning) {
                        walletWarning.style.display = 'none';
                    }
                    confirmBtn.disabled = false;
                    confirmBtn.innerHTML = '<i class="fas fa-check"></i> Proceed with Payment';
                }
            } else {
                // Hide wallet warning for other methods
                if (walletWarning) {
                    walletWarning.style.display = 'none';
                }
                confirmBtn.innerHTML = '<i class="fas fa-check"></i> Proceed with Payment';
            }
        } else {
            card.classList.remove('selected');
        }
    });
}
```

**Changes from original:**
- Added balance validation logic
- Added warning display/hide logic
- Added button state management based on balance
- Updated button text for insufficient balance

---

#### C. Updated `proceedWithCheckout()`

**Original:**
```javascript
if (data.success && data.authorization_url) {
    // Paystack flow...
} else if (data.order) {
    // Error flow...
} else {
    // Generic error...
}
```

**Updated:**
```javascript
if (data.success) {
    // Clear cart after successful order
    this.cart.clearCart();
    this.closeCart();
    
    if (data.payment_method === 'wallet') {
        // Wallet payment completed immediately
        this.cart.showCartNotification('Payment completed with wallet!');
        
        setTimeout(() => {
            window.location.href = '/customer/my-orders';
        }, 1500);
    } else if (data.authorization_url) {
        // Paystack payment - redirect to payment page
        this.cart.showCartNotification('Redirecting to payment...');
        
        setTimeout(() => {
            window.location.href = data.authorization_url;
        }, 1000);
    } else {
        // Unknown payment method
        this.cart.showCartNotification('Order created successfully!');
        
        setTimeout(() => {
            window.location.href = '/customer/my-orders';
        }, 1500);
    }
} else if (data.message === 'Insufficient wallet balance') {
    // Handle insufficient balance
    // ... show alert with shortfall amount ...
    this.openPaymentModal();
} else if (data.order) {
    // Order created but payment failed...
} else {
    // Generic error...
}
```

**Key Addition:** Handle wallet payment success (no authorization_url) and insufficient balance error

---

### 4. JavaScript - Event Listeners (Line ~2888)

**Updated Wallet Selection Click Handler:**

**Before:**
```javascript
paymentMethodCards.forEach(card => {
    card.addEventListener('click', () => {
        // Only allow clicking on the Paystack payment method for now
        if (card.dataset.method === 'paystack' && !card.style.opacity) {
            window.cartManager.selectPaymentMethod(card.dataset.method);
        }
    });
});
```

**After:**
```javascript
paymentMethodCards.forEach(card => {
    card.addEventListener('click', () => {
        // Allow clicking on enabled payment methods
        const method = card.dataset.method;
        const isEnabled = !card.style.opacity || card.style.opacity === '';
        
        if (isEnabled) {
            if (method === 'wallet') {
                // Check if user is logged in and has wallet
                const token = localStorage.getItem('access_token');
                if (!token) {
                    alert('Please log in to use wallet payment');
                    return;
                }
                window.cartManager.selectPaymentMethod(method);
            } else if (method === 'paystack') {
                window.cartManager.selectPaymentMethod(method);
            }
        }
    });
});
```

**Key Changes:**
- Now allows wallet selection (not just paystack)
- Checks login status before allowing wallet payment
- Better method detection logic

---

**Added Wallet Balance Loading Hook:**

```javascript
// Load wallet balance when modal is opened
const originalOpenModal = window.cartManager.openPaymentModal;
window.cartManager.openPaymentModal = function() {
    originalOpenModal.call(this);
    window.cartManager.loadWalletBalanceForModal();
};
```

**Purpose:** Load wallet balance whenever payment modal opens

---

## Backend Changes (app.py)

### 1. Updated Payment Method Validation (Line ~2507)

**Before:**
```python
# Get cart items from request
data = request.get_json()
items = data.get('items', [])
payment_method = data.get('payment_method', 'paystack').lower()

# Validate payment method
valid_payment_methods = ['paystack', 'bank-transfer', 'wallet']
if payment_method not in valid_payment_methods:
    return jsonify({'success': False, 'message': f'Invalid payment method. Supported methods: {", ".join(valid_payment_methods)}'}), 400

# Currently, only Paystack is supported
if payment_method != 'paystack':
    return jsonify({'success': False, 'message': f'{payment_method} payment method is coming soon'}), 400
```

**After:**
```python
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
```

**Key Change:** Changed `!=` to `not in` to allow both 'paystack' and 'wallet'

---

### 2. Updated Payment Processing (Line ~2588)

**Before:**
```python
db.session.commit()

# ===== Now initialize Paystack payment =====
try:
    paystack_url = 'https://api.paystack.co/transaction/initialize'
    # ... Paystack code ...
```

**After:**
```python
db.session.commit()

# ===== Handle payment based on payment method =====
if payment_method == 'wallet':
    # Process wallet payment
    return process_wallet_payment(order, user, customer)
else:
    # Process Paystack payment (default)
    return process_paystack_payment(order, user)
```

**Key Change:** Router logic to handle different payment methods

---

### 3. New Function: `process_wallet_payment()` (Line ~2603)

**Added complete new function:**
```python
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
        wallet_transaction = WalletTransaction(
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
```

**What it does:**
1. Gets or creates customer wallet
2. Validates sufficient balance
3. Deducts amount from wallet
4. Creates payment record (completed status)
5. Creates wallet transaction record
6. Updates order to "paid" status
7. Returns success with wallet details

---

### 4. Refactored Function: `process_paystack_payment()` (Line ~2678)

**Original Paystack code was extracted into this function:**
```python
def process_paystack_payment(order, user):
    """Process payment using Paystack"""
    try:
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {app.config["TEST_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        # ... rest of Paystack code ...
```

**No logic changes**, just code organization

---

## Database Changes

### No Schema Changes Required
All database tables already exist:
- `Wallet` - Stores wallet balances
- `WalletTransaction` - Tracks all wallet transactions  
- `Payments` - Stores payment records
- `Orders` - Stores order info with status

### New Records Created
When wallet payment succeeds:

**Payments Table Entry:**
```
INSERT INTO payments (order_id, amount, payment_method, transaction_id, status, created_at)
VALUES (order_id, total_amount, 'wallet', 'WALLET-{order_id}-{timestamp}', 'completed', now())
```

**WalletTransaction Table Entry:**
```
INSERT INTO wallet_transaction (wallet_id, transaction_type, amount, description, reference_id, status, created_at)
VALUES (wallet_id, 'debit', total_amount, 'Order payment: {reference_number}', order_id, 'completed', now())
```

**Updated Records:**
```
UPDATE wallet SET balance = balance - amount WHERE id = wallet_id
UPDATE orders SET status = 'paid' WHERE id = order_id
```

---

## Summary of Changes

| Component | Change | Lines |
|-----------|--------|-------|
| **HTML** | Enabled wallet card | ~2027 |
| **HTML** | Added warning box | ~2050 |
| **JS** | New `loadWalletBalanceForModal()` | ~2635 |
| **JS** | Updated `selectPaymentMethod()` | ~2623 |
| **JS** | Updated `proceedWithCheckout()` | ~2730 |
| **JS** | Updated click handler | ~2888 |
| **JS** | Added balance loading hook | ~2914 |
| **Python** | Updated payment validation | ~2507 |
| **Python** | Updated payment routing | ~2588 |
| **Python** | New `process_wallet_payment()` | ~2603 |
| **Python** | Refactored `process_paystack_payment()` | ~2678 |

---

## Testing the Changes

### Frontend Test
```javascript
// In browser console:
window.cartManager.selectedPaymentMethod  // Should be 'wallet' after selection
window.cartManager.proceedWithCheckout('wallet')  // Should trigger wallet payment
```

### Backend Test
```bash
# Test wallet payment endpoint
curl -X POST http://localhost:5000/api/checkout-and-pay \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 1}],
    "payment_method": "wallet"
  }'
```

---

## Rollback Plan

If issues occur, these are the minimal changes to rollback:

1. **Revert wallet validation** - Change back to `if payment_method != 'paystack'`
2. **Revert payment routing** - Remove wallet handler, use only Paystack logic
3. **Disable wallet UI** - Add back `style="opacity: 0.6; cursor: not-allowed;"` and `coming-soon-badge`
4. **Remove JS functions** - Remove `loadWalletBalanceForModal()` and wallet logic

No database migration needed to rollback.
