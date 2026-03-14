'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save } from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { Textarea } from './textarea';
import { Label } from './label';
import { Badge } from './badge';
import { lockBodyScroll, unlockBodyScroll } from '@/lib/bodyScrollLock';

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
  const modalRoot = typeof document !== 'undefined' ? document.body : null;

  useEffect(() => {
    if (action) {
      setFormData({ ...action });
      setHasChanges(false);
    }
  }, [action]);

  useEffect(() => {
    if (!isOpen || !modalRoot) return;

    const previousDrawerFlag = document.body.getAttribute('data-edit-drawer-open');
    lockBodyScroll();
    document.body.setAttribute('data-edit-drawer-open', 'true');

    const closeWithGuard = () => {
      if (hasChanges) {
        const confirmClose = window.confirm('You have unsaved changes. Are you sure you want to close?');
        if (!confirmClose) return;
      }
      onClose();
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeWithGuard();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      unlockBodyScroll();
      if (previousDrawerFlag === null) {
        document.body.removeAttribute('data-edit-drawer-open');
      } else {
        document.body.setAttribute('data-edit-drawer-open', previousDrawerFlag);
      }
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, modalRoot, hasChanges, onClose]);

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

  if (!action || !formData || !isOpen || !modalRoot) return null;

  return createPortal(
    <AnimatePresence>
      {/* Backdrop */}
      <motion.div
        key="work-item-edit-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[900] bg-[rgba(0,0,0,0.55)]"
        onClick={handleCancel}
      />

      {/* Drawer */}
      <motion.aside
        key="work-item-edit-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Edit work item"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 28, stiffness: 260 }}
        className="fixed top-0 right-0 z-[1000] h-[100vh] w-screen sm:w-[420px] flex flex-col"
        style={{
          background: '#0f0f0f',
          boxShadow: '-10px 0 30px rgba(0,0,0,0.5)',
        }}
        onClick={(event) => event.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/60 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-foreground">Edit Action</h2>
            {hasChanges && (
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">
                Unsaved changes
              </Badge>
            )}
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleCancel}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6 sm:py-6 space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title" className="text-sm font-medium">
              Action Title
            </Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              placeholder="Enter action title"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm font-medium">
              Description
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Enter detailed description"
              rows={5}
              className="resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="acceptance" className="text-sm font-medium">
              Acceptance Criteria
            </Label>
            <Textarea
              id="acceptance"
              value={formData.acceptance || ''}
              onChange={(e) => handleInputChange('acceptance', e.target.value)}
              placeholder="Define acceptance criteria"
              rows={5}
              className="resize-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-auto border-t border-border/60 px-4 py-4 sm:px-6">
          <div className="flex items-center justify-end gap-2 sm:gap-3">
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={!hasChanges}
              className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </div>
        </div>
      </motion.aside>
    </AnimatePresence>
    ,
    modalRoot
  );
};


