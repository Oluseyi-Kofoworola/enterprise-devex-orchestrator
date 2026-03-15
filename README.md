# Enterprise DevEx Orchestrator

### Describe your business. Get a production-ready Azure app. Powered by GitHub Copilot SDK.

> **One sentence. One command. One fully deployed enterprise application.**
>
> Write what your business does in plain English. The orchestrator -- powered by GitHub Copilot SDK -- understands your intent, extracts your domain entities, and generates a complete, Azure Well-Architected, production-deployable application with infrastructure, CI/CD, tests, security, and a working interactive dashboard. **~5-10 seconds**, not months.

---

## The Problem This Solves

Enterprise teams spend **weeks to months** scaffolding new projects: provisioning Azure infrastructure, writing Bicep templates, configuring CI/CD pipelines, enforcing governance policies, setting up monitoring and alerting, building dashboards, and aligning with the Azure Well-Architected Framework. Most POCs never make it to production because the gap between "demo" and "enterprise-ready" is too wide.

**What if you could skip all of that?**

## The Solution: Intent-Driven Enterprise Scaffolding

```
"Build a smart city IoT platform with sensor monitoring, emergency dispatch,
 and citizen services. Use Cosmos DB, SQL, Redis, and Blob storage.
 Comply with FedRAMP and SOC2."
```

**One command:**

```powershell
devex scaffold --file intent.md -o ./smart-city-output
```

**What you get in ~5-10 seconds (benchmarked):**

> **Measured performance:** Voice agent intent (76 files) in 10s | Contract review (77 files) in 5s | Smart city stress test with 4 data stores + 10 Bicep modules (79 files) in 5s

| Layer | Generated Artifacts | Enterprise Grade |
|-------|-------------------|-----------------|
| **Infrastructure** | 10 Azure Bicep modules, parameterized per environment | Azure CAF naming, 12 enterprise tags |
| **Backend API** | FastAPI with CRUD endpoints, Pydantic schemas, repository pattern | Managed Identity, Key Vault, non-root containers |
| **Interactive Dashboard** | Entity-driven UI with create, update, delete, search, health monitoring | Domain-aware seed data, live status indicators |
| **React Frontend** | TypeScript SPA with API client, entity dashboards, detail pages | Azure-compatible Dockerfile, configurable backend URL |
| **CI/CD** | 4 GitHub Actions workflows (validate, deploy, CodeQL, Dependabot) | OIDC auth -- zero stored credentials |
| **Tests** | 5 auto-generated pytest files per scaffold | Health, API, security, config, storage tests |
| **Governance** | 25-policy validation + STRIDE threat model | Automated compliance evidence |
| **WAF Assessment** | 26 Azure Well-Architected Framework principles scored | 5-pillar coverage with actionable recommendations |
| **Monitoring** | Azure Monitor alert rules + action groups + runbook | Cost estimation included |
| **Documentation** | 7+ files: architecture, security, deployment, ADRs | Auto-generated from your intent |

## Why GitHub Copilot SDK?

The orchestrator is built on **GitHub Copilot SDK** as its default AI backbone -- no API keys, no configuration, no external dependencies. In any Copilot-enabled environment, it just works. This means:

- **Zero-config AI** -- GitHub Copilot SDK auto-detected, no setup required
- **Enterprise-grade LLM** -- Runs on the same trusted infrastructure as GitHub Copilot
- **Fallback resilience** -- When LLM is unavailable, a 5-phase semantic extraction engine takes over with deterministic template generation
- **Multi-provider flexibility** -- Switch to Azure OpenAI, OpenAI, or Anthropic with one env var

## What Makes This Different

Most code generators produce **stubs**. This orchestrator produces **working applications**:

- **Semantic, not keyword-based** -- A 5-phase NLP pipeline (section-header analysis, noun-phrase extraction, business-object pattern matching, merge/rank, EntitySpec building) reads your intent and discovers domain entities, infers field types, and generates appropriate API routes. Handles up to **20 entities** with **25 fields each**, safe singular/plural normalization (preserves "status", "address", "class"), multi-parameter endpoint paths, 10+ field type aliases (string→str, integer→int, boolean→bool, timestamp→datetime), and 45 heading name aliases for flexible intent file formatting. Write about *propane delivery* and get `Tank`, `Delivery`, `Route` entities with `serial_number`, `capacity`, `level` fields. Write about *pet adoption* and get `Animal`, `Application`, `FosterHome` with `breed`, `age`, `medical_status`.
- **Interactive dashboards** -- Every scaffold includes a fully functional dashboard where you can create records, update statuses via action buttons, search, and monitor health -- not a static landing page.
- **Smart AI chatbot** -- 11 intent handlers (greeting, help, temporal, cross-entity comparison, recommendation, count, analytics, list, filter, action, status) with HTML-formatted responses, stat cards, bar charts, and data-driven suggestions. Works without any AI provider -- pure Python analysis on 12 realistic seed records per entity.
- **Domain-aware seed data** -- 12 records per entity with contextually appropriate values from 15+ realistic name pools. Smart city sensors get GPS coordinates and zone IDs, not "item-001".
- **Enterprise governance by default** -- 25 policies validated automatically. No scaffold ships without passing governance.
- **Azure Well-Architected from day one** -- Every scaffold is assessed against all 26 WAF design principles across 5 pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency).
- **POC to production in one pipeline** -- The same scaffold you demo locally deploys to Azure Container Apps unchanged. No rework.

---

## Quick Demo: 3 Commands, Production-Ready App

```powershell
# 1. Install (once)
pip install -e ".[dev]"

# 2. Generate a complete enterprise scaffold from your business intent
devex scaffold --file examples/smart-city-intent.md -o ./smart-city-output

# 3. Preview the interactive dashboard locally (no Azure required)
cd smart-city-output/src/app
pip install fastapi uvicorn pydantic pydantic-settings
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# Open http://127.0.0.1:8000 -- create records, trigger actions, monitor health
```

When ready, deploy to Azure with one more command:

```powershell
devex deploy ./smart-city-output -g rg-smart-city-dev -r eastus2
```

**That's it.** From business description to live Azure deployment with enterprise security, governance, WAF alignment, CI/CD, monitoring, tests, and interactive dashboards.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git

### Install

```powershell
git clone https://github.com/Oluseyi-Kofoworola/enterprise-devex-orchestrator.git
cd enterprise-devex-orchestrator

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

### Verify

```powershell
devex --help
devex version         # Shows: GitHub Copilot SDK (default provider)
pytest tests/ -v      # 609 tests
```

---

## LLM Providers

The orchestrator supports multiple LLM backends. **GitHub Copilot SDK** is the default provider and requires no additional configuration in Copilot-enabled environments.

| Provider | Default Model | Env Vars Required |
|----------|--------------|-------------------|
| **GitHub Copilot SDK** (default) | `gpt-4o` | `GITHUB_TOKEN` (auto-detected) |
| Azure OpenAI | `gpt-4o` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` |
| OpenAI | `gpt-4o` | `OPENAI_API_KEY` |
| Anthropic (Claude) | `claude-opus-4-20250514` | `ANTHROPIC_API_KEY` |

```powershell
# Check current provider and available providers
devex version
devex providers

# Switch provider via environment variable
$env:LLM_PROVIDER = "anthropic"
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

The orchestrator auto-detects the provider from available credentials. When no credentials are found, it defaults to GitHub Copilot SDK. Set `LLM_PROVIDER` explicitly to override auto-detection.

---

## Usage

### Preview a plan (no files written)

```powershell
devex plan --file examples/intent.md
```

### Generate a scaffold

```powershell
devex scaffold --file examples/intent.md -o ./my-output
```

### Validate a generated scaffold

```powershell
devex validate ./my-output
```

### Create your own intent file

```powershell
devex init -o ./my-output -p my-output

# Edit ./my-output/intent.md with your requirements
devex scaffold --file ./my-output/intent.md -o ./my-output
```

### Upgrade with a new intent version

```powershell
devex new-version ./my-output
# Edit the generated intent.v2.md
devex upgrade --file ./my-output/intent.v2.md -o ./my-output
devex history ./my-output
```

---

## Proven Across Domains

The same engine generates production scaffolds for **any business domain** -- no templates, no hardcoded entity lists:

| Intent | Entities Extracted | Endpoints Generated | Data Stores |
|--------|-------------------|-------------------|-------------|
| Healthcare voice agent | Patient, Appointment, VoiceSession | CRUD + schedule, cancel | In-memory |
| Legal contract review | Contract, Clause, ReviewResult | CRUD + analyze, approve | Blob, Cosmos DB |
| Smart city IoT (9 entities) | Sensor, Incident, Route, ServiceRequest + 5 more | 79 endpoints incl. dispatch, triage, correlate | Cosmos, SQL, Blob, Redis, AI Search, Table |
| Propane delivery logistics | Delivery, Tank, Route, Customer | CRUD + optimize, schedule | Cosmos DB |
| E-commerce returns | Order, Refund, Return, Customer | CRUD + process, approve | Cosmos DB |
| AI customer support chatbot | ChatSession, KnowledgeArticle | CRUD + chat, RAG | AI Search |
| Agentic document processor | Document, Task, Agent | CRUD + analyze, dispatch | Blob, AI Search |
| Extreme stress test (15 entities) | Patient, Claim, Provider, Appointment + 11 more | 100+ endpoints with multi-param paths | All 6 data stores |

**Every scaffold gets the same enterprise treatment**: Bicep IaC, CI/CD, governance, WAF assessment, interactive dashboard, tests, and documentation.

## Example Intent Files

Ready-to-run examples are in [`examples/`](examples/):

| File | Description |
|------|-------------|
| [`intent.md`](examples/intent.md) | Healthcare voice agent (v1) |
| [`intent.v2.md`](examples/intent.v2.md) | Voice agent upgrade (v2) |
| [`contract-review-intent.md`](examples/contract-review-intent.md) | Legal contract review AI |
| [`doc-intelligence-intent.md`](examples/doc-intelligence-intent.md) | Document processing service |
| [`propane-delivery-intent.md`](examples/propane-delivery-intent.md) | Propane delivery logistics |
| [`smart-city-intent.md`](examples/smart-city-intent.md) | Smart city operations (stress test — 6 data stores, 9 entities, 10 Bicep modules) |
| [`extreme-healthcare-intent.md`](examples/extreme-healthcare-intent.md) | Extreme stress test — 15 entities, 25 fields/entity, all 6 data stores, multi-param endpoints |

See [`examples/README.md`](examples/README.md) for details on each example.

---

## Output Structure

Each generated scaffold contains:

```
output-dir/
  .devex/                     # State, versioning, and metadata
  .github/workflows/          # CI/CD pipelines (validate, deploy, codeql, dependabot)
  infra/bicep/                # Azure Bicep templates (main + modules + parameters)
  src/app/                    # Backend application + domain services + Dockerfile
  frontend/                   # React + Vite + TypeScript SPA + Dockerfile
  tests/                      # Auto-generated test suite (5 files)
  docs/                       # Architecture, security, WAF, governance, deployment docs
```

---

## CLI Reference

| Command | Purpose |
|---------|---------|
| `devex init` | Create a structured `intent.md` template |
| `devex plan` | Preview architecture plan without generating files |
| `devex scaffold` | Run full pipeline and generate scaffold |
| `devex validate` | Validate a scaffold against 25 governance policies |
| `devex deploy` | Deploy generated Bicep to Azure (staged) |
| `devex upgrade` | Upgrade an existing scaffold from a versioned intent file |
| `devex history` | Show scaffold version history |
| `devex new-version` | Create next intent template from existing output |
| `devex version` | Show CLI and runtime details |
| `devex providers` | List supported LLM providers and models |

---

## Architecture: 4-Agent Chain with Governance Feedback

The orchestrator doesn't just generate files -- it **reasons about your intent** through a 4-agent chain, each with distinct responsibilities, tools, and guardrails:

```
Business Intent
    |
    v
[1. Intent Parser] ---- Semantic NLP: extracts entities, fields, endpoints from any domain
    |
    v
[2. Architecture Planner] ---- Selects Azure services, writes ADRs, builds STRIDE threat model
    |
    v
[3. Governance Reviewer] ---- Validates against 25 policies + 26 WAF principles
    |                               |
    |   <-- feedback loop --------- | (if FAIL: remediates and re-validates, max 2 iterations)
    v
[4. Infrastructure Generator] ---- 9 generators produce 60+ files: Bicep, CI/CD, app, frontend, tests, docs
```

**No scaffold ships without passing governance.** If the reviewer finds violations, the planner automatically remediates -- up to 2 iterations -- before code is generated.

Each agent has a distinct role, instruction set, and tool access. See [`AGENTS.md`](AGENTS.md) for the full specification.

### Enterprise Standards Engine

**Everything a compliance team would ask for -- generated automatically:**

| Component | What It Does | Why It Matters |
|-----------|-------------|----------------|
| **NamingEngine** | Azure CAF naming (20 resource types, 34 regions) | Pass naming audits on first review |
| **TaggingEngine** | 7 required + 5 optional tags with regex validation | Cost tracking, ownership, compliance from day one |
| **WAFAssessor** | 26 principles across 5 pillars with per-pillar scores | Azure Well-Architected alignment with evidence |
| **StateManager** | SHA-256 file manifests, drift detection, audit trail | Know exactly what changed between generations |

### Time Savings (Benchmarked)

**Measured scaffold generation performance:**

| Intent | Complexity | Files Generated | Generation Time |
|--------|-----------|----------------|----------------|
| Voice Agent | 5 Bicep modules | 76 files | ~10 seconds |
| Contract Review | 6 Bicep modules, Blob + Cosmos | 77 files | ~5 seconds |
| Smart City (stress test) | 10 Bicep modules, 6 data stores, 9 entities | 86+ files | ~5 seconds |

**What those seconds replace:**

| Traditional Approach | With Enterprise DevEx Orchestrator |
|---------------------|-----------------------------------|
| 2-4 weeks: Bicep templates + naming + tagging | **5-10 seconds**: `devex scaffold` |
| 1-2 weeks: CI/CD pipelines with OIDC | **Included**: 4 workflows, zero stored credentials |
| 1 week: Governance review + WAF assessment | **Automatic**: 25 policies + 26 WAF principles |
| 3-5 days: Dashboard and API scaffolding | **Generated**: Interactive CRUD dashboard + React SPA |
| 2-3 days: Security review + threat model | **Built-in**: STRIDE threat model + 8-layer defense in depth |
| 1-2 days: Documentation | **7+ files**: Architecture, security, deployment, ADRs |
| **Total: 6-12 weeks** | **Total: Under 10 seconds** |

### Advanced Patterns

| Pattern | Module |
|---------|--------|
| Skills registry | `src/orchestrator/skills/registry.py` -- 9 pluggable skills, 12 categories |
| Subagent dispatcher | `src/orchestrator/agents/subagent_dispatcher.py` -- parallel fan-out |
| Persistent planner | `src/orchestrator/planning/` -- 13-task DAG with checkpoints |
| Deploy orchestrator | `src/orchestrator/agents/deploy_orchestrator.py` -- staged deployment |
| Semantic entity extraction | `src/orchestrator/agents/intent_parser.py` -- 5-phase NLP pipeline, dynamic entity/endpoint discovery |
| Frontend generator | `src/orchestrator/generators/frontend_generator.py` -- Entity-driven React + Vite + TypeScript SPA |

---

## Project Structure

```
src/orchestrator/
  agent.py                # 4-agent chain runtime
  config.py               # Configuration management (multi-provider LLM)
  intent_file.py          # Markdown intent file parser (9 enterprise sections)
  intent_schema.py        # Pydantic schemas (IntentSpec, PlanOutput, GovernanceReport, DomainType, EntitySpec)
  llm_client.py           # Multi-provider LLM client abstraction
  main.py                 # CLI entry point (10 commands)
  state.py                # State management and drift detection
  versioning.py           # Version tracking, upgrade, and rollback
  agents/
    architecture_planner.py
    deploy_orchestrator.py
    governance_reviewer.py
    intent_parser.py
    subagent_dispatcher.py
  generators/
    alert_generator.py    # Azure Monitor alert rules and runbook
    app_generator.py      # Entity-driven backend (Python, Node.js, .NET) with dynamic services, repositories, seed data
    bicep_generator.py    # Bicep IaC (7 modules)
    cicd_generator.py     # GitHub Actions workflows (4 files)
    cost_estimator.py     # Cost estimation
    dashboard_generator.py # Azure Monitor dashboard queries
    docs_generator.py     # Documentation (7+ files)
    frontend_generator.py # Entity-driven React + Vite + TypeScript SPA with dynamic dashboards
    test_generator.py     # Pytest test suite (5 files)
  planning/               # Persistent planner (13-task DAG)
  prompts/                # Repo-aware prompt generation
  skills/                 # Pluggable skills registry
  standards/              # NamingEngine, TaggingEngine, WAFAssessor
  tools/                  # Azure validation, governance policies, template rendering

tests/                    # Framework test suite (16 files, 609 tests)
examples/                 # Example intent files
docs/                     # Framework documentation
standards.yaml            # Enterprise standards configuration
```

---

## Security: Enterprise Baselines Enforced by Default

Every scaffold ships with 8 layers of defense -- not optional, not configurable, always on:

| Layer | Control | Generated Artifact |
|-------|---------|-------------------|
| Identity | **Managed Identity** | Zero credentials in code |
| Secrets | **Key Vault** with RBAC | Soft-delete, purge protection |
| Transport | **HTTPS-only** | TLS 1.2+ enforced |
| Container | **Non-root** | Read-only filesystem |
| Registry | **ACR + AcrPull** | No admin credentials |
| CI/CD | **OIDC federation** | No stored secrets |
| Input | **Pydantic validation** | All API boundaries |
| Governance | **STRIDE + 25 policies** | Automated threat model |
| AI Safety | **Content filtering + token budgets** | Azure OpenAI content safety, rate limiting |

---

## AI & Foundry Workloads

Describe an AI-powered business and the orchestrator automatically scaffolds **Azure OpenAI, AI Search, Semantic Kernel agents**, and a chat frontend -- with the same enterprise security baselines as every other workload.

```
"Build an AI-powered customer support copilot with RAG grounding
 from our knowledge base. Use gpt-4o with content safety."
```

**What gets generated for AI workloads (in addition to standard artifacts):**

| Layer | AI Artifacts | Details |
|-------|-------------|---------|
| **Infrastructure** | `openai.bicep`, `ai-search.bicep` | Azure OpenAI (S0) with model deployment, AI Search with semantic search |
| **Backend** | `ai/client.py`, `ai/chat.py`, `ai/agent.py` | Managed Identity auth, chat router, Semantic Kernel agents with tool-calling |
| **Frontend** | `ChatPage.tsx` | React chat interface with message history, streaming UI |
| **Governance** | 5 AI policies (AI-001 to AI-005) | Content safety, Managed Identity for AI, audit logging, RAI docs, token budgets |
| **Threat Model** | THREAT-007, THREAT-008 | Prompt injection / data leakage, token exhaustion |
| **Architecture** | ADR-006, ADR-007, ADR-008 | Azure OpenAI + Foundry, AI Search for RAG, Semantic Kernel |

**AI-specific app types:** `ai_agent` (autonomous agents, multi-agent, tool-use) and `ai_app` (chatbot, copilot, RAG apps).

**AI features auto-detected:** `chat`, `embeddings`, `rag`, `agents`, `content-safety`.

**Models supported:** `gpt-4o` (default), `gpt-4o-mini`, `gpt-35-turbo`.

**Security:** All AI services use Managed Identity with `Cognitive Services OpenAI User` RBAC role -- no API keys. Content safety filters are enabled by default. Token budgets and rate limiting enforced via governance policies.

---

## Run Dashboard Locally (Before Azure Deployment)

Every generated scaffold includes a fully functional dashboard. Preview it locally -- no Azure account, no database, no Docker required:

```powershell
cd my-output/src/app
pip install fastapi uvicorn pydantic pydantic-settings
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000`. The dashboard is fully interactive:
- **Create** records via modal forms with type-aware inputs
- **Update** status via workflow action buttons (dispatch, approve, verify)
- **Delete** records from detail view
- **Search** and filter across all entity types
- **Monitor** health with live status indicator and auto-refresh

> **In-memory storage with domain-aware seed data.** Every entity table is pre-populated with contextually appropriate data. CRUD operations work immediately. Data resets on restart.

### Alternative: Docker

```powershell
cd my-output/src/app
docker build -t my-app .
docker run -p 8000:8000 my-app
```

### Alternative: Full-stack (Backend + React SPA)

```powershell
# Terminal 1: Backend API
cd my-output/src/app && uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: React frontend
cd my-output/frontend && npm install && npm run dev
```

---

## Deploy to Azure (Optional)

Deployment requires Azure CLI and an active subscription:

```powershell
az login
az group create --name rg-my-project-dev --location eastus2
devex deploy ./my-output -g rg-my-project-dev -r eastus2
```

For a safe preview:

```powershell
devex deploy ./my-output -g rg-my-project-dev -r eastus2 --dry-run
```

See [`QUICKSTART.md`](QUICKSTART.md) for the full deployment workflow including OIDC setup.

---

## Quality

```powershell
pytest tests/ -v          # Run all tests
ruff check src/ tests/    # Lint
ruff format --check src/  # Format check
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`QUICKSTART.md`](QUICKSTART.md) | Step-by-step installation, scaffolding, and deployment guide |
| [`AGENTS.md`](AGENTS.md) | Agent architecture, tool bindings, and orchestration flow |
| [`examples/README.md`](examples/README.md) | Example intent files and usage |
| [`docs/architecture.md`](docs/architecture.md) | Framework architecture overview |
| [`docs/security.md`](docs/security.md) | Security controls and compliance |
| [`docs/deployment.md`](docs/deployment.md) | Deployment patterns and procedures |
| [`docs/scorecard.md`](docs/scorecard.md) | Enterprise challenge scorecard |

---

## Contributing

All changes must pass:

```powershell
pytest tests/ -v
ruff check src/ tests/
```

Extension points:

- **New generator** -- Add to `src/orchestrator/generators/`
- **New skill** -- Register in `src/orchestrator/skills/registry.py`
- **New governance policy** -- Update `src/orchestrator/tools/governance.py`
- **New example** -- Add an intent file to `examples/`

---

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| UnicodeEncodeError with Rich spinner on Windows | Set `$env:PYTHONIOENCODING="utf-8"` before running commands |
| `devex deploy` hangs or times out | Verify `az login` session is active and subscription has quota |

---

## Changelog

### v1.8.0

- **Feature**: Hardened parser for extreme-complexity intents
  - Entity cap raised from 8 to 20 entities per intent
  - Field cap raised from 12 to 25 fields per entity
  - Safe singular/plural normalization (`_safe_singular()`) — preserves "status", "address", "class", "bus", "alias", "campus", etc.
  - Multi-parameter endpoint path preservation (`/{order_id}/items/{item_id}` no longer collapses to `/{id}/items/{id}`)
  - AI signal false positive filtering — excludes Azure AI Search infrastructure refs from AI_APP detection
  - H4 heading support (`####`) in intent files
  - 45 section heading aliases (up from 28) — "user stories", "capabilities", "stakeholders", "kpis", "sla", "third-party", etc.
  - 10+ field type aliases — `string→str`, `integer→int`, `boolean→bool`, `timestamp→datetime`, `decimal→float`, etc.
  - `- Actions:` parsing in explicit entity blocks
  - `list[int]` and `list[float]` support in seed data and type defaults
- **Feature**: Smart AI chatbot with 11 intent handlers
  - Temporal queries ("latest incidents", "oldest work orders")
  - Cross-entity comparison with health scores and action breakdown
  - Recommendation engine with data-driven suggestions
  - HTML-formatted responses with stat cards, bar charts, and tables
  - Works without any AI provider — pure Python analysis on seed data
- **Feature**: 12 realistic seed records per entity (108 total for 9-entity intents) with 15+ domain-aware name pools
- **Feature**: Extreme-complexity example intent (`examples/extreme-healthcare-intent.md`) — 15 entities, 25 fields/entity, all 6 data stores, multi-param endpoints
- **Docs**: Updated AGENTS.md with parsing limits, AI chat engine, and 45 heading aliases
- **Docs**: Updated README.md with hardened capabilities and new examples
- **Tests**: 609 tests passing

### v1.7.0

- **Feature**: Fully interactive enterprise dashboard with end-to-end CRUD operations
  - Create records via modal forms with type-aware field inputs
  - Update status via workflow action buttons (dispatch, approve, verify, etc.)
  - Delete records with confirmation
  - Real-time health indicator, auto-refresh, and live clock
  - Search and filter across all entities
- **Feature**: Domain-aware seed data -- generated values are contextually appropriate (e.g., smart city sensors get GPS coordinates and zone IDs, not generic "item-001")
- **Fix**: Single-worker uvicorn in generated Dockerfiles -- prevents in-memory data isolation between forked processes
- **Fix**: HTML entity encoding (`&#39;`) for onclick handlers -- survives nested Python f-string processing
- **Fix**: Missing `from datetime import datetime` in generated Pydantic schemas
- **Docs**: Added "Run Dashboard Locally" guide to README and QUICKSTART
- **Docs**: Updated all documentation for v1.7.0

### v1.6.0

- **Breaking**: Fully domain-agnostic semantic extraction -- all domains now use the same 5-phase NLP pipeline for entity/endpoint discovery
  - Removed hardcoded entity lists for Healthcare, Legal, and Document Processing domains from Intent Parser
  - Removed all domain-specific code generation branches from App Generator (Python, Node.js, .NET)
  - Added 4 new dynamic generator methods for Node.js and .NET (`_dynamic_node_services`, `_dynamic_node_seed_data`, `_dynamic_dotnet_services`, `_dynamic_dotnet_seed_data`)
  - Domain labels (Healthcare/Legal/etc.) still detected for context but no longer drive entity extraction or code generation
- **Feature**: Every business domain -- healthcare, legal, e-commerce, logistics, or any custom domain -- receives identical treatment through semantic reasoning
- **Docs**: Updated all documentation to reflect domain-agnostic architecture

### v1.5.0

- **Feature**: Domain-agnostic React SPA frontend -- generates entity-specific dashboards, API clients, TypeScript types, and detail pages from intent entities
  - Tabbed dashboard with KPI cards, search, create modals, and workflow action buttons
  - Entity-specific API client with dynamic methods (e.g., `listRefunds`, `processReturn`)
  - TypeScript interfaces generated from entity field specs
  - Detail page with full entity field display and action buttons
- **Feature**: Azure-compatible frontend Dockerfile -- configurable `API_BACKEND_URL` env var replaces hardcoded Docker Compose service name
  - Works with Docker Compose (default `http://api:8000`)
  - Works with Azure Container Apps (set `API_BACKEND_URL` to backend FQDN)
- **Docs**: Updated architecture, demo-script, deployment, and RAI docs for domain-agnostic frontend

### v1.4.0

- **Feature**: Multi-provider LLM support -- GitHub Copilot SDK (default), Azure OpenAI, OpenAI, Anthropic (Claude)
- **Feature**: GitHub Copilot SDK is now the default provider (no configuration required)
- **Feature**: `devex providers` command lists all supported providers and models
- **Feature**: `devex version` shows active provider and model
- **Feature**: Auto-detection from available credentials with copilot_sdk fallback
- **Docs**: Updated all documentation with multi-provider LLM configuration

### v1.3.0

- **Feature**: Domain-aware code generation with auto-detection of 4 business domains (superseded by v1.6.0 semantic extraction)
  - Healthcare, Legal, Document Processing, Generic domain templates (now removed in favour of universal semantic extraction)
- **Feature**: Repository pattern with dual-mode storage (in-memory or Azure via `STORAGE_MODE` env var)
- **Feature**: React + Vite + TypeScript frontend SPA generator
  - Domain-specific dashboards, API client, type definitions, and reusable components
  - Multi-stage Dockerfile with nginx for production
- **Feature**: Full-stack parity across Python, Node.js, and .NET backends
  - Domain-specific services and seed data for all 3 language targets
- **Feature**: DomainType, FieldSpec, EntitySpec, EndpointSpec schema models
- **Tests**: 543 tests across 15 test files

### v1.2.0

- **Feature**: Enterprise dashboard UI for all generated applications (Python, Node.js, .NET)
  - Gradient topbar, hero header, status cards, live health polling
  - Dynamic architecture & compliance badges from intent specification
  - API endpoint directory with method badges
  - JavaScript live polling for health and Key Vault status
- **Feature**: Multi-language application scaffold (Python/FastAPI, Node.js/Express, .NET/ASP.NET Core)
- **Feature**: `pydantic-settings` added to generated Python requirements
- **Fix**: Node.js and .NET generators now produce HTML landing pages with KEY_VAULT_URI support
- **Tests**: 543 tests across 15 test files (up from 486/14)

### v1.1.1

- **Fix**: `devex deploy` now works on Windows (resolves `az.cmd` via `shutil.which`)
- **Fix**: Deploy default Bicep paths match generated scaffold structure (`infra/bicep/`)
- **Fix**: Container Registry uses Premium SKU with public network access disabled
- **Fix**: Cosmos DB role assignment uses correct `sqlRoleAssignments` resource type
- **Fix**: Redis uses `Redis Cache Contributor` role (available in all subscriptions)
- **Fix**: Container App and Environment names truncated to 32-character limit

---

## License

MIT

---

*Enterprise DevEx Orchestrator v1.7.0*



