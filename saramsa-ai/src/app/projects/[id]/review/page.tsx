'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchCandidates,
  fetchReviewStats,
  approveCandidate,
  dismissCandidate,
  snoozeCandidate,
  batchApprove,
  toggleSelected,
  clearSelected,
  selectAll,
  setFilters,
  type ReviewCandidate,
} from '@/store/features/review/reviewSlice';
import { decryptProjectId, isValidEncryptedId } from '@/lib/encryption';
import { ReviewQueueStats } from '@/components/ui/review/ReviewQueueStats';
import { ReviewQueueItem } from '@/components/ui/review/ReviewQueueItem';
import { EditCandidateDrawer } from '@/components/ui/review/EditCandidateDrawer';
import { Button } from '@/components/ui/button';
import { Check, Inbox } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import { apiRequest } from '@/lib/apiRequest';

export default function ReviewQueuePage() {
  const params = useParams();
  const dispatch = useAppDispatch();
  const { candidates, filters, selectedIds, loading } = useAppSelector((s) => s.review);

  const [projectId, setProjectId] = useState<string | null>(null);
  const [editCandidate, setEditCandidate] = useState<ReviewCandidate | null>(null);

  // Decrypt project ID
  useEffect(() => {
    const encId = params.id as string;
    if (!encId) return;
    try {
      const id = isValidEncryptedId(encId) ? decryptProjectId(encId) : encId;
      setProjectId(id);
    } catch {
      setProjectId(encId);
    }
  }, [params.id]);

  // Fetch data when project ID is ready
  useEffect(() => {
    if (!projectId) return;
    dispatch(fetchCandidates({ projectId, filters }));
    dispatch(fetchReviewStats(projectId));
  }, [dispatch, projectId, filters]);

  const refresh = useCallback(() => {
    if (!projectId) return;
    dispatch(fetchCandidates({ projectId, filters }));
    dispatch(fetchReviewStats(projectId));
  }, [dispatch, projectId, filters]);

  const handleApprove = useCallback((id: string) => {
    if (!projectId) return;
    dispatch(approveCandidate({ candidateId: id, projectId })).then(refresh);
  }, [dispatch, projectId, refresh]);

  const handleDismiss = useCallback((id: string, reason: string) => {
    if (!projectId) return;
    dispatch(dismissCandidate({ candidateId: id, projectId, reason })).then(refresh);
  }, [dispatch, projectId, refresh]);

  const handleSnooze = useCallback((id: string, days: number) => {
    if (!projectId) return;
    dispatch(snoozeCandidate({ candidateId: id, projectId, snoozeDays: days })).then(refresh);
  }, [dispatch, projectId, refresh]);

  const handleBatchApprove = useCallback(() => {
    if (!projectId || selectedIds.length === 0) return;
    dispatch(batchApprove({ candidateIds: selectedIds, projectId })).then(refresh);
  }, [dispatch, projectId, selectedIds, refresh]);

  const handleSaveApprove = useCallback((candidate: ReviewCandidate, edits: Record<string, any>) => {
    if (!projectId) return;
    dispatch(approveCandidate({ candidateId: candidate.id, projectId, edits })).then(refresh);
  }, [dispatch, projectId, refresh]);

  const handleSaveDraft = useCallback(async (candidateId: string, updates: Record<string, any>) => {
    if (!projectId) return;
    await apiRequest('put', '/work-items/review/update/', { candidate_id: candidateId, project_id: projectId, updates }, true);
    refresh();
  }, [projectId, refresh]);

  if (!projectId) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Review Queue</h1>
        <div className="flex items-center gap-2">
          <select
            value={filters.status}
            onChange={(e) => dispatch(setFilters({ status: e.target.value }))}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
          >
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="dismissed">Dismissed</option>
            <option value="snoozed">Snoozed</option>
          </select>
          <select
            value={filters.priority}
            onChange={(e) => dispatch(setFilters({ priority: e.target.value }))}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
          >
            <option value="">All priorities</option>
            <option value="critical">P0 - Critical</option>
            <option value="high">P1 - High</option>
            <option value="medium">P2 - Medium</option>
            <option value="low">P3 - Low</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <ReviewQueueStats projectId={projectId} />

      {/* Batch actions */}
      {selectedIds.length > 0 && (
        <div className="flex items-center gap-3 p-3 rounded-lg border border-primary/30 bg-primary/5">
          <span className="text-sm font-medium">{selectedIds.length} selected</span>
          <Button size="sm" onClick={handleBatchApprove} className="bg-green-600 hover:bg-green-700 text-white">
            <Check className="w-3.5 h-3.5 mr-1" />
            Approve All Selected
          </Button>
          <Button size="sm" variant="ghost" onClick={() => dispatch(clearSelected())}>
            Clear
          </Button>
          <Button size="sm" variant="ghost" onClick={() => dispatch(selectAll())}>
            Select All
          </Button>
        </div>
      )}

      {/* Candidate list */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-secondary/70 animate-pulse dark:bg-secondary/40" />
          ))}
        </div>
      ) : candidates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Inbox className="w-16 h-16 text-muted-foreground/40 mb-4" />
          <h3 className="text-lg font-semibold text-foreground">Your review queue is clear!</h3>
          <p className="text-sm text-muted-foreground mt-1">
            No candidates to review right now. Check back later.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {candidates.map((c) => (
              <ReviewQueueItem
                key={c.id}
                candidate={c}
                isSelected={selectedIds.includes(c.id)}
                onToggleSelect={(id) => dispatch(toggleSelected(id))}
                onApprove={handleApprove}
                onEdit={setEditCandidate}
                onDismiss={handleDismiss}
                onSnooze={handleSnooze}
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Edit drawer */}
      <EditCandidateDrawer
        candidate={editCandidate}
        isOpen={!!editCandidate}
        onClose={() => setEditCandidate(null)}
        onSaveApprove={handleSaveApprove}
        onSaveDraft={handleSaveDraft}
      />
    </div>
  );
}
