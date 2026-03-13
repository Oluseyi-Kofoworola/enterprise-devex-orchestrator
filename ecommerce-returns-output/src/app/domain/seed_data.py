"""Seed data — auto-generated from intent specification."""

from __future__ import annotations

_SEED: dict[str, list[dict]] = {
    "refund": [
        {"id": "refund-001", "amount": 49.99, "currency": "USD", "method": "original_payment", "customer_id": "CUSTOMER-1001", "user_id": "USER-1001", "order_id": "ORDER-1001", "product_id": "PRODUCT-1001", "status": "pending", "notes": "Sample refund record #1", "created_at": "2024-03-11T09:00:00Z"},
        {"id": "refund-002", "amount": 125.5, "currency": "USD", "method": "store_credit", "customer_id": "CUSTOMER-1002", "user_id": "USER-1002", "order_id": "ORDER-1002", "product_id": "PRODUCT-1002", "status": "in_progress", "notes": "Sample refund record #2", "created_at": "2024-03-12T010:00:00Z"},
        {"id": "refund-003", "amount": 29.95, "currency": "USD", "method": "exchange", "customer_id": "CUSTOMER-1003", "user_id": "USER-1003", "order_id": "ORDER-1003", "product_id": "PRODUCT-1003", "status": "completed", "notes": "Sample refund record #3", "created_at": "2024-03-13T011:00:00Z"},
    ],
    "return": [
        {"id": "return-001", "reason": "Defective product", "priority": "high", "customer_id": "CUSTOMER-1001", "user_id": "USER-1001", "order_id": "ORDER-1001", "product_id": "PRODUCT-1001", "items": ["item-001", "item-002"], "status": "pending", "notes": "Sample return record #1", "created_at": "2024-03-11T09:00:00Z"},
        {"id": "return-002", "reason": "Wrong size", "priority": "medium", "customer_id": "CUSTOMER-1002", "user_id": "USER-1002", "order_id": "ORDER-1002", "product_id": "PRODUCT-1002", "items": ["item-003"], "status": "in_progress", "notes": "Sample return record #2", "created_at": "2024-03-12T010:00:00Z"},
        {"id": "return-003", "reason": "Changed mind", "priority": "low", "customer_id": "CUSTOMER-1003", "user_id": "USER-1003", "order_id": "ORDER-1003", "product_id": "PRODUCT-1003", "items": ["item-003"], "status": "completed", "notes": "Sample return record #3", "created_at": "2024-03-13T011:00:00Z"},
    ],
    "policy": [
        {"id": "policy-001", "customer_id": "CUSTOMER-1001", "user_id": "USER-1001", "order_id": "ORDER-1001", "product_id": "PRODUCT-1001", "status": "pending", "notes": "Sample policy record #1", "created_at": "2024-03-11T09:00:00Z"},
        {"id": "policy-002", "customer_id": "CUSTOMER-1002", "user_id": "USER-1002", "order_id": "ORDER-1002", "product_id": "PRODUCT-1002", "status": "in_progress", "notes": "Sample policy record #2", "created_at": "2024-03-12T010:00:00Z"},
        {"id": "policy-003", "customer_id": "CUSTOMER-1003", "user_id": "USER-1003", "order_id": "ORDER-1003", "product_id": "PRODUCT-1003", "status": "completed", "notes": "Sample policy record #3", "created_at": "2024-03-13T011:00:00Z"},
    ],
    "eligibility": [
        {"id": "eligibility-001", "customer_id": "CUSTOMER-1001", "user_id": "USER-1001", "order_id": "ORDER-1001", "product_id": "PRODUCT-1001", "status": "pending", "notes": "Sample eligibility record #1", "created_at": "2024-03-11T09:00:00Z"},
        {"id": "eligibility-002", "customer_id": "CUSTOMER-1002", "user_id": "USER-1002", "order_id": "ORDER-1002", "product_id": "PRODUCT-1002", "status": "in_progress", "notes": "Sample eligibility record #2", "created_at": "2024-03-12T010:00:00Z"},
        {"id": "eligibility-003", "customer_id": "CUSTOMER-1003", "user_id": "USER-1003", "order_id": "ORDER-1003", "product_id": "PRODUCT-1003", "status": "completed", "notes": "Sample eligibility record #3", "created_at": "2024-03-13T011:00:00Z"},
    ],
    "order": [
        {"id": "order-001", "reason": "Defective product", "priority": "high", "customer_id": "CUSTOMER-1001", "user_id": "USER-1001", "product_id": "PRODUCT-1001", "items": ["item-001", "item-002"], "status": "pending", "notes": "Sample order record #1", "created_at": "2024-03-11T09:00:00Z"},
        {"id": "order-002", "reason": "Wrong size", "priority": "medium", "customer_id": "CUSTOMER-1002", "user_id": "USER-1002", "product_id": "PRODUCT-1002", "items": ["item-003"], "status": "in_progress", "notes": "Sample order record #2", "created_at": "2024-03-12T010:00:00Z"},
        {"id": "order-003", "reason": "Changed mind", "priority": "low", "customer_id": "CUSTOMER-1003", "user_id": "USER-1003", "product_id": "PRODUCT-1003", "items": ["item-003"], "status": "completed", "notes": "Sample order record #3", "created_at": "2024-03-13T011:00:00Z"},
    ],
}


def get_seed_data(entity_name: str) -> list[dict]:
    """Return seed records for the given entity type."""
    return _SEED.get(entity_name, [])
