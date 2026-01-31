export interface Task {
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

export interface ExecutionStep {
  step_id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILURE';
  started_at?: number;
  completed_at?: number;
  duration_ms?: number;
  metadata?: Record<string, any>;
  error?: string;
}

export interface TaskExecution {
  steps: ExecutionStep[];
  current_step: string;
  progress_percentage: number;
}

export interface TaskType {
  task_name: string;
  running: number;
  queued: number;
  activity: Array<{ state: string }>;
  avg_duration_ms?: number;
  run_count: number;
  ok_count: number;
  fail_count: number;
}

export interface Worker {
  name: string;
  status: string;
  active?: number;
  processed?: number;
  queues?: string[];
}

export interface Queue {
  name: string;
  length?: number;
}

export interface ApiResponse<T> {
  [key: string]: T;
  count?: number;
}

export interface StatusResponse {
  celery_ops: string;
  event_consumer: {
    enabled: boolean;
    status: string;
  };
  store: {
    type: string;
    task_count: number;
  };
  broker_connected: boolean;
}