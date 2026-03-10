# demo-doc-intelligence-extractor

> An enterprise document processing service that accepts uploaded files and
> processes them through Azure Document Intelligence using specialized prebuilt
> models (general document, layout, invoice, receipt, ID document). The service
> extracts full text content, identifies tables with their structure, and pulls
> out key-value pairs. Results are displayed in an organized HTML interface
> showing extracted text, structured tables, and detected fields, with optional
> archival to Azure Blob Storage.

## Problem Statement

Organizations process thousands of documents daily -- invoices, contracts,
receipts, ID documents, and general PDFs -- that require manual data entry or
bespoke OCR pipelines. Staff spend 30-40% of their time re-keying data from
documents into downstream systems, leading to errors, delays, and audit risk.
Existing solutions require per-document-type integrations, lack a unified
extraction API, and do not provide structured table parsing alongside key-value
extraction in a single call. The cost of manual document processing is estimated
at $1.8M/year across 12 business units.

## Business Goals

- Reduce manual document data-entry effort by 80% within 6 months of launch
- Achieve extraction accuracy above 95% for typed documents (invoices, forms)
- Support 5 document model types from day one (general, layout, invoice, receipt, ID)
- Provide structured table extraction alongside key-value pairs in a single API call
- Optional archival of raw documents and extracted results to Blob Storage
- KPI: Average processing time per document under 5 seconds (p95)
- KPI: API availability 99.9% uptime

## Target Users

- **Business Analyst** -- uploads invoices and receipts for finance reconciliation; low technical proficiency
- **Document Operations Specialist** -- bulk-processes contracts and ID documents; intermediate proficiency
- **Developer / Integrator** -- calls the API from line-of-business applications; high technical proficiency
- **Compliance Officer** -- reviews extraction audit logs for data handling compliance

## Functional Requirements

- REST endpoint `POST /analyze` accepting multipart file upload (PDF, JPEG, PNG, TIFF, BMP)
- Query parameter `model` to select prebuilt model: `general`, `layout`, `invoice`, `receipt`, `id-document`
- Extract and return: full page text content per page, tables with row/column structure, key-value pairs (field name + confidence score)
- HTML landing page (`GET /`) listing supported models, usage instructions, links to docs and health endpoints
- Health check endpoint `GET /health` for liveness and readiness probes
- Optional `store=true` query parameter to archive uploaded document and JSON result to Azure Blob Storage
- Model info endpoint `GET /models` returning list of supported model IDs and descriptions
- Extraction result endpoint: structured JSON with `pages`, `tables`, `key_value_pairs`, `model_used`, `confidence`
- Key Vault integration for storing Document Intelligence endpoint and API key as secrets
- Structured JSON logging for every analysis request (model, page count, table count, duration_ms)

## Scalability Requirements

- 200 concurrent document analysis requests
- Peak load: 50 documents/minute sustained, 150/minute burst
- Document size: up to 50 MB per file, up to 2000 pages
- Storage: up to 10 TB blob archives over 3 years
- Single region initially (eastus2), expand based on demand
- Auto-scale from 1 to 10 container instances based on CPU/memory

## Security & Compliance

- Authentication: Managed Identity for all Azure service access (Document Intelligence, Key Vault, Blob Storage)
- Authorization: API key validation for external callers (stored in Key Vault)
- Data classification: confidential (uploaded documents may contain PII)
- Encryption: TLS 1.3 in transit, platform-managed keys at rest
- Document retention: configurable (default 90 days), automated Blob lifecycle policy
- Secrets: Document Intelligence endpoint and key stored in Key Vault, never in code or config
- No raw document content logged; only metadata (filename, page count, model, duration)
- Network: public endpoint with TLS; future private endpoint support

## Performance Requirements

- Document analysis latency: p50 < 2s, p95 < 5s, p99 < 10s
- API health check: p99 < 100ms
- Cold start: < 8 seconds for container instance
- Availability SLA: 99.9% uptime
- RTO: 1 hour, RPO: 24 hours

## Integration Requirements

- Upstream: Azure Document Intelligence (prebuilt models REST API v4.0)
- Upstream: Azure Blob Storage for document archival and result storage
- Upstream: Azure Key Vault for secret management (DI endpoint, DI key)
- Downstream: REST API consumers (finance, operations, developer integrations)
- Monitoring: Application Insights for per-request telemetry, Log Analytics for audit

## Acceptance Criteria

- `POST /analyze?model=invoice` with a PDF returns JSON with `key_value_pairs` containing at minimum `VendorName` and `InvoiceTotal`
- `POST /analyze?model=general` returns non-empty `pages[].content`
- `POST /analyze?model=layout` returns structured `tables` with `row_count` and `column_count`
- `GET /models` returns all 5 model descriptors with `model_id` and `description`
- `GET /health` returns `{"status": "healthy"}` within 100ms
- Uploading with `store=true` creates a blob in the configured container
- All secrets (DI endpoint/key) retrieved from Key Vault at runtime, not from env vars directly
- Ruff lint passes with no errors
- Pytest suite passes with ≥ 90% coverage on route handlers

## Configuration

- **App Type**: api
- **Data Stores**: blob
- **Region**: eastus2
- **Environment**: dev
- **Auth**: managed-identity
