# Wallet Payment - Quick Testing Guide

## Setup for Testing

### Prerequisites
1. User must be logged in as a customer
2. Customer must have a wallet (created automatically if not exists)
3. Wallet must have some balance for successful payment test

### How to Add Wallet Balance (for testing)

If you need to manually add wallet balance for testing:

1. **Via Database (Quick)**
```sql
-- Get customer's wallet
SELECT w.* FROM wallet w 
JOIN customers c ON w.customer_id = c.id 
JOIN users u ON c.user_id = u.id 
WHERE u.email = 'customer@example.com';

-- Add balance to wallet
UPDATE wallet SET balance = 10000.00 WHERE id = 1;
```

2. **Via Deposit Endpoint** (if implemented)
```
POST /api/deposit/initialize
{
  "amount": 10000
}
```

## Test Scenario 1: Successful Wallet Payment

### Steps
1. **Log in as customer**
   - Navigate to home page
   - Click login
   - Enter customer credentials

2. **Add products to cart**
   - Browse products
   - Click "Add to Cart" on products
   - Note the total amount (e.g., ₦5,000)

3. **Open cart and initiate checkout**
   - Click cart icon in header
   - Verify items in cart
   - Click "Proceed to Checkout"

4. **Select wallet payment**
   - Payment modal should appear
   - Should see wallet balance displayed (e.g., "Balance: ₦10,000.00")
   - Click the "Wallet" card
   - Card should show orange border and checkmark
   - "Proceed with Payment" button should be enabled

5. **Complete payment**
   - Click "Proceed with Payment"
   - Button shows loading: "⊙ Processing..."
   - Modal closes
   - See notification: "Payment completed with wallet!"
   - Redirected to `/customer/my-orders`

6. **Verify order**
   - Order appears in list
   - Status shows: "paid"
   - Order reference number visible

7. **Verify wallet balance updated**
   - New balance should reflect deduction
   - Previous: ₦10,000.00
   - Purchased: ₦5,000.00
   - New balance: ₦5,000.00

---

## Test Scenario 2: Insufficient Wallet Balance

### Prerequisites
- Customer has wallet balance less than cart total
- Example: Balance ₦2,000, Cart total ₦5,000

### Steps
1. **Add products to cart** (total > wallet balance)
   - Add items totaling more than wallet balance
   - Note the total amount

2. **Open cart and proceed to checkout**
   - Click "Proceed to Checkout"
   - Payment modal appears

3. **Attempt wallet payment**
   - System shows wallet balance: "Balance: ₦2,000.00"
   - Orange warning box appears:
     "Your wallet balance is insufficient for this purchase..."
   - "Proceed with Payment" button is DISABLED

4. **Expected behavior**
   - Cannot click "Proceed with Payment"
   - User must select different payment method
   - Or click "Back to Cart" to return

5. **Select alternative payment**
   - Click "Card Payment" (Paystack)
   - "Proceed with Payment" button becomes enabled
   - Complete card payment instead

---

## Test Scenario 3: User Not Logged In

### Steps
1. **Log out of account**
   - Click user profile dropdown
   - Click "Logout"

2. **Attempt wallet payment**
   - Add item to cart
   - Try to click "Wallet" card
   - Alert appears: "Please log in to use wallet payment"

3. **Expected behavior**
   - Cannot select wallet payment without login
   - Other payment methods (Paystack) may also require login
   - User redirected to login page on checkout

---

## Test Scenario 4: Zero Wallet Balance

### Prerequisites
- Create new customer without wallet
- Wallet auto-created with 0.00 balance

### Steps
1. **Log in as new customer**
   - No wallet funds

2. **Attempt wallet payment**
   - Add product to cart
   - Click "Proceed to Checkout"
   - Try to select "Wallet" card
   - Balance shows: "Balance: ₦0.00"
   - Warning appears immediately
   - "Proceed with Payment" button disabled

3. **Expected behavior**
   - Cannot proceed with insufficient balance
   - Must add funds or use card payment
   - System prevents over-spending

---

## Test Scenario 5: Wallet Balance Exactly Equals Cart Total

### Prerequisites
- Wallet balance: ₦5,000.00
- Cart total: ₦5,000.00

### Steps
1. **Add products totaling exactly ₦5,000**
   
2. **Select wallet payment**
   - Click "Wallet" card
   - Balance shows: "Balance: ₦5,000.00"
   - NO warning appears
   - Button enabled

3. **Complete payment**
   - Click "Proceed with Payment"
   - Payment succeeds
   - Wallet balance: ₦0.00

---

## Test Scenario 6: High-Value Wallet Balance

### Prerequisites
- Wallet balance: ₦100,000.00
- Cart total: ₦5,000.00

### Steps
1. **Add products to cart**
   - Total: ₦5,000

2. **Select wallet payment**
   - Balance shows: "Balance: ₦100,000.00"
   - No warning
   - Button enabled

3. **Complete payment**
   - Succeeds instantly
   - Remaining balance: ₦95,000.00

---

## Expected Modal States

### Wallet Card - Unselected
```
┌─────────────────────┐
│     💳 Wallet       │
│ Pay from your       │
│ wallet              │
│ Balance: ₦10,000.00 │
└─────────────────────┘
```

### Wallet Card - Selected (Sufficient Balance)
```
┌─────────────────────┐
│  💳 Wallet    ✓     │  ← Orange checkmark
│ Pay from your       │  ← Orange border
│ wallet              │
│ Balance: ₦10,000.00 │
└─────────────────────┘
```

### Wallet Card - Selected (Insufficient Balance)
```
┌─────────────────────┐
│  💳 Wallet    ✓     │
│ Pay from your       │
│ wallet              │
│ Balance: ₦2,000.00  │
└─────────────────────┘

⚠️  Your wallet balance is insufficient...
    [Please select another payment method]
```

### Proceed Button States

**Disabled (No selection)**
```
[Proceed with Payment] - Opacity 50%, cursor: not-allowed
```

**Disabled (Insufficient balance)**
```
[Insufficient Wallet Balance] - Opacity 50%, cursor: not-allowed
```

**Enabled (Ready to pay)**
```
[✓ Proceed with Payment] - Full opacity, can click
```

**Processing**
```
[⊙ Processing...] - Loading spinner, disabled
```

---

## Browser Console Verification

### What to check in DevTools (F12 → Console)

1. **Wallet balance loading**
   - Should see no errors when modal opens
   - Wallet balance fetched successfully

2. **Payment method selection**
   - Click wallet card
   - No errors in console

3. **Checkout submission**
   - Submit wallet payment
   - Network tab shows POST to `/api/checkout-and-pay`
   - Payload includes: `"payment_method": "wallet"`
   - Response shows success

### Network Tab Inspection

**Wallet Balance Request**
```
GET /api/wallet
Headers: Authorization: Bearer {token}
Response: {"success": true, "balance": 10000.00}
```

**Wallet Payment Request**
```
POST /api/checkout-and-pay
Headers: Authorization: Bearer {token}
Body: {"items": [...], "payment_method": "wallet"}
Response: {
  "success": true,
  "payment_method": "wallet",
  "order": {...},
  "wallet": {
    "previous_balance": 10000.00,
    "new_balance": 5000.00,
    "amount_deducted": 5000.00
  }
}
```

---

## Troubleshooting Common Issues

### Issue: Wallet card doesn't respond to clicks
**Solution**: 
- Check browser console for JavaScript errors
- Verify customer is logged in
- Check that wallet balance is loaded

### Issue: "Insufficient wallet balance" doesn't appear
**Solution**:
- Ensure wallet balance is less than cart total
- Reload modal to refresh balance
- Check network request to `/api/wallet`

### Issue: Payment hangs on "Processing..."
**Solution**:
- Check browser console for errors
- Check network tab for failed requests
- Verify JWT token is valid
- Check server logs for errors

### Issue: Order created but didn't redirect
**Solution**:
- Check `/customer/my-orders` page directly
- Order may have been created successfully
- Check server logs for errors

---

## What to Verify After Implementation

- [ ] Wallet card is visible and selectable in modal
- [ ] Wallet balance displays correctly
- [ ] Insufficient balance warning shows when needed
- [ ] "Proceed with Payment" button enables/disables correctly
- [ ] Payment completes instantly
- [ ] Order status shows "paid"
- [ ] Wallet balance is correctly deducted
- [ ] User is redirected to orders page
- [ ] Card payment still works as before
- [ ] Non-logged-in users cannot select wallet
- [ ] Console has no JavaScript errors
- [ ] Network requests look correct

---

## Performance Testing

### Load Test Wallet Balance
- Repeated opening/closing payment modal
- Should load balance in < 1 second

### Payment Processing
- Wallet payment should complete in < 2 seconds
- No database locks or timeouts
- Concurrent users can make payments simultaneously

### Error Recovery
- Proper error messages displayed
- User can retry after errors
- No orphaned orders created

---

## Mobile Testing

### Small Device Compatibility
```
✓ Payment modal responsive on mobile
✓ Wallet card touchable (not too small)
✓ Balance text readable
✓ Buttons large enough for touch
✓ Warning box visible on small screens
```

### Orientation Change
```
✓ Modal maintains state when rotating
✓ Layout adjusts properly
✓ All elements still accessible
```

---

## Data Verification Checklist

### After Successful Wallet Payment
- [ ] Order created with correct reference number
- [ ] Order items match cart items
- [ ] Order total matches cart total
- [ ] Order status is "paid" (not "pending")
- [ ] Wallet balance reduced by order amount
- [ ] Payment record created with method="wallet"
- [ ] Payment status is "completed"
- [ ] WalletTransaction record created
- [ ] Transaction type is "debit"

### Database Queries to Verify
```sql
-- Check latest order
SELECT o.*, oi.*, p.* 
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN payments p ON o.id = p.order_id
WHERE o.customer_id = {customer_id}
ORDER BY o.created_at DESC LIMIT 1;

-- Check wallet balance
SELECT w.balance 
FROM wallet w
JOIN customers c ON w.customer_id = c.id
WHERE c.user_id = {user_id};

-- Check wallet transactions
SELECT wt.* 
FROM wallet_transaction wt
JOIN wallet w ON wt.wallet_id = w.id
JOIN customers c ON w.customer_id = c.id
WHERE c.user_id = {user_id}
ORDER BY wt.created_at DESC;
```

---

## Success Criteria

| Test Case | Expected Result | Status |
|-----------|-----------------|--------|
| Sufficient balance | Payment succeeds, redirects | ✓ |
| Insufficient balance | Shows warning, blocks payment | ✓ |
| Not logged in | Alert shows, cannot select | ✓ |
| Zero balance | Shows warning | ✓ |
| Exact balance | Payment succeeds | ✓ |
| High balance | Payment succeeds | ✓ |
| Order creation | Saves to database | ✓ |
| Balance deduction | Correctly reduced | ✓ |
| Status update | Order marked "paid" | ✓ |
| Redirect | Goes to orders page | ✓ |
| Error handling | Proper error messages | ✓ |
| Mobile layout | Responsive design | ✓ |
