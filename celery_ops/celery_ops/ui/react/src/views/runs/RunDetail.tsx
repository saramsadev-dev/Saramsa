import React, { useState, useEffect } from 'react';
import { Header } from '../../components/Header';
import { ExecutionTimeline } from './ExecutionTimeline';
import { DetailSidebar } from './DetailSidebar';
import { apiService } from '../../services/api';
import { usePolling } from '../../hooks/usePolling';
import { Task, TaskExecution } from '../../types';

interface RunDetailProps {
  task: Task;
  onBack: () => void;
}

export const RunDetail: React.FC<RunDetailProps> = ({ task: initialTask, onBack }) => {
  const [task, setTask] = useState<Task>(initialTask);
  const [execution, setExecution] = useState<TaskExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const fetchTaskData = async () => {
    try {
      const [taskData, executionData] = await Promise.all([
        apiService.getTask(task.task_id),
        apiService.getTaskExecution(task.task_id)
      ]);
      
      setTask(taskData);
      setExecution(executionData.execution);
    } catch (error) {
      console.error('Failed to fetch task data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaskData();
  }, [task.task_id]);

  // Poll for updates every 2 seconds, but stop if task is completed
  const isCompleted = ['SUCCESS', 'FAILURE', 'REVOKED'].includes(task.state);
  usePolling(fetchTaskData, 2000, !isCompleted);

  const handleCancel = async () => {
    if (!task.task_id || isCompleted) return;
    
    setCancelling(true);
    try {
      const result = await apiService.cancelTask(task.task_id);
      if (result.ok) {
        alert('Cancel request sent successfully. The task should stop shortly.');
        // Refresh task data after a short delay
        setTimeout(fetchTaskData, 1000);
      } else {
        alert(`Cancel failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Cancel request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setCancelling(false);
    }
  };

  const handleRetry = async () => {
    if (!task.task_id || !isCompleted) return;
    
    setRetrying(true);
    try {
      const result = await apiService.retryTask(task.task_id);
      if (result.ok) {
        alert('Task retry initiated successfully.');
        onBack(); // Go back to runs list
      } else {
        alert(`Retry failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Retry request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setRetrying(false);
    }
  };

  const isRunning = ['STARTED', 'RETRY', 'RECEIVED'].includes(task.state);
  const canCancel = isRunning && !cancelling;
  const canRetry = isCompleted && !retrying;

  const breadcrumbTitle = task.task_name 
    ? `Runs / ${task.task_name} • ${task.task_id.slice(0, 8)}`
    : `Runs / ${task.task_id.slice(0, 8)}...`;

  const headerActions = (
    <div className="flex items-center gap-1">
      <a 
        href="/docs" 
        className="px-3 py-1.5 text-xs text-fg-muted hover:text-fg border border-border rounded bg-bg hover:bg-bg-hover transition-all"
      >
        Run docs
      </a>
      <button
        onClick={handleCancel}
        disabled={!canCancel}
        title={canCancel ? 'Cancel this task' : 'Task cannot be cancelled (not running)'}
        className={`px-2 py-1 text-xs font-medium border rounded transition-all ${
          canCancel
            ? 'text-fg-muted hover:text-fg border-border bg-bg hover:bg-bg-hover'
            : 'text-fg-dim border-border-subtle bg-bg-elevated cursor-not-allowed opacity-50'
        }`}
      >
        {cancelling ? 'Cancelling...' : 'Cancel'}
      </button>
      <button
        onClick={handleRetry}
        disabled={!canRetry}
        title={canRetry ? 'Retry this task with same parameters' : 'Task must be completed to retry'}
        className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
          canRetry
            ? 'bg-accent hover:bg-accent-hover text-white border-accent'
            : 'bg-bg-elevated text-fg-dim border-border-subtle cursor-not-allowed opacity-50'
        } border`}
      >
        {retrying ? 'Retrying...' : 'Replay run'}
      </button>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      <Header 
        title={breadcrumbTitle}
        showBackButton
        onBack={onBack}
        rightContent={headerActions}
      />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Execution Timeline */}
        <div className="flex-1 p-6 overflow-y-auto bg-bg border-r border-border max-w-[calc(100%-400px)]">
          <ExecutionTimeline 
            task={task}
            execution={execution}
            loading={loading}
          />
        </div>
        
        {/* Right Panel: Fixed Sidebar */}
        <div className="w-[400px] flex-shrink-0 bg-bg-elevated border-l border-border">
          <DetailSidebar 
            task={task}
            execution={execution}
          />
        </div>
      </div>
    </div>
  );
};