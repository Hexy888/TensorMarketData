"""
Webhook Service for Real-Time AI Agent Notifications.
Allows agents to subscribe to data updates.
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.core.config import settings


class WebhookEvent:
    """Webhook event types."""
    
    SUPPLIER_UPDATED = "supplier.updated"
    SUPPLIER_NEW = "supplier.new"
    PRODUCT_NEW = "product.new"
    PRODUCT_STOCK_CHANGE = "product.stock_change"
    SEARCH_COMPLETE = "search.complete"
    
    @classmethod
    def all(cls) -> List[str]:
        return [
            cls.SUPPLIER_UPDATED,
            cls.SUPPLIER_NEW,
            cls.PRODUCT_NEW,
            cls.PRODUCT_STOCK_CHANGE,
            cls.SEARCH_COMPLETE,
        ]


class WebhookSubscription:
    """A webhook subscription."""
    
    def __init__(
        self,
        id: str,
        url: str,
        events: List[str],
        secret: str,
        active: bool = True,
    ):
        self.id = id
        self.url = url
        self.events = events
        self.secret = secret
        self.active = active
        self.created_at = datetime.utcnow().isoformat()


class WebhookService:
    """
    Manages webhook subscriptions and deliveries.
    Used by AI agents to get real-time updates.
    """
    
    def __init__(self):
        # In production, would use Redis
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._delivery_history: List[Dict] = []
    
    # ============ SUBSCRIPTION MANAGEMENT ============
    
    async def create_subscription(
        self,
        url: str,
        events: List[str],
    ) -> WebhookSubscription:
        """Create a new webhook subscription."""
        subscription = WebhookSubscription(
            id=str(uuid4()),
            url=url,
            events=events,
            secret=self._generate_secret(),
        )
        self._subscriptions[subscription.id] = subscription
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get a subscription by ID."""
        return self._subscriptions.get(subscription_id)
    
    async def list_subscriptions(
        self,
        event_type: str = None,
    ) -> List[WebhookSubscription]:
        """List all subscriptions, optionally filtered by event type."""
        subs = list(self._subscriptions.values())
        if event_type:
            subs = [s for s in subs if event_type in s.events]
        return subs
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription."""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False
    
    # ============ EVENT DELIVERY ============
    
    async def emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> List[Dict]:
        """
        Emit an event to all matching subscriptions.
        Returns delivery results.
        """
        results = []
        
        for subscription in self._subscriptions.values():
            if not subscription.active:
                continue
            if event_type not in subscription.events:
                continue
            
            result = await self._deliver_webhook(subscription, event_type, payload)
            results.append(result)
        
        return results
    
    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict:
        """Deliver a single webhook."""
        timestamp = datetime.utcnow().isoformat()
        
        # Build signed payload
        payload_data = {
            "id": str(uuid4()),
            "type": event_type,
            "timestamp": timestamp,
            "data": payload,
        }
        
        signature = self._sign_payload(payload_data, subscription.secret)
        
        # In production, would use httpx.AsyncClient
        # For now, simulate delivery
        result = {
            "subscription_id": subscription.id,
            "url": subscription.url,
            "event_type": event_type,
            "status": "delivered",
            "timestamp": timestamp,
            "signature": signature[:16] + "...",
        }
        
        self._delivery_history.append(result)
        
        # Keep only last 1000 deliveries
        self._delivery_history = self._delivery_history[-1000:]
        
        return result
    
    # ============ SIGNATURES ============
    
    def _generate_secret(self) -> str:
        """Generate a webhook signing secret."""
        return hashlib.sha256(uuid4().bytes).hexdigest()[:32]
    
    def _sign_payload(self, payload: Dict, secret: str) -> str:
        """Sign a payload with HMAC-SHA256."""
        payload_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify a webhook signature."""
        expected = self._sign_payload(json.loads(payload.decode()), secret)
        return hmac.compare_digest(signature, expected)
    
    # ============ DELIVERY HISTORY ============
    
    async def get_history(
        self,
        subscription_id: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get webhook delivery history."""
        history = self._delivery_history
        if subscription_id:
            history = [h for h in history if h["subscription_id"] == subscription_id]
        return history[-limit:]


# ============ WEBHOOK EVENT BUILDERS ============

class EventBuilder:
    """Build standardized webhook events."""
    
    @staticmethod
    def supplier_updated(
        supplier_id: str,
        name: str,
        changes: Dict[str, Any],
    ) -> Dict:
        """Build a supplier updated event."""
        return {
            "type": WebhookEvent.SUPPLIER_UPDATED,
            "supplier_id": supplier_id,
            "name": name,
            "changes": changes,
        }
    
    @staticmethod
    def supplier_new(
        supplier_id: str,
        name: str,
        data: Dict[str, Any],
    ) -> Dict:
        """Build a new supplier event."""
        return {
            "type": WebhookEvent.SUPPLIER_NEW,
            "supplier_id": supplier_id,
            "name": name,
            "data": data,
        }
    
    @staticmethod
    def product_new(
        supplier_id: str,
        supplier_name: str,
        product_id: str,
        product_data: Dict[str, Any],
    ) -> Dict:
        """Build a new product event."""
        return {
            "type": WebhookEvent.PRODUCT_NEW,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "product_id": product_id,
            "data": product_data,
        }
    
    @staticmethod
    def product_stock_change(
        supplier_id: str,
        supplier_name: str,
        product_id: str,
        old_stock: int,
        new_stock: int,
    ) -> Dict:
        """Build a stock change event."""
        return {
            "type": WebhookEvent.PRODUCT_STOCK_CHANGE,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "product_id": product_id,
            "old_stock": old_stock,
            "new_stock": new_stock,
        }


# Global service instance
webhook_service = WebhookService()
event_builder = EventBuilder()
