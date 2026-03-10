# Alerting Runbook -- SLHS Voice Agent v3.0

> **Azure Monitor Alert Rules** with severity levels, thresholds, and response procedures
> Live: `https://<container-app-fqdn>`

---

## Alert Overview

| # | Alert | Severity | Threshold | Window |
|---|-------|----------|-----------|--------|
| 1 | High CPU Utilization | Sev2 - Warning | CPU > 80% | 5 min |
| 2 | High Memory Utilization | Sev2 - Warning | Memory > 80% | 5 min |
| 3 | Container Restart Loop | Sev1 - Error | Restarts > 3 | 15 min |
| 4 | HTTP 5xx Spike | Sev1 - Error | 5xx > 10 | 5 min |
| 5 | High Response Latency | Sev2 - Warning | p95 > 2000ms | 5 min |
| 6 | Low Request Rate | Sev3 - Info | Requests < 1/min | 15 min |
| 7 | Container App Unhealthy | Sev0 - Critical | Health probe fails > 3 | 5 min |

---

## Alert Rule 1: High CPU Utilization

**Signal:** `CpuPercentage` metric on `devex-orchestrator-dev`
**Condition:** Average CPU > 80% over 5 minutes
**Severity:** Sev2 (Warning)

### Diagnosis

```bash
# Check current CPU
az monitor metrics list \
  --resource /subscriptions/<AZURE_SUBSCRIPTION_ID>/resourceGroups/rg-enterprise-devex-orchestrator-dev/providers/Microsoft.App/containerApps/devex-orchestrator-dev \
  --metric CpuPercentage \
  --interval PT1M

# Check replica count
az containerapp revision list \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --query "[0].properties.replicas"
```

### Response

1. **Check active sessions** -- Voice sessions hold memory; high concurrent usage spikes CPU
2. **Scale out** -- Increase max replicas in Bicep `maxReplicas` parameter
3. **Profile** -- Check if patient lookup or voice processing is the bottleneck
4. **Long-term** -- Consider async processing for heavy operations

---

## Alert Rule 2: High Memory Utilization

**Signal:** `MemoryPercentage` metric
**Condition:** Average Memory > 80% over 5 minutes
**Severity:** Sev2 (Warning)

### Diagnosis

```bash
# Check memory usage
az monitor metrics list \
  --resource /subscriptions/<AZURE_SUBSCRIPTION_ID>/resourceGroups/rg-enterprise-devex-orchestrator-dev/providers/Microsoft.App/containerApps/devex-orchestrator-dev \
  --metric MemoryPercentage \
  --interval PT1M
```

### Response

1. **Check session store** -- In-memory `session_store` dict grows with active sessions
2. **Session cleanup** -- Sessions auto-expire but concurrent load may cause buildup
3. **Restart** -- Deploy new revision to clear memory if critical
4. **Long-term** -- Consider Redis for session storage if persistent memory pressure

---

## Alert Rule 3: Container Restart Loop

**Signal:** `RestartCount` metric
**Condition:** Restarts > 3 in 15 minutes
**Severity:** Sev1 (Error)

### Diagnosis

```bash
# Check container logs
az containerapp logs show \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --type system

# Check revision status
az containerapp revision list \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --query "[].{name:name, status:properties.healthState, replicas:properties.replicas}"
```

### Response

1. **Check logs** -- Look for OOM kills, startup crashes, or import errors
2. **Image integrity** -- Verify the image tag in ACR: `devexorchestratordevacr.azurecr.io/devex-orchestrator:v3.0.1`
3. **Health probe** -- Ensure `/health` returns 200 within the startup grace period
4. **Rollback** -- If new deployment caused CrashLoopBackOff:

```bash
az containerapp revision list \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --query "[].name" -o tsv

az containerapp ingress traffic set \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --revision-weight <previous-revision>=100
```

---

## Alert Rule 4: HTTP 5xx Spike

**Signal:** `Requests` metric filtered by `statusCodeCategory=5xx`
**Condition:** Count > 10 in 5 minutes
**Severity:** Sev1 (Error)

### Diagnosis

```kql
// KQL in Log Analytics (devex-orchestrator-dev-law)
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "devex-orchestrator-dev"
| where Log_s contains "ERROR" or Log_s contains "500"
| order by TimeGenerated desc
| take 50
```

### Response

1. **Check error patterns** -- Identify which endpoints are failing (`/chat`, `/health`, `/`)
2. **Validate input** -- Pydantic validation may reject malformed requests (expected 422, not 500)
3. **Key Vault** -- If secrets are unavailable, the app degrades gracefully but some features may fail
4. **Deploy fix** -- Build and deploy patched image:

```bash
az acr build --registry devexorchestratordevacr --image devex-orchestrator:v3.0.2 --no-logs slhs-voice-agent/src/app/
```

---

## Alert Rule 5: High Response Latency

**Signal:** `ResponseLatency` metric (p95)
**Condition:** p95 > 2000ms over 5 minutes
**Severity:** Sev2 (Warning)

### Diagnosis

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "devex-orchestrator-dev"
| where Log_s contains "duration"
| parse Log_s with * "duration=" duration:double *
| summarize p50=percentile(duration, 50), p95=percentile(duration, 95), p99=percentile(duration, 99) by bin(TimeGenerated, 5m)
```

### Response

1. **Identify slow endpoints** -- `/chat` with voice processing is expected to be slower than `/health`
2. **Check intent routing** -- Complex intents (medications, labs, vitals) require more processing
3. **Session lookup** -- Large session histories increase response time
4. **Scale** -- Add replicas if load is the cause

---

## Alert Rule 6: Low Request Rate

**Signal:** `Requests` metric (total)
**Condition:** Total < 1 per minute over 15 minutes
**Severity:** Sev3 (Info)

### Response

1. **Verify app is running** -- Hit health endpoint: `curl https://<container-app-fqdn>/health`
2. **Check scale-to-zero** -- Container Apps may scale to 0 replicas; first request has cold start
3. **DNS/networking** -- Verify the FQDN resolves correctly
4. **Expected** -- Low traffic in dev is normal; suppress this alert in non-prod if desired

---

## Alert Rule 7: Container App Unhealthy

**Signal:** Health probe failure on `/health` endpoint
**Condition:** 3 consecutive failures
**Severity:** Sev0 (Critical)

### Diagnosis

```bash
# Test health endpoint
curl -s -o /dev/null -w "%{http_code}" https://<container-app-fqdn>/health

# Check running revisions
az containerapp revision list \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --query "[].{name:name, active:properties.active, healthy:properties.healthState}"
```

### Response

1. **IMMEDIATE** -- Check if the container is running
2. **Logs** -- Pull system + console logs to identify crash reason
3. **Rollback** -- Switch traffic to last known good revision (see Rule 3 rollback)
4. **Escalate** -- If all revisions are unhealthy, redeploy from ACR:

```bash
az containerapp update \
  --name devex-orchestrator-dev \
  --resource-group rg-enterprise-devex-orchestrator-dev \
  --image devexorchestratordevacr.azurecr.io/devex-orchestrator:v3.0.1
```

---

## Escalation Matrix

| Severity | Response Time | Notification | Escalation |
|----------|--------------|-------------|-----------|
| Sev0 (Critical) | Immediate | PagerDuty + Email + Teams | On-call engineer immediately |
| Sev1 (Error) | 15 minutes | Email + Teams | Engineering lead within 30 min |
| Sev2 (Warning) | 1 hour | Email | Review in next standup |
| Sev3 (Info) | Next business day | Dashboard | No escalation |

## Action Group Configuration

```bicep
// Alert action group (in infra/modules/action-group.bicep)
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${projectName}-alerts-ag'
  location: 'global'
  properties: {
    groupShortName: 'DevExAlerts'
    enabled: true
    emailReceivers: [
      {
        name: 'platform-team'
        emailAddress: 'platform-alerts@contoso.com'
      }
    ]
  }
}
```

---

*Azure Monitor Alerting | 7 Rules | 4 Severity Levels*
*All alerts reference actual deployed resources in `rg-enterprise-devex-orchestrator-dev`*


