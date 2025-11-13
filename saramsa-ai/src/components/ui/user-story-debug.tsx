'use client';

import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Trash2, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { 
  fetchUserStoriesByProject,
  deleteUserStory,
  deleteUserStories
} from '@/store/features/userStories/userStoriesSlice';
import { RootState, AppDispatch } from '@/store/store';

interface UserStoryDebugProps {
  projectId: string;
  userId?: string;
}

export function UserStoryDebug({ projectId, userId }: UserStoryDebugProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { currentProjectUserStories, loading, error } = useSelector((state: RootState) => state.userStories);

  useEffect(() => {
    if (projectId) {
      dispatch(fetchUserStoriesByProject({ projectId, userId }));
    }
  }, [dispatch, projectId, userId]);

  const handleRefresh = () => {
    dispatch(fetchUserStoriesByProject({ projectId, userId }));
  };

  const handleDeleteSingle = async (userStoryId: string) => {
    if (confirm(`Are you sure you want to delete user story: ${userStoryId}?`)) {
      try {
        await dispatch(deleteUserStory({ userStoryId })).unwrap();
        console.log(`Successfully deleted user story: ${userStoryId}`);
        // Refresh the list
        dispatch(fetchUserStoriesByProject({ projectId, userId }));
      } catch (error) {
        console.error('Failed to delete user story:', error);
        alert(`Failed to delete user story: ${error}`);
      }
    }
  };

  const handleDeleteAll = async () => {
    const userStoryIds = currentProjectUserStories.map(story => story.id);
    
    if (userStoryIds.length === 0) {
      alert('No user stories to delete');
      return;
    }

    if (confirm(`Are you sure you want to delete ALL ${userStoryIds.length} user stories? This action cannot be undone.`)) {
      try {
        await dispatch(deleteUserStories({ userStoryIds })).unwrap();
        console.log(`Successfully deleted ${userStoryIds.length} user stories`);
        // Refresh the list
        dispatch(fetchUserStoriesByProject({ projectId, userId }));
      } catch (error) {
        console.error('Failed to delete user stories:', error);
        alert(`Failed to delete user stories: ${error}`);
      }
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>User Story Debug Tool</span>
            <div className="flex gap-2">
              <Button
                onClick={handleRefresh}
                disabled={loading}
                variant="outline"
                size="sm"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                onClick={handleDeleteAll}
                disabled={loading || currentProjectUserStories.length === 0}
                variant="destructive"
                size="sm"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete All ({currentProjectUserStories.length})
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
              <span className="text-red-700 dark:text-red-300">{error}</span>
            </div>
          )}

          <div className="grid gap-2 text-sm">
            <div><strong>Project ID:</strong> {projectId}</div>
            <div><strong>User ID:</strong> {userId || 'Not specified'}</div>
            <div><strong>Total User Stories:</strong> {currentProjectUserStories.length}</div>
          </div>

          {loading && (
            <div className="text-center py-4">
              <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading user stories...</p>
            </div>
          )}

          {!loading && currentProjectUserStories.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No user stories found for this project.
            </div>
          )}

          {!loading && currentProjectUserStories.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">User Stories:</h3>
              {currentProjectUserStories.map((userStory, index) => (
                <Card key={userStory.id} className="border-l-4 border-l-blue-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">#{index + 1}</Badge>
                          <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                            {userStory.platform}
                          </Badge>
                        </div>
                        
                        <div className="space-y-1 text-sm">
                          <div><strong>ID:</strong> <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">{userStory.id}</code></div>
                          <div><strong>Type:</strong> {userStory.type}</div>
                          <div><strong>Project ID:</strong> {userStory.projectId}</div>
                          <div><strong>User ID:</strong> {userStory.userId}</div>
                          <div><strong>Generated:</strong> {new Date(userStory.generated_at).toLocaleString()}</div>
                          <div><strong>Work Items:</strong> {userStory.work_items.length}</div>
                        </div>

                        {userStory.work_items.length > 0 && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-sm font-medium text-blue-600 dark:text-blue-400">
                              View Work Items ({userStory.work_items.length})
                            </summary>
                            <div className="mt-2 space-y-1 pl-4 border-l-2 border-gray-200 dark:border-gray-700">
                              {userStory.work_items.slice(0, 5).map((item, idx) => (
                                <div key={item.id} className="text-xs">
                                  <strong>{idx + 1}.</strong> {item.title} 
                                  <Badge variant="outline" className="ml-2 text-xs">{item.type}</Badge>
                                  <Badge variant="outline" className="ml-1 text-xs">{item.priority}</Badge>
                                </div>
                              ))}
                              {userStory.work_items.length > 5 && (
                                <div className="text-xs text-gray-500">
                                  ... and {userStory.work_items.length - 5} more
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                      
                      <Button
                        onClick={() => handleDeleteSingle(userStory.id)}
                        disabled={loading}
                        variant="outline"
                        size="sm"
                        className="text-red-600 border-red-200 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/20"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Test Section */}
      <Card>
        <CardHeader>
          <CardTitle>API Test Examples</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm space-y-2">
            <p><strong>Current Project ID:</strong> <code>{projectId}</code></p>
            <p><strong>Available User Story IDs:</strong></p>
            <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs font-mono">
              {currentProjectUserStories.length > 0 ? (
                currentProjectUserStories.map(story => (
                  <div key={story.id}>"{story.id}"</div>
                ))
              ) : (
                <div>No user stories found</div>
              )}
            </div>
          </div>
          
          <div className="text-sm">
            <p><strong>Test with curl:</strong></p>
            <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs font-mono overflow-x-auto">
              {currentProjectUserStories.length > 0 ? (
                `curl -X DELETE "http://127.0.0.1:8000/api/insights/user-stories/${currentProjectUserStories[0].id}/delete/" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"`
              ) : (
                'No user stories available for testing'
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
