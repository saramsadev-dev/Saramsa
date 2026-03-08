import React from 'react';
import { Clock } from '@/components/ui/no-icons';

interface DurationBadgeProps {
  durationMs?: number;
  size?: 'sm' | 'md';
}

export const DurationBadge: React.FC<DurationBadgeProps> = ({ durationMs, size = 'md' }) => {
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  };

  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  if (durationMs == null) {
    return (
      <div className="flex items-center gap-1 text-sm font-medium text-blue-500">
        <Clock className={`${iconSize} text-blue-500`} />
        <span>—</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 text-sm font-medium text-blue-500">
      <Clock className={`${iconSize} text-blue-500`} />
      <span>{formatDuration(durationMs)}</span>
    </div>
  );
};
