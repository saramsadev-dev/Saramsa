import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import { apiRequest } from '@/lib/apiRequest';

interface UploadedFile {
  id: string;
  filename: string;
  originalName: string;
  size: number;
  mimeType: string;
  uploadedAt: string;
  url?: string;
}

interface UploadState {
  uploadedFiles: UploadedFile[];
  currentFile: UploadedFile | null;
  loading: boolean;
  error: string | null;
  isUploading: boolean;
}

const initialState: UploadState = {
  uploadedFiles: [],
  currentFile: null,
  loading: false,
  error: null,
  isUploading: false,
};

// Async thunk for uploading a file
export const uploadFile = createAsyncThunk<
  UploadedFile,
  File,
  { rejectValue: string }
>('upload/uploadFile', async (file, { rejectWithValue }) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiRequest('post', '/upload/file/', formData, true, true);
    return response.data;
  } catch (err: any) {
    let errorMessage = 'File upload failed. Please try again.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 400) {
      errorMessage = err.response?.data?.detail || 'Invalid file format or size.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

// Async thunk for getting uploaded files
export const getUploadedFiles = createAsyncThunk<
  UploadedFile[],
  void,
  { rejectValue: string }
>('upload/getUploadedFiles', async (_, { rejectWithValue }) => {
  try {
    const response = await apiRequest('get', '/upload/files/');
    return response.data;
  } catch (err: any) {
    let errorMessage = 'Failed to load uploaded files.';
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

// Async thunk for deleting a file
export const deleteFile = createAsyncThunk<
  string,
  string,
  { rejectValue: string }
>('upload/deleteFile', async (fileId, { rejectWithValue }) => {
  try {
    await apiRequest('delete', `/upload/files/${fileId}/`);
    return fileId;
  } catch (err: any) {
    let errorMessage = 'Failed to delete file.';
    if (err.response?.status === 401) {
      errorMessage = 'Authentication required. Please login again.';
    } else if (err.response?.status === 404) {
      errorMessage = 'File not found.';
    } else if (err.response?.status >= 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (err.message) {
      errorMessage = err.message;
    }
    return rejectWithValue(errorMessage);
  }
});

const uploadSlice = createSlice({
  name: 'upload',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentFile: (state, action: PayloadAction<UploadedFile | null>) => {
      state.currentFile = action.payload;
    },
    clearUploadedFiles: (state) => {
      state.uploadedFiles = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadFile.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.isUploading = true;
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.loading = false;
        state.currentFile = action.payload;
        state.error = null;
        state.isUploading = false;
        // Add to uploaded files list
        state.uploadedFiles.unshift(action.payload);
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'File upload failed.';
        state.isUploading = false;
      })
      .addCase(getUploadedFiles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getUploadedFiles.fulfilled, (state, action) => {
        state.loading = false;
        state.uploadedFiles = action.payload;
        state.error = null;
      })
      .addCase(getUploadedFiles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to load uploaded files.';
      })
      .addCase(deleteFile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteFile.fulfilled, (state, action) => {
        state.loading = false;
        state.uploadedFiles = state.uploadedFiles.filter(
          file => file.id !== action.payload
        );
        if (state.currentFile?.id === action.payload) {
          state.currentFile = null;
        }
        state.error = null;
      })
      .addCase(deleteFile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to delete file.';
      });
  },
});

export const {
  clearError,
  setCurrentFile,
  clearUploadedFiles,
} = uploadSlice.actions;

export default uploadSlice.reducer; 