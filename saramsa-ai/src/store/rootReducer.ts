import { combineReducers } from '@reduxjs/toolkit';
import authReducer from './features/auth/authSlice';
import analysisReducer from './features/analysis/analysisSlice';
import uploadReducer from './features/upload/uploadSlice';
import workItemsReducer from './features/workItems/workItemsSlice';
import azureReducer from './features/azure/azureSlice';
import jiraReducer from './features/jira/jiraSlice';
import integrationsReducer from './features/integrations/integrationsSlice';
import projectsReducer from './features/projects/projectsSlice';
import userStoriesReducer from './features/userStories/userStoriesSlice';
import reviewReducer from './features/review/reviewSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  analysis: analysisReducer,
  upload: uploadReducer,
  workItems: workItemsReducer,
  azure: azureReducer,
  jira: jiraReducer,
  integrations: integrationsReducer,
  projects: projectsReducer,
  userStories: userStoriesReducer,
  review: reviewReducer,
});

export type RootState = ReturnType<typeof rootReducer>;
export default rootReducer;