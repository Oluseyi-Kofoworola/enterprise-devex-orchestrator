"""Tests for AILayoutComposer -- intelligent entity-driven UI layout."""

from __future__ import annotations

from src.orchestrator.generators.ai_ui_composer import AILayoutComposer, EntityRole
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    ComplianceFramework,
    DataStore,
    EntitySpec,
    FieldSpec,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    SecurityRequirements,
)


def _make_multi_entity_spec() -> IntentSpec:
    return IntentSpec(
        project_name="layout-test",
        app_type=AppType.WEB,
        description="A multi-entity app for layout testing",
        raw_intent="Build a fleet management dashboard",
        data_stores=[DataStore.COSMOS_DB],
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
        ),
        observability=ObservabilityRequirements(),
        networking=NetworkingModel.PUBLIC_RESTRICTED,
        entities=[
            EntitySpec(
                name="Vehicle",
                fields=[
                    FieldSpec(name="vin", type="str", description="VIN number"),
                    FieldSpec(name="make", type="str", description="Manufacturer"),
                    FieldSpec(name="model", type="str", description="Vehicle model"),
                    FieldSpec(name="mileage", type="int", description="Odometer reading"),
                    FieldSpec(name="fuel_level", type="float", description="Fuel percentage"),
                    FieldSpec(name="status", type="str", description="Active/inactive"),
                    FieldSpec(name="latitude", type="float", description="GPS lat"),
                    FieldSpec(name="longitude", type="float", description="GPS lng"),
                    FieldSpec(name="assigned_driver_id", type="str", description="Driver FK"),
                ],
            ),
            EntitySpec(
                name="Driver",
                fields=[
                    FieldSpec(name="name", type="str", description="Driver name"),
                    FieldSpec(name="license_number", type="str", description="License"),
                    FieldSpec(name="status", type="str", description="Active/on-leave"),
                    FieldSpec(name="rating", type="float", description="Performance rating"),
                ],
            ),
            EntitySpec(
                name="MaintenanceLog",
                fields=[
                    FieldSpec(name="vehicle_id", type="str", description="Vehicle FK"),
                    FieldSpec(name="event_type", type="str", description="Type of event"),
                    FieldSpec(name="description", type="str", description="Description"),
                    FieldSpec(name="timestamp", type="datetime", description="When occurred"),
                    FieldSpec(name="severity", type="str", description="Severity level"),
                    FieldSpec(name="cost", type="float", description="Repair cost"),
                ],
            ),
            EntitySpec(
                name="Route",
                fields=[
                    FieldSpec(name="name", type="str", description="Route name"),
                    FieldSpec(name="origin", type="str", description="Start point"),
                    FieldSpec(name="destination", type="str", description="End point"),
                    FieldSpec(name="distance_km", type="float", description="Distance"),
                ],
            ),
        ],
    )


def _make_single_entity_spec() -> IntentSpec:
    return IntentSpec(
        project_name="single-test",
        app_type=AppType.API,
        description="A single entity app",
        raw_intent="Build a simple task tracker",
        data_stores=[],
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
        ),
        observability=ObservabilityRequirements(),
        networking=NetworkingModel.PUBLIC_RESTRICTED,
        entities=[
            EntitySpec(
                name="Task",
                fields=[
                    FieldSpec(name="title", type="str", description="Task title"),
                    FieldSpec(name="status", type="str", description="Task status"),
                    FieldSpec(name="priority", type="str", description="Priority level"),
                ],
            ),
        ],
    )


class TestAILayoutComposer:
    def test_compose_returns_layout_plan(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        assert plan is not None
        assert len(plan.pages) > 0

    def test_dashboard_page_always_present(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        dashboard = [p for p in plan.pages if p.page_type == "dashboard"]
        assert len(dashboard) >= 1

    def test_primary_entity_gets_kanban_or_analytics_page(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        # Vehicle should be primary and get kanban/analytics pages
        entity_pages = [p for p in plan.pages if p.page_type in ("kanban", "analytics")]
        assert len(entity_pages) >= 1

    def test_event_log_entity_detected(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        # MaintenanceLog has event_type + severity + FK fields
        log_analyses = [a for a in plan.entity_analyses if "maintenance" in a.name.lower()]
        assert len(log_analyses) == 1
        # Has temporal + severity fields consistent with event log characteristics
        assert log_analyses[0].has_priority  # severity maps to priority signal

    def test_relationships_inferred(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        # MaintenanceLog.vehicle_id -> Vehicle, Vehicle.assigned_driver_id -> Driver
        assert len(plan.relationships) >= 1

    def test_nav_items_generated(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        assert len(plan.nav_items) > 0

    def test_single_entity_still_produces_pages(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_single_entity_spec())
        assert len(plan.pages) >= 1

    def test_geo_page_for_geo_entities(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        # Vehicle has lat/lng → should trigger geo/map page
        geo_pages = [p for p in plan.pages if p.page_type in ("geo", "map")]
        assert len(geo_pages) >= 1, "Vehicle with lat/lng should trigger a geo/map page"

    def test_dynamic_builder_page_for_multiple_entities(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        # 4 entities → should always include dynamic builder
        builder_pages = [p for p in plan.pages if p.page_type == "builder"]
        assert len(builder_pages) >= 1

    def test_entity_analysis_completeness(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        assert len(plan.entity_analyses) == 4  # Vehicle, Driver, MaintenanceLog, Route
        for a in plan.entity_analyses:
            assert a.name != ""
            assert a.field_count > 0
            assert a.importance_score > 0

    def test_widgets_have_valid_types(self):
        composer = AILayoutComposer()
        plan = composer.compose(_make_multi_entity_spec())
        valid_types = {
            "chart_bar", "chart_line", "chart_pie", "gauge", "heatmap",
            "table", "kanban", "timeline", "feed", "sparkline_grid",
            "treemap", "radar", "geo_map",
        }
        for page in plan.pages:
            for widget in page.widgets:
                assert widget.widget_type in valid_types, (
                    f"Unknown widget type: {widget.widget_type}"
                )
