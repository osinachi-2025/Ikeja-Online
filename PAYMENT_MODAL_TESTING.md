# Payment Method Modal - Quick Start Guide

## Testing the Feature

### Step 1: Navigate to Home Page
1. Open the application in a browser
2. Go to the home page (`/`)

### Step 2: Add Products to Cart
1. Browse products on the home page
2. Click "Add to Cart" on any product
3. A notification should appear: "Product added to cart!"
4. Cart icon in header should show item count

### Step 3: Open Shopping Cart
1. Click the shopping cart icon in the header
2. Cart modal opens showing your items
3. You can see:
   - Product list with quantities
   - Total amount at bottom
   - "Proceed to Checkout" button

### Step 4: Trigger Payment Modal
1. Click "Proceed to Checkout" button
2. Payment Method Selection modal should appear with:
   - **Card Payment** (enabled)
   - **Bank Transfer** (Coming Soon - disabled)
   - **Wallet** (Coming Soon - disabled)

### Step 5: Select Payment Method
1. Click on the "Card Payment" card
2. You should see:
   - Orange border appears
   - Checkmark badge appears in top-right corner
   - Card background highlights
3. Notice "Proceed with Payment" button becomes enabled

### Step 6: Complete Checkout
1. Click "Proceed with Payment" button
2. Modal closes and cart shows loading state
3. Checkout button shows: `<i class="fas fa-spinner fa-spin"></i> Processing...`
4. API call is made with:
   ```json
   {
     "items": [...],
     "payment_method": "paystack"
   }
   ```

### Step 7: Payment Processing
If logged in:
- Paystack payment page should load
- Complete payment flow as normal

If not logged in:
- Redirected to login page

## Interaction Patterns

### Closing the Modal (3 ways)

**Method 1: Using Cancel/Back Button**
```
Click "Back to Cart" → Modal closes → You return to cart modal
```

**Method 2: Using Close Button**
```
Click X button in header → Modal closes → You return to cart modal
```

**Method 3: Click Outside Modal**
```
Click on dark overlay → Modal closes → You return to cart modal
```

## Testing Scenario: Coming Soon Payment Methods

Currently, if you try to select a "Coming Soon" method:

1. Cards are slightly greyed out (opacity: 0.6)
2. Cards have cursor: not-allowed
3. Cards cannot be selected (click handler prevents it)
4. If you manually try to proceed with these methods:
   - Backend returns: "bank-transfer payment method is coming soon"

## Expected User Flow

### Happy Path (New Customer)
```
Browse Products
   ↓
Add Products to Cart
   ↓
Click Cart Icon
   ↓
Review Cart Items
   ↓
Click "Proceed to Checkout"
   ↓
Select "Card Payment"
   ↓
Click "Proceed with Payment"
   ↓
Redirected to Paystack
   ↓
Enter Card Details
   ↓
Complete Payment
```

### Alternative Path (Change Mind)
```
Click "Proceed to Checkout"
   ↓
See Payment Method Modal
   ↓
Click "Back to Cart"
   ↓
Return to Cart Modal
   ↓
Can continue shopping or modify cart
```

## Visual Feedback Elements

### Payment Method Card States

**Unselected (Default)**
```
┌─────────────────┐
│  💳             │
│ Card Payment    │
│ Pay via Debit   │
│ or Credit Card  │
└─────────────────┘
```

**Hovered Over (Enabled)**
```
┌──────────────────┐  ← Orange border
│  💳 (glowing)    │  ← Slight shadow
│ Card Payment     │  ← Slightly raised
│ Pay via Debit    │
│ or Credit Card   │
└──────────────────┘
```

**Selected (Active)**
```
┌──────────────────┐
│  💳      ✓       │ ← Checkmark badge
│ Card Payment     │  ← Orange background
│ Pay via Debit    │  ← Strong shadow
│ or Credit Card   │
└──────────────────┘
```

**Disabled (Coming Soon)**
```
┌──────────────────┐
│  🏦      🏷      │ ← "Coming Soon" badge
│ Bank Transfer    │  ← Greyed out (0.6 opacity)
│ Pay via bank     │  ← Cursor not-allowed
│ transfer         │
└──────────────────┘
```

## Button States

### "Proceed with Payment" Button

**Disabled** (before selecting payment method)
```
[Proceed with Payment] ← Opacity 0.5, cursor: not-allowed
```

**Enabled** (after selecting payment method)
```
[✓ Proceed with Payment] ← Full opacity, can click
```

**Processing** (during checkout)
```
[⊙ Processing...] ← Spinner animation, disabled
```

## Mobile Behavior

### Responsive Changes

**Desktop View (>768px)**
- Modal: 600px wide
- Cards: 3 columns
- Full animations enabled

**Tablet View (768px)**
- Modal: 90% width
- Cards: auto-fit columns
- Same animations

**Mobile View (<480px)**
- Modal: 90% width, full height
- Cards: 1-2 columns
- Touch-optimized spacing
- Larger touch targets

## Keyboard Navigation (Future Enhancement)

Currently not implemented, but planned:
- Tab through payment methods
- Enter/Space to select
- Escape to close modal

## Error Handling

### Scenario: Cart becomes empty
- If items are removed before checkout completes
- Modal closes automatically
- User returns to cart modal
- "Cart is empty" message displays

### Scenario: Login expires
- If user logs out before completing payment
- Checkout function detects missing token
- Page redirects to login

### Scenario: Stock becomes unavailable
- If product stock changes before payment
- Backend returns stock error
- User notified via alert
- Cart modal remains open

## API Integration Details

### Request Format
```javascript
const body = {
  items: [
    { product_id: 1, quantity: 2 },
    { product_id: 3, quantity: 1 }
  ],
  payment_method: "paystack"  // NEW
};
```

### Processing Timeline
1. User selects payment method
2. Modal stores selection in `window.cartManager.selectedPaymentMethod`
3. Click "Proceed with Payment"
4. `proceedWithCheckout()` function called with method
5. API request sent to `/api/checkout-and-pay`
6. Backend validates and processes
7. Response determines next action

## Troubleshooting

### Modal doesn't appear
- Check browser console for JavaScript errors
- Verify DOM elements exist (F12 → Elements)
- Check local storage token is valid

### Payment method not selectable
- Check that Paystack card is not having opacity: 0.6
- Verify event listeners are attached
- Check console for click handler errors

### Checkout not proceeding
- Verify payment method is selected
- Check network tab for API errors
- Verify JWT token in local storage
- Check server logs for errors

### Modal overlays not working
- Check z-index values (should be 1000-1001)
- Verify backdrop-filter is supported
- Check for CSS conflicts

## Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Payment Modal UI | ✅ Complete | Fully styled and responsive |
| Card Payment (Paystack) | ✅ Complete | Functional and tested |
| Bank Transfer | 🔄 Coming Soon | Placeholder in place |
| Wallet | 🔄 Coming Soon | Placeholder in place |
| Mobile Responsive | ✅ Complete | Works on all screen sizes |
| Keyboard Navigation | ⏳ Planned | Can be added later |
| Payment History | ✅ Existing | Available in orders page |
| Payment Verification | ✅ Existing | Handled via callbacks |
