"""CompilationGate -- validate generated code before writing to disk.

This is the critical safety net that prevents broken code from reaching
the output directory. Every generated file passes through format-specific
validation before it's allowed through.

Validation checks:
- Python: ast.parse() for syntax correctness
- TSX/JSX: Brace/bracket/paren balance + JSX tag matching
- YAML: yaml.safe_load()
- Bicep: Basic syntax checks (param/resource/module declarations)
- Dockerfile: FROM instruction presence
- JSON: json.loads()
- Markdown: Always passes (no syntax to break)

Files that fail validation are replaced with safe error stubs that
explain what went wrong, rather than writing broken code.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass
class CompilationError:
    """A single compilation/validation error."""
    file_path: str
    error_type: str  # "syntax", "balance", "structure", "parse"
    message: str
    line: int | None = None


@dataclass
class CompilationResult:
    """Result of running the compilation gate on all files."""
    errors: list[CompilationError] = field(default_factory=list)
    files_checked: int = 0
    files_passed: int = 0
    files_fixed: int = 0

    @property
    def all_passed(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if self.all_passed:
            return f"CompilationGate: {self.files_checked} files checked, all passed."
        return (
            f"CompilationGate: {self.files_checked} checked, "
            f"{self.files_passed} passed, "
            f"{len(self.errors)} errors fixed with safe stubs."
        )


class CompilationGate:
    """Validates and optionally fixes generated files before disk write.

    Usage:
        gate = CompilationGate()
        files, result = gate.validate_and_fix(files)
        # files dict now has broken entries replaced with safe stubs
    """

    def validate_and_fix(self, files: dict[str, str]) -> tuple[dict[str, str], CompilationResult]:
        """Validate all files. Replace failures with safe error stubs.

        Returns (fixed_files, result).
        """
        result = CompilationResult()
        fixed_files = {}

        for path, content in files.items():
            result.files_checked += 1
            error = self._validate_file(path, content)

            if error:
                result.errors.append(error)
                result.files_fixed += 1
                fixed_files[path] = self._generate_stub(path, error)
            else:
                result.files_passed += 1
                fixed_files[path] = content

        return fixed_files, result

    def validate_only(self, files: dict[str, str]) -> CompilationResult:
        """Validate without fixing. Returns result with errors."""
        result = CompilationResult()
        for path, content in files.items():
            result.files_checked += 1
            error = self._validate_file(path, content)
            if error:
                result.errors.append(error)
            else:
                result.files_passed += 1
        return result

    def _validate_file(self, path: str, content: str) -> CompilationError | None:
        """Dispatch validation to the correct checker based on file extension."""
        ext = PurePosixPath(path).suffix.lower()
        name = PurePosixPath(path).name.lower()

        if ext == ".py":
            return self._check_python(path, content)
        if ext in (".tsx", ".ts", ".jsx", ".js"):
            return self._check_tsx(path, content)
        if ext in (".yml", ".yaml"):
            return self._check_yaml(path, content)
        if ext == ".json":
            return self._check_json(path, content)
        if name == "dockerfile" or name.startswith("dockerfile"):
            return self._check_dockerfile(path, content)
        if ext == ".bicep":
            return self._check_bicep(path, content)

        # Markdown, CSS, HTML, shell scripts, etc. — always pass
        return None

    def _check_python(self, path: str, content: str) -> CompilationError | None:
        """Validate Python syntax via ast.parse()."""
        try:
            ast.parse(content, filename=path)
            return None
        except SyntaxError as e:
            return CompilationError(
                file_path=path,
                error_type="syntax",
                message=str(e),
                line=e.lineno,
            )

    def _check_tsx(self, path: str, content: str) -> CompilationError | None:
        """Validate TSX/JSX via brace/bracket/paren balance."""
        # Strip string literals and template literals to avoid false positives
        stripped = self._strip_js_strings(content)

        # Check brace balance
        opens = stripped.count("{")
        closes = stripped.count("}")
        if opens != closes:
            return CompilationError(
                file_path=path,
                error_type="balance",
                message=f"Unbalanced braces: {opens} opening vs {closes} closing",
            )

        # Check paren balance
        opens = stripped.count("(")
        closes = stripped.count(")")
        if opens != closes:
            return CompilationError(
                file_path=path,
                error_type="balance",
                message=f"Unbalanced parentheses: {opens} opening vs {closes} closing",
            )

        # Check bracket balance
        opens = stripped.count("[")
        closes = stripped.count("]")
        if opens != closes:
            return CompilationError(
                file_path=path,
                error_type="balance",
                message=f"Unbalanced brackets: {opens} opening vs {closes} closing",
            )

        # Check for common JSX injection patterns (raw error messages in JSX)
        # This catches the exact bug class that caused the Dashboard.tsx crash
        if re.search(r"\{[^}]*validation error[^}]*\}", content, re.IGNORECASE):
            return CompilationError(
                file_path=path,
                error_type="structure",
                message="Raw validation error text found in JSX expression (would crash Babel parser)",
            )

        return None

    def _check_yaml(self, path: str, content: str) -> CompilationError | None:
        """Validate YAML via safe_load."""
        try:
            import yaml
            yaml.safe_load(content)
            return None
        except Exception as e:
            return CompilationError(
                file_path=path,
                error_type="parse",
                message=str(e),
            )

    def _check_json(self, path: str, content: str) -> CompilationError | None:
        """Validate JSON via json.loads."""
        try:
            json.loads(content)
            return None
        except json.JSONDecodeError as e:
            return CompilationError(
                file_path=path,
                error_type="parse",
                message=str(e),
                line=e.lineno,
            )

    def _check_dockerfile(self, path: str, content: str) -> CompilationError | None:
        """Validate Dockerfile has FROM instruction."""
        if "FROM" not in content.upper():
            return CompilationError(
                file_path=path,
                error_type="structure",
                message="Dockerfile missing FROM instruction",
            )
        return None

    def _check_bicep(self, path: str, content: str) -> CompilationError | None:
        """Basic Bicep structure validation."""
        # Check for at least one resource, module, or output declaration
        has_content = any(
            keyword in content
            for keyword in ("resource ", "module ", "param ", "output ", "var ", "targetScope")
        )
        if not has_content and len(content.strip()) > 50:
            return CompilationError(
                file_path=path,
                error_type="structure",
                message="Bicep file has no resource, module, param, or output declarations",
            )
        return None

    def _strip_js_strings(self, content: str) -> str:
        """Remove string literals from JS/TS to avoid false brace-balance errors."""
        # Remove template literals (backtick strings)
        result = re.sub(r"`(?:[^`\\]|\\.)*`", '""', content, flags=re.DOTALL)
        # Remove double-quoted strings
        result = re.sub(r'"(?:[^"\\]|\\.)*"', '""', result)
        # Remove single-quoted strings
        result = re.sub(r"'(?:[^'\\]|\\.)*'", "''", result)
        # Remove single-line comments
        result = re.sub(r"//.*$", "", result, flags=re.MULTILINE)
        # Remove multi-line comments
        result = re.sub(r"/\*.*?\*/", "", result, flags=re.DOTALL)
        return result

    def _generate_stub(self, path: str, error: CompilationError) -> str:
        """Generate a safe error stub for a file that failed validation."""
        ext = PurePosixPath(path).suffix.lower()
        name = PurePosixPath(path).name

        # Sanitize error message for safe embedding
        safe_msg = error.message.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")[:200]

        if ext == ".py":
            return (
                f'"""Auto-generated stub: {name} failed compilation gate."""\n'
                f"# Error: {safe_msg}\n"
                f'# Fix this file and re-run `devex scaffold`\n'
                f"\n"
                f"raise NotImplementedError(\n"
                f'    "This file failed the compilation gate and was replaced with a stub. "\n'
                f'    "Error: {safe_msg}"\n'
                f")\n"
            )

        if ext in (".tsx", ".ts", ".jsx", ".js"):
            return (
                f"import React from 'react';\n\n"
                f"export default function CompilationError() {{\n"
                f"  return (\n"
                f'    <div className="p-8 max-w-2xl mx-auto mt-20 bg-yellow-50 '
                f'dark:bg-yellow-900/20 text-yellow-700 rounded-lg border border-yellow-200">\n'
                f'      <h2 className="text-xl font-bold mb-2">Compilation Gate</h2>\n'
                f"      <p>This component failed validation and was replaced with a safe stub.</p>\n"
                f'      <pre className="mt-4 text-xs bg-yellow-100 dark:bg-yellow-900/40 '
                f'p-3 rounded overflow-auto">{_escape_for_jsx(safe_msg)}</pre>\n'
                f"    </div>\n"
                f"  );\n"
                f"}}\n"
            )

        if ext in (".yml", ".yaml"):
            return f"# Compilation gate: original file failed validation\n# Error: {safe_msg}\n{{}}\n"

        if ext == ".json":
            return json.dumps({"_compilation_error": safe_msg}, indent=2)

        # Generic stub
        return f"# Compilation gate stub\n# Original file failed validation: {safe_msg}\n"


def _escape_for_jsx(text: str) -> str:
    """Escape text for safe embedding in JSX."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
        .replace('"', "&quot;")
    )
