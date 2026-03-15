# Metro Command — AI-Powered Metropolitan Operations Intelligence Platform

Build an enterprise-grade AI-powered metropolitan operations intelligence platform that orchestrates **14 domain entities** across every supported data store (Cosmos DB, SQL, Blob Storage, Redis, AI Search, Table Storage), uses Azure OpenAI for multi-agent AI workflows, RAG-grounded citizen chatbot, content safety filtering, and predictive analytics. The platform manages the full lifecycle of emergency incidents, infrastructure assets, environmental sensors, citizen service requests, transit routes, utility grids, city zones, fleet vehicles, work orders, AI audit logs — plus **users with RBAC profiles, a citizen-facing chatbot with conversation history, an internal AI assistant for operators, and a notification hub** — each with unique field types, status workflows, and action endpoints. A GPT-4o command center copilot enables natural-language queries over all 14 entities, and 8 Semantic Kernel agents autonomously triage incidents, predict failures, detect environmental violations, route citizen requests, manage user access, handle chatbot conversations, provide operator assistance, and send intelligent notifications. The system must handle 250,000+ concurrent IoT sensor streams, 500+ operator sessions, 50,000 citizen chatbot interactions/day, and 2,000 internal AI assistant queries/hour with FedRAMP, SOC2, and HIPAA compliance, WAF-protected public endpoints, and full AI audit logging. File upload processing supports incident photos (GPT-4o Vision), audio recordings (Whisper transcription), and scanned document extraction.

---

## Configuration

- **App Type**: ai_app
- **Data Stores**: cosmos, blob, sql, redis, ai_search, table
- **Region**: eastus2
- **Environment**: dev
- **Auth**: entra-id
- **Compliance**: SOC2, HIPAA, FedRAMP

---

## Problem Statement

Metropolitan operations across 2.1 million residents and 85,000 city employees are fragmented across 18 disconnected legacy systems. Emergency response times average 12 minutes due to manual dispatch — an AI agent could triage and dispatch in under 30 seconds. Utility outages go undetected for hours because 250,000+ sensor alerts are siloed across 12 vendor protocols — an LLM-powered anomaly correlation engine could detect cascading failures in real time. Citizens file 40% duplicate service requests across 3 separate portals with no unified chatbot experience — a RAG-grounded AI chatbot with conversation memory could resolve 70% instantly. Environmental compliance violations have increased 23% YoY with $4.2M in EPA fines. Transit delays cost $180M annually. Fleet maintenance consumes $22M/year with 30% reactive emergency repairs. The city has no centralized user management system — operators, supervisors, and citizens all use different credentials with no SSO. There is no AI assistant for internal staff — operators manually search 6 dashboards and 4 knowledge bases to answer routine questions. The notification system relies on manual email chains with no intelligent routing, priority escalation, or delivery tracking. The city loses $8.6M annually from uncoordinated operations, $2.1M from duplicate citizen interactions, and $1.4M from notification failures during emergencies.

---

## Business Goals

- Deploy a multi-agent AI system with **8 specialized Semantic Kernel agents** orchestrated via tool-calling with agent-to-agent delegation: DispatchAgent, MaintenanceAgent, EnvironmentAgent, CitizenChatbotAgent, AnalyticsAgent, FleetAgent, UserManagementAgent, NotificationAgent
- Reduce emergency dispatch triage from 12 minutes to under 30 seconds using GPT-4o incident classification with Vision for photo evidence analysis
- Implement RAG-grounded **citizen chatbot** resolving 70% of inquiries from 500,000+ knowledge articles via hybrid vector + BM25 search, with persistent conversation history and multi-turn context
- Deploy **internal AI assistant** for 500+ city operators handling 2,000 queries/hour for real-time cross-domain intelligence, report generation, and decision support
- Build centralized **user management** with role-based profiles, department assignments, session tracking, preference management, and AI-personalized dashboards
- Implement **intelligent notification hub** with multi-channel delivery (push, SMS, email, in-app), priority-based routing, delivery tracking, and AI-generated content personalization
- Process 50,000 citizen chatbot interactions/day with <2s response latency, 70% resolution rate, and seamless human handoff for complex cases
- Achieve 99.99% uptime SLA for the AI command center serving 500+ concurrent operators with natural-language cross-domain queries
- Save $5M annually through AI-predicted maintenance using embeddings similarity search against 100,000+ historical failure signatures
- Reduce environmental violations by 80% through autonomous LLM-powered threshold monitoring with auto-generated EPA reports
- Track 47,000 infrastructure assets with AI-generated health scores, GPS coordinates, and full maintenance history
- Manage a fleet of 1,200 city vehicles with real-time GPS tracking, fuel analytics, and AI-predicted maintenance scheduling
- Maintain full AI audit trail with every prompt, completion, token count, latency, content safety result, user identity, and chatbot session logged for 7-year retention
- Achieve FedRAMP Moderate, SOC2 Type II, and HIPAA compliance across all AI data pipelines

---

## Target Users

1. **City Operations Commander** — Senior C-suite using the AI assistant to query cross-domain city status in natural language. Interacts through the internal AI assistant grounded by RAG over all operational data. Needs unified dashboard showing all 14 entity types with KPI tiles.

2. **Emergency Dispatch Coordinator** — First responder staff receiving AI-generated triage recommendations. The DispatchAgent auto-classifies incidents from text+photo, recommends nearest units, generates GPS routes. Human approves or overrides.

3. **Utility Grid Engineer** — Engineers receiving AI failure predictions. The MaintenanceAgent analyzes vibration/temperature/load via embeddings similarity to historical failures and generates preventive work orders.

4. **Environmental Compliance Officer** — Regulatory staff using the EnvironmentAgent for continuous threshold monitoring, LLM-classified violation severity, and auto-generated compliance reports with RAG-cited EPA regulations.

5. **Citizen Services Agent** — Call center staff augmented by the CitizenChatbotAgent. Citizens interact via the public chatbot, AI searches knowledge base, creates service requests, and detects duplicates. Agent sees full chatbot conversation history.

6. **Citizen (Public User)** — Residents using the public-facing chatbot to report issues, check request status, ask questions about city services, and receive AI-generated answers with knowledge base citations. No login required for basic queries; authenticated for request tracking.

7. **Transit Operations Manager** — Transit managers querying AI for route optimization, ridership predictions, delay forecasting, and incident impact analysis via natural-language queries.

8. **Fleet Manager** — Fleet supervisors tracking 1,200 vehicles with GPS, managing fuel budgets, scheduling maintenance, and receiving AI-predicted failure alerts.

9. **Zone Administrator** — District managers overseeing specific city zones with aggregated dashboards of all entities within their geographic boundary.

10. **City Data Analyst** — Analysts using AI assistant for natural-language analytics ("What was the average response time for fire incidents in Q3?") translated to KQL by AnalyticsAgent.

11. **AI Safety Reviewer** — Security staff monitoring content safety dashboards, reviewing flagged AI interactions from both chatbot and internal assistant, tuning content filtering policies, and auditing AI decision logs.

12. **Maintenance Planner** — Planners reviewing AI-generated work orders, scheduling maintenance windows, and tracking asset lifecycle costs.

13. **System Administrator** — IT staff managing user accounts, role assignments, department configurations, API key rotation, and platform health monitoring via the UserManagementAgent.

14. **Notification Manager** — Staff configuring notification rules, monitoring delivery rates, managing channel preferences, and reviewing AI-generated notification content.

---

## Functional Requirements

### AI Agent Orchestration (Semantic Kernel)
- Deploy **8 specialized Semantic Kernel agents** with tool-calling: DispatchAgent, MaintenanceAgent, EnvironmentAgent, CitizenChatbotAgent, AnalyticsAgent, FleetAgent, UserManagementAgent, NotificationAgent
- Each agent has domain-specific kernel_functions deployed as tools
- Agent-to-agent delegation: DispatchAgent → FleetAgent for vehicle availability, CitizenChatbotAgent → NotificationAgent for status updates, UserManagementAgent → AnalyticsAgent for usage metrics
- Agent orchestration via function_choice_behavior="auto" for autonomous multi-step reasoning
- Conversation history maintained per agent session with sliding window of 20 messages

### RAG Pipeline (Azure AI Search + Embeddings)
- Index 500,000+ city documents in AI Search with hybrid semantic + BM25 search
- Document chunking: 512-token windows with 128-token overlap
- Top-k=5 retrieval with relevance threshold > 0.75

### Citizen Chatbot (Public-Facing)
- POST /api/v1/chatbot/conversations — Create new chatbot conversation with optional citizen auth
- POST /api/v1/chatbot/conversations/{id}/messages — Send message, receive AI response with RAG citations
- GET /api/v1/chatbot/conversations/{id}/history — Full conversation history with timestamps
- POST /api/v1/chatbot/conversations/{id}/handoff — Escalate to human agent with full context transfer
- POST /api/v1/chatbot/conversations/{id}/feedback — Rate chatbot response quality
- Intent detection routes to: report_issue, check_status, ask_question, schedule_appointment, file_complaint
- Multi-turn context: chatbot remembers previous messages in session
- Suggested follow-up questions generated by AI after each response

### Internal AI Assistant (Operator-Facing)
- POST /api/v1/assistant/query — Natural-language query across all 14 entities with streaming SSE
- POST /api/v1/assistant/report — AI-generated report (PDF/markdown) for any domain
- POST /api/v1/assistant/analyze — Deep analysis with charts, trends, and recommendations
- GET /api/v1/assistant/suggestions — Proactive AI suggestions based on current system state
- Context-aware: assistant adapts responses based on user role and department
- Cross-domain correlation: "Show all critical incidents near Zone 7 with affected assets and transit disruptions"

### Content Safety & Responsible AI
- Content filtering on all 4 categories at medium threshold for both chatbot and assistant
- Custom prompt injection detection on every inbound request
- PII scrubbing on chatbot outputs (citizens may share sensitive info)
- Per-role token rate limiting (100 tokens/sec for operators, 50 tokens/sec for citizens)
- Full audit logging of every AI interaction from both chatbot and assistant

### Entity: Incident
- Fields: title (str), description (str), category (str — fire/medical/traffic/utility/environmental/security/cyber), severity (str — critical/high/medium/low), status (str — reported/triaged/dispatched/in_progress/resolved/closed), latitude (float), longitude (float), zone_id (str), reporter_id (str), affected_population (int), estimated_damage (float), ai_confidence (float), ai_triage_notes (str), photo_url (str), audio_transcript (str), assigned_units (list[str]), resolution_notes (str), response_time_minutes (float), chatbot_originated (bool)
- POST /api/v1/incidents — Create with AI auto-classification
- POST /api/v1/incidents/{id}/triage — AI-powered triage
- POST /api/v1/incidents/{id}/dispatch — AI-recommended dispatch
- POST /api/v1/incidents/{id}/escalate — Escalate severity
- POST /api/v1/incidents/{id}/resolve — Close with metrics
- POST /api/v1/incidents/{id}/correlate — AI cross-domain correlation

### Entity: Asset
- Fields: name (str), asset_type (str — bridge/road/pipe/transformer/pump/signal/building/park/server/network), status (str — operational/degraded/maintenance/offline/decommissioned), location_address (str), latitude (float), longitude (float), zone_id (str), install_date (str), expected_lifespan_years (int), manufacturer (str), model_number (str), last_inspection_date (str), health_score (float), replacement_cost (float), maintenance_budget (float), sensor_ids (list[str]), ai_failure_prediction (str), ai_health_trend (str), assigned_team_id (str)
- POST /api/v1/assets/{id}/predict — AI failure prediction
- POST /api/v1/assets/{id}/inspect — AI-generated health assessment
- POST /api/v1/assets/{id}/schedule_maintenance — AI maintenance scheduling
- POST /api/v1/assets/{id}/decommission — AI replacement recommendation

### Entity: Sensor
- Fields: name (str), sensor_type (str — temperature/air_quality/water_flow/power_load/traffic/acoustic/vibration/pressure/humidity/radiation/co2/noise), status (str — online/offline/calibrating/error/maintenance), latitude (float), longitude (float), zone_id (str), asset_id (str), vendor (str), protocol (str), last_reading_value (float), last_reading_unit (str), last_reading_timestamp (str), threshold_min (float), threshold_max (float), alert_enabled (bool), battery_level (float), firmware_version (str), calibration_date (str)
- POST /api/v1/sensors/{id}/calibrate — Calibration cycle
- POST /api/v1/sensors/{id}/acknowledge_alert — Acknowledge threshold alert
- POST /api/v1/sensors/{id}/disable — Temporarily disable

### Entity: ServiceRequest
- Fields: title (str), description (str), category (str — pothole/streetlight/noise/graffiti/water/sewer/parks/trash/permits/flooding/illegal_dumping), priority (str — urgent/high/medium/low), status (str — submitted/acknowledged/in_progress/awaiting_parts/scheduled/completed/rejected), citizen_id (str), citizen_name (str), citizen_email (str), latitude (float), longitude (float), zone_id (str), assigned_team (str), estimated_completion_date (str), ai_duplicate_score (float), ai_category_confidence (float), ai_suggested_resolution (str), photo_url (str), satisfaction_rating (int), chatbot_session_id (str)
- POST /api/v1/service_requests/{id}/acknowledge — Staff acknowledges
- POST /api/v1/service_requests/{id}/assign — Assign team
- POST /api/v1/service_requests/{id}/complete — Complete with resolution
- POST /api/v1/service_requests/{id}/reject — Reject with AI explanation
- POST /api/v1/service_requests/{id}/check_duplicate — AI duplicate detection

### Entity: TransitRoute
- Fields: name (str), route_number (str), route_type (str — bus/rail/ferry/shuttle/express), status (str — active/delayed/suspended/rerouted/out_of_service), start_location (str), end_location (str), total_stops (int), daily_ridership (int), average_delay_minutes (float), on_time_percentage (float), fare_revenue_daily (float), operating_cost_daily (float), vehicle_count (int), zone_ids (list[str]), ai_demand_forecast (str), ai_optimization_notes (str), last_disruption_reason (str)
- POST /api/v1/transit_routes/{id}/optimize — AI route optimization
- POST /api/v1/transit_routes/{id}/reroute — Alternative route
- POST /api/v1/transit_routes/{id}/suspend — Suspend with AI impact
- POST /api/v1/transit_routes/{id}/restore — Restore operations

### Entity: Vehicle
- Fields: name (str), vehicle_type (str — sedan/suv/truck/van/bus/ambulance/fire_engine/utility/drone), status (str — available/deployed/maintenance/refueling/out_of_service), license_plate (str), vin_number (str), current_latitude (float), current_longitude (float), assigned_department (str), driver_id (str), fuel_level_pct (float), odometer_miles (int), last_maintenance_date (str), next_maintenance_due (str), maintenance_cost_ytd (float), ai_maintenance_prediction (str), gps_speed_mph (float), engine_health_score (float)
- POST /api/v1/vehicles/{id}/deploy — Deploy vehicle
- POST /api/v1/vehicles/{id}/recall — Recall to depot
- POST /api/v1/vehicles/{id}/refuel — Log refueling
- POST /api/v1/vehicles/{id}/schedule_maintenance — AI maintenance

### Entity: Zone
- Fields: name (str), zone_code (str), zone_type (str — residential/commercial/industrial/mixed/park/transit_hub/government/hospital_district), status (str — normal/alert/emergency/evacuation/construction), population (int), area_sq_miles (float), council_district (int), emergency_contacts (list[str]), active_incident_count (int), active_sensor_count (int), active_asset_count (int), air_quality_index (float), noise_level_db (float), power_load_pct (float), ai_risk_score (float), ai_trend_summary (str), assigned_admin_id (str)
- POST /api/v1/zones/{id}/alert — Raise alert with AI risk assessment
- POST /api/v1/zones/{id}/evacuate — Evacuation protocol
- POST /api/v1/zones/{id}/clear — Clear alert

### Entity: WorkOrder
- Fields: title (str), description (str), work_type (str — preventive/corrective/emergency/inspection/replacement/upgrade), priority (str — critical/high/medium/low), status (str — created/approved/scheduled/in_progress/on_hold/completed/cancelled), asset_id (str), assigned_team (str), requester_id (str), scheduled_date (str), estimated_hours (float), actual_hours (float), parts_cost (float), labor_cost (float), total_cost (float), ai_generated (bool), ai_justification (str), completion_notes (str), quality_rating (int)
- POST /api/v1/work_orders/{id}/approve — Approve
- POST /api/v1/work_orders/{id}/schedule — Set window
- POST /api/v1/work_orders/{id}/start — Begin work
- POST /api/v1/work_orders/{id}/complete — Complete with costs
- POST /api/v1/work_orders/{id}/cancel — Cancel with AI impact

### Entity: User (Identity & Access Management)
- Fields: username (str), email (str), display_name (str), role (str — commander/dispatcher/engineer/compliance_officer/citizen_agent/transit_manager/fleet_manager/zone_admin/analyst/planner/ai_reviewer/sys_admin/notification_manager/citizen), department (str — emergency/utilities/environment/citizen_services/transit/fleet/planning/it/executive/public), status (str — active/suspended/locked/pending_approval/deactivated), phone (str), employee_id (str), last_login (str), login_count (int), mfa_enabled (bool), preferred_language (str), notification_preferences (str), assigned_zones (list[str]), ai_usage_tokens_today (int), ai_usage_tokens_month (int), profile_photo_url (str), created_by (str)
- POST /api/v1/users/{id}/activate — Activate pending user
- POST /api/v1/users/{id}/suspend — Suspend with reason
- POST /api/v1/users/{id}/unlock — Unlock locked account
- POST /api/v1/users/{id}/reset_mfa — Reset MFA enrollment
- POST /api/v1/users/{id}/update_preferences — Update notification and UI preferences
- POST /api/v1/users/{id}/assign_zones — Assign geographic zones

### Entity: ChatbotConversation (Citizen Chatbot Sessions)
- Fields: citizen_id (str), citizen_name (str), channel (str — web/mobile/sms/voice/whatsapp), status (str — active/waiting_human/handed_off/resolved/abandoned/timed_out), topic (str — report_issue/check_status/ask_question/schedule/complaint/general), language (str), message_count (int), ai_resolution_achieved (bool), satisfaction_score (int), escalation_reason (str), assigned_agent_id (str), service_request_id (str), ai_sentiment (str — positive/neutral/negative/frustrated), avg_response_latency_ms (int), total_tokens_used (int), last_message_preview (str), started_at (str), resolved_at (str)
- POST /api/v1/chatbot_conversations/{id}/handoff — Escalate to human
- POST /api/v1/chatbot_conversations/{id}/resolve — Mark resolved
- POST /api/v1/chatbot_conversations/{id}/reopen — Reopen conversation
- POST /api/v1/chatbot_conversations/{id}/assign_agent — Assign human agent
- POST /api/v1/chatbot_conversations/{id}/rate — Submit satisfaction rating

### Entity: AssistantQuery (Internal AI Assistant Sessions)
- Fields: user_id (str), user_role (str), query_text (str), response_text (str), query_type (str — search/report/analyze/predict/compare/summarize), domain_entities_referenced (list[str]), status (str — processing/completed/failed/cached), tokens_prompt (int), tokens_completion (int), latency_ms (int), model_used (str), rag_sources_count (int), rag_relevance_avg (float), content_safety_passed (bool), cached (bool), feedback_rating (int), feedback_comment (str), session_id (str)
- POST /api/v1/assistant_queries/{id}/feedback — Submit feedback
- POST /api/v1/assistant_queries/{id}/regenerate — Regenerate response
- POST /api/v1/assistant_queries/{id}/export — Export to PDF/CSV

### Entity: Notification (Intelligent Notification Hub)
- Fields: title (str), body (str), notification_type (str — alert/info/warning/action_required/reminder/escalation), channel (str — push/sms/email/in_app/webhook), priority (str — critical/high/medium/low), status (str — queued/sending/delivered/read/failed/expired), recipient_id (str), recipient_role (str), sender_agent (str), related_entity_type (str), related_entity_id (str), delivery_attempts (int), delivered_at (str), read_at (str), action_url (str), ai_generated (bool), ai_personalization_applied (bool), expiry_hours (int), zone_id (str)
- POST /api/v1/notifications/broadcast — Send to multiple recipients by role/zone
- POST /api/v1/notifications/{id}/retry — Retry failed delivery
- POST /api/v1/notifications/{id}/acknowledge — Recipient acknowledges
- POST /api/v1/notifications/{id}/escalate — Escalate unread notification

### Entity: AuditLog (AI Governance)
- Fields: event_type (str — chat/agent_call/tool_invocation/content_filter/embedding/search/file_upload/chatbot_message/assistant_query/notification_sent/user_action), agent_name (str), user_id (str), user_role (str), prompt_text (str), completion_text (str), token_count_prompt (int), token_count_completion (int), latency_ms (int), model_name (str), content_safety_result (str), content_safety_categories (str), pii_detected (bool), session_id (str), correlation_id (str), ip_address (str), status (str — success/filtered/error/rate_limited)
- (Read-only — no create/update/delete from API, only query)

### Cross-Domain AI Correlation
- AI correlates incidents with nearby sensors, affected assets, transit disruptions, impacted zones, active chatbot conversations, and relevant notifications
- Natural-language queries from the AI assistant span all 14 entity types simultaneously
- AI generates unified situational awareness reports aggregating all domains
- Chatbot can trigger incident creation, service request filing, and notification dispatch

---

## Scalability Requirements

- 50,000 concurrent WebSocket connections for real-time command center
- 250,000 IoT sensor streams with p99 < 500ms ingestion latency
- GPT-4o inference: 500 concurrent AI sessions (chatbot + assistant combined) with p95 < 3s
- AI Search: 1,000 queries/second across 500,000+ documents
- 50,000 citizen chatbot interactions/day with burst 5,000/hour
- 2,000 internal AI assistant queries/hour sustained
- 500+ concurrent operator sessions
- Token budget: 3M tokens/hour across all 8 AI agents
- 100TB+ blob storage for sensor data, media, photos, audio, and audit logs
- 5TB Cosmos DB at 50,000 RU/s for hot telemetry, chatbot sessions, and AI cache
- Redis 50GB for session management, chatbot context, assistant cache, and rate limiting
- SQL database for relational user management, work orders, citizen cases, fleet records, and notifications
- Table Storage for high-volume audit log archival (billions of entries)
- Auto-scale 4 to 50 container instances based on sensor + AI + chatbot load

---

## Security & Compliance

- Entra ID with Conditional Access for operators; anonymous + optional auth for citizen chatbot
- RBAC with 14 roles: Commander, Dispatcher, GridEngineer, ComplianceOfficer, CitizenServiceAgent, TransitManager, FleetManager, ZoneAdmin, DataAnalyst, MaintenancePlanner, AISafetyReviewer, SystemAdmin, NotificationManager, Citizen
- Azure OpenAI via Managed Identity with Cognitive Services OpenAI User role — zero API keys
- AI Search via Managed Identity with Search Index Data Contributor + Search Service Contributor
- Content safety filtering on all public AI endpoints (chatbot and citizen-facing) with custom blocklists
- Enhanced prompt injection detection for citizen chatbot (untrusted input)
- PII scrubbing on chatbot outputs — citizens may inadvertently share SSN, medical info, addresses
- Per-role token rate limiting: operators 100 tok/s, citizens 50 tok/s, chatbot 30 tok/s
- User session management with JWT tokens, refresh rotation, and concurrent session limits
- Full audit logging with 7-year retention for both chatbot and assistant interactions
- FedRAMP Moderate, SOC2 Type II, HIPAA across all AI data pipelines
- Encryption at rest (AES-256) and in transit (TLS 1.3)
- Key Vault with HSM-backed keys, soft delete, purge protection
- Private endpoints for all Azure services
- WAF on citizen-facing chatbot and API endpoints
- Network segmentation: IoT DMZ, AI private subnet, chatbot public subnet, management plane
- Chatbot conversation data classified as PII with 90-day auto-purge for anonymous sessions

---

## Performance Requirements

- Citizen chatbot: p50 < 1s, p95 < 2s, p99 < 4s (RAG + LLM + context retrieval)
- Internal AI assistant: p50 < 1.5s, p95 < 3s, p99 < 5s (cross-domain queries)
- RAG retrieval: p50 < 100ms, p95 < 300ms
- Agent tool-calling: < 2s per invocation
- Sensor ingestion: p50 < 100ms, p95 < 250ms, p99 < 500ms
- API (non-AI): p50 < 50ms, p95 < 200ms, p99 < 500ms
- AI incident triage: < 30 seconds end-to-end
- Content safety: < 200ms additional latency
- File upload analysis: < 10s for photos (Vision), < 30s for audio (Whisper)
- Cross-domain correlation: < 5s for multi-entity AI query
- Notification delivery: p95 < 5s for critical push, p95 < 30s for email
- User authentication: < 500ms for token validation
- SLA: 99.99%, RTO: 5 min, RPO: 30 sec

---

## Integration Requirements

### Upstream
- Azure OpenAI Service (GPT-4o, GPT-4o Vision, Whisper, text-embedding-ada-002)
- Azure AI Search for RAG vector store
- Azure AI Content Safety for chatbot and assistant filtering
- 12 IoT sensor vendor APIs via normalized adapter
- City GIS (ArcGIS) for spatial queries
- National Weather Service API, EPA AirNow API

### Downstream
- Computer-Aided Dispatch (CAD)
- City ERP (SAP) for work orders
- Citizen notification service (SMS via Twilio, email via SendGrid, push via Azure Notification Hubs)
- Open data portal (CKAN)
- Regional transit feed (GTFS-RT)
- Fleet GPS tracking provider
- Active Directory for user provisioning

### Event-Driven
- Event Grid for agent triggers and notification fanout
- Service Bus for chatbot message queue and assistant query queue
- Event Hub for sensor fan-out and audit log streaming
- Webhook callbacks for third-party systems and notification delivery receipts

---

## Acceptance Criteria

1. **14 Entity CRUD**: All 14 entities (Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, User, ChatbotConversation, AssistantQuery, Notification, AuditLog) have full CRUD endpoints with proper schemas, validation, and 12 realistic seed records each
2. **Action Endpoints**: All 50+ domain action endpoints (triage, dispatch, escalate, predict, calibrate, optimize, deploy, evacuate, approve, handoff, resolve, broadcast, activate, suspend, unlock, assign, feedback, regenerate, retry, acknowledge, etc.) are generated and routable
3. **AI Agents**: 8 Semantic Kernel agents deployed with tool-calling and agent-to-agent delegation
4. **Citizen Chatbot**: Public-facing chatbot with conversation creation, message exchange, history, handoff, feedback, and multi-turn context
5. **Internal AI Assistant**: Operator-facing assistant with natural-language queries, reports, analysis, and proactive suggestions
6. **User Management**: Full user lifecycle with roles, departments, zones, MFA, preferences, token tracking, and account actions
7. **Notification Hub**: Multi-channel notifications with broadcast, retry, acknowledge, escalate, and AI-generated content
8. **RAG Pipeline**: AI Search index with hybrid search, verified retrieval with >0.75 relevance
9. **Content Safety**: 100% of injection attempts blocked on chatbot, all flagged interactions audit-logged
10. **Dashboard**: Interactive dashboard shows all 14 entity types with KPI tiles, status badges, and entity-specific metrics
11. **Frontend**: React + Vite SPA with design tokens, dark mode, responsive nav, chatbot widget, assistant panel, user management views, notification center, loading skeletons, error boundaries, toast notifications
12. **Data Stores**: All 6 data stores (Cosmos, SQL, Blob, Redis, AI Search, Table) properly configured with Bicep modules
13. **Security**: Zero API keys, Managed Identity everywhere, WAF enabled, RBAC with 14 roles, session management, PII scrubbing
14. **Governance**: All policy checks pass, WAF alignment >95% across all 5 pillars
15. **Performance**: API p95 < 200ms, chatbot p95 < 2s, assistant p95 < 3s, sensor ingestion p99 < 500ms
16. **Seed Data**: 12 realistic records per entity (168 total) with domain-aware values, dynamic timestamps, and realistic relationships between entities
