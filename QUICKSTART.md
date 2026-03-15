# Quickstart

Step-by-step guide to install the orchestrator, generate your first scaffold, and optionally deploy to Azure.

---

## 1. Clone and Install

```powershell
git clone https://github.com/Oluseyi-Kofoworola/enterprise-devex-orchestrator.git
cd enterprise-devex-orchestrator

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

Verify the installation:

```powershell
devex --help
devex version      # Shows provider: GitHub Copilot SDK (default)
```

---

## 2. LLM Provider (Optional)

The orchestrator defaults to **GitHub Copilot SDK** -- no configuration needed. To use a different provider:

```powershell
# List supported providers
devex providers

# Switch to Azure OpenAI
$env:LLM_PROVIDER = "azure_openai"
$env:AZURE_OPENAI_ENDPOINT = "https://my-endpoint.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY = "..."

# Or use a .env file (copy from .env.example)
copy .env.example .env
# Edit .env with your provider settings
```

---

## 3. Run the Tests

Confirm everything works before generating scaffolds:

```powershell
pytest tests/ -v
```

---

## 4. Preview an Architecture Plan

See how the orchestrator interprets an intent file without writing any files:

```powershell
devex plan --file examples/intent.md
```

JSON output for automation:

```powershell
devex plan --file examples/intent.md -F json
```

---

## 5. Generate a Scaffold

```powershell
devex scaffold --file examples/intent.md -o ./my-first-output
```

This produces a complete, deployable project:

```
my-first-output/
  .devex/                     # State and metadata
  .github/workflows/          # CI/CD pipelines (validate, deploy, codeql, dependabot)
  infra/bicep/                # Azure Bicep templates (main + modules + parameters)
  src/app/                    # Multi-language application (Python/Node.js/.NET) + Enterprise Dashboard UI + Dockerfile
  tests/                      # Auto-generated test suite
  docs/                       # Plan, security, WAF, governance, deployment docs
```

> **Enterprise Dashboard UI** -- Every generated scaffold includes a production-grade
> enterprise dashboard with live health monitoring, compliance badges, architecture
> overview, and quick-action links -- out of the box.

---

## 5b. Preview Dashboard Locally

Before deploying to Azure, run the dashboard locally to verify everything works:

```powershell
# Navigate to the generated app
cd my-first-output/src/app

# Install dependencies
pip install fastapi uvicorn pydantic pydantic-settings

# Start the local server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000` in your browser. The dashboard is fully interactive:

| Action | How |
|--------|-----|
| **Summary bar** | Total records, active count, entity count, items needing attention |
| **Entity KPI cards** | Donut charts showing status distribution per entity |
| **View data** | Smart tables with 5-7 key columns and type-aware rendering (badges, dates, progress bars) |
| **Filter by status** | Click status filter pills above the table |
| **Create record** | Click "+" button, fill the type-aware modal form (date pickers, number inputs, textareas) |
| **Update status** | Click a row, use action buttons (dispatch, approve, verify) |
| **Delete record** | Click a row, press Delete with confirmation modal |
| **Export CSV** | Click the download icon to export entity data |
| **Search** | Type in the search box above each table |
| **Detail page** | Click any row — grouped field sections with breadcrumb navigation |
| **Health check** | Green dot in header = server healthy |

> **No database or Azure resources required.** Local mode uses in-memory storage
> with auto-seeded data. Data resets on server restart.

Alternatively, run with Docker:

```powershell
cd my-first-output/src/app
docker build -t my-app .
docker run -p 8000:8000 my-app
# Open http://localhost:8000
```

---

## 6. Validate Governance

```powershell
devex validate ./my-first-output
```

Runs 25 governance policy checks and drift-aware validation against the generated scaffold.

---

## 7. Create Your Own Intent

```powershell
devex init -o ./my-first-output -p my-first-output
```

Edit `./my-first-output/intent.md` with your business requirements, then:

```powershell
devex scaffold --file ./my-first-output/intent.md -o ./my-first-output
```

---

## 8. Try Other Examples

The [`examples/`](examples/) folder includes additional intent files:

```powershell
devex scaffold --file examples/contract-review-intent.md -o ./contract-review
devex scaffold --file examples/doc-intelligence-intent.md -o ./doc-intelligence
devex scaffold --file examples/propane-delivery-intent.md -o ./propane-delivery
devex scaffold --file examples/metro-command-intent.md -o ./metro-command-output
```

The Metro Command intent (`metro-command-intent.md`) is the recommended showcase example — 14 entities, all 6 data stores, 8 AI agents, and demonstrates the full production dashboard with donut charts, type-aware rendering, and grouped detail pages.

Each generates a full scaffold with CI/CD workflows ready to push and deploy. The orchestrator uses semantic extraction to discover entities and endpoints from any business domain -- no hardcoded templates.

---

## 9. Iterate with Versioned Intents

```powershell
devex new-version ./my-first-output
# Edit ./my-first-output/intent.v2.md with changes
devex upgrade --file ./my-first-output/intent.v2.md -o ./my-first-output
devex history ./my-first-output
```

Recommended iteration loop:

1. Review `docs/improvement-suggestions.md` in your output
2. Update the intent version
3. Run `devex upgrade`
4. Push changes and deploy

---

## 10. Push to GitHub

Create a new repo on GitHub, then push the scaffold:

```powershell
cd my-first-output
git init
git add .
git commit -m "Initial enterprise scaffold"
git remote add origin https://github.com/<your-username>/my-first-output.git
git branch -M main
git push -u origin main
```

The generated `.github/workflows/` folder contains:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `validate.yml` | Pull requests | Lint, test, Bicep build, `az deployment validate` |
| `deploy.yml` | `workflow_dispatch` | Deploy Bicep infra, build Docker, push to ACR, update Container App |
| `codeql.yml` | Push / schedule | Code scanning (GitHub Advanced Security) |
| `dependabot.yml` | Schedule | Dependency updates for pip and GitHub Actions |

---

## 11. Deploy to Azure (Optional)

Deployment requires Azure CLI (`az`) and an active Azure subscription.

### a. Configure Azure OIDC for GitHub Actions

The generated workflows use **OpenID Connect (OIDC)** -- no stored credentials.

```powershell
az login

# Create an Entra ID App Registration
az ad app create --display-name "my-first-output-cicd"
# Note the appId from the output

# Create a Service Principal
az ad sp create --id <appId>

# Add Federated Credential
az ad app federated-credential create --id <appId> --parameters '{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:<your-username>/my-first-output:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'

# Assign Contributor Role
az role assignment create `
  --assignee <appId> `
  --role Contributor `
  --scope /subscriptions/<subscription-id>
```

### b. Set GitHub Repository Secrets

In your GitHub repo, go to **Settings > Secrets and variables > Actions** and add:

| Secret | Value |
|--------|-------|
| `AZURE_CLIENT_ID` | App registration `appId` |
| `AZURE_TENANT_ID` | Your Entra ID tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |

### c. Run the Deploy Workflow

1. Go to your repo on GitHub, then **Actions** tab
2. Select the **Deploy** workflow
3. Click **Run workflow**, choose `dev` environment, then **Run workflow**

The deploy pipeline:

1. Logs in via OIDC (no secrets stored)
2. Deploys Bicep infrastructure (Container Apps, ACR, Key Vault, Log Analytics)
3. Builds and pushes the Docker image to ACR
4. Updates the Container App with the new image
5. Runs a health check against the deployed endpoint

---

## 12. Cleanup

Generated folders are disposable:

```powershell
Remove-Item -Recurse -Force ./my-first-output -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./contract-review -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./doc-intelligence -ErrorAction SilentlyContinue
```

To delete Azure resources:

```powershell
az group delete --name rg-<project-name>-dev --yes --no-wait
```

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `devex init` | Create an intent.md template |
| `devex plan` | Preview architecture plan (no files written) |
| `devex scaffold` | Generate full production scaffold |
| `devex validate` | Validate scaffold against 25 governance policies |
| `devex deploy` | Deploy to Azure (staged) |
| `devex upgrade` | Upgrade scaffold with new intent version |
| `devex history` | View version history |
| `devex new-version` | Generate upgrade intent template |
| `devex version` | Show orchestrator version info |
| `devex providers` | List supported LLM providers and models |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `devex` not found | Activate venv: `.venv\Scripts\Activate.ps1` |
| "No intent provided" | Pass `--file` or quote inline: `devex scaffold "Build an API" -o ./out` |
| LLM connection error | Expected -- falls back to template-only mode automatically |
| pip install fails | Check Python 3.11+: `python --version` |
| GitHub Actions OIDC fails | Verify federated credential `subject` matches your repo/branch |
| `az deployment` errors | Run `az account show` and check subscription |

---

*Enterprise DevEx Orchestrator v1.4.0*


