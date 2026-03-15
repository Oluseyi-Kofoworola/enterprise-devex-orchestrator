"""Dashboard Generator -- produces Azure Monitor dashboard Bicep module.

Generates an Azure Portal dashboard with KQL-powered tiles for:
    - Request count / throughput
    - P50 / P95 / P99 response latency
    - Error rate (4xx + 5xx)
    - Compute-specific replica/instance monitoring
    - Data store operations (per configured store)

Adapts KQL queries to the actual compute target and data stores
specified in the IntentSpec. Only produced when
``spec.observability.dashboard`` is ``True``.
"""

from __future__ import annotations

from src.orchestrator.intent_schema import ComputeTarget, DataStore, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)

# -- Compute-target-aware log tables and KQL patterns ------------------

_LOG_TABLES = {
    ComputeTarget.CONTAINER_APPS: {
        "app_log": "ContainerAppConsoleLogs_CL",
        "sys_log": "ContainerAppSystemLogs_CL",
        "request_kql": "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | summarize RequestCount=count() by bin(TimeGenerated, 5m) | render timechart",
        "latency_kql": 'ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h) | extend duration_ms = todouble(extract("duration_ms=([\\\\\\\\d.]+)", 1, Log_s)) | summarize p50=percentile(duration_ms, 50), p95=percentile(duration_ms, 95), p99=percentile(duration_ms, 99) by bin(TimeGenerated, 5m) | render timechart',
        "error_kql": 'ContainerAppConsoleLogs_CL | where TimeGenerated > ago(24h) | extend statusCode = toint(extract("status_code=([\\\\\\\\d]+)", 1, Log_s)) | summarize Total=count(), Errors=countif(statusCode >= 400) by bin(TimeGenerated, 15m) | extend ErrorRate = round(100.0 * Errors / Total, 2) | render timechart',
        "scale_kql": 'ContainerAppSystemLogs_CL | where TimeGenerated > ago(1h) | where RevisionName_s != "" | summarize ReplicaCount=dcount(ContainerName_s) by bin(TimeGenerated, 5m) | render timechart',
        "scale_title": "Active Replicas",
    },
    ComputeTarget.APP_SERVICE: {
        "app_log": "AppServiceHTTPLogs",
        "sys_log": "AppServiceConsoleLogs",
        "request_kql": "AppServiceHTTPLogs | where TimeGenerated > ago(1h) | summarize RequestCount=count() by bin(TimeGenerated, 5m) | render timechart",
        "latency_kql": "AppServiceHTTPLogs | where TimeGenerated > ago(1h) | summarize p50=percentile(TimeTaken, 50), p95=percentile(TimeTaken, 95), p99=percentile(TimeTaken, 99) by bin(TimeGenerated, 5m) | render timechart",
        "error_kql": "AppServiceHTTPLogs | where TimeGenerated > ago(24h) | summarize Total=count(), Errors=countif(ScStatus >= 400) by bin(TimeGenerated, 15m) | extend ErrorRate = round(100.0 * Errors / Total, 2) | render timechart",
        "scale_kql": "AppServiceHTTPLogs | where TimeGenerated > ago(1h) | summarize ActiveInstances=dcount(CsHost) by bin(TimeGenerated, 5m) | render timechart",
        "scale_title": "Active Instances",
    },
    ComputeTarget.FUNCTIONS: {
        "app_log": "FunctionAppLogs",
        "sys_log": "FunctionAppLogs",
        "request_kql": "FunctionAppLogs | where TimeGenerated > ago(1h) | where Category == 'Function.Host.Results' | summarize Invocations=count() by bin(TimeGenerated, 5m) | render timechart",
        "latency_kql": "FunctionAppLogs | where TimeGenerated > ago(1h) | where Category == 'Function.Host.Results' | extend duration_ms = DurationMs | summarize p50=percentile(duration_ms, 50), p95=percentile(duration_ms, 95), p99=percentile(duration_ms, 99) by bin(TimeGenerated, 5m) | render timechart",
        "error_kql": "FunctionAppLogs | where TimeGenerated > ago(24h) | where Category == 'Function.Host.Results' | summarize Total=count(), Errors=countif(Level == 'Error') by bin(TimeGenerated, 15m) | extend ErrorRate = round(100.0 * Errors / Total, 2) | render timechart",
        "scale_kql": "FunctionAppLogs | where TimeGenerated > ago(1h) | summarize ActiveWorkers=dcount(HostInstanceId) by bin(TimeGenerated, 5m) | render timechart",
        "scale_title": "Active Workers",
    },
}

# Data store KQL patterns
_DATA_STORE_TILES = {
    DataStore.BLOB_STORAGE: ("StorageBlobLogs", "Storage Blob Operations", "OperationName"),
    DataStore.TABLE_STORAGE: ("StorageTableLogs", "Storage Table Operations", "OperationName"),
    DataStore.COSMOS_DB: ("CDBDataPlaneRequests", "Cosmos DB Operations", "OperationName"),
    DataStore.SQL: ("AzureDiagnostics | where ResourceProvider == 'MICROSOFT.SQL'", "SQL Database Operations", "OperationName"),
    DataStore.REDIS: ("AzureDiagnostics | where ResourceProvider == 'MICROSOFT.CACHE'", "Redis Cache Operations", "OperationName"),
    DataStore.AI_SEARCH: ("AzureDiagnostics | where ResourceProvider == 'MICROSOFT.SEARCH'", "AI Search Operations", "OperationName"),
}


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
        """Bicep module for an Azure Portal shared dashboard -- compute-target aware."""

        ct = spec.compute_target
        log_cfg = _LOG_TABLES.get(ct, _LOG_TABLES[ComputeTarget.CONTAINER_APPS])
        scale_title = log_cfg["scale_title"]

        # Build data store tiles dynamically
        data_store_tiles = ""
        tile_y = 8
        for ds in spec.data_stores:
            entry = _DATA_STORE_TILES.get(ds)
            if entry:
                tbl, title, col = entry
                data_store_tiles += f"""
        {{
          position: {{ x: 6, y: {tile_y}, colSpan: 6, rowSpan: 4 }}
          metadata: {{
            type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
            inputs: [
              {{ name: 'resourceTypeMode', value: 'workspace' }}
              {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
              {{ name: 'Query', value: '{tbl} | where TimeGenerated > ago(24h) | summarize Operations=count() by {col} | top 10 by Operations' }}
              {{ name: 'TimeRange', value: 'P1D' }}
              {{ name: 'PartTitle', value: '{title} (24h)' }}
            ]
          }}
        }}"""
                tile_y += 4

        return f"""// ===================================================================
// Azure Monitor Dashboard Module
// Auto-generated observability dashboard with KQL tiles.
// Compute target: {ct.value}
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
                {{ name: 'Query', value: '{log_cfg["request_kql"]}' }}
                {{ name: 'TimeRange', value: 'PT1H' }}
                {{ name: 'PartTitle', value: 'Request Throughput (5m bins)' }}
              ]
            }}
          }}
          // -- Latency percentiles tile --
          {{
            position: {{ x: 6, y: 0, colSpan: 6, rowSpan: 4 }}
            metadata: {{
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              inputs: [
                {{ name: 'resourceTypeMode', value: 'workspace' }}
                {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
                {{ name: 'Query', value: '{log_cfg["latency_kql"]}' }}
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
                {{ name: 'Query', value: '{log_cfg["error_kql"]}' }}
                {{ name: 'TimeRange', value: 'P1D' }}
                {{ name: 'PartTitle', value: 'Error Rate % (24h)' }}
              ]
            }}
          }}
          // -- Scale / instance monitoring tile --
          {{
            position: {{ x: 6, y: 4, colSpan: 6, rowSpan: 4 }}
            metadata: {{
              type: 'Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart'
              inputs: [
                {{ name: 'resourceTypeMode', value: 'workspace' }}
                {{ name: 'ComponentId', value: logAnalyticsWorkspaceId }}
                {{ name: 'Query', value: '{log_cfg["scale_kql"]}' }}
                {{ name: 'TimeRange', value: 'PT1H' }}
                {{ name: 'PartTitle', value: '{scale_title}' }}
              ]
            }}
          }}{data_store_tiles}
        ]
      }}
    ]
  }}
}}

output dashboardId string = dashboard.id
output dashboardName string = dashboard.name
"""

    def _kql_doc(self, spec: IntentSpec) -> str:
        """Markdown document with standalone KQL queries -- compute-target aware."""
        ct = spec.compute_target
        log_cfg = _LOG_TABLES.get(ct, _LOG_TABLES[ComputeTarget.CONTAINER_APPS])
        app_log = log_cfg["app_log"]
        compute_label = ct.value.replace("_", " ").title()

        # Build data store query sections dynamically
        ds_sections = ""
        for ds in spec.data_stores:
            entry = _DATA_STORE_TILES.get(ds)
            if entry:
                tbl, title, col = entry
                ds_sections += f"""
## {title}

```kql
{tbl}
| where TimeGenerated > ago(24h)
| summarize Operations=count() by {col}
| top 10 by Operations
```
"""

        return f"""# Dashboard KQL Queries -- {spec.project_name}

> Compute target: **{compute_label}** | Copy these into **Log Analytics > Logs** for ad-hoc analysis.

## Request Throughput (5-minute bins)

```kql
{log_cfg['request_kql']}
```

## Response Latency Percentiles

```kql
{log_cfg['latency_kql']}
```

## Error Rate (24h)

```kql
{log_cfg['error_kql']}
```

## {log_cfg['scale_title']}

```kql
{log_cfg['scale_kql']}
```
{ds_sections}"""
