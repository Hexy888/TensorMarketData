"""
Stripe Payment Integration for TensorMarketData - Reputation Operations.
Handles subscriptions for Package A/B/C.
"""

import stripe
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from app.core.config import settings


# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Stripe payment service for reputation operations."""
    
    def __init__(self):
        self.webhook_secret = settings.stripe_webhook_secret
    
    # ============ SUBSCRIPTIONS ============
    
    async def create_customer(self, email: str, name: str = None) -> Dict:
        """Create a Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "tensormarketdata_reputation"},
        )
        return customer
    
    async def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID."""
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.NotFound:
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """Get customer by email."""
        customers = stripe.Customer.list(email=email, limit=1)
        return customers.data[0] if customers.data else None
    
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
        """Cancel a subscription at period end."""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Get subscription by ID."""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.NotFound:
            return None
    
    # ============ CHECKOUT SESSIONS ============
    
    async def create_checkout_session(
        self,
        price_id: str,
        customer_id: str = None,
        customer_email: str = None,
        success_url: str = "https://tensormarketdata.com/thank-you?session_id={CHECKOUT_SESSION_ID}",
        cancel_url: str = "https://tensormarketdata.com/pricing?canceled=1",
    ) -> Dict:
        """Create a checkout session for subscription."""
        checkout_params = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "allow_promotion_codes": True,
            "billing_address_collection": "required",
            "customer_update": {
                "address": "auto",
                "name": "auto",
            },
            "metadata": {
                "package": self._get_package_from_price(price_id),
            },
        }
        
        if customer_id:
            checkout_params["customer"] = customer_id
        elif customer_email:
            checkout_params["customer_email"] = customer_email
        
        session = stripe.checkout.Session.create(**checkout_params)
        return session
    
    def _get_package_from_price(self, price_id: str) -> str:
        """Map price ID to package name."""
        mapping = {
            "price_monitor_respond_monthly": "package_a",
            "price_package_b_monthly": "package_b",
            "price_multi_location_monthly": "package_c",
        }
        return mapping.get(price_id, "unknown")
    
    # ============ CUSTOMER PORTAL ============
    
    async def create_portal_session(
        self,
        customer_id: str,
        return_url: str = "https://tensormarketdata.com/app/billing",
    ) -> Dict:
        """Create customer portal session."""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session
    
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
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return await handler(data)
        
        return f"Unhandled event: {event_type}"
    
    async def _handle_checkout_completed(self, data: Dict) -> str:
        """Handle checkout session completed."""
        # This is where we'd create the client record
        customer_id = data.get("customer")
        customer_email = data.get("customer_email")
        subscription_id = data.get("subscription")
        package = data.get("metadata", {}).get("package", "unknown")
        
        # Log for now - database operations come in Block 9
        print(f"[STRIPE WEBHOOK] Checkout completed: customer={customer_id}, package={package}")
        
        return f"Checkout completed for package: {package}"
    
    async def _handle_subscription_created(self, data: Dict) -> str:
        """Handle new subscription created."""
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")
        
        print(f"[STRIPE WEBHOOK] Subscription created: {subscription_id}, status={status}")
        
        return f"Subscription created: {subscription_id}"
    
    async def _handle_subscription_updated(self, data: Dict) -> str:
        """Handle subscription updated."""
        subscription_id = data.get("id")
        status = data.get("status")
        
        print(f"[STRIPE WEBHOOK] Subscription updated: {subscription_id}, status={status}")
        
        return f"Subscription updated: {subscription_id}"
    
    async def _handle_subscription_deleted(self, data: Dict) -> str:
        """Handle subscription canceled."""
        subscription_id = data.get("id")
        
        print(f"[STRIPE WEBHOOK] Subscription canceled: {subscription_id}")
        
        return f"Subscription canceled: {subscription_id}"
    
    async def _handle_payment_succeeded(self, data: Dict) -> str:
        """Handle successful payment."""
        invoice_id = data.get("id")
        customer_id = data.get("customer")
        
        print(f"[STRIPE WEBHOOK] Payment succeeded: {invoice_id}")
        
        return f"Payment succeeded: {invoice_id}"
    
    async def _handle_payment_failed(self, data: Dict) -> str:
        """Handle failed payment."""
        invoice_id = data.get("id")
        customer_id = data.get("customer")
        
        print(f"[STRIPE WEBHOOK] Payment failed: {invoice_id}")
        
        return f"Payment failed: {invoice_id}"


# Price IDs - UPDATE WITH REAL STRIPE PRICE IDs
PRICES = {
    "package_a": {
        "name": "Monitor + Respond",
        "price_id": "price_monitor_respond_monthly",  # Replace with real Stripe price ID
        "amount": 9900,  # $99.00 in cents
        "interval": "month",
    },
    "package_b": {
        "name": "Package B",
        "price_id": "price_package_b_monthly",  # Replace with real Stripe price ID
        "amount": 19900,  # $199.00 in cents
        "interval": "month",
    },
    "package_c": {
        "name": "Multi-Location Pro",
        "price_id": "price_multi_location_monthly",  # Replace with real Stripe price ID
        "amount": 39900,  # $399.00 in cents
        "interval": "month",
    },
}


# Global service instance
stripe_service = StripeService()
