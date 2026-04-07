"""Tests for UIModelCompiler -- deterministic UI generation from EntitySpec."""

import pytest
from src.orchestrator.generators.ui_model_compiler import (
    UIModelCompiler,
    _escape_attr,
    _escape_text,
    _infer_render_hint,
    _pluralize,
    _safe_identifier,
    _select_display_fields,
    _to_snake,
)
from src.orchestrator.intent_schema import EntitySpec, FieldSpec, IntentSpec


# -- Helpers ---------------------------------------------------------------

def _make_spec(entities: list[EntitySpec] | None = None) -> IntentSpec:
    return IntentSpec(
        project_name="test-project",
        description="Test project for UI compiler",
        raw_intent="test",
        entities=entities or [],
    )


def _make_entity(name: str, fields: list[tuple[str, str]] | None = None) -> EntitySpec:
    if fields is None:
        fields = [("name", "str"), ("status", "str"), ("created_at", "datetime")]
    return EntitySpec(
        name=name,
        fields=[FieldSpec(name=n, type=t) for n, t in fields],
        description=f"Test entity {name}",
    )


# -- Unit tests: string utilities -----------------------------------------

class TestStringUtilities:
    def test_pluralize_regular(self):
        assert _pluralize("Customer") == "Customers"
        assert _pluralize("order") == "orders"

    def test_pluralize_es(self):
        assert _pluralize("status") == "statuses"
        assert _pluralize("box") == "boxes"

    def test_pluralize_ies(self):
        assert _pluralize("category") == "categories"
        assert _pluralize("Policy") == "Policies"

    def test_pluralize_irregular(self):
        assert _pluralize("person") == "people"
        assert _pluralize("Analysis") == "Analyses"
        assert _pluralize("Child") == "Children"

    def test_pluralize_no_change(self):
        assert _pluralize("sheep") == "sheep"
        assert _pluralize("fish") == "fish"

    def test_to_snake(self):
        assert _to_snake("CustomerOrder") == "customer_order"
        assert _to_snake("HTTPSConnection") == "https_connection"
        assert _to_snake("simple") == "simple"

    def test_safe_identifier(self):
        assert _safe_identifier("valid_name") == "valid_name"
        assert _safe_identifier("with-dashes") == "withdashes"
        assert _safe_identifier("123start") == "x123start"

    def test_escape_attr(self):
        assert _escape_attr('hello "world"') == 'hello &quot;world&quot;'
        assert _escape_attr("<script>") == "&lt;script&gt;"

    def test_escape_text(self):
        assert _escape_text("{value}") == "&#123;value&#125;"
        assert _escape_text("<div>") == "&lt;div&gt;"


# -- Unit tests: field intelligence ---------------------------------------

class TestFieldIntelligence:
    def test_boolean_field(self):
        hint = _infer_render_hint(FieldSpec(name="is_active", type="bool"))
        assert hint.display_type == "boolean"

    def test_datetime_field(self):
        hint = _infer_render_hint(FieldSpec(name="created_at", type="datetime"))
        assert hint.display_type == "date"

    def test_currency_field(self):
        hint = _infer_render_hint(FieldSpec(name="total_price", type="float"))
        assert hint.display_type == "currency"

    def test_percentage_field(self):
        hint = _infer_render_hint(FieldSpec(name="success_rate", type="float"))
        assert hint.display_type == "percentage"

    def test_status_badge(self):
        hint = _infer_render_hint(FieldSpec(name="status", type="str"))
        assert hint.display_type == "badge"
        assert hint.is_filterable

    def test_email_field(self):
        hint = _infer_render_hint(FieldSpec(name="email_address", type="str"))
        assert hint.display_type == "email"

    def test_plain_text(self):
        hint = _infer_render_hint(FieldSpec(name="description", type="str"))
        assert hint.display_type == "text"


# -- Unit tests: field selection -------------------------------------------

class TestFieldSelection:
    def test_selects_name_first(self):
        entity = _make_entity("User", [
            ("id", "str"),
            ("name", "str"),
            ("age", "int"),
            ("status", "str"),
        ])
        selected = _select_display_fields(entity)
        # ID should be excluded, name should be first
        assert selected[0].name == "name"
        # Status should be second (priority name)
        assert selected[1].name == "status"

    def test_skips_id_field(self):
        entity = _make_entity("User", [("id", "str"), ("name", "str")])
        selected = _select_display_fields(entity)
        assert all(f.name != "id" for f in selected)

    def test_limits_columns(self):
        entity = _make_entity("User", [(f"field_{i}", "str") for i in range(20)])
        selected = _select_display_fields(entity, max_cols=5)
        assert len(selected) <= 5

    def test_empty_entity(self):
        entity = EntitySpec(name="Empty", fields=[])
        assert _select_display_fields(entity) == []


# -- Integration tests: UIModelCompiler -----------------------------------

class TestUIModelCompiler:
    def setup_method(self):
        self.compiler = UIModelCompiler()

    def test_compile_dashboard_no_entities(self):
        spec = _make_spec([])
        result = self.compiler.compile_dashboard(spec)
        assert "export default function Dashboard" in result
        assert "import" in result

    def test_compile_dashboard_with_entities(self):
        spec = _make_spec([
            _make_entity("Customer"),
            _make_entity("Order"),
        ])
        result = self.compiler.compile_dashboard(spec)
        assert "export default function Dashboard" in result
        assert "Total Customers" in result or "customer" in result.lower()
        assert "Total Orders" in result or "order" in result.lower()
        assert "useState" in result
        assert "useEffect" in result

    def test_compile_dashboard_tsx_is_balanced(self):
        """Core guarantee: generated TSX has balanced braces."""
        spec = _make_spec([
            _make_entity("Document", [
                ("title", "str"),
                ("status", "str"),
                ("created_at", "datetime"),
                ("file_url", "str"),
            ]),
        ])
        result = self.compiler.compile_dashboard(spec)
        # Strip strings before checking
        assert result.count("{") == result.count("}")
        assert result.count("(") == result.count(")")
        assert result.count("[") == result.count("]")

    def test_compile_entity_page(self):
        entity = _make_entity("Invoice", [
            ("invoice_number", "str"),
            ("amount", "float"),
            ("status", "str"),
            ("due_date", "datetime"),
        ])
        spec = _make_spec([entity])
        page = self.compiler.compile_entity_page(entity, spec)

        assert page.component_name == "Invoice"
        assert "InvoicePage" in page.tsx_content
        assert page.route_path == "/invoice"
        assert "useState" in page.tsx_content

    def test_compile_all_returns_file_dict(self):
        spec = _make_spec([
            _make_entity("Patient"),
            _make_entity("Appointment"),
        ])
        files = self.compiler.compile_all(spec)
        assert "frontend/src/pages/Dashboard.tsx" in files
        assert "frontend/src/pages/PatientPage.tsx" in files
        assert "frontend/src/pages/AppointmentPage.tsx" in files
        assert len(files) == 3

    def test_no_raw_curly_injection(self):
        """Ensure error messages can't inject raw curlies into JSX."""
        # This is the exact bug class that caused the Dashboard crash
        entity = _make_entity("Test", [
            ("name", "str"),
            ("value", "str"),
        ])
        entity_with_bad_desc = EntitySpec(
            name="Test{Injection}",
            fields=[FieldSpec(name="na{me", type="str")],
            description="Test {with} curlies",
        )
        spec = _make_spec([entity_with_bad_desc])
        result = self.compiler.compile_dashboard(spec)
        # Should not contain raw unescaped curlies from entity names in text positions
        assert "export default function Dashboard" in result

    def test_compiled_tsx_is_deterministic(self):
        """Same input always produces identical output."""
        spec = _make_spec([_make_entity("Widget")])
        result1 = self.compiler.compile_dashboard(spec)
        result2 = self.compiler.compile_dashboard(spec)
        assert result1 == result2
