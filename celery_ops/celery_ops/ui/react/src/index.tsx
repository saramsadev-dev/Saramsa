import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import { 
  CheckSquare, 
  Play, 
  Monitor, 
  Layers, 
  Check, 
  X, 
  Loader2, 
  Ban, 
  Clock, 
  Search, 
  ArrowLeft 
} from '@/components/ui/no-icons';

// Types
interface Task {
  task_id: string;
  task_name: string;
  state: 'PENDING' | 'RECEIVED' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'REVOKED' | 'RETRY';
  worker?: string;
  queue?: string;
  started_at?: number;
  succeeded_at?: number;
  failed_at?: number;
  received_at?: number;
  runtime_ms?: number;
  retries?: number;
  error?: string;
  args?: any;
  kwargs?: any;
}

// API Service
const api = {
  async getTasks(params?: any) {
    const url = new URL('/api/tasks', window.location.origin);
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined) {
          url.searchParams.append(key, params[key]);
        }
      });
    }
    const response = await fetch(url.toString());
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  async getTask(taskId: string) {
    const response = await fetch(`/api/tasks/${taskId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  async cancelTask(taskId: string) {
    const response = await fetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  async retryTask(taskId: string) {
    const response = await fetch(`/api/tasks/${taskId}/retry`, { method: 'POST' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
};

// Custom Hook for Polling
function usePolling(callback: () => void | Promise<void>, interval: number, enabled: boolean = true) {
  const intervalRef = useRef<number | null>(null);
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    if (enabled) {
      intervalRef.current = window.setInterval(async () => {
        try {
          await callbackRef.current();
        } catch (error) {
          console.warn('Polling error:', error);
        }
      }, interval);
    }
  }, [interval, enabled]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    return stopPolling;
  }, [enabled, startPolling, stopPolling]);

  return { startPolling, stopPolling };
}

// Professional Icons from Lucide React
const Icons = {
  Tasks: CheckSquare,
  Runs: Play,
  Workers: Monitor,
  Queues: Layers,
  Success: Check,
  Failure: X,
  Running: ({ size = 16, className = "" }: { size?: number; className?: string }) => (
    <Loader2 
      size={size} 
      className={`animate-spin ${className}`}
      style={{ animation: 'spin 1s linear infinite' }}
    />
  ),
  Cancelled: Ban,
  Pending: Clock,
  Clock: Clock,
  Search: Search,
  ArrowLeft: ArrowLeft
};
function StatusBadge({ status }: { status: string }) {
  const getStatusConfig = (state: string) => {
    const upperState = state.toUpperCase();
    
    switch (upperState) {
      case 'SUCCESS':
        return { label: 'Completed', color: '#28bf5c', icon: Icons.Success };
      case 'FAILURE':
        return { label: 'Failed', color: '#ef4444', icon: Icons.Failure };
      case 'STARTED':
      case 'RETRY':
        return { label: 'Running', color: '#3b82f6', icon: Icons.Running };
      case 'REVOKED':
        return { label: 'Cancelled', color: '#f59e0b', icon: Icons.Cancelled };
      case 'RECEIVED':
        return { label: 'Received', color: '#6b7280', icon: Icons.Pending };
      default:
        return { label: 'Pending', color: '#6b7280', icon: Icons.Pending };
    }
  };

  const config = getStatusConfig(status);
  const IconComponent = config.icon;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', fontWeight: 500, color: config.color }}>
      {typeof IconComponent === 'function' ? (
        <IconComponent size={16} />
      ) : (
        <IconComponent size={16} />
      )}
      <span>{config.label}</span>
    </div>
  );
}

// Compact Live Duration Component for step timeline
function LiveDurationCompact({ startTime }: { startTime: number }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const updateElapsed = () => {
      const now = Date.now() / 1000;
      const elapsedSeconds = Math.max(0, now - startTime);
      setElapsed(elapsedSeconds);
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const formatElapsed = (seconds: number) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return <span>{formatElapsed(elapsed)}</span>;
}

// Live Duration Component for running tasks
function LiveDuration({ startTime }: { startTime?: number }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;

    const updateElapsed = () => {
      const now = Date.now() / 1000; // Convert to seconds
      const elapsedSeconds = Math.max(0, now - startTime);
      setElapsed(elapsedSeconds);
    };

    // Update immediately
    updateElapsed();

    // Update every second
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const formatElapsed = (seconds: number) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (minutes < 60) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  if (!startTime) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 500, color: '#3b82f6' }}>
        <Icons.Clock size={16} />
        <span>—</span>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 500, color: '#3b82f6' }}>
      <Icons.Clock size={16} />
      <span>{formatElapsed(elapsed)}</span>
    </div>
  );
}

// Duration Badge Component
function DurationBadge({ durationMs, isRunning, startTime }: { 
  durationMs?: number; 
  isRunning?: boolean; 
  startTime?: number; 
}) {
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  };

  // For running tasks, show live duration
  if (isRunning && startTime) {
    return <LiveDuration startTime={startTime} />;
  }

  // For completed tasks, show final duration
  if (durationMs != null) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 500, color: '#3b82f6' }}>
        <Icons.Clock size={16} />
        <span>{formatDuration(durationMs)}</span>
      </div>
    );
  }

  // For tasks without duration info
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 500, color: '#3b82f6' }}>
      <Icons.Clock size={16} />
      <span>—</span>
    </div>
  );
}

// Sidebar Component
function Sidebar({ activeSection, onSectionChange }: { 
  activeSection: string; 
  onSectionChange: (section: string) => void; 
}) {
  const navItems = [
    { id: 'tasks', label: 'Tasks', icon: Icons.Tasks },
    { id: 'runs', label: 'Runs', icon: Icons.Runs },
    { id: 'workers', label: 'Workers', icon: Icons.Workers },
    { id: 'queues', label: 'Queues', icon: Icons.Queues },
  ];

  return (
    <aside style={{ 
      width: '220px', 
      background: '#0a0a0b', 
      borderRight: '1px solid #1f1f23', 
      display: 'flex', 
      flexDirection: 'column',
      height: '100vh'
    }}>
      <div style={{ 
        padding: '16px 12px 10px', 
        borderBottom: '1px solid #1f1f23', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '10px' 
      }}>
        <div style={{ 
          width: '28px', 
          height: '28px', 
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', 
          borderRadius: '6px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          fontWeight: '600', 
          fontSize: '14px', 
          color: 'white' 
        }}>
          Co
        </div>
        <div>
          <div style={{ fontWeight: '600', fontSize: '14px', color: '#fafafa' }}>Celery Ops</div>
          <div style={{ fontSize: '11px', color: '#a1a1aa' }}>Environment: default</div>
        </div>
      </div>
      
      <nav style={{ padding: '12px 0', flex: 1 }}>
        {navItems.map((item) => {
          const isActive = activeSection === item.id;
          const IconComponent = item.icon;
          
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 12px',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                borderLeft: isActive ? '2px solid #3b82f6' : '2px solid transparent',
                background: isActive ? 'rgba(59,130,246,0.08)' : 'transparent',
                color: isActive ? '#fafafa' : '#a1a1aa',
                border: 'none',
                textAlign: 'left',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#e4e4e7';
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#a1a1aa';
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <IconComponent size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      
      <div style={{ 
        padding: '12px', 
        borderTop: '1px solid #1f1f23', 
        fontSize: '11px', 
        color: '#71717a', 
        textAlign: 'center' 
      }}>
        Ops-only, best-effort. <a href="/docs" style={{ color: '#3b82f6' }}>API</a>
      </div>
    </aside>
  );
}

// Header Component
function Header({ title, showBackButton, onBack, rightContent }: {
  title: string;
  showBackButton?: boolean;
  onBack?: () => void;
  rightContent?: React.ReactNode;
}) {
  return (
    <header style={{
      padding: '12px 20px',
      borderBottom: '1px solid #1f1f23',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: '#0a0a0b',
      minHeight: '52px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {showBackButton && onBack ? (
          <button
            onClick={onBack}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'none',
              border: 'none',
              color: '#3b82f6',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              fontFamily: 'inherit'
            }}
          >
            <Icons.ArrowLeft size={16} />
            <span>{title}</span>
          </button>
        ) : (
          <h1 style={{ fontSize: '15px', fontWeight: '600', color: '#fafafa', margin: 0 }}>{title}</h1>
        )}
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {rightContent || (
          <a 
            href="/docs" 
            style={{ 
              fontSize: '12px', 
              color: '#71717a', 
              textDecoration: 'none',
              transition: 'color 0.15s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#a1a1aa'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#71717a'}
          >
            API docs
          </a>
        )}
      </div>
    </header>
  );
}

// Queues List Component
function QueuesList({ searchQuery }: { searchQuery: string }) {
  const [queues, setQueues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueues = useCallback(async () => {
    try {
      const response = await fetch('/api/queues');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      
      let queueList = data.queues || [];
      
      // Filter by search query if provided
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        queueList = queueList.filter((queue: any) => 
          queue.name.toLowerCase().includes(query)
        );
      }
      
      setQueues(queueList);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queues');
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    fetchQueues();
  }, [fetchQueues]);

  // Poll for updates every 3 seconds
  usePolling(fetchQueues, 3000, true);

  const getQueueStatus = (queue: any) => {
    const hasConsumers = queue.consumers > 0;
    const hasPendingTasks = queue.messages > 0;
    
    if (!hasConsumers && hasPendingTasks) {
      return { status: 'warning', label: 'No Consumers', color: '#f59e0b' };
    } else if (hasConsumers && hasPendingTasks) {
      return { status: 'active', label: 'Processing', color: '#3b82f6' };
    } else if (hasConsumers && !hasPendingTasks) {
      return { status: 'idle', label: 'Idle', color: '#28bf5c' };
    } else {
      return { status: 'inactive', label: 'Inactive', color: '#6b7280' };
    }
  };

  const getPriorityBadge = (priority?: number) => {
    if (priority === undefined || priority === null) return null;
    
    let color = '#6b7280';
    let label = 'Normal';
    
    if (priority >= 8) {
      color = '#ef4444';
      label = 'Critical';
    } else if (priority >= 6) {
      color = '#f59e0b';
      label = 'High';
    } else if (priority >= 4) {
      color = '#3b82f6';
      label = 'Normal';
    } else {
      color = '#6b7280';
      label = 'Low';
    }
    
    return { color, label };
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#71717a' }}>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#ef4444' }}>{error}</div>
      </div>
    );
  }

  if (queues.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '40px', opacity: 0.3, marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
            <Icons.Queues size={40} />
          </div>
          <div style={{ color: '#a1a1aa' }}>No queues found</div>
          <div style={{ fontSize: '12px', color: '#71717a' }}>Configure Celery queues to see them here</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
        <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
          <tr style={{ borderBottom: '1px solid #1f1f23', background: '#0a0a0b' }}>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Queue Name</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Pending</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Consumers</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Priority</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Exchange</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Routing Key</th>
          </tr>
        </thead>
        <tbody>
          {queues.map((queue) => {
            const status = getQueueStatus(queue);
            const priority = getPriorityBadge(queue.priority);
            
            return (
              <tr
                key={queue.name}
                style={{
                  borderBottom: '1px solid #18181b',
                  cursor: 'pointer',
                  transition: 'background-color 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.025)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Icons.Queues size={14} />
                    <span style={{ color: '#e4e4e7', fontSize: '13px', fontFamily: 'monospace' }}>
                      {queue.name}
                    </span>
                    {queue.name === 'default' && (
                      <span style={{ 
                        padding: '2px 6px', 
                        fontSize: '10px', 
                        fontWeight: 500, 
                        background: 'rgba(59,130,246,0.12)', 
                        color: '#3b82f6', 
                        borderRadius: '3px' 
                      }}>
                        Default
                      </span>
                    )}
                  </div>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', fontWeight: 500, color: status.color }}>
                    {status.status === 'active' && <Icons.Running size={16} />}
                    {status.status === 'idle' && <Icons.Success size={16} />}
                    {status.status === 'warning' && <Icons.Cancelled size={16} />}
                    {status.status === 'inactive' && <Icons.Pending size={16} />}
                    <span>{status.label}</span>
                  </div>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  {queue.messages > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ 
                        color: queue.messages > 100 ? '#ef4444' : queue.messages > 10 ? '#f59e0b' : '#3b82f6', 
                        fontSize: '12px', 
                        fontWeight: 500 
                      }}>
                        {queue.messages.toLocaleString()}
                      </span>
                      {queue.messages > 100 && (
                        <span style={{ 
                          padding: '1px 4px', 
                          fontSize: '9px', 
                          fontWeight: 500, 
                          background: 'rgba(239,68,68,0.12)', 
                          color: '#ef4444', 
                          borderRadius: '2px' 
                        }}>
                          HIGH
                        </span>
                      )}
                    </div>
                  ) : (
                    <span style={{ color: '#71717a', fontSize: '12px' }}>0</span>
                  )}
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Icons.Workers size={12} />
                    <span style={{ 
                      color: queue.consumers > 0 ? '#28bf5c' : '#ef4444', 
                      fontSize: '12px', 
                      fontWeight: 500 
                    }}>
                      {queue.consumers || 0}
                    </span>
                  </div>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  {priority ? (
                    <span style={{ 
                      padding: '2px 6px', 
                      fontSize: '10px', 
                      fontWeight: 500, 
                      background: `${priority.color}20`, 
                      color: priority.color, 
                      borderRadius: '3px' 
                    }}>
                      {priority.label}
                    </span>
                  ) : (
                    <span style={{ color: '#71717a', fontSize: '12px' }}>—</span>
                  )}
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '12px', fontFamily: 'monospace' }}>
                    {queue.exchange || 'default'}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '12px', fontFamily: 'monospace' }}>
                    {queue.routing_key || queue.name}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// Workers List Component
function WorkersList({ searchQuery }: { searchQuery: string }) {
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkers = useCallback(async () => {
    try {
      const response = await fetch('/api/workers');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      
      let workerList = data.workers || [];
      
      // Filter by search query if provided
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        workerList = workerList.filter((worker: any) => 
          worker.name.toLowerCase().includes(query) ||
          (worker.hostname && worker.hostname.toLowerCase().includes(query))
        );
      }
      
      setWorkers(workerList);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch workers');
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    fetchWorkers();
  }, [fetchWorkers]);

  // Poll for updates every 3 seconds
  usePolling(fetchWorkers, 3000, true);

  const formatUptime = (seconds?: number) => {
    if (!seconds) return '—';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatMemory = (bytes?: number) => {
    if (!bytes) return '—';
    
    const mb = bytes / (1024 * 1024);
    if (mb > 1024) {
      return `${(mb / 1024).toFixed(1)}GB`;
    }
    return `${mb.toFixed(0)}MB`;
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#71717a' }}>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#ef4444' }}>{error}</div>
      </div>
    );
  }

  if (workers.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '40px', opacity: 0.3, marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
            <Icons.Workers size={40} />
          </div>
          <div style={{ color: '#a1a1aa' }}>No workers found</div>
          <div style={{ fontSize: '12px', color: '#71717a' }}>Start some Celery workers to see them here</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
        <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
          <tr style={{ borderBottom: '1px solid #1f1f23', background: '#0a0a0b' }}>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Worker</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Active Tasks</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Processed</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Load Avg</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Memory</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Uptime</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((worker) => {
            const isOnline = worker.status === 'online' || worker.active !== undefined;
            const loadAvg = worker.loadavg ? worker.loadavg[0]?.toFixed(2) : '—';
            
            return (
              <tr
                key={worker.name}
                style={{
                  borderBottom: '1px solid #18181b',
                  cursor: 'pointer',
                  transition: 'background-color 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.025)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Icons.Workers size={14} />
                      <span style={{ color: '#e4e4e7', fontSize: '13px', fontFamily: 'monospace' }}>
                        {worker.name}
                      </span>
                    </div>
                    {worker.hostname && (
                      <div style={{ fontSize: '11px', color: '#71717a', marginTop: '2px' }}>
                        {worker.hostname}
                      </div>
                    )}
                  </div>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', fontWeight: 500 }}>
                    {isOnline ? (
                      <>
                        <Icons.Success size={16} />
                        <span style={{ color: '#28bf5c' }}>Online</span>
                      </>
                    ) : (
                      <>
                        <Icons.Failure size={16} />
                        <span style={{ color: '#ef4444' }}>Offline</span>
                      </>
                    )}
                  </div>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#3b82f6', fontSize: '12px', fontWeight: 500 }}>
                    {worker.active || 0}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#e4e4e7', fontSize: '12px' }}>
                    {worker.processed ? worker.processed.toLocaleString() : '—'}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '12px' }}>
                    {loadAvg}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '12px' }}>
                    {formatMemory(worker.memory_usage)}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '12px' }}>
                    {formatUptime(worker.uptime)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// Task Types List Component (for Tasks section)
function TaskTypesList({ searchQuery }: { searchQuery: string }) {
  const [taskTypes, setTaskTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTaskTypes = useCallback(async () => {
    try {
      const response = await fetch('/api/task-types');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      
      let types = data.task_types || [];
      
      // Filter by search query if provided
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        types = types.filter((type: any) => 
          type.task_name.toLowerCase().includes(query)
        );
      }
      
      setTaskTypes(types);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch task types');
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    fetchTaskTypes();
  }, [fetchTaskTypes]);

  // Poll for updates every 5 seconds
  usePolling(fetchTaskTypes, 5000, true);

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#71717a' }}>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#ef4444' }}>{error}</div>
      </div>
    );
  }

  if (taskTypes.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '40px', opacity: 0.3, marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
            <Icons.Tasks size={40} />
          </div>
          <div style={{ color: '#a1a1aa' }}>No task types found</div>
          <div style={{ fontSize: '12px', color: '#71717a' }}>Register some Celery tasks to see them here</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
        <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
          <tr style={{ borderBottom: '1px solid #1f1f23', background: '#0a0a0b' }}>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Task Name</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Running</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Queued</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Runs</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Success Rate</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Avg Duration</th>
          </tr>
        </thead>
        <tbody>
          {taskTypes.map((taskType) => {
            const successRate = taskType.run_count > 0 ? 
              ((taskType.ok_count / taskType.run_count) * 100).toFixed(1) : '—';
            
            const avgDuration = taskType.avg_duration_ms ? 
              (taskType.avg_duration_ms < 1000 ? 
                `${taskType.avg_duration_ms.toFixed(0)}ms` : 
                `${(taskType.avg_duration_ms / 1000).toFixed(1)}s`) : '—';

            return (
              <tr
                key={taskType.task_name}
                style={{
                  borderBottom: '1px solid #18181b',
                  cursor: 'pointer',
                  transition: 'background-color 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.025)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Icons.Tasks size={14} />
                    <span style={{ color: '#e4e4e7', fontSize: '13px', fontFamily: 'monospace' }}>
                      {taskType.task_name}
                    </span>
                  </div>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  {taskType.running > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Icons.Running size={12} />
                      <span style={{ color: '#3b82f6', fontSize: '12px', fontWeight: 500 }}>
                        {taskType.running}
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: '#71717a', fontSize: '12px' }}>0</span>
                  )}
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  {taskType.queued > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Icons.Pending size={12} />
                      <span style={{ color: '#f59e0b', fontSize: '12px', fontWeight: 500 }}>
                        {taskType.queued}
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: '#71717a', fontSize: '12px' }}>0</span>
                  )}
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#e4e4e7', fontSize: '12px' }}>
                    {taskType.run_count.toLocaleString()}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  {taskType.run_count > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <div style={{
                        width: '40px',
                        height: '4px',
                        background: '#1f1f23',
                        borderRadius: '2px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${successRate}%`,
                          height: '100%',
                          background: parseFloat(successRate) >= 90 ? '#28bf5c' : 
                                   parseFloat(successRate) >= 70 ? '#f59e0b' : '#ef4444',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                      <span style={{ 
                        color: parseFloat(successRate) >= 90 ? '#28bf5c' : 
                               parseFloat(successRate) >= 70 ? '#f59e0b' : '#ef4444',
                        fontSize: '11px',
                        fontWeight: 500
                      }}>
                        {successRate}%
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: '#71717a', fontSize: '12px' }}>—</span>
                  )}
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                  <span style={{ color: '#3b82f6', fontSize: '12px' }}>
                    {avgDuration}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
function RunsList({ searchQuery, onTaskSelect }: {
  searchQuery: string;
  onTaskSelect: (task: Task) => void;
}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const params: any = { limit: 200 };
      if (searchQuery.trim()) {
        params.task_name = searchQuery.trim();
      }
      
      const response = await api.getTasks(params);
      setTasks(response.tasks || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

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

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#71717a' }}>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#ef4444' }}>{error}</div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '40px', opacity: 0.3, marginBottom: '8px', display: 'flex', justifyContent: 'center' }}>
            <Icons.Runs size={40} />
          </div>
          <div style={{ color: '#a1a1aa' }}>No runs yet</div>
          <div style={{ fontSize: '12px', color: '#71717a' }}>Run some Celery tasks to see them here</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
        <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
          <tr style={{ borderBottom: '1px solid #1f1f23', background: '#0a0a0b' }}>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ID</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Task</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Worker</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Started</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Duration</th>
            <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: '11px', fontWeight: 500, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Queue</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr
              key={task.task_id}
              style={{
                borderBottom: '1px solid #18181b',
                cursor: 'pointer',
                transition: 'background-color 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.025)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              onClick={() => onTaskSelect(task)}
            >
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                <span style={{ fontFamily: 'monospace', color: '#fafafa', fontSize: '12px' }}>{task.task_id.slice(0, 8)}</span>
              </td>
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: '#e4e4e7', fontSize: '13px' }}>{task.task_name || ''}</span>
                  <span style={{ 
                    padding: '2px 6px', 
                    fontSize: '10px', 
                    fontWeight: 500, 
                    background: 'rgba(139,92,246,0.12)', 
                    color: '#8b5cf6', 
                    borderRadius: '3px' 
                  }}>
                    Root
                  </span>
                </div>
              </td>
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                <StatusBadge status={task.state} />
              </td>
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#e4e4e7' }}>{task.worker || ''}</span>
              </td>
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                <span style={{ fontSize: '12px', color: '#a1a1aa' }}>
                  {formatTimestamp(task.started_at)}
                </span>
              </td>
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                <DurationBadge 
                  durationMs={task.runtime_ms} 
                  isRunning={task.state === 'STARTED' || task.state === 'RETRY'}
                  startTime={task.started_at}
                />
              </td>
              <td style={{ padding: '8px 12px', borderBottom: '1px solid #18181b' }}>
                {task.queue ? (
                  <span style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: '4px', 
                    padding: '2px 6px', 
                    fontSize: '10px', 
                    fontWeight: 500, 
                    background: 'rgba(139,92,246,0.12)', 
                    color: '#8b5cf6', 
                    borderRadius: '3px' 
                  }}>
                    <Icons.Queues size={12} /> {task.queue}
                  </span>
                ) : (
                  <span style={{ color: '#71717a' }}>—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Main App Component
function App() {
  const [activeSection, setActiveSection] = useState('tasks');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleTaskSelect = (task: Task) => {
    setSelectedTask(task);
  };

  const handleBack = () => {
    setSelectedTask(null);
  };

// Enhanced Run Detail Component with Step Timeline
function RunDetail({ task, onBack, activeSection, onSectionChange }: { 
  task: Task; 
  onBack: () => void; 
  activeSection: string;
  onSectionChange: (section: string) => void;
}) {
  const [execution, setExecution] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchExecution = useCallback(async () => {
    try {
      const response = await fetch(`/api/tasks/${task.task_id}/execution`);
      if (response.ok) {
        const data = await response.json();
        setExecution(data.execution);
        if (data.execution?.steps?.length > 0 && !selectedStep) {
          setSelectedStep(data.execution.steps[0].step_id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch execution details:', error);
    } finally {
      setLoading(false);
    }
  }, [task.task_id, selectedStep]);

  useEffect(() => {
    fetchExecution();
  }, [fetchExecution]);

  // Poll for execution updates every 2 seconds
  usePolling(fetchExecution, 2000, task.state === 'STARTED' || task.state === 'RETRY');

  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return '—';
    try {
      const date = new Date(timestamp * 1000);
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        second: '2-digit', 
        hour12: true 
      });
    } catch {
      return String(timestamp);
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '—';
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  };

  const getStepIcon = (status: string) => {
    const IconComponent = (() => {
      switch (status.toUpperCase()) {
        case 'SUCCESS':
          return Icons.Success;
        case 'FAILURE':
          return Icons.Failure;
        case 'RUNNING':
          return Icons.Running;
        default:
          return Icons.Pending;
      }
    })();
    
    return typeof IconComponent === 'function' ? (
      <IconComponent size={10} />
    ) : (
      <IconComponent size={10} />
    );
  };

  const getStepColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'SUCCESS':
        return '#28bf5c';
      case 'FAILURE':
        return '#ef4444';
      case 'RUNNING':
        return '#3b82f6';
      default:
        return '#6b7280';
    }
  };

  const selectedStepData = execution?.steps?.find((step: any) => step.step_id === selectedStep);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'detail', label: 'Detail' },
    { id: 'context', label: 'Context' },
    { id: 'metadata', label: 'Metadata' }
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0a0b', color: '#fafafa' }}>
      <Sidebar activeSection={activeSection} onSectionChange={onSectionChange} />
      
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Header 
          title={`Runs / ${task.task_name} • ${task.task_id.slice(0, 8)}`}
          showBackButton
          onBack={onBack}
          rightContent={
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <a 
                href="/docs" 
                style={{ 
                  padding: '4px 8px', 
                  fontSize: '11px', 
                  color: '#a1a1aa', 
                  textDecoration: 'none',
                  border: '1px solid #1f1f23',
                  borderRadius: '3px',
                  background: '#0a0a0b'
                }}
              >
                Run docs
              </a>
              <button
                onClick={async () => {
                  try {
                    await api.cancelTask(task.task_id);
                    alert('Cancel request sent');
                  } catch (e) {
                    alert('Cancel failed: ' + (e as Error).message);
                  }
                }}
                style={{
                  padding: '3px 6px',
                  fontSize: '10px',
                  fontWeight: 500,
                  border: '1px solid #1f1f23',
                  borderRadius: '3px',
                  background: '#0a0a0b',
                  color: '#a1a1aa',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  try {
                    await api.retryTask(task.task_id);
                    alert('Retry initiated');
                    onBack();
                  } catch (e) {
                    alert('Retry failed: ' + (e as Error).message);
                  }
                }}
                style={{
                  padding: '4px 8px',
                  fontSize: '11px',
                  fontWeight: 500,
                  border: '1px solid #3b82f6',
                  borderRadius: '3px',
                  background: '#3b82f6',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Replay run
              </button>
            </div>
          }
        />
        
        <div style={{ flex: 1, display: 'flex' }}>
          {/* Left Panel - Execution Timeline */}
          <div style={{ 
            width: '320px', 
            borderRight: '1px solid #1f1f23', 
            display: 'flex', 
            flexDirection: 'column',
            background: '#0a0a0b'
          }}>
            {/* Timeline Header */}
            <div style={{ 
              padding: '8px 12px', 
              borderBottom: '1px solid #1f1f23',
              background: '#111113'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <StatusBadge status={task.state} />
                <DurationBadge 
                  durationMs={task.runtime_ms} 
                  isRunning={task.state === 'STARTED' || task.state === 'RETRY'}
                  startTime={task.started_at}
                />
              </div>
              <div style={{ fontSize: '10px', color: '#71717a' }}>
                Started {formatTimestamp(task.started_at)}
              </div>
              {execution?.progress_percentage !== undefined && (
                <div style={{ marginTop: '6px' }}>
                  <div style={{ 
                    width: '100%', 
                    height: '2px', 
                    background: '#1f1f23', 
                    borderRadius: '1px',
                    overflow: 'hidden'
                  }}>
                    <div style={{ 
                      width: `${execution.progress_percentage}%`, 
                      height: '100%', 
                      background: '#28bf5c',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <div style={{ fontSize: '9px', color: '#71717a', marginTop: '2px' }}>
                    {execution.progress_percentage.toFixed(0)}% complete
                  </div>
                </div>
              )}
            </div>

            {/* Execution Steps */}
            <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
              {loading ? (
                <div style={{ padding: '12px', textAlign: 'center', color: '#71717a', fontSize: '11px' }}>
                  Loading execution details...
                </div>
              ) : execution?.steps ? (
                <div style={{ position: 'relative' }}>
                  {/* Timeline Line */}
                  <div style={{
                    position: 'absolute',
                    left: '23px',
                    top: '0',
                    bottom: '0',
                    width: '1px',
                    background: '#1f1f23'
                  }} />
                  
                  {execution.steps.map((step: any, index: number) => {
                    const isSelected = selectedStep === step.step_id;
                    const isActive = execution.current_step === step.step_id && task.state === 'STARTED';
                    
                    return (
                      <div
                        key={step.step_id}
                        onClick={() => setSelectedStep(step.step_id)}
                        style={{
                          position: 'relative',
                          padding: '6px 12px 6px 40px',
                          cursor: 'pointer',
                          background: isSelected ? 'rgba(59,130,246,0.08)' : 'transparent',
                          borderLeft: isSelected ? '2px solid #3b82f6' : '2px solid transparent',
                          transition: 'all 0.15s ease'
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.025)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.background = 'transparent';
                          }
                        }}
                      >
                        {/* Step Icon */}
                        <div style={{
                          position: 'absolute',
                          left: '12px',
                          top: '8px',
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          background: '#0a0a0b',
                          border: `1px solid ${getStepColor(step.status)}`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: getStepColor(step.status),
                          zIndex: 1,
                          fontSize: '10px'
                        }}>
                          {getStepIcon(step.status)}
                        </div>

                        {/* Step Content */}
                        <div>
                          <div style={{ 
                            fontSize: '11px', 
                            fontWeight: 500, 
                            color: '#fafafa',
                            marginBottom: '2px'
                          }}>
                            {step.name}
                          </div>
                          
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9px' }}>
                            <span style={{ color: getStepColor(step.status) }}>
                              {step.status}
                            </span>
                            {step.status === 'RUNNING' && step.started_at ? (
                              <span style={{ color: '#3b82f6', fontSize: '9px' }}>
                                <LiveDurationCompact startTime={step.started_at} />
                              </span>
                            ) : step.duration_ms ? (
                              <span style={{ color: '#71717a' }}>
                                {formatDuration(step.duration_ms)}
                              </span>
                            ) : null}
                            {step.started_at && step.status !== 'RUNNING' && (
                              <span style={{ color: '#71717a' }}>
                                {formatTimestamp(step.started_at)}
                              </span>
                            )}
                          </div>

                          {isActive && task.state === 'STARTED' && (
                            <div style={{ 
                              fontSize: '9px', 
                              color: '#3b82f6', 
                              marginTop: '2px',
                              fontWeight: 500
                            }}>
                              Currently running...
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ padding: '12px', textAlign: 'center', color: '#71717a', fontSize: '11px' }}>
                  No execution details available
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Step Details */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            {/* Tab Navigation */}
            <div style={{ 
              borderBottom: '1px solid #1f1f23',
              background: '#0a0a0b'
            }}>
              <div style={{ display: 'flex', padding: '0 12px' }}>
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      padding: '8px 10px',
                      fontSize: '11px',
                      fontWeight: 500,
                      background: 'none',
                      border: 'none',
                      color: activeTab === tab.id ? '#fafafa' : '#71717a',
                      borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => {
                      if (activeTab !== tab.id) {
                        e.currentTarget.style.color = '#a1a1aa';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (activeTab !== tab.id) {
                        e.currentTarget.style.color = '#71717a';
                      }
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div style={{ flex: 1, padding: '12px', overflow: 'auto' }}>
              {activeTab === 'overview' && (
                <div>
                  <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px', color: '#fafafa' }}>
                    Task Overview
                  </h3>
                  
                  <div style={{ 
                    background: '#111113', 
                    border: '1px solid #1f1f23', 
                    borderRadius: '4px', 
                    padding: '8px',
                    marginBottom: '8px'
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      <div>
                        <div style={{ fontSize: '10px', color: '#71717a', marginBottom: '2px' }}>Status</div>
                        <StatusBadge status={task.state} />
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: '#71717a', marginBottom: '2px' }}>Duration</div>
                        <DurationBadge 
                          durationMs={task.runtime_ms} 
                          isRunning={task.state === 'STARTED' || task.state === 'RETRY'}
                          startTime={task.started_at}
                        />
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: '#71717a', marginBottom: '2px' }}>Worker</div>
                        <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#e4e4e7' }}>
                          {task.worker || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: '#71717a', marginBottom: '2px' }}>Queue</div>
                        <div style={{ fontSize: '11px', color: '#e4e4e7' }}>
                          {task.queue || 'default'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {task.error && (
                    <div style={{ 
                      background: 'rgba(239,68,68,0.12)', 
                      border: '1px solid #ef4444', 
                      borderRadius: '4px', 
                      padding: '8px',
                      marginBottom: '8px'
                    }}>
                      <h4 style={{ color: '#ef4444', fontSize: '11px', fontWeight: 500, marginBottom: '4px' }}>
                        Error Details
                      </h4>
                      <pre style={{ 
                        color: '#fca5a5', 
                        fontSize: '10px', 
                        fontFamily: 'monospace', 
                        whiteSpace: 'pre-wrap',
                        margin: 0
                      }}>
                        {task.error}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'detail' && selectedStepData && (
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#fafafa' }}>
                    Step: {selectedStepData.name}
                  </h3>
                  
                  <div style={{ 
                    background: '#111113', 
                    border: '1px solid #1f1f23', 
                    borderRadius: '6px', 
                    padding: '12px',
                    marginBottom: '12px'
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div>
                        <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '3px' }}>Status</div>
                        <div style={{ color: getStepColor(selectedStepData.status), fontWeight: 500, fontSize: '12px' }}>
                          {selectedStepData.status}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '3px' }}>Duration</div>
                        <div style={{ color: '#3b82f6', fontSize: '12px' }}>
                          {formatDuration(selectedStepData.duration_ms)}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '3px' }}>Started</div>
                        <div style={{ fontSize: '12px', color: '#e4e4e7' }}>
                          {formatTimestamp(selectedStepData.started_at)}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: '#71717a', marginBottom: '3px' }}>Completed</div>
                        <div style={{ fontSize: '12px', color: '#e4e4e7' }}>
                          {formatTimestamp(selectedStepData.completed_at)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {selectedStepData.error && (
                    <div style={{ 
                      background: 'rgba(239,68,68,0.12)', 
                      border: '1px solid #ef4444', 
                      borderRadius: '6px', 
                      padding: '12px',
                      marginBottom: '12px'
                    }}>
                      <h4 style={{ color: '#ef4444', fontSize: '12px', fontWeight: 500, marginBottom: '6px' }}>
                        Step Error
                      </h4>
                      <pre style={{ 
                        color: '#fca5a5', 
                        fontSize: '11px', 
                        fontFamily: 'monospace', 
                        whiteSpace: 'pre-wrap',
                        margin: 0
                      }}>
                        {selectedStepData.error}
                      </pre>
                    </div>
                  )}

                  {selectedStepData.metadata && Object.keys(selectedStepData.metadata).length > 0 && (
                    <div style={{ 
                      background: '#111113', 
                      border: '1px solid #1f1f23', 
                      borderRadius: '6px', 
                      padding: '12px'
                    }}>
                      <h4 style={{ fontSize: '12px', fontWeight: 500, marginBottom: '8px', color: '#fafafa' }}>
                        Step Metadata
                      </h4>
                      <pre style={{ 
                        color: '#e4e4e7', 
                        fontSize: '11px', 
                        fontFamily: 'monospace', 
                        whiteSpace: 'pre-wrap',
                        margin: 0,
                        background: '#0a0a0b',
                        padding: '8px',
                        borderRadius: '4px',
                        border: '1px solid #1f1f23'
                      }}>
                        {JSON.stringify(selectedStepData.metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'context' && (
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#fafafa' }}>
                    Execution Context
                  </h3>
                  
                  <div style={{ 
                    background: '#111113', 
                    border: '1px solid #1f1f23', 
                    borderRadius: '6px', 
                    padding: '12px'
                  }}>
                    <h4 style={{ fontSize: '12px', fontWeight: 500, marginBottom: '8px', color: '#fafafa' }}>
                      Task Arguments
                    </h4>
                    <pre style={{ 
                      color: '#e4e4e7', 
                      fontSize: '11px', 
                      fontFamily: 'monospace', 
                      whiteSpace: 'pre-wrap',
                      margin: 0,
                      background: '#0a0a0b',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #1f1f23'
                    }}>
                      {JSON.stringify({
                        args: task.args,
                        kwargs: task.kwargs
                      }, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {activeTab === 'metadata' && (
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#fafafa' }}>
                    Task Metadata
                  </h3>
                  
                  <div style={{ 
                    background: '#111113', 
                    border: '1px solid #1f1f23', 
                    borderRadius: '6px', 
                    padding: '12px'
                  }}>
                    <pre style={{ 
                      color: '#e4e4e7', 
                      fontSize: '11px', 
                      fontFamily: 'monospace', 
                      whiteSpace: 'pre-wrap',
                      margin: 0,
                      background: '#0a0a0b',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #1f1f23'
                    }}>
                      {JSON.stringify({
                        task_id: task.task_id,
                        task_name: task.task_name,
                        state: task.state,
                        retries: task.retries,
                        started_at: task.started_at,
                        succeeded_at: task.succeeded_at,
                        failed_at: task.failed_at,
                        received_at: task.received_at,
                        runtime_ms: task.runtime_ms,
                        worker: task.worker,
                        queue: task.queue
                      }, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

  if (selectedTask) {
    return <RunDetail task={selectedTask} onBack={handleBack} activeSection={activeSection} onSectionChange={setActiveSection} />;
  }

  const renderContent = () => {
    switch (activeSection) {
      case 'tasks':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Header title="Tasks" />
            
            {/* Filter Bar */}
            <div style={{ 
              padding: '6px 20px', 
              borderBottom: '1px solid #1f1f23', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: '#0a0a0b' 
            }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px', 
                background: '#111113', 
                border: '1px solid #1f1f23', 
                borderRadius: '4px', 
                padding: '6px 12px', 
                minWidth: '180px',
                maxWidth: '240px'
              }}>
                <Icons.Search size={16} />
                <input
                  type="text"
                  placeholder="Search task types..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    boxShadow: 'none',
                    color: '#fafafa',
                    fontSize: '13px',
                    flex: 1,
                    fontFamily: 'inherit',
                    fontWeight: 400
                  }}
                />
              </div>
            </div>
            
            <TaskTypesList searchQuery={searchQuery} />
          </div>
        );
      case 'runs':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Header title="Runs" />
            
            {/* Filter Bar */}
            <div style={{ 
              padding: '6px 20px', 
              borderBottom: '1px solid #1f1f23', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: '#0a0a0b' 
            }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px', 
                background: '#111113', 
                border: '1px solid #1f1f23', 
                borderRadius: '4px', 
                padding: '6px 12px', 
                minWidth: '180px',
                maxWidth: '240px'
              }}>
                <Icons.Search size={16} />
                <input
                  type="text"
                  placeholder="Search runs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    boxShadow: 'none',
                    color: '#fafafa',
                    fontSize: '13px',
                    flex: 1,
                    fontFamily: 'inherit',
                    fontWeight: 400
                  }}
                />
              </div>
            </div>
            
            <RunsList 
              searchQuery={searchQuery}
              onTaskSelect={handleTaskSelect}
            />
          </div>
        );
      case 'workers':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Header title="Workers" />
            
            {/* Filter Bar */}
            <div style={{ 
              padding: '6px 20px', 
              borderBottom: '1px solid #1f1f23', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: '#0a0a0b' 
            }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px', 
                background: '#111113', 
                border: '1px solid #1f1f23', 
                borderRadius: '4px', 
                padding: '6px 12px', 
                minWidth: '180px',
                maxWidth: '240px'
              }}>
                <Icons.Search size={16} />
                <input
                  type="text"
                  placeholder="Search workers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    boxShadow: 'none',
                    color: '#fafafa',
                    fontSize: '13px',
                    flex: 1,
                    fontFamily: 'inherit',
                    fontWeight: 400
                  }}
                />
              </div>
            </div>
            
            <WorkersList searchQuery={searchQuery} />
          </div>
        );
      case 'queues':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Header title="Queues" />
            
            {/* Filter Bar */}
            <div style={{ 
              padding: '6px 20px', 
              borderBottom: '1px solid #1f1f23', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: '#0a0a0b' 
            }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px', 
                background: '#111113', 
                border: '1px solid #1f1f23', 
                borderRadius: '4px', 
                padding: '6px 12px', 
                minWidth: '180px',
                maxWidth: '240px'
              }}>
                <Icons.Search size={16} />
                <input
                  type="text"
                  placeholder="Search queues..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    boxShadow: 'none',
                    color: '#fafafa',
                    fontSize: '13px',
                    flex: 1,
                    fontFamily: 'inherit',
                    fontWeight: 400
                  }}
                />
              </div>
            </div>
            
            <QueuesList searchQuery={searchQuery} />
          </div>
        );
      default:
        return (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Header title={activeSection.charAt(0).toUpperCase() + activeSection.slice(1)} />
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center', color: '#a1a1aa' }}>
                <div style={{ fontSize: '40px', marginBottom: '16px' }}>🚧</div>
                <div>Coming soon...</div>
                <div style={{ fontSize: '12px', marginTop: '8px' }}>
                  This section is under development
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0a0b', color: '#fafafa' }}>
      <Sidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection} 
      />
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {renderContent()}
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
