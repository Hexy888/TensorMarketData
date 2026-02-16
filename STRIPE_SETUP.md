# Stripe Payment Setup

## What's Built
- Stripe checkout integration
- Credit packages (Starter $29, Pro $99, Enterprise custom)
- Provider payouts (revenue share model)
- Webhook handling

## Setup Steps

### 1. Create Stripe Account
- Go to stripe.com
- Sign up (free)
- Verify email

### 2. Get API Keys
- Dashboard → Developers → API Keys
- Use **Test Mode** keys (start with `sk_test_` and `pk_test_`)

### 3. Add to Render
1. Go to Render Dashboard → Your Web Service → Environment
2. Add these variables:
   - `STRIPE_SECRET_KEY` = `sk_test_xxxxxxxxxxxx`
   - `STRIPE_PUBLISHABLE_KEY` = `pk_test_xxxxxxxxxxxx`
   - `STRIPE_WEBHOOK_SECRET` = `whsec_xxxxxxxxxxxx` (after creating webhook)
3. Redeploy

### 4. Create Webhook (After deployment)
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://tensormarketdata.onrender.com/api/v1/webhooks/stripe`
3. Select events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`
4. Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET`

### 5. Test It
- Your dashboard will show payment options
- Use Stripe test cards: 4242 4242 4242 4242 (any future date, any CVC)

## Test Card Numbers
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
- Requires auth: 4000 0000 0000 3228

## Current Pricing (in code)
- Starter: $29/mo - 10,000 API calls
- Pro: $99/mo - 100,000 API calls
- Enterprise: Custom
