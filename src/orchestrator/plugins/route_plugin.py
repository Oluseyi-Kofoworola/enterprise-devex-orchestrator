"""Route Plugins -- custom FastAPI route patterns.

Each plugin generates Python source for additional API route modules
(health checks, webhooks, bulk operations, etc.).
"""

from __future__ import annotations

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class HealthRoutePlugin:
    """Generates an enhanced health-check router with dependency probing."""

    def applies_to(self, spec: IntentSpec) -> bool:
        return spec.observability.health_endpoint

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        store_values = {s.value if hasattr(s, "value") else s for s in (spec.data_stores or [])}
        checks: list[str] = []
        if any("cosmos" in s for s in store_values):
            checks.append('        "cosmos": await _probe("cosmos"),')
        if any("sql" in s for s in store_values):
            checks.append('        "sql": await _probe("sql"),')
        if any("redis" in s for s in store_values):
            checks.append('        "redis": await _probe("redis"),')
        if any("blob" in s for s in store_values):
            checks.append('        "blob": await _probe("blob"),')

        dep_lines = "\n".join(checks) if checks else '        "core": "ok",'
        return {
            f"src/routes/health.py": f"""\
\"\"\"Enhanced health-check router with dependency probes.\"\"\"

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])

_START = time.monotonic()


async def _probe(name: str) -> str:
    \"\"\"Placeholder dependency probe -- replace with real checks.\"\"\"
    return "ok"


@router.get("/health")
async def health():
    \"\"\"Basic liveness probe.\"\"\"
    return {{"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}}


@router.get("/health/ready")
async def readiness():
    \"\"\"Readiness probe with dependency checks.\"\"\"
    deps = {{
{dep_lines}
    }}
    all_ok = all(v == "ok" for v in deps.values())
    return {{
        "status": "ready" if all_ok else "degraded",
        "uptime_seconds": round(time.monotonic() - _START, 2),
        "dependencies": deps,
    }}
""",
        }


class WebhookRoutePlugin:
    """Generates a webhook receiver router with signature validation."""

    def applies_to(self, spec: IntentSpec) -> bool:
        keywords = {"webhook", "event-driven", "callback", "notification"}
        return any(kw in spec.raw_intent.lower() for kw in keywords)

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        return {
            f"src/routes/webhooks.py": """\
\"\"\"Webhook receiver with HMAC signature validation.\"\"\"

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_SECRET = os.environ.get("WEBHOOK_SECRET", "")


def _verify_signature(payload: bytes, signature: str) -> bool:
    \"\"\"Verify HMAC-SHA256 webhook signature.\"\"\"
    if not _SECRET:
        return True  # skip verification in dev when no secret is set
    expected = hmac.new(
        _SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@router.post("/ingest")
async def ingest_webhook(
    request: Request,
    x_hub_signature_256: str = Header(default=""),
) -> dict[str, Any]:
    \"\"\"Receive and validate an incoming webhook event.\"\"\"
    body = await request.body()
    if not _verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")
    # Process payload -- extend with actual handler logic
    return {"accepted": True}
""",
        }


class BulkOperationRoutePlugin:
    """Generates a bulk-operation router for batch create/update/delete."""

    def applies_to(self, spec: IntentSpec) -> bool:
        keywords = {"bulk", "batch", "import", "mass", "csv"}
        return (
            any(kw in spec.raw_intent.lower() for kw in keywords)
            or len(spec.entities) >= 3
        )

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        entity_names = [e.name for e in spec.entities[:5]]
        entities_str = ", ".join(f'"{e}"' for e in entity_names)
        return {
            f"src/routes/bulk.py": f"""\
\"\"\"Bulk operations router for batch create/update/delete.\"\"\"

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/bulk", tags=["bulk"])

SUPPORTED_ENTITIES = [{entities_str}]


@router.post("/{{entity_type}}")
async def bulk_create(entity_type: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    \"\"\"Create multiple records in a single request.\"\"\"
    if entity_type not in SUPPORTED_ENTITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {{entity_type}}")
    if len(items) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 items per batch")
    # Placeholder -- implement actual storage logic
    return {{"entity": entity_type, "created": len(items)}}


@router.delete("/{{entity_type}}")
async def bulk_delete(entity_type: str, ids: list[str]) -> dict[str, Any]:
    \"\"\"Delete multiple records by ID.\"\"\"
    if entity_type not in SUPPORTED_ENTITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {{entity_type}}")
    if len(ids) > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 deletes per batch")
    return {{"entity": entity_type, "deleted": len(ids)}}
""",
        }
