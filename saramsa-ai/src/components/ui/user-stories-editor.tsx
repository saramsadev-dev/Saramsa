'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Edit, Save, X, Plus, Trash2, Send, ExternalLink } from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { Textarea } from './textarea';
import { Label } from './label';
import { Badge } from './badge';
import { Card, CardContent } from './card';

interface UserStory {
  id: string;
  type: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  tags?: string[];
  acceptance_criteria?: string;
  business_value?: string;
  effort_estimate?: string;
  feature_area: string;
  status?: 'draft' | 'ready' | 'pushed';
}

interface UserStoriesEditorProps {
  userStories: UserStory[];
  onSave: (stories: UserStory[]) => void;
  onPushToITSM: (stories: UserStory[]) => void;
  platform: 'azure' | 'jira';
  isLoading?: boolean;
}

export function UserStoriesEditor({ 
  userStories, 
  onSave, 
  onPushToITSM, 
  platform,
  isLoading = false 
}: UserStoriesEditorProps) {
  const [editingStories, setEditingStories] = useState<UserStory[]>([]);
  const [selectedStories, setSelectedStories] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setEditingStories([...userStories]);
    setHasChanges(false);
  }, [userStories]);

  const handleStoryUpdate = (id: string, field: keyof UserStory, value: string | string[]) => {
    setEditingStories(prev => 
      prev.map(story => 
        story.id === id 
          ? { ...story, [field]: value, status: 'draft' as const }
          : story
      )
    );
    setHasChanges(true);
  };

  const handleAddStory = () => {
    const newStory: UserStory = {
      id: `story_${Date.now()}`,
      type: 'User Story',
      title: 'New User Story',
      description: 'Enter description here',
      priority: 'medium',
      tags: [],
      acceptance_criteria: '',
      business_value: '',
      effort_estimate: '3',
      feature_area: 'General',
      status: 'draft'
    };
    
    setEditingStories(prev => [...prev, newStory]);
    setEditingId(newStory.id);
    setHasChanges(true);
  };

  const handleDeleteStory = (id: string) => {
    if (confirm('Are you sure you want to delete this user story?')) {
      setEditingStories(prev => prev.filter(story => story.id !== id));
      setSelectedStories(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
      setHasChanges(true);
    }
  };

  const handleSelectStory = (id: string) => {
    setSelectedStories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedStories.size === editingStories.length) {
      setSelectedStories(new Set());
    } else {
      setSelectedStories(new Set(editingStories.map(story => story.id)));
    }
  };

  const handleSave = () => {
    onSave(editingStories);
    setHasChanges(false);
  };

  const handlePushSelected = () => {
    const selectedStoriesData = editingStories.filter(story => selectedStories.has(story.id));
    if (selectedStoriesData.length === 0) {
      alert('Please select at least one user story to push.');
      return;
    }
    onPushToITSM(selectedStoriesData);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pushed': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'ready': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'draft': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  if (editingStories.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 text-gray-400">
          📝
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No User Stories Generated
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          User stories will appear here after analysis is complete.
        </p>
        <Button onClick={handleAddStory} className="bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white">
          <Plus className="w-4 h-4 mr-2" />
          Add User Story
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            User Stories Editor
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Edit and manage user stories before pushing to {platform === 'azure' ? 'Azure DevOps' : 'Jira'}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {hasChanges && (
            <Badge variant="secondary" className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">
              Unsaved changes
            </Badge>
          )}
          
          <Button
            onClick={handleAddStory}
            variant="outline"
            size="sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Story
          </Button>
          
          {hasChanges && (
            <Button
              onClick={handleSave}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          )}
        </div>
      </div>

      {/* Bulk Actions */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={selectedStories.size === editingStories.length && editingStories.length > 0}
            onChange={handleSelectAll}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {selectedStories.size} of {editingStories.length} selected
          </span>
        </div>
        
        {selectedStories.size > 0 && (
          <Button
            onClick={handlePushSelected}
            disabled={isLoading}
            className="bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white"
          >
            <Send className="w-4 h-4 mr-2" />
            Push to {platform === 'azure' ? 'Azure DevOps' : 'Jira'} ({selectedStories.size})
          </Button>
        )}
      </div>

      {/* User Stories List */}
      <div className="space-y-4">
        {editingStories.map((story, index) => (
          <motion.div
            key={story.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
          >
            <Card className="border border-gray-200 dark:border-gray-700">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  {/* Selection Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedStories.has(story.id)}
                    onChange={() => handleSelectStory(story.id)}
                    className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  
                  {/* Story Content */}
                  <div className="flex-1 space-y-4">
                    {editingId === story.id ? (
                      /* Edit Mode */
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor={`title-${story.id}`}>Title</Label>
                            <Input
                              id={`title-${story.id}`}
                              value={story.title}
                              onChange={(e) => handleStoryUpdate(story.id, 'title', e.target.value)}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <Label htmlFor={`priority-${story.id}`}>Priority</Label>
                            <select
                              id={`priority-${story.id}`}
                              value={story.priority}
                              onChange={(e) => handleStoryUpdate(story.id, 'priority', e.target.value)}
                              className="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            >
                              <option value="low">Low</option>
                              <option value="medium">Medium</option>
                              <option value="high">High</option>
                              <option value="critical">Critical</option>
                            </select>
                          </div>
                        </div>
                        
                        <div>
                          <Label htmlFor={`description-${story.id}`}>Description</Label>
                          <Textarea
                            id={`description-${story.id}`}
                            value={story.description}
                            onChange={(e) => handleStoryUpdate(story.id, 'description', e.target.value)}
                            rows={3}
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor={`acceptance-${story.id}`}>Acceptance Criteria</Label>
                          <Textarea
                            id={`acceptance-${story.id}`}
                            value={story.acceptance_criteria || ''}
                            onChange={(e) => handleStoryUpdate(story.id, 'acceptance_criteria', e.target.value)}
                            rows={2}
                            className="mt-1"
                          />
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Button
                            onClick={() => setEditingId(null)}
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <Save className="w-4 h-4 mr-2" />
                            Done
                          </Button>
                          <Button
                            onClick={() => setEditingId(null)}
                            variant="outline"
                            size="sm"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      /* View Mode */
                      <div className="space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                              {story.title}
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400 mt-1">
                              {story.description}
                            </p>
                          </div>
                          
                          <div className="flex items-center gap-2 ml-4">
                            <Badge className={getPriorityColor(story.priority)}>
                              {story.priority}
                            </Badge>
                            <Badge className={getStatusColor(story.status || 'draft')}>
                              {story.status || 'draft'}
                            </Badge>
                          </div>
                        </div>
                        
                        {story.acceptance_criteria && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              Acceptance Criteria:
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {story.acceptance_criteria}
                            </p>
                          </div>
                        )}
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                            <span>Feature: {story.feature_area}</span>
                            {story.effort_estimate && (
                              <span>Effort: {story.effort_estimate}</span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Button
                              onClick={() => setEditingId(story.id)}
                              variant="outline"
                              size="sm"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteStory(story.id)}
                              variant="outline"
                              size="sm"
                              className="text-red-600 border-red-200 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/20"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}