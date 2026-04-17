# Checkout Button Implementation Examples

## HTML Examples

### Simple Checkout Button
```html
<button class="btn btn-primary" onclick="handleCheckout()">
    <i class="fas fa-shopping-bag"></i> Checkout
</button>

<script>
async function handleCheckout() {
    const result = await cart.checkout();
    // User will be redirected on success
}
</script>
```

### With Loading State
```html
<button id="checkoutBtn" class="btn btn-primary" onclick="handleCheckoutWithLoader()">
    <i class="fas fa-shopping-bag"></i> Checkout
</button>

<script>
async function handleCheckoutWithLoader() {
    const btn = document.getElementById('checkoutBtn');
    const originalHTML = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    const result = await cart.checkout();
    
    if (!result.success) {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        // Error notification is shown by cart.showCartNotification()
    }
}
</script>
```

### In Cart Modal
```html
<div class="modal-footer">
    <button type="button" class="btn btn-secondary" data-dismiss="modal">
        Continue Shopping
    </button>
    <button type="button" class="btn btn-primary" onclick="handleCheckout()">
        <i class="fas fa-check"></i> Proceed to Checkout
    </button>
</div>

<script>
async function handleCheckout() {
    if (cart.items.length === 0) {
        alert('Your cart is empty');
        return;
    }
    
    const result = await cart.checkout();
    if (result.success) {
        // Modal will auto-close on redirect
    }
}
</script>
```

### Cart Summary Before Checkout
```html
<div class="cart-summary">
    <h4>Order Summary</h4>
    <div id="cartItems"></div>
    <div class="total">
        <strong>Total: $<span id="cartTotal">0.00</span></strong>
    </div>
    <button class="btn btn-success btn-block" onclick="proceedCheckout()">
        Proceed to Checkout
    </button>
</div>

<script>
function displayCartSummary() {
    const itemsDiv = document.getElementById('cartItems');
    const totalSpan = document.getElementById('cartTotal');
    
    itemsDiv.innerHTML = cart.items.map(item => `
        <div class="cart-item">
            <span>${item.name} x ${item.quantity}</span>
            <span>$${(item.price * item.quantity).toFixed(2)}</span>
        </div>
    `).join('');
    
    totalSpan.textContent = cart.getCartTotal().toFixed(2);
}

async function proceedCheckout() {
    displayCartSummary(); // Update display
    
    if (cart.items.length === 0) {
        cart.showCartNotification('Your cart is empty');
        return;
    }
    
    const result = await cart.checkout();
    // Success or error handled by checkout method
}

// Update on page load and item changes
document.addEventListener('DOMContentLoaded', displayCartSummary);
</script>
```

---

## Advanced Examples

### Checkout with Confirmation Dialog
```html
<button class="btn btn-primary" onclick="confirmCheckout()">
    Checkout
</button>

<script>
async function confirmCheckout() {
    const total = cart.getCartTotal();
    const itemCount = cart.getCartCount();
    
    const confirmed = confirm(
        `You are about to place an order for ${itemCount} items totaling $${total.toFixed(2)}.\n\nProceed?`
    );
    
    if (confirmed) {
        const result = await cart.checkout();
        if (!result.success) {
            console.error('Checkout error:', result.error);
        }
    }
}
</script>
```

### Checkout with Success Page
```javascript
async function checkout() {
    const result = await cart.checkout();
    
    if (result.success) {
        // Show success page before redirect
        showSuccessPage(result.order);
        
        // Redirect after 3 seconds
        setTimeout(() => {
            window.location.href = `/customer/dashboard?order_ref=${result.order.reference_number}`;
        }, 3000);
    }
}

function showSuccessPage(order) {
    const successHTML = `
        <div class="alert alert-success">
            <h4>✓ Order Created Successfully!</h4>
            <p>Order Reference: <strong>${order.reference_number}</strong></p>
            <p>Total Amount: <strong>$${order.total_amount.toFixed(2)}</strong></p>
            <p>Redirecting to dashboard...</p>
        </div>
    `;
    
    document.getElementById('checkoutContainer').innerHTML = successHTML;
}
```

### Checkout with Item Validation
```javascript
async function validateAndCheckout() {
    // Check cart
    if (cart.items.length === 0) {
        cart.showCartNotification('Cart is empty');
        return false;
    }
    
    // Check token
    const token = localStorage.getItem('access_token');
    if (!token) {
        cart.showCartNotification('Please login first');
        window.location.href = '/login';
        return false;
    }
    
    // Verify items
    for (const item of cart.items) {
        if (!item.id || !item.price || item.quantity <= 0) {
            cart.showCartNotification('Invalid item in cart');
            return false;
        }
    }
    
    // Proceed with checkout
    const result = await cart.checkout();
    return result.success;
}
```

---

## Integration with Cart Page

### Complete Cart Page with Checkout
```html
<div class="container mt-5">
    <h2>Shopping Cart</h2>
    
    <div class="row">
        <!-- Cart Items -->
        <div class="col-md-8">
            <div id="cartItemsList">
                <p>Your cart is empty</p>
            </div>
        </div>
        
        <!-- Cart Summary -->
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Order Summary</h5>
                    
                    <div class="mb-3">
                        <small class="text-muted">Subtotal:</small>
                        <span class="float-right">$<span id="subtotal">0.00</span></span>
                    </div>
                    
                    <div class="mb-3">
                        <small class="text-muted">Tax:</small>
                        <span class="float-right">$<span id="tax">0.00</span></span>
                    </div>
                    
                    <hr>
                    
                    <div class="mb-3">
                        <strong>Total:</strong>
                        <span class="float-right">
                            $<strong id="total">0.00</strong>
                        </span>
                    </div>
                    
                    <button class="btn btn-success btn-block" 
                            onclick="proceedToCheckout()"
                            id="checkoutButton">
                        <i class="fas fa-lock"></i> Proceed to Checkout
                    </button>
                    
                    <a href="/browse-products" class="btn btn-outline-primary btn-block mt-2">
                        Continue Shopping
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function updateCartDisplay() {
    const itemsList = document.getElementById('cartItemsList');
    const subtotal = cart.getCartTotal();
    const tax = subtotal * 0.1; // 10% tax
    const total = subtotal + tax;
    
    if (cart.items.length === 0) {
        itemsList.innerHTML = '<p class="alert alert-info">Your cart is empty</p>';
        document.getElementById('checkoutButton').disabled = true;
    } else {
        itemsList.innerHTML = cart.items.map((item, index) => `
            <div class="cart-item-row d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                <div>
                    <strong>${item.name}</strong>
                    <br>
                    <small>Qty: ${item.quantity} × $${item.price.toFixed(2)}</small>
                </div>
                <div>
                    <span class="mr-3">$${(item.price * item.quantity).toFixed(2)}</span>
                    <button class="btn btn-sm btn-danger" 
                            onclick="removeFromCart(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        document.getElementById('checkoutButton').disabled = false;
    }
    
    document.getElementById('subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('tax').textContent = tax.toFixed(2);
    document.getElementById('total').textContent = total.toFixed(2);
}

function removeFromCart(productId) {
    if (confirm('Remove this item from cart?')) {
        cart.removeItem(productId);
        updateCartDisplay();
    }
}

async function proceedToCheckout() {
    if (cart.items.length === 0) {
        cart.showCartNotification('Your cart is empty');
        return;
    }
    
    const result = await cart.checkout();
    if (!result.success) {
        console.error('Checkout failed:', result.error);
    }
}

document.addEventListener('DOMContentLoaded', updateCartDisplay);
</script>
```

---

## CSS Classes You Can Use

For custom styling add these classes:

```css
.checkout-button {
    background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
    border: none;
    color: white;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.checkout-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
}

.checkout-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.cart-item-row {
    padding: 15px;
    background: #f9f9f9;
    border-radius: 4px;
    margin-bottom: 10px;
}
```

---

## Key Points

1. **Always check for empty cart** before checkout
2. **Show loading state** during processing
3. **Handle errors gracefully** with user notifications
4. **Clear cart automatically** after success
5. **Redirect to dashboard** with order reference
6. **Use await** with async checkout method
7. **Check JWT token** if doing custom implementations

---

## Common Patterns

### Pattern 1: Simple Button Click
```javascript
onclick="cart.checkout()"
```

### Pattern 2: With Validation
```javascript
onclick="if (cart.items.length > 0) cart.checkout()"
```

### Pattern 3: With Async Handler
```javascript
onclick="handleCheckout()"
// with async function definition
```

### Pattern 4: With Event Listener
```javascript
document.getElementById('checkoutBtn').addEventListener('click', async () => {
    await cart.checkout();
});
```

All methods should work seamlessly with the implemented backend API!
