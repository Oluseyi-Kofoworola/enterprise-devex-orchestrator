# Enterprise DevEx Orchestrator

Transform business intent into production-ready Azure solutions using a repeatable, intent-first workflow.

## What This Repository Is

This project is a CLI-driven orchestration framework that takes either:
- An inline business intent string, or
- A structured intent markdown file,

and generates a complete enterprise scaffold:
- Azure Bicep infrastructure
- Application scaffold
- CI/CD workflows
- Tests
- Governance and WAF reports
- Operations documentation

It is designed for iterative enterprise delivery:
1. Define intent
2. Scaffold
3. Review governance and improvement suggestions
4. Upgrade from a new intent version

## New User Starting Point

If you just cloned this repo, start in this order:
1. Follow [QUICKSTART.md](QUICKSTART.md)
2. Run `devex --help`
3. Scaffold from an example intent in [examples](examples)
4. Generate your own `intent.md` with `devex init`

## Prerequisites

- Python 3.11+
- PowerShell (Windows) or a Unix shell
- Git
- Optional for deployment: Azure CLI (`az`) and active Azure subscription

## Installation

```powershell
git clone https://github.com/Oluseyi-Kofoworola/enterprise-devex-orchestrator.git
cd enterprise-devex-orchestrator

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

Verify:

```powershell
devex --help
devex version
```

## Intent-First Workflow

### 1) Plan without writing files

```powershell
devex plan --file examples/intent.md
```

### 2) Generate scaffold

```powershell
devex scaffold --file examples/intent.md -o ./my-project
```

### 3) Validate generated scaffold

```powershell
devex validate ./my-project
```

### 4) Iterate with versioned intent

```powershell
devex new-version ./my-project
# edit ./my-project/intent.v2.md
devex upgrade --file ./my-project/intent.v2.md -o ./my-project
devex history ./my-project
```

## Example Intents

Ready-to-run examples are in [examples](examples):
- [examples/intent.md](examples/intent.md)
- [examples/intent.v2.md](examples/intent.v2.md)
- [examples/contract-review-intent.md](examples/contract-review-intent.md)
- [examples/doc-intelligence-intent.md](examples/doc-intelligence-intent.md)

## Output Structure (Generated)

Each scaffold output contains:
- `.devex/` metadata and versioning state
- `.github/workflows/` CI/CD pipelines
- `infra/bicep/` deployable infrastructure
- `src/app/` generated application scaffold
- `tests/` generated validation tests
- `docs/` architecture, governance, WAF, deployment, and operations docs

## Deploy to Azure (Optional)

```powershell
az login
az group create --name rg-my-project-dev --location eastus2
devex deploy ./my-project -g rg-my-project-dev -r eastus2
```

For a safe preview:

```powershell
devex deploy ./my-project -g rg-my-project-dev -r eastus2 --dry-run
```

## CLI Command Reference

- `devex init` - Create a structured `intent.md` template
- `devex plan` - Parse and plan architecture without generating scaffold files
- `devex scaffold` - Run full pipeline and generate scaffold
- `devex validate` - Validate a generated scaffold against governance checks
- `devex deploy` - Deploy generated Bicep to Azure (staged deployment)
- `devex upgrade` - Upgrade an existing scaffold with a versioned intent file
- `devex history` - Show scaffold version history
- `devex new-version` - Create next intent template from existing output
- `devex version` - Show CLI and runtime details

## Testing and Quality Checks

```powershell
pytest tests/ -q
ruff check src/ tests/
mypy src/orchestrator/
```

## Notes for Contributors

- Keep the repository source clean. Treat generated folders as disposable outputs.
- Reuse and version intent files in [examples](examples) rather than committing large generated outputs.
- If you add new orchestration behavior, update both this file and [QUICKSTART.md](QUICKSTART.md).

## License

MIT
| `devex version` | Show orchestrator version info |

---

## Project Structure

```
src/orchestrator/
    agent.py              # 4-agent chain
    config.py             # Configuration management
    intent_file.py        # Markdown intent file parser (9 enterprise sections)
    intent_schema.py      # Pydantic schemas
    main.py               # CLI entrypoint (8 commands)
    state.py              # State management + drift detection
    versioning.py         # Version tracking + upgrade + rollback
    agents/
        deploy_orchestrator.py   # 4-stage Azure deployment
        subagent_dispatcher.py   # Parallel subagent fan-out
    generators/
        infra.py          # BicepGenerator (7 modules)
        cicd.py           # CICDGenerator (4 workflows)
        app.py            # AppGenerator (FastAPI + Docker)
        docs.py           # DocsGenerator (7 doc files)
        tests.py          # TestGenerator (5 test files)
        alerts.py         # AlertGenerator (Bicep alerts + runbook)
    planning/
        __init__.py       # Persistent planner (13-task DAG)
    prompts/
        generator.py      # Repo-aware prompt generation
    skills/
        registry.py       # Skills registry (9 skills, 12 categories)
    standards/
        __init__.py       # NamingEngine + TaggingEngine
    tools/
        azure.py          # Azure validation tools
        governance.py     # Policy engine tools
        generation.py     # Template rendering tools

tests/                    # 486 tests across 14 files
infra/bicep/              # Bicep IaC templates
standards.yaml            # Enterprise standards configuration
```

---

## Testing

486 tests across 14 test files:

| Test File | Tests | Coverage |
|-----------|-------|---------|
| `test_standards.py` | 67 | Azure CAF naming (20 types), tagging (7+5 tags) |
| `test_waf.py` | 61 | WAF 5-pillar assessment, 26 principles |
| `test_enterprise_features.py` | 37 | Enterprise intent model, completeness tracking |
| `test_state.py` | 37 | State management, SHA-256 manifest, drift detection |
| `test_intent_versioning.py` | 33 | Intent files, version tracking, CI/CD promotion |
| `test_skills_registry.py` | 26 | 9 skills, dynamic discovery, priority routing |
| `test_superpowers.py` | 24 | Test/alert/deploy generators |
| `test_planning.py` | 22 | 13-task DAG, checkpoints, resume |
| `test_deploy_orchestrator.py` | 19 | 4-stage deploy, error recovery |
| `test_prompt_generator.py` | 18 | Repo scanning, context-enriched prompts |
| `test_subagent_dispatcher.py` | 17 | Parallel fan-out, result aggregation |
| (+ 3 more) | 123+ | Intent parsing, generators, governance |

```bash
pytest tests/ -v  # All 486 tests should pass
```

---

## Security

- **Managed Identity** for all service-to-service auth (no credentials in code)
- **Key Vault** with RBAC access, soft-delete, purge protection
- **HTTPS-only** with TLS 1.2+ enforcement
- **Non-root containers** with read-only filesystem
- **OIDC** for CI/CD (no stored secrets)
- **Pydantic validation** on all API inputs
- **STRIDE threat model** generated for every scaffold
- **25 governance policies** validated automatically

---

## Examples

See [`examples/`](examples/README.md) for production-ready applications built with this orchestrator:

| Example | Description | Deploy Time | Cost (Dev) |
|---------|-------------|-------------|------------|
| [SLHS Voice Agent](slhs-voice-agent/) | Voice-enabled patient information system | 12 min | ~$28/month |
| [Contract Review AI](contract-review/) | Legal contract analysis with Document Intelligence + GPT-4-1 | 8 min | ~$120/month |

Both examples include full source code, Bicep IaC, CI/CD, tests, and comprehensive documentation.

---

## Enterprise Guardrails

| Guardrail | Enforcement |
|-----------|------------|
| No secrets in code | Key Vault references only |
| No `:latest` tags | Explicit version tags required |
| No admin credentials | Managed Identity + RBAC |
| No access policies | RBAC over Key Vault access policies |
| Non-root containers | Enforced in Dockerfile |
| OIDC for CI/CD | No stored credentials in workflows |
| CAF naming | NamingEngine validates all resource names |
| Enterprise tags | TaggingEngine validates 7 required tags |
| Diagnostic settings | Log Analytics configured for all resources |
| Threat model | STRIDE analysis required for every scaffold |

---

## What Makes This 0.0001% Engineering

1. **4-agent orchestration** with governance feedback loop -- not a single-agent chatbot
2. **25 automated governance policies** validated on every scaffold -- not best-effort checklists
3. **26/26 WAF principles** scored with evidence -- not hand-waved compliance
4. **486 tests** across 14 files -- not "it works on my machine"
5. **Enterprise standards engine** (naming + tagging + config) -- not ad-hoc conventions
6. **Advanced patterns** (skills, subagents, persistent planning, deploy orchestrator) -- not MVP features
7. **Intent-to-production pipeline** with a single command -- not a 20-step runbook
8. **Versioned upgrades** with improvement suggestions -- not one-shot generation

---

## Documentation

- [`QUICKSTART.md`](QUICKSTART.md) -- Step-by-step installation and testing guide
- [`AGENTS.md`](AGENTS.md) -- Complete agent architecture and tool bindings
- [`examples/README.md`](examples/README.md) -- Production-ready example applications
- [`docs/`](docs/) -- Framework architecture, security, deployment, scorecard

---

## Contributing

Want to extend the orchestrator? See the contribution patterns:

- **Add a new generator** -- Extend `src/orchestrator/generators/`
- **Add a new skill** -- Register in `src/orchestrator/skills/registry.py`
- **Add a new governance policy** -- Update `src/orchestrator/tools/governance.py`
- **Add a new example** -- Follow [`examples/README.md`](examples/README.md#contributing-new-examples)

All changes must:
- Pass `pytest tests/ -v` (486 tests)
- Pass `ruff check src/ tests/`
- Pass `mypy src/orchestrator/`

---

## License

MIT License. See `LICENSE` for details.

---

*Enterprise DevEx Orchestrator v1.1.0*  
*Deployed on Azure Container Apps*  
*486 tests | 25 governance policies | 26 WAF principles | 135/135 scorecard*  
*Enterprise proof-of-concept*



