import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/lib/apiRequest';

export interface ActionItem {
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
  submitted?: boolean;
  submittedAt?: string;
  externalWorkItemId?: string | number;
  externalUrl?: string;
}

export interface Feature {
  id: string;
  name: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'proposed' | 'approved' | 'in_development' | 'testing' | 'released';
  assignee?: string;
  dueDate?: string;
  createdAt: string;
  updatedAt: string;
  color: string;
  actions: ActionItem[];
}

interface WorkItemsState {
  actionItems: ActionItem[];
  features: Feature[];
  selectedActions: string[];
  loading: boolean;
  error: string | null;
  selectedItem: ActionItem | Feature | null;
}

const initialState: WorkItemsState = {
  actionItems: [],
  features: [],
  selectedActions: [],
  loading: false,
  error: null,
  selectedItem: null,
};

// Async thunk for loading work items for a project
export const loadWorkItemsForProject = createAsyncThunk<
  { work_items: any[]; work_items_by_feature: any; summary: any },
  string,
  { rejectValue: string }
>('workItems/loadWorkItemsForProject', async (projectId, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', `/insights/work-items/?project_id=${projectId}`, {}, true);
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to load work items.';
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

// Async thunk for getting action items
export const getActionItems = createAsyncThunk<
  ActionItem[],
  void,
  { rejectValue: string }
>('workItems/getActionItems', async (_, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', '/workitems/action-items/');
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to load action items.';
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

// Async thunk for getting features
export const getFeatures = createAsyncThunk<
  Feature[],
  void,
  { rejectValue: string }
>('workItems/getFeatures', async (_, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', '/workitems/features/');
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to load features.';
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

// Async thunk for creating a generic work item
export const createWorkItem = createAsyncThunk<
  ActionItem | Feature,
  { type: 'action' | 'feature'; data: Partial<ActionItem | Feature> },
  { rejectValue: string }
>('workItems/createWorkItem', async (payload, { rejectWithValue }) => {
  try {
    const response = await apiRequest('post', '/workitems/create', {
      type: payload.type,
      data: payload.data,
    });
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to create work item.';
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

const workItemsSlice = createSlice({
  name: 'workItems',
  initialState,
  reducers: {
    addActionItem: (state, action: PayloadAction<ActionItem>) => {
      state.actionItems.push(action.payload);
    },
    updateActionItem: (state, action: PayloadAction<ActionItem>) => {
      const index = state.actionItems.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {
        state.actionItems[index] = action.payload;
      }
    },
    removeActionItem: (state, action: PayloadAction<string>) => {
      state.actionItems = state.actionItems.filter(item => item.id !== action.payload);
    },
    addFeature: (state, action: PayloadAction<Feature>) => {
      state.features.push(action.payload);
    },
    updateFeature: (state, action: PayloadAction<Feature>) => {
      const index = state.features.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {
        state.features[index] = action.payload;
      }
    },
    removeFeature: (state, action: PayloadAction<string>) => {
      state.features = state.features.filter(item => item.id !== action.payload);
    },
    toggleActionSelection: (state, action: PayloadAction<string>) => {
      const actionId = action.payload;
      if (state.selectedActions.includes(actionId)) {
        state.selectedActions = state.selectedActions.filter(id => id !== actionId);
      } else {
        state.selectedActions.push(actionId);
      }
    },
    clearSelectedActions: (state) => {
      state.selectedActions = [];
    },
    clearActionItems: (state) => {
      state.actionItems = [];
    },
    setSelectedItem: (state, action: PayloadAction<ActionItem | Feature | null>) => {
      state.selectedItem = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Load work items for project
      .addCase(loadWorkItemsForProject.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadWorkItemsForProject.fulfilled, (state, action) => {
        state.loading = false;
        // Map the response to our state structure
        if (action.payload.work_items) {
          state.actionItems = action.payload.work_items;
        }
        state.error = null;
      })
      .addCase(loadWorkItemsForProject.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to load work items';
      })
      // Get action items
      .addCase(getActionItems.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getActionItems.fulfilled, (state, action) => {
        state.loading = false;
        state.actionItems = action.payload;
        state.error = null;
      })
      .addCase(getActionItems.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to load action items';
      })
      // Get features
      .addCase(getFeatures.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getFeatures.fulfilled, (state, action) => {
        state.loading = false;
        state.features = action.payload;
        state.error = null;
      })
      .addCase(getFeatures.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to load features';
      })
      // Create work item
      .addCase(createWorkItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createWorkItem.fulfilled, (state, action) => {
        state.loading = false;
        // Add the created item to the appropriate array
        if ('actions' in action.payload) {
          state.features.push(action.payload as Feature);
        } else {
          state.actionItems.push(action.payload as ActionItem);
        }
        state.error = null;
      })
      .addCase(createWorkItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to create work item';
      });
  },
});

export const {
  addActionItem,
  updateActionItem,
  removeActionItem,
  addFeature,
  updateFeature,
  removeFeature,
  toggleActionSelection,
  clearSelectedActions,
  clearActionItems,
  setSelectedItem,
  clearError,
} = workItemsSlice.actions;

export default workItemsSlice.reducer;
