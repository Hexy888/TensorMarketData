# Google Business Profile Client - Full Implementation

from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests

from app.integrations.google_oauth import refresh_access_token

MYBUSINESS_V4_BASE = "https://mybusiness.googleapis.com/v4"
DEFAULT_TIMEOUT = 25


@dataclass
class GBPReview:
    gbp_review_name: str
    reviewer_name: str
    rating: int
    comment: str
    review_time: Optional[datetime]
    has_reply: bool
    reply_text: str


class GBPAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _raise_if_bad(r: requests.Response, context: str) -> None:
    if 200 <= r.status_code < 300:
        return
    try:
        payload = r.json()
    except Exception:
        payload = {"raw": (r.text or "")[:2000]}
    
    msg = f"{context} failed ({r.status_code})"
    try:
        gmsg = payload.get("error", {}).get("message")
        if gmsg:
            msg = f"{msg}: {gmsg}"
    except Exception:
        pass
    raise GBPAPIError(msg, status_code=r.status_code, details=payload)


class GBPClient:
    """Implements GBP Reviews API."""
    
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
    
    def _access_token(self) -> str:
        tok = refresh_access_token(self.refresh_token)
        return tok["access_token"]
    
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token()}"}
    
    # ---------------------------
    # Reviews
    # ---------------------------
    def list_reviews(
        self,
        location_name: str,
        page_size: int = 50,
        order_by: str = "updateTime desc",
        max_pages: int = 50,
    ) -> List[GBPReview]:
        """location_name: 'accounts/123/locations/456'"""
        if not location_name.startswith("accounts/") or "/locations/" not in location_name:
            raise ValueError("location_name must look like 'accounts/{id}/locations/{id}'")
        
        page_size = max(1, min(int(page_size), 50))
        url = f"{MYBUSINESS_V4_BASE}/{location_name}/reviews"
        params = {"pageSize": page_size, "orderBy": order_by}
        
        out: List[GBPReview] = []
        page_token: Optional[str] = None
        pages = 0
        
        while True:
            if page_token:
                params["pageToken"] = page_token
            else:
                params.pop("pageToken", None)
            
            r = requests.get(url, headers=self._headers(), params=params, timeout=DEFAULT_TIMEOUT)
            _raise_if_bad(r, "GBP list_reviews")
            
            data = r.json() or {}
            reviews = data.get("reviews") or []
            
            for it in reviews:
                name = (it.get("name") or "").strip()
                reviewer = it.get("reviewer") or it.get("author") or {}
                reviewer_name = (
                    reviewer.get("displayName") or 
                    reviewer.get("name") or 
                    reviewer.get("profileName") or ""
                ).strip()
                
                # Rating: string or int
                rating_raw = it.get("rating") or it.get("starRating")
                rating = 0
                try:
                    if isinstance(rating_raw, str):
                        mapping = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
                        rating = mapping.get(rating_raw.upper(), 0)
                    else:
                        rating = int(rating_raw)
                except Exception:
                    rating = 0
                
                comment = (it.get("comment") or it.get("reviewText") or "").strip()
                review_time = _parse_dt(it.get("createTime")) or _parse_dt(it.get("updateTime"))
                reply_obj = it.get("reviewReply") or it.get("reply") or {}
                reply_text = (reply_obj.get("comment") or reply_obj.get("text") or "").strip()
                has_reply = bool(reply_text)
                
                if not name:
                    continue
                
                out.append(GBPReview(
                    gbp_review_name=name,
                    reviewer_name=reviewer_name or "Google User",
                    rating=rating,
                    comment=comment,
                    review_time=review_time,
                    has_reply=has_reply,
                    reply_text=reply_text,
                ))
            
            page_token = data.get("nextPageToken")
            pages += 1
            if not page_token or pages >= max_pages:
                break
        
        return out
    
    def post_reply(self, gbp_review_name: str, reply_text: str) -> None:
        """gbp_review_name: 'accounts/123/locations/456/reviews/789'"""
        if not gbp_review_name.startswith("accounts/") or "/reviews/" not in gbp_review_name:
            raise ValueError("gbp_review_name must look like 'accounts/{id}/locations/{id}/reviews/{id}'")
        
        reply_text = (reply_text or "").strip()
        if not reply_text:
            raise ValueError("reply_text empty")
        
        url = f"{MYBUSINESS_V4_BASE}/{gbp_review_name}/reply"
        payload = {"comment": reply_text}
        
        r = requests.put(
            url,
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        _raise_if_bad(r, "GBP post_reply")
    
    # ---------------------------
    # Accounts & Locations
    # ---------------------------
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List GBP accounts."""
        url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
        r = requests.get(url, headers=self._headers(), timeout=DEFAULT_TIMEOUT)
        _raise_if_bad(r, "GBP list_accounts")
        return (r.json() or {}).get("accounts", [])
    
    def list_locations(
        self,
        account_name: str,
        read_mask: str = "name,title,storefrontAddress",
    ) -> List[Dict[str, Any]]:
        """List locations for an account."""
        url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations"
        params = {"readMask": read_mask, "pageSize": 100}
        
        out = []
        page_token = None
        
        while True:
            if page_token:
                params["pageToken"] = page_token
            r = requests.get(url, headers=self._headers(), params=params, timeout=DEFAULT_TIMEOUT)
            _raise_if_bad(r, "GBP list_locations")
            data = r.json() or {}
            out.extend(data.get("locations", []) or [])
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        
        return out


def is_verified_location_error(e: Exception) -> bool:
    """Check if error is about unverified location."""
    if not isinstance(e, GBPAPIError):
        return False
    msg = str(e).lower()
    return ("verified" in msg) or ("failed_precondition" in msg) or ("precondition" in msg)
