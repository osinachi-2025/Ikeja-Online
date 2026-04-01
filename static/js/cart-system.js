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

    // Get cart total
    getCartTotal() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    }

    // Clear cart
    clearCart() {
        this.items = [];
        this.saveCart();
    }

    // Checkout - create order
    async checkout() {
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

        try {
            // Prepare cart items for order
            const checkoutItems = this.items.map(item => ({
                product_id: item.id,
                id: item.id,
                quantity: item.quantity
            }));

            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: checkoutItems
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Clear cart after successful order
                this.clearCart();
                this.showCartNotification('Order created successfully!');
                
                // Redirect to order confirmation or dashboard
                setTimeout(() => {
                    window.location.href = `/customer/dashboard?order_ref=${data.order.reference_number}`;
                }, 1500);
                
                return {
                    success: true,
                    order: data.order
                };
            } else {
                this.showCartNotification(data.message || 'Checkout failed');
                return {
                    success: false,
                    error: data.message || 'Unknown error'
                };
            }
        } catch (error) {
            console.error('Checkout error:', error);
            this.showCartNotification('Error during checkout');
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Update UI
    updateCartUI() {
        const cartCount = document.getElementById('cartCount');
        if (cartCount) {
            const count = this.getCartCount();
            cartCount.textContent = count;
            cartCount.style.display = count > 0 ? 'flex' : 'none';
        }
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
