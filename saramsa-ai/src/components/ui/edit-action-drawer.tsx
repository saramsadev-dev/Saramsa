'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, Trash2, ExternalLink } from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { Textarea } from './textarea';
import { Label } from './label';
import { Badge } from './badge';

interface ActionItem {
  id: string;
  title: string;
  description: string;
  acceptance?: string;
  isCompleted?: boolean;
  featureId?: string;
  type: 'feature' | 'bug' | 'change';
  priority: 'low' | 'medium' | 'high' | 'critical';
  tags?: string[];
  status: 'todo' | 'in_progress' | 'done';
  createdAt: string;
  updatedAt: string;
  assignee?: string;
  dueDate?: string;
}

interface EditActionDrawerProps {
  action: ActionItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (action: ActionItem) => void;
}

export const EditActionDrawer = ({ action, isOpen, onClose, onSave }: EditActionDrawerProps) => {
  const [formData, setFormData] = useState<ActionItem | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (action) {
      setFormData({ ...action });
      setHasChanges(false);
    }
  }, [action]);

  const handleInputChange = (field: keyof ActionItem, value: string) => {
    if (!formData) return;
    
    setFormData(prev => ({
      ...prev!,
      [field]: value
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    if (!formData) return;
    onSave(formData);
    setHasChanges(false);
  };

  const handleCancel = () => {
    if (hasChanges) {
      const confirmClose = window.confirm("You have unsaved changes. Are you sure you want to close?");
      if (!confirmClose) return;
    }
    onClose();
  };

  if (!action || !formData) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleCancel}
            className="fixed inset-0 bg-black/50 z-40"
          />
          
          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-card/95 dark:bg-background shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-border/60 dark:border-border/60 bg-secondary/40 dark:bg-card/95">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-semibold text-foreground dark:text-foreground">
                    Edit Action
                  </h2>
                  {hasChanges && (
                    <Badge variant="secondary" className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">
                      Unsaved changes
                    </Badge>
                  )}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancel}
                  className="text-muted-foreground hover:text-muted-foreground dark:text-muted-foreground dark:hover:text-foreground"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Action Title */}
                <div className="space-y-2">
                  <Label htmlFor="title" className="text-sm font-medium">
                    Action Title
                  </Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="Enter action title"
                    className="flex-1"
                  />
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description" className="text-sm font-medium">
                    Description
                  </Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Enter detailed description"
                    rows={4}
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground dark:text-muted-foreground">
                    Provide a clear description of what needs to be done
                  </p>
                </div>

                {/* Acceptance Criteria */}
                <div className="space-y-2">
                  <Label htmlFor="acceptance" className="text-sm font-medium">
                    Acceptance Criteria
                  </Label>
                  <Textarea
                    id="acceptance"
                    value={formData.acceptance || ''}
                    onChange={(e) => handleInputChange('acceptance', e.target.value)}
                    placeholder="Define acceptance criteria"
                    rows={4}
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground dark:text-muted-foreground">
                    Specify the conditions that must be met for this action to be accepted
                  </p>
                </div>
              </div>

              {/* Footer Actions */}
              <div className="flex items-center justify-between p-6 border-t border-border/60 dark:border-border/60 bg-secondary/40 dark:bg-card/95">
                <Button
                  variant="outline"
                  onClick={() => console.log('Delete action:', formData.id)}
                  className="text-red-600 border-red-200 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/20"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Action
                </Button>

                <div className="flex items-center gap-3">
                  <Button
                    variant="outline"
                    onClick={handleCancel}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={!hasChanges}
                    className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}; 