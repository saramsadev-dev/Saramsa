param databaseAccounts_saramsa_cosmosdb_name string = 'saramsa-cosmosdb'

resource databaseAccounts_saramsa_cosmosdb_name_resource 'Microsoft.DocumentDB/databaseAccounts@2025-05-01-preview' = {
  name: databaseAccounts_saramsa_cosmosdb_name
  location: 'West US 2'
  tags: {
    defaultExperience: 'Core (SQL)'
    'hidden-workload-type': 'Development/Testing'
    'hidden-cosmos-mmspecial': ''
  }
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'None'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    enableAutomaticFailover: true
    enableMultipleWriteLocations: false
    isVirtualNetworkFilterEnabled: false
    virtualNetworkRules: []
    disableKeyBasedMetadataWriteAccess: false
    enableFreeTier: false
    enableAnalyticalStorage: false
    analyticalStorageConfiguration: {
      schemaType: 'WellDefined'
    }
    databaseAccountOfferType: 'Standard'
    enableMaterializedViews: false
    capacityMode: 'Serverless'
    defaultIdentity: 'FirstPartyIdentity'
    networkAclBypass: 'None'
    disableLocalAuth: false
    enablePartitionMerge: false
    enablePerRegionPerPartitionAutoscale: false
    enableBurstCapacity: false
    enablePriorityBasedExecution: false
    defaultPriorityLevel: 'High'
    minimalTlsVersion: 'Tls12'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxIntervalInSeconds: 5
      maxStalenessPrefix: 100
    }
    locations: [
      {
        locationName: 'West US 2'
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    cors: []
    capabilities: []
    ipRules: []
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Geo'
      }
    }
    networkAclBypassResourceIds: []
    diagnosticLogSettings: {
      enableFullTextQuery: 'None'
    }
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000003 'Microsoft.DocumentDB/databaseAccounts/cassandraRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000003'
  properties: {
    roleName: 'Cosmos DB Cassandra Built-in Data Reader'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/read'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/containers/executeQuery'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/containers/readChangeFeed'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/containers/entities/read'
        ]
        notDataActions: []
      }
    ]
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000004 'Microsoft.DocumentDB/databaseAccounts/cassandraRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000004'
  properties: {
    roleName: 'Cosmos DB Cassandra Built-in Data Contributor'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/read'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/write'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/*'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/write'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/delete'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/cassandra/containers/entities/*'
        ]
        notDataActions: []
      }
    ]
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_Portal_users_1758905476 'Microsoft.DocumentDB/databaseAccounts/copyJobs@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: 'Portal_users_1758905476'
  properties: {
    mode: 'Offline'
    jobProperties: {
      sourceDetails: {}
      destinationDetails: {}
      tasks: [
        {
          source: {
            databaseName: 'saramsa-cpsmosdb'
            containerName: 'projects'
          }
          destination: {
            databaseName: 'saramsa-cpsmosdb'
            containerName: 'users'
          }
        }
      ]
      jobType: 'NoSqlRUToNoSqlRU'
    }
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_Portal_users_1759571197 'Microsoft.DocumentDB/databaseAccounts/copyJobs@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: 'Portal_users_1759571197'
  properties: {
    mode: 'Offline'
    jobProperties: {
      sourceDetails: {}
      destinationDetails: {}
      tasks: [
        {
          source: {
            databaseName: 'saramsa-cpsmosdb'
            containerName: 'user-stories'
          }
          destination: {
            databaseName: 'saramsa-cpsmosdb'
            containerName: 'users'
          }
        }
      ]
      jobType: 'NoSqlRUToNoSqlRU'
    }
  }
}

resource Microsoft_DocumentDB_databaseAccounts_dataTransferJobs_databaseAccounts_saramsa_cosmosdb_name_Portal_users_1758905476 'Microsoft.DocumentDB/databaseAccounts/dataTransferJobs@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: 'Portal_users_1758905476'
  properties: {
    mode: 'Offline'
    source: {
      databaseName: 'saramsa-cpsmosdb'
      containerName: 'projects'
      component: 'CosmosDBSql'
    }
    destination: {
      databaseName: 'saramsa-cpsmosdb'
      containerName: 'users'
      component: 'CosmosDBSql'
    }
  }
}

resource Microsoft_DocumentDB_databaseAccounts_dataTransferJobs_databaseAccounts_saramsa_cosmosdb_name_Portal_users_1759571197 'Microsoft.DocumentDB/databaseAccounts/dataTransferJobs@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: 'Portal_users_1759571197'
  properties: {
    mode: 'Offline'
    source: {
      databaseName: 'saramsa-cpsmosdb'
      containerName: 'user-stories'
      component: 'CosmosDBSql'
    }
    destination: {
      databaseName: 'saramsa-cpsmosdb'
      containerName: 'users'
      component: 'CosmosDBSql'
    }
  }
}

resource Microsoft_DocumentDB_databaseAccounts_gremlinRoleDefinitions_databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000003 'Microsoft.DocumentDB/databaseAccounts/gremlinRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000003'
  properties: {
    roleName: 'Cosmos DB Gremlin Built-in Data Reader'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/read'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/containers/executeQuery'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/containers/readChangeFeed'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/containers/entities/read'
        ]
        notDataActions: []
      }
    ]
  }
}

resource Microsoft_DocumentDB_databaseAccounts_gremlinRoleDefinitions_databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000004 'Microsoft.DocumentDB/databaseAccounts/gremlinRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000004'
  properties: {
    roleName: 'Cosmos DB Gremlin Built-in Data Contributor'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/read'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/write'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/*'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/write'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/delete'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/gremlin/containers/entities/*'
        ]
        notDataActions: []
      }
    ]
  }
}

resource Microsoft_DocumentDB_databaseAccounts_mongoMIRoleDefinitions_databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000003 'Microsoft.DocumentDB/databaseAccounts/mongoMIRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000003'
  properties: {
    roleName: 'Cosmos DB Mongo Built-in Data Reader'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/read'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/containers/executeQuery'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/containers/readChangeFeed'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/containers/entities/read'
        ]
        notDataActions: []
      }
    ]
  }
}

resource Microsoft_DocumentDB_databaseAccounts_mongoMIRoleDefinitions_databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000004 'Microsoft.DocumentDB/databaseAccounts/mongoMIRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000004'
  properties: {
    roleName: 'Cosmos DB Mongo Built-in Data Contributor'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/read'
          'Microsoft.DocumentDB/databaseAccounts/throughputSettings/write'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/*'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/write'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/delete'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/mongoMI/containers/entities/*'
        ]
        notDataActions: []
      }
    ]
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: 'saramsa-cpsmosdb'
  properties: {
    resource: {
      id: 'saramsa-cpsmosdb'
    }
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000001 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000001'
  properties: {
    roleName: 'Cosmos DB Built-in Data Reader'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/executeQuery'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/readChangeFeed'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read'
        ]
        notDataActions: []
      }
    ]
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000002 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000002'
  properties: {
    roleName: 'Cosmos DB Built-in Data Contributor'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
        ]
        notDataActions: []
      }
    ]
  }
}

resource Microsoft_DocumentDB_databaseAccounts_tableRoleDefinitions_databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000001 'Microsoft.DocumentDB/databaseAccounts/tableRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000001'
  properties: {
    roleName: 'Cosmos DB Built-in Data Reader'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/tables/containers/executeQuery'
          'Microsoft.DocumentDB/databaseAccounts/tables/containers/readChangeFeed'
          'Microsoft.DocumentDB/databaseAccounts/tables/containers/entities/read'
        ]
        notDataActions: []
      }
    ]
  }
}

resource Microsoft_DocumentDB_databaseAccounts_tableRoleDefinitions_databaseAccounts_saramsa_cosmosdb_name_00000000_0000_0000_0000_000000000002 'Microsoft.DocumentDB/databaseAccounts/tableRoleDefinitions@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_resource
  name: '00000000-0000-0000-0000-000000000002'
  properties: {
    roleName: 'Cosmos DB Built-in Data Contributor'
    type: 'BuiltInRole'
    assignableScopes: [
      databaseAccounts_saramsa_cosmosdb_name_resource.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/tables/*'
          'Microsoft.DocumentDB/databaseAccounts/tables/containers/*'
          'Microsoft.DocumentDB/databaseAccounts/tables/containers/entities/*'
        ]
        notDataActions: []
      }
    ]
  }
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb_analysis 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb
  name: 'analysis'
  properties: {
    resource: {
      id: 'analysis'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
        version: 2
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
    }
  }
  dependsOn: [
    databaseAccounts_saramsa_cosmosdb_name_resource
  ]
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb_integrations 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb
  name: 'integrations'
  properties: {
    resource: {
      id: 'integrations'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/userId'
        ]
        kind: 'Hash'
        version: 2
      }
      uniqueKeyPolicy: {
        uniqueKeys: []
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
      fullTextPolicy: {
        defaultLanguage: 'en-US'
        fullTextPaths: []
      }
      computedProperties: []
    }
  }
  dependsOn: [
    databaseAccounts_saramsa_cosmosdb_name_resource
  ]
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb_projects 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb
  name: 'projects'
  properties: {
    resource: {
      id: 'projects'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
        version: 2
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
    }
  }
  dependsOn: [
    databaseAccounts_saramsa_cosmosdb_name_resource
  ]
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb_user_data 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb
  name: 'user_data'
  properties: {
    resource: {
      id: 'user_data'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/userId/projectId'
        ]
        kind: 'Hash'
        version: 2
      }
      uniqueKeyPolicy: {
        uniqueKeys: []
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
      fullTextPolicy: {
        defaultLanguage: 'en-US'
        fullTextPaths: []
      }
      computedProperties: []
    }
  }
  dependsOn: [
    databaseAccounts_saramsa_cosmosdb_name_resource
  ]
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb_user_stories 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb
  name: 'user_stories'
  properties: {
    resource: {
      id: 'user_stories'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/userId'
        ]
        kind: 'Hash'
        version: 2
      }
      uniqueKeyPolicy: {
        uniqueKeys: []
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
      fullTextPolicy: {
        defaultLanguage: 'en-US'
        fullTextPaths: []
      }
      computedProperties: []
    }
  }
  dependsOn: [
    databaseAccounts_saramsa_cosmosdb_name_resource
  ]
}

resource databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb_users 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-05-01-preview' = {
  parent: databaseAccounts_saramsa_cosmosdb_name_saramsa_cpsmosdb
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
        version: 2
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
    }
  }
  dependsOn: [
    databaseAccounts_saramsa_cosmosdb_name_resource
  ]
}
