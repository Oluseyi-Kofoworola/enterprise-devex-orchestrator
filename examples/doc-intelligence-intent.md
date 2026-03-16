# doc-intelligence-platform

> An enterprise document intelligence platform that ingests, classifies, extracts,
> reviews, and archives business documents at scale. Supporting 8 document types
> (invoices, receipts, contracts, ID documents, purchase orders, tax forms, medical
> records, and general PDFs), the platform uses Azure Document Intelligence for
> structured extraction, provides a review/approval workflow for human-in-the-loop
> validation, supports batch processing of document queues, and tracks extraction
> templates and confidence metrics. A React SPA dashboard shows real-time processing
> status, extraction accuracy analytics, and document audit trails.

## Problem Statement

Organizations process 10,000+ documents daily across finance, legal, HR, and
operations -- invoices, contracts, receipts, ID documents, purchase orders, and
tax forms -- requiring manual data entry or fragmented OCR pipelines. Staff spend
30-40% of their time re-keying data, leading to a 4.2% error rate, 3-day average
processing lag, and $2.4M/year in labor costs across 15 business units. Existing
solutions lack unified multi-model extraction, have no review workflow for
low-confidence results, cannot batch-process document queues, and provide no
analytics on extraction quality over time. Compliance teams have no visibility
into document handling lineage, creating audit risk for SOC2 and HIPAA-regulated
document types.

## Business Goals

- Reduce manual document data-entry effort by 85% within 6 months
- Achieve extraction accuracy above 97% for typed documents (invoices, POs, tax forms)
- Process 500 documents/hour sustained throughput with batch queue support
- Provide human-in-the-loop review workflow for extractions below 90% confidence
- Track extraction templates and confidence metrics with historical trend analytics
- Support 8 document model types from day one
- KPI: Average processing time per document under 4 seconds (p95)
- KPI: Review queue turnaround under 2 hours for flagged documents
- KPI: API availability 99.9% uptime
- KPI: Document classification accuracy above 92%

## Target Users

- **Business Analyst** -- uploads invoices and receipts for finance reconciliation; reviews flagged extractions; low technical proficiency
- **Document Operations Specialist** -- manages batch processing queues, monitors throughput dashboards, escalates failures; intermediate proficiency
- **Developer / Integrator** -- calls extraction and batch APIs from line-of-business applications; high technical proficiency
- **Compliance Officer** -- reviews audit logs, document retention policies, and extraction lineage; intermediate proficiency
- **Team Lead** -- monitors extraction accuracy trends, assigns review tasks, approves template configurations; intermediate proficiency

## Functional Requirements

### Entity: Document
- Fields: filename (str), file_type (str), file_size_bytes (int), model_type (str), status (str), uploaded_by (str), upload_date (datetime), blob_url (str), page_count (int), confidence_score (float), category (str), department (str), priority (str), retention_days (int), is_archived (bool)
- Endpoints: POST /documents (upload), GET /documents (list with filters), GET /documents/{id}, POST /documents/{id}/analyze, POST /documents/{id}/archive, DELETE /documents/{id}

### Entity: ExtractionResult
- Fields: document_id (str), model_used (str), status (str), extracted_text (str), table_count (int), field_count (int), confidence_avg (float), confidence_min (float), processing_time_ms (int), page_results (str), key_value_pairs (str), tables_json (str), error_message (str), extracted_at (datetime), reviewed (bool), reviewer_id (str)
- Endpoints: POST /extraction_results, GET /extraction_results, GET /extraction_results/{id}, POST /extraction_results/{id}/approve, POST /extraction_results/{id}/reject

### Entity: BatchJob
- Fields: name (str), status (str), total_documents (int), processed_count (int), failed_count (int), started_at (datetime), completed_at (datetime), created_by (str), model_type (str), priority (str), error_summary (str), progress_pct (float)
- Endpoints: POST /batch_jobs (create queue), GET /batch_jobs, GET /batch_jobs/{id}, POST /batch_jobs/{id}/cancel, POST /batch_jobs/{id}/retry

### Entity: ExtractionTemplate
- Fields: name (str), model_type (str), description (str), expected_fields (str), validation_rules (str), confidence_threshold (float), is_active (bool), created_by (str), created_at (datetime), usage_count (int), avg_accuracy (float), category (str)
- Endpoints: POST /extraction_templates, GET /extraction_templates, GET /extraction_templates/{id}, POST /extraction_templates/{id}/activate, POST /extraction_templates/{id}/deactivate

### Entity: ReviewTask
- Fields: document_id (str), extraction_id (str), assigned_to (str), status (str), priority (str), review_notes (str), corrections_json (str), created_at (datetime), completed_at (datetime), review_duration_mins (int), category (str), confidence_flag (str)
- Endpoints: POST /review_tasks, GET /review_tasks, GET /review_tasks/{id}, POST /review_tasks/{id}/complete, POST /review_tasks/{id}/escalate, POST /review_tasks/{id}/reassign

### Entity: AuditEntry
- Fields: action (str), entity_type (str), entity_id (str), performed_by (str), timestamp (datetime), details (str), ip_address (str), department (str), result (str), duration_ms (int)
- Endpoints: POST /audit_entries, GET /audit_entries, GET /audit_entries/{id}

### Entity: ModelConfig
- Fields: model_id (str), display_name (str), description (str), version (str), supported_formats (str), max_file_size_mb (int), is_enabled (bool), avg_latency_ms (int), total_invocations (int), accuracy_rate (float), last_used_at (datetime), category (str)
- Endpoints: POST /model_configs, GET /model_configs, GET /model_configs/{id}, POST /model_configs/{id}/enable, POST /model_configs/{id}/disable

### Entity: RetentionPolicy
- Fields: name (str), document_category (str), retention_days (int), action_on_expiry (str), is_active (bool), created_by (str), created_at (datetime), affected_documents (int), department (str), compliance_framework (str)
- Endpoints: POST /retention_policies, GET /retention_policies, GET /retention_policies/{id}, POST /retention_policies/{id}/activate

- Health check endpoint `GET /health` for liveness and readiness
- Dashboard analytics endpoint `GET /analytics/overview` for extraction metrics
- Structured JSON logging for every operation (action, model, page count, duration_ms)
- Key Vault integration for Document Intelligence endpoint and API key

## Scalability Requirements

- 500 concurrent document analysis requests
- Peak load: 150 documents/minute sustained, 400/minute burst
- Batch queue: up to 10,000 documents per batch job
- Document size: up to 50 MB per file, up to 2000 pages
- Storage: up to 25 TB blob archives over 3 years
- Extraction results: up to 50M records in Cosmos DB
- Single region initially (eastus2), expand based on demand
- Auto-scale from 2 to 20 container instances based on CPU/queue depth

## Security & Compliance

- Authentication: Managed Identity for all Azure service access
- Authorization: API key validation for external callers (stored in Key Vault)
- Data classification: confidential (documents may contain PII, PHI, financial data)
- Compliance: SOC2, HIPAA for medical document types
- Encryption: TLS 1.3 in transit, platform-managed keys at rest
- Document retention: configurable per-category via RetentionPolicy entity
- Secrets: all credentials stored in Key Vault, never in code or config
- Audit: complete lineage tracking via AuditEntry for every document operation
- No raw document content logged; only metadata (filename, page count, model, duration)
- Network: public endpoint with TLS; private endpoint support planned

## Performance Requirements

- Document analysis latency: p50 < 2s, p95 < 4s, p99 < 8s
- Batch job throughput: 500 documents/hour per worker
- API health check: p99 < 100ms
- Dashboard load: < 1.5 seconds for analytics overview
- Cold start: < 6 seconds for container instance
- Availability SLA: 99.9% uptime
- RTO: 1 hour, RPO: 4 hours

## Integration Requirements

- Upstream: Azure Document Intelligence (prebuilt models REST API v4.0)
- Upstream: Azure Blob Storage for document archival and result storage
- Upstream: Azure Cosmos DB for extraction results, templates, and audit log
- Upstream: Azure Key Vault for secret management
- Downstream: REST API consumers (finance, legal, operations, HR integrations)
- Downstream: Webhook notifications for batch job completion
- Monitoring: Application Insights for per-request telemetry, Log Analytics for audit

## Acceptance Criteria

- Upload a PDF invoice and receive structured extraction with VendorName and InvoiceTotal fields
- Batch job processes 100 documents and reports progress percentage
- Low-confidence extractions automatically create ReviewTask entries
- ExtractionTemplate controls which fields are expected and validates results
- AuditEntry created for every document upload, extraction, review, and deletion
- ModelConfig shows accuracy rates and invocation counts per model
- RetentionPolicy auto-archives documents past retention window
- Dashboard shows real-time extraction metrics, review queue depth, and accuracy trends
- All secrets retrieved from Key Vault at runtime
- Ruff lint passes with no errors
- Pytest suite passes with >= 90% coverage

## Configuration

- **App Type**: api
- **Data Stores**: blob, cosmos
- **Region**: eastus2
- **Environment**: dev
- **Auth**: managed-identity
- **Compliance**: SOC2, HIPAA
