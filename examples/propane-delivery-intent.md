# propane-delivery-automation

> An enterprise-grade, AI-powered propane delivery automation platform for a
> regional propane distribution company. Combines IoT tank-level monitoring,
> ML-driven consumption forecasting, global propane price prediction, smart
> delivery scheduling, dynamic pricing, AI-optimized driver dispatch and
> supply logistics, automated billing, and a customer-facing mobile/web app
> — replacing manual meter reads, phone-call scheduling, and paper invoicing.

## Problem Statement

Our propane delivery company operates a fleet of 45 delivery trucks serving
12,000 residential and commercial customers across a 200-mile service radius.
Drivers currently perform manual tank reads on a fixed 30-day cycle, resulting
in 18% of deliveries arriving when tanks are still above 50% (wasted trips)
and 7% of customers running out of propane before the next scheduled delivery
(emergency calls, customer churn). Dispatchers manually assign routes each
morning using spreadsheets, with no optimization for distance or load. Pricing
is recalculated weekly by the office manager using spreadsheets that reference
wholesale propane indexes, and invoices are mailed on paper — averaging
22 days from delivery to payment. The company loses an estimated $1.8M/year
in inefficient routing, emergency deliveries, late payments, and customer
churn caused by run-outs. Additionally, the company has no predictive capability
— pricing reacts to yesterday's market instead of anticipating trends, consumption
forecasts are gut-feel estimates, and supply procurement is reactive rather than
planned. There is no AI or machine learning in any part of the operation.

## Business Goals

- Eliminate propane run-outs by triggering deliveries when AI-predicted days-to-empty falls below threshold
- Reduce wasted deliveries (tank > 50%) from 18% to under 3% using ML consumption forecasting
- Cut average delivery-to-payment cycle from 22 days to 2 days via automated billing
- Optimize driver routes to reduce total fleet mileage by 30% using AI route optimization
- Achieve real-time propane pricing accuracy within 1% of market wholesale index
- Predict global propane prices 7-30 days ahead with < 5% mean absolute error
- Forecast per-customer consumption 30-90 days ahead to enable proactive supply procurement
- Reduce supply procurement cost by 15% through AI-driven demand aggregation and bulk purchasing timing
- Provide customers self-service access to tank levels, AI consumption forecasts, delivery history, and invoices
- KPI: Customer retention rate above 95% (currently 88%)
- KPI: Average delivery cost per gallon reduced by 20% within 12 months
- KPI: AI consumption forecast accuracy > 90% (within 10% of actual usage)
- KPI: Global price prediction accuracy > 95% on 7-day horizon

## Target Users

- **Customer**: Views current tank level, delivery history, invoices, and payment status via web/mobile app; low technical proficiency
- **Delivery Driver**: Receives optimized route with stop sequence, records delivery volume, captures meter readings via mobile app; low-to-intermediate technical proficiency
- **Dispatcher**: Monitors fleet in real-time, manages delivery queue, handles exceptions and emergency requests; intermediate technical proficiency
- **Operations Manager**: Reviews fleet analytics, delivery KPIs, pricing reports, and customer satisfaction metrics; intermediate technical proficiency
- **Finance/Billing Team**: Manages invoicing, payment reconciliation, overdue accounts, and pricing configuration; intermediate technical proficiency
- **IT Administrator**: Manages IoT sensor fleet, monitors system health, configures integrations; high technical proficiency

## Functional Requirements

### Entity: Customer
- Fields: name (str), account_number (str), address (str), city (str), state (str), zip_code (str), phone (str), email (str), customer_type (str), status (str), latitude (float), longitude (float), zone (str), credit_status (str), balance (float), notes (str)
- Endpoints: POST /customers, GET /customers, GET /customers/{id}, PUT /customers/{id}, DELETE /customers/{id}

### Entity: Tank
- Fields: serial_number (str), customer_id (str), tank_size_gallons (int), install_date (datetime), last_inspection (datetime), next_inspection (datetime), latitude (float), longitude (float), address (str), status (str), sensor_id (str), current_level_pct (float), last_reading_at (datetime), tank_type (str), location (str)
- Endpoints: POST /tanks, GET /tanks, GET /tanks/{id}, PUT /tanks/{id}, POST /tanks/{id}/inspect

### Entity: TankReading
- Fields: tank_id (str), sensor_id (str), reading (float), temperature (float), pressure (float), battery_voltage (float), timestamp (datetime), signal_strength (int), anomaly_flag (bool), device_id (str)
- Endpoints: POST /tank_readings, GET /tank_readings, GET /tank_readings/{id}

### Entity: Delivery
- Fields: customer_id (str), tank_id (str), driver_id (str), route_id (str), scheduled_date (datetime), delivered_at (datetime), gallons_delivered (float), meter_start (float), meter_end (float), unit_price (float), amount (float), status (str), delivery_type (str), latitude (float), longitude (float), notes (str), signature_url (str)
- Endpoints: POST /deliveries, GET /deliveries, GET /deliveries/{id}, PUT /deliveries/{id}, POST /deliveries/{id}/complete, POST /deliveries/{id}/cancel

### Entity: Route
- Fields: name (str), driver_id (str), date (datetime), status (str), total_stops (int), completed_stops (int), total_gallons (float), total_miles (float), started_at (datetime), completed_at (datetime), depot_id (str), zone (str), estimated_duration_mins (int)
- Endpoints: POST /routes, GET /routes, GET /routes/{id}, PUT /routes/{id}, POST /routes/{id}/start, POST /routes/{id}/complete

### Entity: ServiceCall
- Fields: customer_id (str), tank_id (str), assigned_to (str), status (str), priority (str), category (str), description (str), scheduled_date (datetime), completed_at (datetime), resolution (str), review_notes (str), parts_used (str), labor_hours (float), cost (float)
- Endpoints: POST /service_calls, GET /service_calls, GET /service_calls/{id}, PUT /service_calls/{id}, POST /service_calls/{id}/complete, POST /service_calls/{id}/escalate

### Entity: Invoice
- Fields: customer_id (str), delivery_id (str), invoice_number (str), amount (float), tax (float), total (float), status (str), issued_date (datetime), due_date (datetime), paid_date (datetime), payment_method (str), balance (float), notes (str)
- Endpoints: POST /invoices, GET /invoices, GET /invoices/{id}, POST /invoices/{id}/send, POST /invoices/{id}/pay

### Entity: Inventory
- Fields: depot_id (str), product (str), quantity (float), units_available (float), units_reserved (float), reorder_point (float), last_delivery_date (datetime), cost_per_gallon (float), stock_level (float), status (str), warehouse (str)
- Endpoints: POST /inventory, GET /inventory, GET /inventory/{id}, PUT /inventory/{id}, POST /inventory/{id}/reorder

### Tank Monitoring & Smart Scheduling
- IoT tank-level ingestion API: receive telemetry from ultrasonic/pressure tank sensors (MQTT or HTTP POST) with tank ID, level percentage, temperature, timestamp
- Tank level history storage with configurable read intervals (default: every 4 hours)
- Usage pattern analysis: calculate daily burn rate per customer based on historical readings, weather correlation, and AI consumption model predictions
- Smart delivery trigger: when AI-predicted days-to-empty falls below configurable threshold (default: 7 days or 25% level), auto-create a delivery order
- Delivery order queue with priority scoring: emergency (< 10%), urgent (10-20%), standard (20-30%), top-up (30-40%)

### Driver Management & Route Optimization
- Driver profile management: license, certifications (HAZMAT, CDL), truck assignment, availability schedule
- Daily route generation: optimize stop sequence by driving distance, delivery volume, truck capacity, and time windows
- Driver mobile API: receive route, navigate to stops, record gallons delivered, capture tank meter photo, mark delivery complete
- Driver log API: record hours-of-service (HOS), pre-trip/post-trip inspection checklists, fuel purchases
- Real-time fleet GPS tracking with ETA updates to dispatch and customers

### Dynamic Pricing Engine
- Ingest daily wholesale propane price from market index API (Mont Belvieu, Conway)
- Calculate per-customer delivery price: base wholesale price + distance surcharge ($/mile from depot) + volume discount tiers + seasonal adjustment + margin
- Volume discount tiers: configurable brackets (e.g., 100-200 gal: 5% off, 200-500 gal: 10% off, 500+: 15% off)
- Price lock contracts: support fixed-price and cap-price annual contracts per customer
- Price quote API: given customer ID and estimated gallons, return itemized price breakdown

### Billing & Payments
- Auto-generate invoice on delivery completion with itemized charges: gallons × price/gal, delivery fee, taxes, discount applied
- Payment processing integration: credit card (Stripe), ACH/bank transfer, autopay enrollment
- Payment receipt generation (PDF) and delivery via email
- Accounts receivable tracking: outstanding balance, payment due date, overdue alerts
- Autopay: customers can enroll for automatic payment on delivery or monthly billing cycle

### Customer App & Notifications
- Customer dashboard: current tank level gauge, AI-predicted days-to-empty, next scheduled delivery, delivery history, invoices, payment status
- AI consumption insights: personalized monthly forecast ("Based on your usage pattern, your next delivery is estimated for March 15"), historical accuracy tracking
- Push notifications and email alerts: delivery scheduled, driver en route (with ETA), delivery complete, invoice ready, payment received, low tank warning, AI early-warning ("Usage is 20% above forecast — consider scheduling early delivery")
- Customer self-service: request early delivery, update payment method, download invoices, view price history
- Usage analytics: monthly/annual propane consumption charts, AI forecast vs. actual comparison, cost comparison year-over-year, projected annual spend

### AI-Powered Consumption Prediction
- ML model trained on historical tank readings, weather data (temperature, heating degree days), property size, household occupancy, and appliance profile to predict per-customer daily/weekly/monthly propane consumption
- Consumption forecast API: given customer ID and date range, return predicted gallons with confidence interval
- Seasonal pattern detection: automatically identify heating season ramp-up/ramp-down curves per customer segment (residential, commercial, agricultural)
- Anomaly detection: flag customers with consumption significantly above or below predicted range (potential leak, meter malfunction, or vacancy)
- Customer segmentation: cluster customers by usage pattern (high-constant, seasonal-peaker, low-intermittent) to optimize delivery batching
- Forecast dashboard for dispatchers: aggregated demand heatmap by region and week, enabling proactive fleet and inventory planning

### AI Global Propane Price Prediction
- ML model ingesting historical Mont Belvieu/Conway spot prices, crude oil futures (WTI, Brent), natural gas futures (Henry Hub), EIA inventory reports, seasonal demand curves, and geopolitical risk indicators
- Price prediction API: return 7-day, 14-day, and 30-day propane price forecast with confidence bands
- Buy signal engine: recommend optimal timing for bulk wholesale propane procurement based on predicted price troughs
- Cost-savings tracker: compare actual procurement cost vs. what would have been paid without AI timing recommendations
- Price trend alerts: notify finance team when model predicts price increase > 10% within 14 days, enabling early contract locks
- Model retraining pipeline: automated weekly retraining on latest market data with drift detection and accuracy monitoring

### AI Driver & Supply Logistics Optimization
- ML-based route optimization: factor in real-time traffic, historical delivery durations per stop, driver skill profiles, truck fuel efficiency curves, and delivery urgency to produce optimal daily routes
- Predictive driver scheduling: forecast delivery demand 1-2 weeks ahead and auto-generate driver shift schedules to match predicted load
- Fleet utilization optimizer: recommend truck-to-route assignments that minimize deadhead miles and balance truck wear evenly
- Predictive maintenance alerts: analyze truck telematics (engine hours, mileage, brake wear) to predict maintenance needs before breakdown
- Supply chain demand aggregation: aggregate predicted customer consumption across service area to forecast weekly/monthly bulk propane procurement volume
- Depot inventory optimizer: predict optimal propane inventory levels at each depot/terminal to prevent stockouts while minimizing holding costs
- What-if simulator: dispatchers can simulate adding/removing trucks, changing depot locations, or shifting delivery windows and see AI-predicted impact on cost and service level

### Email & Communication Automation
- Transactional emails to customers: delivery confirmation, invoice, payment receipt, low-tank alert, price change notification, AI consumption forecast summary (monthly)
- Driver notifications: daily AI-optimized route assignment, schedule changes, emergency dispatch
- Dispatcher alerts: AI-predicted run-out risk, driver delay, route deviation, demand surge warning
- Finance team: daily payment summary, overdue account alerts, weekly revenue report, AI price forecast and buy-signal alerts
- Operations team: weekly AI accuracy report (consumption forecast vs. actuals, price prediction vs. actuals)
- Configurable email templates with company branding

## Scalability Requirements

- 12,000 active customer accounts, growing 15% annually
- 45 delivery trucks, 150-200 deliveries/day
- IoT telemetry: 12,000 tanks × 6 readings/day = 72,000 data points/day
- AI inference: 12,000 consumption predictions/day (batch) + on-demand forecast queries
- Price prediction model: 1 inference/hour for market monitoring, batch retrain weekly
- Peak season (November-March): 2.5x delivery volume, 3x IoT read frequency
- API: 50 RPS sustained, 200 RPS peak (customer app + driver app + IoT ingestion + AI endpoints)
- ML training data: 3+ years of historical readings, weather, and pricing for model training
- Data retention: 7 years for billing/financial records, 3 years for telemetry, 5 years for ML training data

## Security & Compliance

- Auth: managed-identity for service-to-service, Entra ID for staff apps, OAuth2 + JWT for customer app
- PCI DSS compliance for payment card processing
- SOC2 Type II for enterprise customer contracts
- Role-based access: customer (own data only), driver (assigned routes), dispatcher (all routes), ops_manager (analytics + config), finance (billing), admin (full)
- PII protection: customer addresses, payment info, contact details encrypted at rest
- Audit trail: every delivery, payment, price change, and configuration update logged with actor and timestamp
- API rate limiting per client to prevent abuse
- IoT device authentication: per-device API keys with automatic rotation

## Performance Requirements

- IoT telemetry ingestion: p95 < 200ms per reading
- Tank level query: p50 < 50ms, p95 < 150ms (Redis-cached)
- AI consumption forecast query: p50 < 200ms, p95 < 500ms (pre-computed, Redis-cached)
- AI price prediction query: p50 < 150ms, p95 < 400ms (cached hourly)
- AI route optimization: p95 < 8s for 30-stop route (ML-enhanced vs. pure heuristic)
- Price calculation: p50 < 100ms, p95 < 300ms
- Invoice generation: p95 < 2s
- Customer dashboard load: p95 < 1s (including AI forecast widgets)
- Email delivery: within 60 seconds of triggering event
- ML batch prediction (all customers): < 15 minutes nightly
- ML model retraining: < 2 hours weekly
- SLA: 99.9% uptime
- RTO: 1 hour, RPO: 15 minutes

## Integration Requirements

- Upstream: IoT tank sensors (MQTT broker or HTTP webhook) for telemetry ingestion
- Upstream: Wholesale propane price index API (Mont Belvieu/Conway daily feed)
- Upstream: Weather API (OpenWeatherMap or NOAA) for burn-rate prediction, heating degree days, and seasonal adjustment
- Upstream: EIA (Energy Information Administration) API for weekly propane inventory reports and market data
- Upstream: Commodity futures data feed (CME) for crude oil and natural gas futures used in price prediction model
- Upstream: Azure AD (Entra ID) for staff authentication
- AI/ML: Azure Machine Learning for model training, versioning, and managed inference endpoints
- AI/ML: Azure AI Services for anomaly detection on tank telemetry and consumption patterns
- Downstream: Stripe API for credit card payments and ACH transfers
- Downstream: SendGrid or Azure Communication Services for transactional email
- Downstream: Google Maps / Azure Maps for route optimization and distance calculation
- Downstream: PDF generation service for invoices and receipts
- Event-driven: Delivery completion triggers invoice generation, email, and payment processing via Event Grid
- Event-driven: Low-tank-level event triggers delivery order creation and customer notification
- Monitoring: Application Insights for APM, Log Analytics for audit queries

## Acceptance Criteria

- IoT telemetry endpoint ingests readings and updates tank level within p95 latency target
- Smart delivery trigger correctly creates delivery orders when tank falls below threshold — verified with simulated sensor data
- Route optimization produces valid stop sequences that reduce total distance vs. naive ordering
- Price calculation matches expected output given wholesale price, distance, volume, and contract terms — within $0.01 precision
- Invoice auto-generates on delivery completion with correct line items, taxes, and totals
- Payment processing via Stripe test mode completes successfully for card and ACH
- Customer dashboard displays real-time tank level, delivery history, and invoices
- Email notifications sent for all lifecycle events (low tank, delivery scheduled, en route, delivered, invoice, payment received)
- RBAC enforcement: customer cannot view other customers' data, driver cannot modify pricing — verified by integration tests
- All endpoints enforce authentication and return correct HTTP status codes
- Health endpoint reports status of all dependencies (Cosmos DB, Redis, Stripe, email service)
- CI/CD pipeline passes: lint, tests, security scan, Bicep validation
- AI consumption forecast accuracy > 90% on 30-day horizon — verified with backtesting on historical data
- AI price prediction within 5% MAE on 7-day horizon — verified against held-out test period
- AI route optimizer produces routes with lower total distance than non-AI baseline in > 80% of test cases
- AI anomaly detection flags simulated leak scenario within 2 reading cycles
- Buy-signal engine recommendations are backtested against 12 months of historical pricing
- Governance validation passes with no FAIL status

## Configuration

- **App Type**: api
- **Data Stores**: cosmos, redis, blob
- **Region**: eastus2
- **Environment**: dev
- **Auth**: managed-identity
- **Compliance**: SOC2, PCI

## Version

- **Version**: 1
- **Based On**: none
- **Changes**: Initial scaffold — AI-powered propane delivery automation platform
