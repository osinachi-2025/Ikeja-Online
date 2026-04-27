// Cart Management System
class ShoppingCart {
    constructor() {
        this.items = this.loadCart();
    }

    // Load cart from localStorage
    loadCart() {
        const stored = localStorage.getItem('shopping_cart');
        return stored ? JSON.parse(stored) : [];
    }

    // Save cart to localStorage
    saveCart() {
        localStorage.setItem('shopping_cart', JSON.stringify(this.items));
        this.updateCartUI();
        this.renderCartPanel();
    }

    // Add item to cart
    addItem(product) {
        const existingItem = this.items.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity += product.quantity || 1;
        } else {
            this.items.push({
                id: product.id,
                name: product.name,
                price: product.price,
                image: product.image || null,
                quantity: product.quantity || 1,
                store_name: product.store_name || 'Unknown Store'
            });
        }
        
        this.saveCart();
        this.showCartNotification(`${product.name} added to cart!`);
    }

    // Remove item from cart
    removeItem(productId) {
        this.items = this.items.filter(item => item.id !== productId);
        this.saveCart();
    }

    // Update item quantity
    updateQuantity(productId, quantity) {
        const item = this.items.find(item => item.id === productId);
        if (item) {
            if (quantity <= 0) {
                this.removeItem(productId);
            } else {
                item.quantity = quantity;
                this.saveCart();
            }
        }
    }

    // Get cart count
    getCartCount() {
        return this.items.reduce((total, item) => total + item.quantity, 0);
    }

    // Format price for display
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN' }).format(amount);
    }

    // Render the cart drawer panel
    renderCartPanel() {
        const panel = document.getElementById('cart-panel');
        if(!panel) return;
        const listEl = panel.querySelector('#cart-items');
        const totalEl = panel.querySelector('#cart-total');
        const countEl = panel.querySelector('#cart-item-count');
        const actions = panel.querySelector('.cart-actions');
        if(!listEl || !totalEl || !countEl || !actions) return;

        if(this.items.length === 0) {
            listEl.innerHTML = '<div class="cart-empty">Your cart is empty. Add products to get started.</div>';
            actions.style.display = 'none';
        } else {
            listEl.innerHTML = this.items.map(item => `
                <div class="cart-item">
                    <div class="cart-item-image">
                        ${item.image ? `<img src="${item.image}" alt="${item.name}">` : `<div class="cart-item-image-fallback">🛍️</div>`}
                    </div>
                    <div class="cart-item-details">
                        <div class="cart-item-head">
                            <div class="cart-item-name">${item.name}</div>
                            <div class="cart-item-price">${this.formatCurrency(item.price)}</div>
                        </div>
                        <div class="cart-item-store">${item.store_name}</div>
                        <div class="quantity-controls">
                            <button type="button" onclick="cart.updateQuantity(${item.id}, ${item.quantity - 1})">−</button>
                            <span>${item.quantity}</span>
                            <button type="button" onclick="cart.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                            <button type="button" class="cart-remove" onclick="cart.removeItem(${item.id})">Remove</button>
                        </div>
                    </div>
                </div>
            `).join('');
            actions.style.display = 'grid';
        }

        countEl.textContent = `${this.items.length} item${this.items.length === 1 ? '' : 's'}`;
        totalEl.textContent = this.formatCurrency(this.getCartTotal());
    }

    openCartDrawer() {
        this.renderCartPanel();
        const overlay = document.getElementById('cart-overlay');
        if(overlay) {
            overlay.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
    }

    closeCartDrawer() {
        const overlay = document.getElementById('cart-overlay');
        if(overlay) {
            overlay.classList.remove('open');
            document.body.style.overflow = '';
        }
    }

    async checkout(paymentMethod = 'paystack') {
        const token = localStorage.getItem('access_token');
        if (!token) {
            this.showCartNotification('Please login to checkout');
            window.location.href = '/login';
            return false;
        }

        if (this.items.length === 0) {
            this.showCartNotification('Your cart is empty');
            return false;
        }

        const checkoutItems = this.items.map(item => ({
            product_id: item.id,
            id: item.id,
            quantity: item.quantity
        }));

        try {
            const response = await fetch('/api/checkout-and-pay', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: checkoutItems,
                    payment_method: paymentMethod
                })
            });

            const data = await response.json();
            if (response.ok && data.success) {
                if (paymentMethod === 'paystack' && data.authorization_url) {
                    this.showCartNotification('Redirecting to Paystack...');
                    setTimeout(() => {
                        window.location.href = data.authorization_url;
                    }, 600);
                    return {
                        success: true,
                        order: data.order
                    };
                }

                this.clearCart();
                this.showCartNotification(data.message || 'Payment completed!');
                setTimeout(() => {
                    window.location.href = `/customer/dashboard?order_ref=${encodeURIComponent(data.order.reference_number)}`;
                }, 1000);
                return {
                    success: true,
                    order: data.order
                };
            }

            const message = data.message || data.error || 'Checkout failed';
            this.showCartNotification(message);
            return {
                success: false,
                error: message
            };
        } catch (error) {
            console.error('Checkout error:', error);
            this.showCartNotification('Error during checkout');
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Get cart total
    getCartTotal() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    }

    // Clear cart
    clearCart() {
        this.items = [];
        this.saveCart();
    }

    // Update UI
    updateCartUI() {
        const count = this.getCartCount();
        
        // Update all cart badges
        const cartBadges = document.querySelectorAll('#navCartBadge, #floatingCartBadge, #mobileCartBadge, #cartCount, #cart-badge');
        cartBadges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });
    }

    // Show notification
    showCartNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            animation: slideIn 0.3s ease;
            font-weight: 600;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
}

// Initialize cart
let cart = new ShoppingCart();

// Expose cart drawer helpers globally
function openCartDrawer() { cart.openCartDrawer(); }
function closeCartDrawer() { cart.closeCartDrawer(); }

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Update cart UI on page load
document.addEventListener('DOMContentLoaded', () => {
    cart.updateCartUI();
});
