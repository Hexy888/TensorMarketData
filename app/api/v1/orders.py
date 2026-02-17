"""
Orders API - Fulfillment Pipeline
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
import uuid
from datetime import datetime

router = APIRouter()

# Enums
class Package(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    PREMIUM = "premium"

class OrderType(str, Enum):
    PAID = "paid"
    SAMPLE = "sample"

class OrderStatus(str, Enum):
    NEW = "new"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    ACCEPTED = "accepted"
    IN_RESEARCH = "in_research"
    VERIFYING = "verifying"
    ENRICHING = "enriching"
    READY_FOR_DELIVERY = "ready_for_delivery"
    DELIVERED = "delivered"
    REPLACEMENT_REQUESTED = "replacement_requested"
    REPLACEMENT_DELIVERED = "replacement_delivered"
    CLOSED = "closed"

class OutreachChannel(str, Enum):
    COLD_EMAIL = "cold_email"
    LINKEDIN = "linkedin"
    CALLLING = "calling"

# Minimums
MINIMUMS = {
    Package.STARTER: 300,
    Package.PRO: 200,
    Package.PREMIUM: 150
}

# Status transitions
ALLOWED_TRANSITIONS = {
    OrderStatus.NEW: [OrderStatus.AWAITING_CLARIFICATION, OrderStatus.ACCEPTED],
    OrderStatus.AWAITING_CLARIFICATION: [OrderStatus.ACCEPTED],
    OrderStatus.ACCEPTED: [OrderStatus.IN_RESEARCH],
    OrderStatus.IN_RESEARCH: [OrderStatus.VERIFYING],
    OrderStatus.VERIFYING: [OrderStatus.ENRICHING],
    OrderStatus.ENRICHING: [OrderStatus.READY_FOR_DELIVERY],
    OrderStatus.READY_FOR_DELIVERY: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [OrderStatus.REPLACEMENT_REQUESTED, OrderStatus.CLOSED],
    OrderStatus.REPLACEMENT_REQUESTED: [OrderStatus.REPLACEMENT_DELIVERED],
    OrderStatus.REPLACEMENT_DELIVERED: [OrderStatus.CLOSED],
    OrderStatus.CLOSED: []
}

# Schemas
class Geography(BaseModel):
    country: str
    regions: Optional[List[str]] = None
    metros: Optional[List[str]] = None

class BuyerTitles(BaseModel):
    titles: List[str]
    free_text: Optional[str] = None

class OrderRequirements(BaseModel):
    work_email: EmailStr
    target_industry: str
    geography: Geography
    company_size_range: str
    buyer_titles: BuyerTitles
    outreach_channel: OutreachChannel
    exclusions: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    order_type: OrderType
    package: Package
    quantity: int
    requirements: OrderRequirements

class OrderResponse(BaseModel):
    id: str
    order_type: OrderType
    package: Package
    quantity: int
    status: OrderStatus
    eta_at: Optional[datetime] = None
    created_at: datetime

class SampleCreate(BaseModel):
    work_email: EmailStr
    target_industry: str
    geography: str
    company_size_range: str
    buyer_titles: str
    outreach_channel: OutreachChannel

# In-memory storage (replace with Supabase)
orders_db: dict = {}
requirements_db: dict = {}
status_events_db: list = []

@router.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """Create a new paid order."""
    # Validate minimum
    if order.quantity < MINIMUMS.get(order.package, 200):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum for {order.package} is {MINIMUMS[order.package]} leads"
        )
    
    order_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    orders_db[order_id] = {
        "id": order_id,
        "order_type": order.order_type,
        "package": order.package,
        "quantity": order.quantity,
        "status": OrderStatus.NEW,
        "eta_at": None,
        "accepted_at": None,
        "delivered_at": None,
        "closed_at": None,
        "created_at": now,
        "updated_at": now
    }
    
    requirements_db[order_id] = {
        "order_id": order_id,
        **order.requirements.model_dump(),
        "created_at": now
    }
    
    # Log status event
    status_events_db.append({
        "order_id": order_id,
        "from_status": None,
        "to_status": OrderStatus.NEW,
        "note": "Order created",
        "created_at": now
    })
    
    return OrderResponse(
        id=order_id,
        order_type=order.order_type,
        package=order.package,
        quantity=order.quantity,
        status=OrderStatus.NEW,
        created_at=now
    )

@router.post("/samples", response_model=OrderResponse)
async def create_sample(sample: SampleCreate):
    """Create a free sample request (10 leads, Pro package)."""
    order_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    orders_db[order_id] = {
        "id": order_id,
        "order_type": OrderType.SAMPLE,
        "package": Package.PRO,
        "quantity": 10,
        "status": OrderStatus.NEW,
        "eta_at": None,
        "accepted_at": None,
        "delivered_at": None,
        "closed_at": None,
        "created_at": now,
        "updated_at": now
    }
    
    requirements_db[order_id] = {
        "order_id": order_id,
        "work_email": sample.work_email,
        "target_industry": sample.target_industry,
        "geography": {"country": sample.geography},
        "company_size_range": sample.company_size_range,
        "buyer_titles": {"titles": sample.buyer_titles.split(", "), "free_text": None},
        "outreach_channel": sample.outreach_channel,
        "exclusions": None,
        "deadline": None,
        "notes": None,
        "created_at": now
    }
    
    status_events_db.append({
        "order_id": order_id,
        "from_status": None,
        "to_status": OrderStatus.NEW,
        "note": "Sample request created",
        "created_at": now
    })
    
    return OrderResponse(
        id=order_id,
        order_type=OrderType.SAMPLE,
        package=Package.PRO,
        quantity=10,
        status=OrderStatus.NEW,
        created_at=now
    )

@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    requirements = requirements_db.get(order_id, {})
    
    return {
        **order,
        "requirements": requirements
    }

@router.post("/orders/{order_id}/status")
async def update_order_status(order_id: str, new_status: OrderStatus, note: Optional[str] = None):
    """Update order status (with transition validation)."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    current_status = order["status"]
    
    # Validate transition
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {current_status} to {new_status}"
        )
    
    now = datetime.utcnow()
    order["status"] = new_status
    order["updated_at"] = now
    
    if new_status == OrderStatus.ACCEPTED:
        order["accepted_at"] = now
    elif new_status == OrderStatus.DELIVERED:
        order["delivered_at"] = now
    elif new_status == OrderStatus.CLOSED:
        order["closed_at"] = now
    
    # Log event
    status_events_db.append({
        "order_id": order_id,
        "from_status": current_status,
        "to_status": new_status,
        "note": note,
        "created_at": now
    })
    
    return {"status": "updated", "new_status": new_status}

@router.get("/orders/{order_id}/events")
async def get_order_events(order_id: str):
    """Get order status change history."""
    events = [e for e in status_events_db if e["order_id"] == order_id]
    return {"events": events}

@router.get("/health")
async def health():
    return {"status": "ok"}
