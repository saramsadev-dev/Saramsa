param staticSites_saramsa_fe_name string = 'saramsa-fe'

resource staticSites_saramsa_fe_name_resource 'Microsoft.Web/staticSites@2024-11-01' = {
  name: staticSites_saramsa_fe_name
  location: 'West US 2'
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    repositoryUrl: 'https://github.com/sivakamyl/saramsa-final'
    branch: 'main'
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    provider: 'GitHub'
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

resource staticSites_saramsa_fe_name_default 'Microsoft.Web/staticSites/basicAuth@2024-11-01' = {
  parent: staticSites_saramsa_fe_name_resource
  name: 'default'
  location: 'West US 2'
  properties: {
    applicableEnvironmentsMode: 'SpecifiedEnvironments'
  }
}
