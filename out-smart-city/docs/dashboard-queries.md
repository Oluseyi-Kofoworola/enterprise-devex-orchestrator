# Dashboard KQL Queries -- smart-city-ai-operations-platform-extre

> Compute target: **Container Apps** | Copy these into **Log Analytics > Logs** for ad-hoc analysis.

## Request Throughput (5-minute bins)

```kql
ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | summarize RequestCount=count() by bin(TimeGenerated, 5m) | render timechart
```

## Response Latency Percentiles

```kql
ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | extend duration_ms = todouble(extract("duration_ms=([\\\\d.]+)", 1, Log_s)) | summarize p50=percentile(duration_ms, 50), p95=percentile(duration_ms, 95), p99=percentile(duration_ms, 99) by bin(TimeGenerated, 5m) | render timechart
```

## Error Rate (24h)

```kql
ContainerAppConsoleLogs_CL | where TimeGenerated > ago(24h) | extend statusCode = toint(extract("status_code=([\\\\d]+)", 1, Log_s)) | summarize Total=count(), Errors=countif(statusCode >= 400) by bin(TimeGenerated, 15m) | extend ErrorRate = round(100.0 * Errors / Total, 2) | render timechart
```

## Active Replicas

```kql
ContainerAppSystemLogs_CL | where TimeGenerated > ago(1h) | where RevisionName_s != "" | summarize ReplicaCount=dcount(ContainerName_s) by bin(TimeGenerated, 5m) | render timechart
```

## Cosmos DB Operations

```kql
CDBDataPlaneRequests
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```

## Storage Blob Operations

```kql
StorageBlobLogs
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```

## SQL Database Operations

```kql
AzureDiagnostics | where ResourceProvider == 'MICROSOFT.SQL'
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```

## Redis Cache Operations

```kql
AzureDiagnostics | where ResourceProvider == 'MICROSOFT.CACHE'
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```

## AI Search Operations

```kql
AzureDiagnostics | where ResourceProvider == 'MICROSOFT.SEARCH'
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```

## Storage Table Operations

```kql
StorageTableLogs
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```
