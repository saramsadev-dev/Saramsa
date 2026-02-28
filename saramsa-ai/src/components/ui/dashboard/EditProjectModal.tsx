'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import type { Project } from '@/store/features/projects/projectsSlice';

interface EditProjectModalProps {
  project: Project;
  onClose: () => void;
  onSave: (projectId: string, name: string, description?: string) => void;
  loading?: boolean;
}

export function EditProjectModal({ project, onClose, onSave, loading = false }: EditProjectModalProps) {
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || '');
  const maxDescriptionLength = 100;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onSave(project.id, name.trim(), description.trim() || undefined);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-card/95 rounded-xl shadow-xl max-w-md w-full"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border/60">
            <h2 className="text-xl font-semibold text-foreground">
              Edit Project
            </h2>
            <Button
              onClick={onClose}
              variant="ghost"
              size="icon"
              className="h-8 w-8 hover:bg-accent/60"
              disabled={loading}
            >
              <X className="w-5 h-5 text-muted-foreground" />
            </Button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label htmlFor="project-name" className="block text-sm font-medium text-muted-foreground mb-2">
                Project Name *
              </label>
              <Input
                id="project-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-border/60 rounded-xl bg-background/80 text-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40"
                placeholder="Enter project name"
                required
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="project-description" className="block text-sm font-medium text-muted-foreground mb-2">
                Description
              </label>
              <Textarea
                id="project-description"
                value={description}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value.length <= maxDescriptionLength) {
                    setDescription(value);
                  }
                }}
                rows={3}
                className="w-full px-3 py-2 border border-border/60 rounded-xl bg-background/80 text-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40 resize-none"
                placeholder="Enter project description (optional)"
                disabled={loading}
              />
              <div className="flex justify-end items-center mt-1">
                <p className="text-xs text-muted-foreground">
                  {description.length}/{maxDescriptionLength}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                className="flex-1"
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="saramsa"
                className="flex-1 gap-2"
                disabled={loading || !name.trim()}
              >
                <Save className="w-4 h-4" />
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
