# Intent: Smart Retail Inventory & Supply Chain AI

## Project Configuration

- **Project Name:** smart-retail-inventory
- **App Type:** api
- **Data Stores:** cosmos, blob, redis
- **Region:** eastus2
- **Environment:** dev
- **Auth:** entra-id
- **Compliance:** SOC2

---

## Problem Statement

FreshMart Retail operates 340+ stores nationwide carrying 85,000+ SKUs including 12,000 perishable items (fresh produce, dairy, bakery, deli, meat/seafood). The company loses $47M annually to spoilage and markdowns on expiring products -- 8.2% of perishable inventory is discarded before sale. Store managers manually decide when to mark down near-expiry items, often too late to recover meaningful revenue. Demand forecasting relies on spreadsheet-based seasonal averages that miss weather, local events, and trend shifts. Restocking decisions are made by individual buyers using gut instinct and vendor relationships rather than data-driven optimization.

**Affected Users:** 340 store managers, 45 regional supply chain planners, 22 category buyers, 1,200+ department leads across produce/dairy/bakery/deli/meat

**Cost of Inaction:** $47M annual spoilage loss, 8.2% perishable waste rate (industry best-in-class is 3.1%), missed $18M in recoverable revenue through optimized markdowns, 15% overstocking on 2,400+ slow-moving SKUs, increasing food waste ESG liability

---

## Business Goals

1. **Reduce perishable spoilage by 60%** -- from 8.2% waste rate to under 3.3% within 12 months
2. **Recover $12M+ annually** through AI-optimized dynamic markdown pricing on near-expiry items
3. **Cut overstock carrying costs by 25%** -- eliminate dead stock through predictive demand signals
4. **Achieve 96% shelf availability** for top 500 SKUs (current: 89%) through smarter restocking
5. **Reduce emergency reorders by 40%** -- AI anticipates demand spikes from weather, events, holidays
6. **Automate 80% of restocking decisions** -- shift buyers from manual PO creation to exception-based review
7. **Improve fresh produce gross margin by 3.5 percentage points** through waste reduction and dynamic pricing

**Revenue/Cost Impact:** $47M spoilage reduction target, $12M markdown recovery, $8M overstock reduction, $3M labor savings from automated reordering = $70M total addressable savings

---

## Target Users

### Primary: Store Manager
- **Persona:** Carlos Mendez, Store Manager -- FreshMart #127
- **Role:** Daily inventory oversight, markdown approval, shrink accountability
- **Technical Proficiency:** POS systems, basic inventory app, tablet-based
- **Needs:** Morning dashboard showing at-risk items, one-tap markdown approval, AI-suggested discount percentages with projected sell-through rates

### Secondary: Category Buyer
- **Persona:** Rachel Kim, Senior Fresh Produce Buyer
- **Role:** Vendor negotiations, purchase order management, seasonal planning
- **Technical Proficiency:** ERP systems, Excel power user, BI dashboards
- **Needs:** Demand forecasts by region/store cluster, optimal order quantities, vendor performance scores, seasonal trend predictions

### Tertiary: Supply Chain Planner
- **Persona:** David Okafor, Regional Supply Chain Director
- **Role:** Distribution center allocation, transportation optimization, waste KPI ownership
- **Technical Proficiency:** Supply chain management platforms, SQL queries, analytics tools
- **Needs:** Cross-store inventory visibility, transfer recommendations between stores, waste trend analytics, DC allocation optimization

---

## Functional Requirements

- Product catalog management for 85,000+ SKUs across produce, dairy, bakery, deli, meat, grocery, and frozen categories with shelf life tracking, supplier linkage, and storage temperature classification
- Real-time store inventory tracking with quantity on hand, expiry dates, shelf-life-remaining calculations, and location zones (floor, backroom, cooler, freezer) across 340 stores
- AI-powered demand forecasting per product-store combination incorporating weather impact, local event signals, and seasonal trend detection with confidence scoring
- Dynamic markdown recommendations for near-expiry perishable items with AI-calculated discount percentages, predicted sell-through rates, and revenue recovery estimates
- Automated purchase order generation when inventory falls below safety stock with supplier routing, priority classification (routine/urgent/emergency), and AI-generated vs manual flagging
- Supplier performance management with lead time tracking, reliability scores, on-time delivery rates, quality ratings, and category specialization
- Inter-store transfer proposals for overstock redistribution with estimated savings, AI confidence scoring, and dispatch-to-completion lifecycle tracking
- Wastage recording with root cause classification (expired, damaged, recalled, quality), cost impact, and preventability analysis to feed back into demand forecasting
- Configurable dynamic pricing rules per product category with expiry-trigger thresholds, escalating discount levels, minimum price floors, and auto-approve settings
- Inventory alert rules with configurable thresholds for low-stock, expiry warnings, demand spikes, overstock detection, and waste threshold breaches with multi-channel notifications

---

## Scalability Requirements

- **Concurrent Users:** 500 store managers accessing dashboards simultaneously during morning shift
- **Data Volume:** 85,000 SKUs x 340 stores = 28.9M inventory records updated daily
- **API Rate:** 2,000 requests/minute during peak store operations (7-9 AM, 4-7 PM)
- **Forecast Generation:** Nightly batch processing of demand forecasts for all product-store combinations
- **Real-time Events:** POS sales feed processing at 50,000 transactions/hour across all stores
- **Storage:** 18 months of historical sales/inventory data (~2TB)

---

## Security & Compliance

### Authentication & Authorization
- Microsoft Entra ID SSO for all users
- Role-based access control:
  - `Store.Manager` -- store-level inventory, markdown approval, waste logging
  - `Category.Buyer` -- cross-store demand data, purchase order management
  - `Supply.Planner` -- all stores, transfer management, analytics
  - `System.Admin` -- pricing rules, alert configuration, system settings
- Managed Identity for all Azure service authentication

### Data Security
- Encryption at rest (AES-256) for all inventory and pricing data
- TLS 1.3 for all API communications
- No PII in inventory data -- user identifiers only
- Soft delete and purge protection for Key Vault
- Audit logging for all pricing changes and markdown approvals

### Compliance
- **SOC2:** Access controls, audit logging, change management
- **Food Safety Modernization Act (FSMA):** Traceability for recalled products
- Data residency within US regions

---

## Performance Requirements

- **Dashboard Load:** < 3 seconds for store-level inventory overview (500+ items)
- **Markdown Decision API:** < 2 seconds for AI discount recommendation
- **Demand Forecast Query:** < 5 seconds for 30-day forecast per product-store
- **Bulk Inventory Update:** < 30 seconds for full store inventory refresh (2,500 items)
- **API p95 Latency:** < 500ms for GET requests, < 2 seconds for POST
- **Availability SLA:** 99.9% uptime
- **RTO:** 2 hours, **RPO:** 15 minutes

---

## Integration Requirements

### Upstream Systems
- **POS System (NCR)** -- Real-time sales transaction feed for demand signal updates
- **Warehouse Management System (Blue Yonder)** -- Inbound shipment notifications, DC inventory levels
- **Weather API (OpenWeatherMap)** -- 10-day forecasts for demand impact modeling
- **Microsoft Entra ID** -- SSO authentication and group-based RBAC

### Downstream Systems
- **ERP (SAP S/4HANA)** -- Push approved purchase orders for fulfillment
- **Transportation Management** -- Store transfer logistics coordination
- **BI Platform (Power BI)** -- Waste analytics, demand accuracy metrics, ROI dashboards

### Event-Driven Triggers
- POS sale recorded -> update real-time inventory -> recalculate demand forecast
- Item reaches expiry threshold -> generate markdown recommendation -> notify store manager
- Inventory falls below safety stock -> auto-generate purchase order draft -> route for approval
- Demand spike detected -> trigger emergency reorder -> alert supply chain planner

---

## Acceptance Criteria

### Functional Tests
- AI demand forecast accuracy within 15% MAPE (Mean Absolute Percentage Error) on 30-day horizon
- Markdown recommendations generated for all items within 3 days of expiry
- Purchase orders auto-generated when inventory drops below safety stock threshold
- Store transfers proposed when overstock detected at one store and low stock at nearby store
- All 10 entity CRUD endpoints operational with 12 seed records each

### Performance Benchmarks
- Dashboard loads under 3 seconds with 500+ inventory items
- Forecast API responds under 5 seconds for 30-day product-store query
- System handles 500 concurrent dashboard sessions without degradation

### Security Validation
- Managed Identity used for Cosmos DB, Blob Storage, Redis, Azure OpenAI
- No secrets in code or environment variables
- RBAC enforced -- Store.Manager cannot modify pricing rules
- All API endpoints require authenticated Entra ID token

---

*Generated for enterprise proof-of-concept use*
*Target: FreshMart Retail -- AI-Powered Inventory & Supply Chain Optimization*
