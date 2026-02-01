import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { usePolling } from '../../hooks/usePolling';
import { Task } from '../../types';
import { StatusBadge } from '../../components/StatusBadge';
import { DurationBadge } from '../../components/DurationBadge';

interface RunsListProps {
  searchQuery: string;
  onTaskSelect: (task: Task) => void;
}

export const RunsList: React.FC<RunsListProps> = ({ searchQuery, onTaskSelect }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    try {
      const params: any = { limit: 200 };
      if (searchQuery.trim()) {
        params.task_name = searchQuery.trim();
      }
      
      const response = await apiService.getTasks(params);
      setTasks(response.tasks || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [searchQuery]);

  // Poll for updates every 3 seconds
  usePolling(fetchTasks, 3000, true);

  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return '—';
    
    try {
      const date = new Date(timestamp * 1000);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      }) + ', ' + date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        second: '2-digit', 
        hour12: true 
      });
    } catch {
      return String(timestamp);
    }
  };

  const getRowClassName = (state: string) => {
    const baseClass = "hover:bg-bg-row-hover cursor-pointer transition-colors";
    switch (state.toUpperCase()) {
      case 'SUCCESS':
        return `${baseClass} border-l-3 border-l-success hover:bg-success/5`;
      case 'FAILURE':
        return `${baseClass} border-l-3 border-l-error hover:bg-error/5`;
      case 'STARTED':
      case 'RETRY':
      case 'RECEIVED':
        return `${baseClass} border-l-3 border-l-accent hover:bg-accent/5`;
      case 'REVOKED':
        return `${baseClass} border-l-3 border-l-warning hover:bg-warning/5`;
      default:
        return `${baseClass} border-l-3 border-l-fg-dim`;
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-fg-dim">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-error">{error}</div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <svg className="w-10 h-10 text-fg-dim opacity-30 mx-auto mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <div className="text-fg-muted">No runs yet</div>
          <div className="text-xs text-fg-dim">Run some Celery tasks to see them here</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10">
          <tr className="border-b border-border bg-bg">
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide w-9">
              <input type="checkbox" className="accent-accent" />
            </th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">ID</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Task</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Status</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Worker</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Started</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Duration</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Retries</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Queue</th>
            <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide w-10"></th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr
              key={task.task_id}
              className={getRowClassName(task.state)}
              onClick={() => onTaskSelect(task)}
            >
              <td className="p-4 border-b border-border-subtle">
                <input 
                  type="checkbox" 
                  className="accent-accent" 
                  onClick={(e) => e.stopPropagation()} 
                />
              </td>
              <td className="p-4 border-b border-border-subtle">
                <span className="font-mono text-fg">{task.task_id.slice(0, 8)}</span>
              </td>
              <td className="p-4 border-b border-border-subtle">
                <div className="flex items-center gap-2">
                  <span className="text-fg-secondary">{task.task_name || ''}</span>
                  <span className="px-2 py-0.5 text-xs font-medium bg-purple-bg text-purple rounded">
                    Root
                  </span>
                </div>
              </td>
              <td className="p-4 border-b border-border-subtle">
                <StatusBadge status={task.state} />
              </td>
              <td className="p-4 border-b border-border-subtle">
                <span className="font-mono text-xs text-fg-secondary">{task.worker || ''}</span>
              </td>
              <td className="p-4 border-b border-border-subtle">
                <span className="text-xs text-fg-muted">
                  {formatTimestamp(task.started_at)}
                </span>
              </td>
              <td className="p-4 border-b border-border-subtle">
                <DurationBadge durationMs={task.runtime_ms} />
              </td>
              <td className="p-4 border-b border-border-subtle">
                <span className="text-fg-secondary">{task.retries ?? '—'}</span>
              </td>
              <td className="p-4 border-b border-border-subtle">
                {task.queue ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-purple-bg text-purple rounded">
                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <line x1="8" y1="6" x2="21" y2="6"/>
                      <line x1="8" y1="12" x2="21" y2="12"/>
                      <line x1="8" y1="18" x2="21" y2="18"/>
                    </svg>
                    {task.queue}
                  </span>
                ) : (
                  <span className="text-fg-dim">—</span>
                )}
              </td>
              <td className="p-4 border-b border-border-subtle">
                {task.state === 'SUCCESS' ? (
                  <svg className="w-4 h-4 text-success" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : task.state === 'FAILURE' ? (
                  <svg className="w-4 h-4 text-error" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                ) : (
                  <span className="text-fg-dim">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};