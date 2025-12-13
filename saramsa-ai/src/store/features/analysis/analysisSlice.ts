import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/lib/apiRequest';
import type { AnalysisData } from '@/lib/uploadService';

interface ProjectContext {
  project_id: string;
  project_status?: string;
  config_state?: string;
  is_draft?: boolean;
}

interface AnalysisState {
  analysisData: AnalysisData | null;
  deepAnalysis: any | null;
  loading: boolean;
  error: string | null;
  isAnalyzing: boolean;
  loadedComments: string[] | null;
  latestAnalysis: any | null;
  latestLoading: boolean;
  latestError: string | null;
  projectContext: ProjectContext | null;
}

const initialState: AnalysisState = {
  analysisData: null,
  deepAnalysis: null,
  loading: false,
  error: null,
  isAnalyzing: false,
  loadedComments: null,
  latestAnalysis: null,
  latestLoading: false,
  latestError: null,
  projectContext: null,
};

// Async thunk for analyzing comments (sentiment analysis only)
export const analyzeComments = createAsyncThunk<
  any,
  { comments: string[]; projectId?: string; fileName?: string },
  { rejectValue: string }
>('analysis/analyzeComments', async (data, { rejectWithValue }) => {
  try {
    const payload: any = { 
      comments: data.comments
    };
    if (data.projectId) {
      payload.project_id = data.projectId;
    }
    if (data.fileName) {
      payload.file_name = data.fileName;
    }
    
    const response = await apiRequest('post', '/insights/analyze/', payload, true, false);
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Sentiment analysis failed. Please try again.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || 'Invalid input data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for getting latest analysis for a project
export const getLatestAnalysis = createAsyncThunk<
  any,
  string,
  { rejectValue: string }
>('analysis/getLatestAnalysis', async (projectId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/projects/${projectId}/analysis/latest/`, undefined, true);
    // StandardResponse format: response.data.data contains the actual data
    return response.data.data;
  } catch (err: any) {
    let errorMessage = 'Failed to load latest analysis.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 404) {
      errorMessage = 'Analysis not found.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for getting consolidated dashboard data (replaces multiple API calls)
export const getConsolidatedDashboardData = createAsyncThunk<
  any,
  string,
  { rejectValue: string }
>('analysis/getConsolidatedDashboardData', async (projectId, { rejectWithValue }) => {
  try {
    // This single call now returns: analysis + user stories + comments + submission status
    const response = await apiRequest('get', `/projects/${projectId}/analysis/latest/`, undefined, true);
    return response.data.data;
  } catch (err: any) {
    let errorMessage = 'Failed to load dashboard data.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 404) {
      errorMessage = 'No data found for this project.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for generating user stories/work items from analysis data
export const generateUserStories = createAsyncThunk<
  any,
  { 
    analysisData: any; 
    comments: string[]; 
    platform: 'azure' | 'jira';
    processTemplate?: string; 
    projectId?: string; 
    projectMetadata?: any;
  },
  { rejectValue: string }
>('analysis/generateUserStories', async (data, { rejectWithValue }) => {
  try {
    const payload: any = {
      analysis_data: data.analysisData,
      comments: data.comments,
      platform: data.platform, // Correctly pass the platform parameter
      process_template: data.processTemplate || 'Agile'
    };
    
    if (data.projectId) {
      payload.project_id = data.projectId;
    }
    
    if (data.projectMetadata) {
      payload.project_metadata = data.projectMetadata;
    }
    
    console.log(`🔧 generateUserStories payload for ${data.platform}:`, payload);
    
    // User story generation involves LLM calls which can take longer - increase timeout to 3 minutes
    const response = await apiRequest(
      'post', 
      '/insights/user-story-creation/', 
      payload, 
      true, 
      false,
      { timeout: 180000 } // 3 minutes timeout for LLM calls
    );
    return response.data;
  } catch (err: any) {
    let errorMessage = `${data.platform === 'jira' ? 'Jira' : 'Azure'} work items generation failed. Please try again.`;
    
    // Handle timeout errors specifically
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      errorMessage = 'Work item generation is taking longer than expected. This may happen with large datasets. Please try again or reduce the number of comments.';
    } else if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Invalid input data.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for submitting user stories to ITSM tools
export const submitUserStories = createAsyncThunk<
  any,
  {
    userId: string;
    projectId: string;
    userStories: any[];
    platform: 'azure' | 'jira';
    processTemplate?: string;
    time?: string;
  },
  { rejectValue: string }
>('analysis/submitUserStories', async (data, { rejectWithValue }) => {
  try {
    const payload = {
      user_id: data.userId,
      project_id: data.projectId,
      user_stories: data.userStories,
      platform: data.platform,
      process_template: data.processTemplate || 'Agile',
      time: data.time || new Date().toISOString()
    };
    
    console.log(`🔧 submitUserStories payload for ${data.platform}:`, payload);
    
    const response = await apiRequest('post', '/insights/user-story-submission/', payload, true, false);
    return response.data;
  } catch (err: any) {
    let errorMessage = `${data.platform === 'jira' ? 'Jira' : 'Azure DevOps'} user story submission failed. Please try again.`;
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Invalid input data.';
    } else if (err.response?.status === 404) {
      errorMessage = 'Project not found. Please check your project configuration.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    clearAnalysisData: (state) => {
      state.analysisData = null;
      state.deepAnalysis = null;
      state.error = null;
      state.projectContext = null;
    },
    clearError: (state) => {
      state.error = null;
    },
    setAnalyzing: (state, action: PayloadAction<boolean>) => {
      state.isAnalyzing = action.payload;
    },
    setLoadedComments: (state, action: PayloadAction<string[] | null>) => {
      state.loadedComments = action.payload;
    },
    setAnalysisData: (state, action: PayloadAction<AnalysisData | null>) => {
      state.analysisData = action.payload;
    },
    setDeepAnalysis: (state, action: PayloadAction<any | null>) => {
      state.deepAnalysis = action.payload;
    },
    setProjectContext: (state, action: PayloadAction<ProjectContext | null>) => {
      state.projectContext = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(analyzeComments.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.isAnalyzing = true;
      })
      .addCase(analyzeComments.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        state.isAnalyzing = false;
        // Store the comments that were analyzed
        if (action.meta.arg.comments) {
          state.loadedComments = action.meta.arg.comments;
        }
        state.projectContext = action.payload?.context ?? state.projectContext;
        // The analysis data will be set by the component after normalization
      })
      .addCase(analyzeComments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Analysis failed.';
        state.isAnalyzing = false;
      })
      .addCase(getLatestAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getLatestAnalysis.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        
        // Check if analysis exists - if not, clear all analysis data
        if (!action.payload?.exists || !action.payload?.analysis) {
          state.analysisData = null;
          state.deepAnalysis = null;
          state.loadedComments = null;
          state.projectContext = null;
        }
        state.projectContext = action.payload?.analysis?.context ?? state.projectContext;
        // The analysis data will be set by the component after normalization if exists
      })
      .addCase(getLatestAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to load latest analysis.';
      })
      .addCase(getConsolidatedDashboardData.pending, (state) => {
        state.latestLoading = true;
        state.latestError = null;
      })
      .addCase(getConsolidatedDashboardData.fulfilled, (state, action) => {
        state.latestLoading = false;
        state.latestError = null;
        state.latestAnalysis = action.payload;
        
        // Check if analysis exists - if not, clear all analysis data
        if (!action.payload?.exists || !action.payload?.analysis) {
          state.analysisData = null;
          state.deepAnalysis = null;
          state.loadedComments = null;
          state.projectContext = null;
        } else {
          if (action.payload.analysis.comments) {
            state.loadedComments = action.payload.analysis.comments.comments || [];
          }
          state.projectContext = action.payload.analysis.context ?? state.projectContext;
        }
      })
      .addCase(getConsolidatedDashboardData.rejected, (state, action) => {
        state.latestLoading = false;
        state.latestError = action.payload || 'Failed to load dashboard data.';
      })
      .addCase(generateUserStories.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generateUserStories.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        state.deepAnalysis = action.payload;
        state.projectContext = action.payload?.context ?? state.projectContext;
      })
      .addCase(generateUserStories.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'User stories generation failed.';
      })
      .addCase(submitUserStories.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitUserStories.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        // Optionally store submission results
      })
      .addCase(submitUserStories.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'User stories submission failed.';
      });
  },
});

export const {
  clearAnalysisData,
  clearError,
  setAnalyzing,
  setLoadedComments,
  setAnalysisData,
  setDeepAnalysis,
  setProjectContext,
} = analysisSlice.actions;

export default analysisSlice.reducer; 