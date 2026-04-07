"""Tests for ScaffoldValidator -- Phase 10 cross-generator validation."""

from __future__ import annotations

import pytest

from src.orchestrator.generators.scaffold_validator import (
    ScaffoldValidator,
    ValidationIssue,
    ValidationReport,
)
from src.orchestrator.intent_schema import DataStore, EntitySpec, FieldSpec, IntentSpec


def _make_spec(**kwargs) -> IntentSpec:
    defaults = {
        "project_name": "test-project",
        "description": "Test project",
        "raw_intent": "test intent",
    }
    defaults.update(kwargs)
    return IntentSpec(**defaults)


def _minimal_files(lang: str = "python") -> dict[str, str]:
    """Return a minimal valid file set."""
    base = {
        "infra/bicep/main.bicep": "// main bicep",
        ".github/workflows/validate.yml": "name: Validate",
        ".github/workflows/deploy.yml": "name: Deploy",
    }
    if lang == "python":
        base.update({
            "src/app/main.py": "# main.py",
            "src/app/requirements.txt": "fastapi",
            "src/app/Dockerfile": "FROM python:3.12-slim",
        })
    elif lang == "node":
        base.update({
            "src/app/index.js": "// index.js",
            "src/app/package.json": "{}",
            "src/app/Dockerfile": "FROM node:20-slim",
        })
    elif lang == "dotnet":
        base.update({
            "src/app/Program.cs": "// Program.cs",
            "src/app/App.csproj": "<Project>",
            "src/app/Dockerfile": "FROM mcr.microsoft.com/dotnet/aspnet:8.0",
        })
    return base


class TestScaffoldValidator:
    """Tests for ScaffoldValidator.validate."""

    def test_minimal_valid_scaffold(self) -> None:
        spec = _make_spec()
        validator = ScaffoldValidator()
        report = validator.validate(spec, _minimal_files())
        assert report.is_valid

    def test_missing_main_bicep(self) -> None:
        spec = _make_spec()
        files = _minimal_files()
        del files["infra/bicep/main.bicep"]
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        assert not report.is_valid
        assert report.error_count >= 1

    def test_missing_deploy_workflow(self) -> None:
        spec = _make_spec()
        files = _minimal_files()
        del files[".github/workflows/deploy.yml"]
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        assert not report.is_valid

    def test_missing_python_main(self) -> None:
        spec = _make_spec(language="python")
        files = _minimal_files()
        del files["src/app/main.py"]
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        assert not report.is_valid

    def test_node_language_required_files(self) -> None:
        spec = _make_spec(language="node")
        files = _minimal_files("node")
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        assert report.is_valid

    def test_dotnet_language_required_files(self) -> None:
        spec = _make_spec(language="dotnet")
        files = _minimal_files("dotnet")
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        assert report.is_valid

    def test_dockerfile_without_from(self) -> None:
        spec = _make_spec()
        files = _minimal_files()
        files["src/app/Dockerfile"] = "RUN echo hello"  # No FROM
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        assert not report.is_valid

    def test_entity_not_in_router_warns(self) -> None:
        spec = _make_spec(
            entities=[EntitySpec(name="Widget", fields=[FieldSpec(name="name", type="str")])],
        )
        files = _minimal_files()
        files["src/app/api/v1/router.py"] = "# empty router"
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        warnings = [i for i in report.issues if i.severity == "warning" and "Widget" in i.message]
        assert len(warnings) >= 1

    def test_bicep_missing_data_store_warns(self) -> None:
        spec = _make_spec(data_stores=[DataStore.COSMOS_DB])
        files = _minimal_files()
        files["infra/bicep/main.bicep"] = "// basic template with no data store modules"
        validator = ScaffoldValidator()
        report = validator.validate(spec, files)
        warnings = [i for i in report.issues if "cosmos" in i.message.lower()]
        assert len(warnings) >= 1


class TestValidationReport:
    """Tests for ValidationReport data structure."""

    def test_empty_report_is_valid(self) -> None:
        report = ValidationReport()
        assert report.is_valid
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_report_with_error_is_invalid(self) -> None:
        report = ValidationReport(issues=[
            ValidationIssue("error", "missing_file", "Missing main.bicep"),
        ])
        assert not report.is_valid
        assert report.error_count == 1

    def test_report_with_warning_is_valid(self) -> None:
        report = ValidationReport(issues=[
            ValidationIssue("warning", "inconsistency", "Minor issue"),
        ])
        assert report.is_valid
        assert report.warning_count == 1

    def test_markdown_output_contains_table(self) -> None:
        report = ValidationReport(issues=[
            ValidationIssue("error", "missing_file", "Missing file", "main.bicep"),
        ])
        md = report.to_markdown()
        assert "| Severity |" in md
        assert "FAIL" in md

    def test_markdown_pass_status(self) -> None:
        report = ValidationReport()
        md = report.to_markdown()
        assert "PASS" in md
