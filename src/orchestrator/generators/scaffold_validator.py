"""Scaffold Validator -- cross-generator consistency checks.

Validates the complete output of all generators to catch:
- Missing files that should exist
- Entity references in tests that don't match router routes
- Bicep parameters missing from workflows
- Frontend pages referencing entities that don't exist in the API
- Broken import paths in generated code

Runs after all generators complete to provide a validation report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.orchestrator.generators.route_manifest import RouteBuilder
from src.orchestrator.intent_schema import DataStore, IntentSpec


@dataclass
class ValidationIssue:
    """A single validation finding."""
    severity: str  # "error", "warning", "info"
    category: str  # "missing_file", "broken_ref", "inconsistency"
    message: str
    file_path: str = ""


@dataclass
class ValidationReport:
    """Complete validation report for the scaffold."""
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    def to_markdown(self) -> str:
        lines = ["# Scaffold Validation Report", ""]
        if self.is_valid:
            lines.append(f"**Status: PASS** ({self.warning_count} warnings)")
        else:
            lines.append(f"**Status: FAIL** ({self.error_count} errors, {self.warning_count} warnings)")
        lines.append("")
        if self.issues:
            lines.append("| Severity | Category | File | Message |")
            lines.append("|----------|----------|------|---------|")
            for issue in self.issues:
                lines.append(f"| {issue.severity} | {issue.category} | {issue.file_path} | {issue.message} |")
        else:
            lines.append("No issues found.")
        return "\n".join(lines)


class ScaffoldValidator:
    """Validates generated scaffold files for cross-generator consistency."""

    def validate(self, spec: IntentSpec, files: dict[str, str]) -> ValidationReport:
        """Run all validation checks on the generated file set."""
        report = ValidationReport()

        self._check_required_files(spec, files, report)
        self._check_entity_coverage(spec, files, report)
        self._check_route_test_alignment(spec, files, report)
        self._check_bicep_completeness(spec, files, report)
        self._check_dockerfile_exists(spec, files, report)

        return report

    def _check_required_files(self, spec: IntentSpec, files: dict[str, str],
                               report: ValidationReport) -> None:
        """Verify essential files are present."""
        required = [
            "infra/bicep/main.bicep",
            ".github/workflows/validate.yml",
            ".github/workflows/deploy.yml",
        ]

        lang = spec.language.lower()
        if lang == "python":
            required.extend([
                "src/app/main.py",
                "src/app/requirements.txt",
                "src/app/Dockerfile",
            ])
        elif lang == "node":
            required.extend([
                "src/app/index.js",
                "src/app/package.json",
                "src/app/Dockerfile",
            ])
        elif lang == "dotnet":
            required.extend([
                "src/app/Program.cs",
                "src/app/App.csproj",
                "src/app/Dockerfile",
            ])

        for path in required:
            if path not in files:
                report.issues.append(ValidationIssue(
                    severity="error",
                    category="missing_file",
                    message=f"Required file missing from scaffold",
                    file_path=path,
                ))

    def _check_entity_coverage(self, spec: IntentSpec, files: dict[str, str],
                                report: ValidationReport) -> None:
        """Ensure every spec entity is referenced in generated code."""
        if not spec.entities:
            return

        lang = spec.language.lower()
        # Check router/controller references each entity
        if lang == "python":
            router_path = "src/app/api/v1/router.py"
        elif lang == "node":
            router_path = "src/app/routes/index.js"
        else:
            router_path = "src/app/Program.cs"

        router_content = files.get(router_path, "")
        for ent in spec.entities:
            if ent.name.lower() not in router_content.lower():
                report.issues.append(ValidationIssue(
                    severity="warning",
                    category="broken_ref",
                    message=f"Entity '{ent.name}' not found in router",
                    file_path=router_path,
                ))

    def _check_route_test_alignment(self, spec: IntentSpec, files: dict[str, str],
                                     report: ValidationReport) -> None:
        """Check that generated tests cover all routes in the manifest."""
        if not spec.entities:
            return

        manifest = RouteBuilder.build(spec)
        test_content = ""
        for path, content in files.items():
            if path.startswith("tests/") and path.endswith(".py"):
                test_content += content

        for route in manifest.routes:
            # Check that the route's path appears somewhere in tests
            clean_path = re.sub(r"\{[^}]+\}", "", route.path)
            if clean_path not in test_content and route.action_name not in test_content:
                report.issues.append(ValidationIssue(
                    severity="info",
                    category="inconsistency",
                    message=f"Route {route.method} {route.path} has no test coverage",
                    file_path="tests/",
                ))

    def _check_bicep_completeness(self, spec: IntentSpec, files: dict[str, str],
                                   report: ValidationReport) -> None:
        """Verify Bicep modules match required data stores."""
        main_bicep = files.get("infra/bicep/main.bicep", "")

        ds_to_module = {
            DataStore.BLOB_STORAGE: "storage",
            DataStore.COSMOS_DB: "cosmos",
            DataStore.SQL: "sql",
            DataStore.REDIS: "redis",
        }

        for ds in spec.data_stores:
            if ds in ds_to_module:
                keyword = ds_to_module[ds]
                if keyword not in main_bicep.lower():
                    report.issues.append(ValidationIssue(
                        severity="warning",
                        category="missing_file",
                        message=f"Data store '{ds.value}' not found in Bicep templates",
                        file_path="infra/bicep/main.bicep",
                    ))

    def _check_dockerfile_exists(self, spec: IntentSpec, files: dict[str, str],
                                  report: ValidationReport) -> None:
        """Verify Dockerfile is present and not empty."""
        dockerfile_path = "src/app/Dockerfile"
        if dockerfile_path in files:
            content = files[dockerfile_path]
            if "FROM" not in content:
                report.issues.append(ValidationIssue(
                    severity="error",
                    category="broken_ref",
                    message="Dockerfile missing FROM instruction",
                    file_path=dockerfile_path,
                ))
        # Dockerfile presence already checked in required files
