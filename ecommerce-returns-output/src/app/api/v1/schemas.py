"""API v1 request/response schemas.

Auto-generated from intent specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

class RefundCreate(BaseModel):
    """Schema for creating a refund."""

    amount: float = Field(default=..., description="Monetary amount")
    currency: str = Field(default="", description="Currency code (e.g. USD)")
    method: str = Field(default="", description="Processing method")
    customer_id: str = Field(default=..., description="Associated customer identifier")
    user_id: str = Field(default=..., description="Associated user identifier")
    order_id: str = Field(default=..., description="Associated order identifier")
    product_id: str = Field(default=..., description="Associated product identifier")
    notes: str = Field(default="", description="Additional notes")


class RefundResponse(BaseModel):
    """Schema returned by refund endpoints."""

    id: str = Field(..., description="Unique identifier")
    amount: float = Field(..., description="Monetary amount")
    currency: str = Field(default=None, description="Currency code (e.g. USD)")
    method: str = Field(default=None, description="Processing method")
    customer_id: str = Field(..., description="Associated customer identifier")
    user_id: str = Field(..., description="Associated user identifier")
    order_id: str = Field(..., description="Associated order identifier")
    product_id: str = Field(..., description="Associated product identifier")
    status: str = Field(..., description="Current status")
    notes: str = Field(default=None, description="Additional notes")
    created_at: str = Field(default="", description="Creation timestamp")


class ReturnCreate(BaseModel):
    """Schema for creating a return."""

    reason: str = Field(default="", description="Reason or justification")
    priority: str = Field(default="", description="Priority level")
    customer_id: str = Field(default=..., description="Associated customer identifier")
    user_id: str = Field(default=..., description="Associated user identifier")
    order_id: str = Field(default=..., description="Associated order identifier")
    product_id: str = Field(default=..., description="Associated product identifier")
    items: list[str] = Field(default=Field(default_factory=list), description="Associated item IDs")
    notes: str = Field(default="", description="Additional notes")


class ReturnResponse(BaseModel):
    """Schema returned by return endpoints."""

    id: str = Field(..., description="Unique identifier")
    reason: str = Field(default=None, description="Reason or justification")
    priority: str = Field(default=None, description="Priority level")
    customer_id: str = Field(..., description="Associated customer identifier")
    user_id: str = Field(..., description="Associated user identifier")
    order_id: str = Field(..., description="Associated order identifier")
    product_id: str = Field(..., description="Associated product identifier")
    items: list[str] = Field(default_factory=list, description="Associated item IDs")
    status: str = Field(..., description="Current status")
    notes: str = Field(default=None, description="Additional notes")
    created_at: str = Field(default="", description="Creation timestamp")


class PolicyCreate(BaseModel):
    """Schema for creating a policy."""

    customer_id: str = Field(default=..., description="Associated customer identifier")
    user_id: str = Field(default=..., description="Associated user identifier")
    order_id: str = Field(default=..., description="Associated order identifier")
    product_id: str = Field(default=..., description="Associated product identifier")
    notes: str = Field(default="", description="Additional notes")


class PolicyResponse(BaseModel):
    """Schema returned by policy endpoints."""

    id: str = Field(..., description="Unique identifier")
    customer_id: str = Field(..., description="Associated customer identifier")
    user_id: str = Field(..., description="Associated user identifier")
    order_id: str = Field(..., description="Associated order identifier")
    product_id: str = Field(..., description="Associated product identifier")
    status: str = Field(..., description="Current status")
    notes: str = Field(default=None, description="Additional notes")
    created_at: str = Field(default="", description="Creation timestamp")


class EligibilityCreate(BaseModel):
    """Schema for creating a eligibility."""

    customer_id: str = Field(default=..., description="Associated customer identifier")
    user_id: str = Field(default=..., description="Associated user identifier")
    order_id: str = Field(default=..., description="Associated order identifier")
    product_id: str = Field(default=..., description="Associated product identifier")
    notes: str = Field(default="", description="Additional notes")


class EligibilityResponse(BaseModel):
    """Schema returned by eligibility endpoints."""

    id: str = Field(..., description="Unique identifier")
    customer_id: str = Field(..., description="Associated customer identifier")
    user_id: str = Field(..., description="Associated user identifier")
    order_id: str = Field(..., description="Associated order identifier")
    product_id: str = Field(..., description="Associated product identifier")
    status: str = Field(..., description="Current status")
    notes: str = Field(default=None, description="Additional notes")
    created_at: str = Field(default="", description="Creation timestamp")


class OrderCreate(BaseModel):
    """Schema for creating a order."""

    reason: str = Field(default="", description="Reason or justification")
    priority: str = Field(default="", description="Priority level")
    customer_id: str = Field(default=..., description="Associated customer identifier")
    user_id: str = Field(default=..., description="Associated user identifier")
    product_id: str = Field(default=..., description="Associated product identifier")
    items: list[str] = Field(default=Field(default_factory=list), description="Associated item IDs")
    notes: str = Field(default="", description="Additional notes")


class OrderResponse(BaseModel):
    """Schema returned by order endpoints."""

    id: str = Field(..., description="Unique identifier")
    reason: str = Field(default=None, description="Reason or justification")
    priority: str = Field(default=None, description="Priority level")
    customer_id: str = Field(..., description="Associated customer identifier")
    user_id: str = Field(..., description="Associated user identifier")
    product_id: str = Field(..., description="Associated product identifier")
    items: list[str] = Field(default_factory=list, description="Associated item IDs")
    status: str = Field(..., description="Current status")
    notes: str = Field(default=None, description="Additional notes")
    created_at: str = Field(default="", description="Creation timestamp")

