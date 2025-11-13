import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/lib/apiRequest';

interface JiraProject {
  id: string;
  key: string;
  name: string;
  description?: string;
  projectTypeKey: string;
  style: string;
  isCompanyManaged: boolean;
  isTeamManaged: boolean;
  projectCategory?: string;
}

interface JiraIssueType {
  id: string;
  name: string;
  description?: string;
  iconUrl?: string;
  hierarchyLevel: number;
  isSubtask: boolean;
}

interface JiraState {
  projects: JiraProject[];
  issueTypes: JiraIssueType[];
  selectedProject: JiraProject | null;
  projectMetadata: any | null;
  loading: boolean;
  error: string | null;
  isAnalyzing: boolean;
  analysis: any | null;
  createdProject: any | null;
}

const initialState: JiraState = {
  projects: [],
  issueTypes: [],
  selectedProject: null,
  projectMetadata: null,
  loading: false,
  error: null,
  isAnalyzing: false,
  analysis: null,
  createdProject: null,
};

// Async thunk for Jira configuration
export const configureJira = createAsyncThunk<
  { projects: JiraProject[]; domain: string },
  { domain: string; email: string; api_token: string },
  { rejectValue: string }
>('jira/configure', async (credentials, { rejectWithValue }) => {
  try {
    const response = await apiRequest('post', '/workitems/jira/config', credentials, true, false);
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to configure Jira connection.';
    if (err.response?.status === 401) {
      errorMessage = 'Invalid Jira credentials. Please check your domain, email, and API token.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.error || 'Invalid configuration data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for fetching Jira projects
export const fetchJiraProjects = createAsyncThunk<
  JiraProject[],
  void,
  { rejectValue: string }
>('jira/fetchProjects', async (_, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', '/workitems/jira/projects', {}, true, false);
    return response.data.projects || [];
  } catch (err: any) {
    let errorMessage = 'Failed to fetch Jira projects.';
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

// Async thunk for fetching Jira issue types
export const fetchJiraIssueTypes = createAsyncThunk<
  JiraIssueType[],
  string,
  { rejectValue: string }
>('jira/fetchIssueTypes', async (projectId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/workitems/jira/issue-types?projectId=${projectId}`, {}, true, false);
    return response.data.issue_types || [];
  } catch (err: any) {
    let errorMessage = 'Failed to fetch Jira issue types.';
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

// Async thunk for fetching Jira project metadata
export const fetchJiraProjectMetadata = createAsyncThunk<
  any,
  string,
  { rejectValue: string }
>('jira/fetchProjectMetadata', async (projectId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/workitems/jira/project-metadata?projectId=${projectId}`, {}, true, false);
    return response.data.metadata;
  } catch (err: any) {
    let errorMessage = 'Failed to fetch Jira project metadata.';
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

// Async thunk for creating Jira issues
export const createJiraIssues = createAsyncThunk<
  any,
  { items: any[]; projectId?: string; projectKey?: string },
  { rejectValue: string }
>('jira/createIssues', async (data, { rejectWithValue }) => {
  try {
    const payload: any = { items: data.items };
    if (data.projectId) {
      payload.project_id = data.projectId;
    }
    if (data.projectKey) {
      payload.project_key = data.projectKey;
    }
    
    const response = await apiRequest('post', '/workitems/jira/create', payload, true, false);
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to create Jira issues.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || 'Invalid work item data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for creating a new Jira project
export const createJiraProject = createAsyncThunk<
  any,
  {
    project_name: string;
    jira_project_id: string;
    jira_project_key: string;
    jira_project_name: string;
    jira_domain: string;
    jira_email: string;
    jira_api_token: string;
  },
  { rejectValue: string }
>('jira/createProject', async (data, { rejectWithValue }) => {
  try {
    const response = await apiRequest('post', '/workitems/jira/project/create', data, true, false);
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to create Jira project.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.error || 'Invalid project data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});




const jiraSlice = createSlice({
  name: 'jira',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setSelectedProject: (state, action: PayloadAction<JiraProject | null>) => {
      state.selectedProject = action.payload;
    },
    clearProjects: (state) => {
      state.projects = [];
      state.selectedProject = null;
      state.error = null;
    },
    clearAnalysis: (state) => {
      state.analysis = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Configure Jira
      .addCase(configureJira.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(configureJira.fulfilled, (state, action) => {
        state.loading = false;
        state.projects = action.payload.projects;
        state.error = null;
      })
      .addCase(configureJira.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to configure Jira';
      })
      // Fetch projects
      .addCase(fetchJiraProjects.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchJiraProjects.fulfilled, (state, action) => {
        state.loading = false;
        state.projects = action.payload;
        state.error = null;
      })
      .addCase(fetchJiraProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch projects';
      })
      // Fetch issue types
      .addCase(fetchJiraIssueTypes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchJiraIssueTypes.fulfilled, (state, action) => {
        state.loading = false;
        state.issueTypes = action.payload;
        state.error = null;
      })
      .addCase(fetchJiraIssueTypes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch issue types';
      })
      // Fetch project metadata
      .addCase(fetchJiraProjectMetadata.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchJiraProjectMetadata.fulfilled, (state, action) => {
        state.loading = false;
        state.projectMetadata = action.payload;
        state.error = null;
      })
      .addCase(fetchJiraProjectMetadata.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch project metadata';
      })
      // Create issues
      .addCase(createJiraIssues.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createJiraIssues.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(createJiraIssues.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to create issues';
      })
      // Create project
      .addCase(createJiraProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createJiraProject.fulfilled, (state, action) => {
        state.loading = false;
        state.createdProject = action.payload;
        state.error = null;
      })
      .addCase(createJiraProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to create project';
      })
;
  },
});

export const {
  clearError,
  setSelectedProject,
  clearProjects,
  clearAnalysis,
} = jiraSlice.actions;

export default jiraSlice.reducer;
