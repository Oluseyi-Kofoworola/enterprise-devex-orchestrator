# Changelog

All notable changes to the Enterprise DevEx Orchestrator.

---

## [1.7.0] - 2026-03-17

### Added
- **Domain Context** — 12 industry-specific intelligence models (`DomainContext`) providing org names, email domains, terminology, seed data pools, compliance frameworks, and UI branding per domain (healthcare, legal, fintech, logistics, retail, manufacturing, agriculture, government, cybersecurity, IoT/smart city, document processing, finance). New file: `src/orchestrator/generators/domain_context.py`.
- **Deployment Profiles** — Environment-aware resource sizing (`DeploymentProfile`, `SKUSelector`) with structured SKU tables for compute, datastores, and core infra across 4 workload tiers (DEV/STAGING/PROD_LOW/PROD_HIGH). New file: `src/orchestrator/generators/deployment_profile.py`.
- **Route Manifest** — Canonical API route registry (`RouteManifest`, `RouteBuilder`) consumed by TestGenerator and ScaffoldValidator for deterministic test generation and route-test alignment validation. New file: `src/orchestrator/generators/route_manifest.py`.
- **Scaffold Validator** — Post-generation cross-generator consistency checks (5 validation rules: required files, entity coverage, route-test alignment, Bicep completeness, Dockerfile presence). Produces `docs/validation-report.md`. New file: `src/orchestrator/generators/scaffold_validator.py`.
- **LLM Enricher** — Optional AI enrichment layer with type-constrained targets, guardrails against code injection and prompt manipulation, and batch processing support. New file: `src/orchestrator/generators/llm_enricher.py`.
- **Design System** — Domain-aware design tokens and Tailwind CSS theming with 10 industry presets, dark mode toggle, WCAG AA accessible. New file: `src/orchestrator/generators/design_system.py`.
- **84 new tests** — `test_deployment_profile.py`, `test_domain_context.py`, `test_llm_enricher.py`, `test_route_manifest.py`, `test_scaffold_validator.py`. Total: **745 tests**.

### Changed
- **App Generator** — Now uses `DomainContext` for domain-aware seed data (12 realistic records per entity), CORS middleware for frontend dev servers, rate limiting middleware, OWASP security headers. Eliminated hardcoded domain leakage.
- **CI/CD Generator** — Language-aware lint/test steps, CodeQL language detection, Dependabot ecosystem mapping (Python/Node/dotnet).
- **Cost Estimator** — Uses `DeploymentProfile` for accurate per-environment costing instead of flat estimates.
- **Test Generator** — RouteManifest-driven entity CRUD test generation covering LIST/CREATE/GET/DELETE/CUSTOM actions.
- **Infrastructure Generator Agent** — Now runs ScaffoldValidator post-generation and outputs `docs/validation-report.md`.
- **Intent Schema** — `DomainType` expanded from 4 to 12 domain types.

### Fixed
- **Tailwind CSS pipeline** — Added `@tailwind base/components/utilities` directives to generated CSS, import via `main.tsx` instead of HTML link tag (enables Vite/PostCSS processing).
- **API response normalization** — Added `Array.isArray()` guards at 5 fetch-to-state patterns in frontend to prevent `forEach` crash when API returns object instead of array.
- **Frontend CSP** — Removed bypassing `<link>` tag from `index.html`; CSS now bundled via Vite/PostCSS.

---

## [1.6.0] - 2026-03-17

### Added
- **Generator Plugin Protocol** — Uniform `generate(spec, context)` interface for all 9 generators via `GeneratorProtocol` (Python `typing.Protocol`), `GeneratorAdapter`, `GeneratorRegistry`, and `GeneratorContext`. New file: `src/orchestrator/generators/protocol.py`.
- **create_default_registry()** — Factory function that pre-loads all built-in generators with correct bridge functions. Adding a new generator requires one import + one `register()` call.
- **25 new protocol tests** — `tests/test_protocol.py` covering context, protocol conformance, adapter bridges, registry operations, and integration with `InfrastructureGeneratorAgent`.

### Changed
- **InfrastructureGeneratorAgent** — Refactored from 9 hardcoded imports/instantiations/calls to a single `registry.run_all(spec, context)` call. Open-Closed Principle: no agent changes needed for new generators.
- **generators/__init__.py** — Now exports `GeneratorProtocol`, `GeneratorContext`, `GeneratorRegistry`, `GeneratorAdapter`, `create_default_registry`.

---

## [1.5.0] - 2026-03-15

### Fixed
- **Seed data overflow** — Float handler now caps percentage fields (progress, accuracy, rate) to 15-99% range. No more 1500% progress values.
- **GitHub Actions triple braces** — Fixed f-string brace escaping in `deploy.yml` generation. `${{{ secrets.X }}}` → `${{ secrets.X }}`.
- **Rate limiter too aggressive** — Increased default from 120 to 600 requests/min. Dashboards with 8+ entities no longer trigger 429 cascades.
- **CSP blocks React dev mode** — Added `'unsafe-eval'` to Content-Security-Policy `script-src` for Vite's React Fast Refresh.
- **FastAPI description crash** — Backslash characters in entity descriptions no longer cause SyntaxError on startup.
- **Key Vault unreachable** — Changed `publicNetworkAccess` from `'Disabled'` to `'Enabled'` (with `AzureServices` bypass) since private endpoints aren't provisioned by default.
- **Cosmos DB 404 on first write** — Added default container resource with `/partitionKey` partition key and 400 RU/s.
- **Container resources too small** — Increased from 0.5 CPU / 1 GiB to 1.0 CPU / 2 GiB.
- **Frontend missing PUT/DELETE** — Added `update{Entity}` and `delete{Entity}` methods to generated API client.
- **Status transition typos** — Added `_past_tense()` helper for correct verb conjugation (dispatched, verified, etc.).
- **AI keyword detection** — Added "intelligence", "cognitive", "vision", "recognition" to Intent Parser AI keyword list.

### Improved
- QUICKSTART.md — Added troubleshooting table, venv activation reminders, terminal session guidance.

---

## [1.4.0] - 2026-03-10

### Added
- **Document Intelligence support** — Full file upload/processing pipeline with `FileUpload` entity and multipart endpoints.
- **Comma-separated endpoint parsing** — Intent Parser now handles `GET /items, POST /items, DELETE /items/:id` in a single line.
- **Expanded action verb detection** — 12 new verbs: analyze, classify, extract, validate, process, convert, review, approve, reject, assign, schedule, notify.

### Fixed
- Upload page crash — Rewrote with proper `selectedFile` state, `fileInputRef`, and two-step FormData upload flow.
- Logger key conflict — Fixed duplicate `type` key in structured logging for dynamic services.
- Schema flexibility — `_dynamic_schemas()` now handles entities with varying field counts gracefully.

---

## [1.3.0] - 2026-03-05

### Added
- **Frontend Generator** — Entity-driven React + Vite + TypeScript SPA with design-token theming (10 industry presets), dark mode, responsive mobile nav, loading skeletons, error boundaries, toast notifications, SVG icons, mini charts, pagination, sortable columns, delete confirmation modals.
- **Dashboard Generator** — Enterprise dashboard with health monitoring, compliance badges, architecture overview, quick-action links.
- **Alert Generator** — Azure Monitor alert rules (Bicep), action groups, and alerting runbook.
- **Test Generator** — Auto-generated pytest suite covering health, API, security, config, and storage.
- **Cost Estimator** — Azure pricing estimates based on selected services and SKUs.

### Improved
- App Generator — 12 realistic seed records per entity with domain-aware values (names, addresses, timestamps relative to current date).
- App Generator — CORS middleware for frontend dev servers (localhost:3000/5173), rate limiting, OWASP security headers.

---

## [1.2.0] - 2026-02-25

### Added
- **WAF Assessor** — Azure Well-Architected Framework assessment across 5 pillars and 26 design principles with per-pillar scoring.
- **Skills Registry** — Pluggable skill system with 9 built-in skills across 12 categories.
- **Subagent Dispatcher** — Parallel fan-out execution with ThreadPoolExecutor and structured result aggregation.
- **Persistent Planner** — Manus-style checkpoint-based 13-task execution with retry logic and plan history.
- **Deploy Orchestrator** — 4-stage Azure deployment: validate → what-if → deploy → verify.

### Improved
- Governance Reviewer — AI governance checks for AI workloads (content safety, RAI, model governance).
- Policy Engine — Expanded to 25 policies including WAF alignment rules.

---

## [1.1.0] - 2026-02-15

### Added
- **Multi-provider LLM support** — Azure OpenAI, OpenAI, Anthropic (Claude), GitHub Copilot SDK, and template-only mode.
- **Intent File System** — Markdown-based declarative intent files with 9 enterprise requirement sections and completeness tracking.
- **Version Management** — Track scaffold versions, plan upgrades, support rollback. State in `.devex/versions.json`.
- **State Manager** — Persistent state in `.devex/state.json` with SHA-256 file manifests and drift detection.
- **Prompt Generator** — Scans user repos to detect languages, frameworks, and CI/CD config for context-enriched prompts.

---

## [1.0.0] - 2026-02-01

### Added
- **4-agent chain architecture** — Intent Parser → Architecture Planner → Governance Reviewer → Infrastructure Generator.
- **Intent Parser** — LLM extraction with 5-phase semantic fallback engine and rule-based keyword extraction.
- **Architecture Planner** — Azure component selection, ADRs, STRIDE threat model, Mermaid diagrams.
- **Governance Reviewer** — 25-policy validation with feedback loop to Architecture Planner (max 2 iterations).
- **Bicep Generator** — 7 modules with Azure CAF naming (22 resource types, 34 regions) and enterprise tagging (7 required tags).
- **CI/CD Generator** — 4 GitHub Actions workflows (validate, deploy, CodeQL, Dependabot) with OIDC authentication.
- **App Generator** — FastAPI scaffold with entity-driven CRUD, Managed Identity, structured logging, health probes, Dockerfile (non-root).
- **Docs Generator** — 7 documentation files including plan, security, deployment, RAI notes, governance scorecard.
- **Naming Engine** — Azure CAF naming conventions for 22 resource types.
- **Tagging Engine** — 7 required + 5 optional enterprise tags with regex validation.
- **CLI** — 8 commands: init, plan, scaffold, validate, deploy, upgrade, history, new-version, version.
- **GitHub Copilot SDK as default provider** — Zero-configuration LLM integration.

---

*Enterprise DevEx Orchestrator — Built on GitHub Copilot SDK*
