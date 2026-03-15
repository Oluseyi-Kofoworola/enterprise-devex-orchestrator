// ===================================================================
// Azure OpenAI Module
// Enterprise-grade LLM inference with content safety and RBAC access.
// ===================================================================

@description('Azure region')
param location string

@description('Azure OpenAI account name')
param openaiName string

@description('Managed Identity principal ID for RBAC')
param managedIdentityPrincipalId string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

@description('Tags for all resources')
param tags object

// -- Azure OpenAI Account ------------------------------------------
resource openai 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openaiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openaiName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
  tags: tags
}

// -- Chat Model Deployment ------------------------------------------
resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openai
  name: 'gpt-4o-mini'
  sku: {
    name: 'GlobalStandard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
  }
}

// -- Embeddings Model Deployment ------------------------------------
resource embeddingsDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openai
  name: 'text-embedding-ada-002'
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
  }
  dependsOn: [chatDeployment]
}

output embeddingsDeploymentName string = embeddingsDeployment.name

// -- RBAC: Cognitive Services OpenAI User ---------------------------
resource openaiRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: openai
  name: guid(openai.id, managedIdentityPrincipalId, 'Cognitive Services OpenAI User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// -- Diagnostic Settings --------------------------------------------
resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: openai
  name: '${openaiName}-diagnostics'
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'Audit'
        enabled: true
      }
      {
        category: 'RequestResponse'
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

output openaiEndpoint string = openai.properties.endpoint
output openaiName string = openai.name
output openaiId string = openai.id
output chatDeploymentName string = chatDeployment.name
