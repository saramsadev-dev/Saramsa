'use client';

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchReviewStats } from '@/store/features/review/reviewSlice';

interface ReviewQueueStatsProps {
  projectId: string;
}

const statCards = [
  { key: 'pending' as const, label: 'Pending', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' },
  { key: 'approved_this_week' as const, label: 'Approved this week', color: 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' },
  { key: 'dismissed_this_week' as const, label: 'Dismissed this week', color: 'bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400' },
  { key: 'snoozed' as const, label: 'Snoozed', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' },
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
          className="rounded-xl border border-border/60 bg-card/80 p-4 flex flex-col items-center justify-center gap-1"
        >
          {statsLoading ? (
            <div className="h-8 w-12 bg-secondary/60 animate-pulse rounded" />
          ) : (
            <span className={`text-2xl font-bold px-3 py-0.5 rounded-full ${color}`}>
              {stats?.[key] ?? 0}
            </span>
          )}
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
      ))}
    </div>
  );
}
