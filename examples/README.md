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

A full-scale smart city operations platform integrating IoT sensor ingestion, emergency response, utility grid management, citizen services, environmental monitoring, transit tracking, fleet management, and asset maintenance. Exercises all 6 data stores (Cosmos DB, SQL, Blob, Redis, AI Search, Table Storage), 10 Bicep modules, FedRAMP + SOC2 + HIPAA compliance, 9 entities, and 11 user personas. Designed to stress-test every generator path.

```powershell
devex scaffold --file examples/smart-city-intent.md -o ./smart-city-output
```

### 7. Extreme Healthcare Network (Extreme Stress Test)

**File:** [`extreme-healthcare-intent.md`](extreme-healthcare-intent.md)

A unified healthcare network platform exercising every parser and generator limit: **15 entities** (Patient, Claim, Provider, Appointment, Prescription, LabOrder, ImagingStudy, NursingAssessment, SurgicalCase, MedicalDevice, ClinicalTrial, Referral, PortalMessage, BillingRecord, ComplianceAuditLog) with up to **25 fields each**, all 6 data stores, multi-parameter endpoint paths (`/patients/{patient_id}/prescriptions/{prescription_id}/interactions`), complex field types (`list[str]`, `list[float]`, `list[int]`), H4 sub-headings, em-dash enum descriptions, 45 heading alias variants, and HIPAA + SOC2 + FedRAMP compliance. Designed to validate every hardened parser capability.

```powershell
devex scaffold --file examples/extreme-healthcare-intent.md -o ./extreme-healthcare-output
```

---

## Comparison

| Feature | Voice Agent | Contract Review | Doc Intelligence | Propane Delivery | Smart City | Extreme Healthcare |
|---------|-------------|-----------------|------------------|------------------|------------|--------------------|
| Industry | Healthcare Ops | Legal Ops | Document Processing | Logistics | Government/IoT | Healthcare Network |
| Primary User | Clinical staff | Legal team | Back-office staff | Delivery operations | City operators | Clinical staff |
| Entities | 3 | 3 | 3 | 4 | 9 | **15** |
| Data Stores | None (in-memory) | Blob, Cosmos DB | Blob | Cosmos DB | All 6 | **All 6** |
| AI/ML | Pattern matching | GPT-4, clause extraction | Document Intelligence | Route optimization | Multi-agent AI | Multi-agent AI |
| Compliance | HIPAA | HIPAA, SOC2 | SOC2 | SOC2 | FedRAMP, SOC2, HIPAA | **HIPAA, SOC2, FedRAMP** |
| Auth | Entra ID | Entra ID + RBAC | Managed Identity | Managed Identity | Entra ID | Entra ID |
| Entity Discovery | Semantic NLP | Semantic NLP | Semantic NLP | Semantic NLP | Semantic NLP | **Explicit + Semantic** |
| Bicep Modules | 5 | 6 | 5 | 6 | 10 | **10+** |
| Multi-param paths | No | No | No | No | No | **Yes** |

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

## Preview Dashboard Locally

After scaffolding, preview the interactive dashboard before deploying:

```powershell
cd <output-dir>/src/app
pip install fastapi uvicorn pydantic pydantic-settings
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000`. The dashboard includes:
- **Entity tabs** with pre-seeded domain data
- **Create** records via modal forms
- **Workflow actions** (dispatch, approve, verify) that update record status
- **Search** and health monitoring
- **No database required** -- uses in-memory storage with auto-seeded data

---

*Enterprise DevEx Orchestrator v1.8.0*



