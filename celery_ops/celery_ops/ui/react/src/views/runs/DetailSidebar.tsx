import React, { useState } from 'react';
import { Task, TaskExecution } from '../../types';

interface DetailSidebarProps {
  task: Task;
  execution: TaskExecution | null;
}

type TabType = 'overview' | 'detail' | 'context' | 'metadata';

export const DetailSidebar: React.FC<DetailSidebarProps> = ({ task, execution }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return 'Not started';
    return new Date(timestamp * 1000).toLocaleString();
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  };

  const addLineNumbers = (json: string) => {
    return json.split('\n').map((line, i) => (
      <div key={i} className="flex">
        <span className="text-fg-dim select-none inline-block w-8 text-right mr-4 opacity-60">
          {i + 1}
        </span>
        <span>{line}</span>
      </div>
    ));
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        const statusColor = task.state === 'SUCCESS' ? '#28bf5c' : 
                           task.state === 'FAILURE' ? '#ef4444' : 
                           task.state === 'STARTED' || task.state === 'RETRY' ? '#3b82f6' : '#6b7280';
        
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-fg-dim uppercase tracking-wide mb-3">
                Task Information
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-fg-muted">Status:</span>
                  <span style={{ color: statusColor }} className="font-medium">
                    {task.state}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">Started:</span>
                  <span className="text-fg-secondary">
                    {formatTimestamp(task.started_at)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">Duration:</span>
                  <span className="text-blue-500 font-medium">
                    {formatDuration(task.runtime_ms)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">Worker:</span>
                  <span className="text-fg-secondary font-mono text-sm">
                    {task.worker || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">Queue:</span>
                  <span className="text-fg-secondary">
                    {task.queue || 'default'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        );

      case 'detail':
        const payload = task.kwargs || task.args || task;
        const json = JSON.stringify(payload, null, 2);
        return (
          <pre className="text-xs leading-relaxed text-fg-secondary bg-bg border border-border rounded-md p-3 overflow-auto font-mono">
            {addLineNumbers(json)}
          </pre>
        );

      case 'context':
        const context = {
          task_id: task.task_id,
          task_name: task.task_name,
          worker: task.worker,
          queue: task.queue,
          state: task.state,
          retries: task.retries || 0,
          started_at: task.started_at,
          runtime_ms: task.runtime_ms
        };
        const contextJson = JSON.stringify(context, null, 2);
        return (
          <pre className="text-xs leading-relaxed text-fg-secondary bg-bg border border-border rounded-md p-3 overflow-auto font-mono">
            {addLineNumbers(contextJson)}
          </pre>
        );

      case 'metadata':
        const meta = { ...task };
        delete (meta as any).args;
        delete (meta as any).kwargs;
        const metaJson = JSON.stringify(meta, null, 2);
        return (
          <pre className="text-xs leading-relaxed text-fg-secondary bg-bg border border-border rounded-md p-3 overflow-auto font-mono">
            {addLineNumbers(metaJson)}
          </pre>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-border bg-bg-elevated px-4">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'detail', label: 'Detail' },
          { id: 'context', label: 'Context' },
          { id: 'metadata', label: 'Metadata' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`px-4 py-3 text-xs font-medium border-b-2 -mb-px transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'text-accent border-b-accent'
                : 'text-fg-muted border-b-transparent hover:text-fg-secondary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Content */}
      <div className="flex-1 p-5 overflow-y-auto bg-bg-elevated">
        {renderTabContent()}
      </div>
    </div>
  );
};