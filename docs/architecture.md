# Architecture Overview

> **Enterprise DevEx Orchestrator** -- 4-Agent Chain Architecture
> Transforms business intent into production-ready Azure workloads

---

## High-Level Flow

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0078D4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#005A9E', 'lineColor': '#555', 'fontFamily': 'Segoe UI', 'fontSize': '13px'}}}%%
flowchart TD
    UI["👤 User Intent"]:::user
    CLI["📋 CLI / DevEx Command"]:::cli
    IP["🤖 Intent Parser Agent"]:::agent
    AP["🏗️ Architecture Planner Agent"]:::agent
    PO["Plan Output +\nADRs + Threat Model"]:::plan
    GR["🔍 Governance Reviewer\n+ WAF Assessor"]:::reviewer
    IG["⚙️ Infrastructure\nGenerator Agent"]:::generator
    IS["📄 IntentSpec Schema"]:::schema
    GS1["📦 Generated Scaffold"]:::scaffold
    GS2["📦 Generated Scaffold"]:::scaffold

    UI --> CLI --> IP --> AP
    IP --> IS --> GS1
    AP -.- PO
    PO -->|"Pass"| IG
    PO -->|"Fail"| GR
    GR -->|"Feedback\nLoop"| AP
    IG --> GS2

    subgraph MCP["MCP Tool Servers"]
        direction LR
        AV["✅ Azure\nValidator"]:::tool
        PE["⚖️ Policy\nEngine"]:::tool
        TR["📝 Template\nRenderer"]:::tool
    end

    GS1 -..-> MCP
    GS2 -..-> MCP

    MCP --> IB["infra / bicep"]:::artifact
    MCP --> GW[".github / workflows"]:::artifact
    MCP --> SA["src / app"]:::artifact
    MCP --> FE["frontend"]:::artifact
    MCP --> DC["docs"]:::artifact
    MCP --> TS["tests"]:::artifact

    classDef user fill:#fff,stroke:#0078D4,color:#333,stroke-width:2px
    classDef cli fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    classDef agent fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    classDef plan fill:#263238,stroke:#37474F,color:#fff,stroke-width:2px
    classDef reviewer fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    classDef generator fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    classDef schema fill:#E8F4FD,stroke:#0078D4,color:#333,stroke-width:2px
    classDef scaffold fill:#546E7A,stroke:#37474F,color:#fff,stroke-width:2px
    classDef tool fill:#FFB900,stroke:#D48C00,color:#333,stroke-width:2px
    classDef artifact fill:#fff,stroke:#0078D4,color:#333,stroke-width:1px

    style MCP fill:none,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5,color:#333

    linkStyle 4 stroke:#107C10,stroke-width:2px
    linkStyle 5 stroke:#D13438,stroke-width:2px
```

## Component Architecture

### Core Pipeline

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0078D4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#005A9E', 'lineColor': '#555', 'fontFamily': 'Segoe UI', 'fontSize': '18px'}}}%%
flowchart LR
    subgraph ORCH["🔷 Orchestrator Agent"]
        O1["📋 CLI · 10 commands"]:::agent
        O2["🤖 Intent Parser"]:::agent
        O3["🏗️ Architecture Planner"]:::agent
        O4["🔍 Governance Reviewer + WAF"]:::agent
        O5["⚙️ Infrastructure Generator"]:::agent
    end

    subgraph GENS["🟩 9 Generators"]
        G1["🔧 Bicep"]:::gen
        G2["🔄 CI/CD"]:::gen
        G3["📦 App"]:::gen
        G4["🖥️ Frontend"]:::gen
        G5["📄 Docs"]:::gen
        G6["🧪 Tests"]:::gen
        G7["🔔 Alerts"]:::gen
        G8["💰 Cost"]:::gen
        G9["📊 Dashboard"]:::gen
    end

    ORCH ==>|"Plugin Protocol"| GENS

    classDef agent fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    classDef gen fill:#E8F5E9,stroke:#107C10,color:#333,stroke-width:2px
    style ORCH fill:#E8F4FD,stroke:#0078D4,stroke-width:3px,color:#0078D4
    style GENS fill:#E8F5E9,stroke:#107C10,stroke-width:3px,color:#107C10
```

### Standards, Patterns & Tools

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0078D4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#005A9E', 'lineColor': '#555', 'fontFamily': 'Segoe UI', 'fontSize': '18px'}}}%%
flowchart LR
    subgraph STD["🟧 Enterprise Standards"]
        S1["📛 Naming"]:::std
        S2["🏷️ Tagging"]:::std
        S3["🌐 Domain Context"]:::std
        S4["📏 Deploy Profile"]:::std
        S5["🗺️ Route Manifest"]:::std
        S6["🎨 Design System"]:::std
        S7["✅ Scaffold Validator"]:::std
    end

    subgraph ADV["🟪 Advanced Patterns"]
        A1["🧩 Skills Registry"]:::adv
        A2["🔀 Subagent Dispatcher"]:::adv
        A3["📋 Persistent Planner"]:::adv
        A4["💡 Prompt Generator"]:::adv
        A5["🚀 Deploy Orchestrator"]:::adv
    end

    subgraph TOOLS["⬛ 9 MCP Tools"]
        T1["validate_bicep"]:::tool
        T2["check_policy"]:::tool
        T3["check_region"]:::tool
        T4["render_template"]:::tool
        T5["preview_output"]:::tool
    end

    ADV ==> TOOLS

    classDef std fill:#FFF3E0,stroke:#D48C00,color:#333,stroke-width:2px
    classDef adv fill:#F3E5F5,stroke:#7B1FA2,color:#333,stroke-width:2px
    classDef tool fill:#F5F5F5,stroke:#616161,color:#333,stroke-width:2px
    style STD fill:#FFF3E0,stroke:#D48C00,stroke-width:3px,color:#D48C00
    style ADV fill:#F3E5F5,stroke:#7B1FA2,stroke-width:3px,color:#7B1FA2
    style TOOLS fill:#F5F5F5,stroke:#616161,stroke-width:3px,color:#333
```

### Azure Target Resources

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0078D4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#005A9E', 'lineColor': '#555', 'fontFamily': 'Segoe UI', 'fontSize': '18px'}}}%%
flowchart LR
    GEN["⚙️ Generators"]:::gen ==> AZ

    subgraph AZ["🔷 Azure Resources"]
        R1["📦 Container Apps"]:::azure
        R2["🔐 Key Vault"]:::azure
        R3["📊 Log Analytics"]:::azure
        R4["🔑 Managed Identity"]:::azure
        R5["🗄️ Container Registry"]:::azure
    end

    classDef gen fill:#E8F5E9,stroke:#107C10,color:#333,stroke-width:2px
    classDef azure fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    style AZ fill:#E8F4FD,stroke:#0078D4,stroke-width:3px,color:#0078D4
```

## Data Flow

| Stage | Input | Processing | Output |
|-------|-------|-----------|--------|
| 1. Parse | Plain-text intent or `intent.md` | LLM extraction + 5-phase semantic entity extraction + rule-based fallback | `IntentSpec` (Pydantic) with `DomainType`, semantically-extracted entities, endpoints |
| 2. Plan | `IntentSpec` | Component selection, 6 ADRs, STRIDE threat model, Mermaid diagram | `PlanOutput` |
| 3. Review | `IntentSpec` + `PlanOutput` | 25-policy validation, WAF 5-pillar assessment (26 principles) | `GovernanceReport` + `WAFAlignmentReport` |
| 4. Generate | All above | 9 generators produce Bicep, workflows, app, frontend, docs, tests, alerts, cost, dashboard | `dict[str, str]` file map |
| 5. Record | Generated files | SHA-256 manifest, drift detection, audit trail | `.devex/state.json` |
| 6. Deploy | Output directory | 4-stage: validate -> what-if -> deploy -> verify | Deployment result |

## Security Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0078D4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#005A9E', 'lineColor': '#555', 'fontFamily': 'Segoe UI', 'fontSize': '13px'}}}%%
flowchart TD
    subgraph IAM["🔑 Identity & Access"]
        MI["Managed Identity\nproject-env-id"]:::azure
        RBAC["RBAC Assignments"]:::azure
    end

    subgraph SEC["🔐 Secrets Management"]
        KV["Key Vault\nprojectenvkv\nSoft-delete · Purge Protection"]:::keyvault
    end

    subgraph COMP["📦 Compute"]
        CA["Container App\nproject-env\nNon-root · Read-only FS"]:::azure
        ACR["Container Registry\nprojectenvacr\nPremium · No Admin"]:::azure
    end

    subgraph OBS["📊 Observability"]
        LA["Log Analytics\nproject-env-law"]:::azure
    end

    subgraph CICD["🔄 CI/CD Security"]
        GH["GitHub Actions"]:::cicd
        OIDC["OIDC Federation\nZero Stored Credentials"]:::cicd
        ENTRA["Microsoft Entra ID"]:::entra
    end

    MI -->|"Key Vault\nSecrets User"| KV
    MI -->|"AcrPull"| ACR
    CA -->|"Uses"| MI
    CA -->|"Reads secrets"| KV
    CA -->|"Sends logs"| LA
    KV -->|"Diagnostics"| LA
    ACR -->|"Diagnostics"| LA
    GH -->|"OIDC token"| OIDC
    OIDC -->|"Federated auth"| ENTRA

    classDef azure fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px
    classDef keyvault fill:#FFB900,stroke:#D48C00,color:#333,stroke-width:2px
    classDef cicd fill:#50E6FF,stroke:#0078D4,color:#333,stroke-width:2px
    classDef entra fill:#0078D4,stroke:#005A9E,color:#fff,stroke-width:2px

    style IAM fill:#E8F4FD,stroke:#0078D4,stroke-width:3px,color:#0078D4
    style SEC fill:#FFF3E0,stroke:#FFB900,stroke-width:3px,color:#D48C00
    style COMP fill:#E8F4FD,stroke:#0078D4,stroke-width:3px,color:#0078D4
    style OBS fill:#E8F4FD,stroke:#0078D4,stroke-width:3px,color:#0078D4
    style CICD fill:#E0F7FA,stroke:#50E6FF,stroke-width:3px,color:#0078D4
```

## Design Principles

| # | Principle | Implementation |
|---|-----------|---------------|
| 1 | Deterministic Structure | File layout, naming, and module organization are always the same |
| 2 | Controlled Variability | LLM adds context-specific content within deterministic boundaries |
| 3 | Governance by Default | Every scaffold passes 25-policy governance validation before output |
| 4 | Defense in Depth | Identity, encryption, networking, scanning -- multiple security layers |
| 5 | Observable from Day 1 | Log Analytics + diagnostics configured for all resources |
| 6 | Enterprise Standards | Azure CAF naming (20 types) + tagging (12 tags) enforced via YAML |
| 7 | State Awareness | Every generation tracked with drift detection between runs |
| 8 | WAF Aligned | 26/26 Azure Well-Architected Framework principles covered |

## Agent Capabilities Summary

| Agent | Tools | LLM Provider | Fallback | Key Output |
|-------|-------|-------------|----------|-----------|
| Intent Parser | None (pure LLM) | GitHub Copilot SDK (default) | 5-phase semantic extraction engine + domain detection | `IntentSpec` with `DomainType`, entities, endpoints |
| Architecture Planner | `check_policy`, `check_region_availability` | GitHub Copilot SDK (default) | Template-based component builder | `PlanOutput` with ADRs + threat model |
| Governance Reviewer | `check_policy`, `list_policies`, `validate_bicep` | GitHub Copilot SDK (default) | Policy catalog evaluation | `GovernanceReport` + `WAFAlignmentReport` |
| Infrastructure Generator | `render_template`, `preview_output`, `validate_bicep` | GitHub Copilot SDK (default) | Direct file generation | Complete file tree (backend + frontend + infra) |

## LLM Provider Architecture

The orchestrator supports multiple LLM backends with **GitHub Copilot SDK as the default**:

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0078D4', 'primaryTextColor': '#fff', 'primaryBorderColor': '#005A9E', 'lineColor': '#6BA4D9', 'fontFamily': 'Segoe UI', 'fontSize': '13px'}}}%%
flowchart TD
    subgraph LAYER["LLM Provider Layer"]
        direction TB
        subgraph CFG_BOX[" "]
            CFG["⚙️ LLMConfig\nAuto-detect  +  Copilot SDK default"]:::config
        end

        CLIENT["🏭 LLM Client Factory"]:::factory

        CFG_BOX --> CLIENT

        CLIENT --> CS
        CLIENT --> AO
        CLIENT --> OA
        CLIENT --> AN
        CLIENT --> TO
    end

    CS["🐙 GitHub Copilot SDK\n— DEFAULT —"]:::copilot
    AO["Ⓐ Azure OpenAI\ngpt-4o"]:::azure_provider
    OA["◎ OpenAI\ngpt-4o"]:::openai_provider
    AN["Ⓐ Anthropic / Claude\nclaude-opus-4-20250514"]:::anthropic_provider
    TO["⊘ Template-Only\nNo LLM"]:::template_provider

    classDef config fill:#E8F4FD,stroke:#B3D4ED,color:#333,stroke-width:2px
    classDef factory fill:#D6E4F0,stroke:#0078D4,color:#333,stroke-width:2px
    classDef copilot fill:#E8F4FD,stroke:#0078D4,color:#333,stroke-width:2px
    classDef azure_provider fill:#E8F4FD,stroke:#0078D4,color:#333,stroke-width:2px
    classDef openai_provider fill:#E8F4FD,stroke:#0078D4,color:#333,stroke-width:2px
    classDef anthropic_provider fill:#E8F4FD,stroke:#0078D4,color:#333,stroke-width:2px
    classDef template_provider fill:#F5F5F5,stroke:#999,color:#333,stroke-width:2px

    style LAYER fill:#F0F6FC,stroke:#0078D4,stroke-width:3px,color:#0078D4
    style CFG_BOX fill:#E8F4FD,stroke:#B3D4ED,stroke-width:2px,color:#333
```

| Provider | Default Model | Auto-Detect Env Var | Priority |
|----------|--------------|---------------------|----------|
| Azure OpenAI | `gpt-4o` | `AZURE_OPENAI_ENDPOINT` | 1 (highest) |
| Anthropic | `claude-opus-4-20250514` | `ANTHROPIC_API_KEY` | 2 |
| OpenAI | `gpt-4o` | `OPENAI_API_KEY` | 3 |
| GitHub Copilot SDK | `gpt-4o` | `GITHUB_TOKEN` | 4 |
| GitHub Copilot SDK | `gpt-4o` | (none — default fallback) | 5 (always) |

**Key modules:** `config.py` (LLMConfig, auto-detection), `llm_client.py` (provider adapters), `agent.py` (AgentRuntime integration).

## Why This Architecture?

The 4-agent chain isn't just a technical choice — it solves the core enterprise AI adoption problem: **consistency with governance**.

**Why 4 agents instead of 1?** A single AI agent producing everything has no separation of concerns. The Governance Reviewer exists as a *separate* agent specifically so it can reject the Planner's output. This mirrors enterprise design review processes — the person who designs the system shouldn't be the same person who approves it.

**Why schemas instead of chat?** Chat-based AI tools produce non-deterministic output. The IntentSpec Pydantic schema normalizes any business description into a strict typed contract. Two developers describing the same system in different words produce the same schema — and therefore the same downstream output.

**Why deterministic fallbacks?** Enterprise environments often have restricted network access. Every agent has a rule-based fallback that activates if the LLM is unavailable. The orchestrator produces identical output with or without an AI provider — the LLM enhances, but doesn't define, the output.

**Why GitHub Copilot SDK as default?** Most enterprises already have Copilot licenses approved through procurement. Using the SDK as the default LLM provider means zero new vendor approvals, zero new DPAs, and zero new security reviews. Teams can start generating scaffolds immediately on infrastructure they already own.

---

*4-agent chain | 9 MCP tools | 9 generators | 25 policies | 636 tests*
*Multi-provider LLM: GitHub Copilot SDK (default) · Azure OpenAI · OpenAI · Anthropic (Claude)*
*Azure CAF naming + enterprise tagging + WAF 5-pillar alignment*
*Domain-agnostic semantic extraction: Any business domain*
*Backend: Python (FastAPI) · Node.js (Express) · .NET (ASP.NET Core)*
*Frontend: Entity-Driven React 18 + Vite 5 + TypeScript SPA*
*Dashboard: Interactive CRUD with domain-aware seed data, local preview via `uvicorn`*


