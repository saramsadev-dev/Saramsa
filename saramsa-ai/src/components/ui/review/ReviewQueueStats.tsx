'use client';

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchReviewStats } from '@/store/features/review/reviewSlice';

interface ReviewQueueStatsProps {
  projectId: string;
}

const statCards = [
  { key: 'pending' as const, label: 'Pending', color: 'text-saramsa-brand' },
  { key: 'approved_this_week' as const, label: 'Approved this week', color: 'text-foreground' },
  { key: 'dismissed_this_week' as const, label: 'Dismissed this week', color: 'text-muted-foreground' },
  { key: 'snoozed' as const, label: 'Snoozed', color: 'text-foreground' },
];

export function ReviewQueueStats({ projectId }: ReviewQueueStatsProps) {
  const dispatch = useAppDispatch();
  const { stats, statsLoading } = useAppSelector((s) => s.review);

  useEffect(() => {
    dispatch(fetchReviewStats(projectId));
  }, [dispatch, projectId]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statCards.map(({ key, label, color }) => (
        <div
          key={key}
          className="rounded-2xl border border-border/60 bg-background/40 p-5 flex flex-col items-center justify-center gap-2"
        >
          {statsLoading ? (
            <div className="h-9 w-14 bg-secondary/60 animate-pulse rounded-lg" />
          ) : (
            <span className={`text-3xl font-bold ${color}`}>
              {stats?.[key] ?? 0}
            </span>
          )}
          <span className="text-xs text-muted-foreground text-center">{label}</span>
        </div>
      ))}
    </div>
  );
}
