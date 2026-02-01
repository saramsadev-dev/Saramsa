import axios from 'axios';
import { Task, TaskExecution, TaskType, Worker, Queue, ApiResponse, StatusResponse } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Accept': 'application/json',
  },
});

export const apiService = {
  // Tasks
  async getTasks(params?: { state?: string; task_name?: string; worker?: string; limit?: number }): Promise<ApiResponse<Task[]>> {
    const response = await api.get('/tasks', { params });
    return response.data;
  },

  async getTask(taskId: string): Promise<Task> {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  async getTaskExecution(taskId: string): Promise<{ task_id: string; execution: TaskExecution }> {
    const response = await api.get(`/tasks/${taskId}/execution`);
    return response.data;
  },

  async cancelTask(taskId: string): Promise<{ ok: boolean; task_id: string; message?: string; error?: string }> {
    const response = await api.post(`/tasks/${taskId}/cancel`);
    return response.data;
  },

  async retryTask(taskId: string, queue?: string): Promise<{ ok: boolean; task_id: string; message?: string; error?: string }> {
    const response = await api.post(`/tasks/${taskId}/retry`, { params: { queue } });
    return response.data;
  },

  // Task Types
  async getTaskTypes(): Promise<ApiResponse<TaskType[]>> {
    const response = await api.get('/task-types');
    return response.data;
  },

  // Workers
  async getWorkers(): Promise<ApiResponse<Worker[]>> {
    const response = await api.get('/workers');
    return response.data;
  },

  async getWorker(name: string): Promise<Worker> {
    const response = await api.get(`/workers/${name}`);
    return response.data;
  },

  // Queues
  async getQueues(): Promise<ApiResponse<Queue[]>> {
    const response = await api.get('/queues');
    return response.data;
  },

  // Status
  async getStatus(): Promise<StatusResponse> {
    const response = await api.get('/status');
    return response.data;
  },

  // Stats
  async getStats(): Promise<any> {
    const response = await api.get('/stats');
    return response.data;
  },
};