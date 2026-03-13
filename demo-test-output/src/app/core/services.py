"""Business service layer -- Healthcare domain.

Domain-specific services with real business logic, validation,
and status management. Uses repository pattern for data access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.repositories import BaseRepository


class SessionService:
    """Manages healthcare voice agent sessions."""

    def __init__(self, repo: BaseRepository) -> None:
        self.repo = repo

    def list_sessions(self, status: str | None = None) -> list[dict]:
        items = self.repo.list_all()
        if status:
            items = [i for i in items if i.get("status") == status]
        return items

    def get_session(self, session_id: str) -> dict | None:
        return self.repo.get(session_id)

    def create_session(self, patient_id: str, intent: str = "") -> dict:
        session = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "status": "active",
            "intent_detected": intent,
            "transcript": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.create(session["id"], session)
        return session

    def end_session(self, session_id: str) -> dict | None:
        session = self.repo.get(session_id)
        if not session:
            return None
        session["status"] = "completed"
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.repo.update(session_id, session)
        return session

    def escalate_session(self, session_id: str, reason: str = "") -> dict | None:
        session = self.repo.get(session_id)
        if not session:
            return None
        if session["status"] != "active":
            raise ValueError(f"Cannot escalate session in {session['status']} state")
        session["status"] = "escalated"
        session["escalation_reason"] = reason
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.repo.update(session_id, session)
        return session


class AppointmentService:
    """Manages medical appointments."""

    def __init__(self, repo: BaseRepository) -> None:
        self.repo = repo

    def list_appointments(self, patient_id: str | None = None) -> list[dict]:
        items = self.repo.list_all()
        if patient_id:
            items = [i for i in items if i.get("patient_id") == patient_id]
        return items

    def book_appointment(self, patient_id: str, provider: str, date_time: str, reason: str = "") -> dict:
        appointment = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "provider": provider,
            "date_time": date_time,
            "reason": reason,
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.create(appointment["id"], appointment)
        return appointment

    def cancel_appointment(self, appointment_id: str) -> dict | None:
        appt = self.repo.get(appointment_id)
        if not appt:
            return None
        if appt["status"] == "cancelled":
            raise ValueError("Appointment is already cancelled")
        appt["status"] = "cancelled"
        self.repo.update(appointment_id, appt)
        return appt


class PrescriptionService:
    """Manages prescription refill requests."""

    def __init__(self, repo: BaseRepository) -> None:
        self.repo = repo

    def list_refills(self, patient_id: str | None = None) -> list[dict]:
        items = self.repo.list_all()
        if patient_id:
            items = [i for i in items if i.get("patient_id") == patient_id]
        return items

    def request_refill(self, patient_id: str, medication: str, pharmacy: str = "") -> dict:
        refill = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "medication": medication,
            "pharmacy": pharmacy,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.create(refill["id"], refill)
        return refill


class AuditService:
    """HIPAA audit trail logging."""

    def __init__(self, repo: BaseRepository) -> None:
        self.repo = repo

    def log_access(self, user_id: str, action: str, resource_type: str, resource_id: str, phi_accessed: bool = False) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "phi_accessed": phi_accessed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.create(entry["id"], entry)
        return entry

    def query_logs(self, user_id: str | None = None, resource_type: str | None = None) -> list[dict]:
        items = self.repo.list_all()
        if user_id:
            items = [i for i in items if i.get("user_id") == user_id]
        if resource_type:
            items = [i for i in items if i.get("resource_type") == resource_type]
        return items


# Keep backward-compatible alias
class ItemService:
    """Backward-compatible wrapper -- delegates to SessionService."""

    def __init__(self, project_name: str = "") -> None:
        self.project_name = project_name

    def list_items(self) -> list[dict]:
        return [{"id": "sample-001", "name": "HealthcareSession", "description": "See /api/v1/sessions", "project": self.project_name}]

    def create_item(self, name: str, description: str = "") -> dict:
        import uuid as _uuid
        return {"id": str(_uuid.uuid4()), "name": name, "description": description, "project": self.project_name}
