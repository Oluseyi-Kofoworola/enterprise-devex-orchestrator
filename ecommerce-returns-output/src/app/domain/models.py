"""Domain models — auto-generated from intent specification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Refund:
    id: str = ""
    amount: float = 0.0
    currency: str = ""
    method: str = ""
    customer_id: str = ""
    user_id: str = ""
    order_id: str = ""
    product_id: str = ""
    status: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Return:
    id: str = ""
    reason: str = ""
    priority: str = ""
    customer_id: str = ""
    user_id: str = ""
    order_id: str = ""
    product_id: str = ""
    items: list[str] = field(default_factory=list)
    status: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Policy:
    id: str = ""
    customer_id: str = ""
    user_id: str = ""
    order_id: str = ""
    product_id: str = ""
    status: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Eligibility:
    id: str = ""
    customer_id: str = ""
    user_id: str = ""
    order_id: str = ""
    product_id: str = ""
    status: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Order:
    id: str = ""
    reason: str = ""
    priority: str = ""
    customer_id: str = ""
    user_id: str = ""
    product_id: str = ""
    items: list[str] = field(default_factory=list)
    status: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

