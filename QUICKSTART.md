# Quickstart

End-to-end guide: generate an enterprise scaffold from an intent file, push it to GitHub, and deploy to Azure via GitHub Actions.

## Prerequisites

- Python 3.11+
- Git
- PowerShell (Windows) or a Unix shell
- GitHub account
- Azure subscription (for deployment)
- Azure CLI (`az`) installed

---

## 1. Clone and Install

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

## 2. Preview the Architecture Plan

Run a plan-only preview to see how the orchestrator interprets the intent without writing files:

```powershell
devex plan --file examples/intent.md
```

JSON output for automation:

```powershell
devex plan --file examples/intent.md -F json
```

## 3. Generate the Scaffold

```powershell
devex scaffold --file examples/intent.md -o ./my-first-output
```

This produces a complete, deployable project:

```
my-first-output/
├── .devex/                    # State and metadata
├── .github/workflows/         # CI/CD pipelines (validate, deploy, codeql, dependabot)
├── infra/bicep/               # Azure Bicep templates (main + modules + parameters)
├── src/app/                   # FastAPI application + Dockerfile
├── tests/                     # Auto-generated test suite
└── docs/                      # Plan, security, WAF, governance, deployment docs
```

## 4. Validate Governance

```powershell
devex validate ./my-first-output
```

This re-runs the 25-policy governance check and drift-aware validation against the generated scaffold.

## 5. Push to a New GitHub Repository

Create a new repo on GitHub (e.g., `my-first-output`), then push the scaffold:

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
| `deploy.yml` | `workflow_dispatch` | Deploy Bicep infra, build Docker image, push to ACR, update Container App |
| `codeql.yml` | Push / schedule | Code scanning (GitHub Advanced Security) |
| `dependabot.yml` | Schedule | Dependency updates for pip and GitHub Actions |

## 6. Configure Azure OIDC for GitHub Actions

The generated workflows use **OpenID Connect (OIDC)** — no stored credentials. Set up a federated identity:

### a. Create an Entra ID App Registration

```powershell
az login
az ad app create --display-name "my-first-output-cicd"
# Note the appId from the output
```

### b. Create a Service Principal

```powershell
az ad sp create --id <appId>
```

### c. Add Federated Credential

```powershell
az ad app federated-credential create --id <appId> --parameters '{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:<your-username>/my-first-output:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

### d. Assign Contributor Role

```powershell
az role assignment create `
  --assignee <appId> `
  --role Contributor `
  --scope /subscriptions/<subscription-id>
```

### e. Set GitHub Repository Secrets

In your GitHub repo, go to **Settings > Secrets and variables > Actions** and add:

| Secret | Value |
|--------|-------|
| `AZURE_CLIENT_ID` | App registration `appId` |
| `AZURE_TENANT_ID` | Your Entra ID tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |

## 7. Deploy via GitHub Actions

1. Go to your repo on GitHub → **Actions** tab
2. Select the **Deploy** workflow
3. Click **Run workflow** → choose `dev` environment → **Run workflow**

The deploy pipeline:
1. Logs in via OIDC (no secrets stored)
2. Deploys Bicep infrastructure (Container Apps, ACR, Key Vault, Log Analytics)
3. Builds and pushes the Docker image to ACR
4. Updates the Container App with the new image
5. Runs a health check against the deployed endpoint

## 8. Iterate with Versioned Intents

```powershell
cd ..  # back to orchestrator root
devex new-version ./my-first-output
# Edit ./my-first-output/intent.v2.md with changes
devex upgrade --file ./my-first-output/intent.v2.md -o ./my-first-output
devex history ./my-first-output
```

For v2+ upgrades, the generator adds `promote.yml` and `rollback.yml` workflows
that deploy as Container Apps revisions with traffic shifting.

Recommended iteration loop:
1. Review `docs/improvement-suggestions.md` in your output
2. Update the intent version
3. Run `devex upgrade`
4. Push changes — `validate.yml` runs on PR, `deploy.yml` on manual dispatch

## 9. Try Other Examples

The [examples/](examples/) folder includes additional intent files:

```powershell
devex scaffold --file examples/contract-review-intent.md -o ./contract-review
devex scaffold --file examples/doc-intelligence-intent.md -o ./doc-intelligence
```

Each generates a full scaffold with its own CI/CD workflows ready to push and deploy.

## 10. Create Your Own Intent

```powershell
devex init -o ./my-project -p my-enterprise-api
```

Edit `./my-project/intent.md` with your business requirements, then:

```powershell
devex scaffold --file ./my-project/intent.md -o ./my-project
```

## 11. Cleanup

Generated folders are disposable:

```powershell
Remove-Item -Recurse -Force ./my-first-output -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./contract-review -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./doc-intelligence -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ./my-project -ErrorAction SilentlyContinue
```

To delete Azure resources:

```powershell
az group delete --name rg-<project-name>-dev --yes --no-wait
```

## Command Reference

| Command | Purpose |
|---------|---------|
| `devex init` | Create an intent.md template |
| `devex plan` | Preview architecture plan (no files) |
| `devex scaffold` | Generate full production scaffold |
| `devex validate` | Validate scaffold against policies |
| `devex deploy` | Deploy to Azure (staged) |
| `devex upgrade` | Upgrade scaffold with new intent version |
| `devex history` | View version history |
| `devex new-version` | Generate upgrade intent template |
| `devex version` | Show orchestrator version info |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `devex` not found | Activate venv: `.venv\Scripts\Activate.ps1` |
| "No intent provided" | Pass `--file` or quote inline: `devex scaffold "Build an API" -o ./out` |
| "No .devex metadata found" | Run `devex scaffold` before `validate` / `deploy` / `upgrade` |
| LLM connection error | Expected — auto-falls back to template-only mode |
| pip install fails | Check Python 3.11+: `python --version` |
| GitHub Actions OIDC fails | Verify federated credential `subject` matches your repo/branch |
| `az deployment` errors | Run `az account show` and check subscription selection |

---

*Enterprise DevEx Orchestrator v1.1.0 | Enterprise proof-of-concept*
*486 tests | 25 governance policies | 26 WAF principles | 135/135 scorecard*


