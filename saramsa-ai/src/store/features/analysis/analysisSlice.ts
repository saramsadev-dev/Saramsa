import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/lib/apiRequest';
import type { AnalysisData } from '@/types/analysis';

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
  analyzingByProject: Record<string, boolean>;
  loadedComments: string[] | null;
  latestAnalysis: any | null;
  latestLoading: boolean;
  latestError: string | null;
  projectContext: ProjectContext | null;
  // Async task tracking for Celery
  taskId: string | null;
  analysisStatus: 'idle' | 'pending' | 'processing' | 'success' | 'failure';
  pollingInterval: number | null;
}

const initialState: AnalysisState = {
  analysisData: null,
  deepAnalysis: null,
  loading: false,
  error: null,
  isAnalyzing: false,
  analyzingByProject: {},
  loadedComments: null,
  latestAnalysis: null,
  latestLoading: false,
  latestError: null,
  projectContext: null,
  // Async task tracking
  taskId: null,
  analysisStatus: 'idle',
  pollingInterval: null,
};


// Async thunk for polling task status
export const pollTaskStatus = createAsyncThunk<
  any,
  string,
  { rejectValue: string }
>('analysis/pollTaskStatus', async (taskId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/insights/task-status/${taskId}/`, undefined, true);
    return response.data.data; // Returns { status, result, error }
  } catch (err: any) {
    let errorMessage = 'Failed to check task status.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 404) {
      errorMessage = 'Task not found.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for analyzing comments (sentiment analysis with Celery)
export const analyzeComments = createAsyncThunk<
  any,
  { comments: string[]; projectId?: string; fileName?: string },
  { rejectValue: string }
>('analysis/analyzeComments', async (data, { dispatch, rejectWithValue }) => {
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

    // Call the async endpoint - returns task_id immediately
    const response = await apiRequest('post', '/insights/analyze/', payload, true, false);
    const taskId = response.data.data.task_id;

    if (!taskId) {
      throw new Error('No task ID received from server');
    }

    // Start polling for task status
    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        try {
          const statusResult = await dispatch(pollTaskStatus(taskId)).unwrap();

          const terminalStatus = statusResult.status;
          if (terminalStatus === 'SUCCESS' || terminalStatus === 'PARTIAL') {
            clearInterval(pollInterval);
            const taskResult = statusResult.result;

            // Preferred: fetch the exact analysis by ID (avoids "latest" race conditions)
            if (taskResult?.insight_id) {
              try {
                const analysisRes = await apiRequest(
                  'get',
                  `/insights/analysis/${taskResult.insight_id}/`,
                  undefined,
                  true
                );
                const analysisData = analysisRes.data?.data;
                if (analysisData?.exists && analysisData?.analysis) {
                  const analysis = analysisData.analysis;
                  resolve({
                    id: analysis.id || taskResult.insight_id,
                    analysisData: analysis.result ?? analysis
                  });
                  return;
                }
                reject('Analysis saved but not found by ID.');
                return;
              } catch (fetchErr: any) {
                reject(fetchErr?.message || 'Analysis saved but failed to load by ID.');
                return;
              }
            }

            // Legacy: task included full result (e.g. older backend)
            const rawData = taskResult?.result ?? taskResult;
            const wrappedData = {
              id: taskResult?.insight_id || `analysis_${Date.now()}`,
              analysisData: rawData
            };
            resolve(wrappedData);
          } else if (terminalStatus === 'FAILURE' || terminalStatus === 'FAILED') {
            clearInterval(pollInterval);
            reject(statusResult.error || 'Analysis failed');
          }
          // Continue polling if status is PENDING or STARTED
        } catch (error) {
          clearInterval(pollInterval);
          reject(error);
        }
      }, 2000); // Poll every 2 seconds

      // Timeout after 15 minutes (for large datasets with NLI processing)
      setTimeout(() => {
        clearInterval(pollInterval);
        reject('Analysis timeout - task took too long');
      }, 900000); // 15 minutes timeout
    });
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
    const response = await apiRequest('get', `/projects/${projectId}/analysis/latest/`, { refresh: Date.now() }, true);
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
    const response = await apiRequest('get', `/projects/${projectId}/analysis/latest/`, { refresh: Date.now() }, true);
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

    console.log('✅ Raw API response received:', {
      status: response.status,
      dataSize: JSON.stringify(response.data).length,
      hasData: !!response.data,
      hasNestedData: !!response.data?.data
    });

    // Fix: Extract user stories from nested response structure
    // Backend returns: { data: { data: { user_stories: [{ work_items: [...] }] } } }
    const userStoriesData = response.data.data?.user_stories?.[0];
    
    console.log('✅ Extracted user stories data:', {
      hasUserStoriesData: !!userStoriesData,
      workItemsCount: userStoriesData?.work_items?.length || 0
    });
    
    return userStoriesData || response.data;
  } catch (err: any) {
    console.error('❌ generateUserStories error:', err);
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
    
    console.error('❌ Final error message:', errorMessage);
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
      .addCase(analyzeComments.pending, (state, action) => {
        state.loading = true;
        state.error = null;
        state.isAnalyzing = true;
        const key = action.meta.arg.projectId ?? 'personal';
        state.analyzingByProject[key] = true;
        state.analysisStatus = 'pending';
      })
      .addCase(analyzeComments.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        const key = action.meta.arg.projectId ?? 'personal';
        state.analyzingByProject[key] = false;
        state.isAnalyzing = Object.values(state.analyzingByProject).some(Boolean);
        state.analysisStatus = 'success';
        state.taskId = null;
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
        const key = action.meta.arg.projectId ?? 'personal';
        state.analyzingByProject[key] = false;
        state.isAnalyzing = Object.values(state.analyzingByProject).some(Boolean);
        state.analysisStatus = 'failure';
        state.taskId = null;
      })
      .addCase(pollTaskStatus.pending, (state) => {
        state.analysisStatus = 'processing';
      })
      .addCase(pollTaskStatus.fulfilled, (state, action) => {
        // Status is updated by analyzeComments thunk based on result
        if (action.payload.status === 'SUCCESS') {
          state.analysisStatus = 'success';
        } else if (action.payload.status === 'FAILURE') {
          state.analysisStatus = 'failure';
        }
      })
      .addCase(pollTaskStatus.rejected, (state) => {
        state.analysisStatus = 'failure';
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
