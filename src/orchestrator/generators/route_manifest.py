"""Route Manifest -- single source of truth for all generated API routes.

Provides a structured description of every route the scaffold exposes,
derived deterministically from the IntentSpec. Both the app generator
(router code) and the test generator (pytest test cases) consume
this manifest so route coverage is guaranteed.

Components:
- RouteSpec: individual route definition (method, path, entity, action)
- RouteManifest: complete collection of routes for a spec
- RouteBuilder: builds the manifest from IntentSpec entities + endpoints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re


class RouteAction(str, Enum):
    """Standard CRUD actions and custom actions."""
    LIST = "list"
    CREATE = "create"
    GET = "get"
    UPDATE = "update"
    DELETE = "delete"
    CUSTOM = "custom"


@dataclass(frozen=True)
class RouteSpec:
    """A single API route in the manifest."""
    method: str  # GET, POST, PUT, DELETE
    path: str  # e.g. /api/v1/incidents
    entity: str  # PascalCase entity name (e.g. "Incident")
    action: RouteAction
    action_name: str  # e.g. "list_incidents", "approve_contract"
    has_path_param: bool = False  # True if route has {id} param
    has_status_filter: bool = False  # True if LIST route supports ?status=
    status_code: int = 200
    summary: str = ""


@dataclass
class RouteManifest:
    """Complete set of routes for a scaffold."""
    routes: list[RouteSpec] = field(default_factory=list)
    health_route: RouteSpec = field(default_factory=lambda: RouteSpec(
        method="GET", path="/health", entity="", action=RouteAction.GET,
        action_name="health_check", summary="Health check"
    ))

    @property
    def entity_names(self) -> list[str]:
        """Return unique entity names in manifest order."""
        seen: set[str] = set()
        result: list[str] = []
        for r in self.routes:
            if r.entity and r.entity not in seen:
                seen.add(r.entity)
                result.append(r.entity)
        return result

    def routes_for_entity(self, entity: str) -> list[RouteSpec]:
        return [r for r in self.routes if r.entity == entity]

    @property
    def all_routes(self) -> list[RouteSpec]:
        return [self.health_route] + self.routes

    @property
    def route_count(self) -> int:
        return len(self.all_routes)


def _snake(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower().replace(" ", "_").replace("-", "_")


_IRREGULAR_PLURALS = {
    "child": "children", "person": "people", "man": "men",
    "woman": "women", "mouse": "mice", "goose": "geese",
    "tooth": "teeth", "foot": "feet", "datum": "data",
    "analysis": "analyses", "criterion": "criteria",
    "phenomenon": "phenomena", "index": "indices",
    "matrix": "matrices", "vertex": "vertices",
    "appendix": "appendices", "crisis": "crises",
}


def _plural(word: str) -> str:
    """Simple pluralization."""
    lower = word.lower()
    if lower in _IRREGULAR_PLURALS:
        result = _IRREGULAR_PLURALS[lower]
        return result[0].upper() + result[1:] if word[0].isupper() else result
    if lower.endswith(("s", "sh", "ch", "x", "z")):
        return word + "es"
    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


class RouteBuilder:
    """Builds a RouteManifest from an IntentSpec."""

    @staticmethod
    def build(spec: "IntentSpec") -> RouteManifest:
        from src.orchestrator.intent_schema import IntentSpec as _IntentSpec

        routes: list[RouteSpec] = []
        api_prefix = "/api/v1"

        for ent in spec.entities:
            sn = _snake(ent.name)
            slug = _snake(_plural(ent.name))
            has_status = any(f.name in ("status", "state") for f in ent.fields)

            # LIST
            routes.append(RouteSpec(
                method="GET",
                path=f"{api_prefix}/{slug}",
                entity=ent.name,
                action=RouteAction.LIST,
                action_name=f"list_{slug}",
                has_status_filter=has_status,
                summary=f"List {_plural(ent.name).lower()}",
            ))
            # CREATE
            routes.append(RouteSpec(
                method="POST",
                path=f"{api_prefix}/{slug}",
                entity=ent.name,
                action=RouteAction.CREATE,
                action_name=f"create_{sn}",
                status_code=201,
                summary=f"Create {ent.name.lower()}",
            ))
            # GET by ID
            routes.append(RouteSpec(
                method="GET",
                path=f"{api_prefix}/{slug}/{{{sn}_id}}",
                entity=ent.name,
                action=RouteAction.GET,
                action_name=f"get_{sn}",
                has_path_param=True,
                summary=f"Get {ent.name.lower()} by ID",
            ))
            # UPDATE
            routes.append(RouteSpec(
                method="PUT",
                path=f"{api_prefix}/{slug}/{{{sn}_id}}",
                entity=ent.name,
                action=RouteAction.UPDATE,
                action_name=f"update_{sn}",
                has_path_param=True,
                summary=f"Update {ent.name.lower()}",
            ))
            # DELETE
            routes.append(RouteSpec(
                method="DELETE",
                path=f"{api_prefix}/{slug}/{{{sn}_id}}",
                entity=ent.name,
                action=RouteAction.DELETE,
                action_name=f"delete_{sn}",
                has_path_param=True,
                status_code=204,
                summary=f"Delete {ent.name.lower()}",
            ))

            # Custom action endpoints from spec.endpoints
            for ep in (spec.endpoints or []):
                parts = ep.path.strip("/").split("/")
                if len(parts) >= 3 and ep.method.upper() == "POST" and parts[0] == slug:
                    action_word = parts[-1]
                    routes.append(RouteSpec(
                        method="POST",
                        path=f"{api_prefix}/{slug}/{{{sn}_id}}/{action_word}",
                        entity=ent.name,
                        action=RouteAction.CUSTOM,
                        action_name=f"{action_word}_{sn}",
                        has_path_param=True,
                        summary=ep.description or f"{action_word.title()} {ent.name}",
                    ))

        return RouteManifest(routes=routes)
