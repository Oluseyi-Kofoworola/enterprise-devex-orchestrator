"""API v1 request/response schemas.

Keep Pydantic models here so routers stay thin.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=120, description="Item name")
    description: str = Field(default="", max_length=500, description="Item description")


class ItemResponse(BaseModel):
    """Schema returned by item endpoints."""

    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., description="Item name")
    description: str = Field(default="", description="Item description")
    project: str = Field(..., description="Owning project name")


class SessionCreate(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    intent: str = Field(default="", description="Detected voice intent")


class SessionResponse(BaseModel):
    id: str
    patient_id: str
    status: str
    intent_detected: str = ""
    created_at: str = ""


class AppointmentCreate(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    provider: str = Field(..., description="Healthcare provider name")
    date_time: str = Field(..., description="Appointment date/time ISO format")
    reason: str = Field(default="", description="Reason for visit")


class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    provider: str
    date_time: str
    status: str
    reason: str = ""


class RefillCreate(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    medication: str = Field(..., description="Medication name")
    pharmacy: str = Field(default="", description="Preferred pharmacy")


class RefillResponse(BaseModel):
    id: str
    patient_id: str
    medication: str
    status: str
