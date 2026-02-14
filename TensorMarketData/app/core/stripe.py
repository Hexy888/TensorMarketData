"""
Stripe Payment Integration for TensorMarketData.
Handles subscriptions, credits, and provider payouts.
"""

import stripe
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from app.core.config import settings


# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Stripe payment service."""
    
    def __init__(self):
        self.webhook_secret = settings.stripe_webhook_secret
    
    # ============ SUBSCRIPTIONS ============
    
    async def create_customer(self, email: str, name: str = None) -> Dict:
        """Create a Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "tensormarketdata"},
        )
        return customer
    
    async def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID."""
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.NotFound:
            return None
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
    ) -> Dict:
        """Create a subscription."""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
        return subscription
    
    async def cancel_subscription(self, subscription_id: str) -> Dict:
        """Cancel a subscription."""
        return stripe.Subscription.cancel(subscription_id)
    
    # ============ PAYMENTS ============
    
    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict:
        """Create a checkout session for one-time purchase."""
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session
    
    async def create_credit_package_session(
        self,
        customer_id: str,
        package_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict:
        """Create checkout session for credit packages."""
        packages = {
            "starter": {"price": "price_starter", "credits": 1000},
            "pro": {"price": "price_pro", "credits": 10000},
            "enterprise": {"price": "price_enterprise", "credits": 100000},
        }
        
        pkg = packages.get(package_id, packages["starter"])
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="payment",
            line_items=[{"price": pkg["price"], "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"credits": pkg["credits"]},
        )
        return session
    
    # ============ PROVIDER PAYOUTS ============
    
    async def create_connect_account(self, provider_email: str) -> Dict:
        """Create a Stripe Connect account for a data provider."""
        account = stripe.Account.create(
            type="express",
            email=provider_email,
            metadata={"source": "tensormarketdata_provider"},
            capabilities={
                "transfers": {"requested": True},
            },
        )
        return account
    
    async def create_transfer(
        self,
        amount: int,  # in cents
        destination_account: str,
        description: str = None,
    ) -> Dict:
        """Transfer funds to a provider."""
        transfer = stripe.Transfer.create(
            amount=amount,
            currency="usd",
            destination=destination_account,
            description=description,
            metadata={
                "source": "tensormarketdata",
                "type": "provider_payout",
            },
        )
        return transfer
    
    async def get_account_balance(self, account_id: str) -> int:
        """Get provider account balance in cents."""
        balance = stripe.Balance.retrieve(stripe_account=account_id)
        return balance.available[0].amount if balance.available else 0
    
    # ============ WEBHOOKS ============
    
    def construct_webhook_event(self, payload: bytes, signature: str) -> Dict:
        """Verify and construct webhook event."""
        return stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )
    
    async def handle_webhook(self, event: Dict) -> str:
        """Handle incoming webhook."""
        event_type = event["type"]
        data = event["data"]["object"]
        
        handlers = {
            "checkout.session.completed": self._handle_checkout,
            "customer.subscription.created": self._handle_subscription,
            "customer.subscription.deleted": self._handle_cancel,
            "invoice.payment_succeeded": self._handle_payment,
            "invoice.payment_failed": self._handle_payment_failed,
            "account.updated": self._handle_connect_account,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return await handler(data)
        
        return f"Unhandled event: {event_type}"
    
    async def _handle_checkout(self, data: Dict) -> str:
        """Handle checkout completed."""
        credits = data.get("metadata", {}).get("credits", 0)
        customer_id = data.get("customer")
        
        # Add credits to customer account
        # In production, would update database
        return f"Checkout completed: {credits} credits for customer {customer_id}"
    
    async def _handle_subscription(self, data: Dict) -> str:
        """Handle new subscription."""
        return f"Subscription created: {data['id']}"
    
    async def _handle_cancel(self, data: Dict) -> str:
        """Handle subscription cancellation."""
        return f"Subscription cancelled: {data['id']}"
    
    async def _handle_payment(self, data: Dict) -> str:
        """Handle successful payment."""
        return f"Payment succeeded: {data['id']}"
    
    async def _handle_payment_failed(self, data: Dict) -> str:
        """Handle failed payment."""
        return f"Payment failed: {data['id']}"
    
    async def _handle_connect_account(self, data: Dict) -> str:
        """Handle Connect account update."""
        return f"Connect account updated: {data['id']}"


# Price IDs (create in Stripe Dashboard)
PRICES = {
    "starter": {
        "monthly": "price_starter_monthly_id",
        "credits": 1000,
    },
    "pro": {
        "monthly": "price_pro_monthly_id", 
        "credits": 10000,
    },
    "enterprise": {
        "monthly": "price_enterprise_monthly_id",
        "credits": 100000,
    },
}

# Credit packages (Stripe Dashboard prices)
CREDIT_PACKAGES = {
    "starter": {"stripe_price": "price_1T0Z4k3TkjY65gWqiMPrfi2b", "credits": 10000, "dollars": 29},
    "pro": {"stripe_price": "price_1T0Z6s3TkjY65gWqKCaUHu8A", "credits": 100000, "dollars": 99},
    "enterprise": {"stripe_price": "price_credits_100000", "credits": 100000, "dollars": 500},
}

# Revenue share percentage for providers
PROVIDER_REVENUE_SHARE = 0.70  # Providers get 70%


# Global service instance
stripe_service = StripeService()
