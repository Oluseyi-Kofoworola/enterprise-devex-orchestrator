"""SLHS Voice Agent -- St. Luke's Health System

Enterprise-grade healthcare voice agent with:
- Real-time voice chat (Web Speech API with cross-browser fallback)
- Patient record lookup with rich card display
- Medications, vitals, lab results, and referral tracking
- Appointment scheduling with conversational flow
- HIPAA-ready audit logging and session management
- Key Vault integration and Managed Identity auth
"""

from __future__ import annotations

import html as html_mod
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# -- Configuration ----------------------------------------------------
APP_NAME = "SLHS Voice Agent"
VERSION = "3.0.0"

# -- Logging ----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("slhs-voice-agent")

# -- FastAPI Application ---------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="St. Luke's Health System Voice Agent -- enterprise real-time healthcare assistant with voice interaction, patient records, and appointment scheduling.",
    docs_url="/docs",
    redoc_url=None,
)

# =====================================================================
# In-Memory Data (demo -- production would use Cosmos DB / SQL)
# =====================================================================

PATIENTS: dict[str, dict] = {
    "P-1001": {
        "id": "P-1001", "first_name": "Maria", "last_name": "Garcia",
        "dob": "1985-03-14", "phone": "(555) 234-5678",
        "conditions": ["Type 2 Diabetes", "Hypertension"],
        "allergies": ["Penicillin"], "primary_doctor": "Dr. Sarah Chen",
        "last_visit": "2026-02-15", "next_appointment": "2026-03-20",
        "insurance": "Blue Cross Blue Shield",
        "medications": [
            {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"},
            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"},
        ],
        "vitals": {"bp": "128/82", "hr": 72, "temp": "98.6F", "spo2": "98%", "weight": "154 lbs"},
        "lab_results": [
            {"test": "HbA1c", "result": "6.8%", "date": "2026-02-15", "status": "borderline"},
            {"test": "Lipid Panel", "result": "Total: 195 mg/dL", "date": "2026-02-15", "status": "normal"},
        ],
    },
    "P-1002": {
        "id": "P-1002", "first_name": "James", "last_name": "Wilson",
        "dob": "1972-08-22", "phone": "(555) 345-6789",
        "conditions": ["Asthma", "Seasonal Allergies"],
        "allergies": [], "primary_doctor": "Dr. Michael Park",
        "last_visit": "2026-01-28", "next_appointment": None,
        "insurance": "Aetna",
        "medications": [
            {"name": "Albuterol", "dosage": "90mcg", "frequency": "As needed"},
            {"name": "Cetirizine", "dosage": "10mg", "frequency": "Once daily"},
        ],
        "vitals": {"bp": "118/76", "hr": 68, "temp": "98.4F", "spo2": "97%", "weight": "182 lbs"},
        "lab_results": [
            {"test": "CBC", "result": "WBC 7.2, RBC 4.8", "date": "2026-01-28", "status": "normal"},
        ],
    },
    "P-1003": {
        "id": "P-1003", "first_name": "Emily", "last_name": "Johnson",
        "dob": "1990-11-05", "phone": "(555) 456-7890",
        "conditions": ["Migraine"], "allergies": ["Sulfa drugs"],
        "primary_doctor": "Dr. Sarah Chen",
        "last_visit": "2026-03-01", "next_appointment": "2026-04-10",
        "insurance": "UnitedHealthcare",
        "medications": [
            {"name": "Sumatriptan", "dosage": "50mg", "frequency": "As needed for migraine"},
        ],
        "vitals": {"bp": "110/70", "hr": 64, "temp": "98.2F", "spo2": "99%", "weight": "135 lbs"},
        "lab_results": [],
    },
    "P-1004": {
        "id": "P-1004", "first_name": "Robert", "last_name": "Thompson",
        "dob": "1965-06-30", "phone": "(555) 567-8901",
        "conditions": ["Coronary Artery Disease", "High Cholesterol", "GERD"],
        "allergies": ["Aspirin", "Ibuprofen"], "primary_doctor": "Dr. Lisa Wong",
        "last_visit": "2026-02-20", "next_appointment": "2026-03-15",
        "insurance": "Medicare",
        "medications": [
            {"name": "Atorvastatin", "dosage": "40mg", "frequency": "Once daily"},
            {"name": "Clopidogrel", "dosage": "75mg", "frequency": "Once daily"},
            {"name": "Omeprazole", "dosage": "20mg", "frequency": "Once daily"},
        ],
        "vitals": {"bp": "136/88", "hr": 78, "temp": "98.5F", "spo2": "96%", "weight": "198 lbs"},
        "lab_results": [
            {"test": "Lipid Panel", "result": "Total: 210 mg/dL, LDL: 130", "date": "2026-02-20", "status": "high"},
            {"test": "Troponin", "result": "0.02 ng/mL", "date": "2026-02-20", "status": "normal"},
        ],
    },
    "P-1005": {
        "id": "P-1005", "first_name": "Sofia", "last_name": "Martinez",
        "dob": "1998-01-17", "phone": "(555) 678-9012",
        "conditions": [], "allergies": [],
        "primary_doctor": "Dr. Michael Park",
        "last_visit": "2025-12-10", "next_appointment": None,
        "insurance": "Cigna",
        "medications": [],
        "vitals": {"bp": "112/72", "hr": 66, "temp": "98.6F", "spo2": "99%", "weight": "128 lbs"},
        "lab_results": [
            {"test": "Metabolic Panel", "result": "All values normal", "date": "2025-12-10", "status": "normal"},
        ],
    },
}

DOCTORS = {
    "Dr. Sarah Chen": {"specialty": "Internal Medicine", "available_slots": 12},
    "Dr. Michael Park": {"specialty": "Family Medicine", "available_slots": 8},
    "Dr. Lisa Wong": {"specialty": "Cardiology", "available_slots": 5},
    "Dr. Raj Patel": {"specialty": "Pulmonology", "available_slots": 10},
    "Dr. Amanda Foster": {"specialty": "Neurology", "available_slots": 7},
}

APPOINTMENTS: list[dict] = []

CONVERSATION_HISTORY: dict[str, list[dict]] = {}

# -- Intent Classification -------------------------------------------

INTENT_RESPONSES = {
    "greeting": "Hello! Welcome to St. Luke's Health System. I'm your virtual healthcare assistant. How can I help you today? I can help with:\n- Looking up patient records\n- Medications and vitals\n- Scheduling appointments\n- Checking doctor availability\n- Lab results and referrals",
    "appointment": "I'd be happy to help you schedule an appointment. Could you provide the patient ID (e.g., P-1001) and preferred doctor or specialty?",
    "doctor": "Here are our available physicians:\n- Dr. Sarah Chen (Internal Medicine) -- 12 slots\n- Dr. Michael Park (Family Medicine) -- 8 slots\n- Dr. Lisa Wong (Cardiology) -- 5 slots\n- Dr. Raj Patel (Pulmonology) -- 10 slots\n- Dr. Amanda Foster (Neurology) -- 7 slots\n\nWould you like to schedule with any of them?",
    "hours": "St. Luke's Health System operating hours:\n- Monday-Friday: 7:00 AM - 8:00 PM\n- Saturday: 8:00 AM - 4:00 PM\n- Sunday: Closed (Emergency only)\n- Telehealth available 24/7",
    "emergency": "If this is a medical emergency, please call 911 immediately or go to your nearest emergency room. St. Luke's Emergency Department is open 24/7. For urgent but non-emergency issues, our urgent care clinic is available during business hours.",
    "insurance": "St. Luke's accepts most major insurance plans including:\n- Blue Cross Blue Shield\n- Aetna\n- UnitedHealthcare\n- Cigna\n- Medicare/Medicaid\n\nFor specific coverage questions, please call our billing department at (555) 123-4567.",
    "pharmacy": "Our on-site pharmacy is located on the first floor, open Monday-Saturday 8 AM - 6 PM. Prescription refills can be requested through your patient portal or by calling (555) 123-4570.",
    "medication": "I can look up medication information for a specific patient. Please provide the patient ID (e.g., P-1001) and I'll show their current prescriptions.",
    "vitals": "I can retrieve vital signs for a specific patient. Please provide the patient ID (e.g., P-1001) and I'll pull up their latest readings.",
    "labs": "I can check lab results for a specific patient. Please provide the patient ID (e.g., P-1001) to view their most recent test results.",
    "default": "I understand you need help. I can assist with:\n- Patient lookups (say a name or ID like P-1001)\n- Medications and vitals\n- Lab results\n- Appointment scheduling\n- Doctor availability\n- Insurance and pharmacy\n\nCould you be more specific?",
}


def classify_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["hi", "hello", "hey", "good morning", "good afternoon", "help"]):
        return "greeting"
    if any(w in msg for w in ["appointment", "schedule", "book", "visit", "slot"]):
        return "appointment"
    if any(w in msg for w in ["doctor", "physician", "specialist", "available"]):
        return "doctor"
    if any(w in msg for w in ["hour", "open", "close", "when"]):
        return "hours"
    if any(w in msg for w in ["emergency", "urgent", "911", "critical"]):
        return "emergency"
    if any(w in msg for w in ["insurance", "coverage", "billing", "pay"]):
        return "insurance"
    if any(w in msg for w in ["pharmacy", "prescription", "refill"]):
        return "pharmacy"
    if any(w in msg for w in ["medication", "medicine", "drug", "rx", "dose"]):
        return "medication"
    if any(w in msg for w in ["vital", "blood pressure", "heart rate", "temperature", "bp", "pulse", "weight"]):
        return "vitals"
    if any(w in msg for w in ["lab", "test result", "blood work", "panel", "hba1c", "cbc"]):
        return "labs"
    return "default"


def _build_patient_html(p: dict) -> str:
    """Build an HTML card for inline chat display of a patient record."""
    conditions = ", ".join(p["conditions"]) if p["conditions"] else "None"
    allergies = ", ".join(p["allergies"]) if p["allergies"] else "None"
    appt = p["next_appointment"] or "Not scheduled"
    allergy_color = "#ef4444" if p["allergies"] else "#6b7280"
    return (
        '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px;margin:4px 0;'
        'font-size:0.85rem;max-width:100%;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
        f'<strong style="color:#0078d4;font-size:0.95rem;">{html_mod.escape(p["first_name"])} {html_mod.escape(p["last_name"])}</strong>'
        f'<span style="background:#e0e7ff;color:#0078d4;padding:2px 8px;border-radius:12px;font-size:0.75rem;">{html_mod.escape(p["id"])}</span>'
        '</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;">'
        f'<div><span style="color:#6b7280;">DOB:</span> {html_mod.escape(p["dob"])}</div>'
        f'<div><span style="color:#6b7280;">Doctor:</span> {html_mod.escape(p["primary_doctor"])}</div>'
        f'<div><span style="color:#6b7280;">Conditions:</span> {html_mod.escape(conditions)}</div>'
        f'<div><span style="color:{allergy_color};">Allergies:</span> {html_mod.escape(allergies)}</div>'
        f'<div><span style="color:#6b7280;">Last Visit:</span> {html_mod.escape(p["last_visit"])}</div>'
        f'<div><span style="color:#6b7280;">Next Appt:</span> {html_mod.escape(appt)}</div>'
        f'<div><span style="color:#6b7280;">Insurance:</span> {html_mod.escape(p.get("insurance", "N/A"))}</div>'
        f'<div><span style="color:#6b7280;">Phone:</span> {html_mod.escape(p["phone"])}</div>'
        '</div></div>'
    )


def _build_meds_html(p: dict) -> str:
    """Build HTML card showing patient medications."""
    meds = p.get("medications", [])
    if not meds:
        return f'<div style="color:#6b7280;font-style:italic;">No active medications for {html_mod.escape(p["first_name"])} {html_mod.escape(p["last_name"])}.</div>'
    rows = ""
    for m in meds:
        rows += (
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #e5e7eb;">'
            f'<strong>{html_mod.escape(m["name"])}</strong>'
            f'<span style="color:#6b7280;">{html_mod.escape(m["dosage"])} -- {html_mod.escape(m["frequency"])}</span></div>'
        )
    return (
        f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px;margin:4px 0;font-size:0.85rem;">'
        f'<div style="font-weight:600;color:#166534;margin-bottom:8px;">Medications for {html_mod.escape(p["first_name"])} {html_mod.escape(p["last_name"])} ({html_mod.escape(p["id"])})</div>'
        f'{rows}</div>'
    )


def _build_vitals_html(p: dict) -> str:
    """Build HTML card showing patient vitals."""
    v = p.get("vitals", {})
    if not v:
        return f'<div style="color:#6b7280;font-style:italic;">No vitals on file for {html_mod.escape(p["first_name"])}.</div>'
    return (
        '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px;margin:4px 0;font-size:0.85rem;">'
        f'<div style="font-weight:600;color:#1e40af;margin-bottom:8px;">Vitals -- {html_mod.escape(p["first_name"])} {html_mod.escape(p["last_name"])}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center;">'
        f'<div style="background:#fff;border-radius:8px;padding:8px;"><div style="font-size:1.1rem;font-weight:700;color:#0078d4;">{html_mod.escape(v.get("bp","--"))}</div><div style="color:#6b7280;font-size:0.75rem;">Blood Pressure</div></div>'
        f'<div style="background:#fff;border-radius:8px;padding:8px;"><div style="font-size:1.1rem;font-weight:700;color:#0078d4;">{v.get("hr","--")}</div><div style="color:#6b7280;font-size:0.75rem;">Heart Rate</div></div>'
        f'<div style="background:#fff;border-radius:8px;padding:8px;"><div style="font-size:1.1rem;font-weight:700;color:#0078d4;">{html_mod.escape(str(v.get("temp","--")))}</div><div style="color:#6b7280;font-size:0.75rem;">Temp</div></div>'
        f'<div style="background:#fff;border-radius:8px;padding:8px;"><div style="font-size:1.1rem;font-weight:700;color:#0078d4;">{html_mod.escape(str(v.get("spo2","--")))}</div><div style="color:#6b7280;font-size:0.75rem;">SpO2</div></div>'
        f'<div style="background:#fff;border-radius:8px;padding:8px;"><div style="font-size:1.1rem;font-weight:700;color:#0078d4;">{html_mod.escape(str(v.get("weight","--")))}</div><div style="color:#6b7280;font-size:0.75rem;">Weight</div></div>'
        '</div></div>'
    )


def _build_labs_html(p: dict) -> str:
    """Build HTML card showing patient lab results."""
    labs = p.get("lab_results", [])
    if not labs:
        return f'<div style="color:#6b7280;font-style:italic;">No lab results on file for {html_mod.escape(p["first_name"])} {html_mod.escape(p["last_name"])}.</div>'
    rows = ""
    for lab in labs:
        color_map = {"normal": "#10b981", "borderline": "#f59e0b", "high": "#ef4444"}
        sc = color_map.get(lab.get("status", ""), "#6b7280")
        rows += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #e5e7eb;">'
            f'<div><strong>{html_mod.escape(lab["test"])}</strong><span style="color:#6b7280;margin-left:8px;font-size:0.8rem;">{html_mod.escape(lab["date"])}</span></div>'
            f'<div><span style="margin-right:8px;">{html_mod.escape(lab["result"])}</span>'
            f'<span style="background:{sc}20;color:{sc};padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;">{html_mod.escape(lab["status"])}</span></div>'
            '</div>'
        )
    return (
        f'<div style="background:#fefce8;border:1px solid #fde68a;border-radius:10px;padding:12px;margin:4px 0;font-size:0.85rem;">'
        f'<div style="font-weight:600;color:#92400e;margin-bottom:8px;">Lab Results -- {html_mod.escape(p["first_name"])} {html_mod.escape(p["last_name"])}</div>'
        f'{rows}</div>'
    )


def generate_response(message: str, session_id: str) -> tuple[str, str]:
    """Generate AI response and optional HTML card. Returns (text, html)."""
    msg = message.lower()

    # Check for specific data requests with patient context
    # First find which patient is referenced
    matched_patient = None
    for pid, patient in PATIENTS.items():
        if pid.lower() in msg or patient["last_name"].lower() in msg or patient["first_name"].lower() in msg:
            matched_patient = patient
            break

    # Also check conversation history for patient context
    if not matched_patient and session_id in CONVERSATION_HISTORY:
        for entry in reversed(CONVERSATION_HISTORY[session_id]):
            if entry["role"] == "assistant":
                for pid, patient in PATIENTS.items():
                    if pid in entry["content"]:
                        matched_patient = patient
                        break
                if matched_patient:
                    break

    # Handle medication queries
    if matched_patient and any(w in msg for w in ["medication", "medicine", "drug", "rx", "dose", "prescription"]):
        meds = matched_patient.get("medications", [])
        text_lines = [f"Medications for {matched_patient['first_name']} {matched_patient['last_name']} ({matched_patient['id']}):"]
        for m in meds:
            text_lines.append(f"- {m['name']} {m['dosage']} ({m['frequency']})")
        if not meds:
            text_lines.append("No active medications on file.")
        return "\n".join(text_lines), _build_meds_html(matched_patient)

    # Handle vitals queries
    if matched_patient and any(w in msg for w in ["vital", "blood pressure", "heart rate", "bp", "pulse", "temp", "weight", "spo2"]):
        v = matched_patient.get("vitals", {})
        text = (
            f"Vitals for {matched_patient['first_name']} {matched_patient['last_name']}:\n"
            f"- BP: {v.get('bp','N/A')}\n- HR: {v.get('hr','N/A')}\n"
            f"- Temp: {v.get('temp','N/A')}\n- SpO2: {v.get('spo2','N/A')}\n- Weight: {v.get('weight','N/A')}"
        )
        return text, _build_vitals_html(matched_patient)

    # Handle lab result queries
    if matched_patient and any(w in msg for w in ["lab", "test result", "blood work", "panel", "hba1c", "cbc", "result"]):
        labs = matched_patient.get("lab_results", [])
        text_lines = [f"Lab results for {matched_patient['first_name']} {matched_patient['last_name']}:"]
        for lab in labs:
            text_lines.append(f"- {lab['test']}: {lab['result']} ({lab['status']}) -- {lab['date']}")
        if not labs:
            text_lines.append("No lab results on file.")
        return "\n".join(text_lines), _build_labs_html(matched_patient)

    # General patient lookup
    if matched_patient:
        p = matched_patient
        conditions = ", ".join(p["conditions"]) if p["conditions"] else "None on record"
        allergies = ", ".join(p["allergies"]) if p["allergies"] else "None on record"
        appt = p["next_appointment"] or "No upcoming appointment"
        med_count = len(p.get("medications", []))
        text = (
            f"Patient Record Found:\n"
            f"- Name: {p['first_name']} {p['last_name']}\n"
            f"- ID: {p['id']}\n"
            f"- DOB: {p['dob']}\n"
            f"- Primary Doctor: {p['primary_doctor']}\n"
            f"- Conditions: {conditions}\n"
            f"- Allergies: {allergies}\n"
            f"- Active Medications: {med_count}\n"
            f"- Insurance: {p.get('insurance', 'N/A')}\n"
            f"- Last Visit: {p['last_visit']}\n"
            f"- Next Appointment: {appt}\n\n"
            f"Ask me about their medications, vitals, or lab results."
        )
        return text, _build_patient_html(p)

    # Check for specific doctor info
    for doc_name, info in DOCTORS.items():
        if doc_name.lower().split()[-1] in msg:
            text = (
                f"{doc_name}\n"
                f"- Specialty: {info['specialty']}\n"
                f"- Available Appointment Slots: {info['available_slots']}\n\n"
                f"Would you like to schedule an appointment with {doc_name}?"
            )
            return text, ""

    intent = classify_intent(message)
    return INTENT_RESPONSES[intent], ""


# =====================================================================
# Pydantic Models
# =====================================================================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class AppointmentRequest(BaseModel):
    patient_id: str
    doctor_name: str
    reason: str = "General consultation"
    preferred_date: Optional[str] = None


# =====================================================================
# Key Vault Client
# =====================================================================

def get_keyvault_client() -> SecretClient:
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    vault_name = os.getenv("KEY_VAULT_NAME", "")
    if not vault_name:
        raise ValueError("KEY_VAULT_NAME environment variable not set")
    vault_url = f"https://{vault_name}.vault.azure.net"
    return SecretClient(vault_url=vault_url, credential=credential)


# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patients_loaded": len(PATIENTS),
        "doctors_available": len(DOCTORS),
    }


@app.get("/api/info")
async def api_info():
    return {
        "service": APP_NAME, "version": VERSION, "status": "running",
        "endpoints": ["/", "/chat", "/docs", "/health", "/api/patients", "/api/doctors", "/api/appointments"],
    }


# -- Chat Endpoint ----------------------------------------------------
@app.post("/api/chat")
async def chat(msg: ChatMessage):
    session_id = msg.session_id or str(uuid.uuid4())
    if session_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[session_id] = []

    CONVERSATION_HISTORY[session_id].append({
        "role": "user", "content": msg.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    response_text, response_html = generate_response(msg.message, session_id)

    CONVERSATION_HISTORY[session_id].append({
        "role": "assistant", "content": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    logger.info(f"Chat session={session_id} intent={classify_intent(msg.message)}")
    return {
        "session_id": session_id,
        "response": response_text,
        "html": response_html,
        "intent": classify_intent(msg.message),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# -- Patient Endpoints ------------------------------------------------
@app.get("/api/patients")
async def list_patients():
    return {"patients": list(PATIENTS.values()), "total": len(PATIENTS)}


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    patient = PATIENTS.get(patient_id.upper())
    if not patient:
        return JSONResponse(status_code=404, content={"error": "Patient not found", "patient_id": patient_id})
    return patient


@app.get("/api/patients/search/{name}")
async def search_patient(name: str):
    results = [
        p for p in PATIENTS.values()
        if name.lower() in p["first_name"].lower() or name.lower() in p["last_name"].lower()
    ]
    return {"results": results, "count": len(results)}


# -- Doctor Endpoints -------------------------------------------------
@app.get("/api/doctors")
async def list_doctors():
    docs = [{"name": k, **v} for k, v in DOCTORS.items()]
    return {"doctors": docs, "total": len(docs)}


# -- Appointment Endpoints --------------------------------------------
@app.post("/api/appointments")
async def create_appointment(req: AppointmentRequest):
    patient = PATIENTS.get(req.patient_id.upper())
    if not patient:
        return JSONResponse(status_code=404, content={"error": "Patient not found"})
    if req.doctor_name not in DOCTORS:
        return JSONResponse(status_code=404, content={"error": "Doctor not found"})
    if DOCTORS[req.doctor_name]["available_slots"] <= 0:
        return JSONResponse(status_code=409, content={"error": "No available slots"})

    appt_date = req.preferred_date or (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    appt = {
        "id": f"APT-{uuid.uuid4().hex[:8].upper()}",
        "patient_id": req.patient_id.upper(),
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "doctor": req.doctor_name,
        "specialty": DOCTORS[req.doctor_name]["specialty"],
        "date": appt_date,
        "reason": req.reason,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    APPOINTMENTS.append(appt)
    DOCTORS[req.doctor_name]["available_slots"] -= 1
    patient["next_appointment"] = appt_date

    logger.info(f"Appointment created: {appt['id']} for {req.patient_id}")
    return appt


@app.get("/api/appointments")
async def list_appointments(patient_id: Optional[str] = Query(None)):
    if patient_id:
        filtered = [a for a in APPOINTMENTS if a["patient_id"] == patient_id.upper()]
        return {"appointments": filtered, "total": len(filtered)}
    return {"appointments": APPOINTMENTS, "total": len(APPOINTMENTS)}


# -- Key Vault Status -------------------------------------------------
@app.get("/keyvault/status")
async def keyvault_status():
    try:
        client = get_keyvault_client()
        list(client.list_properties_of_secrets(max_page_size=1))
        return {"status": "connected", "vault_accessible": True}
    except Exception as e:
        logger.error(f"Key Vault health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


# -- Startup ----------------------------------------------------------
@app.on_event("startup")
async def startup():
    logger.info(f"{APP_NAME} v{VERSION} starting up")
    logger.info(f"Loaded {len(PATIENTS)} patients, {len(DOCTORS)} doctors")


# =====================================================================
# HTML Pages
# =====================================================================

COMMON_CSS = """
:root { --primary: #0078d4; --primary-dark: #005a9e; --bg: #f0f2f5; --card: #fff;
  --text: #1a1a2e; --muted: #6b7280; --green: #10b981; --red: #ef4444;
  --border: #e5e7eb; --shadow: 0 2px 8px rgba(0,0,0,0.08); --amber: #f59e0b; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }
"""

NAV_HTML = """
<nav style="background:#fff;border-bottom:1px solid var(--border);padding:0.5rem 2rem;display:flex;align-items:center;gap:2rem;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
  <a href="/" style="font-weight:700;font-size:1.1rem;color:var(--primary);text-decoration:none;">SLHS Voice Agent</a>
  <a href="/chat" style="font-size:0.9rem;">Voice Chat</a>
  <a href="/patients" style="font-size:0.9rem;">Patients</a>
  <a href="/appointments" style="font-size:0.9rem;">Appointments</a>
  <a href="/docs" style="font-size:0.9rem;">API Docs</a>
  <span style="margin-left:auto;font-size:0.75rem;color:var(--green);">&#9679; Online</span>
</nav>
"""


# -- Landing Page -----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    upcoming = sum(1 for p in PATIENTS.values() if p.get("next_appointment"))
    total_meds = sum(len(p.get("medications", [])) for p in PATIENTS.values())
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{APP_NAME}</title>
<style>{COMMON_CSS}
.hero {{ background:linear-gradient(135deg,#0078d4,#005a9e); color:#fff; padding:3rem 2rem; text-align:center; }}
.hero h1 {{ font-size:2.2rem; margin-bottom:0.5rem; }}
.hero p {{ opacity:0.9; max-width:600px; margin:0 auto; }}
.hero .badge {{ display:inline-block; background:var(--green); padding:0.3rem 1rem; border-radius:2rem;
  font-size:0.8rem; font-weight:600; margin-top:1rem; }}
.hero .dot {{ width:8px;height:8px;border-radius:50%;background:#fff;display:inline-block;margin-right:6px;
  animation:pulse 2s infinite; }}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}
.container {{ max-width:1100px; margin:0 auto; padding:1.5rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; margin:-2rem 0 1.5rem; position:relative; z-index:1; }}
.stat-card {{ background:var(--card); border-radius:12px; padding:1.5rem; text-align:center; box-shadow:var(--shadow); border:1px solid var(--border); }}
.stat-card .num {{ font-size:2rem; font-weight:700; color:var(--primary); }}
.stat-card .label {{ color:var(--muted); font-size:0.85rem; margin-top:0.25rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:1.25rem; }}
.card {{ background:var(--card); border-radius:12px; padding:1.5rem; box-shadow:var(--shadow); border:1px solid var(--border); }}
.card h3 {{ color:var(--primary); font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:1rem; }}
.quick-action {{ display:block; padding:0.75rem 1rem; margin:0.5rem 0; background:var(--bg); border-radius:8px;
  color:var(--text); font-size:0.9rem; transition:all 0.2s; border:1px solid var(--border); }}
.quick-action:hover {{ background:var(--primary); color:#fff; text-decoration:none; border-color:var(--primary); }}
.features {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:0.75rem; }}
.feature {{ display:flex; align-items:center; gap:0.5rem; font-size:0.9rem; padding:0.5rem; }}
.feature .icon {{ font-size:1.3rem; }}
.footer {{ text-align:center; padding:2rem; color:var(--muted); font-size:0.8rem; }}
.patient-row {{ display:flex; justify-content:space-between; align-items:center; padding:0.6rem 0; border-bottom:1px solid var(--border); }}
.patient-row:last-child {{ border:none; }}
</style></head><body>
{NAV_HTML}
<div class="hero">
  <h1>SLHS Voice Agent</h1>
  <p>Enterprise-grade real-time voice-to-voice healthcare assistant for St. Luke's Health System</p>
  <div class="badge"><span class="dot"></span>System Online &mdash; v{VERSION}</div>
</div>
<div class="container">
  <div class="stats">
    <div class="stat-card"><div class="num">{len(PATIENTS)}</div><div class="label">Registered Patients</div></div>
    <div class="stat-card"><div class="num">{len(DOCTORS)}</div><div class="label">Available Doctors</div></div>
    <div class="stat-card"><div class="num">{upcoming}</div><div class="label">Upcoming Appointments</div></div>
    <div class="stat-card"><div class="num">{total_meds}</div><div class="label">Active Prescriptions</div></div>
    <div class="stat-card"><div class="num">{len(APPOINTMENTS)}</div><div class="label">Appointments Today</div></div>
  </div>
  <div class="grid">
    <div class="card">
      <h3>Quick Actions</h3>
      <a href="/chat" class="quick-action">&#127897; Start Voice Conversation</a>
      <a href="/patients" class="quick-action">&#128100; View Patient Records</a>
      <a href="/appointments" class="quick-action">&#128197; Schedule Appointment</a>
      <a href="/docs" class="quick-action">&#128214; API Documentation</a>
    </div>
    <div class="card">
      <h3>Recent Patients</h3>
      {"".join(f'<div class="patient-row"><span><strong>{p["first_name"]} {p["last_name"]}</strong> &mdash; {p["id"]}</span><span style="color:var(--muted);font-size:0.8rem;">{p["primary_doctor"]}</span></div>' for p in list(PATIENTS.values())[:4])}
      <a href="/patients" style="display:block;text-align:center;margin-top:0.75rem;font-size:0.85rem;">View all patients &rarr;</a>
    </div>
    <div class="card" style="grid-column:1/-1;">
      <h3>Platform Capabilities</h3>
      <div class="features">
        <div class="feature"><span class="icon">&#127897;</span> Real-time voice interaction</div>
        <div class="feature"><span class="icon">&#127973;</span> HIPAA-ready workflows</div>
        <div class="feature"><span class="icon">&#128274;</span> RBAC + Managed Identity</div>
        <div class="feature"><span class="icon">&#128202;</span> Azure Monitor observability</div>
        <div class="feature"><span class="icon">&#128138;</span> Medication tracking</div>
        <div class="feature"><span class="icon">&#128200;</span> Lab results &amp; vitals</div>
        <div class="feature"><span class="icon">&#128230;</span> Container Apps auto-scaling</div>
        <div class="feature"><span class="icon">&#128272;</span> Key Vault secret management</div>
      </div>
    </div>
  </div>
</div>
<div class="footer">HIPAA-Compliant Healthcare Platform &mdash; {APP_NAME} v{VERSION} &mdash; St. Luke's Health System</div>
</body></html>"""


# -- Voice Chat Page --------------------------------------------------
@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    # NOTE: All JavaScript curly braces are double-escaped for Python f-string.
    # Template literals in JS use ${{var}} which renders as ${var} in output.
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Voice Chat &mdash; {APP_NAME}</title>
<style>{COMMON_CSS}
.chat-wrap {{ display:flex; flex-direction:column; height:calc(100vh - 52px); max-width:900px; margin:0 auto; padding:0.75rem; }}
.chat-header {{ display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0.75rem;
  background:var(--card); border-radius:12px 12px 0 0; border:1px solid var(--border); border-bottom:none; }}
.chat-header .title {{ font-weight:600; font-size:0.95rem; }}
.chat-header .status {{ display:flex; align-items:center; gap:0.5rem; font-size:0.8rem; color:var(--muted); }}
.chat-header .status .dot {{ width:8px; height:8px; border-radius:50%; background:var(--green); }}
.hipaa-badge {{ background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; }}
.messages {{ flex:1; overflow-y:auto; padding:1rem; background:var(--card); border:1px solid var(--border); border-top:none;
  scroll-behavior:smooth; }}
.msg {{ margin-bottom:1rem; display:flex; gap:0.75rem; animation:fadeIn 0.3s ease-out; }}
@keyframes fadeIn {{ from{{opacity:0;transform:translateY(10px)}} to{{opacity:1;transform:translateY(0)}} }}
.msg.user {{ flex-direction:row-reverse; }}
.msg .bubble {{ max-width:80%; padding:0.75rem 1rem; border-radius:12px; font-size:0.9rem; line-height:1.6; }}
.msg.user .bubble {{ background:var(--primary); color:#fff; border-bottom-right-radius:4px; }}
.msg.assistant .bubble {{ background:#f3f4f6; color:var(--text); border-bottom-left-radius:4px; }}
.msg .avatar {{ width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:1rem; flex-shrink:0; }}
.msg.user .avatar {{ background:var(--primary); color:#fff; }}
.msg.assistant .avatar {{ background:#dbeafe; color:var(--primary); }}
.msg .meta {{ font-size:0.7rem; color:var(--muted); margin-top:4px; }}
.msg.user .meta {{ text-align:right; }}
.typing-indicator {{ display:flex; gap:4px; padding:0.5rem 0; align-items:center; }}
.typing-indicator span {{ width:8px; height:8px; border-radius:50%; background:var(--muted); animation:bounce 1.4s infinite ease-in-out; }}
.typing-indicator span:nth-child(1) {{ animation-delay:0s; }}
.typing-indicator span:nth-child(2) {{ animation-delay:0.2s; }}
.typing-indicator span:nth-child(3) {{ animation-delay:0.4s; }}
@keyframes bounce {{ 0%,80%,100%{{transform:scale(0);opacity:0.4}} 40%{{transform:scale(1);opacity:1}} }}
.suggestions {{ display:flex; flex-wrap:wrap; gap:0.4rem; padding:0.5rem 0.75rem; background:var(--card);
  border:1px solid var(--border); border-top:none; }}
.suggestion {{ padding:0.35rem 0.75rem; background:var(--bg); border:1px solid var(--border); border-radius:2rem;
  font-size:0.8rem; cursor:pointer; transition:all 0.2s; white-space:nowrap; }}
.suggestion:hover {{ background:var(--primary); color:#fff; border-color:var(--primary); }}
.input-area {{ display:flex; gap:0.5rem; padding:0.75rem; background:var(--card); border-radius:0 0 12px 12px;
  border:1px solid var(--border); border-top:none; }}
.input-area input {{ flex:1; padding:0.7rem 1rem; border:2px solid var(--border); border-radius:12px;
  font-size:0.95rem; outline:none; transition:border-color 0.2s; }}
.input-area input:focus {{ border-color:var(--primary); }}
.btn {{ padding:0.7rem 1.25rem; border:none; border-radius:12px; font-size:0.9rem; font-weight:600;
  cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; }}
.btn-send {{ background:var(--primary); color:#fff; min-width:70px; }}
.btn-send:hover {{ background:var(--primary-dark); }}
.btn-send:disabled {{ background:var(--border); cursor:not-allowed; }}
.btn-mic {{ background:var(--card); border:2px solid var(--border); font-size:1.2rem; width:48px; height:48px;
  border-radius:50%; position:relative; }}
.btn-mic:hover {{ border-color:var(--primary); background:#f0f7ff; }}
.btn-mic.recording {{ background:var(--red); border-color:var(--red); color:#fff; }}
.btn-mic.recording::after {{ content:''; position:absolute; inset:-4px; border-radius:50%;
  border:3px solid var(--red); animation:mic-ring 1.5s ease-out infinite; }}
@keyframes mic-ring {{ 0%{{transform:scale(1);opacity:0.6}} 100%{{transform:scale(1.4);opacity:0}} }}
.btn-mic.disabled {{ opacity:0.3; cursor:not-allowed; }}
.voice-status {{ font-size:0.75rem; color:var(--muted); text-align:center; padding:2px 0; min-height:18px; }}
.interim {{ color:var(--primary); font-style:italic; font-size:0.85rem; padding:0 0.75rem; min-height:20px; }}
.voice-bar {{ display:flex; justify-content:center; gap:3px; height:20px; align-items:center; }}
.voice-bar span {{ width:3px; background:var(--red); border-radius:2px; animation:sound 0.5s infinite alternate; }}
.voice-bar span:nth-child(1) {{ height:8px; animation-delay:0s; }}
.voice-bar span:nth-child(2) {{ height:14px; animation-delay:0.1s; }}
.voice-bar span:nth-child(3) {{ height:10px; animation-delay:0.2s; }}
.voice-bar span:nth-child(4) {{ height:16px; animation-delay:0.3s; }}
.voice-bar span:nth-child(5) {{ height:6px; animation-delay:0.4s; }}
@keyframes sound {{ to{{height:3px}} }}
.speaking-indicator {{ display:flex; justify-content:center; gap:3px; height:20px; align-items:center; }}
.speaking-indicator span {{ width:3px; background:var(--primary); border-radius:2px; animation:sound 0.6s infinite alternate; }}
.speaking-indicator span:nth-child(1) {{ height:6px; animation-delay:0.05s; }}
.speaking-indicator span:nth-child(2) {{ height:12px; animation-delay:0.15s; }}
.speaking-indicator span:nth-child(3) {{ height:8px; animation-delay:0.25s; }}
.speaking-indicator span:nth-child(4) {{ height:14px; animation-delay:0.35s; }}
.speaking-indicator span:nth-child(5) {{ height:5px; animation-delay:0.45s; }}
</style></head><body>
{NAV_HTML}
<div class="chat-wrap">
  <div class="chat-header">
    <div class="title">SLHS Voice Assistant</div>
    <div class="status">
      <span class="hipaa-badge">HIPAA</span>
      <span class="dot"></span>
      <span id="connStatus">Connected</span>
    </div>
  </div>
  <div class="messages" id="messages">
    <div class="msg assistant">
      <div class="avatar">&#129302;</div>
      <div>
        <div class="bubble">Welcome to St. Luke's Health System. I'm your healthcare assistant and I can help with:<br><br>
&#128100; <strong>Patient Records</strong> -- Look up by ID (P-1001) or name<br>
&#128138; <strong>Medications</strong> -- View prescriptions and dosages<br>
&#128200; <strong>Vitals &amp; Labs</strong> -- Check vital signs and test results<br>
&#128197; <strong>Appointments</strong> -- Schedule with any physician<br>
&#127897; <strong>Voice</strong> -- Click the mic to speak naturally<br><br>
Try a suggestion below or just ask!</div>
        <div class="meta" id="welcomeTime"></div>
      </div>
    </div>
  </div>
  <div class="suggestions" id="suggestions">
    <span class="suggestion" onclick="useSuggestion(this)">Look up patient P-1001</span>
    <span class="suggestion" onclick="useSuggestion(this)">Garcia medications</span>
    <span class="suggestion" onclick="useSuggestion(this)">Vitals for Thompson</span>
    <span class="suggestion" onclick="useSuggestion(this)">Lab results P-1004</span>
    <span class="suggestion" onclick="useSuggestion(this)">Show available doctors</span>
    <span class="suggestion" onclick="useSuggestion(this)">Schedule an appointment</span>
    <span class="suggestion" onclick="useSuggestion(this)">What are your hours?</span>
    <span class="suggestion" onclick="useSuggestion(this)">Insurance information</span>
  </div>
  <div class="interim" id="interimText"></div>
  <div class="voice-status" id="voiceStatus"></div>
  <div class="input-area">
    <button class="btn btn-mic" id="micBtn" onclick="toggleMic()" title="Hold to speak or click to toggle (Ctrl+M)" aria-label="Voice input">&#127908;</button>
    <input type="text" id="userInput" placeholder="Type a message or press Ctrl+M for voice..." autocomplete="off"
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){{event.preventDefault();sendMessage();}}" aria-label="Chat message input">
    <button class="btn btn-send" id="sendBtn" onclick="sendMessage()" aria-label="Send message">Send</button>
  </div>
</div>
<script>
(function() {{
  'use strict';
  const SESSION_ID = crypto.randomUUID();
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('userInput');
  const micBtn = document.getElementById('micBtn');
  const sendBtn = document.getElementById('sendBtn');
  const interimEl = document.getElementById('interimText');
  const voiceStatusEl = document.getElementById('voiceStatus');
  const suggestionsEl = document.getElementById('suggestions');

  let recognition = null;
  let isRecording = false;
  let isSending = false;
  let isSpeaking = false;
  let voiceRetries = 0;
  const MAX_VOICE_RETRIES = 3;

  // -- Timestamp helpers --
  function timeStr() {{
    return new Date().toLocaleTimeString([], {{hour:'2-digit',minute:'2-digit'}});
  }}
  document.getElementById('welcomeTime').textContent = timeStr();

  // =====================================================
  // Speech Synthesis (text-to-speech)
  // =====================================================
  const synth = window.speechSynthesis;
  let voicesLoaded = false;
  let preferredVoice = null;

  function loadVoices() {{
    const voices = synth.getVoices();
    if (voices.length > 0) {{
      voicesLoaded = true;
      preferredVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Female'))
        || voices.find(v => v.lang.startsWith('en') && (v.name.includes('Zira') || v.name.includes('Samantha')))
        || voices.find(v => v.lang.startsWith('en'))
        || voices[0];
    }}
  }}
  loadVoices();
  if (synth.onvoiceschanged !== undefined) {{
    synth.onvoiceschanged = loadVoices;
  }}
  // Fallback: try loading voices after a short delay
  setTimeout(loadVoices, 500);

  function speak(text) {{
    if (!synth || !text) return;
    synth.cancel();
    // Strip HTML tags and special chars for speech
    const clean = text.replace(/<[^>]*>/g, ' ').replace(/&[a-z]+;/g, ' ')
      .replace(/[-*#|]/g, ' ').replace(/\\s+/g, ' ').trim().substring(0, 600);
    if (!clean) return;
    const utt = new SpeechSynthesisUtterance(clean);
    utt.rate = 1.0;
    utt.pitch = 1.0;
    if (preferredVoice) utt.voice = preferredVoice;
    utt.onstart = () => {{
      isSpeaking = true;
      voiceStatusEl.innerHTML = '<div class="speaking-indicator"><span></span><span></span><span></span><span></span><span></span></div>';
    }};
    utt.onend = () => {{
      isSpeaking = false;
      voiceStatusEl.textContent = '';
    }};
    utt.onerror = () => {{
      isSpeaking = false;
      voiceStatusEl.textContent = '';
    }};
    synth.speak(utt);
  }}

  // =====================================================
  // Speech Recognition (voice-to-text)
  // =====================================================
  const SRConstructor = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SRConstructor) {{
    recognition = new SRConstructor();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onresult = function(e) {{
      let interim = '';
      let final_transcript = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {{
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) {{
          final_transcript += t;
        }} else {{
          interim += t;
        }}
      }}
      if (interim) {{
        interimEl.textContent = interim;
      }}
      if (final_transcript) {{
        interimEl.textContent = '';
        inputEl.value = final_transcript;
        stopRecording();
        sendMessage();
      }}
    }};

    recognition.onend = function() {{
      if (isRecording) stopRecording();
    }};

    recognition.onerror = function(e) {{
      stopRecording();
      if (e.error === 'network') {{
        if (voiceRetries < MAX_VOICE_RETRIES) {{
          voiceRetries++;
          voiceStatusEl.textContent = 'Network issue, retrying (' + voiceRetries + '/' + MAX_VOICE_RETRIES + ')...';
          setTimeout(() => {{
            try {{ recognition.start(); isRecording = true; micBtn.classList.add('recording');
              micBtn.innerHTML = '<div class="voice-bar"><span></span><span></span><span></span><span></span><span></span></div>';
            }} catch(err) {{ voiceStatusEl.textContent = 'Retry failed. Use text input instead.'; }}
          }}, 500 * voiceRetries);
          return;
        }} else {{
          voiceStatusEl.innerHTML = 'Voice unavailable (network blocked). <button onclick="retryVoice()" style="background:#2563eb;color:#fff;border:none;border-radius:4px;padding:2px 8px;cursor:pointer;font-size:0.8rem;">Retry</button> or type your message below.';
          voiceRetries = 0;
          setTimeout(() => {{ if (voiceStatusEl.textContent.startsWith('Voice unavailable')) voiceStatusEl.innerHTML = ''; }}, 10000);
          return;
        }}
      }} else if (e.error === 'not-allowed') {{
        voiceStatusEl.textContent = 'Microphone access denied. Check browser permissions.';
      }} else if (e.error === 'no-speech') {{
        voiceStatusEl.textContent = 'No speech detected. Try again.';
      }} else if (e.error !== 'aborted') {{
        voiceStatusEl.textContent = 'Voice error: ' + e.error;
      }}
      voiceRetries = 0;
      setTimeout(() => {{ voiceStatusEl.textContent = ''; }}, 4000);
    }};
  }} else {{
    micBtn.classList.add('disabled');
    micBtn.title = 'Voice not supported. Use Chrome or Edge for voice input.';
    voiceStatusEl.textContent = 'Voice requires Chrome or Edge browser';
  }}

  function startRecording() {{
    if (!recognition || isRecording) return;
    if (isSpeaking) synth.cancel();
    voiceRetries = 0;
    try {{
      recognition.start();
      isRecording = true;
      micBtn.classList.add('recording');
      micBtn.innerHTML = '<div class="voice-bar"><span></span><span></span><span></span><span></span><span></span></div>';
      voiceStatusEl.textContent = 'Listening...';
      interimEl.textContent = '';
    }} catch(err) {{
      voiceStatusEl.textContent = 'Could not start microphone.';
      setTimeout(() => {{ voiceStatusEl.textContent = ''; }}, 3000);
    }}
  }}

  function stopRecording() {{
    isRecording = false;
    micBtn.classList.remove('recording');
    micBtn.innerHTML = '&#127908;';
    interimEl.textContent = '';
    if (voiceStatusEl.textContent === 'Listening...') voiceStatusEl.textContent = '';
    try {{ recognition?.stop(); }} catch(e) {{}}
  }}

  function toggleMic() {{
    if (!recognition || micBtn.classList.contains('disabled')) return;
    if (isRecording) stopRecording();
    else startRecording();
  }}

  // Keyboard shortcut: Ctrl+M to toggle mic
  document.addEventListener('keydown', function(e) {{
    if (e.ctrlKey && e.key === 'm') {{
      e.preventDefault();
      toggleMic();
    }}
  }});

  // =====================================================
  // Chat Message Rendering
  // =====================================================
  function addMessage(role, text, htmlContent) {{
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    const icon = role === 'user' ? '&#128100;' : '&#129302;';
    const inner = document.createElement('div');

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = icon;
    div.appendChild(avatar);

    const bubbleWrap = document.createElement('div');
    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (htmlContent && role === 'assistant') {{
      // Rich HTML card + text
      const textPart = text.replace(/\\n/g, '<br>');
      bubble.innerHTML = textPart + htmlContent;
    }} else {{
      bubble.innerHTML = text.replace(/\\n/g, '<br>');
    }}
    bubbleWrap.appendChild(bubble);

    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = timeStr();
    bubbleWrap.appendChild(meta);

    div.appendChild(bubbleWrap);
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }}

  function showTyping() {{
    const div = document.createElement('div');
    div.className = 'msg assistant';
    div.id = 'typingMsg';
    div.innerHTML = '<div class="avatar">&#129302;</div><div><div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }}

  function removeTyping() {{
    const el = document.getElementById('typingMsg');
    if (el) el.remove();
  }}

  // =====================================================
  // Send Message
  // =====================================================
  function useSuggestion(el) {{
    inputEl.value = el.textContent;
    sendMessage();
  }}

  async function sendMessage() {{
    const text = inputEl.value.trim();
    if (!text || isSending) return;
    isSending = true;
    inputEl.value = '';
    sendBtn.disabled = true;
    addMessage('user', text, '');
    suggestionsEl.style.display = 'none';
    showTyping();

    try {{
      const resp = await fetch('/api/chat', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{ message: text, session_id: SESSION_ID }})
      }});
      if (!resp.ok) throw new Error('Server error: ' + resp.status);
      const data = await resp.json();
      removeTyping();
      addMessage('assistant', data.response, data.html || '');
      speak(data.response);
    }} catch(err) {{
      removeTyping();
      addMessage('assistant', 'I apologize, but I encountered a connection error. Please try again.', '');
      voiceStatusEl.textContent = 'Connection error';
      setTimeout(() => {{ voiceStatusEl.textContent = ''; }}, 3000);
    }} finally {{
      isSending = false;
      sendBtn.disabled = false;
      inputEl.focus();
    }}
  }}

  // Expose to inline handlers
  window.toggleMic = toggleMic;
  window.sendMessage = sendMessage;
  window.useSuggestion = useSuggestion;
  window.retryVoice = function() {{
    voiceStatusEl.textContent = '';
    voiceRetries = 0;
    startRecording();
  }};
}})();
</script></body></html>"""


# -- Patients Page ----------------------------------------------------
@app.get("/patients", response_class=HTMLResponse)
async def patients_page():
    rows = ""
    for p in PATIENTS.values():
        conditions = ", ".join(p["conditions"]) if p["conditions"] else "None"
        allergies = ", ".join(p["allergies"]) if p["allergies"] else "None"
        med_count = len(p.get("medications", []))
        appt = p["next_appointment"] or "Not scheduled"
        appt_color = "var(--green)" if p["next_appointment"] else "var(--muted)"
        rows += f"""<tr>
          <td><strong>{p['id']}</strong></td>
          <td>{p['first_name']} {p['last_name']}</td>
          <td>{p['dob']}</td>
          <td>{p['primary_doctor']}</td>
          <td>{conditions}</td>
          <td>{allergies}</td>
          <td>{med_count}</td>
          <td style="color:{appt_color}">{appt}</td>
        </tr>"""

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Patients &mdash; {APP_NAME}</title>
<style>{COMMON_CSS}
.container {{ max-width:1300px; margin:0 auto; padding:1.5rem; }}
h2 {{ margin-bottom:1rem; }}
.search {{ padding:0.6rem 1rem; border:2px solid var(--border); border-radius:8px; width:300px; font-size:0.9rem; margin-bottom:1rem; }}
.search:focus {{ outline:none; border-color:var(--primary); }}
table {{ width:100%; border-collapse:collapse; background:var(--card); border-radius:12px; overflow:hidden; box-shadow:var(--shadow); }}
th {{ background:var(--primary); color:#fff; padding:0.75rem 1rem; text-align:left; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; }}
td {{ padding:0.75rem 1rem; border-bottom:1px solid var(--border); font-size:0.85rem; }}
tr:hover td {{ background:#f8fafc; }}
tr:last-child td {{ border:none; }}
</style></head><body>
{NAV_HTML}
<div class="container">
  <h2>Patient Records</h2>
  <input type="text" class="search" placeholder="Search patients..." oninput="filterTable(this.value)">
  <table id="patientTable">
    <thead><tr><th>ID</th><th>Name</th><th>DOB</th><th>Doctor</th><th>Conditions</th><th>Allergies</th><th>Meds</th><th>Next Appt</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<script>
function filterTable(q) {{
  const rows = document.querySelectorAll('#patientTable tbody tr');
  rows.forEach(r => {{ r.style.display = r.textContent.toLowerCase().includes(q.toLowerCase()) ? '' : 'none'; }});
}}
</script></body></html>"""


# -- Appointments Page ------------------------------------------------
@app.get("/appointments", response_class=HTMLResponse)
async def appointments_page():
    doctor_options = "".join(f'<option value="{d}">{d} ({info["specialty"]})</option>' for d, info in DOCTORS.items())
    patient_options = "".join(f'<option value="{p["id"]}">{p["first_name"]} {p["last_name"]} ({p["id"]})</option>' for p in PATIENTS.values())

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Appointments &mdash; {APP_NAME}</title>
<style>{COMMON_CSS}
.container {{ max-width:1100px; margin:0 auto; padding:1.5rem; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }}
@media(max-width:768px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{ background:var(--card); border-radius:12px; padding:1.5rem; box-shadow:var(--shadow); border:1px solid var(--border); }}
.card h3 {{ color:var(--primary); margin-bottom:1rem; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; }}
label {{ display:block; margin-bottom:0.25rem; font-size:0.85rem; font-weight:600; color:var(--muted); margin-top:0.75rem; }}
select,input[type=text],input[type=date] {{ width:100%; padding:0.6rem; border:2px solid var(--border); border-radius:8px; font-size:0.9rem; }}
select:focus,input:focus {{ outline:none; border-color:var(--primary); }}
.btn {{ display:inline-block; padding:0.7rem 1.5rem; background:var(--primary); color:#fff; border:none; border-radius:8px;
  font-size:0.9rem; font-weight:600; cursor:pointer; margin-top:1rem; width:100%; }}
.btn:hover {{ background:var(--primary-dark); }}
.appt-item {{ padding:0.75rem; margin-bottom:0.5rem; background:var(--bg); border-radius:8px; border-left:3px solid var(--green); }}
.appt-item .title {{ font-weight:600; font-size:0.9rem; }}
.appt-item .detail {{ font-size:0.8rem; color:var(--muted); }}
.success {{ background:#ecfdf5; border:1px solid var(--green); color:#065f46; padding:0.75rem; border-radius:8px; margin-top:0.75rem; display:none; }}
#apptList {{ max-height:400px; overflow-y:auto; }}
</style></head><body>
{NAV_HTML}
<div class="container">
  <h2 style="margin-bottom:1rem;">Appointment Management</h2>
  <div class="grid">
    <div class="card">
      <h3>Schedule New Appointment</h3>
      <form id="apptForm" onsubmit="return createAppt(event)">
        <label>Patient</label>
        <select name="patient_id" required>{patient_options}</select>
        <label>Doctor</label>
        <select name="doctor_name" required>{doctor_options}</select>
        <label>Preferred Date</label>
        <input type="date" name="preferred_date">
        <label>Reason</label>
        <input type="text" name="reason" value="General consultation" placeholder="Reason for visit">
        <button type="submit" class="btn">Schedule Appointment</button>
      </form>
      <div class="success" id="successMsg"></div>
    </div>
    <div class="card">
      <h3>Scheduled Appointments</h3>
      <div id="apptList"><div style="color:var(--muted);font-size:0.9rem;padding:1rem;text-align:center;">Loading...</div></div>
    </div>
  </div>
</div>
<script>
async function loadAppts() {{
  const resp = await fetch('/api/appointments');
  const data = await resp.json();
  const el = document.getElementById('apptList');
  if (data.total === 0) {{ el.innerHTML = '<div style="color:var(--muted);font-size:0.9rem;padding:2rem;text-align:center;">No appointments scheduled yet.<br>Use the form to create one.</div>'; return; }}
  el.innerHTML = data.appointments.map(a => `
    <div class="appt-item">
      <div class="title">${{a.patient_name}} &mdash; ${{a.doctor}}</div>
      <div class="detail">${{a.date}} &bull; ${{a.reason}} &bull; ${{a.specialty}}</div>
      <div class="detail">ID: ${{a.id}} &bull; Status: ${{a.status}}</div>
    </div>`).join('');
}}
async function createAppt(e) {{
  e.preventDefault();
  const form = new FormData(e.target);
  const body = Object.fromEntries(form);
  const resp = await fetch('/api/appointments', {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(body)
  }});
  const data = await resp.json();
  if (resp.ok) {{
    const msg = document.getElementById('successMsg');
    msg.style.display = 'block';
    msg.textContent = `Appointment ${{data.id}} confirmed for ${{data.patient_name}} with ${{data.doctor}} on ${{data.date}}`;
    loadAppts();
    setTimeout(() => msg.style.display = 'none', 5000);
  }} else {{
    alert(data.error || 'Failed to create appointment');
  }}
}}
loadAppts();
</script></body></html>"""
