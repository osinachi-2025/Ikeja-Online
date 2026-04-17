# Checkout & Order System Implementation

## Overview
A complete checkout and order management system has been implemented that allows customers to convert their shopping cart into orders with database persistence.

## What Was Implemented

### 1. Database Model Update (models.py)

#### Orders Table Enhancement
Added a new field to track unique order references:
- `reference_number` (String, Unique) - Unique identifier for each order (format: ORD-YYYYMMDD-XXXXXX)

Example reference numbers: `ORD-20260327-A1B2C3`, `ORD-20260327-X9Z2M5`

### 2. Backend API Endpoints (app.py)

#### POST /api/checkout
**Creates a new order from cart items**

Request:
```json
{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 3,
      "quantity": 1
    }
  ]
}
```

Response (Success - 201):
```json
{
  "success": true,
  "message": "Order created successfully",
  "order": {
    "id": 42,
    "reference_number": "ORD-20260327-A1B2C3",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "total_amount": 5500.50,
    "status": "pending",
    "created_at": "2026-03-27T10:30:00",
    "items_count": 2
  }
}
```

**Features:**
- ✅ JWT authentication required
- ✅ Validates all cart items exist
- ✅ Checks product stock availability
- ✅ Calculates total amount automatically
- ✅ Generates unique reference number
- ✅ Creates Order and Order_Items records
- ✅ Deducts stock from product inventory
- ✅ Returns complete order details including customer info

**Error Responses:**
- `400 Bad Request` - Empty cart or invalid items
- `403 Forbidden` - User is not a customer
- `404 Not Found` - Product doesn't exist or customer profile not found
- `500 Server Error` - Database or server errors

---

#### GET /api/orders
**Retrieves all orders for the logged-in customer**

Response (Success - 200):
```json
{
  "success": true,
  "orders": [
    {
      "id": 42,
      "reference_number": "ORD-20260327-A1B2C3",
      "total_amount": 5500.50,
      "status": "pending",
      "created_at": "2026-03-27T10:30:00",
      "items": [
        {
          "product_id": 1,
          "product_name": "Gaming Laptop",
          "quantity": 2,
          "price_at_purchase": 2500.00,
          "total": 5000.00
        },
        {
          "product_id": 3,
          "product_name": "Mouse Pad",
          "quantity": 1,
          "price_at_purchase": 500.50,
          "total": 500.50
        }
      ]
    }
  ],
  "count": 1
}
```

**Features:**
- ✅ JWT authentication required
- ✅ Only shows customer's own orders
- ✅ Orders sorted by creation date (newest first)
- ✅ Includes detailed item information
- ✅ Shows historical prices (price_at_purchase)

---

#### GET /api/orders/<order_id>
**Retrieves detailed information about a specific order**

Response (Success - 200):
```json
{
  "success": true,
  "order": {
    "id": 42,
    "reference_number": "ORD-20260327-A1B2C3",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "total_amount": 5500.50,
    "status": "pending",
    "created_at": "2026-03-27T10:30:00",
    "items": [
      {
        "product_id": 1,
        "product_name": "Gaming Laptop",
        "quantity": 2,
        "price_at_purchase": 2500.00,
        "total": 5000.00
      }
    ]
  }
}
```

**Features:**
- ✅ JWT authentication required
- ✅ Ownership verification (customer can only view own orders)
- ✅ Complete order details including customer info
- ✅ Full item details with historical pricing

---

### 3. Frontend Implementation (cache-system.js)

#### New Method: checkout()
**Creates an order from the current cart**

```javascript
// Usage
const result = await cart.checkout();

if (result.success) {
    console.log('Order created:', result.order.reference_number);
    // Redirect to order confirmation
} else {
    console.error('Checkout failed:', result.error);
}
```

**Implementation Details:**
- ✅ Checks for JWT token before checkout
- ✅ Validates cart is not empty
- ✅ Converts cart items to checkout format
- ✅ Sends POST request to /api/checkout
- ✅ Clears cart after successful order
- ✅ Shows notifications to user
- ✅ Redirects to customer dashboard with order reference
- ✅ Handles errors gracefully

**Process Flow:**
1. User clicks checkout button
2. cart.checkout() is called
3. Validates login and cart contents
4. Sends items to backend
5. Backend creates order and deducts stock
6. Cart is cleared on success
7. User sees success notification
8. User redirected to dashboard with order reference in URL

---

## Order Data Structure

### Order Record
```python
{
    'id': 42,
    'customer_id': 5,
    'reference_number': 'ORD-20260327-A1B2C3',
    'total_amount': 5500.50,
    'status': 'pending',
    'created_at': '2026-03-27T10:30:00'
}
```

### Order_Items Records (Multiple per Order)
```python
{
    'id': 1,
    'order_id': 42,
    'product_id': 1,
    'quantity': 2,
    'price_at_purchase': 2500.00,
    'created_at': '2026-03-27T10:30:00'
}
```

---

## Usage Examples

### JavaScript - Checkout Button
```html
<button onclick="handleCheckout()" class="btn btn-primary">
    Checkout
</button>

<script>
async function handleCheckout() {
    const result = await cart.checkout();
    // Result contains order details
}
</script>
```

### JavaScript - View Orders
```javascript
// Fetch customer's orders
const token = localStorage.getItem('access_token');
const response = await fetch('/api/orders', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});

const data = await response.json();
console.log(data.orders); // Array of orders
```

### JavaScript - Get Specific Order
```javascript
const orderId = 42;
const response = await fetch(`/api/orders/${orderId}`, {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});

const data = await response.json();
console.log(data.order.reference_number); // ORD-20260327-A1B2C3
```

### cURL - Checkout Example
```bash
curl -X POST http://localhost:5000/api/checkout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      },
      {
        "product_id": 3,
        "quantity": 1
      }
    ]
  }'
```

---

## Security Features

1. **Authentication**: All endpoints require valid JWT token
2. **Role-Based Access**: Only customers can checkout and view orders
3. **Order Ownership**: Customers can only view their own orders
4. **Input Validation**: Product IDs and quantities validated
5. **Stock Management**: Inventory checked and updated atomically
6. **Unique References**: Each order gets unique reference number
7. **CORS Protection**: Enabled with credential support

---

## Order Status Values

- `pending` - Order created, awaiting payment
- `processing` - Payment confirmed, being prepared
- `completed` - Order fulfilled and delivered
- `cancelled` - Order cancelled by customer or system

**Default**: All new orders start as `pending`

---

## Reference Number Format

Format: `ORD-YYYYMMDD-XXXXXX`

- `ORD` - Static prefix
- `YYYYMMDD` - Date of order creation
- `XXXXXX` - 6 random alphanumeric characters

Example: `ORD-20260327-K7M2P9`

---

## Database Impact

### New/Modified Tables
- `orders` - Added `reference_number` column
- `order_items` - Already existed, used to store order line items

### Data Relationships
```
Customer (1) ──→ (Many) Orders
Order (1) ──→ (Many) Order_Items
Order_Items (Many) ──→ (1) Products
```

---

## Testing Checklist

- [ ] Create order with single item
- [ ] Create order with multiple items
- [ ] Verify stock is deducted from products
- [ ] Verify cart is cleared after checkout
- [ ] Get all orders for customer
- [ ] Get specific order details
- [ ] Try unauthorized checkout (should fail)
- [ ] Try checkout with empty cart (should fail)
- [ ] Try checkout with non-existent product (should fail)
- [ ] Try accessing other customer's order (should fail)
- [ ] Verify reference number is unique
- [ ] Test with insufficient stock (should fail)

---

## Files Modified

1. **models.py**
   - Added `reference_number` field to Orders model

2. **app.py**
   - Added `generate_order_reference()` function
   - Added `POST /api/checkout` endpoint
   - Added `GET /api/orders` endpoint
   - Added `GET /api/orders/<order_id>` endpoint

3. **static/js/cart-system.js**
   - Added `async checkout()` method
   - Updated checkout to call backend API
   - Added error handling and notifications
   - Auto-redirects to dashboard on success

---

## Next Steps (Optional Enhancements)

1. Add payment integration (Stripe, PayPal)
2. Add order status update endpoints
3. Add order cancellation functionality
4. Add email notifications for order confirmation
5. Add order tracking/shipping information
6. Add invoice generation
7. Add return/refund functionality
8. Add order filtering and search
9. Add batch order operations
10. Add order analytics and reporting

---

## Notes

- All timestamps are in UTC
- Prices are stored as Float (can be enhanced to Decimal for financial accuracy)
- Stock deduction is atomic - either succeeds fully or fails completely
- Order IDs are auto-incremented by database
- Reference numbers are manually generated with uniqueness checks
- All amounts should be positive values
