# Demo Script — Senior Engineering Team Presentation

> **Enterprise DevEx Orchestrator** — 15-minute demonstration
> Audience: Senior Developer Engineers
> Shows: architecture deep-dive, live scaffold generation, working dashboard, enterprise standards, extensibility, and collaboration opportunities

---

## Pre-Demo Setup Checklist

```powershell
# Ensure orchestrator is installed and venv activated
cd enterprise-devex-orchestrator
.venv\Scripts\Activate.ps1
devex version        # Shows provider: GitHub Copilot SDK (default)
devex providers      # Lists all supported providers and models

# Pre-generate a scaffold for backup (in case live demo fails)
devex scaffold --file examples/metro-command-intent.md -o ./demo-backup

# Have 3 terminals ready:
# Terminal 1: CLI commands
# Terminal 2: Backend API (uvicorn)
# Terminal 3: Frontend (npm run dev)
```

---

## Segment 1: The Problem We Solve (1 min)

**Say:** "How long does it take your team to go from 'we need a new service' to a deployable, governance-compliant scaffold with Bicep IaC, CI/CD, threat model, WAF alignment, and a working API? Typically 6-12 weeks."

| Traditional Task | Time |
|---|---|
| Bicep templates + naming + tagging | 2-4 weeks |
| CI/CD pipelines with OIDC | 1-2 weeks |
| Governance review + WAF assessment | 1 week |
| Dashboard + API scaffolding | 3-5 days |
| Security review + threat model | 2-3 days |
| Documentation | 1-2 days |
| **Total** | **6-12 weeks** |

**Say:** "What if all of that was generated in 5-10 seconds, passing 25 governance policies and 26 WAF principles automatically? That's what this orchestrator does."

---

## Segment 2: Architecture Deep-Dive (2 min)

**Say:** "The system uses a 4-agent chain architecture. Each agent has a distinct role, instruction set, and tool access."

```
User Intent → Intent Parser → Architecture Planner → Governance Reviewer → Infrastructure Generator
                                       ↑                    |
                                       └── Fail (remediate) ─┘
```

Walk through each agent:

1. **Intent Parser** — 5-phase semantic extraction engine. Discovers entities, fields, endpoints from natural language. No hardcoded templates. Handles up to 20 entities with 25 fields each. 10+ field type aliases, safe singular/plural normalization.

2. **Architecture Planner** — Selects Azure services, writes 6 ADRs, produces a STRIDE threat model, generates a Mermaid architecture diagram.

3. **Governance Reviewer** — Validates the plan against 25 enterprise policies + 26 WAF design principles across 5 pillars. If it fails, feedback loops back to the planner (max 2 iterations). **No scaffold ships without passing governance.**

4. **Infrastructure Generator** — Dispatches to 9 sub-generators via the Generator Plugin Protocol. Uses `GeneratorRegistry` with priority ordering — adding a new generator is one `register()` call (Open-Closed Principle).

**Say:** "The key design decision: governance is not optional. It's a hard gate in the pipeline."

---

## Segment 3: Live Scaffold Generation (3 min)

### Show the intent file

```powershell
# Terminal 1
Get-Content examples/intent.md | Select-Object -First 30
```

**Say:** "This is a plain-English description of an AI voice agent platform. The parser will semantically extract entities like Patient, VoiceSession, Provider, Equipment."

### Generate the scaffold

```powershell
devex scaffold --file examples/intent.md -o ./live-demo
```

**Say:** "~5-10 seconds. Let's look at what we got."

### Walk through key artifacts

```powershell
# File count
Get-ChildItem -Recurse ./live-demo -File | Measure-Object

# Bicep modules (infra as code)
Get-ChildItem ./live-demo/infra/bicep/modules/

# CI/CD — 4 GitHub Actions workflows
Get-ChildItem ./live-demo/.github/workflows/

# Backend — entity-driven FastAPI services
Get-ChildItem ./live-demo/src/app/services/

# Frontend — React SPA dashboard pages
Get-ChildItem ./live-demo/frontend/src/pages/

# Tests — auto-generated with RouteManifest alignment
Get-ChildItem ./live-demo/tests/

# Governance report
Get-Content ./live-demo/docs/governance-report.md | Select-Object -First 30

# WAF report — 26 principles across 5 pillars
Get-Content ./live-demo/docs/waf-report.md | Select-Object -First 30
```

**Say:** "Every entity discovered from the intent gets a full vertical slice: Pydantic model, repository, service, API routes, seed data, frontend page, tests, and Bicep resources."

---

## Segment 4: Live Dashboard Demo (3 min)

### Start the backend API

```powershell
# Terminal 2
cd live-demo/src/app
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Say:** "The backend starts with in-memory storage and 12 realistic seed records per entity — domain-aware names, addresses, timestamps. No database required."

**Open browser:** `http://127.0.0.1:8000/docs`

**Say:** "Auto-generated Swagger/OpenAPI docs. All entities, all CRUD endpoints, plus domain-specific actions like triage, escalate, dispatch."

### Start the frontend

```powershell
# Terminal 3
cd live-demo/frontend
npm install
npm run dev
```

**Open browser:** `http://localhost:3000`

### Walk through the dashboard

| Feature | What to show |
|---|---|
| **Summary bar** | Total records, active count, entities, items needing attention |
| **Entity KPI cards** | Donut charts showing status distribution |
| **Data table** | Smart column selection (5-7 key columns), type-aware rendering (badges, dates, progress bars) |
| **Status filters** | Click filter pills above the table |
| **Create record** | Click "+", fill type-aware modal, submit |
| **Detail page** | Click a row — grouped field sections, breadcrumb nav, action buttons |
| **Dark mode** | Toggle in the header |
| **CSV export** | Download icon |
| **AI chat** | Open chat panel — 11 intent handlers work locally with no AI provider |

**Say:** "This is not a mockup. It's generated code talking to a generated API with generated seed data. The same code deploys to Azure Container Apps unchanged."

---

## Segment 5: Enterprise Standards (2 min)

### Show Bicep naming

```powershell
Select-String "name:" ./live-demo/infra/bicep/main.bicep | Select-Object -First 10
```

**Say:** "Azure CAF naming conventions — 22 resource types, 34 region abbreviations. Passes naming audits on first review."

### Show security layers

| Layer | What's generated |
|---|---|
| Identity | Managed Identity — zero credentials in code |
| Secrets | Key Vault with RBAC, soft-delete, purge protection |
| Transport | HTTPS-only, TLS 1.2+ |
| Container | Non-root Docker user, read-only filesystem |
| Registry | ACR with AcrPull — no admin credentials |
| CI/CD | OIDC federation — no stored secrets |
| Input | Pydantic validation at all API boundaries |
| Governance | STRIDE threat model + 25 policies |

**Say:** "These aren't optional flags — they're baked into every scaffold. You cannot generate an insecure scaffold."

### Show configurable standards

```powershell
Get-Content standards.yaml | Select-Object -First 30
```

**Say:** "Organizations can override naming, tagging, and governance rules with their own `standards.yaml` via `--standards`."

---

## Segment 6: Domain Versatility (1.5 min)

**Say:** "This isn't a healthcare-specific tool. The same engine handles any business domain."

| Intent | Entities | Data Stores | Time |
|---|---|---|---|
| AI Voice Agent (12 entities) | Patient, VoiceSession, Provider + 9 more | Cosmos, SQL, Blob, Redis, Table | ~10s |
| Smart City IoT (9 entities) | Sensor, Incident, Route + 6 more | All 6 data stores | ~5s |
| Metro Command (14 entities) | Incident, Asset, Vehicle, Zone + 10 more | All 6, 8 AI agents | ~5s |
| Global Supply Chain (15 entities) | Supplier, Shipment, RiskAssessment + 12 more | Cosmos, SQL, Redis, Blob, Table | ~5s |
| Legal Contract Review | Contract, Clause, ReviewResult | Blob, Cosmos | ~5s |
| Propane Delivery | Delivery, Tank, Route, Customer | Cosmos | ~5s |

**Say:** "Write about propane delivery and you get `Tank`, `Delivery`, `Route` entities with `serial_number`, `capacity`, `level` fields. Write about pet adoption and you get `Animal`, `Application`, `FosterHome`. The 5-phase semantic extraction pipeline reads your intent and infers the domain model."

### AI workloads auto-detected

**Say:** "Mention AI, RAG, or agents in your intent, and you automatically get Azure OpenAI Bicep modules, Semantic Kernel agent scaffolds, a chat frontend, plus 5 additional AI governance policies."

---

## Segment 7: Extensibility for Engineers (1.5 min)

**Say:** "Let me show you the parts that matter for contributing."

### Generator Plugin Protocol

```python
# Adding a new generator — ONE line in create_default_registry()
registry.register("my-gen", GeneratorAdapter(MyGenerator(), _bridge_spec_only), priority=85)
```

**Say:** "Open-Closed Principle. 9 generators today – adding a 10th requires zero changes to the agent."

### Key extension points

| Extension Point | File | What to add |
|---|---|---|
| New generator | `src/orchestrator/generators/protocol.py` | `registry.register()` |
| New governance policy | `src/orchestrator/tools/policy_engine.py` | Add to policy catalog |
| New domain context | `src/orchestrator/generators/domain_context.py` | New `DomainDefinition` |
| New design theme | `src/orchestrator/generators/design_system.py` | New industry preset |
| New skill | `src/orchestrator/skills/registry.py` | `SkillDefinition` + register |
| New CLI command | `src/orchestrator/main.py` | Typer command |
| Custom standards | `standards.yaml` | YAML config |

### Test suite

```powershell
pytest tests/ -v --tb=short 2>&1 | Select-Object -Last 5
# 880 passed
```

**Say:** "880 tests across 25 test files. Every generator, every agent, every governance rule is tested. RouteManifest ensures test-route alignment — add an entity, tests generate automatically."

---

## Segment 8: Collaboration Opportunities (1.5 min)

**Say:** "Here's where this gets interesting with your involvement."

| Area | Current State | Collaboration Opportunity |
|---|---|---|
| **Language support** | Python (FastAPI) primary | Full-stack Node.js (Express/NestJS), .NET (ASP.NET Core) generators |
| **Database migrations** | In-memory storage + seed data | Alembic/Prisma migration generators from EntitySpec → real DB schemas |
| **Multi-cloud** | Azure-only (Bicep) | Terraform generator for AWS/GCP via Plugin Protocol |
| **GitOps** | GitHub Actions only | ArgoCD/Flux manifests, Kubernetes Helm charts |
| **Observability** | Azure Monitor + Log Analytics | OpenTelemetry instrumentation, Grafana dashboards |
| **AI agents** | Semantic Kernel scaffolds | LangChain/CrewAI/AutoGen support |
| **Testing** | Pytest CRUD + E2E | Load testing (Locust/k6), contract testing (Pact) |
| **Frontend** | React + Vite + TypeScript | Vue/Svelte/Angular generators, Storybook |
| **Schema evolution** | Version tracking with `devex upgrade` | Auto backward-compatible API versioning |
| **Compliance** | SOC2, HIPAA, PCI, FedRAMP | Auto-generate compliance evidence artifacts |

### Quick wins for first contributors

1. **Add a new domain context** — One Python dataclass in `domain_context.py` gives every scaffold domain-aware seed data for a new industry
2. **Add a governance policy** — One entry in the policy catalog gives every scaffold a new compliance check
3. **Improve an existing generator** — Each generator is isolated with its own `generate()` method
4. **Add an example intent** — Write a new `examples/*.md` file to showcase a new domain

---

## Closing (30 sec)

**Say:** "To recap: one plain-English description produces a complete enterprise application — Bicep infrastructure, FastAPI backend, React dashboard, CI/CD pipelines, 880+ governance checks, WAF alignment, threat model, tests, and documentation. In 5-10 seconds. The same scaffold runs locally and deploys to Azure unchanged."

"The codebase is designed for extension — Plugin Protocol for generators, pluggable skills, configurable standards. Try it yourself:"

```powershell
pip install -e ".[dev]"
devex scaffold --file examples/metro-command-intent.md -o ./metro-demo
cd metro-demo/src/app && uvicorn main:app --port 8000 --reload
```

"Questions?"

---

## Backup Plan

If live demo fails:

1. Use pre-generated scaffold directory already in the workspace
2. Show file tree + governance report + WAF report from existing output
3. Run `pytest tests/ -v` to demonstrate test suite (no Azure needed)
4. Walk through `docs/governance-report.md` and `docs/waf-report.md`

---

*Full pipeline: intent → parse → plan → govern → generate → deploy*
*880 tests | 25 policies | 26 WAF principles | 12 CLI commands*
*Multi-provider LLM: GitHub Copilot SDK (default) · Azure OpenAI · OpenAI · Anthropic (Claude)*
*9 generators | 12 domain contexts | 10 design themes*
*Full-stack: Python (FastAPI) + React 18 + Vite 5 + TypeScript + Azure Bicep*
*Enterprise DevEx Orchestrator v2.2.0*


