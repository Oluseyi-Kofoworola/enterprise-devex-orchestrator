# demo-voice-agent

> An enterprise-grade AI-powered voice agent platform for Demo Health System's
> 14-clinic network. Orchestrates **12 domain entities** across 5 data stores
> (Cosmos DB, SQL, Redis, Blob, Table Storage) with GPT-4o Realtime voice,
> Semantic Kernel agents for clinical decision support, RAG-grounded knowledge
> base, and full HIPAA + SOC2 compliance. Handles real-time voice sessions,
> appointment scheduling, prescription management, clinical triage,
> staff workforce tracking, facility operations, and immutable audit logging
> with 7-year PHI retention.

## Problem Statement

Demo Health System clinical and administrative staff spend significant
time on manual phone workflows -- appointment scheduling, prescription refill
requests, post-discharge follow-ups, insurance eligibility checks, clinical
triage, and inter-facility referrals. Patients wait on hold an average of
8 minutes, and after-hours calls go to voicemail with next-business-day
callbacks. Front-desk staff handle ~1,200 calls/day across 14 clinics, leading
to burnout and a 22% annual turnover rate. HIPAA compliance requires every
patient interaction to be logged and access-controlled, but the current phone
system has no structured audit trail. Clinical triage errors result in 4.2%
of callers being directed to the wrong care level, causing $1.8M/year in
unnecessary ER visits. Prescription refill verification takes 6 minutes per
call due to manual pharmacy system lookups. Staff scheduling conflicts cause
$940K/year in overtime costs across the network. Facility equipment
maintenance is tracked in spreadsheets with no predictive capabilities,
resulting in 18% unplanned downtime. The cost of these operational
inefficiencies is estimated at $8.6M/year.

## Business Objectives

- Reduce average patient wait time from 8 minutes to under 30 seconds via AI voice agent with GPT-4o Realtime
- Deploy 4 specialized Semantic Kernel agents: TriageAgent, SchedulingAgent, PharmacyAgent, AnalyticsAgent
- Automate 75% of routine calls (scheduling, refills, triage, FAQs) without human handoff
- Achieve 97% clinical triage accuracy using AI classification with RAG-grounded clinical protocols
- Reduce prescription verification time from 6 minutes to under 30 seconds via AI pharmacy lookup
- Eliminate staff scheduling conflicts through AI-optimized shift planning across 14 facilities
- Predict 85% of equipment failures 48 hours in advance using AI maintenance scoring
- Maintain full PHI audit trail with 7-year HIPAA retention across all 12 entity types
- Achieve HIPAA audit readiness and SOC2 Type II certification by end of quarter
- KPI: Patient satisfaction (CSAT) score above 4.5/5.0 within 6 months
- KPI: Average handle time for automated calls under 60 seconds
- KPI: Triage accuracy > 97%, refill automation > 90%, scheduling conflict rate < 0.5%

## User Roles

1. **Patient** — Calls to schedule appointments, request refills, ask billing questions, report symptoms for AI triage; low technical proficiency, expects natural conversation
2. **Front-Desk Coordinator** — Monitors live agent dashboard, handles escalations, manages patient check-in; intermediate proficiency
3. **Clinical Staff (Nurse/PA)** — Receives AI-triaged calls with clinical context summary, reviews AI-recommended care levels; intermediate proficiency
4. **Attending Physician** — Reviews AI triage recommendations, approves prescription changes, oversees clinical protocols; high clinical proficiency
5. **Pharmacist** — Reviews AI-flagged drug interactions, verifies refill requests, manages formulary compliance; intermediate proficiency
6. **Workforce Manager** — Manages staff schedules across 14 facilities, reviews AI shift optimization, tracks overtime and coverage metrics
7. **Facility Operations Manager** — Monitors equipment health scores, reviews AI maintenance predictions, manages work orders; intermediate proficiency
8. **IT Administrator** — Manages voice agent configuration, monitors uptime and AI performance metrics; high technical proficiency
9. **Compliance Officer** — Reviews PHI audit logs, monitors AI interaction logs, generates compliance reports weekly; low technical proficiency
10. **Quality Assurance Analyst** — Reviews call recordings and transcripts, evaluates AI triage accuracy, measures patient satisfaction; intermediate proficiency

## Functional Requirements

### AI Agent Orchestration (Semantic Kernel)
- Deploy 4 specialized Semantic Kernel agents with tool-calling: TriageAgent (symptom classification, care level recommendation), SchedulingAgent (appointment optimization, conflict resolution), PharmacyAgent (drug interaction checking, refill automation), AnalyticsAgent (natural-language queries over operational data)
- Agent-to-agent delegation: TriageAgent invokes SchedulingAgent for urgent appointment booking
- Conversation history maintained per agent session with sliding window of 15 messages

### RAG Pipeline (Knowledge Base)
- Index 50,000+ clinical protocols, drug databases, insurance policies, and FAQ documents
- Hybrid search: semantic vector search (text-embedding-ada-002) + keyword BM25
- Top-k=5 retrieval with relevance threshold > 0.75
- Used by TriageAgent for clinical protocol grounding and PharmacyAgent for drug interaction data

### Voice & Session Management
- Real-time voice-to-voice conversations using OpenAI GPT-4o Realtime API (WebSocket-based)
- Automatic language detection (English/Spanish) in first 3 seconds of conversation
- Call recording persistence in Azure Blob with configurable retention (default 180 days, HIPAA immutable tier)

### Entity: VoiceSession
- Fields: session_id (str), patient_id (str), agent_type (str — triage/scheduling/pharmacy/general/escalation), status (str — active/paused/completed/escalated/dropped/failed), language (str — en/es), channel (str — phone/web/mobile), start_time (str), end_time (str), duration_seconds (int), transcript_text (str), ai_intent_detected (str), ai_confidence (float), ai_sentiment_score (float), escalation_reason (str), escalated_to_staff_id (str), caller_phone (str), recording_blob_url (str), token_count_prompt (int), token_count_completion (int), content_safety_result (str), satisfaction_rating (int), facility_id (str), notes (str)
- Actions: create, end, pause, resume, escalate, rate
- POST /api/v1/voice_sessions — Create with AI agent routing based on initial intent detection
- POST /api/v1/voice_sessions/{session_id}/escalate — Escalate to human with full context
- POST /api/v1/voice_sessions/{session_id}/end — End session, persist recording, log metrics
- GET /api/v1/voice_sessions/{session_id}/transcript — Get full transcript with AI annotations
- GET /api/v1/patients/{patient_id}/voice_sessions/{session_id}/recording — Playback recording (RBAC-restricted)

### Entity: Patient
- Fields: first_name (str), last_name (str), date_of_birth (str), gender (str — male/female/other), mrn (str), phone (str), email (str), address (str), city (str), state (str), zip_code (str), insurance_id (str), insurance_provider (str), primary_provider_id (str), preferred_language (str — en/es), allergies (list[str]), active_medications (list[str]), problem_list (list[str]), emergency_contact_name (str), emergency_contact_phone (str), last_visit_date (str), portal_active (boolean), risk_score (float)
- POST /api/v1/patients — Register new patient with demographics
- POST /api/v1/patients/{patient_id}/verify — Verify identity for voice interactions
- GET /api/v1/patients/{patient_id}/summary — AI-generated clinical summary
- POST /api/v1/patients/{patient_id}/flag_allergy — Add allergy with AI drug interaction check

### Entity: Appointment
- Fields: patient_id (str), provider_id (str), facility_id (str), appointment_type (str — office_visit/telehealth/procedure/follow_up/urgent/annual_physical), status (str — scheduled/confirmed/checked_in/in_progress/completed/no_show/cancelled/rescheduled), scheduled_date (str), scheduled_time (str), duration_minutes (integer), room_number (str), reason_for_visit (str), chief_complaint (str), insurance_verified (boolean), copay_amount (float), copay_collected (boolean), ai_no_show_risk (float), ai_suggested_slot (str), reminder_sent (boolean), voice_session_id (str), pre_auth_required (boolean), pre_auth_number (str), wait_time_minutes (integer), notes (str)
- POST /api/v1/appointments — Schedule with AI conflict detection and no-show risk scoring
- POST /api/v1/appointments/{appointment_id}/confirm — Patient confirmation via voice or portal
- POST /api/v1/appointments/{appointment_id}/check_in — Check-in with insurance verification
- POST /api/v1/appointments/{appointment_id}/cancel — Cancel with AI reschedule suggestion
- POST /api/v1/appointments/{appointment_id}/reschedule — AI-optimized reschedule
- GET /api/v1/providers/{provider_id}/appointments/{date}/availability — Provider slot availability by date

### Entity: Prescription
- Fields: patient_id (str), provider_id (str), drug_name (str), drug_ndc (str), dosage (str), frequency (str — once_daily/twice_daily/three_times_daily/as_needed/weekly), route (str — oral/topical/injection/inhalation), quantity (integer), refills_remaining (integer), refills_total (integer), status (str — active/expired/discontinued/on_hold/cancelled), start_date (str), end_date (str), pharmacy_name (str), dispense_as_written (boolean), ai_interaction_alerts (list[str]), ai_formulary_status (str), ai_generic_alternative (str), prior_auth_required (boolean), prior_auth_status (str), controlled_substance_schedule (str), last_fill_date (str), total_cost (decimal)
- POST /api/v1/prescriptions — Create with AI drug interaction check against active medications + allergies
- POST /api/v1/prescriptions/{prescription_id}/refill — Process refill via voice or portal
- POST /api/v1/prescriptions/{prescription_id}/discontinue — Discontinue with clinical reason
- POST /api/v1/patients/{patient_id}/prescriptions/{prescription_id}/interactions — AI interaction analysis against all active meds

### Entity: TriageRecord
- Fields: patient_id (str), voice_session_id (str), reported_symptoms (list[str]), symptom_duration (str), symptom_severity (str — mild/moderate/severe/critical), ai_assessed_urgency (str — routine/urgent/emergent/life_threatening), ai_recommended_care_level (str — self_care/nurse_line/office_visit/urgent_care/emergency), ai_confidence (float), ai_protocol_references (list[str]), vital_signs_reported (str), medical_history_flags (list[str]), triage_outcome (str — scheduled/referred/escalated/self_care_advised/911_dispatched), provider_override (boolean), provider_override_reason (str), override_provider_id (str), follow_up_required (boolean), follow_up_date (str), created_at (str), facility_id (str)
- POST /api/v1/triage_records — AI triage from voice session symptoms with protocol-grounded reasoning
- POST /api/v1/triage_records/{triage_id}/override — Provider overrides AI recommendation
- POST /api/v1/triage_records/{triage_id}/dispatch_911 — Emergency dispatch for life-threatening triage
- GET /api/v1/patients/{patient_id}/triage_records/{triage_id}/protocol — AI protocol references used
- POST /api/v1/triage_records/{triage_id}/follow_up — Schedule follow-up from triage outcome

### Entity: Provider
- Fields: first_name (str), last_name (str), npi (str), specialty (str — family_medicine/internal_medicine/pediatrics/cardiology/orthopedics/neurology/dermatology/psychiatry/emergency), credential (str — MD/DO/NP/PA/RN), status (str — active/inactive/on_leave/credentialing), facility_ids (list[str]), department (str), license_number (str), license_state (str), license_expiry (str), board_certified (boolean), accepting_patients (boolean), panel_size (integer), average_rating (float), years_experience (integer), languages (list[str]), telehealth_enabled (boolean), schedule_template (str), email (str), phone (str)
- POST /api/v1/providers/{provider_id}/update_availability — Update schedule template
- POST /api/v1/providers/{provider_id}/refer — Create inter-provider referral
- GET /api/v1/providers/{provider_id}/quality_scores — AI-generated quality metrics from patient data

### Entity: Facility
- Fields: name (str), facility_code (str), facility_type (str — clinic/hospital/urgent_care/telehealth_hub/pharmacy), status (str — operational/limited/closed/maintenance), address (str), city (str), state (str), zip_code (str), phone (str), latitude (float), longitude (float), operating_hours (str), bed_count (integer), staff_count (integer), active_patient_count (integer), equipment_count (integer), ai_utilization_score (float), ai_capacity_forecast (str), last_inspection_date (str), accreditation_status (str), zone_id (str)
- POST /api/v1/facilities/{facility_id}/set_status — Update operational status
- GET /api/v1/facilities/{facility_id}/capacity — Real-time capacity with AI forecast
- GET /api/v1/facilities/{facility_id}/equipment_health — Aggregated equipment health scores

### Entity: StaffMember
- Fields: first_name (str), last_name (str), employee_id (str), role (str — nurse/coordinator/technician/administrator/pharmacist/qa_analyst), status (str — active/on_leave/terminated/training), facility_id (str), department (str), hire_date (str), shift_pattern (str — day/night/rotating/flex), weekly_hours_target (integer), weekly_hours_actual (float), overtime_hours_ytd (float), certification_expiry (str), performance_rating (float), ai_schedule_preference (str), ai_burnout_risk_score (float), phone (str), email (str), supervisor_id (str), last_shift_date (str)
- POST /api/v1/staff_members/{staff_id}/assign_shift — Assign shift with AI conflict detection
- POST /api/v1/staff_members/{staff_id}/swap_shift — AI-optimized shift swap matching
- GET /api/v1/facilities/{facility_id}/staff_members/{staff_id}/schedule — Staff schedule at facility

### Entity: Equipment
- Fields: name (str), equipment_type (str — infusion_pump/ventilator/monitor/defibrillator/x_ray/ultrasound/ecg/autoclave), manufacturer (str), model_number (str), serial_number (str), status (str — available/in_use/maintenance/calibration/retired/recalled), facility_id (str), department (str), location_room (str), purchase_date (str), warranty_expiry (str), last_calibration_date (str), next_calibration_due (str), last_pm_date (str), next_pm_due (str), total_usage_hours (integer), firmware_version (str), risk_category (str — low/medium/high/critical), ai_failure_prediction (str), ai_replacement_recommendation (str), maintenance_cost_ytd (decimal), assigned_patient_id (str)
- POST /api/v1/equipment/{equipment_id}/calibrate — Record calibration with results
- POST /api/v1/equipment/{equipment_id}/retire — Retire with AI replacement recommendation
- POST /api/v1/equipment/{equipment_id}/maintenance — Create maintenance work order
- GET /api/v1/facilities/{facility_id}/equipment/{equipment_id}/history — Equipment service history by facility

### Entity: InsuranceClaim
- Fields: claim_number (str), patient_id (str), provider_id (str), facility_id (str), service_date (str), submission_date (str), claim_type (str — professional/institutional), status (str — draft/submitted/pending/adjudicated/paid/denied/appealed), cpt_codes (list[str]), icd10_codes (list[str]), total_charges (float), allowed_amount (float), paid_amount (float), patient_responsibility (float), denial_reason (str), denial_code (str), payer_name (str), authorization_number (str), ai_denial_risk_score (float), ai_appeal_recommendation (str), remittance_date (str), adjustment_codes (list[str]), ar_aging_days (integer)
- POST /api/v1/insurance_claims — Submit claim with CPT/ICD-10 codes
- POST /api/v1/insurance_claims/{claim_id}/adjudicate — AI-powered adjudication risk simulation
- POST /api/v1/insurance_claims/{claim_id}/appeal — Generate AI appeal letter with policy citations
- GET /api/v1/patients/{patient_id}/insurance_claims/{claim_id}/explanation — AI explanation of benefits

### Entity: KnowledgeArticle
- Fields: title (str), category (str — clinical_protocol/drug_reference/insurance_policy/faq/procedure_guide/safety_bulletin), status (str — draft/published/archived/under_review), content_text (str), author_id (str), facility_scope (str — all/specific), applicable_facility_ids (list[str]), tags (list[str]), version (integer), effective_date (str), review_date (str), ai_embedding_status (str — pending/indexed/failed), ai_relevance_score (float), view_count (integer), helpful_votes (integer), last_updated (str)
- POST /api/v1/knowledge_articles — Create and index in AI Search
- POST /api/v1/knowledge_articles/{article_id}/publish — Publish and re-index embeddings
- POST /api/v1/knowledge_articles/{article_id}/archive — Archive with removal from search index
- GET /api/v1/knowledge_articles/search — Hybrid semantic + keyword search

### Entity: Notification
- Fields: recipient_id (str), recipient_type (str — patient/staff/provider), channel (str — sms/email/push/voice_callback/in_app), notification_type (str — appointment_reminder/refill_ready/triage_follow_up/schedule_change/equipment_alert/compliance_alert), status (str — queued/sent/delivered/failed/read), subject (str), body (str), priority (str — low/medium/high/urgent), scheduled_send_time (str), actual_send_time (str), delivery_confirmation (str), related_entity_type (str), related_entity_id (str), facility_id (str), ai_generated (boolean), retry_count (integer)
- POST /api/v1/notifications — Queue notification with AI content generation
- POST /api/v1/notifications/{notification_id}/send — Send queued notification
- POST /api/v1/notifications/{notification_id}/retry — Retry failed delivery

### Entity: AuditLog
- Fields: event_type (str — phi_access/phi_export/login/logout/role_change/ai_interaction/voice_session/prescription_change/triage_decision/config_change), actor_id (str), actor_role (str), patient_id (str), resource_type (str), resource_id (str), action (str — view/create/update/delete/export/escalate), ip_address (str), user_agent (str), facility_id (str), department (str), access_reason (str), break_glass (boolean), phi_categories_accessed (list[str]), ai_anomaly_score (float), ai_risk_level (str — normal/elevated/high/critical), flagged_for_review (boolean), review_status (str — pending/reviewed/escalated/cleared), retention_expiry (str), correlation_id (str), session_id (str), geo_location (str), timestamp (str)
- (Read-only entity — system-generated immutable audit trail)
- GET /api/v1/audit_logs — Query with filters by event_type, actor, patient, date range
- GET /api/v1/audit_logs/anomalies — AI anomaly detection over access patterns
- GET /api/v1/audit_logs/report — AI-generated compliance report for HIPAA review

#### Cross-Domain AI Correlation
- AI correlates voice session intents with triage outcomes, appointment completions, and prescription fills
- Natural-language queries via AnalyticsAgent span all 12 entity types simultaneously
- AI generates unified operational reports aggregating clinical, financial, and workforce data

---

## Scalability & Performance

- 1,000 concurrent voice sessions during peak hours (8am-6pm across 14 clinics)
- 400 new sessions/minute sustained, 1,000/minute burst (Monday mornings)
- GPT-4o inference: 500 concurrent AI sessions with p95 < 2 seconds
- AI Search: 500 queries/second across 50,000+ clinical knowledge articles
- Token budget: 1M tokens/hour across all 4 AI agents
- Initial data volume: 100,000 session records/month (~40 GB Cosmos DB)
- 50TB+ blob storage for call recordings (avg 3 min/call, compressed audio)
- Redis 20GB for session cache, real-time alerts, and AI response caching
- SQL database for relational scheduling, insurance claims, and staff workforce data
- Table Storage for high-volume audit log archival (7-year HIPAA retention)
- Growth: 30% year-over-year as clinics onboard and patient adoption increases
- Auto-scale from 4 to 30 container instances based on active WebSocket connections
- Availability SLA: 99.9% uptime during business hours, 99.5% after-hours

---

## Data Protection

- Authentication: Azure AD (Entra ID) via managed identity for service-to-service, OAuth2 for staff dashboard
- Authorization: RBAC with 10 roles matching user personas enforced at API layer
- Data classification: PHI (Protected Health Information) by default, de-identified for analytics
- Encryption: TLS 1.3 in transit (including WebSocket), AES-256 at rest (platform-managed keys)
- Network: Private endpoints for Cosmos DB, SQL, Redis, and Blob — no public internet access to data stores
- Compliance frameworks: HIPAA (BAA required with Azure), SOC2 Type II
- Secret management: Azure Key Vault with RBAC access policy, soft delete, purge protection
- No secrets in code, config, or CI/CD — all via managed identity or Key Vault references
- PHI access logging: every read/write of patient data logged with user identity and justification
- Break-glass access logging with mandatory review within 24 hours
- Voice data retention: configurable retention period (default 180 days) with automated purge
- Audit log retention: 7-year immutable storage for HIPAA compliance
- Azure OpenAI via Managed Identity — zero API keys

---

## SLA

- Voice latency: p50 < 300ms, p95 < 600ms, p99 < 1s (end-to-end voice round-trip)
- AI inference latency: p50 < 500ms, p95 < 2s (clinical decision support)
- API response latency: p50 < 100ms, p95 < 300ms, p99 < 1s (REST endpoints)
- Session creation latency: p95 < 2s (including WebSocket handshake)
- Triage response: p95 < 3s from symptom input to care-level recommendation
- RTO: 2 hours, RPO: 30 minutes (geo-redundant Cosmos DB)
- Cold start time: < 5 seconds for container instances

---

## External Systems

- Upstream: Azure AD for authentication, hospital EHR system (HL7 FHIR R4) for patient demographics and clinical data
- Upstream: OpenAI GPT-4o Realtime API for voice-to-voice inference (WebSocket)
- Downstream: Pharmacy system API for refill submissions and drug database lookups
- Downstream: Scheduling system for appointment CRUD and provider availability
- Third-party: Twilio or Azure Communication Services for telephony/SIP trunk integration
- Third-party: Surescripts for medication history and eligibility verification
- Event-driven: Escalation and triage events trigger notification via Event Grid
- Monitoring: Application Insights for telemetry, Log Analytics for HIPAA audit queries (KQL)

---

## Verification

- All 12 entity CRUD endpoints return correct HTTP status codes and JSON responses
- AI triage accuracy > 97% against gold-standard clinical test dataset
- AI drug interaction detection recall > 99% against reference database
- RBAC enforcement: clinician cannot delete sessions, auditor cannot modify transcripts — verified by integration tests
- Audit log captures 100% of voice interactions and PHI access with correct metadata
- Multi-parameter endpoints (`/patients/{patient_id}/prescriptions/{prescription_id}/interactions`) resolve correctly
- Voice agent responds naturally within p95 latency targets
- Escalation hands off full transcript, triage summary, and AI recommendations to human coordinator
- Infrastructure deploys successfully via `az deployment group create` with zero manual steps
- CI/CD pipeline passes: lint, unit tests, integration tests, security scan (CodeQL), Bicep validation
- Governance validation passes with no FAIL status
- HIPAA-required controls (access control, audit logging, encryption at rest, PHI access logs, 7-year retention) are demonstrably present

## Configuration

- **App Type**: ai_app
- **Data Stores**: cosmos, redis, blob, sql, table
- **Region**: eastus2
- **Environment**: dev
- **Auth**: managed-identity
- **Compliance**: HIPAA, SOC2

## Version

- **Version**: 1
- **Based On**: none
- **Changes**: Initial scaffold — enterprise AI voice agent platform with 12 entities, 4 AI agents, RAG, and full HIPAA compliance


