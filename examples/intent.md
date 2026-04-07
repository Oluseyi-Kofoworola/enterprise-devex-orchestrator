# demo-voice-agent

> AI-powered voice agent for Demo Health System's clinic network. Manages
> voice sessions, patients, appointments, prescriptions, triage, and staff.

## Configuration

- App Type: ai_app
- Data Stores: cosmos, redis, blob
- Region: eastus2
- Environment: dev
- Auth: managed-identity
- Compliance: HIPAA

## Problem Statement

Clinical staff spend too much time on manual phone workflows. Patients wait
8 minutes on hold, triage errors cost $1.8M/year, prescription verification
takes 6 minutes per call. No structured audit trail for HIPAA compliance.

## Business Goals

- Reduce patient wait time to under 30 seconds via AI voice agent
- Automate 75% of routine calls without human handoff
- Achieve 97% clinical triage accuracy
- Maintain HIPAA-compliant audit trail

## Target Users

1. **Patient** — Schedules appointments, requests refills, reports symptoms
2. **Clinical Staff** — Reviews AI-triaged calls, manages care levels
3. **Pharmacist** — Verifies refill requests, checks drug interactions
4. **IT Administrator** — Manages voice agent config and monitors performance

---





