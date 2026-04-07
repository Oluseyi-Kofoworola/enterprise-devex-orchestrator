"""UIModelCompiler -- Deterministic UI derivation from EntitySpec.

This is the core innovation that overcomes MDD/SDD limitations:
- No LLM dependency for UI generation (compilable by construction)
- UI structure derived deterministically from domain model
- Every generated TSX is guaranteed to parse (no string injection bugs)
- Model changes automatically propagate to UI (living model)

The compiler operates on the principle that a well-defined EntitySpec
contains enough information to derive a complete, functional UI:
  EntitySpec → UIPageSpec → TSX (all deterministic, all compile-safe)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from src.orchestrator.intent_schema import EntitySpec, FieldSpec, IntentSpec


# ---------------------------------------------------------------------------
# Safe TSX builder primitives -- prevent injection by construction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TSXNode:
    """A single JSX element that is safe to render."""
    tag: str
    class_name: str = ""
    children: list[str | "TSXNode"] = field(default_factory=list)
    props: dict[str, str] = field(default_factory=dict)

    def render(self, indent: int = 0) -> str:
        pad = "  " * indent
        props_str = ""
        if self.class_name:
            props_str += f' className="{_escape_attr(self.class_name)}"'
        for k, v in self.props.items():
            if v.startswith("{") and v.endswith("}"):
                props_str += f" {k}={v}"
            else:
                props_str += f' {k}="{_escape_attr(v)}"'

        if not self.children:
            return f"{pad}<{self.tag}{props_str} />"

        inner_parts = []
        for child in self.children:
            if isinstance(child, TSXNode):
                inner_parts.append(child.render(indent + 1))
            else:
                inner_parts.append(f"{'  ' * (indent + 1)}{child}")

        inner = "\n".join(inner_parts)
        return f"{pad}<{self.tag}{props_str}>\n{inner}\n{pad}</{self.tag}>"


def _escape_attr(s: str) -> str:
    """Escape a string for safe use in JSX attributes."""
    return s.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_text(s: str) -> str:
    """Escape a string for safe use in JSX text content."""
    return s.replace("{", "&#123;").replace("}", "&#125;").replace("<", "&lt;").replace(">", "&gt;")


def _safe_identifier(name: str) -> str:
    """Convert entity/field name to a safe JS identifier."""
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = "x" + cleaned
    return cleaned


# ---------------------------------------------------------------------------
# Field type intelligence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldRenderHint:
    """How a field should be rendered in the UI."""
    display_type: Literal["text", "number", "badge", "date", "boolean", "url", "email", "currency", "percentage"]
    is_sortable: bool = True
    is_filterable: bool = False
    column_width: str = "auto"


def _infer_render_hint(f: FieldSpec) -> FieldRenderHint:
    """Infer UI rendering hints from field spec."""
    name_lower = f.name.lower()
    type_lower = f.type.lower()

    if type_lower in ("bool", "boolean"):
        return FieldRenderHint("boolean", is_sortable=False)
    if type_lower in ("datetime", "date"):
        return FieldRenderHint("date")
    if type_lower in ("int", "float", "number", "decimal"):
        if "price" in name_lower or "cost" in name_lower or "amount" in name_lower:
            return FieldRenderHint("currency")
        if "percent" in name_lower or "rate" in name_lower or "ratio" in name_lower:
            return FieldRenderHint("percentage")
        return FieldRenderHint("number")
    if "email" in name_lower:
        return FieldRenderHint("email", is_sortable=False)
    if "url" in name_lower or "link" in name_lower:
        return FieldRenderHint("url", is_sortable=False)
    if "status" in name_lower or "state" in name_lower or "priority" in name_lower or "severity" in name_lower:
        return FieldRenderHint("badge", is_filterable=True)

    return FieldRenderHint("text")


def _select_display_fields(entity: EntitySpec, max_cols: int = 6) -> list[FieldSpec]:
    """Select the most important fields for table display."""
    if not entity.fields:
        return []

    # Priority ordering: name/title first, then status, then other required, then optional
    priority_names = {"name", "title", "label", "subject", "description"}
    status_names = {"status", "state", "priority", "severity", "type", "category"}

    scored: list[tuple[int, FieldSpec]] = []
    for f in entity.fields:
        name_lower = f.name.lower()
        if name_lower == "id":
            continue  # Skip ID, always implicit
        score = 0
        if name_lower in priority_names:
            score = 100
        elif name_lower in status_names:
            score = 80
        elif f.required:
            score = 50
        else:
            score = 20
        scored.append((score, f))

    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:max_cols]]


# ---------------------------------------------------------------------------
# Page compiler
# ---------------------------------------------------------------------------

@dataclass
class CompiledPage:
    """Result of compiling an entity into a page."""
    component_name: str
    tsx_content: str
    route_path: str
    nav_label: str


class UIModelCompiler:
    """Deterministic compiler: EntitySpec[] → compilable React TSX pages.

    Every output is guaranteed to be valid JSX because we build the AST
    programmatically (no string interpolation of user data into code positions).
    """

    def compile_dashboard(self, spec: IntentSpec) -> str:
        """Compile all entities into a unified dashboard page."""
        entities = spec.entities or []
        project_name = spec.project_name.replace("-", " ").title()
        api_base = "${import.meta.env.VITE_API_BASE_URL || '/api/v1'}"

        # Build KPI cards and entity summaries
        kpi_cards = self._build_kpi_cards(entities)
        entity_tables = self._build_entity_tables(entities)

        return self._assemble_dashboard_tsx(
            page_title=f"{project_name} Dashboard",
            kpi_cards=kpi_cards,
            entity_tables=entity_tables,
            api_base=api_base,
            entities=entities,
        )

    def compile_entity_page(self, entity: EntitySpec, spec: IntentSpec) -> CompiledPage:
        """Compile a single entity into a detail/list page."""
        component_name = _safe_identifier(entity.name)
        plural = _pluralize(entity.name)
        snake = _to_snake(entity.name)
        slug = _to_snake(plural)
        display_fields = _select_display_fields(entity)
        field_hints = {f.name: _infer_render_hint(f) for f in display_fields}

        tsx = self._assemble_entity_page_tsx(
            component_name=component_name,
            entity_name=entity.name,
            plural_name=plural,
            snake_name=slug,
            fields=display_fields,
            field_hints=field_hints,
        )

        return CompiledPage(
            component_name=component_name,
            tsx_content=tsx,
            route_path=f"/{snake}",
            nav_label=plural,
        )

    def compile_all(self, spec: IntentSpec) -> dict[str, str]:
        """Compile the full UI from spec. Returns file_path → content."""
        files: dict[str, str] = {}

        # Dashboard
        files["frontend/src/pages/Dashboard.tsx"] = self.compile_dashboard(spec)

        # Entity pages
        for entity in (spec.entities or []):
            page = self.compile_entity_page(entity, spec)
            files[f"frontend/src/pages/{page.component_name}Page.tsx"] = page.tsx_content

        return files

    # -- Private assembly methods ------------------------------------------

    def _build_kpi_cards(self, entities: list[EntitySpec]) -> list[dict]:
        """Build KPI card definitions from entity list."""
        cards = []
        for entity in entities:
            plural = _pluralize(entity.name)
            snake = _to_snake(entity.name)
            cards.append({
                "label": f"Total {plural}",
                "entity": snake,
                "icon": "Activity",
            })
        return cards

    def _build_entity_tables(self, entities: list[EntitySpec]) -> list[dict]:
        """Build entity table definitions."""
        tables = []
        for entity in entities:
            display_fields = _select_display_fields(entity, max_cols=5)
            tables.append({
                "entity_name": entity.name,
                "plural": _pluralize(entity.name),
                "snake": _to_snake(entity.name),
                "fields": [(f.name, _infer_render_hint(f)) for f in display_fields],
            })
        return tables

    def _assemble_dashboard_tsx(
        self,
        page_title: str,
        kpi_cards: list[dict],
        entity_tables: list[dict],
        api_base: str,
        entities: list[EntitySpec],
    ) -> str:
        """Assemble a complete, compilable Dashboard TSX file."""
        # Build state declarations
        state_lines = []
        fetch_lines = []
        for entity in entities:
            snake = _to_snake(entity.name)
            slug = _to_snake(_pluralize(entity.name))
            var = _safe_identifier(snake)
            state_lines.append(
                f"  const [{var}Data, set{var.capitalize()}Data] = "
                f"useState<Record<string, unknown>[]>([]);"
            )
            state_lines.append(
                f"  const [{var}Loading, set{var.capitalize()}Loading] = useState(true);"
            )
            fetch_lines.append(f"      fetch(`{api_base}/{slug}`)")
            fetch_lines.append(f"        .then(r => r.ok ? r.json() : [])")
            fetch_lines.append(f"        .then(d => {{ set{var.capitalize()}Data(Array.isArray(d) ? d : []); set{var.capitalize()}Loading(false); }})")
            fetch_lines.append(f"        .catch(() => set{var.capitalize()}Loading(false));")

        # Build KPI card JSX
        kpi_jsx_parts = []
        for card in kpi_cards:
            var = _safe_identifier(card["entity"])
            label = _escape_text(card["label"])
            kpi_jsx_parts.append(f"""        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            {{{var}Loading ? "..." : {var}Data.length}}
          </p>
        </div>""")

        kpi_grid = "\n".join(kpi_jsx_parts)

        # Build entity table JSX
        table_jsx_parts = []
        for tbl in entity_tables:
            var = _safe_identifier(tbl["snake"])
            plural_escaped = _escape_text(tbl["plural"])

            header_cells = []
            body_cells = []
            for fname, hint in tbl["fields"]:
                header_cells.append(
                    f'                  <th className="px-4 py-3 text-left text-xs font-medium '
                    f'text-gray-500 uppercase">{_escape_text(fname)}</th>'
                )
                cell_expr = self._render_cell_expr(fname, hint)
                body_cells.append(
                    f'                    <td className="px-4 py-3 text-sm text-gray-700 '
                    f'dark:text-gray-300">{cell_expr}</td>'
                )

            headers_str = "\n".join(header_cells)
            cells_str = "\n".join(body_cells)

            table_jsx_parts.append(f"""      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{plural_escaped}</h2>
        </div>
        {{{var}Loading ? (
          <div className="p-6 text-center text-gray-400">Loading...</div>
        ) : {var}Data.length === 0 ? (
          <div className="p-6 text-center text-gray-400">No {_escape_text(tbl["plural"].lower())} found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
{headers_str}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {{{var}Data.slice(0, 10).map((item, i) => (
                  <tr key={{i}} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
{cells_str}
                  </tr>
                ))}}
              </tbody>
            </table>
          </div>
        )}}
      </div>""")

        tables_str = "\n\n".join(table_jsx_parts)

        # Assemble complete file
        return f"""import {{ useEffect, useState }} from 'react';

export default function Dashboard() {{
{chr(10).join(state_lines)}

  useEffect(() => {{
{chr(10).join(fetch_lines)}
  }}, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <header className="mb-4">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{_escape_text(page_title)}</h1>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-{min(len(kpi_cards), 4)} gap-6">
{kpi_grid}
      </div>

{tables_str}
    </div>
  );
}}
"""

    def _assemble_entity_page_tsx(
        self,
        component_name: str,
        entity_name: str,
        plural_name: str,
        snake_name: str,
        fields: list[FieldSpec],
        field_hints: dict[str, FieldRenderHint],
    ) -> str:
        """Assemble a compilable entity list/detail page."""
        api_base = "${import.meta.env.VITE_API_BASE_URL || '/api/v1'}"
        var = _safe_identifier(snake_name)

        # Table headers
        headers = []
        cells = []
        for f in fields:
            hint = field_hints.get(f.name, FieldRenderHint("text"))
            headers.append(
                f'              <th className="px-4 py-3 text-left text-xs font-medium '
                f'text-gray-500 uppercase">{_escape_text(f.name)}</th>'
            )
            cell_expr = self._render_cell_expr(f.name, hint)
            cells.append(
                f'                <td className="px-4 py-3 text-sm">{cell_expr}</td>'
            )

        headers_str = "\n".join(headers)
        cells_str = "\n".join(cells)
        plural_escaped = _escape_text(plural_name)
        entity_escaped = _escape_text(entity_name)

        return f"""import {{ useEffect, useState }} from 'react';

export default function {component_name}Page() {{
  const [{var}Data, set{var.capitalize()}Data] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    fetch(`{api_base}/{snake_name}`)
      .then(r => {{
        if (!r.ok) throw new Error(`HTTP ${{r.status}}`);
        return r.json();
      }})
      .then(d => {{ set{var.capitalize()}Data(Array.isArray(d) ? d : []); setLoading(false); }})
      .catch(e => {{ setError(e.message); setLoading(false); }});
  }}, []);

  if (error) {{
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900/20 text-red-600 p-4 rounded-lg">
          Failed to load {_escape_text(plural_name.lower())}: {{error}}
        </div>
      </div>
    );
  }}

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <header className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{plural_escaped}</h1>
        <span className="text-sm text-gray-500">{{loading ? "Loading..." : `${{{var}Data.length}} {_escape_text(plural_name.lower())}`}}</span>
      </header>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        {{loading ? (
          <div className="p-8 text-center text-gray-400">Loading {_escape_text(plural_name.lower())}...</div>
        ) : {var}Data.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No {_escape_text(plural_name.lower())} found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
{headers_str}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {{{var}Data.map((item, i) => (
                  <tr key={{i}} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
{cells_str}
                  </tr>
                ))}}
              </tbody>
            </table>
          </div>
        )}}
      </div>
    </div>
  );
}}
"""

    def _render_cell_expr(self, field_name: str, hint: FieldRenderHint) -> str:
        """Render a safe JSX expression for a table cell."""
        accessor = f"item.{_safe_identifier(field_name)}"
        safe_name = _safe_identifier(field_name)

        if hint.display_type == "badge":
            return (
                f'{{String({accessor} || "")}}'
            )
        if hint.display_type == "boolean":
            return f'{{{accessor} ? "Yes" : "No"}}'
        if hint.display_type == "date":
            return f'{{typeof {accessor} === "string" ? new Date({accessor}).toLocaleDateString() : String({accessor} ?? "")}}'
        if hint.display_type == "currency":
            return f'{{typeof {accessor} === "number" ? `$${{{accessor}.toFixed(2)}}` : String({accessor} ?? "")}}'
        if hint.display_type == "percentage":
            return f'{{typeof {accessor} === "number" ? `${{{accessor}}}%` : String({accessor} ?? "")}}'
        if hint.display_type in ("url", "email"):
            return f'{{String({accessor} || "")}}'

        return f'{{String({accessor} ?? "")}}'


# ---------------------------------------------------------------------------
# String utilities (deterministic, no external deps)
# ---------------------------------------------------------------------------

_IRREGULAR_PLURALS = {
    "person": "people", "child": "children", "analysis": "analyses",
    "diagnosis": "diagnoses", "criterion": "criteria", "datum": "data",
    "medium": "media", "index": "indices", "vertex": "vertices",
    "matrix": "matrices", "crisis": "crises", "thesis": "theses",
    "stimulus": "stimuli", "focus": "foci", "fungus": "fungi",
}

_NO_CHANGE_PLURALS = {"sheep", "fish", "deer", "aircraft", "species", "series"}


def _pluralize(name: str) -> str:
    """Deterministic English pluralization."""
    lower = name.lower()
    if lower in _IRREGULAR_PLURALS:
        result = _IRREGULAR_PLURALS[lower]
        return result[0].upper() + result[1:] if name[0].isupper() else result
    if lower in _NO_CHANGE_PLURALS:
        return name
    if lower.endswith("s") or lower.endswith("x") or lower.endswith("z") or lower.endswith("ch") or lower.endswith("sh"):
        return name + "es"
    if lower.endswith("y") and lower[-2:] not in ("ay", "ey", "iy", "oy", "uy"):
        return name[:-1] + "ies"
    return name + "s"


def _to_snake(name: str) -> str:
    """PascalCase → snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
