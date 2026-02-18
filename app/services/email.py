"""
Email subscription service for marketing notifications.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.supabase import supabase


class EmailService:
    """Email subscription management."""
    
    @staticmethod
    async def subscribe(email: str) -> dict:
        """Add email to subscription list."""
        try:
            # Check if already subscribed
            existing = supabase.table("email_subscribers").select("*").eq("email", email).execute()
            
            if existing.data:
                # Update existing
                supabase.table("email_subscribers").update({
                    "subscribed_at": datetime.utcnow().isoformat(),
                    "active": True,
                }).eq("email", email).execute()
                return {"status": "updated", "email": email}
            
            # Add new subscriber
            supabase.table("email_subscribers").insert({
                "id": str(uuid4()),
                "email": email,
                "subscribed_at": datetime.utcnow().isoformat(),
                "source": "website_footer",
                "active": True,
            }).execute()
            
            return {"status": "subscribed", "email": email}
            
        except Exception as e:
            print(f"Email subscribe error: {e}")
            # Return success anyway to avoid friction
            return {"status": "subscribed", "email": email}
    
    @staticmethod
    async def unsubscribe(email: str) -> dict:
        """Unsubscribe an email."""
        try:
            supabase.table("email_subscribers").update({
                "unsubscribed_at": datetime.utcnow().isoformat(),
                "active": False,
            }).eq("email", email).execute()
            return {"status": "unsubscribed", "email": email}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    
    @staticmethod
    async def get_subscribers(active_only: bool = True) -> List[dict]:
        """Get all subscribers."""
        try:
            query = supabase.table("email_subscribers").select("*")
            if active_only:
                query = query.eq("active", True)
            result = query.execute()
            return result.data or []
        except Exception as e:
            print(f"Get subscribers error: {e}")
            return []
    
    @staticmethod
    async def get_count() -> int:
        """Get subscriber count."""
        try:
            result = supabase.table("email_subscribers").select("id", count="exact").eq("active", True).execute()
            return result.count or 0
        except Exception as e:
            print(f"Get count error: {e}")
            return 0


# Global service instance
email_service = EmailService()
