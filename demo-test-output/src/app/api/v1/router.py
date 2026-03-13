"""API v1 router -- Healthcare Voice Agent endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from api.v1.schemas import (
    SessionCreate, SessionResponse, AppointmentCreate, AppointmentResponse,
    RefillCreate, RefillResponse, ItemCreate, ItemResponse,
)
from core.dependencies import get_settings, get_repository
from core.config import Settings
from core.services import SessionService, AppointmentService, PrescriptionService, ItemService

router = APIRouter()


# --- Items (backward-compatible) ---
@router.get("/items", response_model=list[ItemResponse], summary="List items")
async def list_items(settings: Settings = Depends(get_settings)):
    svc = ItemService(project_name=settings.app_name)
    return svc.list_items()


@router.post("/items", response_model=ItemResponse, status_code=201, summary="Create item")
async def create_item(payload: ItemCreate, settings: Settings = Depends(get_settings)):
    svc = ItemService(project_name=settings.app_name)
    return svc.create_item(payload.name, payload.description)


# --- Sessions ---
@router.get("/sessions", summary="List sessions")
async def list_sessions(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("session", settings.storage_mode)
    svc = SessionService(repo)
    return svc.list_sessions(status)


@router.post("/sessions", response_model=SessionResponse, status_code=201, summary="Create session")
async def create_session(payload: SessionCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("session", settings.storage_mode)
    svc = SessionService(repo)
    return svc.create_session(payload.patient_id, payload.intent)


@router.get("/sessions/{session_id}", summary="Get session")
async def get_session(session_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("session", settings.storage_mode)
    svc = SessionService(repo)
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/end", summary="End session")
async def end_session(session_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("session", settings.storage_mode)
    svc = SessionService(repo)
    session = svc.end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/escalate", summary="Escalate session")
async def escalate_session(session_id: str, reason: str = "", settings: Settings = Depends(get_settings)):
    repo = get_repository("session", settings.storage_mode)
    svc = SessionService(repo)
    try:
        session = svc.escalate_session(session_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# --- Appointments ---
@router.get("/appointments", summary="List appointments")
async def list_appointments(patient_id: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("appointment", settings.storage_mode)
    svc = AppointmentService(repo)
    return svc.list_appointments(patient_id)


@router.post("/appointments", response_model=AppointmentResponse, status_code=201, summary="Book appointment")
async def book_appointment(payload: AppointmentCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("appointment", settings.storage_mode)
    svc = AppointmentService(repo)
    return svc.book_appointment(payload.patient_id, payload.provider, payload.date_time, payload.reason)


# --- Prescription Refills ---
@router.get("/prescriptions/refills", summary="List refills")
async def list_refills(patient_id: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("prescription", settings.storage_mode)
    svc = PrescriptionService(repo)
    return svc.list_refills(patient_id)


@router.post("/prescriptions/refills", response_model=RefillResponse, status_code=201, summary="Request refill")
async def request_refill(payload: RefillCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("prescription", settings.storage_mode)
    svc = PrescriptionService(repo)
    return svc.request_refill(payload.patient_id, payload.medication, payload.pharmacy)
