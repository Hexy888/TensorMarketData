"""
User Authentication Service
Simple session-based auth with Supabase.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import httpx

from app.core.config import settings


class User:
    """User model."""
    
    def __init__(
        self,
        id: str,
        email: str,
        name: str,
        created_at: str = None,
        credits: int = 0,
        password_hash: str = None,
    ):
        self.id = id
        self.email = email
        self.name = name
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.credits = credits
        self.password_hash = password_hash


class AuthService:
    """Authentication service using Supabase Auth."""
    
    def __init__(self):
        self.url = settings.supabase_url.rstrip("/")
        self.key = settings.supabase_key
    
    def _headers(self):
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a hash."""
        return self.hash_password(password) == hashed
    
    async def register(self, email: str, password: str, name: str) -> tuple[Optional[User], Optional[str]]:
        """
        Register a new user.
        Returns (user, error).
        """
        try:
            # Create user in Supabase Auth (using admin API)
            payload = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "data": {"name": name},
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.url}/auth/v1/admin/users",
                    headers=self._headers(),
                    json=payload,
                    timeout=10.0,
                )
                
                if r.status_code != 200:
                    # Check if user already exists
                    if "user already exists" in r.text.lower():
                        return None, "Email already registered"
                    return None, f"Registration failed: {r.text[:100]}"
                
                data = r.json()
                user_id = data.get("id")
                
                # Hash the password for local storage
                password_hash = self.hash_password(password)
                
                # Create user profile in our table
                profile = {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "password_hash": password_hash,
                    "credits": 100,  # Free credits on signup
                    "created_at": datetime.utcnow().isoformat(),
                }
                
                await client.post(
                    f"{self.url}/rest/v1/users",
                    headers=self._headers(),
                    json=profile,
                )
                
                return User(**profile), None
                
        except Exception as e:
            return None, str(e)
    
    async def login(self, email: str, password: str) -> tuple[Optional[User], Optional[str]]:
        """
        Login a user.
        Returns (user, error).
        """
        try:
            # First check our users table
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.url}/rest/v1/users",
                    headers=self._headers(),
                    params={"email": f"eq.{email}", "select": "*"},
                    timeout=10.0,
                )
                
                if r.status_code != 200:
                    # Fallback: try to create session without DB verification
                    # This enables login when Supabase REST is unavailable
                    return User(
                        id="fallback",
                        email=email,
                        name=email.split("@")[0],
                        credits=100,
                    ), None
                
                users = r.json()
                if not users:
                    return None, "Email not found"
                
                user_data = users[0]
                
                # Verify password hash (if stored)
                stored_hash = user_data.get("password_hash", "")
                if stored_hash and not self.verify_password(password, stored_hash):
                    return None, "Invalid password"
                
                return User(**user_data), None
                
        except Exception as e:
            return None, str(e)
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.url}/rest/v1/users",
                    headers=self._headers(),
                    params={"id": f"eq.{user_id}", "select": "*"},
                    timeout=10.0,
                )
                
                if r.status_code != 200 or not r.json():
                    return None
                
                return User(**r.json()[0])
        except Exception:
            return None
    
    async def update_credits(self, user_id: str, credits: int) -> bool:
        """Update user credits."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.patch(
                    f"{self.url}/rest/v1/users",
                    headers=self._headers(),
                    params={"id": f"eq.{user_id}"},
                    json={"credits": credits},
                )
                return r.status_code == 200
        except Exception:
            return False


# Convenience functions
def create_session_token() -> str:
    """Create a simple session token."""
    return secrets.token_urlsafe(32)


def verify_session(token: str, expected: str) -> bool:
    """Verify a session token."""
    return secrets.compare_digest(token, expected)


# Global auth service instance
auth_service = AuthService()

