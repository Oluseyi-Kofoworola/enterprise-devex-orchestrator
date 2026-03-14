# Example Intent Files

> Ready-to-use intent files for generating production-ready Azure scaffolds

---

## Overview

This directory contains example intent files that you can pass to `devex scaffold` to generate complete, deployable Azure applications. Each intent file demonstrates enterprise-grade requirement definition with the 9-section structure.

Every generated scaffold includes:

- Full Bicep IaC with 5-10 modules
- GitHub Actions CI/CD (4 workflows)
- FastAPI application with Pydantic validation
- Pytest test suite
- Docker containerization (non-root, multi-stage)
- Managed Identity authentication (zero credentials)
- Complete documentation (7+ files)
- Azure Monitor alerts and runbook
- HIPAA/SOC2 compliance where applicable

---

## Available Examples

### 1. Voice Agent (v1)

**File:** [`intent.md`](intent.md)

A voice-enabled patient information system for a healthcare network. Cross-browser speech recognition with auto-retry, synthetic patient clinical data, appointment scheduling, and multi-turn conversation context.

```powershell
devex scaffold --file examples/intent.md -o ./voice-agent-output
```

### 2. Voice Agent (v2 -- Upgrade)

**File:** [`intent.v2.md`](intent.v2.md)

An upgraded version of the voice agent adding multi-language support, advanced analytics, and blob storage for call recordings. Demonstrates the versioned upgrade workflow.

```powershell
devex upgrade --file examples/intent.v2.md -o ./voice-agent-output
```

### 3. Contract Review AI

**File:** [`contract-review-intent.md`](contract-review-intent.md)

AI-powered legal contract analysis for healthcare. Upload vendor contracts, extract text via Document Intelligence, analyze with GPT-4 against a healthcare risk framework, and generate redline suggestions with protective alternative clauses.

```powershell
devex scaffold --file examples/contract-review-intent.md -o ./contract-review-output
```

### 4. Document Intelligence Extractor

**File:** [`doc-intelligence-intent.md`](doc-intelligence-intent.md)

An enterprise document processing service that accepts uploaded files and processes them through Azure Document Intelligence using prebuilt models (general document, layout, invoice, receipt, ID document).

```powershell
devex scaffold --file examples/doc-intelligence-intent.md -o ./doc-intel-output
```

### 5. Propane Delivery Logistics

**File:** [`propane-delivery-intent.md`](propane-delivery-intent.md)

A propane delivery logistics platform for managing deliveries, tank monitoring, route optimization, and customer management. Demonstrates the semantic extraction engine working on a non-standard business domain with no hardcoded templates.

```powershell
devex scaffold --file examples/propane-delivery-intent.md -o ./propane-delivery-output
```

### 6. Smart City Operations Platform (Stress Test)

**File:** [`smart-city-intent.md`](smart-city-intent.md)

A full-scale smart city operations platform integrating IoT sensor ingestion, emergency response, utility grid management, citizen services, environmental monitoring, transit tracking, parking management, and asset maintenance. Exercises all 4 data stores (Cosmos DB, SQL, Blob, Redis), 10 Bicep modules, FedRAMP + SOC2 + HIPAA compliance, and 8 user personas. Designed to stress-test every generator path.

```powershell
devex scaffold --file examples/smart-city-intent.md -o ./smart-city-output
```

---

## Comparison

| Feature | Voice Agent | Contract Review | Doc Intelligence | Propane Delivery | Smart City |
|---------|-------------|-----------------|------------------|------------------|------------|
| Industry | Healthcare Ops | Legal Ops | Document Processing | Logistics | Government/IoT |
| Primary User | Clinical staff | Legal team | Back-office staff | Delivery operations | City operators |
| Data Stores | None (in-memory) | Blob, Cosmos DB | Blob | Cosmos DB | Cosmos, SQL, Blob, Redis |
| AI/ML | Pattern matching | GPT-4, clause extraction | Document Intelligence | Route optimization | Anomaly detection, NLP |
| Compliance | HIPAA | HIPAA, SOC2 | SOC2 | SOC2 | FedRAMP, SOC2, HIPAA |
| Auth | Entra ID | Entra ID + RBAC | Managed Identity | Managed Identity | Entra ID |
| Entity Discovery | Semantic NLP | Semantic NLP | Semantic NLP | Semantic NLP | Semantic NLP |
| Bicep Modules | 5 | 6 | 5 | 6 | 10 |

---

## How to Use

### Option 1: Use an existing intent file

```powershell
devex scaffold --file examples/contract-review-intent.md -o ./my-contract-review
```

### Option 2: Create your own

```powershell
devex init -o ./my-app -p my-app-name
# Edit my-app/intent.md with your business requirements
devex scaffold --file my-app/intent.md -o ./my-app
```

### Option 3: Quick inline test

```powershell
devex scaffold "Build a healthcare appointment scheduler with SMS reminders" -o ./scheduler
```

---

## Writing a Good Intent File

The best results come from filling all 9 enterprise sections:

| Section | Purpose |
|---------|---------|
| Problem Statement | Business problem, affected users, cost of inaction |
| Business Goals | Measurable KPIs, revenue/cost impact |
| Target Users | User personas with roles and proficiency |
| Functional Requirements | Features, endpoints, workflows |
| Scalability Requirements | Concurrent users, RPS, data volume |
| Security & Compliance | Auth, RBAC, encryption, compliance frameworks |
| Performance Requirements | p50/p95/p99 latency, SLA, RTO/RPO |
| Integration Requirements | Upstream/downstream systems, events |
| Acceptance Criteria | Functional tests, benchmarks, security scans |

See [`contract-review-intent.md`](contract-review-intent.md) as a comprehensive example.

---

*Enterprise DevEx Orchestrator v1.6.0*



