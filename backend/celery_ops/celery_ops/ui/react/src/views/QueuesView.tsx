import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { apiService } from '../services/api';
import { Queue } from '../types';

export const QueuesView: React.FC = () => {
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueues = async () => {
    try {
      const response = await apiService.getQueues();
      setQueues(response.queues || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueues();
    const interval = setInterval(fetchQueues, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Queues" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-fg-dim">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full">
        <Header title="Queues" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-error">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header title="Queues" />
      
      <div className="flex-1 overflow-auto">
        {queues.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <svg className="w-10 h-10 text-fg-dim opacity-30 mx-auto mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
              </svg>
              <div className="text-fg-muted">No queues found</div>
            </div>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-border bg-bg">
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Queue</th>
                <th className="text-left p-4 text-xs font-medium text-fg-dim uppercase tracking-wide">Length</th>
              </tr>
            </thead>
            <tbody>
              {queues.map((queue) => (
                <tr
                  key={queue.name}
                  className="hover:bg-bg-row-hover transition-colors"
                >
                  <td className="p-4 border-b border-border-subtle">
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium bg-purple-bg text-purple rounded">
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <line x1="8" y1="6" x2="21" y2="6"/>
                        <line x1="8" y1="12" x2="21" y2="12"/>
                        <line x1="8" y1="18" x2="21" y2="18"/>
                      </svg>
                      {queue.name}
                    </span>
                  </td>
                  <td className="p-4 border-b border-border-subtle">
                    <span className="text-fg">{queue.length ?? '—'}</span>
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