"""Dashboard Generator -- produces Azure Monitor dashboard Bicep module.

Generates an Azure Portal dashboard with KQL-powered tiles for:
    - Request count / throughput
    - P50 / P95 / P99 response latency
    - Error rate (4xx + 5xx)
    - Container App replica count
    - Key Vault operations

Only produced when ``spec.observability.dashboard`` is ``True``.
"""

from __future__ import annotations

from src.orchestrator.intent_schema import DataStore, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class DashboardGenerator:
    """Generates Azure Monitor dashboard Bicep module and KQL queries."""

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        """Return file-path -> content mapping for dashboard artifacts.

        If ``spec.observability.dashboard`` is ``False`` (the default),
        an empty dict is returned so nothing is emitted.
        """
        if not spec.observability.dashboard:
            logger.info("dashboard_generator.skipped", reason="dashboard not requested")
            return {}

        logger.info("dashboard_generator.start", project=spec.project_name)

        files: dict[str, str] = {}
        files["infra/bicep/modules/dashboard.bicep"] = self._dashboard_module(spec)
        files["docs/dashboard-queries.md"] = self._kql_doc(spec)

        logger.info("dashboard_generator.complete", file_count=len(files))
        return files

    # ------------------------------------------------------------------

    def _dashboard_module(self, spec: IntentSpec) -> str:
        """Bicep module for an Azure Portal shared dashboard."""

        storage_tile = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_tile = """
        {
          position: { x: 6, y: 6, colSpan: 6, rowSpan: 4 }
          metadata: {
            type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
            inputs: [
              { name: 'resourceTypeMode', value: 'workspace' }
              { name: 'ComponentId', value: logAnalyticsWorkspaceId }
              { name: 'Query', value: 'StorageBlobLogs | where TimeGenerated > ago(24h) | summarize Operations=count() by OperationName | top 10 by Operations' }
              { name: 'TimeRange', value: 'P1D' }
              { name: 'PartTitle', value: 'Storage Blob Operations (24h)' }
            ]
          }
        }"""

        return f"""// ===================================================================
// Azure Monitor Dashboard Module
// Auto-generated observability dashboard with KQL tiles.
// Project: {spec.project_name}
// ===================================================================

@description('Azure region')
param location string

@description('Dashboard display name')
param dashboardName string

@description('Log Analytics workspace resource ID')
param logAnalyticsWorkspaceId string

@description('Resource tags')
param tags object = {{}}

resource dashboard 'Microsoft.Portal/dashboards@2020-09-01-preview' = {{
  name: dashboardName
  location: location
  tags: tags
  properties: {{
    lenses: [
      {{
        order: 0
        parts: [
          // -- Request throughput tile --
          {{
            position: {{ x: 0, y: 0, colSpan: 6, rowSpan: 4 }}
            metadata: {{
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              inputs: [
                {{ name: 'resourceTypeMode', value: 'workspace' }}
                {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
                {{ name: 'Query', value: 'ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | summarize RequestCount=count() by bin(TimeGenerated, 5m) | render timechart' }}
                {{ name: 'TimeRange', value: 'PT1H' }}
                {{ name: 'PartTitle', value: 'Request Throughput (5m bins)' }}
              ]
            }}
          }}
          // -- P95 latency tile --
          {{
            position: {{ x: 6, y: 0, colSpan: 6, rowSpan: 4 }}
            metadata: {{
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              inputs: [
                {{ name: 'resourceTypeMode', value: 'workspace' }}
                {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
                {{ name: 'Query', value: 'ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | extend duration_ms = todouble(extract("duration_ms=([\\\\d.]+)", 1, Log_s)) | summarize p50=percentile(duration_ms, 50), p95=percentile(duration_ms, 95), p99=percentile(duration_ms, 99) by bin(TimeGenerated, 5m) | render timechart' }}
                {{ name: 'TimeRange', value: 'PT1H' }}
                {{ name: 'PartTitle', value: 'Response Latency Percentiles' }}
              ]
            }}
          }}
          // -- Error rate tile --
          {{
            position: {{ x: 0, y: 4, colSpan: 6, rowSpan: 4 }}
            metadata: {{
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              inputs: [
                {{ name: 'resourceTypeMode', value: 'workspace' }}
                {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
                {{ name: 'Query', value: 'ContainerAppConsoleLogs_CL | where TimeGenerated > ago(24h) | extend statusCode = toint(extract("status_code=([\\\\d]+)", 1, Log_s)) | summarize Total=count(), Errors=countif(statusCode >= 400) by bin(TimeGenerated, 15m) | extend ErrorRate = round(100.0 * Errors / Total, 2) | render timechart' }}
                {{ name: 'TimeRange', value: 'P1D' }}
                {{ name: 'PartTitle', value: 'Error Rate % (24h)' }}
              ]
            }}
          }}
          // -- Container replica count tile --
          {{
            position: {{ x: 6, y: 4, colSpan: 6, rowSpan: 4 }}
            metadata: {{
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              inputs: [
                {{ name: 'resourceTypeMode', value: 'workspace' }}
                {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
                {{ name: 'Query', value: 'ContainerAppSystemLogs_CL | where TimeGenerated > ago(1h) | where RevisionName_s != "" | summarize ReplicaCount=dcount(ContainerName_s) by bin(TimeGenerated, 5m) | render timechart' }}
                {{ name: 'TimeRange', value: 'PT1H' }}
                {{ name: 'PartTitle', value: 'Active Replicas' }}
              ]
            }}
          }}{storage_tile}
        ]
      }}
    ]
  }}
}}

output dashboardId string = dashboard.id
output dashboardName string = dashboard.name
"""

    def _kql_doc(self, spec: IntentSpec) -> str:
        """Markdown document with standalone KQL queries for ad-hoc use."""
        storage_section = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_section = """
## Storage Blob Operations

```kql
StorageBlobLogs
| where TimeGenerated > ago(24h)
| summarize Operations=count() by OperationName
| top 10 by Operations
```
"""

        return f"""# Dashboard KQL Queries -- {spec.project_name}

> Copy these into **Log Analytics > Logs** for ad-hoc analysis.

## Request Throughput (5-minute bins)

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| summarize RequestCount=count() by bin(TimeGenerated, 5m)
| render timechart
```

## Response Latency Percentiles

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| extend duration_ms = todouble(extract("duration_ms=([\\\\d.]+)", 1, Log_s))
| summarize
    p50=percentile(duration_ms, 50),
    p95=percentile(duration_ms, 95),
    p99=percentile(duration_ms, 99)
  by bin(TimeGenerated, 5m)
| render timechart
```

## Error Rate (24h)

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| extend statusCode = toint(extract("status_code=([\\\\d]+)", 1, Log_s))
| summarize Total=count(), Errors=countif(statusCode >= 400) by bin(TimeGenerated, 15m)
| extend ErrorRate = round(100.0 * Errors / Total, 2)
| render timechart
```

## Active Container Replicas

```kql
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(1h)
| where RevisionName_s != ""
| summarize ReplicaCount=dcount(ContainerName_s) by bin(TimeGenerated, 5m)
| render timechart
```
{storage_section}"""
