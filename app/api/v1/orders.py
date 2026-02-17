"""
Orders API - Fulfillment Pipeline
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
import uuid
from datetime import datetime

# Import email dispatcher
from app.core.emails import dispatch_email

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
    
    # Send order received email
    order_obj = orders_db[order_id]
    req_obj = requirements_db[order_id]
    await dispatch_email("order", "created", order_obj, req_obj)
    
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
    
    # Send sample received email
    await dispatch_email("sample", "created", orders_db[order_id], requirements_db[order_id])
    
    return OrderResponse(
        id=order_id,
        order_type=OrderType.SAMPLE,
        package=Package.PRO,
        quantity=10,
        status=OrderStatus.NEW,
        created_at=now
    )

@router.get("/orders")
async def list_orders(email: Optional[str] = None):
    """List orders for a customer (by email)."""
    orders = list(orders_db.values())
    if email:
        orders = [o for o in orders if requirements_db.get(o["id"], {}).get("work_email") == email]
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    return {"orders": orders}
    """Get order details."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    requirements = requirements_db.get(order_id, {})
    
    return {
        **order,
        "requirements": requirements
    }

@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details by ID."""
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


# ============ ADMIN ENDPOINTS ============

@router.get("/admin/orders")
async def admin_list_orders(status: Optional[str] = None):
    """List all orders (admin)."""
    orders = list(orders_db.values())
    if status:
        orders = [o for o in orders if o["status"] == status]
    # Sort by created_at desc
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    return {"orders": orders}


@router.post("/admin/orders/{order_id}/upload")
async def admin_upload_deliverable(order_id: str, file_data: dict):
    """
    Upload deliverable file for an order.
    Expects: {filename, content_base64, package}
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    import base64
    
    try:
        file_content = base64.b64decode(file_data["content_base64"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file content")
    
    # TODO: Validate CSV against package schema
    # from app.core.csv_schema import validate_csv_schema
    # is_valid, errors = validate_csv_schema(file_content.decode('utf-8'), file_data["package"])
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=f"Validation failed: {errors}")
    
    # Store file (placeholder - implement with storage.py)
    # upload_file(file_content, file_data["filename"], "deliverable", order_id)
    
    # Update order status to ready_for_delivery
    order = orders_db[order_id]
    order["status"] = OrderStatus.READY_FOR_DELIVERY
    order["updated_at"] = datetime.utcnow()
    
    # Log event
    status_events_db.append({
        "order_id": order_id,
        "from_status": order["status"],
        "to_status": OrderStatus.READY_FOR_DELIVERY,
        "note": f"Uploaded deliverable: {file_data['filename']}",
        "created_at": datetime.utcnow()
    })
    
    return {"status": "uploaded", "filename": file_data["filename"]}


@router.post("/admin/orders/{order_id}/deliver")
async def admin_deliver_order(order_id: str):
    """Mark order as delivered and generate signed download URL."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    
    if order["status"] != OrderStatus.READY_FOR_DELIVERY:
        raise HTTPException(status_code=400, detail="Order must be in ready_for_delivery status")
    
    now = datetime.utcnow()
    order["status"] = OrderStatus.DELIVERED
    order["delivered_at"] = now
    order["updated_at"] = now
    
    # Log event
    status_events_db.append({
        "order_id": order_id,
        "from_status": OrderStatus.READY_FOR_DELIVERY,
        "to_status": OrderStatus.DELIVERED,
        "note": "Order delivered",
        "created_at": now
    })
    
    # TODO: Generate signed URL
    # download_url = generate_signed_download_url(storage_key, filename)
    
    return {
        "status": "delivered",
        "delivered_at": now.isoformat()
        # "download_url": download_url
    }


@router.post("/admin/orders/{order_id}/clarification")
async def admin_request_clarification(order_id: str, question: str):
    """Request clarification from customer."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    now = datetime.utcnow()
    
    # Update status
    order["status"] = OrderStatus.AWAITING_CLARIFICATION
    order["updated_at"] = now
    
    # Log event
    status_events_db.append({
        "order_id": order_id,
        "from_status": order.get("_prev_status", OrderStatus.NEW),
        "to_status": OrderStatus.AWAITING_CLARIFICATION,
        "note": f"Clarification needed: {question}",
        "created_at": now
    })
    
    # TODO: Send clarification email
    
    return {"status": "clarification_requested"}


# ============ REPLACEMENT FLOW ============

@router.post("/orders/{order_id}/replacement-request")
async def request_replacement(order_id: str, request: dict):
    """
    Customer requests replacement.
    Expects: {evidence_type, evidence_text, affected_emails}
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    
    if order["status"] != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Can only request replacement for delivered orders")
    
    now = datetime.utcnow()
    
    # Update status
    order["status"] = OrderStatus.REPLACEMENT_REQUESTED
    order["updated_at"] = now
    
    # Log event
    status_events_db.append({
        "order_id": order_id,
        "from_status": OrderStatus.DELIVERED,
        "to_status": OrderStatus.REPLACEMENT_REQUESTED,
        "note": f"Replacement requested. Evidence: {request.get('evidence_type')}",
        "created_at": now
    })
    
    # TODO: Store replacement request
    
    return {"status": "replacement_requested"}


# ============ ANALYTICS ============

@router.post("/analytics")
async def track_event(event: dict):
    """Track analytics event."""
    # TODO: Store in analytics_events table
    print(f"Analytics: {event.get('event_name')}")
    return {"status": "tracked"}


@router.get("/health")
async def health():
    return {"status": "ok"}
