import React from 'react';
import { Task, TaskExecution } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';

interface ExecutionTimelineProps {
  task: Task;
  execution: TaskExecution | null;
  loading: boolean;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ 
  task, 
  execution, 
  loading 
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        <span className="ml-3 text-fg-muted">Loading...</span>
      </div>
    );
  }

  const progressPercentage = execution?.progress_percentage || 0;
  const statusClass = task.state === 'SUCCESS' ? 'bg-success' : 
                     task.state === 'FAILURE' ? 'bg-error' : 'bg-accent';

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <div className="w-5 h-5 rounded-full flex items-center justify-center bg-success">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
        );
      case 'FAILURE':
        return (
          <div className="w-5 h-5 bg-error rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </div>
        );
      case 'RUNNING':
        return (
          <div className="w-5 h-5 bg-accent rounded-full flex items-center justify-center animate-spin">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-5 h-5 bg-fg-dim rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10"/>
            </svg>
          </div>
        );
    }
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-fg mb-5 tracking-tight">
        Execution Timeline
      </h2>
      
      {/* Progress Bar */}
      <div className="mb-7">
        <h3 className="text-xs font-semibold text-fg-secondary mb-3 uppercase tracking-wide">
          Progress
        </h3>
        <div className="flex items-center gap-3 mb-1.5">
          <div className="flex-1 h-1 bg-bg-elevated border border-border-subtle rounded-sm overflow-hidden">
            <div 
              className={`h-full ${statusClass} transition-all duration-500 ease-out rounded-sm`}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-fg-muted font-mono min-w-[35px]">
            {Math.round(progressPercentage)}%
          </span>
        </div>
      </div>
      
      {/* Timeline Steps */}
      <div className="space-y-0.5">
        {execution?.steps?.map((step, index) => (
          <div
            key={step.step_id}
            className="flex items-start gap-3 p-3 rounded-md hover:bg-bg-elevated cursor-pointer transition-colors border border-transparent hover:border-border"
          >
            <div className="flex-shrink-0 mt-0.5">
              {getStepIcon(step.status)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-fg truncate">
                  {step.name}
                </h4>
                {step.duration_ms && (
                  <span className="text-xs text-accent font-mono ml-2 font-medium">
                    {formatDuration(step.duration_ms)}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs font-medium ${
                  step.status === 'SUCCESS' ? 'text-success' :
                  step.status === 'FAILURE' ? 'text-error' :
                  step.status === 'RUNNING' ? 'text-accent' : 'text-fg-dim'
                }`}>
                  {step.status}
                </span>
                {step.error && (
                  <span className="text-xs text-error">• Error</span>
                )}
              </div>
            </div>
          </div>
        )) || (
          <div className="text-fg-muted text-sm py-4">
            No execution steps available
          </div>
        )}
      </div>
    </div>
  );
};