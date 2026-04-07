# propane-delivery-platform

> Smart propane delivery and tank monitoring platform for regional fuel
> distributors with IoT tank sensors, route optimization, and automated billing.

## Configuration

- App Type: api
- Data Stores: cosmos, redis, blob
- Region: eastus2
- Environment: dev
- Auth: managed-identity
- Compliance: SOC2

## Problem Statement

Regional propane distributor serves 8,200 residential and commercial customers
across 14 counties. Manual tank level checks cause 340 emergency deliveries/month
at 3x normal cost. Route inefficiency wastes 18% of driver hours. Paper invoicing
delays payment collection by 12 days on average.

## Business Goals

- Eliminate 90% of emergency deliveries via predictive tank monitoring
- Reduce driver route time by 25% with AI-optimized routing
- Cut invoice-to-payment cycle from 12 days to 3 days
- Achieve 99.5% delivery accuracy with GPS-verified drop confirmation

## Target Users

1. **Dispatch Manager** -- Assigns routes, monitors fleet, handles emergency calls
2. **Delivery Driver** -- Follows optimized routes, confirms deliveries via mobile
3. **Customer Service Rep** -- Manages accounts, schedules deliveries, handles billing
4. **Operations Director** -- Reviews KPIs, fleet utilization, and revenue dashboards
