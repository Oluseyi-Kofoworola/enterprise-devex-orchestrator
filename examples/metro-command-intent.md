# Metro Command — Metropolitan Operations Intelligence Platform

An AI-powered metropolitan operations platform managing emergency incidents, infrastructure assets, environmental sensors, citizen service requests, transit routes, utility grids, city zones, fleet vehicles, and work orders. Uses Azure OpenAI for AI chat, content safety, and predictive analytics.

---

## Configuration

- **App Type**: ai_app
- **Data Stores**: cosmos, blob, sql, redis, ai_search, table
- **Region**: eastus2
- **Environment**: dev
- **Auth**: entra-id
- **Compliance**: SOC2

---

## Problem Statement

City operations across 2M residents are fragmented across disconnected legacy systems. Emergency response averages 12 minutes. Utility outages go undetected. Citizens file duplicate service requests. Environmental compliance violations increasing yearly.

---

## Business Goals

- Reduce emergency dispatch triage time using AI incident classification
- Track infrastructure assets with health scores and maintenance history
- Monitor environmental sensors with threshold-based alerting
- Manage citizen service requests with duplicate detection
- Optimize transit routes with ridership analytics
- Track fleet vehicles with GPS and maintenance scheduling
- Organize city operations by geographic zones
- Generate and track work orders for maintenance

---

## Target Users

- **Operations Commander** — queries city status via AI dashboard
- **Dispatch Coordinator** — receives AI triage recommendations for incidents
- **Grid Engineer** — reviews AI failure predictions for infrastructure
- **Citizen** — reports issues and checks request status

---

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
