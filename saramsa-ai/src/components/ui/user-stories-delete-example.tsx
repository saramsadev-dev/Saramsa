'use client';

import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Trash2, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { 
  deleteUserStory, 
  deleteUserStories, 
  deleteWorkItems,
  fetchUserStoriesByProject 
} from '@/store/features/userStories/userStoriesSlice';
import { RootState, AppDispatch } from '@/store/store';

interface UserStoryDeleteExampleProps {
  projectId: string;
  userId?: string;
}

export function UserStoryDeleteExample({ projectId, userId }: UserStoryDeleteExampleProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { currentProjectUserStories, loading, error } = useSelector((state: RootState) => state.userStories);
  const [selectedUserStories, setSelectedUserStories] = useState<string[]>([]);
  const [selectedWorkItems, setSelectedWorkItems] = useState<string[]>([]);

  // Delete a single user story
  const handleDeleteSingleUserStory = async (userStoryId: string) => {
    if (confirm('Are you sure you want to delete this user story? This action cannot be undone.')) {
      try {
        await dispatch(deleteUserStory({ userStoryId })).unwrap();
        console.log('User story deleted successfully');
      } catch (error) {
        console.error('Failed to delete user story:', error);
      }
    }
  };

  // Delete multiple user stories (bulk delete)
  const handleDeleteMultipleUserStories = async () => {
    if (selectedUserStories.length === 0) {
      alert('Please select at least one user story to delete.');
      return;
    }

    if (confirm(`Are you sure you want to delete ${selectedUserStories.length} user stories? This action cannot be undone.`)) {
      try {
        const result = await dispatch(deleteUserStories({ 
          userStoryIds: selectedUserStories 
        })).unwrap();
        
        console.log(`Successfully deleted ${result.deletedIds.length} user stories`);
        
        if (result.failedDeletions && result.failedDeletions.length > 0) {
          console.warn('Some deletions failed:', result.failedDeletions);
        }
        
        setSelectedUserStories([]);
      } catch (error) {
        console.error('Failed to delete user stories:', error);
      }
    }
  };

  // Delete work items from user stories
  const handleDeleteWorkItems = async () => {
    if (selectedWorkItems.length === 0) {
      alert('Please select at least one work item to delete.');
      return;
    }

    if (confirm(`Are you sure you want to delete ${selectedWorkItems.length} work items? This action cannot be undone.`)) {
      try {
        const matchingUserStories = currentProjectUserStories.filter(story => 
          story.work_items?.some(item => selectedWorkItems.includes(item.id))
        );
        
        if (matchingUserStories.length === 0) {
          alert('Could not find user story containing these work items');
          return;
        }

        const userStoryId = matchingUserStories[0].id;
        
        const result = await dispatch(deleteWorkItems({ 
          workItemIds: selectedWorkItems,
          userStoryId: userStoryId
        })).unwrap();
        
        console.log(`Successfully deleted ${result.deletedCount} work items`);
        setSelectedWorkItems([]);
        
        // Refresh user stories to reflect the changes
        if (userId) {
          dispatch(fetchUserStoriesByProject({ projectId, userId }));
        } else {
          dispatch(fetchUserStoriesByProject({ projectId }));
        }
      } catch (error) {
        console.error('Failed to delete work items:', error);
      }
    }
  };

  const toggleUserStorySelection = (userStoryId: string) => {
    setSelectedUserStories(prev => 
      prev.includes(userStoryId) 
        ? prev.filter(id => id !== userStoryId)
        : [...prev, userStoryId]
    );
  };

  const toggleWorkItemSelection = (workItemId: string) => {
    setSelectedWorkItems(prev => 
      prev.includes(workItemId) 
        ? prev.filter(id => id !== workItemId)
        : [...prev, workItemId]
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="w-5 h-5" />
            User Story Delete Operations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
              <span className="text-red-700 dark:text-red-300">{error}</span>
            </div>
          )}

          {/* Bulk Actions */}
          <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Selected User Stories:</span>
              <Badge variant="secondary">{selectedUserStories.length}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Selected Work Items:</span>
              <Badge variant="secondary">{selectedWorkItems.length}</Badge>
            </div>
            <div className="flex gap-2 ml-auto">
              <Button
                onClick={handleDeleteMultipleUserStories}
                disabled={loading || selectedUserStories.length === 0}
                variant="destructive"
                size="sm"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete User Stories ({selectedUserStories.length})
              </Button>
              <Button
                onClick={handleDeleteWorkItems}
                disabled={loading || selectedWorkItems.length === 0}
                variant="outline"
                size="sm"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Work Items ({selectedWorkItems.length})
              </Button>
            </div>
          </div>

          {/* User Stories List */}
          <div className="space-y-4">
            {currentProjectUserStories.map((userStory) => (
              <Card key={userStory.id} className="border-l-4 border-l-blue-500">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={selectedUserStories.includes(userStory.id)}
                      onChange={() => toggleUserStorySelection(userStory.id)}
                      className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          User Story: {userStory.id}
                        </h3>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                            {userStory.platform}
                          </Badge>
                          <Button
                            onClick={() => handleDeleteSingleUserStory(userStory.id)}
                            disabled={loading}
                            variant="outline"
                            size="sm"
                            className="text-red-600 border-red-200 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/20"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        <p><strong>Project:</strong> {userStory.projectId}</p>
                        <p><strong>Platform:</strong> {userStory.platform}</p>
                        <p><strong>Work Items:</strong> {userStory.work_items.length}</p>
                      </div>

                      {/* Work Items */}
                      {userStory.work_items.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Work Items:
                          </h4>
                          <div className="grid gap-2">
                            {userStory.work_items.map((workItem) => (
                              <div 
                                key={workItem.id} 
                                className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded"
                              >
                                <input
                                  type="checkbox"
                                  checked={selectedWorkItems.includes(workItem.id)}
                                  onChange={() => toggleWorkItemSelection(workItem.id)}
                                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <div className="flex-1">
                                  <span className="text-sm font-medium">{workItem.title}</span>
                                  <div className="flex items-center gap-2 mt-1">
                                    <Badge variant="outline" className="text-xs">
                                      {workItem.type}
                                    </Badge>
                                    <Badge variant="outline" className="text-xs">
                                      {workItem.priority}
                                    </Badge>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {currentProjectUserStories.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No user stories found for this project.
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Usage Examples */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            API Usage Examples
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3 text-sm">
            <div>
              <h4 className="font-medium mb-2">1. Delete Single User Story:</h4>
              <code className="block p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                {`// Using the individual endpoint
DELETE /api/insights/user-stories/{user_story_id}/delete/

// Using Redux
dispatch(deleteUserStory({ userStoryId: "story_id_here" }))`}
              </code>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">2. Delete Multiple User Stories:</h4>
              <code className="block p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                {`// Using the bulk endpoint
DELETE /api/insights/user-stories/delete-items/
Body: {
  "ids": ["story_id_1", "story_id_2"],
  "type": "user_stories"
}

// Using Redux
dispatch(deleteUserStories({ userStoryIds: ["story_id_1", "story_id_2"] }))`}
              </code>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">3. Delete Work Items:</h4>
              <code className="block p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                {`// Using the bulk endpoint
DELETE /api/insights/user-stories/delete-items/
Body: {
  "ids": ["work_item_id_1", "work_item_id_2"],
  "type": "work_items"  // This is the default
}

// Using Redux
dispatch(deleteWorkItems({ workItemIds: ["work_item_id_1", "work_item_id_2"] }))`}
              </code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
