"""AI Chat Router -- domain-aware chat with entity context and RAG.

Capabilities: chat, embeddings, rag, agents, content-safety
Handles any enterprise domain by grounding responses in the app's own data.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from ai.client import CHAT_MODEL, chat_completion, get_ai_client
from core.dependencies import get_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _search_rag_context(query: str, top_k: int = 3) -> str:
    """Retrieve context from Azure AI Search when configured."""
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    if not search_endpoint:
        return ""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.search.documents import SearchClient

        credential = DefaultAzureCredential(
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
        )
        client = SearchClient(
            endpoint=search_endpoint,
            index_name=os.getenv("AZURE_SEARCH_INDEX", "documents"),
            credential=credential,
        )
        results = client.search(search_text=query, top=top_k)
        chunks = [doc.get("content", "") for doc in results if doc.get("content")]
        return "\n\n".join(chunks)
    except Exception as e:
        logger.warning("ai_search.rag_fallback", extra={"error": str(e)})
        return ""


def _build_domain_context() -> str:
    """Build RAG context from the app's own entity repositories."""
    sections: list[str] = []
    try:
        repo = get_repository("incident")
        items = repo.list_all()
        sections.append(f"Incidents ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("asset")
        items = repo.list_all()
        sections.append(f"Assets ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("sensor")
        items = repo.list_all()
        sections.append(f"Sensors ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("service_request")
        items = repo.list_all()
        sections.append(f"ServiceRequests ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("transit_route")
        items = repo.list_all()
        sections.append(f"TransitRoutes ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("vehicle")
        items = repo.list_all()
        sections.append(f"Vehicles ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("zone")
        items = repo.list_all()
        sections.append(f"Zones ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("work_order")
        items = repo.list_all()
        sections.append(f"WorkOrders ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    try:
        repo = get_repository("audit_log")
        items = repo.list_all()
        sections.append(f"AuditLogs ({len(items)} records):")
        for item in items[:5]:
            sections.append(f"  - {item}")
        if len(items) > 5:
            sections.append(f"  ... and {len(items) - 5} more")
    except Exception:
        pass
    return "\n".join(sections) if sections else "No data available yet."


SYSTEM_PROMPT = """You are an AI assistant for smart-city-ai-operations-platform-extre.
Project: smart-city-ai-operations-platform-extre
Description: Build an enterprise-grade AI-powered smart city operations platform that orchestrates **9 distinct domain entities** across every supported data store (Cosmos DB, SQL, Blob Storage, Redis, AI Search, 

You have access to the following domain entities:
  - Incident: title, description, category, severity, status, latitude, longitude, zone_id, reporter_name, reporter_phone, affected_population, estimated_damage, ai_confidence, ai_triage_notes, photo_url, audio_transcript, assigned_units, resolution_notes, response_time_minutes\n  - Asset: name, asset_type, status, location_address, latitude, longitude, zone_id, install_date, expected_lifespan_years, manufacturer, model_number, last_inspection_date, health_score, replacement_cost, maintenance_budget, sensor_ids, ai_failure_prediction, ai_health_trend\n  - Sensor: name, sensor_type, status, latitude, longitude, zone_id, asset_id, vendor, protocol, last_reading_value, last_reading_unit, last_reading_timestamp, threshold_min, threshold_max, alert_enabled, battery_level, firmware_version, calibration_date\n  - ServiceRequest: title, description, category, priority, status, citizen_name, citizen_email, citizen_phone, latitude, longitude, zone_id, assigned_team, estimated_completion_date, ai_duplicate_score, ai_category_confidence, ai_suggested_resolution, photo_url, satisfaction_rating\n  - TransitRoute: name, route_number, route_type, status, start_location, end_location, total_stops, daily_ridership, average_delay_minutes, on_time_percentage, fare_revenue_daily, operating_cost_daily, vehicle_count, zone_ids, ai_demand_forecast, ai_optimization_notes, last_disruption_reason\n  - Vehicle: name, vehicle_type, status, license_plate, vin_number, current_latitude, current_longitude, assigned_department, driver_name, fuel_level_pct, odometer_miles, last_maintenance_date, next_maintenance_due, maintenance_cost_ytd, ai_maintenance_prediction, gps_speed_mph, engine_health_score\n  - Zone: name, zone_code, zone_type, status, population, area_sq_miles, council_district, emergency_contacts, active_incident_count, active_sensor_count, active_asset_count, air_quality_index, noise_level_db, power_load_pct, ai_risk_score, ai_trend_summary\n  - WorkOrder: title, description, work_type, priority, status, asset_id, assigned_team, scheduled_date, estimated_hours, actual_hours, parts_cost, labor_cost, total_cost, ai_generated, ai_justification, completion_notes, quality_rating\n  - AuditLog: event_type, agent_name, user_id, user_role, prompt_text, completion_text, token_count_prompt, token_count_completion, latency_ms, model_name, content_safety_result, content_safety_categories, pii_detected, session_id, correlation_id, ip_address, status

When answering questions:
- Use the provided data context to give accurate, specific answers
- Reference actual records and data when relevant
- Provide actionable insights based on the data
- If asked about data you don't have, say so clearly
- Be concise but thorough
"""


class ChatRequest(BaseModel):
    """Chat request with message and optional history."""

    message: str = Field(..., description="User message", max_length=4000)
    conversation_id: str = Field(default="", description="Conversation ID for history")
    history: list[dict] = Field(default_factory=list, description="Previous messages")


class ChatResponse(BaseModel):
    """Chat response from the AI model."""

    reply: str
    model: str
    provider: str = ""
    usage: dict = Field(default_factory=dict)
    context_used: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI model grounded in domain data."""
    try:
        get_ai_client()  # Validate provider is configured
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Build domain context from repositories
    domain_context = _build_domain_context()
    rag_ext = _search_rag_context(request.message)
    if rag_ext:
        domain_context += "\n\nExternal Knowledge:\n" + rag_ext

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current data context:\n{domain_context}"},
    ]

    # Add conversation history
    for msg in request.history[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    messages.append({"role": "user", "content": request.message})

    result = chat_completion(messages)
    logger.info("ai_chat.complete", extra={"model": result["model"], "tokens": result["usage"].get("total_tokens", 0)})

    return ChatResponse(
        reply=result["reply"],
        model=result["model"],
        provider=result.get("provider", ""),
        usage=result["usage"],
        context_used=bool(domain_context.strip()),
    )


@router.get("/models")
async def list_models():
    """List available AI model deployments and provider status."""
    try:
        _, provider = get_ai_client()
        return {
            "chat_model": CHAT_MODEL,
            "provider": provider,
            "status": "available",
        }
    except RuntimeError:
        return {
            "chat_model": CHAT_MODEL,
            "provider": "none",
            "status": "not_configured",
            "help": "Set AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY",
        }


@router.get("/context")
async def get_context():
    """Preview the domain context used for RAG grounding."""
    context = _build_domain_context()
    return {
        "context": context,
        "entities": ['Incident', 'Asset', 'Sensor', 'ServiceRequest', 'TransitRoute', 'Vehicle', 'Zone', 'WorkOrder', 'AuditLog'],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# -- File types and processing strategies ----------------------------
_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp", "image/bmp", "image/tiff"}
_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/webm", "audio/mp4", "audio/x-m4a"}
_DOC_TYPES = {
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json", "text/plain", "text/csv", "text/html", "text/markdown", "text/xml",
    "application/xml",
}
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _detect_file_category(content_type: str, filename: str) -> str:
    """Classify uploaded file into a processing category."""
    ct = (content_type or "").lower()
    fn = (filename or "").lower()

    if ct in _IMAGE_TYPES or fn.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff")):
        return "image"
    if ct in _AUDIO_TYPES or fn.endswith((".mp3", ".wav", ".ogg", ".webm", ".m4a")):
        return "audio"
    if ct == "application/pdf" or fn.endswith(".pdf"):
        return "document"
    if fn.endswith((".xlsx", ".xls")):
        return "spreadsheet"
    if fn.endswith((".csv",)):
        return "csv"
    if ct in _DOC_TYPES or fn.endswith((".txt", ".md", ".html", ".xml", ".json", ".docx")):
        return "text"
    return "binary"


async def _process_image(file_bytes: bytes, filename: str) -> str:
    """Process image using OpenAI Vision (GPT-4o) or description fallback."""
    try:
        client, provider = get_ai_client()
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a document and image analysis assistant for smart-city-ai-operations-platform-extre. Analyze the image and extract all relevant information including text (OCR), objects, data, receipts, invoices, charts, diagrams, or any structured content. Return a detailed analysis."},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Analyze this file: {filename}"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
                ]}
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content or "Image processed but no content extracted."
    except Exception as e:
        logger.warning("ai_upload.image_fallback", extra={"error": str(e)})
        return f"Image received: {filename} ({len(file_bytes)} bytes). AI vision processing unavailable: {e}. Configure an OpenAI-compatible model with vision support."


async def _process_audio(file_bytes: bytes, filename: str) -> str:
    """Process audio using OpenAI Whisper transcription."""
    try:
        client, _ = get_ai_client()
        import io
        audio_file = io.BytesIO(file_bytes)
        audio_file.name = filename

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        text = transcript.text
        # Summarize the transcript
        summary = chat_completion([
            {"role": "system", "content": "You are an assistant for smart-city-ai-operations-platform-extre. Summarize and extract key information from the following audio transcript."},
            {"role": "user", "content": f"Transcript from {filename}:\n\n{text}"},
        ])
        return f"**Transcript:**\n{text}\n\n**Analysis:**\n{summary['reply']}"
    except Exception as e:
        logger.warning("ai_upload.audio_fallback", extra={"error": str(e)})
        return f"Audio received: {filename} ({len(file_bytes)} bytes). Whisper transcription unavailable: {e}."


async def _process_text_content(content: str, filename: str) -> str:
    """Process text-based files (PDF text, CSV, JSON, etc.) through AI analysis."""
    try:
        # Truncate very large files for the context window
        if len(content) > 15000:
            content = content[:15000] + f"\n\n... (truncated, {len(content)} total characters)"

        result = chat_completion([
            {"role": "system", "content": "You are a document analysis assistant for smart-city-ai-operations-platform-extre. Analyze the uploaded file and extract key information, patterns, summaries, and actionable insights. For receipts/invoices, extract line items, totals, dates. For data files, summarize structure and key findings. For documents, provide a comprehensive summary."},
            {"role": "user", "content": f"Analyze this file ({filename}):\n\n{content}"},
        ])
        return result["reply"]
    except Exception as e:
        return f"File received: {filename} ({len(content)} chars). AI analysis unavailable: {e}"


async def _extract_text(file_bytes: bytes, filename: str, category: str) -> str:
    """Extract readable text from various file formats."""
    fn = filename.lower()

    if category == "csv" or fn.endswith(".csv"):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith(".json"):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith((".txt", ".md", ".html", ".xml")):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith(".pdf"):
        # Try basic PDF text extraction 
        text = file_bytes.decode("latin-1", errors="replace")
        # Extract text between stream markers (basic)
        import re
        streams = re.findall(r'BT\s*(.*?)\s*ET', text, re.DOTALL)
        if streams:
            # Extract text operators
            extracted = []
            for stream in streams:
                texts = re.findall(r'\(([^)]+)\)', stream)
                extracted.extend(texts)
            if extracted:
                return " ".join(extracted)
        return f"[PDF file: {len(file_bytes)} bytes - for full extraction configure Azure Document Intelligence]"
    if fn.endswith(".docx"):
        # Basic docx extraction (XML inside zip)
        try:
            import zipfile, io
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                if "word/document.xml" in z.namelist():
                    xml = z.read("word/document.xml").decode("utf-8")
                    import re
                    texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', xml)
                    return " ".join(texts)
        except Exception:
            pass
        return f"[DOCX file: {len(file_bytes)} bytes]"
    if fn.endswith((".xlsx", ".xls")):
        return f"[Spreadsheet: {len(file_bytes)} bytes - upload as CSV for text analysis]"

    return f"[Binary file: {len(file_bytes)} bytes]"


class UploadResponse(BaseModel):
    """Response after file upload and processing."""
    analysis: str
    filename: str
    file_type: str
    size_bytes: int
    model: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(file: UploadFile = File(...)):
    """Upload and process a file (image, document, audio, receipt, etc.).

    Supports: images (OCR/vision), audio (transcription), PDFs, DOCX,
    CSV, JSON, spreadsheets, receipts, invoices, and text files.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {_MAX_FILE_SIZE // (1024*1024)}MB)")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    category = _detect_file_category(file.content_type or "", file.filename)
    logger.info("ai_upload.processing", extra={
        "filename": file.filename,
        "category": category,
        "size": len(file_bytes),
        "content_type": file.content_type,
    })

    if category == "image":
        analysis = await _process_image(file_bytes, file.filename)
    elif category == "audio":
        analysis = await _process_audio(file_bytes, file.filename)
    else:
        # Text-based processing: extract text then analyze
        text_content = await _extract_text(file_bytes, file.filename, category)
        analysis = await _process_text_content(text_content, file.filename)

    return UploadResponse(
        analysis=analysis,
        filename=file.filename,
        file_type=category,
        size_bytes=len(file_bytes),
        model=CHAT_MODEL,
    )


@router.get("/upload/supported")
async def supported_file_types():
    """List supported file types for upload and processing."""
    return {
        "image": ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"],
        "audio": ["mp3", "wav", "ogg", "webm", "m4a"],
        "document": ["pdf", "docx"],
        "data": ["csv", "json", "xlsx", "xls"],
        "text": ["txt", "md", "html", "xml"],
        "max_size_mb": 20,
        "features": {
            "image": "OCR, receipt/invoice extraction, diagram analysis (via GPT-4o Vision)",
            "audio": "Transcription and summarization (via Whisper)",
            "document": "Text extraction and AI analysis",
            "data": "Structure analysis and insights",
        },
    }
