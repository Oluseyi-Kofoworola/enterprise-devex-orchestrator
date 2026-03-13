"""Seed data -- Healthcare demo records.

Pre-loaded into InMemoryRepository on first access
so the API returns realistic data immediately.
"""

from __future__ import annotations

_SEED: dict[str, list[dict]] = {
    "session": [
        {"id": "ses-001", "patient_id": "P-1001", "status": "active", "intent_detected": "appointment_booking", "transcript": ["Hello, I need to schedule a checkup"], "created_at": "2024-03-15T09:00:00Z", "updated_at": "2024-03-15T09:05:00Z"},
        {"id": "ses-002", "patient_id": "P-1002", "status": "completed", "intent_detected": "prescription_refill", "transcript": ["I need to refill my blood pressure medication"], "created_at": "2024-03-15T10:00:00Z", "updated_at": "2024-03-15T10:12:00Z"},
        {"id": "ses-003", "patient_id": "P-1003", "status": "escalated", "intent_detected": "symptom_report", "transcript": ["I have been experiencing chest pain"], "escalation_reason": "Urgent symptom reported", "created_at": "2024-03-15T11:00:00Z", "updated_at": "2024-03-15T11:01:00Z"},
    ],
    "appointment": [
        {"id": "apt-001", "patient_id": "P-1001", "provider": "Dr. Sarah Chen", "date_time": "2024-03-20T14:00:00Z", "reason": "Annual checkup", "status": "scheduled", "created_at": "2024-03-15T09:05:00Z"},
        {"id": "apt-002", "patient_id": "P-1004", "provider": "Dr. James Wilson", "date_time": "2024-03-21T10:30:00Z", "reason": "Follow-up consultation", "status": "scheduled", "created_at": "2024-03-14T16:00:00Z"},
        {"id": "apt-003", "patient_id": "P-1002", "provider": "Dr. Maria Garcia", "date_time": "2024-03-18T09:00:00Z", "reason": "Lab results review", "status": "completed", "created_at": "2024-03-10T11:00:00Z"},
    ],
    "prescription": [
        {"id": "rx-001", "patient_id": "P-1002", "medication": "Lisinopril 10mg", "pharmacy": "CVS Pharmacy #4521", "status": "approved", "created_at": "2024-03-15T10:10:00Z"},
        {"id": "rx-002", "patient_id": "P-1005", "medication": "Metformin 500mg", "pharmacy": "Walgreens", "status": "pending", "created_at": "2024-03-15T13:00:00Z"},
        {"id": "rx-003", "patient_id": "P-1001", "medication": "Atorvastatin 20mg", "pharmacy": "CVS Pharmacy #4521", "status": "pending", "created_at": "2024-03-15T14:30:00Z"},
    ],
    "audit": [],
}


def get_seed_data(entity_name: str) -> list[dict]:
    """Return seed records for the given entity type."""
    return _SEED.get(entity_name, [])
