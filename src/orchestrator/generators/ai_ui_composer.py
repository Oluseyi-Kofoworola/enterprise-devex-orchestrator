"""AI Layout Composer -- intelligent, semantic-driven page composition.

Uses entity role classification, relationship inference, and field analysis
to determine optimal page layouts and widget selections. This replaces
static capability detection with a semantic understanding of the domain model.

Architecture:
    1. Entity Role Classification: primary / supporting / reference / event-log / config
    2. Relationship Inference: FK patterns, parent-child, many-to-many
    3. Page Composition Rules: role-based page template selection
    4. Widget Selection Matrix: (entity_role × field_types) → component type

Falls back to UICapabilityProfile detection when classification is ambiguous.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.orchestrator.intent_schema import EntitySpec, FieldSpec, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────
# Data models
# ────────────────────────────────────────────────────────────────────

class EntityRole:
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    REFERENCE = "reference"
    EVENT_LOG = "event_log"
    CONFIG = "config"


@dataclass
class EntityAnalysis:
    """Semantic analysis of a single entity."""

    name: str
    role: str = EntityRole.PRIMARY
    field_count: int = 0
    numeric_fields: list[str] = field(default_factory=list)
    status_fields: list[str] = field(default_factory=list)
    temporal_fields: list[str] = field(default_factory=list)
    geo_fields: list[str] = field(default_factory=list)
    text_fields: list[str] = field(default_factory=list)
    fk_fields: list[str] = field(default_factory=list)
    has_priority: bool = False
    has_assignee: bool = False
    importance_score: float = 0.0


@dataclass
class Relationship:
    """Inferred relationship between two entities."""

    source: str
    target: str
    rel_type: str  # "belongs_to", "has_many", "references"
    fk_field: str


@dataclass
class WidgetSpec:
    """Specification for a UI widget to place on a page."""

    widget_type: str  # chart_bar, chart_line, gauge, heatmap, table, kanban, map, timeline, radar, treemap, feed
    title: str
    entity: str
    data_fields: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    grid_col_span: int = 1  # 1-3 grid columns
    grid_row_span: int = 1


@dataclass
class PageLayout:
    """Layout plan for a single page."""

    page_id: str
    title: str
    route: str
    page_type: str  # dashboard, detail, kanban, analytics, realtime, map, timeline, builder
    primary_entity: str
    widgets: list[WidgetSpec] = field(default_factory=list)
    description: str = ""


@dataclass
class LayoutPlan:
    """Complete layout plan for the application."""

    pages: list[PageLayout] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    entity_analyses: list[EntityAnalysis] = field(default_factory=list)
    nav_items: list[dict[str, str]] = field(default_factory=list)


# ────────────────────────────────────────────────────────────────────
# Signal dictionaries for entity role classification
# ────────────────────────────────────────────────────────────────────

_EVENT_LOG_SIGNALS = {
    "names": {"event", "log", "audit", "alert", "notification", "activity",
              "history", "incident", "trace", "metric", "reading"},
    "fields": {"event_type", "severity", "level", "logged_at", "occurred_at",
               "message", "source", "trace_id"},
}

_REFERENCE_SIGNALS = {
    "names": {"category", "type", "tag", "label", "role", "permission",
              "setting", "region", "zone", "department", "team"},
    "fields": {"code", "abbreviation", "display_name"},
}

_CONFIG_SIGNALS = {
    "names": {"config", "configuration", "setting", "preference", "parameter",
              "feature_flag", "policy", "rule"},
    "fields": {"key", "value", "config_key", "config_value", "is_enabled"},
}

_SUPPORTING_FIELD_PATTERNS = {
    "fk_suffixes": {"_id", "_ref", "_key", "_code"},
}

_GEO_FIELDS = {"latitude", "longitude", "lat", "lng", "location", "coordinates",
               "geo_point", "address", "city", "region", "zip_code", "postal_code"}

_TEMPORAL_FIELDS = {"created_at", "updated_at", "timestamp", "event_date",
                    "occurred_at", "logged_at", "start_date", "end_date",
                    "due_date", "completed_at", "scheduled_at"}

_STATUS_FIELDS = {"status", "state", "stage", "phase", "condition"}

_PRIORITY_FIELDS = {"priority", "severity", "urgency", "importance", "level"}

_ASSIGNEE_FIELDS = {"assigned_to", "assignee", "owner", "responsible", "handler"}


# ────────────────────────────────────────────────────────────────────
# Widget selection matrix
# ────────────────────────────────────────────────────────────────────

# Maps (entity_role, dominant_field_type) -> list of widget types
_WIDGET_MATRIX: dict[tuple[str, str], list[str]] = {
    # Primary entities get full dashboards
    (EntityRole.PRIMARY, "numeric"): ["chart_bar", "gauge", "sparkline_grid"],
    (EntityRole.PRIMARY, "status"): ["kanban", "chart_pie"],
    (EntityRole.PRIMARY, "temporal"): ["chart_line", "timeline"],
    (EntityRole.PRIMARY, "geo"): ["geo_map"],
    (EntityRole.PRIMARY, "text"): ["table", "feed"],

    # Event logs get timelines and feeds
    (EntityRole.EVENT_LOG, "temporal"): ["timeline", "feed", "chart_line"],
    (EntityRole.EVENT_LOG, "numeric"): ["chart_line", "heatmap"],
    (EntityRole.EVENT_LOG, "status"): ["feed", "chart_bar"],

    # Supporting entities get comparison widgets
    (EntityRole.SUPPORTING, "numeric"): ["chart_bar", "radar"],
    (EntityRole.SUPPORTING, "status"): ["chart_pie", "table"],

    # Reference entities are mostly dropdowns/tables, not full pages
    (EntityRole.REFERENCE, "text"): ["table"],
}


# ────────────────────────────────────────────────────────────────────
# Main composer
# ────────────────────────────────────────────────────────────────────

class AILayoutComposer:
    """Performs semantic analysis and produces intelligent page layouts."""

    def compose(self, spec: IntentSpec) -> LayoutPlan:
        """Analyze entities and produce a complete layout plan."""
        entities = spec.entities or []
        if not entities:
            return LayoutPlan()

        # Step 1: Analyze each entity
        analyses = [self._analyze_entity(e) for e in entities]

        # Step 2: Score and rank
        analyses.sort(key=lambda a: a.importance_score, reverse=True)
        self._assign_roles(analyses)

        # Step 3: Infer relationships
        relationships = self._infer_relationships(entities)

        # Step 4: Compose pages
        pages = self._compose_pages(analyses, relationships, spec)

        # Step 5: Build nav
        nav_items = [
            {"label": p.title, "route": p.route, "icon": self._page_icon(p.page_type)}
            for p in pages
        ]

        return LayoutPlan(
            pages=pages,
            relationships=relationships,
            entity_analyses=analyses,
            nav_items=nav_items,
        )

    # ── Entity analysis ──────────────────────────────────────────

    def _analyze_entity(self, entity: EntitySpec) -> EntityAnalysis:
        """Perform deep field analysis on a single entity."""
        analysis = EntityAnalysis(
            name=entity.name,
            field_count=len(entity.fields),
        )
        ename_lower = entity.name.lower().replace(" ", "_")

        for f in entity.fields:
            fn = f.name.lower()

            # Classify fields
            if f.type in ("int", "float"):
                analysis.numeric_fields.append(f.name)
            if fn in _STATUS_FIELDS or any(fn.endswith(s) for s in ("_status", "_state")):
                analysis.status_fields.append(f.name)
            if fn in _TEMPORAL_FIELDS:
                analysis.temporal_fields.append(f.name)
            if fn in _GEO_FIELDS:
                analysis.geo_fields.append(f.name)
            if f.type == "str" and fn not in _STATUS_FIELDS and fn not in _GEO_FIELDS:
                analysis.text_fields.append(f.name)
            if any(fn.endswith(suffix) for suffix in _SUPPORTING_FIELD_PATTERNS["fk_suffixes"]):
                analysis.fk_fields.append(f.name)
            if fn in _PRIORITY_FIELDS:
                analysis.has_priority = True
            if fn in _ASSIGNEE_FIELDS:
                analysis.has_assignee = True

        # Calculate importance score
        score = 0.0
        score += len(entity.fields) * 1.0  # More fields = more important
        score += len(analysis.numeric_fields) * 2.0  # Numeric = dashboardable
        score += len(analysis.status_fields) * 3.0  # Status = workflow entity
        score += (5.0 if analysis.has_priority else 0)
        score += (5.0 if analysis.has_assignee else 0)
        score -= len(analysis.fk_fields) * 1.5  # Many FKs = supporting
        # Event log entities are important but secondary
        if ename_lower in _EVENT_LOG_SIGNALS["names"]:
            score += 2.0
        # Reference/config entities are low importance
        if ename_lower in _REFERENCE_SIGNALS["names"] or ename_lower in _CONFIG_SIGNALS["names"]:
            score -= 5.0

        analysis.importance_score = score
        return analysis

    def _assign_roles(self, analyses: list[EntityAnalysis]) -> None:
        """Assign roles based on scores and signal matching."""
        for analysis in analyses:
            ename = analysis.name.lower().replace(" ", "_")

            # Exact name matches take priority
            if ename in _EVENT_LOG_SIGNALS["names"]:
                analysis.role = EntityRole.EVENT_LOG
                continue
            if ename in _REFERENCE_SIGNALS["names"]:
                analysis.role = EntityRole.REFERENCE
                continue
            if ename in _CONFIG_SIGNALS["names"]:
                analysis.role = EntityRole.CONFIG
                continue

            # Field-based signal matching
            field_names = {f.lower() for f in analysis.text_fields + analysis.numeric_fields + analysis.status_fields}
            event_signal = len(field_names & _EVENT_LOG_SIGNALS["fields"])
            config_signal = len(field_names & _CONFIG_SIGNALS["fields"])

            if event_signal >= 3:
                analysis.role = EntityRole.EVENT_LOG
            elif config_signal >= 2:
                analysis.role = EntityRole.CONFIG
            elif len(analysis.fk_fields) > len(analysis.numeric_fields):
                analysis.role = EntityRole.SUPPORTING
            elif analysis.importance_score >= 10:
                analysis.role = EntityRole.PRIMARY
            else:
                analysis.role = EntityRole.SUPPORTING

        # Ensure at least one primary
        primaries = [a for a in analyses if a.role == EntityRole.PRIMARY]
        if not primaries and analyses:
            analyses[0].role = EntityRole.PRIMARY

    # ── Relationship inference ───────────────────────────────────

    def _infer_relationships(self, entities: list[EntitySpec]) -> list[Relationship]:
        """Detect FK patterns and parent-child relationships."""
        relationships: list[Relationship] = []
        entity_names = {e.name.lower().replace(" ", "_") for e in entities}

        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            for f in entity.fields:
                fn = f.name.lower()
                # Pattern: field_name ends with _id and matches another entity
                if fn.endswith("_id"):
                    ref_name = fn[:-3]  # strip _id
                    if ref_name in entity_names and ref_name != sn:
                        relationships.append(Relationship(
                            source=sn,
                            target=ref_name,
                            rel_type="belongs_to",
                            fk_field=f.name,
                        ))
                # Pattern: field named "assigned_to", "owner", etc references a person entity
                if fn in _ASSIGNEE_FIELDS:
                    for target in entity_names:
                        if target in ("user", "employee", "agent", "operator", "staff"):
                            relationships.append(Relationship(
                                source=sn,
                                target=target,
                                rel_type="references",
                                fk_field=f.name,
                            ))
                            break

        return relationships

    # ── Page composition ─────────────────────────────────────────

    def _compose_pages(
        self,
        analyses: list[EntityAnalysis],
        relationships: list[Relationship],
        spec: IntentSpec,
    ) -> list[PageLayout]:
        """Compose pages based on entity roles and field types."""
        pages: list[PageLayout] = []

        # 1. Overview dashboard (always)
        pages.append(self._overview_dashboard(analyses, spec))

        # 2. Per-primary-entity pages
        for analysis in analyses:
            if analysis.role == EntityRole.PRIMARY:
                pages.extend(self._primary_entity_pages(analysis))
            elif analysis.role == EntityRole.EVENT_LOG:
                pages.append(self._event_log_page(analysis))

        # 3. Real-time page (if any entity has temporal/sensor data)
        has_realtime = any(
            a.temporal_fields or a.name.lower() in {"sensor", "device", "telemetry", "monitor"}
            for a in analyses
        )
        if has_realtime:
            pages.append(self._realtime_page(analyses))

        # 4. Analytics deep-dive
        numeric_entities = [a for a in analyses if a.numeric_fields]
        if len(numeric_entities) >= 2:
            pages.append(self._analytics_page(numeric_entities))

        # 5. Geo page
        geo_entities = [a for a in analyses if a.geo_fields]
        if geo_entities:
            pages.append(self._geo_page(geo_entities))

        # 6. Conversational builder (always for 3+ entities)
        if len(analyses) >= 3:
            pages.append(PageLayout(
                page_id="builder",
                title="Dynamic Builder",
                route="/builder",
                page_type="builder",
                primary_entity=analyses[0].name,
                description="Natural language query interface for dynamic data exploration",
            ))

        return pages

    def _overview_dashboard(self, analyses: list[EntityAnalysis], spec: IntentSpec) -> PageLayout:
        """Compose the main overview dashboard."""
        widgets: list[WidgetSpec] = []

        # KPI gauges for primary entities
        for a in analyses[:4]:  # top 4 entities
            if a.numeric_fields:
                widgets.append(WidgetSpec(
                    widget_type="gauge",
                    title=f"{a.name} Overview",
                    entity=a.name,
                    data_fields=a.numeric_fields[:2],
                    grid_col_span=1,
                ))

        # Status breakdown for entities with status fields
        for a in analyses:
            if a.status_fields:
                widgets.append(WidgetSpec(
                    widget_type="chart_pie",
                    title=f"{a.name} by Status",
                    entity=a.name,
                    data_fields=a.status_fields[:1],
                ))

        # Trend chart for the most important numeric entity
        if analyses and analyses[0].numeric_fields:
            widgets.append(WidgetSpec(
                widget_type="chart_line",
                title=f"{analyses[0].name} Trends",
                entity=analyses[0].name,
                data_fields=analyses[0].numeric_fields[:3],
                grid_col_span=2,
            ))

        # Cross-entity comparison
        if len(analyses) >= 2:
            widgets.append(WidgetSpec(
                widget_type="radar",
                title="Entity Health Comparison",
                entity="__cross_entity__",
                data_fields=[a.name for a in analyses[:5]],
                grid_col_span=2,
            ))

        return PageLayout(
            page_id="overview",
            title="Dashboard",
            route="/",
            page_type="dashboard",
            primary_entity=analyses[0].name if analyses else "",
            widgets=widgets,
            description="Executive overview with KPIs, trends, and cross-entity metrics",
        )

    def _primary_entity_pages(self, analysis: EntityAnalysis) -> list[PageLayout]:
        """Generate pages for a primary entity."""
        pages: list[PageLayout] = []
        sn = analysis.name.lower().replace(" ", "_")

        # Kanban page (if has status + priority/assignee)
        if analysis.status_fields and (analysis.has_priority or analysis.has_assignee):
            widgets = [WidgetSpec(
                widget_type="kanban",
                title=f"{analysis.name} Board",
                entity=analysis.name,
                data_fields=analysis.status_fields + (
                    ["priority"] if analysis.has_priority else []
                ),
                grid_col_span=3,
                grid_row_span=2,
            )]
            pages.append(PageLayout(
                page_id=f"{sn}-kanban",
                title=f"{analysis.name} Board",
                route=f"/{sn}/board",
                page_type="kanban",
                primary_entity=analysis.name,
                widgets=widgets,
            ))

        # Analytics page (if has numeric fields)
        if len(analysis.numeric_fields) >= 2:
            widgets = []
            widgets.append(WidgetSpec(
                widget_type="chart_bar",
                title=f"{analysis.name} Distribution",
                entity=analysis.name,
                data_fields=analysis.numeric_fields[:3],
                grid_col_span=2,
            ))
            widgets.append(WidgetSpec(
                widget_type="sparkline_grid",
                title=f"{analysis.name} Metrics",
                entity=analysis.name,
                data_fields=analysis.numeric_fields,
                grid_col_span=1,
            ))
            if analysis.temporal_fields:
                widgets.append(WidgetSpec(
                    widget_type="heatmap",
                    title=f"{analysis.name} Activity Heatmap",
                    entity=analysis.name,
                    data_fields=analysis.temporal_fields[:1] + analysis.numeric_fields[:1],
                    grid_col_span=2,
                ))
            pages.append(PageLayout(
                page_id=f"{sn}-analytics",
                title=f"{analysis.name} Analytics",
                route=f"/{sn}/analytics",
                page_type="analytics",
                primary_entity=analysis.name,
                widgets=widgets,
            ))

        return pages

    def _event_log_page(self, analysis: EntityAnalysis) -> PageLayout:
        """Generate timeline/feed page for event-log entities."""
        sn = analysis.name.lower().replace(" ", "_")
        widgets = [
            WidgetSpec(
                widget_type="timeline",
                title=f"{analysis.name} Timeline",
                entity=analysis.name,
                data_fields=analysis.temporal_fields + analysis.text_fields[:2],
                grid_col_span=2,
                grid_row_span=2,
            ),
            WidgetSpec(
                widget_type="feed",
                title=f"Latest {analysis.name}",
                entity=analysis.name,
                data_fields=analysis.text_fields[:3],
                grid_col_span=1,
            ),
        ]
        if analysis.numeric_fields:
            widgets.append(WidgetSpec(
                widget_type="chart_line",
                title=f"{analysis.name} Volume",
                entity=analysis.name,
                data_fields=analysis.numeric_fields[:2],
                grid_col_span=3,
            ))

        return PageLayout(
            page_id=f"{sn}-timeline",
            title=f"{analysis.name} Feed",
            route=f"/{sn}/feed",
            page_type="timeline",
            primary_entity=analysis.name,
            widgets=widgets,
        )

    def _realtime_page(self, analyses: list[EntityAnalysis]) -> PageLayout:
        """Generate real-time monitoring page."""
        widgets: list[WidgetSpec] = []

        # Live feed
        widgets.append(WidgetSpec(
            widget_type="feed",
            title="Live Event Stream",
            entity="__realtime__",
            config={"source": "sse", "endpoint": "/api/v1/stream"},
            grid_col_span=1,
            grid_row_span=2,
        ))

        # Gauges for entities with numeric data
        for a in analyses[:3]:
            if a.numeric_fields:
                widgets.append(WidgetSpec(
                    widget_type="gauge",
                    title=f"{a.name} Live",
                    entity=a.name,
                    data_fields=a.numeric_fields[:1],
                ))

        # Sparkline grid
        numeric = [a for a in analyses if a.numeric_fields]
        if numeric:
            widgets.append(WidgetSpec(
                widget_type="sparkline_grid",
                title="Real-Time Metrics",
                entity="__cross_entity__",
                data_fields=[f"{a.name}.{a.numeric_fields[0]}" for a in numeric[:6]],
                grid_col_span=2,
            ))

        return PageLayout(
            page_id="realtime",
            title="Real-Time Monitor",
            route="/realtime",
            page_type="realtime",
            primary_entity=analyses[0].name,
            widgets=widgets,
            description="Live data stream with real-time gauges and metrics",
        )

    def _analytics_page(self, numeric_entities: list[EntityAnalysis]) -> PageLayout:
        """Generate advanced analytics deep-dive page."""
        widgets: list[WidgetSpec] = []

        # Treemap for category breakdown
        widgets.append(WidgetSpec(
            widget_type="treemap",
            title="Entity Size Comparison",
            entity="__cross_entity__",
            data_fields=[a.name for a in numeric_entities],
            grid_col_span=2,
        ))

        # Radar for multi-dimensional comparison
        widgets.append(WidgetSpec(
            widget_type="radar",
            title="Multi-Metric Comparison",
            entity="__cross_entity__",
            data_fields=[f"{a.name}.{a.numeric_fields[0]}" for a in numeric_entities[:5]],
            grid_col_span=1,
        ))

        # Heatmap
        if len(numeric_entities) >= 2:
            widgets.append(WidgetSpec(
                widget_type="heatmap",
                title="Cross-Entity Correlation",
                entity="__cross_entity__",
                data_fields=[f"{a.name}.{nf}" for a in numeric_entities[:3] for nf in a.numeric_fields[:2]],
                grid_col_span=3,
            ))

        return PageLayout(
            page_id="analytics-advanced",
            title="Advanced Analytics",
            route="/analytics/advanced",
            page_type="analytics",
            primary_entity=numeric_entities[0].name,
            widgets=widgets,
            description="Deep-dive analytics with treemaps, radar charts, and correlations",
        )

    def _geo_page(self, geo_entities: list[EntityAnalysis]) -> PageLayout:
        """Generate geographic visualization page."""
        widgets = [
            WidgetSpec(
                widget_type="geo_map",
                title=f"{e.name} Locations",
                entity=e.name,
                data_fields=e.geo_fields[:2],
                grid_col_span=3,
                grid_row_span=2,
            )
            for e in geo_entities[:2]
        ]

        return PageLayout(
            page_id="geo",
            title="Geographic View",
            route="/geo",
            page_type="map",
            primary_entity=geo_entities[0].name,
            widgets=widgets,
            description="Geographic data visualization with entity locations",
        )

    def _page_icon(self, page_type: str) -> str:
        """Return icon name for a page type."""
        icons = {
            "dashboard": "LayoutDashboard",
            "kanban": "Columns",
            "analytics": "BarChart3",
            "timeline": "Clock",
            "realtime": "Activity",
            "map": "MapPin",
            "builder": "Wand2",
            "detail": "FileText",
        }
        return icons.get(page_type, "Circle")
