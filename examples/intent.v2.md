# demo-voice-agent

> Version 2 of the demo voice agent -- adds lab orders, referrals,
> insurance verification, and provider scheduling enhancements.

## Configuration

- App Type: ai_app
- Data Stores: cosmos, redis, blob
- Region: eastus2
- Environment: dev
- Auth: managed-identity
- Compliance: HIPAA

## Version

- Version: 2
- Based On: 1
- Changes: Added LabOrder and Referral entities, insurance verification workflow, enhanced provider scheduling with availability slots

## Problem Statement

Voice-first AI clinical assistant for outpatient clinics. V1 handled basic
appointment booking and prescription queries. V2 adds lab order management,
specialist referrals, and insurance pre-authorization to reduce phone hold
times from 12 minutes to under 2 minutes.

## Business Goals

- Add lab order lookup and status tracking via voice
- Enable specialist referral creation through voice commands
- Automate insurance pre-authorization checks
- Reduce average call handling time by 40%

## Target Users

1. **Patient** -- Checks lab results, requests referrals, verifies insurance via phone
2. **Front Desk Staff** -- Monitors voice session queue, handles escalations
3. **Clinical Coordinator** -- Reviews referrals and lab orders created by voice agent
4. **Provider** -- Views scheduled appointments and pending referrals
