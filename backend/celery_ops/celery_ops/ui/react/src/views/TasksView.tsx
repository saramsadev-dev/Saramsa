import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { apiService } from '../services/api';
import { TaskType } from '../types';
import { DurationBadge } from '../components/DurationBadge';

export const TasksView: React.FC = () => {
  const [taskTypes, setTaskTypes] = useState<TaskType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchTaskTypes = async () => {
    try {
      const response = await apiService.getTaskTypes();
      let types = response.task_types || [];
      
      // Filter by search query
      if (searchQuery.trim()) {
        types = types.filter(t => 
          t.task_name.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      
      setTaskTypes(types);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch task types');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaskTypes();
  }, [searchQuery]);

  const renderActivityBar = (activity: Array<{ state: string }>) => {
    if (!activity || !activity.length) {
      return <div className="h-5 w-28 bg-bg-elevated rounded"></div>;
    }
    
    const recent = activity.slice(0, 28).reverse();
    return (
      <div className="flex gap-0.5 h-5 items-end">
        {recent.map((a, i) => (
          <div
            key={i}
            className={`w-1 min-h-1 rounded-sm ${
              a.state === 'SUCCESS' ? 'bg-success' :
              a.state === 'FAILURE' ? 'bg-error' : 'bg-fg-dim opacity-40'
            }`}
            style={{ height: `${Math.random() * 16 + 4}px` }}
            title={a.state}
          />
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Tasks" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-fg-dim">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Tasks" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="Tasks" />
      
      {/* Filter Bar */}
      <div className="px-6 py-3 border-b border-border flex items-center gap-2 bg-bg">
        <div className="flex items-center gap-2 bg-bg-elevated border border-border rounded-md px-3 py-1.5 min-w-56">
          <svg className="w-3.5 h-3.5 text-fg-dim" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none outline-none text-fg text-sm flex-1 placeholder-fg-dim"
          />
        </div>
      </div>
      
      {/* Tasks Table */}
      <div className="flex-1 overflow-auto">
        {taskTypes.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <svg className="w-10 h-10 text-fg-dim opacity-30 mx-auto mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <rect x="3" y="3" width="7" height="7" rx="1"/>
                <rect x="14" y="3" width="7" height="7" rx="1"/>
                <rect x="3" y="14" width="7" height="7" rx="1"/>
                <rect x="14" y="14" width="7" height="7" rx="1"/>
              </svg>
              <div className="text-fg-muted">No registered tasks</div>
              <div className="text-xs text-fg-dim">Add Celery tasks to your app</div>
            </div>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-border bg-bg">
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Task</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Running</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Queued</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Activity (recent)</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Duration</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide w-10"></th>
              </tr>
            </thead>
            <tbody>
              {taskTypes.map((taskType) => (
                <tr
                  key={taskType.task_name}
                  className="hover:bg-bg-row-hover cursor-pointer transition-colors"
                >
                  <td className="p-4 border-b border-border-subtle">
                    <span className="font-mono text-fg">{taskType.task_name}</span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <span className="text-fg-secondary">{taskType.running ?? 0}</span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <span className="text-fg-secondary">{taskType.queued ?? 0}</span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    {renderActivityBar(taskType.activity)}
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <DurationBadge durationMs={taskType.avg_duration_ms} />
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <button className="text-fg-dim hover:text-fg-secondary transition-colors">
                      ›
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};