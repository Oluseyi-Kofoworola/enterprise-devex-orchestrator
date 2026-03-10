# Quick Start Guide -- Test Everything Step by Step

> Follow this guide to install, run, and test every feature of the
> Enterprise DevEx Orchestrator. No Azure account needed for local testing.

**Total verification time:** Under 10 minutes for Steps 1-10.
**Azure deployment (optional):** Step 11.

---

## Step 1: Install

Open a terminal in the project root directory.

```powershell
# Create virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install project + dev dependencies
pip install -e ".[dev]"
```

Verify the installation:

```powershell
devex --help
```

You should see commands: `init`, `plan`, `scaffold`, `validate`,
`deploy`, `upgrade`, `history`, `new-version`, `version`.

---

## Step 2: Check Version Info

```powershell
devex version
```

Shows orchestrator version (1.1.0), Python version, platform, and LLM backend.
If no `.env` file exists, it shows "Config not loaded" -- that is expected.

---

## Step 3: Plan from the Enterprise Example (No Files Generated)

```powershell
devex plan --file examples/intent.md
```

This runs the 4-agent chain (Intent Parser -> Architecture Planner ->
Governance Reviewer) against the fully defined enterprise intent file:

- **Requirements completeness** -- percentage of 9 enterprise sections filled
- **Architecture plan** -- Azure services, ADRs, Mermaid diagram
- **Governance report** -- 25 policy checks with PASS/FAIL
- **WAF assessment** -- 5-pillar scores with 26 principle-level detail

No files are written. This is a preview only.

For a quick inline test:

```powershell
devex plan "Build a healthcare voice agent with Cosmos DB and Redis"
```

---

## Step 4: Scaffold from the Enterprise Intent File

```powershell
devex scaffold --file examples/intent.md -o ./test-enterprise
```

Generates a full production scaffold in `./test-enterprise/`. Expect ~36 files.
The console shows requirements completeness, architecture plan, governance
results, WAF assessment, and improvement suggestions.

Explore the output:

```powershell
# List top-level directories
Get-ChildItem ./test-enterprise -Directory

# Read improvement suggestions -- what to refine for the next iteration
Get-Content ./test-enterprise/docs/improvement-suggestions.md

# Check Bicep infrastructure (main + 7 modules + parameters)
Get-ChildItem ./test-enterprise/infra/bicep -Recurse

# Check GitHub Actions workflows (4 workflows)
Get-ChildItem ./test-enterprise/.github/workflows

# Read generated FastAPI app
Get-Content ./test-enterprise/src/app/main.py

# Read architecture plan with ADRs and Mermaid diagram
Get-Content ./test-enterprise/docs/plan.md

# Check governance results (25 policies evaluated)
Get-Content ./test-enterprise/.devex/governance.json

# Check state tracking with SHA-256 file manifest
Get-Content ./test-enterprise/.devex/state.json
```

---

## Step 5: Validate the Scaffold

```powershell
devex validate ./test-enterprise
```

Re-runs governance validation against the generated scaffold. Shows 25 policy
results and WAF assessment with pillar-by-pillar scores.

---

## Step 6: Create Your Own Enterprise Intent File

The **define-then-run** workflow:

```powershell
# 6a: Generate an enterprise requirements template (9 sections)
devex init -o ./my-test -p my-cool-api

# 6b: Review the template -- note the 9 enterprise sections
Get-Content ./my-test/intent.md

# 6c: Fill in every section (problem statement, business goals,
#     target users, functional requirements, scalability, security,
#     performance, integration, acceptance criteria)

# 6d: Scaffold from your intent file
devex scaffold --file ./my-test/intent.md -o ./test-from-template

# 6e: Review improvement suggestions for the next iteration
Get-Content ./test-from-template/docs/improvement-suggestions.md
```

For a quick inline test (skips enterprise sections):

```powershell
devex scaffold "Build a healthcare voice agent with Cosmos DB and Redis" -o ./test-inline
```

---

## Step 7: Dry Run (Preview Without Writing)

```powershell
devex scaffold "Build a healthcare voice agent" --dry-run
```

Shows what files would be generated without writing to disk.

---

## Step 8: Plan from an Intent File (JSON Output)

```powershell
devex plan --file examples/intent.md
```

Plan-only mode using the intent file. Shows architecture, governance, and WAF
results without generating files.

JSON output:

```powershell
devex plan --file examples/intent.md -F json
```

---

## Step 9: Versioned Upgrades (Iterative Improvement)

Tests the full upgrade workflow where each version converges toward production:

```powershell
# 9a: Scaffold v1
devex scaffold --file examples/intent.md -o ./test-upgrade

# 9b: Review v1 improvement suggestions
Get-Content ./test-upgrade/docs/improvement-suggestions.md

# 9c: Check version history (shows v1 active)
devex history ./test-upgrade

# 9d: Generate v2 upgrade template (embeds v1 suggestions)
devex new-version ./test-upgrade

# 9e: Review generated template -- carries forward enterprise sections
#     and adds "Improvement Suggestions from v1" section
Get-Content ./test-upgrade/intent.v2.md

# 9f: Or use the pre-made v2 example
devex upgrade --file examples/intent.v2.md -o ./test-upgrade

# 9g: Review v2 suggestions (should show fewer gaps)
Get-Content ./test-upgrade/docs/improvement-suggestions.md

# 9h: Check version history (v1 superseded, v2 active)
devex history ./test-upgrade
```

---

## Step 10: Run All Tests

```powershell
# Run the full test suite (486 tests)
pytest tests/ -v
```

All 486 tests should pass. Key test files:

| Test File | Tests | Coverage |
|-----------|-------|---------|
| `test_standards.py` | 67 | Azure CAF naming (20 types), tagging (7+5 tags), config |
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

Run a specific category:

```powershell
pytest tests/test_standards.py -v      # 67 naming + tagging tests
pytest tests/test_waf.py -v            # WAF assessment tests
pytest tests/test_governance_validator.py -v  # 25 governance policies
```

---

## Step 11: Lint and Type Check

```powershell
# Lint (should pass clean)
ruff check src/ tests/

# Format check
ruff format --check src/ tests/

# Type check
mypy src/orchestrator/
```

---

## Step 12: Deploy to Azure (Optional)

Requires an Azure subscription and Azure CLI.

```powershell
# Login to Azure
az login

# Create a resource group
az group create --name rg-my-test --location eastus2

# Deploy (staged: validate -> what-if -> deploy -> verify)
devex deploy ./test-inline -g rg-my-test -r eastus2

# Or dry-run (validate + what-if only, no actual deployment)
devex deploy ./test-inline -g rg-my-test -r eastus2 --dry-run
```

**Live reference deployment:** The SLHS Voice Agent is deployed at
`https://<container-app-fqdn>`
in resource group `rg-enterprise-devex-orchestrator-dev` (East US 2).

---

## Cleanup

Remove test output directories:

```powershell
Remove-Item -Recurse -Force ./test-enterprise -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./test-inline -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./test-from-template -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./test-upgrade -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./my-test -ErrorAction SilentlyContinue
```

---

## All Commands Reference

| Command | Purpose |
|---------|---------|
| `devex --help` | Show all available commands |
| `devex version` | Show version and environment info |
| `devex init` | Create intent.md template (9 enterprise sections) |
| `devex plan "..."` | Preview architecture plan (no files) |
| `devex plan --file intent.md` | Plan from intent file |
| `devex scaffold "..." -o ./out` | Generate full scaffold from inline intent |
| `devex scaffold --file intent.md -o ./out` | Generate scaffold from intent file |
| `devex scaffold "..." --dry-run` | Preview without writing files |
| `devex validate ./out` | Validate scaffold against 25 policies |
| `devex deploy ./out -g rg -r region` | Deploy to Azure (4-stage pipeline) |
| `devex upgrade --file v2.md -o ./out` | Upgrade scaffold to new version |
| `devex history ./out` | View version history |
| `devex new-version ./out` | Generate upgrade template from current version |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `devex` not found | Activate venv: `.venv\Scripts\Activate.ps1` |
| "No intent provided" | Quote the intent: `devex scaffold "Build a healthcare voice agent" -o ./out` |
| "No .devex metadata found" | Run `devex scaffold` first before `validate`/`deploy`/`upgrade` |
| LLM connection error | Expected -- auto-falls back to template-only mode |
| pip install fails | Check Python 3.11+: `python --version` |

---

*Enterprise DevEx Orchestrator v1.1.0 | Enterprise proof-of-concept*
*486 tests | 25 governance policies | 26 WAF principles | 135/135 scorecard*


