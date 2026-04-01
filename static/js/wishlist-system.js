// Wishlist Management System
class WishlistManager {
    constructor() {
        this.wishlistKey = 'ikeja_wishlist';
        this.wishlist = [];
        this.isLoading = false;
        this.init();
    }

    async init() {
        const token = localStorage.getItem('access_token');
        if (token) {
            await this.loadWishlistFromServer();
        }
    }

    // Load wishlist from server
    async loadWishlistFromServer() {
        this.isLoading = true;
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                this.wishlist = [];
                return;
            }

            const response = await fetch('/api/wishlist', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.wishlist = data.items || [];
                this.updateUI();
            } else if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('access_token');
                this.wishlist = [];
            }
        } catch (error) {
            console.error('Error loading wishlist from server:', error);
            this.wishlist = [];
        } finally {
            this.isLoading = false;
        }
    }

    // Add item to wishlist (server-side)
    async addItem(product) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return false;
        }

        if (this.isInWishlist(product.id)) {
            this.showNotification('Item already in wishlist');
            return false;
        }

        try {
            const response = await fetch('/api/wishlist/add', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: product.id })
            });

            const data = await response.json();

            if (response.ok) {
                // Add to local cache
                this.wishlist.push({
                    id: product.id,
                    name: product.name,
                    price: product.price,
                    image: product.image || '/static/uploads/products/placeholder.png',
                    store_name: product.store_name || 'Unknown',
                    added_date: new Date().toISOString()
                });
                this.updateUI();
                this.showNotification(`${product.name} added to wishlist!`);
                return true;
            } else if (response.status === 409) {
                this.showNotification('Item already in wishlist');
                return false;
            } else {
                this.showNotification(data.message || 'Failed to add to wishlist');
                return false;
            }
        } catch (error) {
            console.error('Error adding to wishlist:', error);
            this.showNotification('Error adding to wishlist');
            return false;
        }
    }

    // Remove item from wishlist (server-side)
    async removeItem(productId) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            this.showNotification('Please login to manage wishlist');
            return false;
        }

        try {
            const response = await fetch(`/api/wishlist/remove/${productId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                // Remove from local cache
                this.wishlist = this.wishlist.filter(item => item.id !== productId);
                this.updateUI();
                this.showNotification('Removed from wishlist');
                return true;
            } else {
                this.showNotification(data.message || 'Failed to remove from wishlist');
                return false;
            }
        } catch (error) {
            console.error('Error removing from wishlist:', error);
            this.showNotification('Error removing from wishlist');
            return false;
        }
    }

    // Check if item is in wishlist
    isInWishlist(productId) {
        return this.wishlist.some(item => item.id === productId);
    }

    // Get wishlist count
    getWishlistCount() {
        return this.wishlist.length;
    }

    // Get all wishlist items
    getWishlistItems() {
        return this.wishlist;
    }

    // Clear wishlist (server-side)
    async clearWishlist() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            this.showNotification('Please login to manage wishlist');
            return false;
        }

        try {
            const response = await fetch('/api/wishlist/clear', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.wishlist = [];
                this.updateUI();
                this.showNotification('Wishlist cleared');
                return true;
            } else {
                this.showNotification(data.message || 'Failed to clear wishlist');
                return false;
            }
        } catch (error) {
            console.error('Error clearing wishlist:', error);
            this.showNotification('Error clearing wishlist');
            return false;
        }
    }

    // Update UI elements
    updateUI() {
        const wishlistBadges = document.querySelectorAll('[data-wishlist-badge]');
        const count = this.getWishlistCount();
        
        wishlistBadges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });

        // Update all wishlist buttons
        document.querySelectorAll('[data-wishlist-btn]').forEach(btn => {
            const productId = parseInt(btn.getAttribute('data-wishlist-btn'));
            if (this.isInWishlist(productId)) {
                btn.classList.add('in-wishlist');
                btn.innerHTML = '<i class="fas fa-heart"></i>';
            } else {
                btn.classList.remove('in-wishlist');
                btn.innerHTML = '<i class="far fa-heart"></i>';
            }
        });
    }

    // Show notification
    showNotification(message) {
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
            font-size: 0.95rem;
            max-width: 300px;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Toggle wishlist item
    async toggleWishlist(product) {
        if (this.isInWishlist(product.id)) {
            await this.removeItem(product.id);
        } else {
            await this.addItem(product);
        }
    }
}

// Initialize wishlist manager globally
window.wishlistManager = new WishlistManager();

// Update UI on page load
document.addEventListener('DOMContentLoaded', () => {
    if (window.wishlistManager) {
        window.wishlistManager.updateUI();
    }
});

