param serverfarms_ASP_saramsa_858d_name string = 'ASP-saramsa-858d'

resource serverfarms_ASP_saramsa_858d_name_resource 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: serverfarms_ASP_saramsa_858d_name
  location: 'West US 2'
  sku: {
    name: 'B1'
    tier: 'Basic'
    size: 'B1'
    family: 'B'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    freeOfferExpirationTime: '2025-10-13T01:49:14.0766667'
    reserved: true
    isXenon: false
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
    asyncScalingEnabled: false
  }
}

output appServicePlanId string = serverfarms_ASP_saramsa_858d_name_resource.id
