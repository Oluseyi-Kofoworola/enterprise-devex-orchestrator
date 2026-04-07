"""Tests for RouteManifest -- Phase 6 route single source of truth."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.route_manifest import (
    RouteAction,
    RouteBuilder,
    RouteManifest,
    RouteSpec,
)
from src.orchestrator.intent_schema import (
    EndpointSpec,
    EntitySpec,
    FieldSpec,
    IntentSpec,
)


def _make_spec(**kwargs) -> IntentSpec:
    defaults = {
        "project_name": "test-project",
        "description": "Test project",
        "raw_intent": "test intent",
    }
    defaults.update(kwargs)
    return IntentSpec(**defaults)


class TestRouteBuilder:
    """Tests for RouteBuilder.build."""

    def test_empty_entities_produces_empty_manifest(self) -> None:
        spec = _make_spec(entities=[])
        manifest = RouteBuilder.build(spec)
        assert len(manifest.routes) == 0
        assert manifest.health_route is not None

    def test_single_entity_produces_five_crud_routes(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Incident", fields=[
                FieldSpec(name="title", type="str"),
                FieldSpec(name="status", type="str"),
            ]),
        ])
        manifest = RouteBuilder.build(spec)
        assert len(manifest.routes) == 5  # LIST, CREATE, GET, UPDATE, DELETE

    def test_crud_methods(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Task", fields=[FieldSpec(name="title", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        methods = {r.method for r in manifest.routes}
        assert methods == {"GET", "POST", "PUT", "DELETE"}

    def test_crud_actions(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Task", fields=[FieldSpec(name="title", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        actions = {r.action for r in manifest.routes}
        assert RouteAction.LIST in actions
        assert RouteAction.CREATE in actions
        assert RouteAction.GET in actions
        assert RouteAction.UPDATE in actions
        assert RouteAction.DELETE in actions

    def test_status_filter_detected(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Ticket", fields=[
                FieldSpec(name="title", type="str"),
                FieldSpec(name="status", type="str"),
            ]),
        ])
        manifest = RouteBuilder.build(spec)
        list_route = next(r for r in manifest.routes if r.action == RouteAction.LIST)
        assert list_route.has_status_filter is True

    def test_no_status_filter_without_status_field(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Note", fields=[FieldSpec(name="content", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        list_route = next(r for r in manifest.routes if r.action == RouteAction.LIST)
        assert list_route.has_status_filter is False

    def test_custom_action_endpoints(self) -> None:
        spec = _make_spec(
            entities=[
                EntitySpec(name="Contract", fields=[FieldSpec(name="title", type="str")]),
            ],
            endpoints=[
                EndpointSpec(method="POST", path="/contracts/{id}/approve", description="Approve contract"),
            ],
        )
        manifest = RouteBuilder.build(spec)
        custom = [r for r in manifest.routes if r.action == RouteAction.CUSTOM]
        assert len(custom) == 1
        assert "approve" in custom[0].action_name

    def test_multiple_entities(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Incident", fields=[FieldSpec(name="title", type="str")]),
            EntitySpec(name="WorkOrder", fields=[FieldSpec(name="title", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        assert len(manifest.routes) == 10  # 5 per entity
        assert len(manifest.entity_names) == 2

    def test_path_params_for_detail_routes(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Item", fields=[FieldSpec(name="name", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        detail_routes = [r for r in manifest.routes if r.has_path_param]
        assert len(detail_routes) == 3  # GET, UPDATE, DELETE

    def test_create_has_201_status(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Item", fields=[FieldSpec(name="name", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        create = next(r for r in manifest.routes if r.action == RouteAction.CREATE)
        assert create.status_code == 201

    def test_delete_has_204_status(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Item", fields=[FieldSpec(name="name", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        delete = next(r for r in manifest.routes if r.action == RouteAction.DELETE)
        assert delete.status_code == 204


class TestRouteManifest:
    """Tests for RouteManifest data structure."""

    def test_entity_names_unique_ordered(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Alpha", fields=[FieldSpec(name="x", type="str")]),
            EntitySpec(name="Beta", fields=[FieldSpec(name="x", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        assert manifest.entity_names == ["Alpha", "Beta"]

    def test_routes_for_entity(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Alpha", fields=[FieldSpec(name="x", type="str")]),
            EntitySpec(name="Beta", fields=[FieldSpec(name="x", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        alpha_routes = manifest.routes_for_entity("Alpha")
        assert len(alpha_routes) == 5
        assert all(r.entity == "Alpha" for r in alpha_routes)

    def test_all_routes_includes_health(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Item", fields=[FieldSpec(name="x", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        all_routes = manifest.all_routes
        assert len(all_routes) == 6  # 5 CRUD + 1 health
        assert all_routes[0].path == "/health"

    def test_route_count(self) -> None:
        spec = _make_spec(entities=[
            EntitySpec(name="Task", fields=[FieldSpec(name="x", type="str")]),
        ])
        manifest = RouteBuilder.build(spec)
        assert manifest.route_count == 6  # 5 + health
