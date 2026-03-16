# Contributing to Enterprise DevEx Orchestrator

Thank you for your interest in contributing! This guide covers the process for reporting issues, submitting changes, and coding standards.

---

## Getting Started

```powershell
git clone https://github.com/Oluseyi-Kofoworola/enterprise-devex-orchestrator.git
cd enterprise-devex-orchestrator
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # macOS/Linux
pip install -e ".[dev]"
```

Verify everything works:

```powershell
pytest tests/ -v
```

All 636 tests must pass before submitting a PR.

---

## Reporting Issues

1. **Search existing issues** first to avoid duplicates.
2. **Include reproduction steps** — what command you ran, what you expected, what happened.
3. **Include your environment** — Python version, OS, LLM provider (if relevant).
4. **Include generated output** if the issue is in scaffold output — the `.devex/spec.json` file is especially helpful.

---

## Pull Request Process

1. **Fork the repo** and create a feature branch from `main`:
   ```powershell
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** — keep PRs focused. One fix or feature per PR.

3. **Run the full test suite**:
   ```powershell
   pytest tests/ -v
   ```

4. **Test with a real scaffold** to verify your changes work end-to-end:
   ```powershell
   devex scaffold --file examples/intent.md -o ./test-output
   ```

5. **Submit the PR** with a clear description of what changed and why.

---

## Coding Standards

### Python

- **Python 3.11+** required.
- **Type hints** on all function signatures.
- **Pydantic v2** for all data models.
- **No hardcoded secrets** — ever. All secrets go through Key Vault references.
- **Structured logging** via `src/orchestrator/logging.py` — use `get_logger(__name__)`.
- **Snake_case** for variables and functions, **PascalCase** for classes.

### Generators

If you modify a generator (`src/orchestrator/generators/`):

- Run the scaffold and **manually verify the generated output** runs locally.
- Ensure the backend starts: `uvicorn main:app --host 127.0.0.1 --port 8000`
- Ensure the frontend builds: `cd frontend && npm install && npm run dev`
- Check that governance validation passes: `devex validate ./test-output`

### Tests

- All tests live in `tests/`.
- Use `pytest` — no unittest.
- Name test files `test_<module>.py`.
- Name test functions `test_<what_it_tests>`.
- Aim for the test to verify behavior, not implementation details.

---

## Project Structure

```
src/orchestrator/
  agents/          # 4-agent chain (intent parser, planner, reviewer, generator)
  generators/      # 9 code generators (bicep, app, frontend, cicd, docs, tests, alerts, cost, dashboard)
  standards/       # Naming engine, tagging engine, WAF assessor, standards config
  tools/           # MCP tool implementations (policy engine, azure validator, template renderer)
  planning/        # Persistent planner with checkpoint-based execution
  prompts/         # Repo-aware prompt generator
  skills/          # Pluggable skills registry
  config.py        # Multi-provider LLM configuration
  intent_schema.py # IntentSpec Pydantic schema
  main.py          # CLI entrypoint (devex commands)
  state.py         # State management and drift detection
  versioning.py    # Version tracking and rollback
```

---

## Adding a New Generator

1. Create `src/orchestrator/generators/your_generator.py`
2. Implement a class with a `generate(self, spec: IntentSpec) -> dict[str, str]` method
3. Wire it into `src/orchestrator/agents/infra_generator.py`
4. Add tests in `tests/test_generators.py`
5. Update `docs/architecture.md` if the generator adds new output files

---

## Adding a New Governance Policy

1. Add the `PolicyRule` to `src/orchestrator/tools/policy_engine.py` in `POLICY_CATALOG`
2. Add the corresponding check method in `src/orchestrator/agents/governance_reviewer.py`
3. Add tests in `tests/test_governance_validator.py`
4. Update the policy count in documentation (currently 25)

---

## Code of Conduct

Be respectful. Be constructive. Focus on the work, not the person.

---

## Questions?

Open an issue with the `question` label, or reach out via the repo's Discussions tab.

---

*Enterprise DevEx Orchestrator v1.5.0*
