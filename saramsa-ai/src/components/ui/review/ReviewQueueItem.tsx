'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Edit2, X, Clock, GitMerge, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import type { ReviewCandidate } from '@/store/features/review/reviewSlice';

interface ReviewQueueItemProps {
  candidate: ReviewCandidate;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
  onApprove: (id: string) => void;
  onEdit: (candidate: ReviewCandidate) => void;
  onDismiss: (id: string, reason: string) => void;
  onSnooze: (id: string, days: number) => void;
  onMerge?: (id: string) => void;
}

const priorityConfig: Record<string, { color: string; label: string }> = {
  critical: { color: 'bg-red-500 text-white', label: 'P0' },
  high: { color: 'bg-orange-500 text-white', label: 'P1' },
  medium: { color: 'bg-yellow-500 text-white', label: 'P2' },
  low: { color: 'bg-gray-400 text-white', label: 'P3' },
};

const dismissReasons = [
  { value: 'not_relevant', label: 'Not relevant' },
  { value: 'already_known', label: 'Already known' },
  { value: 'will_not_fix', label: 'Will not fix' },
  { value: 'duplicate', label: 'Duplicate' },
];

const snoozeOptions = [
  { days: 7, label: '1 week' },
  { days: 14, label: '2 weeks' },
  { days: 30, label: '1 month' },
];

export function ReviewQueueItem({
  candidate,
  isSelected,
  onToggleSelect,
  onApprove,
  onEdit,
  onDismiss,
  onSnooze,
}: ReviewQueueItemProps) {
  const [showDismiss, setShowDismiss] = useState(false);
  const [showSnooze, setShowSnooze] = useState(false);
  const prio = priorityConfig[candidate.priority] || priorityConfig.low;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100, height: 0 }}
      transition={{ duration: 0.25 }}
      className="group rounded-xl border border-border/60 bg-card/80 hover:bg-card p-4 transition-colors"
    >
      <div className="flex items-start gap-3">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggleSelect(candidate.id)}
          className="mt-1"
        />

        <span className={`px-2 py-0.5 rounded text-xs font-bold ${prio.color} shrink-0 mt-0.5`}>
          {prio.label}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground truncate">{candidate.title}</h3>
            {candidate.feature_area && (
              <Badge variant="secondary" className="text-xs shrink-0">
                {candidate.feature_area}
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
            {candidate.description}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {candidate.comment_count != null && candidate.comment_count > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <MessageSquare className="w-3 h-3" />
              {candidate.comment_count}
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            {new Date(candidate.createdAt).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 mt-3 ml-10">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onApprove(candidate.id)}
          className="text-green-600 border-green-200 hover:bg-green-50 dark:text-green-400 dark:border-green-800 dark:hover:bg-green-900/20"
        >
          <Check className="w-3.5 h-3.5 mr-1" />
          Approve
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={() => onEdit(candidate)}
          className="text-blue-600 border-blue-200 hover:bg-blue-50 dark:text-blue-400 dark:border-blue-800 dark:hover:bg-blue-900/20"
        >
          <Edit2 className="w-3.5 h-3.5 mr-1" />
          Edit
        </Button>

        <div className="relative">
          <Button
            size="sm"
            variant="outline"
            onClick={() => { setShowDismiss(!showDismiss); setShowSnooze(false); }}
            className="text-gray-600 dark:text-gray-400"
          >
            <X className="w-3.5 h-3.5 mr-1" />
            Dismiss
          </Button>
          {showDismiss && (
            <div className="absolute top-full left-0 mt-1 z-20 w-44 rounded-lg border border-border/60 bg-popover shadow-md py-1">
              {dismissReasons.map((r) => (
                <button
                  key={r.value}
                  onClick={() => { onDismiss(candidate.id, r.value); setShowDismiss(false); }}
                  className="w-full text-left px-3 py-1.5 text-sm hover:bg-accent transition-colors"
                >
                  {r.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="relative">
          <Button
            size="sm"
            variant="outline"
            onClick={() => { setShowSnooze(!showSnooze); setShowDismiss(false); }}
            className="text-yellow-600 dark:text-yellow-400"
          >
            <Clock className="w-3.5 h-3.5 mr-1" />
            Snooze
          </Button>
          {showSnooze && (
            <div className="absolute top-full left-0 mt-1 z-20 w-36 rounded-lg border border-border/60 bg-popover shadow-md py-1">
              {snoozeOptions.map((o) => (
                <button
                  key={o.days}
                  onClick={() => { onSnooze(candidate.id, o.days); setShowSnooze(false); }}
                  className="w-full text-left px-3 py-1.5 text-sm hover:bg-accent transition-colors"
                >
                  {o.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
