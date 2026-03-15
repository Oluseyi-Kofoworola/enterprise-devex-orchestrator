// ===================================================================
// Azure AI Search Module
// Vector and semantic search for RAG patterns and knowledge retrieval.
// ===================================================================

@description('Azure region')
param location string

@description('AI Search service name')
param searchName string

@description('Managed Identity principal ID for RBAC')
param managedIdentityPrincipalId string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

@description('Tags for all resources')
param tags object

@description('AI Search SKU')
@allowed(['basic', 'standard', 'standard2'])
param searchSku string = 'basic'

// -- AI Search Service ----------------------------------------------
resource search 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: searchName
  location: location
  sku: {
    name: searchSku
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: 'free'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
  tags: tags
}

// -- RBAC: Search Index Data Contributor ----------------------------
resource searchDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, managedIdentityPrincipalId, 'Search Index Data Contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// -- RBAC: Search Service Contributor -------------------------------
resource searchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, managedIdentityPrincipalId, 'Search Service Contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7ca78c08-252a-4471-8644-bb5ff32d4ba0')
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// -- Diagnostic Settings --------------------------------------------
resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: search
  name: '${searchName}-diagnostics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'OperationLogs'
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

output searchEndpoint string = 'https://${search.name}.search.windows.net'
output searchName string = search.name
output searchId string = search.id
