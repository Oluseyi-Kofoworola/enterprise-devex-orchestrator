"""API v1 router -- domain-specific endpoints.

Auto-generated from intent specification. Entities and endpoints
are derived from the business requirements, not hardcoded templates.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from api.v1.schemas import (RefundCreate, RefundResponse, ReturnCreate, ReturnResponse, PolicyCreate, PolicyResponse, EligibilityCreate, EligibilityResponse, OrderCreate, OrderResponse)
from core.dependencies import get_settings, get_repository
from core.config import Settings
from core.services import (RefundService, ReturnService, PolicyService, EligibilityService, OrderService)

router = APIRouter()


# --- Refund CRUD ---
@router.get("/refunds", response_model=list[RefundResponse], summary="List refunds")
async def list_refunds(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    return svc.list_all(status)


@router.post("/refunds", response_model=RefundResponse, status_code=201, summary="Create refund")
async def create_refund(payload: RefundCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    return svc.create(payload)


@router.get("/refunds/{refund_id}", summary="Get refund by ID")
async def get_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.get(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.put("/refunds/{refund_id}", summary="Update refund")
async def update_refund(refund_id: str, payload: RefundCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.update(refund_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.delete("/refunds/{refund_id}", status_code=204, summary="Delete refund")
async def delete_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    if not svc.delete(refund_id):
        raise HTTPException(status_code=404, detail="Refund not found")


@router.post("/refunds/{refund_id}/approve", summary="Approve Refund")
async def approve_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.approve(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.post("/refunds/{refund_id}/reject", summary="Reject Refund")
async def reject_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.reject(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.post("/refunds/{refund_id}/process", summary="Process Refund")
async def process_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.process(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.post("/refunds/{refund_id}/complete", summary="Complete Refund")
async def complete_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.complete(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.post("/refunds/{refund_id}/escalate", summary="Escalate Refund")
async def escalate_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.escalate(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


@router.post("/refunds/{refund_id}/inspect", summary="Inspect Refund")
async def inspect_refund(refund_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("refund", settings.storage_mode)
    svc = RefundService(repo)
    item = svc.inspect(refund_id)
    if not item:
        raise HTTPException(status_code=404, detail="Refund not found")
    return item


# --- Return CRUD ---
@router.get("/returns", response_model=list[ReturnResponse], summary="List returns")
async def list_returns(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    return svc.list_all(status)


@router.post("/returns", response_model=ReturnResponse, status_code=201, summary="Create return")
async def create_return(payload: ReturnCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    return svc.create(payload)


@router.get("/returns/{return_id}", summary="Get return by ID")
async def get_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.get(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.put("/returns/{return_id}", summary="Update return")
async def update_return(return_id: str, payload: ReturnCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.update(return_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.delete("/returns/{return_id}", status_code=204, summary="Delete return")
async def delete_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    if not svc.delete(return_id):
        raise HTTPException(status_code=404, detail="Return not found")


@router.post("/returns/{return_id}/approve", summary="Approve Return")
async def approve_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.approve(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.post("/returns/{return_id}/reject", summary="Reject Return")
async def reject_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.reject(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.post("/returns/{return_id}/process", summary="Process Return")
async def process_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.process(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.post("/returns/{return_id}/complete", summary="Complete Return")
async def complete_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.complete(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.post("/returns/{return_id}/escalate", summary="Escalate Return")
async def escalate_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.escalate(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


@router.post("/returns/{return_id}/inspect", summary="Inspect Return")
async def inspect_return(return_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("return", settings.storage_mode)
    svc = ReturnService(repo)
    item = svc.inspect(return_id)
    if not item:
        raise HTTPException(status_code=404, detail="Return not found")
    return item


# --- Policy CRUD ---
@router.get("/policies", response_model=list[PolicyResponse], summary="List policies")
async def list_policies(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("policy", settings.storage_mode)
    svc = PolicyService(repo)
    return svc.list_all(status)


@router.post("/policies", response_model=PolicyResponse, status_code=201, summary="Create policy")
async def create_policy(payload: PolicyCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("policy", settings.storage_mode)
    svc = PolicyService(repo)
    return svc.create(payload)


@router.get("/policies/{policy_id}", summary="Get policy by ID")
async def get_policy(policy_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("policy", settings.storage_mode)
    svc = PolicyService(repo)
    item = svc.get(policy_id)
    if not item:
        raise HTTPException(status_code=404, detail="Policy not found")
    return item


@router.put("/policies/{policy_id}", summary="Update policy")
async def update_policy(policy_id: str, payload: PolicyCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("policy", settings.storage_mode)
    svc = PolicyService(repo)
    item = svc.update(policy_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Policy not found")
    return item


@router.delete("/policies/{policy_id}", status_code=204, summary="Delete policy")
async def delete_policy(policy_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("policy", settings.storage_mode)
    svc = PolicyService(repo)
    if not svc.delete(policy_id):
        raise HTTPException(status_code=404, detail="Policy not found")


# --- Eligibility CRUD ---
@router.get("/eligibilities", response_model=list[EligibilityResponse], summary="List eligibilities")
async def list_eligibilities(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("eligibility", settings.storage_mode)
    svc = EligibilityService(repo)
    return svc.list_all(status)


@router.post("/eligibilities", response_model=EligibilityResponse, status_code=201, summary="Create eligibility")
async def create_eligibility(payload: EligibilityCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("eligibility", settings.storage_mode)
    svc = EligibilityService(repo)
    return svc.create(payload)


@router.get("/eligibilities/{eligibility_id}", summary="Get eligibility by ID")
async def get_eligibility(eligibility_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("eligibility", settings.storage_mode)
    svc = EligibilityService(repo)
    item = svc.get(eligibility_id)
    if not item:
        raise HTTPException(status_code=404, detail="Eligibility not found")
    return item


@router.put("/eligibilities/{eligibility_id}", summary="Update eligibility")
async def update_eligibility(eligibility_id: str, payload: EligibilityCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("eligibility", settings.storage_mode)
    svc = EligibilityService(repo)
    item = svc.update(eligibility_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Eligibility not found")
    return item


@router.delete("/eligibilities/{eligibility_id}", status_code=204, summary="Delete eligibility")
async def delete_eligibility(eligibility_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("eligibility", settings.storage_mode)
    svc = EligibilityService(repo)
    if not svc.delete(eligibility_id):
        raise HTTPException(status_code=404, detail="Eligibility not found")


# --- Order CRUD ---
@router.get("/orders", response_model=list[OrderResponse], summary="List orders")
async def list_orders(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    return svc.list_all(status)


@router.post("/orders", response_model=OrderResponse, status_code=201, summary="Create order")
async def create_order(payload: OrderCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    return svc.create(payload)


@router.get("/orders/{order_id}", summary="Get order by ID")
async def get_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.get(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.put("/orders/{order_id}", summary="Update order")
async def update_order(order_id: str, payload: OrderCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.update(order_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.delete("/orders/{order_id}", status_code=204, summary="Delete order")
async def delete_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    if not svc.delete(order_id):
        raise HTTPException(status_code=404, detail="Order not found")


@router.post("/orders/{order_id}/approve", summary="Approve Order")
async def approve_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.approve(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.post("/orders/{order_id}/reject", summary="Reject Order")
async def reject_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.reject(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.post("/orders/{order_id}/process", summary="Process Order")
async def process_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.process(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.post("/orders/{order_id}/complete", summary="Complete Order")
async def complete_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.complete(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.post("/orders/{order_id}/escalate", summary="Escalate Order")
async def escalate_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.escalate(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item


@router.post("/orders/{order_id}/inspect", summary="Inspect Order")
async def inspect_order(order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("order", settings.storage_mode)
    svc = OrderService(repo)
    item = svc.inspect(order_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order not found")
    return item
