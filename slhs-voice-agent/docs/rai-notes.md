# Responsible AI Notes -- SLHS Voice Agent v3.0

> **Ethical AI considerations** for the St. Luke's Health System Voice Agent
> Aligned with standard Responsible AI principles

---

## AI System Classification

| Attribute | Value |
|-----------|-------|
| **System Type** | Rule-based conversational agent (no LLM in runtime) |
| **Domain** | Healthcare -- patient record lookup and appointment scheduling |
| **Risk Level** | Medium -- handles patient data references (demo data only) |
| **Decision Authority** | Assistive -- provides information, does not make clinical decisions |

> **Important:** The SLHS Voice Agent uses deterministic intent matching and
> pattern-based responses. It does NOT use a large language model at runtime.
> All responses are pre-defined and structured.

---

## Six Responsible AI Principles

### 1. Fairness

| Consideration | Implementation |
|--------------|---------------|
| Equitable access | Voice AND text input (voice is enhancement, not requirement) |
| Language bias | English-only in v3.0; support for additional languages documented as enhancement |
| Diverse patient data | Demo patients represent diverse demographics (Garcia, Wilson, Johnson, Thompson, Nguyen) |
| Disability access | Keyboard shortcut (Ctrl+M) for voice toggle, text input always available |

### 2. Reliability & Safety

| Consideration | Implementation |
|--------------|---------------|
| Deterministic responses | Rule-based intent matching -- no hallucination risk |
| Graceful degradation | Voice failure triggers auto-retry (3x with backoff), text fallback always works |
| Health probes | `/health` endpoint validates system operational status |
| Error handling | All API errors return safe, generic messages (no stack traces) |
| Clinical safety | Agent explicitly states it is NOT a substitute for medical advice |

### 3. Privacy & Security

| Consideration | Implementation |
|--------------|---------------|
| Data minimization | Demo data only -- no real patient information |
| PII in logs | No patient names, DOBs, or conditions written to logs |
| Session isolation | UUID-based sessions prevent cross-user data leakage |
| Voice data | Audio processed in browser via Web Speech API -- not sent to our servers |
| Encryption | TLS 1.2+ in transit, encryption at rest for Key Vault and ACR |
| Access control | Managed Identity with RBAC -- principle of least privilege |

### 4. Inclusiveness

| Consideration | Implementation |
|--------------|---------------|
| Multi-modal input | Voice chat for hands-free use + text input for accessibility |
| Visual feedback | Animated voice bars indicate active listening state |
| Rich data display | HTML cards with structured formatting for clear data presentation |
| Mobile-responsive | UI adapts to different screen sizes |
| Keyboard navigation | Full keyboard support including Ctrl+M shortcut |

### 5. Transparency

| Consideration | Implementation |
|--------------|---------------|
| System identification | Clearly identified as "SLHS Voice Agent" -- not a human |
| HIPAA badge | Visual indicator of compliance alignment in UI |
| Intent visibility | API responses include the detected `intent` classification |
| Open documentation | Full architecture, security, and governance documentation |
| Version reporting | `/health` endpoint reports current version number |

### 6. Accountability

| Consideration | Implementation |
|--------------|---------------|
| Audit trail | Structured JSON logging with session_id and intent tracking |
| Governance review | 25 automated governance checks before deployment |
| Threat modeling | STRIDE model with 6 categories and documented mitigations |
| Version control | Git-based deployment with full revision history |
| Rollback capability | Instant rollback via Container Apps revision management |

---

## Healthcare-Specific Considerations

### Clinical Decision Support Boundaries

This agent is an **information retrieval** system, not a clinical decision
support system (CDSS). It:

- **Does:** Look up patient records, display medications, show vitals, list appointments
- **Does NOT:** Suggest diagnoses, recommend treatments, interpret lab results, or provide medical advice
- **Clearly states:** Responses include text directing users to consult healthcare professionals

### HIPAA Alignment (Demo Context)

| HIPAA Safeguard | Implementation |
|----------------|---------------|
| Access Controls | RBAC via Managed Identity, session-based user isolation |
| Audit Controls | Structured logging to Log Analytics |
| Integrity Controls | Read-only patient data (demo), input validation |
| Transmission Security | TLS 1.2+ on all connections |

> **Note:** This is a demo system with synthetic patient data. Production HIPAA
> compliance requires additional controls: BAA with Azure, access auditing,
> breach notification procedures, and ePHI encryption at rest.

---

## Limitations and Known Constraints

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| English only | Non-English speakers cannot use voice | Text input works, language expansion planned |
| Demo data only | Not connected to real EHR systems | Clearly documented as demonstration |
| Browser-dependent voice | Chrome has best support, Firefox/Safari limited | Auto-retry + text fallback |
| Corporate firewall blocks voice | Google Speech API requires internet | 3x auto-retry + text input always available |
| No LLM reasoning | Cannot handle novel/complex queries | Deterministic responses are predictable and safe |
| Single-session context | Context lost on page refresh | Production path: Redis for persistent sessions |

---

## Continuous Improvement Plan

1. **Multi-language support** -- Add Spanish, Mandarin, and Vietnamese voice recognition
2. **WCAG 2.1 AA compliance** -- Full accessibility audit and remediation
3. **User feedback loop** -- In-app feedback mechanism for response quality
4. **Bias testing** -- Regular testing with diverse name patterns and accent recognition
5. **Clinical validation** -- Partner with clinical informaticists for response accuracy

---

*Responsible AI assessment performed as part of Enterprise DevEx Orchestrator governance*
*Aligned with enterprise Responsible AI baseline standards*


