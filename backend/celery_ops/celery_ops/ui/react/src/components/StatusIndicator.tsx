import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { StatusResponse } from '../types';

export const StatusIndicator: React.FC = () => {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const statusData = await apiService.getStatus();
        setStatus(statusData);
      } catch (error) {
        console.warn('Status check failed:', error);
        setStatus(null);
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-fg-muted">
        <div className="w-1.5 h-1.5 rounded-full bg-fg-dim"></div>
        <span>Checking...</span>
      </div>
    );
  }

  const isConnected = status?.event_consumer?.status === 'running' && status?.broker_connected;
  const hasConnectionIssue = status?.event_consumer?.status === 'connection_issue';

  return (
    <div className="flex items-center gap-2 text-xs text-fg-muted">
      <div className={`w-1.5 h-1.5 rounded-full transition-colors ${
        isConnected ? 'bg-success' : 'bg-error'
      }`}></div>
      <span>
        {isConnected 
          ? 'Real-time events active'
          : hasConnectionIssue 
            ? 'Broker connection issue'
            : 'API connection error'
        }
      </span>
    </div>
  );
};