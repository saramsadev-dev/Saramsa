'use client';

import { useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { deleteWorkItems } from '@/store/features/userStories/userStoriesSlice';
import { Button } from './button';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { Trash2, RefreshCw } from 'lucide-react';
import { Checkbox } from './checkbox';

interface WorkItemsSimpleProps {
  projectId?: string;
}

export function WorkItemsSimple({ projectId }: WorkItemsSimpleProps) {
  const dispatch = useAppDispatch();
  const { currentProjectUserStories, loading, error } = useAppSelector((state) => state.userStories);
  const [selectedWorkItems, setSelectedWorkItems] = useState<string[]>([]);
  const [deleting, setDeleting] = useState(false);

  const toggleWorkItemSelection = (workItemId: string) => {
    setSelectedWorkItems(prev => 
      prev.includes(workItemId) 
        ? prev.filter(id => id !== workItemId)
        : [...prev, workItemId]
    );
  };

  const handleDeleteSelected = async () => {
    if (selectedWorkItems.length === 0) {
      alert('Please select work items to delete');
      return;
    }

    // Find which user story contains these work items
    const userStoryWithItems = currentProjectUserStories.find(story => 
      story.work_items?.some(item => selectedWorkItems.includes(item.id))
    );

    if (!userStoryWithItems) {
      alert('Could not find user story containing these work items');
      return;
    }

    if (!confirm(`Delete ${selectedWorkItems.length} work items from "${userStoryWithItems.id}"?`)) {
      return;
    }

    setDeleting(true);
    try {
      await dispatch(deleteWorkItems({
        workItemIds: selectedWorkItems,
        userStoryId: userStoryWithItems.id,
        projectId: projectId
      })).unwrap();

      setSelectedWorkItems([]);
    } catch (err) {
      console.error('Failed to delete work items:', err);
      alert(`Failed to delete work items: ${err}`);
    } finally {
      setDeleting(false);
    }
  };

  const allWorkItems = currentProjectUserStories.flatMap(story => 
    (story.work_items || []).map(item => ({
      ...item,
      userStoryId: story.id,
      userStoryType: story.type
    }))
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Work Items ({allWorkItems.length})</span>
          <div className="flex gap-2">
            <Button
              onClick={handleDeleteSelected}
              disabled={deleting || selectedWorkItems.length === 0}
              variant="destructive"
              size="sm"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {deleting ? 'Deleting...' : `Delete Selected (${selectedWorkItems.length})`}
            </Button>
          </div>
        </CardTitle>
        
        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            {error}
          </div>
        )}
      </CardHeader>
      
      <CardContent className="space-y-3">
        {loading && (
          <div className="text-center py-4">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto" />
            <p className="mt-2 text-sm text-muted-foreground dark:text-muted-foreground">Loading work items...</p>
          </div>
        )}

        {!loading && allWorkItems.length === 0 && (
          <div className="text-center py-8 text-muted-foreground dark:text-muted-foreground">
            No work items found for this project.
          </div>
        )}

        {!loading && allWorkItems.length > 0 && (
          <div className="space-y-2">
            {allWorkItems.map((workItem, index) => (
              <div
                key={workItem.id}
                className={`p-3 border rounded-xl cursor-pointer transition-colors ${
                  selectedWorkItems.includes(workItem.id)
                    ? 'bg-saramsa-brand/10 border-saramsa-brand/20 dark:bg-saramsa-brand/20 dark:border-saramsa-brand/30'
                    : 'bg-secondary/40 border-border/60 dark:bg-card/95 dark:border-border/60 hover:bg-accent/60 dark:hover:bg-accent/60'
                }`}
                onClick={() => toggleWorkItemSelection(workItem.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Checkbox
                        checked={selectedWorkItems.includes(workItem.id)}
                        onCheckedChange={() => toggleWorkItemSelection(workItem.id)}
                        className="border-border/60"
                      />
                      <Badge variant="outline">#{index + 1}</Badge>
                      <Badge className={`text-xs ${
                        workItem.type === 'Bug' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                        workItem.type === 'Feature' ? 'bg-saramsa-brand/10 text-saramsa-brand dark:bg-saramsa-brand/20 dark:text-saramsa-brand' :
                        workItem.type === 'Task' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                        'bg-secondary/60 text-foreground dark:bg-secondary/50 dark:text-foreground'
                      }`}>
                        {workItem.type}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {workItem.priority}
                      </Badge>
                    </div>
                    
                    <div className="text-sm font-medium mb-1">{workItem.title}</div>
                    <div className="text-xs text-muted-foreground dark:text-muted-foreground mb-2">
                      {workItem.description}
                    </div>
                    
                    <div className="text-xs text-muted-foreground dark:text-muted-foreground">
                      <div><strong>Work Item ID:</strong> <code className="bg-secondary/60 dark:bg-secondary/40 px-1 rounded">{workItem.id}</code></div>
                      <div><strong>User Story:</strong> <code className="bg-secondary/60 dark:bg-secondary/40 px-1 rounded">{workItem.userStoryId}</code></div>
                      <div><strong>Feature Area:</strong> {workItem.featurearea || 'N/A'}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-4 text-xs text-muted-foreground dark:text-muted-foreground bg-secondary/40 dark:bg-card/95 p-3 rounded">
          <div className="font-medium mb-1">API Call Preview:</div>
          <div className="font-mono">POST /api/insights/user-stories/delete-items/</div>
          <div className="font-mono mt-1">
            Body: {JSON.stringify({
              ids: selectedWorkItems,
              user_story_id: allWorkItems.find(item => selectedWorkItems.includes(item.id))?.userStoryId || 'N/A',
              type: 'work_items'
            }, null, 2)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}



