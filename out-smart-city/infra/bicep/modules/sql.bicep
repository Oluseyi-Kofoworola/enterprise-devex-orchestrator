// ===================================================================
// Azure SQL Database Module
// Managed SQL database with managed identity access and diagnostics.
// ===================================================================

@description('Azure region')
param location string

@description('SQL Server name')
param serverName string

@description('Database name')
param databaseName string

@description('Managed Identity principal ID for admin access')
param managedIdentityPrincipalId string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

@description('Resource tags')
param tags object = {}

@description('Database SKU name')
param skuName string = 'GP_S_Gen5_1'

@description('Database SKU tier')
param skuTier string = 'GeneralPurpose'

@description('Entra ID admin object ID (deploying user or group)')
param entraAdminObjectId string

@description('Entra ID admin login name')
param entraAdminLogin string = 'entra-admin'

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: serverName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    administrators: {
      administratorType: 'ActiveDirectory'
      azureADOnlyAuthentication: true
      principalType: 'User'
      sid: entraAdminObjectId
      login: entraAdminLogin
      tenantId: subscription().tenantId
    }
  }
}

resource database 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 34359738368  // 32 GB
    zoneRedundant: false
  }
}

// Diagnostic settings for SQL Server
resource serverDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: sqlServer
  name: '${serverName}-diagnostics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'SQLSecurityAuditEvents'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// Diagnostic settings for database
resource dbDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: database
  name: '${databaseName}-diagnostics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'SQLInsights'
        enabled: true
      }
      {
        category: 'QueryStoreRuntimeStatistics'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'Basic'
        enabled: true
      }
    ]
  }
}

output serverName string = sqlServer.name
output serverFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseName string = database.name
output serverId string = sqlServer.id
