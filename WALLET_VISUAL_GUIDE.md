# 💳 Wallet Payment Feature - Visual Guide

## User Interface Flow

### 1. Shopping Cart View
```
┌─────────────────────────────────────┐
│         SHOPPING CART MODAL          │
├─────────────────────────────────────┤
│                                     │
│  🛍️  Product 1  Qty: 1  ₦5,000.00  │
│  🛍️  Product 2  Qty: 2  ₦2,000.00  │
│                                     │
├─────────────────────────────────────┤
│             Total: ₦7,000.00         │
├─────────────────────────────────────┤
│ ┌───────────────────────────────────┐ │
│ │ 🔒 Proceed to Checkout            │ │
│ │         (Click to Open)            │ │
│ └───────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

### 2. Payment Method Selection Modal

#### Modal Opens When User Clicks "Proceed to Checkout"
```
┌─────────────────────────────────────────────────┐
│  Select Payment Method                    [×]   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐           │
│  │  💳          │  │  🏦          │           │
│  │ Card Payment │  │ Bank         │           │
│  │ Pay with     │  │ Transfer     │  🏷       │
│  │ Debit/Credit │  │ (Coming Soon)│           │
│  │              │  │              │           │
│  └──────────────┘  └──────────────┘           │
│                                                 │
│  ┌──────────────┐                             │
│  │  💳          │                             │
│  │ Wallet       │                             │
│  │ Pay from     │                             │
│  │ your wallet  │                             │
│  │ Balance:     │                             │
│  │ ₦10,000.00   │                             │
│  └──────────────┘                             │
│                                                 │
│  ℹ️  Your payment information is encrypted    │
│      and secure...                              │
│                                                 │
├─────────────────────────────────────────────────┤
│ ┌─────────────┐  ┌──────────────────────────┐ │
│ │ ← Back      │  │ ✓ Proceed with Payment   │ │
│ │ to Cart     │  │ (Disabled until select)   │ │
│ └─────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

### 3. Wallet Card Selection States

#### A. Unselected (Before Click)
```
┌──────────────────┐
│    💳            │  ← Wallet icon
│   Wallet         │
│  Pay from your   │
│  Ikeja wallet    │
│  Balance:        │
│  ₦10,000.00      │
└──────────────────┘
Cursor: pointer
```

#### B. Hovered (Before Click)
```
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
│    💳            │  ← Glowing icon
│   Wallet         │
│  Pay from your   │
│  Ikeja wallet    │  ← Highlighted text
│  Balance:        │
│  ₦10,000.00      │
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
Shadow effect, slight lift
```

#### C. Selected (With Sufficient Balance)
```
┌─────────────────────┐
│    💳        ✓       │  ← Checkmark badge
│   Wallet            │
│  Pay from your      │  ← Orange border
│  Ikeja wallet       │  ← Enhanced glow
│  Balance:           │
│  ₦10,000.00         │
└─────────────────────┘
Strong shadow effect
```

#### D. Selected (With Insufficient Balance)
```
┌─────────────────────┐
│    💳        ✓       │
│   Wallet            │
│  Pay from your      │
│  Ikeja wallet       │
│  Balance:           │
│  ₦2,000.00 ⚠️       │  ← Low balance warning
└─────────────────────┘

⚠️  Your wallet balance is insufficient...
    You need ₦5,000.00 more for this purchase
```

---

### 4. Button States

#### A. Before Selection (Disabled)
```
┌──────────────────────────────┐
│ ✓ Proceed with Payment       │
├──────────────────────────────┤
  Opacity: 50%
  Cursor: not-allowed
  Cannot click
```

#### B. After Selection (Enabled - Sufficient Balance)
```
┌──────────────────────────────┐
│ ✓ Proceed with Payment       │
├──────────────────────────────┤
  Opacity: 100%
  Cursor: pointer
  Can click
```

#### C. After Selection (Disabled - Insufficient Balance)
```
┌──────────────────────────────┐
│ ✗ Insufficient Wallet Balance│
├──────────────────────────────┤
  Opacity: 50%
  Cursor: not-allowed
  Cannot click
```

#### D. During Processing
```
┌──────────────────────────────┐
│ ⊙ Processing...              │
├──────────────────────────────┤
  Spinner animation
  Cursor: wait
  Cannot click
```

---

## Payment Processing Flow

### Flowchart
```
┌─ Start ─────────────────────┐
│                              │
│  User clicks Checkout        │
│           │                  │
│           ▼                  │
│  Payment Modal Opens         │
│           │                  │
│           ▼                  │
│  Load Wallet Balance         │
│           │                  │
│           ├─────────────────┐
│           │                 │
│    NO: Show Warning     YES: Enable Button
│           │                 │
│           │    ┌────────────┘
│           │    │
│           │    ▼
│      User Selects   ──NO──┐
│      Payment Method        │
│           │                │
│          YES               │
│           │                │
│           ▼                │
│    Click Proceed ◄─────────┘
│           │
│           ▼
│      Send API Request
│      (payment_method: wallet)
│           │
│           ├──────────────────────┐
│           │                      │
│       SUCCESS          INSUFFICIENT BALANCE
│           │                      │
│           ▼                      ▼
│   Deduct from Wallet       Show Error
│   Mark Order "paid"        Re-open Modal
│   Update Payment Record
│   Create Transaction
│           │
│           ▼
│   Clear Cart
│   Show Success Message
│           │
│           ▼
│   Redirect to Orders
│           │
│           ▼
│      End (Success)
```

---

## Response Examples

### Successful Payment Response
```json
{
  "success": true,
  "message": "Payment completed using wallet",
  "payment_method": "wallet",
  "order": {
    "id": 42,
    "reference_number": "ORD-20260330-A1B2C3",
    "total_amount": 7000.00,
    "status": "paid"
  },
  "wallet": {
    "previous_balance": 10000.00,
    "new_balance": 3000.00,
    "amount_deducted": 7000.00
  }
}
```

**Frontend Displays:**
```
✓ Payment completed with wallet!

Order: ORD-20260330-A1B2C3
Amount: ₦7,000.00
Status: Paid ✓
```

---

### Insufficient Balance Response
```json
{
  "success": false,
  "message": "Insufficient wallet balance",
  "current_balance": 2000.00,
  "required_amount": 7000.00,
  "shortfall": 5000.00
}
```

**Frontend Displays:**
```
⚠️  Insufficient wallet balance!

Current Balance: ₦2,000.00
Required Amount: ₦7,000.00
Shortfall: ₦5,000.00

Please add funds to your wallet or select 
another payment method.

[← Back to Options]
```

---

## User Journey Sequences

### Sequence 1: Successful Wallet Payment
```
USER                        SYSTEM

Log In
    │
    ├─ Check Auth ────────► ✓ Valid
    │
Add to Cart
    │
    ├─ Store Items ────────► ✓ Items Saved
    │
Click Checkout
    │
    ├─ Fetch Wallet ───────► ✓ ₦10,000.00
    │
Open Modal
    │
    ├─ Display Balance ────► Shows: ₦10,000.00
    │
Select Wallet
    │
    ├─ Validate Balance ───► ✓ Sufficient
    │
    ├─ Enable Button ──────► "Proceed..." (✓)
    │
Click Proceed
    │
    ├─ Process Payment ────► ✓ Success
    │
    ├─ Deduct Balance ─────► ₦3,000.00
    │
    ├─ Create Records ─────► Payment + Transaction
    │
    ├─ Mark Paid ──────────► Order Status: PAID
    │
    ├─ Notify ─────────────► "Payment Complete!"
    │
    ├─ Redirect ───────────► /customer/my-orders
    │
View Orders
```

---

### Sequence 2: Insufficient Balance
```
USER                        SYSTEM

Add to Cart
    │
    ├─ Store Items ────────► ✓ Items Saved
    │  (Total: ₦8,000)
    │
Click Checkout
    │
    ├─ Fetch Wallet ───────► ₦3,000.00
    │
Open Modal
    │
    ├─ Display Balance ────► Shows: ₦3,000.00
    │
Select Wallet
    │
    ├─ Validate Balance ───► ✗ INSUFFICIENT
    │  (Need: ₦8,000, Have: ₦3,000, Shortfall: ₦5,000)
    │
    ├─ Show Warning ───────► "Insufficient balance"
    │
    ├─ Disable Button ─────► "Proceed..." (✗)
    │
Click Back
    │
    ├─ Modal Resets ───────► Payment modal reopens
    │
Select Card Payment
    │
    ├─ Enable Button ──────► "Proceed..." (✓)
    │
Click Proceed
    │
    ├─ Redirect to ────────► Paystack Checkout
    │
Complete Payment
    │
    └─► Order Created (PAID)
```

---

## Database State Changes

### Before Payment
```
WALLET TABLE
┌─────────────────────────────────┐
│ id  │ customer_id │ balance    │
├─────┼─────────────┼────────────┤
│ 1   │ 5           │ 10000.00   │
└─────────────────────────────────┘

ORDERS TABLE
┌──────────────────────────────────────────┐
│ id  │ ref_number │ total │ status       │
├─────┼────────────┼───────┼──────────────┤
│ 41  │ ORD-xxx    │ 7000  │ pending      │
└──────────────────────────────────────────┘
```

### After Wallet Payment
```
WALLET TABLE
┌─────────────────────────────────┐
│ id  │ customer_id │ balance    │
├─────┼─────────────┼────────────┤
│ 1   │ 5           │ 3000.00    │ ← DEDUCTED
└─────────────────────────────────┘

PAYMENTS TABLE (NEW RECORD)
┌───────────────────────────────────────────┐
│ id  │ order_id │ method │ status        │
├─────┼──────────┼────────┼───────────────┤
│ 58  │ 42       │ wallet │ completed     │ ← CREATED
└───────────────────────────────────────────┘

WALLET_TRANSACTION TABLE (NEW RECORD)
┌─────────────────────────────────────────────────┐
│ id  │ wallet_id │ type  │ amount │ reference   │
├─────┼───────────┼───────┼────────┼─────────────┤
│ 156 │ 1         │ debit │ 7000   │ 42 (Order)  │ ← CREATED
└─────────────────────────────────────────────────┘

ORDERS TABLE
┌──────────────────────────────────────────┐
│ id  │ ref_number │ total │ status       │
├─────┼────────────┼───────┼──────────────┤
│ 42  │ ORD-xxx    │ 7000  │ paid         │ ← UPDATED
└──────────────────────────────────────────┘
```

---

## Mobile View

### Payment Modal on Mobile
```
┌──────────────────────────────┐
│ Select Payment Method  [×]   │
├──────────────────────────────┤
│                              │
│  ┌──────────────────────┐   │
│  │  💳 Card Payment     │   │
│  │  Pay with Debit or   │   │
│  │  Credit Card         │   │
│  └──────────────────────┘   │
│                              │
│  ┌──────────────────────┐   │
│  │  🏦 Bank Transfer    │   │
│  │  (Coming Soon)   🏷  │   │
│  └──────────────────────┘   │
│                              │
│  ┌──────────────────────┐   │
│  │  💳 Wallet           │   │
│  │  Pay from your       │   │
│  │  wallet              │   │
│  │  Balance: ₦10,000    │   │
│  └──────────────────────┘   │
│                              │
├──────────────────────────────┤
│ ┌──────────┐ ┌────────────┐ │
│ │← Back    │ │✓ Proceed   │ │
│ └──────────┘ └────────────┘ │
└──────────────────────────────┘
```

---

## Error States

### Error 1: Insufficient Balance
```
┌─────────────────────────────────────┐
│  🏪 Alert                           │
├─────────────────────────────────────┤
│                                     │
│  ❌ Insufficient wallet balance!    │
│                                     │
│  Current Balance: ₦2,000.00         │
│  Required Amount: ₦7,000.00         │
│  Shortfall: ₦5,000.00               │
│                                     │
│  Please add funds to your wallet    │
│  or select another payment method.  │
│                                     │
│                      [OK]           │
│                                     │
└─────────────────────────────────────┘
```

---

### Error 2: Not Logged In
```
┌─────────────────────────────────────┐
│  🔔 Alert                           │
├─────────────────────────────────────┤
│                                     │
│  Please log in to use wallet        │
│  payment                            │
│                                     │
│                      [OK]           │
│                                     │
└─────────────────────────────────────┘
```

---

## Summary of Visual States

| State | Visual | Interaction |
|-------|--------|-------------|
| **Before Selection** | Neutral card | Clickable |
| **Hover** | Highlighted, lifted | Cursor pointer |
| **Selected** | Orange border, checkmark | Button enabled |
| **Insufficient** | Selected + warning | Button disabled |
| **Processing** | Loading spinner | Cannot interact |
| **Success** | Green notification | Auto-redirect |
| **Error** | Alert box | Allow retry |

---

## Color Scheme

```
Primary Colors:
├─ Orange:  #FF6B35 (Action, Success)
├─ Gold:    #d4af37  (Accent)
├─ Blue:    #1e3a5f  (Info)
├─ White:   #ffffff  (Text, Background)
├─ Dark:    #0b0b0b  (Primary BG)
└─ Muted:   #9aa0a6  (Secondary text)
```

---

## Key Visual Indicators

✓ **Checkmark** - Selection confirmed
× **Close** - Close modal
⊙ **Spinner** - Processing
⚠️ **Warning** - Action needed
ℹ️ **Info** - Additional information
❌ **Error** - Something failed
✅ **Success** - Action completed

---

This visual guide helps understand the complete user interface and experience flow for the wallet payment system!
