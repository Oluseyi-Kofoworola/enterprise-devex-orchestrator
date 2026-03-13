"""Domain models -- Healthcare."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Session:
    id: str = ""
    patient_id: str = ""
    status: str = "active"
    intent_detected: str = ""
    transcript: list[str] = field(default_factory=list)
    escalation_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Appointment:
    id: str = ""
    patient_id: str = ""
    provider: str = ""
    date_time: str = ""
    reason: str = ""
    status: str = "scheduled"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PrescriptionRefill:
    id: str = ""
    patient_id: str = ""
    medication: str = ""
    pharmacy: str = ""
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AuditLog:
    id: str = ""
    user_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    phi_accessed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
