import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { StatusBadge } from '../components/StatusBadge';
import { apiService } from '../services/api';
import { Worker } from '../types';

export const WorkersView: React.FC = () => {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkers = async () => {
    try {
      const response = await apiService.getWorkers();
      setWorkers(response.workers || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch workers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Workers" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-fg-dim">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Workers" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="Workers" />
      
      <div className="flex-1 overflow-auto">
        {workers.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <svg className="w-10 h-10 text-fg-dim opacity-30 mx-auto mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
              <div className="text-fg-muted">No workers connected</div>
            </div>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-border bg-bg">
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Worker</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Status</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Active</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Processed</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Queues</th>
              </tr>
            </thead>
            <tbody>
              {workers.map((worker) => (
                <tr
                  key={worker.name}
                  className="hover:bg-bg-row-hover transition-colors"
                >
                  <td className="p-4 border-b border-border-subtle">
                    <span className="font-mono text-fg">{worker.name}</span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <StatusBadge status={worker.status === 'online' ? 'STARTED' : worker.status} />
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <span className="text-fg-secondary">{worker.active ?? '—'}</span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <span className="text-fg-secondary">{worker.processed ?? '—'}</span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <span className="font-mono text-xs text-fg-secondary">
                      {worker.queues?.join(', ') || '—'}
                    </span>
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