'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import type { ReviewCandidate } from '@/store/features/review/reviewSlice';

interface EditCandidateDrawerProps {
  candidate: ReviewCandidate | null;
  isOpen: boolean;
  onClose: () => void;
  onSaveApprove: (candidate: ReviewCandidate, edits: Record<string, any>) => void;
  onSaveDraft: (candidateId: string, updates: Record<string, any>) => void;
}

const priorityOptions = [
  { value: 'critical', label: 'P0 / Critical' },
  { value: 'high', label: 'P1 / High' },
  { value: 'medium', label: 'P2 / Medium' },
  { value: 'low', label: 'P3 / Low' },
];

const typeOptions = [
  { value: 'bug', label: 'Bug' },
  { value: 'feature', label: 'Feature' },
  { value: 'task', label: 'Task' },
];

export function EditCandidateDrawer({
  candidate,
  isOpen,
  onClose,
  onSaveApprove,
  onSaveDraft,
}: EditCandidateDrawerProps) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'medium',
    type: 'feature',
    feature_area: '',
    acceptance_criteria: '',
    tags: '' as string,
  });
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (candidate) {
      setForm({
        title: candidate.title || '',
        description: candidate.description || '',
        priority: candidate.priority || 'medium',
        type: candidate.type || 'feature',
        feature_area: candidate.feature_area || '',
        acceptance_criteria: candidate.acceptance_criteria || '',
        tags: (candidate.tags || []).join(', '),
      });
      setHasChanges(false);
    }
  }, [candidate]);

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const getEdits = () => ({
    title: form.title,
    description: form.description,
    priority: form.priority,
    type: form.type,
    feature_area: form.feature_area,
    acceptance_criteria: form.acceptance_criteria,
    tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
  });

  const handleCancel = () => {
    if (hasChanges && !window.confirm('You have unsaved changes. Close anyway?')) return;
    onClose();
  };

  if (!candidate) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleCancel}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[900]"
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-background border-l border-border/60 shadow-2xl z-[1000] overflow-hidden"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-border/60 bg-background/60">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-semibold text-foreground">Edit Work Item</h2>
                  {hasChanges && (
                    <Badge className="bg-saramsa-brand/10 text-saramsa-brand border border-saramsa-brand/20">
                      Unsaved Changes
                    </Badge>
                  )}
                </div>
                <Button variant="ghost" size="sm" onClick={handleCancel} className="hover:bg-accent">
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Form */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                <div className="space-y-1.5">
                  <Label htmlFor="ed-title">Title</Label>
                  <Input id="ed-title" value={form.title} onChange={(e) => update('title', e.target.value)} />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ed-desc">Description</Label>
                  <Textarea id="ed-desc" value={form.description} onChange={(e) => update('description', e.target.value)} rows={4} className="resize-none" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="ed-priority">Priority</Label>
                    <select
                      id="ed-priority"
                      value={form.priority}
                      onChange={(e) => update('priority', e.target.value)}
                      className="w-full rounded-lg border border-border/60 bg-background/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-saramsa-brand/20"
                    >
                      {priorityOptions.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="ed-type">Type</Label>
                    <select
                      id="ed-type"
                      value={form.type}
                      onChange={(e) => update('type', e.target.value)}
                      className="w-full rounded-lg border border-border/60 bg-background/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-saramsa-brand/20"
                    >
                      {typeOptions.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ed-area">Feature Area</Label>
                  <Input id="ed-area" value={form.feature_area} onChange={(e) => update('feature_area', e.target.value)} />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ed-ac">Acceptance Criteria</Label>
                  <Textarea id="ed-ac" value={form.acceptance_criteria} onChange={(e) => update('acceptance_criteria', e.target.value)} rows={4} className="resize-none" />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ed-tags">Tags (comma-separated)</Label>
                  <Input id="ed-tags" value={form.tags} onChange={(e) => update('tags', e.target.value)} />
                </div>

                {/* Evidence (read-only) */}
                {candidate.evidence && candidate.evidence.length > 0 && (
                  <div className="space-y-1.5">
                    <Label>Supporting Evidence</Label>
                    <div className="space-y-2 rounded-xl border border-border/60 bg-background/40 p-4">
                      {candidate.evidence.map((ev, i) => (
                        <div key={i} className="text-sm">
                          <p className="text-muted-foreground italic">&ldquo;{ev.text}&rdquo;</p>
                          <p className="text-xs text-muted-foreground/70 mt-0.5">Source: {ev.source}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 p-6 border-t border-border/60 bg-background/60">
                <Button variant="outline" onClick={handleCancel} className="border-border/70 hover:bg-accent/60">
                  Cancel
                </Button>
                <Button
                  variant="outline"
                  onClick={() => { onSaveDraft(candidate.id, getEdits()); onClose(); }}
                  disabled={!hasChanges}
                  className="border-border/70 hover:bg-accent/60 disabled:opacity-50"
                >
                  <Save className="w-4 h-4 mr-1.5" />
                  Apply Changes
                </Button>
                <Button
                  onClick={() => { onSaveApprove(candidate, getEdits()); onClose(); }}
                  className="bg-saramsa-brand hover:bg-saramsa-brand/90 text-white"
                >
                  <Check className="w-4 h-4 mr-1.5" />
                  Save &amp; Approve
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
