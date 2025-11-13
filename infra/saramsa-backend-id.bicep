param userAssignedIdentities_saramsa_backend_id_84e6_name string = 'saramsa-backend-id-84e6'

resource userAssignedIdentities_saramsa_backend_id_84e6_name_resource 'Microsoft.ManagedIdentity/userAssignedIdentities@2025-01-31-preview' = {
  name: userAssignedIdentities_saramsa_backend_id_84e6_name
  location: 'westus2'
}

resource userAssignedIdentities_saramsa_backend_id_84e6_name_duqsyk5gl2kq6 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2025-01-31-preview' = {
  parent: userAssignedIdentities_saramsa_backend_id_84e6_name_resource
  name: 'duqsyk5gl2kq6'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:sivakamyl/saramsa-final:ref:refs/heads/main'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}
