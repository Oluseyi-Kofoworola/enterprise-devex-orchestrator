# demo-voice-agent

> An enterprise-grade AI-powered voice agent platform for Demo Health System's
> 14-clinic network. v2 extends the platform with AI Search RAG integration,
> 2 new entities (Referral and LabOrder), predictive analytics dashboards,
> multi-language voice support (English/Spanish/Mandarin), and enhanced compliance
> with FedRAMP Moderate in addition to HIPAA and SOC2.

## Problem Statement

Demo Health System deployed the v1 AI voice agent platform with 12 entities,
4 Semantic Kernel agents, and 5 data stores across 14 clinics. v1 resolved core
automation problems — call wait time dropped from 8 minutes to 25 seconds, and
75% of routine calls are handled without human escalation. v2 addresses gaps
identified in the 6-month pilot: referral coordination between clinics still
takes 5 days (target: 24 hours), lab result delivery is not integrated with
the voice platform, 12% of callers speak Mandarin and cannot use the
English/Spanish agent, predictive analytics for no-show and equipment failure
are rule-based rather than AI-driven, and the platform requires FedRAMP
Moderate for an upcoming VA partnership.

## Business Objectives

- All v1 KPIs carried forward and tightened: CSAT > 4.7/5.0, handle time < 45 seconds
- Add Mandarin voice support (third language, 12% of caller base)
- Reduce referral completion time from 5 days to under 24 hours via AI-powered provider matching
- Integrate lab order tracking: patients query results via voice, clinicians receive AI-interpreted results
- Deploy AI Search as the RAG backbone for 50,000+ knowledge articles (replacing keyword-only search)
- Upgrade predictive analytics from rule-based to AI-driven: no-show prediction (> 90% accuracy), equipment failure prediction (> 85% at 72-hour horizon)
- Achieve FedRAMP Moderate certification alongside existing HIPAA + SOC2
- New KPI: Referral completion rate > 95% within 48 hours
- New KPI: Lab result voice query resolution > 85% without escalation

## User Roles

1. **Patient** — Calls to schedule, request refills, query lab results, ask billing questions, report symptoms; low proficiency
2. **Front-Desk Coordinator** — Monitors dashboard, handles escalations, manages check-in; intermediate proficiency
3. **Clinical Staff (Nurse/PA)** — Receives triaged calls, reviews AI-interpreted lab results; intermediate proficiency
4. **Attending Physician** — Reviews triage, approves prescriptions, manages referrals; high clinical proficiency
5. **Pharmacist** — Reviews AI drug interactions, verifies refills; intermediate proficiency
6. **Workforce Manager** — Manages schedules, reviews AI shift optimization; intermediate proficiency
7. **Facility Operations Manager** — Monitors equipment, reviews AI maintenance predictions; intermediate proficiency
8. **Lab Coordinator** — Manages lab orders, reviews AI interpretations, handles critical value alerts; intermediate proficiency
9. **Referral Coordinator** — Manages inter-facility referrals, reviews AI provider matching scores; intermediate proficiency
10. **IT Administrator** — Platform configuration, monitoring, AI performance tuning; high proficiency
11. **Compliance Officer** — PHI audit logs, AI interaction logs, FedRAMP compliance reports; low proficiency
12. **Quality Assurance Analyst** — Reviews recordings, evaluates AI accuracy, CSAT analysis; intermediate proficiency

## Functional Requirements

### Enhanced AI Capabilities (v2)
- All v1 AI agents carried forward (TriageAgent, SchedulingAgent, PharmacyAgent, AnalyticsAgent)
- New agent: ReferralAgent — AI-powered provider matching, availability checking, and referral status tracking
- New agent: LabAgent — AI-interpreted lab results, trend analysis, critical value alerting
- AI Search RAG pipeline: 50,000+ documents indexed with text-embedding-ada-002, hybrid semantic + BM25 search
- Predictive analytics upgrade: ML-powered no-show prediction and equipment failure forecasting
- Multi-language: English, Spanish, and Mandarin with automatic detection in first 3 seconds

### All v1 Entity Endpoints Preserved (Regression)
- VoiceSession, Patient, Appointment, Prescription, TriageRecord, Provider, Facility, StaffMember, Equipment, InsuranceClaim, KnowledgeArticle, Notification, AuditLog — all CRUD and action endpoints

### Entity: Referral (New in v2)
- Fields: patient_id (str), referring_provider_id (str), receiving_provider_id (str), referral_number (str), referral_type (str — consultation/procedure/diagnostic/therapy/second_opinion), specialty_requested (str), status (str — created/submitted/accepted/scheduled/completed/declined/expired), priority (str — routine/urgent/emergent), clinical_reason (str), diagnosis_codes (list[str]), insurance_authorization (str), authorization_status (str — not_required/pending/approved/denied), notes (str), attachments (list[str]), created_date (str), expiry_date (str), appointment_id (str), ai_provider_match_score (float), ai_suggested_providers (list[str]), ai_urgency_assessment (str), follow_up_required (boolean), follow_up_date (str), completion_report (str), patient_consent (boolean), facility_preference (str)
- POST /api/v1/referrals — Create with AI provider matching
- POST /api/v1/referrals/{referral_id}/submit — Submit to receiving provider
- POST /api/v1/referrals/{referral_id}/accept — Receiving provider accepts
- POST /api/v1/referrals/{referral_id}/decline — Decline with AI re-route to next best provider
- POST /api/v1/referrals/{referral_id}/complete — Complete with outcome report
- GET /api/v1/patients/{patient_id}/referrals/{referral_id}/status — Status with AI ETA

### Entity: LabOrder (New in v2)
- Fields: patient_id (str), provider_id (str), order_number (str), test_name (str), test_code (str), panel_type (str — cbc/cmp/lipid/thyroid/urinalysis/a1c/coagulation/hepatic/renal/cardiac/custom), status (str — ordered/collected/in_progress/resulted/reviewed/cancelled), priority (str — routine/stat/urgent/timed), specimen_type (str), collection_date (str), result_date (str), result_values (list[float]), result_units (list[str]), reference_ranges (list[str]), abnormal_flags (list[str]), critical_value (boolean), ai_interpretation (str), ai_trend_analysis (str), fasting_required (boolean), facility_id (str), ordering_diagnosis (str), notes (str), reviewed_by (str), reviewed_date (str)
- POST /api/v1/lab_orders — Create lab order
- POST /api/v1/lab_orders/{order_id}/collect — Record specimen collection
- POST /api/v1/lab_orders/{order_id}/result — Enter results with AI interpretation
- POST /api/v1/patients/{patient_id}/lab_orders/{order_id}/trends — AI trend analysis
- POST /api/v1/lab_orders/{order_id}/cancel — Cancel with reason

### New Analytics Endpoints (v2)
- GET /api/v1/analytics/predictive/no_shows — AI no-show risk predictions for upcoming appointments
- GET /api/v1/analytics/predictive/equipment_failures — AI equipment failure forecasts
- GET /api/v1/analytics/referral_performance — Referral completion metrics by provider and facility
- GET /api/v1/analytics/lab_turnaround — Lab order turnaround times with benchmarks
- GET /api/v1/health/deep — Validates all 7 backing services (Cosmos, SQL, Redis, Blob, Table, AI Search, Key Vault)

---

## Scalability & Performance

- 2,000 concurrent voice sessions (doubled from v1 for multi-clinic + VA rollout)
- 800 new sessions/minute sustained, 2,000/minute burst
- AI Search: 1,000 queries/second across 50,000+ documents
- Lab result processing: 100,000 results/month with p99 < 5 minutes to notification
- Referral processing: 5,000 referrals/month with AI matching < 500ms
- Blob storage: ~1 TB/month for recordings + lab attachments + referral documents
- Data volume: 200,000 session records/month (~80 GB Cosmos DB)
- Auto-scale from 4 to 50 container instances

---

## Data Protection

- All v1 security controls carried forward
- AI Search: Managed Identity with Search Index Data Contributor + Search Service Contributor roles
- FedRAMP Moderate: NIST 800-53 controls, US-region-only data residency, FIPS 140-2 encryption
- Lab data classified as PHI with restricted access logging
- Referral data: inter-facility sharing governed by RBAC + patient consent flag
- Voice recordings: immutable tier extended to 365 days for FedRAMP

---

## SLA

- All v1 latency targets maintained
- Lab result notification: p99 < 5 minutes from result entry to clinician/patient notification
- Referral matching: p95 < 500ms for AI provider scoring
- AI Search query: p95 < 200ms for hybrid semantic + keyword search
- Availability: 99.95% (upgraded from 99.9% for VA partnership)

---

## External Systems

- All v1 integrations carried forward (EHR, pharmacy, scheduling, telephony)
- Lab integration: Quest/LabCorp APIs for external lab order routing and result ingestion
- Referral network: regional HIE (Health Information Exchange) for provider discovery
- AI Search: Azure AI Search for RAG knowledge base indexing and retrieval
- FedRAMP: Azure Government region compatibility for VA workloads

---

## Verification

- All v1 acceptance criteria still pass (regression)
- Mandarin voice interactions produce accurate transcripts and correct intent routing
- Referral CRUD endpoints work with AI provider matching verification
- Lab order result entry triggers AI interpretation and critical value alerts
- Deep health endpoint validates all 7 backing services
- AI Search returns semantically relevant results for clinical queries
- Predictive analytics endpoints return valid ML-scored predictions
- FedRAMP control mappings documented and verifiable
- Load test: 2,000 concurrent voice sessions sustained for 10 minutes without errors

## Improvement Suggestions from v1

The following were identified by the orchestrator after the v1 scaffold run:

1. Add referral management for inter-facility coordination (5-day delay identified)
2. Integrate lab order tracking — patients frequently call for results
3. Add AI Search RAG to replace keyword-only knowledge base search
4. Upgrade predictive analytics from rules to ML-powered models
5. Add Mandarin language support (12% of caller base)
6. Achieve FedRAMP Moderate for VA partnership eligibility
7. Consider private endpoints for all data-plane services

## Configuration

- **App Type**: ai_app
- **Data Stores**: cosmos, redis, blob, sql, table, ai_search
- **Region**: eastus2
- **Environment**: dev
- **Auth**: managed-identity
- **Compliance**: HIPAA, SOC2, FedRAMP

## Version

- **Version**: 2
- **Based On**: 1
- **Changes**: Add AI Search RAG, Referral + LabOrder entities, Mandarin voice, predictive analytics, FedRAMP compliance, 6 AI agents


