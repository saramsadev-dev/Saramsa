import React from 'react';
import { Check, X, Clock, AlertCircle, Loader2 } from '@/components/ui/no-icons';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getStatusConfig = (state: string) => {
    const upperState = state.toUpperCase();
    
    switch (upperState) {
      case 'SUCCESS':
        return {
          label: 'Completed',
          icon: Check,
          color: '#28bf5c',
          className: 'status-success'
        };
      case 'FAILURE':
        return {
          label: 'Failed',
          icon: X,
          color: '#ef4444',
          className: 'status-failure'
        };
      case 'STARTED':
      case 'RETRY':
        return {
          label: 'Running',
          icon: Loader2,
          color: '#3b82f6',
          className: 'status-running animate-spin'
        };
      case 'REVOKED':
        return {
          label: 'Cancelled',
          icon: AlertCircle,
          color: '#f59e0b',
          className: 'status-revoked'
        };
      case 'RECEIVED':
        return {
          label: 'Received',
          icon: Clock,
          color: '#6b7280',
          className: 'status-pending'
        };
      default:
        return {
          label: 'Pending',
          icon: Clock,
          color: '#6b7280',
          className: 'status-pending'
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  return (
    <div className="flex items-center gap-2 text-sm font-medium" style={{ color: config.color }}>
      <Icon className={`${iconSize} ${config.className}`} />
      <span>{config.label}</span>
    </div>
  );
};
