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

### Entity: Product (An individual SKU in the retail catalog)
- Fields: name (str), sku (str), category (str — produce/dairy/bakery/deli/meat/grocery/frozen), subcategory (str), shelf_life_days (int), unit_cost (float), retail_price (float), supplier_id (str), is_perishable (bool), storage_temp (str — ambient/chilled/frozen), weight_unit (str), min_order_qty (int)

### Entity: StoreInventory (Current stock level of a product at a specific store)
- Fields: store_id (str), product_id (str), quantity_on_hand (int), quantity_on_order (int), shelf_life_remaining_days (int), last_received_date (datetime), expiry_date (datetime), location_zone (str — floor/backroom/cooler/freezer), status (str — in-stock/low/critical/expired/on-order)
- Actions: restock, transfer, markdown, dispose

### Entity: DemandForecast (AI-generated demand prediction for a product-store combination)
- Fields: product_id (str), store_id (str), forecast_date (datetime), predicted_demand (int), confidence_score (float), forecast_horizon_days (int), contributing_factors (list[str]), weather_impact (float), event_impact (float), trend_direction (str — rising/stable/declining)

### Entity: MarkdownRecommendation (AI-suggested discount for near-expiry items)
- Fields: product_id (str), store_id (str), current_price (float), recommended_price (float), discount_pct (float), days_until_expiry (int), predicted_sellthrough_pct (float), revenue_recovery (float), status (str — pending/approved/rejected/applied), recommended_at (datetime)
- Actions: approve, reject

### Entity: PurchaseOrder (A restocking order placed with a supplier)
- Fields: supplier_id (str), store_id (str), order_date (datetime), expected_delivery (datetime), total_cost (float), total_items (int), status (str — draft/submitted/confirmed/shipped/delivered/cancelled), is_ai_generated (bool), priority (str — routine/urgent/emergency)
- Actions: submit, confirm, cancel

### Entity: Supplier (A vendor providing products)
- Fields: name (str), contact_email (str), lead_time_days (int), reliability_score (float), region (str), min_order_value (float), payment_terms (str), category_specialization (str), on_time_delivery_pct (float), quality_rating (float)

### Entity: StoreTransfer (Movement of inventory between stores to prevent waste)
- Fields: source_store_id (str), destination_store_id (str), product_id (str), quantity (int), transfer_reason (str — overstock/demand-shift/expiry-risk/promotion), status (str — proposed/approved/in-transit/completed), estimated_savings (float), ai_confidence (float)
- Actions: approve, dispatch, complete

### Entity: WastageRecord (Record of disposed or expired inventory)
- Fields: product_id (str), store_id (str), quantity_wasted (int), waste_reason (str — expired/damaged/recalled/quality), cost_lost (float), disposal_date (datetime), was_markdown_attempted (bool), category (str), preventable (bool)

### Entity: PricingRule (Dynamic pricing rules for markdown automation)
- Fields: category (str), days_before_expiry_trigger (int), initial_discount_pct (float), escalation_discount_pct (float), min_price_floor_pct (float), max_discount_pct (float), auto_approve (bool), applies_to_perishable (bool), active (bool)

### Entity: AlertRule (Configurable alert thresholds for inventory events)
- Fields: name (str), alert_type (str — low-stock/expiry-warning/demand-spike/overstock/waste-threshold), threshold_value (float), severity (str — info/warning/critical), notification_channel (str — email/sms/dashboard/teams), store_scope (str — all/region/specific), active (bool)

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
