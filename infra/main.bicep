targetScope = 'resourceGroup'

// 1️⃣ App Service Plan (Linux)
module asp './asp.bicep' = {
  name: 'asp-module'
}

// 2️⃣ Managed Identity for Backend
module backendIdentity './saramsa-backend-id.bicep' = {
  name: 'backend-identity-module'
  dependsOn: [
    asp
  ]
}

// 3️⃣ Backend App Service (Python)
module backend './saramsa-backend.bicep' = {
  name: 'backend-module'
  params: {
    serverfarms_ASP_saramsa_858d_externalid: asp.outputs.appServicePlanId
  }
  dependsOn: [
    backendIdentity
  ]
}

// 4️⃣ Cosmos DB (Database + Containers)
module cosmos './saramsa-cosmosdb.bicep' = {
  name: 'cosmos-module'
  dependsOn: [
    backend
  ]
}

// 5️⃣ Frontend Static Web App (React / Next.js)
module frontend './saramsa-fe.bicep' = {
  name: 'frontend-module'
  dependsOn: [
    cosmos
  ]
}

