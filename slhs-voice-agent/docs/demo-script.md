# Demo Script -- SLHS Voice Agent v3.0

> **3-minute live demonstration** of the St. Luke's Health System Voice Agent
> Enterprise healthcare assistant with real-time voice interaction

---

## Pre-Demo Setup

1. Open browser (Chrome recommended for best voice support)
2. Navigate to: `https://devex-orchestrator-dev.greenbay-9ec52bc2.eastus2.azurecontainerapps.io`
3. Allow microphone access when prompted
4. Verify the HIPAA badge and "SLHS Voice Agent" header are visible

---

## Demo Flow (3 Minutes)

### Segment 1: Voice Interaction (45 seconds)

**Narration:** "This is the SLHS Voice Agent -- a production healthcare assistant
running on Azure Container Apps with enterprise security controls."

1. Click the **microphone button** (or press `Ctrl+M`)
2. Say: **"Hello, I need to look up a patient"**
3. Wait for the animated voice bars and response
4. Point out: "Notice the real-time voice transcription with interim results.
   The UI shows animated voice bars during listening, and the response appears
   as a rich formatted card."

### Segment 2: Patient Lookup (45 seconds)

**Narration:** "Let me demonstrate the patient record system with rich data cards."

1. Type or say: **"Look up patient Maria Garcia"**
2. Point out the **patient card** with:
   - Demographics (name, DOB, phone)
   - Conditions (Type 2 Diabetes, Hypertension)
   - Allergies (Penicillin)
   - Insurance (Blue Cross Blue Shield)
   - Next appointment date

3. Then say: **"Show me her medications"**
4. Point out the **medication card** showing:
   - Metformin 500mg (twice daily)
   - Lisinopril 10mg (once daily)

### Segment 3: Clinical Data (45 seconds)

**Narration:** "The agent provides clinical data access with contextual follow-up."

1. Say: **"What are her vitals?"**
2. Point out the **vitals card**:
   - Blood pressure: 128/82
   - Heart rate: 72
   - Temperature: 98.6F
   - SpO2: 98%

3. Say: **"Show lab results"**
4. Point out the **lab results card**:
   - HbA1c: 6.8% (borderline)
   - Lipid Panel: 195 mg/dL (normal)

**Key point:** "Notice how the agent maintains conversation context -- it
remembers we're talking about Maria Garcia across multiple turns."

### Segment 4: Enterprise Architecture (45 seconds)

**Narration:** "Let me show the enterprise architecture powering this."

1. Switch to the Azure Portal or show architecture slide
2. Highlight:
   - **Zero secrets in code** -- Managed Identity for all auth
   - **Key Vault** with RBAC, soft-delete, purge protection
   - **Container Registry** -- admin disabled, MI-based pull
   - **Log Analytics** -- structured JSON logging
   - **Non-root container** -- defense-in-depth
   - **486 automated tests** covering health, API, security, config, storage

3. Show health endpoint: `/health` returns version info
4. Mention: "Built with the Enterprise DevEx Orchestrator -- a 4-agent
   chain powered by GitHub Copilot SDK that transforms business intent
   into production-ready Azure workloads."

---

## Key Talking Points

| Feature | Enterprise Value |
|---------|----------------|
| Voice interaction | Hands-free clinical workflow, accessibility |
| Rich HTML cards | Structured data display, reducing errors |
| Multi-turn context | Natural conversation flow, efficiency |
| Auto-retry (voice) | Resilience against network failures |
| Managed Identity | Zero-trust security, no credential management |
| Container Apps | Serverless scaling, revision-based rollback |
| 486 tests | Quality assurance, regression prevention |
| WAF 5-pillar alignment | Enterprise governance compliance |

---

## Backup Plan

If voice is unavailable (corporate firewall blocks Google Speech API):
1. The app auto-retries 3 times with exponential backoff
2. A text input field is always visible below the voice button
3. All functionality works via text -- voice is an enhancement, not a dependency

If the live URL is down:
1. Run locally: `cd slhs-voice-agent/src/app && uvicorn main:app --port 8000`
2. Open `http://localhost:8000`

---

## Azure Portal Verification Points

| What to Show | Where |
|-------------|-------|
| Container App running | Portal > Container Apps > devex-orchestrator-dev |
| Active revision | Revisions blade > devex-orchestrator-dev--0000006 |
| Log Analytics | Logs blade > `ContainerAppConsoleLogs_CL` |
| Key Vault | devexorchestratordevkv > Access policies (RBAC) |
| Managed Identity | devex-orchestrator-dev-id > Role assignments |
| ACR | devexorchestratordevacr > Repositories > slhs-voice-agent |

---

## Sample KQL Query (Live Logs)

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "devex-orchestrator-dev"
| where Log_s contains "chat"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
| take 20
```

---

*SLHS Voice Agent Demo -- St. Luke's Health System*
*Enterprise DevEx Orchestrator | GitHub Copilot SDK Challenge*
