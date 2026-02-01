'use client';

import { useState } from 'react';
import { Button } from './button';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { Trash2 } from 'lucide-react';
import { apiRequest } from '@/lib/apiRequest';

interface WorkItemDeleteTestProps {
  userStoryData: {
    id: string;
    userId: string;
    work_items: Array<{
      id: string;
      title: string;
      type: string;
      priority: string;
    }>;
  };
}

export function WorkItemDeleteTest({ userStoryData }: WorkItemDeleteTestProps) {
  const [selectedWorkItems, setSelectedWorkItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

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

    if (!confirm(`Delete ${selectedWorkItems.length} work items?`)) {
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      // Test the API call directly using PUT method (correct for updates)
      const response = await apiRequest('put', '/insights/user-stories/remove-work-items/', {
        ids: selectedWorkItems,
        user_story_id: userStoryData.id  // Required: specify which user story
      }, true);

      setResult({
        success: true,
        data: response.data
      });
      
      console.log('Delete response:', response.data);
    } catch (error: any) {
      setResult({
        success: false,
        error: error.response?.data || error.message
      });
      
      console.error('Delete error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Work Item Delete Test</CardTitle>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <div><strong>User Story ID:</strong> {userStoryData.id}</div>
          <div><strong>User ID:</strong> {userStoryData.userId}</div>
          <div><strong>Total Work Items:</strong> {userStoryData.work_items.length}</div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-sm">
            Selected: {selectedWorkItems.length} work items
          </div>
          <Button
            onClick={handleDeleteSelected}
            disabled={loading || selectedWorkItems.length === 0}
            variant="destructive"
            size="sm"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            {loading ? 'Deleting...' : `Delete Selected (${selectedWorkItems.length})`}
          </Button>
        </div>

        <div className="space-y-2">
          {userStoryData.work_items.map((workItem, index) => (
            <div
              key={workItem.id}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedWorkItems.includes(workItem.id)
                  ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                  : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
              onClick={() => toggleWorkItemSelection(workItem.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <input
                      type="checkbox"
                      checked={selectedWorkItems.includes(workItem.id)}
                      onChange={() => toggleWorkItemSelection(workItem.id)}
                      className="rounded"
                    />
                    <Badge variant="outline">#{index + 1}</Badge>
                    <Badge className={`text-xs ${
                      workItem.type === 'Bug' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                      workItem.type === 'Feature' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400' :
                      workItem.type === 'Task' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                      'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
                    }`}>
                      {workItem.type}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {workItem.priority}
                    </Badge>
                  </div>
                  
                  <div className="text-sm font-medium">{workItem.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1">
                    ID: {workItem.id}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {result && (
          <div className={`p-4 rounded-lg border-2 ${
            result.success 
              ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300 dark:from-green-900/20 dark:to-emerald-900/20 dark:border-green-600'
              : 'bg-gradient-to-r from-red-50 to-rose-50 border-red-300 dark:from-red-900/20 dark:to-rose-900/20 dark:border-red-600'
          }`}>
            <div className="flex items-center gap-2 font-medium mb-2">
              {result.success ? (
                <>
                  <span className="text-2xl">✅</span>
                  <span className="text-green-800 dark:text-green-300">Success</span>
                </>
              ) : (
                <>
                  <span className="text-2xl">❌</span>
                  <span className="text-red-800 dark:text-red-300">Error</span>
                </>
              )}
            </div>
            <pre className="text-xs overflow-auto bg-white/50 dark:bg-black/20 p-2 rounded border">
              {JSON.stringify(result.success ? result.data : result.error, null, 2)}
            </pre>
          </div>
        )}

        <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 p-3 rounded">
          <div className="font-medium mb-1">API Call Preview:</div>
          <div className="font-mono">
            PUT /api/insights/user-stories/remove-work-items/ (UPDATE operation)
          </div>
          <div className="font-mono mt-1">
            Body: {JSON.stringify({
              ids: selectedWorkItems,
              user_story_id: userStoryData.id
            }, null, 2)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
