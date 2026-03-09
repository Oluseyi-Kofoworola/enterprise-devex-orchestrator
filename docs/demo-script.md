# Demo Script

> Duration: 3 minutes | No improvisation -- follow this script exactly.

## Setup (Before Recording)

1. Terminal open in project root
2. `.env` configured with working credentials
3. Azure Portal open in browser tab
4. (Optional) Pre-deployed resources in Azure as backup

## Demo Flow

### Minute 0:00 -- 0:30 | The Problem

**Say:** "Healthcare systems like St. Luke's handle thousands of patient calls
daily -- appointment scheduling, prescription refills, follow-ups. Patients
wait on hold, staff burn out, and HIPAA compliance requires audit trails that
phone systems don't provide."

**Show:** The README.md briefly on screen.

**Say:** "We built an Enterprise DevEx Orchestrator -- a Copilot SDK-powered
agent that transforms structured business requirements into a complete,
governed, production-ready Azure workload. Let me show you how it works
with a real-time voice agent for healthcare."

### Minute 0:30 -- 1:30 | The Agent in Action

**Run:**
```bash
devex scaffold --file examples/intent.md -o ./demo-output
```

**Narrate as it runs:**
- "The Intent Parser extracts structured requirements -- app type, data stores, compliance framework. It detects HIPAA, Cosmos DB, Redis, and the voice agent pattern."
- "The Architecture Planner selects Azure services and generates ADRs and a STRIDE threat model tailored for healthcare PHI handling."
- "The Governance Reviewer validates against 15 enterprise policies -- including naming and tagging standards -- and passes."
- "The Infrastructure Generator produces all deployable artifacts."

**Show:** The Rich CLI output with tables and progress spinners.

### Minute 1:30 -- 2:15 | The Output

**Run:**
```bash
tree demo-output
```

**Show and narrate each category:**

1. **Bicep Infrastructure** -- `infra/bicep/main.bicep` + modules
   - "Modular Bicep -- Key Vault with RBAC and soft delete, Managed Identity,
     Container Apps with health probes, Cosmos DB for session history,
     Redis for low-latency caching, Log Analytics for HIPAA audit."

2. **CI/CD** -- `.github/workflows/`
   - "OIDC authentication -- no stored credentials. CodeQL and Dependabot included."

3. **Application** -- `src/app/main.py`
   - "FastAPI with health endpoint, non-root Docker container, ready for WebSocket integration."

4. **Documentation** -- `docs/`
   - "Architecture plan, security docs with STRIDE threat model, RAI notes, deployment guide."

5. **Governance Report** -- `docs/governance-report.md`
   - "Every scaffold is validated. This one passed all 15 checks with HIPAA controls."

6. **Enterprise Standards** -- `docs/standards.md`
   - "Azure CAF naming conventions and a 12-tag enterprise tagging standard, auto-generated."

### Minute 2:15 -- 2:45 | Proving It Works

**Option A -- Live Validation:**
```bash
az deployment group validate \
  --resource-group rg-slhs-voice-agent-dev \
  --template-file demo-output/infra/bicep/main.bicep \
  --parameters demo-output/infra/bicep/parameters/dev.parameters.json
```

**Option B -- Pre-deployed:**
- Switch to Azure Portal
- Show Resource Group with Container App, Key Vault, Cosmos DB, Redis, Log Analytics, ACR, Managed Identity
- Click Container App -> show FQDN -> hit /health endpoint
- Click Log Analytics -> run KQL query for HIPAA audit trail

### Minute 2:45 -- 3:00 | Close

**Say:** "Enterprises don't need faster code generation. They need safe,
compliant, repeatable architecture. We built a Copilot SDK-powered orchestrator
that turns structured requirements into governed infrastructure -- with Key Vault,
Managed Identity, STRIDE threat models, HIPAA controls, and CI/CD built in
from the first line. For St. Luke's, this means a voice agent that is
production-ready, auditable, and HIPAA-compliant from day one."

## Backup Plan

If anything fails during the live demo:
1. Show the pre-generated `demo-output/` directory already in the repo
2. Walk through the static Bicep files in `infra/bicep/`
3. Show Azure Portal screenshots

## Key Talking Points

- "Structured requirements in -> production scaffold out"
- "4-agent chain with governance feedback loop"
- "15 enterprise policies + naming and tagging standards validated before any file is written"
- "STRIDE threat model, ADRs, and RAI notes -- generated, not afterthoughts"
- "HIPAA compliance controls baked into every generated resource"
- "State management with drift detection between generations"
- "Works without LLM access via rule-based fallback -- reliability first"

---
*Enterprise DevEx Orchestrator Agent*
