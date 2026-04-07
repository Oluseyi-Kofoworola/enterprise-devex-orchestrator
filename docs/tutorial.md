# Tutorial: Your First Enterprise Scaffold in 5 Minutes

This hands-on tutorial walks you through generating a complete enterprise application
from a plain-English business description. By the end, you'll have a working API,
interactive dashboard, Azure infrastructure templates, CI/CD pipelines, and governance
documentation — all from a single command.

We'll use the **Document Intelligence Platform** example, but the same workflow
applies to any business domain.

---

## Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend dashboard)
- Git

---

## Step 1: Install the Orchestrator

```powershell
git clone https://github.com/Oluseyi-Kofoworola/enterprise-devex-orchestrator.git
cd enterprise-devex-orchestrator

python -m venv .venv
.venv\Scripts\Activate.ps1    # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -e ".[dev]"
```

Verify:

```powershell
devex version
# Output: Enterprise DevEx Orchestrator v2.x.x
# Provider: GitHub Copilot SDK (default)
```

---

## Step 2: Understand the Intent File

Open `examples/doc-intelligence-intent.md` in your editor. This is a **structured
Markdown file** that describes what you want to build:

```markdown
# doc-intelligence-platform

> An enterprise document intelligence platform that ingests, classifies,
> extracts, reviews, and archives business documents at scale...

## Problem Statement
Organizations process 10,000+ documents daily...

## Business Goals
- Reduce manual document data-entry effort by 85%
- Achieve extraction accuracy above 97%
...

## Functional Requirements
### Entity: Document
- Fields: filename (str), file_type (str), status (str), ...
- Endpoints: POST /documents, GET /documents, ...
```

**Key sections the orchestrator reads:**

| Section | What the Orchestrator Extracts |
|---------|-------------------------------|
| Title (`# project-name`) | Project name, used for Azure resource naming |
| Description (`> blockquote`) | Business context, domain detection |
| Problem Statement | Justification for ADRs and documentation |
| Business Goals | KPIs embedded in generated docs |
| Functional Requirements | Entities, fields, endpoints, and actions |
| Security & Compliance | Auth model, compliance frameworks |
| Scalability / Performance | Deployment profile selection |

> **Tip:** You can write your intent as free-form prose or use explicit
> `### Entity:` blocks. The orchestrator's 5-phase NLP pipeline extracts
> entities either way. Explicit declarations give you precise control.

---

## Step 3: Preview the Architecture Plan

Before generating any files, preview what the orchestrator will build:

```powershell
devex plan --file examples/doc-intelligence-intent.md
```

This outputs:
- **Extracted entities** (Document, ExtractionResult, BatchJob, etc.)
- **Azure components** (Container Apps, Key Vault, Cosmos DB, etc.)
- **Architecture Decision Records** (ADRs)
- **STRIDE threat model**
- **Governance validation** (25 policy checks)

No files are written — this is a dry run.

For JSON output (useful for automation):

```powershell
devex plan --file examples/doc-intelligence-intent.md -F json
```

---

## Step 4: Generate the Full Scaffold

```powershell
devex scaffold --file examples/doc-intelligence-intent.md -o ./doc-intelligence-output
```

In about 5 seconds, the orchestrator generates ~80+ files:

```
doc-intelligence-output/
├── .devex/                      # State tracking and metadata
├── .github/workflows/           # 4 CI/CD pipelines
│   ├── validate.yml             # PR validation (lint, test, Bicep validate)
│   ├── deploy.yml               # Staged deployment to Azure
│   ├── codeql.yml               # Security scanning
│   └── dependabot.yml           # Dependency updates
├── infra/bicep/                 # Azure infrastructure
│   ├── main.bicep               # Orchestrator template
│   ├── modules/                 # 7+ resource modules
│   └── parameters/              # Environment-specific params
├── src/app/                     # Backend API
│   ├── main.py                  # FastAPI application
│   ├── schemas.py               # Pydantic models from entities
│   ├── services/                # Business logic per entity
│   ├── repositories/            # Data access layer
│   ├── seed_data.py             # 12 realistic records per entity
│   └── Dockerfile               # Non-root, production-ready
├── frontend/                    # React SPA dashboard
│   ├── src/pages/               # Dashboard, Detail, entity pages
│   ├── src/components/          # Reusable UI components
│   └── package.json             # Vite + TypeScript + Tailwind
├── tests/                       # Auto-generated test suite
│   ├── test_health.py           # Health endpoint tests
│   ├── test_api.py              # Entity CRUD tests
│   ├── test_security.py         # Security header tests
│   └── conftest.py              # Test fixtures
└── docs/                        # 7+ documentation files
    ├── plan.md                  # Architecture plan + ADRs
    ├── security.md              # Security controls
    ├── waf-report.md            # WAF assessment (5 pillars)
    ├── governance-report.md     # 25-policy validation
    └── deployment.md            # Deployment guide
```

---

## Step 5: Run the Backend API Locally

Start the FastAPI backend:

```powershell
cd doc-intelligence-output/src/app
pip install fastapi uvicorn pydantic pydantic-settings
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/docs` — you have auto-generated **Swagger documentation**
for every endpoint. Try these:

| Endpoint | What It Does |
|----------|-------------|
| `GET /health` | Health check — returns `{"status": "healthy"}` |
| `GET /api/v1/documents` | Lists all documents (12 pre-seeded) |
| `POST /api/v1/documents` | Creates a new document |
| `GET /api/v1/documents/{id}` | Gets a single document |
| `POST /api/v1/documents/{id}/analyze` | Triggers document analysis |

All entities have full CRUD endpoints plus any custom actions defined in the intent.

---

## Step 6: Run the Frontend Dashboard

In a **second terminal**:

```powershell
cd doc-intelligence-output/frontend
npm install
npm run dev
```

Open `http://localhost:5173` (or `http://localhost:3000`).

**What you'll see:**

1. **Summary bar** — Total records, active items, entity count
2. **Entity tabs** — One tab per entity (Documents, Extraction Results, Batch Jobs, etc.)
3. **KPI cards** — Donut charts showing status distribution
4. **Data tables** — Smart column selection, type-aware rendering:
   - Status fields → colored badges
   - Dates → formatted timestamps
   - Numbers → locale formatting
   - URLs → clickable links
   - Progress/scores → progress bars
5. **Status filter pills** — Click to filter by status value
6. **CRUD operations** — Create (modal form), Update (action buttons), Delete (confirmation)
7. **CSV export** — Download any entity table

> **No database or Azure account required.** Local mode uses in-memory storage
> with auto-seeded domain-aware data. Data resets on server restart.

---

## Step 7: Validate Governance

```powershell
cd ../..   # Back to doc-intelligence-output root
devex validate ./doc-intelligence-output
```

This checks 25 enterprise governance policies:
- Required components (Key Vault, Managed Identity, Log Analytics)
- Security anti-patterns in Bicep templates
- STRIDE threat model completeness
- CI/CD security (OIDC, no stored credentials)
- Azure Well-Architected Framework alignment

---

## Step 8: Explore the Generated Code

### Backend service example

Open `src/app/services/` — each entity gets a service class with:

```python
class DocumentService:
    def list_all(self) -> list[dict]:      # GET /documents
    def get(self, doc_id) -> dict | None:  # GET /documents/{id}
    def create(self, payload) -> dict:     # POST /documents
    def update(self, doc_id, payload):     # PUT /documents/{id}
    def delete(self, doc_id) -> bool:      # DELETE /documents/{id}
    def analyze(self, doc_id) -> dict:     # POST /documents/{id}/analyze
    def archive(self, doc_id) -> dict:     # POST /documents/{id}/archive
```

### Bicep infrastructure

Open `infra/bicep/main.bicep` — modular Azure infrastructure with:
- Container Apps Environment + Container App
- Container Registry (ACR) with AcrPull role
- Key Vault with RBAC, soft-delete, purge protection
- Log Analytics workspace
- Managed Identity
- Data stores matching your intent (Cosmos DB, Blob Storage, etc.)

### CI/CD workflows

Open `.github/workflows/deploy.yml` — staged deployment:
1. **Validate** — `az deployment group validate`
2. **What-If** — Preview changes
3. **Deploy** — Apply infrastructure
4. **Verify** — Health check the deployed app

Uses OIDC federation — no stored credentials.

---

## Step 9: Write Your Own Intent

```powershell
devex init -o ./my-project -p my-project
```

This creates a template `intent.md` with all 9 enterprise sections.
Edit it with your business requirements:

```markdown
# my-crm-platform

> A customer relationship management system for tracking leads,
> managing accounts, and automating follow-up tasks.

## Problem Statement
Sales team loses 30% of leads due to manual tracking...

## Functional Requirements
### Entity: Lead
- Fields: name (str), email (str), company (str), status (str), score (int)
- Endpoints: POST /leads, GET /leads, GET /leads/{id}, POST /leads/{id}/qualify

### Entity: Account
- Fields: company_name (str), industry (str), revenue (float), tier (str)
- Endpoints: CRUD + POST /accounts/{id}/upgrade
```

Then generate:

```powershell
devex scaffold --file ./my-project/intent.md -o ./my-project
```

---

## Step 10: Iterate with Versions

After your first scaffold, improve it:

```powershell
# Generate an upgrade template with improvement suggestions
devex new-version ./my-project

# Edit intent.v2.md — add entities, change data stores, add compliance
# Then upgrade:
devex upgrade --file ./my-project/intent.v2.md -o ./my-project

# View history
devex history ./my-project
```

Each upgrade is versioned with rollback support.

---

## What to Customize

| Priority | File | What to Change |
|----------|------|---------------|
| 1 | `src/app/services/*.py` | Add your business logic, validations, integrations |
| 2 | `frontend/src/pages/` | Customize dashboard layout, add pages |
| 3 | `infra/bicep/parameters/dev.parameters.json` | Set your Azure subscription and region |
| 4 | `.github/workflows/deploy.yml` | Configure deployment approvals |
| 5 | `frontend/src/styles/design-tokens.css` | Change theme colors and fonts |

---

## Common Patterns

### Use multiple data stores

```markdown
## Configuration
- Data Stores: cosmos, sql, redis, blob
```

### Enable AI features

```markdown
> Build an AI-powered platform with RAG grounding...
## Configuration
- App Type: ai_app
```

This adds Azure OpenAI, AI Search, Semantic Kernel agents, and a chat interface.

### Write free-form prose instead of explicit entities

```markdown
We need to track vehicles, drivers, and routes for a delivery fleet.
Each vehicle has a VIN, make, model, and current GPS coordinates.
Drivers have certification levels and availability schedules.
Routes should be optimizable based on traffic and delivery windows.
```

The NLP pipeline extracts `Vehicle`, `Driver`, and `Route` entities with
appropriate fields — no `### Entity:` blocks needed.

---

## Next Steps

- **Deploy to Azure**: See [QUICKSTART.md](../QUICKSTART.md) section 11
- **Explore examples**: See [examples/README.md](../examples/README.md)
- **Understand the architecture**: See [AGENTS.md](../AGENTS.md)
- **Review security controls**: Check `docs/security.md` in your generated output
