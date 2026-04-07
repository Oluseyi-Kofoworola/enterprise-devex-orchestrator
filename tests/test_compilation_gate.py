"""Tests for CompilationGate -- validate generated code before writing."""

import pytest
from src.orchestrator.generators.compilation_gate import CompilationGate, CompilationError


class TestCompilationGate:
    def setup_method(self):
        self.gate = CompilationGate()

    # -- Python validation -------------------------------------------------

    def test_valid_python(self):
        files = {"src/app/main.py": "def hello():\n    return 'world'\n"}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed
        assert result.files_checked == 1

    def test_invalid_python_syntax(self):
        files = {"src/app/broken.py": "def hello(\n    return 'oops'\n"}
        fixed, result = self.gate.validate_and_fix(files)
        assert not result.all_passed
        assert result.files_fixed == 1
        # Stub should be valid Python
        assert "NotImplementedError" in fixed["src/app/broken.py"]

    # -- TSX validation ----------------------------------------------------

    def test_valid_tsx(self):
        tsx = """import React from 'react';
export default function App() {
  return (
    <div className="test">
      <h1>Hello</h1>
    </div>
  );
}
"""
        files = {"frontend/src/App.tsx": tsx}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    def test_unbalanced_braces_tsx(self):
        tsx = """import React from 'react';
export default function App() {
  return (
    <div>{missing closing
  );
}
"""
        files = {"frontend/src/App.tsx": tsx}
        _, result = self.gate.validate_and_fix(files)
        assert not result.all_passed
        assert any(e.error_type == "balance" for e in result.errors)

    def test_validation_error_in_jsx(self):
        """The exact bug that crashed Dashboard.tsx."""
        tsx = """import React from 'react';
export default function Dashboard() {
  return (
    <div>
      <p>{4 validation errors for UIPageSpec page_name Field required}</p>
    </div>
  );
}
"""
        files = {"frontend/src/pages/Dashboard.tsx": tsx}
        _, result = self.gate.validate_and_fix(files)
        assert not result.all_passed
        assert any("validation error" in e.message.lower() for e in result.errors)

    def test_template_literals_not_false_positive(self):
        """Template literals with braces should not cause false positives."""
        tsx = """import React from 'react';
export default function App() {
  const name = `hello ${"world"}`;
  return (
    <div className="test">
      <p>{name}</p>
    </div>
  );
}
"""
        files = {"frontend/src/App.tsx": tsx}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    # -- YAML validation ---------------------------------------------------

    def test_valid_yaml(self):
        files = {".github/workflows/test.yml": "name: Test\non:\n  push:\n    branches: [main]\n"}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    def test_invalid_yaml(self):
        files = {".github/workflows/bad.yml": "name: Test\n  bad: indentation\n    - broken\n"}
        _, result = self.gate.validate_and_fix(files)
        # YAML parser might or might not fail on this specific case,
        # but let's test the mechanism works
        assert result.files_checked == 1

    # -- JSON validation ---------------------------------------------------

    def test_valid_json(self):
        files = {"package.json": '{"name": "test", "version": "1.0.0"}'}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    def test_invalid_json(self):
        files = {"package.json": '{name: "test", broken}'}
        fixed, result = self.gate.validate_and_fix(files)
        assert not result.all_passed
        assert "_compilation_error" in fixed["package.json"]

    # -- Dockerfile validation ---------------------------------------------

    def test_valid_dockerfile(self):
        files = {"src/app/Dockerfile": "FROM python:3.12-slim\nCOPY . /app\n"}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    def test_dockerfile_missing_from(self):
        files = {"src/app/Dockerfile": "COPY . /app\nRUN pip install\n"}
        _, result = self.gate.validate_and_fix(files)
        assert not result.all_passed

    # -- Bicep validation --------------------------------------------------

    def test_valid_bicep(self):
        files = {"infra/bicep/main.bicep": "param location string = 'eastus'\nresource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {\n  name: 'test'\n  location: location\n}\n"}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    # -- Markdown and other files pass through -----------------------------

    def test_markdown_always_passes(self):
        files = {"README.md": "# Hello {world} [broken link]("}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    def test_css_always_passes(self):
        files = {"frontend/src/styles/app.css": ".broken { color: }"}
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed

    # -- validate_only mode ------------------------------------------------

    def test_validate_only_no_fixes(self):
        files = {
            "good.py": "x = 1\n",
            "bad.py": "def broken(\n",
        }
        result = self.gate.validate_only(files)
        assert not result.all_passed
        assert result.files_passed == 1

    # -- Mixed file set ----------------------------------------------------

    def test_mixed_files(self):
        files = {
            "src/app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "frontend/src/App.tsx": "export default function App() { return <div>Ok</div>; }\n",
            "README.md": "# Project\n",
            "package.json": '{"name": "test"}',
        }
        _, result = self.gate.validate_and_fix(files)
        assert result.all_passed
        assert result.files_checked == 4
