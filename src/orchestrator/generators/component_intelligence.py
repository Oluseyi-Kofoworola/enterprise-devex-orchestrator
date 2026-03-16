"""Component Intelligence -- detects specialized UI capabilities from entity fields.

Analyzes IntentSpec entities to determine what domain-specific UI components
should be generated beyond the standard CRUD dashboard. Field name patterns,
entity names, and endpoint patterns are scored against capability profiles
to detect features like file upload, document processing, batch workflows,
review queues, financial dashboards, sensor monitoring, etc.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DetectedCapabilities:
    """Capabilities detected from entity field analysis."""

    has_file_upload: bool = False
    has_document_processing: bool = False
    has_extraction_results: bool = False
    has_batch_processing: bool = False
    has_review_workflow: bool = False
    has_confidence_metrics: bool = False
    has_geolocation: bool = False
    has_financial_data: bool = False
    has_timeline_events: bool = False
    has_sensor_data: bool = False
    has_inventory_tracking: bool = False

    # Entity references for component generation
    upload_entity: str = ""
    upload_entity_slug: str = ""
    extraction_entity: str = ""
    extraction_entity_slug: str = ""
    batch_entity: str = ""
    batch_entity_slug: str = ""
    review_entity: str = ""
    review_entity_slug: str = ""

    @property
    def has_specialized_ui(self) -> bool:
        return any([
            self.has_file_upload,
            self.has_document_processing,
            self.has_batch_processing,
            self.has_review_workflow,
            self.has_sensor_data,
            self.has_financial_data,
        ])

    @property
    def specialized_pages(self) -> list[str]:
        """Return list of specialized page names to generate."""
        pages: list[str] = []
        if self.has_file_upload or self.has_document_processing:
            pages.append("upload")
        if self.has_batch_processing:
            pages.append("processing")
        if self.has_review_workflow:
            pages.append("reviews")
        if self.has_confidence_metrics or self.has_extraction_results:
            pages.append("analytics")
        return pages


# Field patterns that signal capabilities
_CAPABILITY_PATTERNS: dict[str, dict] = {
    "file_upload": {
        "fields": {
            "filename", "file_type", "file_size", "file_size_bytes",
            "upload_date", "uploaded_by", "blob_url", "file_url",
            "mime_type", "file_path", "content_type",
        },
        "entity_names": {
            "document", "file", "upload", "attachment", "media", "asset",
        },
        "threshold": 3,
    },
    "document_processing": {
        "fields": {
            "model_type", "page_count", "extracted_text", "content",
            "ocr_result", "processing_status", "model_used",
            "category", "confidence_score",
        },
        "entity_names": {
            "document", "extraction", "analysis", "processing",
        },
        "threshold": 2,
    },
    "extraction_results": {
        "fields": {
            "extracted_text", "key_value_pairs", "tables_json",
            "field_count", "table_count", "page_results",
            "confidence_avg", "confidence_min", "model_used",
            "error_message",
        },
        "entity_names": {
            "extraction", "result", "analysis", "output",
        },
        "threshold": 3,
    },
    "batch_processing": {
        "fields": {
            "total_documents", "processed_count", "failed_count",
            "progress_pct", "batch_size", "queue_depth",
            "started_at", "completed_at", "error_summary",
        },
        "entity_names": {
            "batch", "job", "queue", "pipeline", "task",
        },
        "threshold": 3,
    },
    "review_workflow": {
        "fields": {
            "assigned_to", "review_notes", "corrections_json",
            "approved_by", "rejected_by", "review_duration_mins",
            "confidence_flag", "reviewer_id",
        },
        "entity_names": {
            "review", "approval", "verification",
        },
        "threshold": 2,
    },
    "confidence_metrics": {
        "fields": {
            "confidence_score", "confidence_avg", "confidence_min",
            "accuracy_rate", "avg_accuracy", "precision", "recall",
            "f1_score", "processing_time_ms",
        },
        "entity_names": {
            "metric", "analytics", "score", "evaluation", "model",
        },
        "threshold": 2,
    },
    "geolocation": {
        "fields": {
            "latitude", "longitude", "location", "address", "zone",
            "coordinates", "geo_point",
        },
        "entity_names": {
            "location", "site", "zone", "area",
        },
        "threshold": 2,
    },
    "financial_data": {
        "fields": {
            "amount", "total", "balance", "revenue", "cost", "price",
            "budget", "invoice_total", "payment", "transaction_amount",
            "unit_price", "discount",
        },
        "entity_names": {
            "transaction", "payment", "invoice", "account", "ledger",
            "portfolio", "order",
        },
        "threshold": 2,
    },
    "sensor_data": {
        "fields": {
            "reading", "temperature", "humidity", "pressure", "voltage",
            "current", "sensor_id", "device_id", "measurement",
            "threshold_value", "telemetry",
        },
        "entity_names": {
            "sensor", "device", "reading", "measurement", "telemetry",
        },
        "threshold": 2,
    },
    "inventory_tracking": {
        "fields": {
            "quantity", "stock_level", "reorder_point", "sku",
            "warehouse", "lot_number", "shelf_location",
            "units_available", "units_reserved",
        },
        "entity_names": {
            "inventory", "product", "stock", "warehouse", "item",
        },
        "threshold": 2,
    },
}


def _snake(name: str) -> str:
    import re
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def _plural(name: str) -> str:
    lower = name.lower()
    _IRREGULARS = {
        "analysis": "analyses", "diagnosis": "diagnoses", "basis": "bases",
        "crisis": "crises", "thesis": "theses", "hypothesis": "hypotheses",
        "synopsis": "synopses", "parenthesis": "parentheses",
        "person": "people", "child": "children", "man": "men", "woman": "women",
        "staff": "staff", "sheep": "sheep", "fish": "fish", "deer": "deer",
    }
    if lower in _IRREGULARS:
        plural = _IRREGULARS[lower]
        if name[0].isupper():
            return plural[0].upper() + plural[1:]
        return plural
    # Handle compound names ending with an irregular word (e.g. CostAnalysis)
    for irr_singular, irr_plural in _IRREGULARS.items():
        if lower.endswith(irr_singular) and lower != irr_singular:
            prefix = name[: len(name) - len(irr_singular)]
            return prefix + (irr_plural[0].upper() + irr_plural[1:] if name[-len(irr_singular)].isupper() else irr_plural)
    if lower.endswith("y") and lower[-2:] not in ("ay", "ey", "oy", "uy"):
        return name[:-1] + "ies"
    if lower.endswith(("s", "sh", "ch", "x", "z")):
        return name + "es"
    return name + "s"


class ComponentIntelligence:
    """Analyzes entity fields to detect specialized UI capabilities."""

    def detect(self, spec: IntentSpec) -> DetectedCapabilities:
        caps = DetectedCapabilities()

        for cap_name, patterns in _CAPABILITY_PATTERNS.items():
            for entity in spec.entities:
                entity_lower = entity.name.lower()
                field_names = {f.name.lower() for f in entity.fields}

                # Field name matches
                field_matches = len(field_names & patterns["fields"])
                # Entity name keyword match
                entity_match = any(
                    kw in entity_lower
                    for kw in patterns["entity_names"]
                )

                score = field_matches + (2 if entity_match else 0)

                if score >= patterns["threshold"]:
                    setattr(caps, f"has_{cap_name}", True)
                    slug = _snake(_plural(entity.name))
                    if cap_name == "file_upload" and not caps.upload_entity:
                        caps.upload_entity = entity.name
                        caps.upload_entity_slug = slug
                    elif cap_name == "extraction_results" and not caps.extraction_entity:
                        caps.extraction_entity = entity.name
                        caps.extraction_entity_slug = slug
                    elif cap_name == "batch_processing" and not caps.batch_entity:
                        caps.batch_entity = entity.name
                        caps.batch_entity_slug = slug
                    elif cap_name == "review_workflow" and not caps.review_entity:
                        caps.review_entity = entity.name
                        caps.review_entity_slug = slug

        detected = [
            k for k in vars(caps)
            if k.startswith("has_") and getattr(caps, k) is True
        ]
        if detected:
            logger.info(
                "Component intelligence detected: %s",
                ", ".join(detected),
            )

        return caps
