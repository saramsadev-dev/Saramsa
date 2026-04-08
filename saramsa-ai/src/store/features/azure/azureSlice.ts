import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/lib/apiRequest';

interface AzureProject {
  id: string;
  name: string;
  description: string;
  state: string;
  visibility: string;
  lastUpdateTime: string;
}

interface ActionItem {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  type: 'feature' | 'bug' | 'change';
  status: 'todo' | 'in_progress' | 'done';
  assignee?: string;
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
  tags?: string[];
  acceptance?: string;
  isCompleted?: boolean;
  featureId?: string;
}

interface AzureState {
  projects: AzureProject[];
  workItemTypes: any[];
  selectedProject: AzureProject | null;
  projectMetadata: any | null;
  organization: string;
  pat_token: string;
  loading: boolean;
  error: string | null;
  isPushing: boolean;
  createdProject: any | null;
  workItems: any[];
}

const initialState: AzureState = {
  projects: [],
  workItemTypes: [],
  selectedProject: null,
  projectMetadata: null,
  organization: '',
  pat_token: '',
  loading: false,
  error: null,
  isPushing: false,
  createdProject: null,
  workItems: [],
};

// Async thunk for Azure DevOps configuration (similar to Jira configureJira)
const configureAzure = createAsyncThunk<
  { projects: AzureProject[]; organization: string },
  { organization: string; pat_token: string },
  { rejectValue: string }
>('azure/configure', async (credentials, { rejectWithValue }) => {
  try {
    // Use the new integrations endpoint to fetch Azure projects
    const response = await apiRequest('post', '/integrations/azure/projects/', credentials, true, false);
    // StandardResponse format: response.data.data contains { projects: [...], organization: "..." }
    return response.data.data; // StandardResponse format: response.data.data
  } catch (err: any) {
    let errorMessage = 'Failed to configure Azure DevOps connection.';
    if (err.response?.status === 401) {
      errorMessage = 'Invalid Azure DevOps credentials. Please check your organization and PAT token.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || err.response?.data?.title || 'Invalid configuration data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for fetching Azure DevOps projects (similar to Jira fetchJiraProjects)
const fetchAzureProjects = createAsyncThunk<
  AzureProject[],
  void,
  { rejectValue: string }
>('azure/fetchProjects', async (_, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', '/workitems/azure/projects', {}, true, false);
    return response.data.data.projects || []; // StandardResponse format
  } catch (err: any) {
    let errorMessage = 'Failed to fetch Azure DevOps projects.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for fetching Azure DevOps work item types (similar to Jira fetchJiraIssueTypes)
const fetchAzureWorkItemTypes = createAsyncThunk<
  any[],
  string,
  { rejectValue: string }
>('azure/fetchWorkItemTypes', async (projectId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/workitems/azure/work-item-types?projectId=${projectId}`, {}, true, false);
    return response.data.data.work_item_types || []; // StandardResponse format
  } catch (err: any) {
    let errorMessage = 'Failed to fetch Azure DevOps work item types.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for fetching Azure DevOps project metadata (similar to Jira fetchJiraProjectMetadata)
const fetchAzureProjectMetadata = createAsyncThunk<
  any,
  string,
  { rejectValue: string }
>('azure/fetchProjectMetadata', async (projectId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/workitems/azure/project-metadata?projectId=${projectId}`, {}, true, false);
    return response.data.data.metadata; // StandardResponse format
  } catch (err: any) {
    let errorMessage = 'Failed to fetch Azure DevOps project metadata.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for creating Azure DevOps work items (similar to Jira createJiraIssues)
const createAzureWorkItems = createAsyncThunk<
  any,
  { items: any[]; projectId?: string; project?: string },
  { rejectValue: string }
>('azure/createWorkItems', async (data, { rejectWithValue }) => {
  try {
    const payload: any = { items: data.items };
    if (data.projectId) {
      payload.project_id = data.projectId;
    }
    if (data.project) {
      payload.project = data.project;
    }
    
    const response = await apiRequest('post', '/workitems/azure/create', payload, true, false);
    return response.data.data; // StandardResponse format
  } catch (err: any) {
    let errorMessage = 'Failed to create Azure DevOps work items.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || err.response?.data?.title || 'Invalid work item data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for creating a new Azure DevOps project (similar to Jira createJiraProject)
const createAzureProject = createAsyncThunk<
  any,
  {
    project_name: string;
    azure_project_id: string;
    azure_project_name: string;
    azure_organization: string;
    azure_pat_token: string;
    azure_process_template?: string;
  },
  { rejectValue: string }
>('azure/createProject', async (data, { rejectWithValue }) => {
  try {
    const response = await apiRequest('post', '/workitems/azure/project/create', data, true, false);
    return response.data.data; // StandardResponse format
  } catch (err: any) {
    let errorMessage = 'Failed to create Azure DevOps project.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || err.response?.data?.title || 'Invalid project data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for pushing work items to Azure DevOps
const pushWorkItemsToAzure = createAsyncThunk<
  any,
  { actionItems: ActionItem[]; config?: { organization?: string; project?: string; pat_token?: string } },
  { rejectValue: string }
>('azure/pushWorkItems', async ({ actionItems, config }, { rejectWithValue }) => {
  try {
    // Determine process template if available
    const processTemplate = (typeof window !== 'undefined') ? localStorage.getItem('azure_process_template') : null;

    // Map generic types to template-specific names to avoid invalid API calls
    const mapType = (t: string): string => {
      const typeLower = (t || '').toLowerCase();
      if (typeLower === 'feature') return 'Feature';
      if (typeLower === 'bug') return 'Bug';
      if (typeLower === 'change') return 'Task';
      if (typeLower === 'task') return 'Task';
      // If deep analysis produced User Story/PBI/Issue already, keep it
      if (['user story', 'product backlog item', 'issue', 'requirement'].includes(typeLower)) {
        return t;
      }
      // Template-based mapping for ambiguous "feature request" style items
      if (processTemplate === 'Scrum') return 'Product Backlog Item';
      if (processTemplate === 'Agile') return 'User Story';
      if (processTemplate === 'Basic') return 'Issue';
      if (processTemplate === 'CMMI') return 'Requirement';
      return 'User Story';
    };

    const payload: Record<string, unknown> = {
      items: actionItems.map(item => ({
        type: mapType(item.type),
        title: item.title,
        description: item.description,
        priority: item.priority,
        tags: item.tags?.join(', ') || 'Saramsa'
      }))
    };
    
    // Include process template to help backend map when necessary
    if (processTemplate) {
      (payload as any).process_template = processTemplate;
    }
    
    // Add configuration if provided
    if (config) {
      if (config.organization) payload.organization = config.organization;
      if (config.project) payload.project = config.project;
      if (config.pat_token) payload.pat_token = config.pat_token;
    }
    
    const response = await apiRequest('post', '/workitems/azure/create', payload, true);
    return response.data.data; // StandardResponse format
  } catch (err: any) {
    let errorMessage = 'Failed to push work items to Azure DevOps.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || err.response?.data?.title || 'Invalid work item data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});



const azureSlice = createSlice({
  name: 'azure',
  initialState,
  reducers: {
    setSelectedProject: (state, action: PayloadAction<AzureProject | null>) => {
      state.selectedProject = action.payload;
    },
    setOrganization: (state, action: PayloadAction<string>) => {
      state.organization = action.payload;
    },
    setPatToken: (state, action: PayloadAction<string>) => {
      state.pat_token = action.payload;
    },
    clearProjects: (state) => {
      state.projects = [];
      state.selectedProject = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Configure Azure DevOps
      .addCase(configureAzure.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(configureAzure.fulfilled, (state, action) => {
        state.loading = false;
        state.projects = action.payload.projects;
        state.organization = action.payload.organization;
        state.error = null;
      })
      .addCase(configureAzure.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to configure Azure DevOps';
      })
      // Fetch projects
      .addCase(fetchAzureProjects.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAzureProjects.fulfilled, (state, action) => {
        state.loading = false;
        state.projects = action.payload;
        state.error = null;
      })
      .addCase(fetchAzureProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch projects';
      })
      // Fetch work item types
      .addCase(fetchAzureWorkItemTypes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAzureWorkItemTypes.fulfilled, (state, action) => {
        state.loading = false;
        state.workItemTypes = action.payload;
        state.error = null;
      })
      .addCase(fetchAzureWorkItemTypes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch work item types';
      })
      // Fetch project metadata
      .addCase(fetchAzureProjectMetadata.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAzureProjectMetadata.fulfilled, (state, action) => {
        state.loading = false;
        state.projectMetadata = action.payload;
        state.error = null;
      })
      .addCase(fetchAzureProjectMetadata.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch project metadata';
      })
      // Create work items
      .addCase(createAzureWorkItems.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createAzureWorkItems.fulfilled, (state) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(createAzureWorkItems.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to create work items';
      })
      // Create project
      .addCase(createAzureProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createAzureProject.fulfilled, (state, action) => {
        state.loading = false;
        state.createdProject = action.payload;
        state.error = null;
      })
      .addCase(createAzureProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to create project';
      })
      // Push work items
      .addCase(pushWorkItemsToAzure.pending, (state) => {
        state.isPushing = true;
        state.error = null;
      })
      .addCase(pushWorkItemsToAzure.fulfilled, (state) => {
        state.isPushing = false;
        state.error = null;
      })
      .addCase(pushWorkItemsToAzure.rejected, (state, action) => {
        state.isPushing = false;
        state.error = action.payload || 'Failed to push work items.';
      });
  },
});

export const {
  setSelectedProject,
  setOrganization,
  setPatToken,
  clearProjects,
  clearError,
} = azureSlice.actions;

// Export all async thunks
export {
  configureAzure,
  fetchAzureProjects,
  fetchAzureWorkItemTypes,
  fetchAzureProjectMetadata,
  createAzureWorkItems,
  createAzureProject,
  pushWorkItemsToAzure,
};

export default azureSlice.reducer;

