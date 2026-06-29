import { apiClient } from '../common/apiClient';
import type {
  InferenceTaskPerformanceData,
  InferenceWorkersStatusData,
  RuntimeDashboardData,
  RuntimeInferenceOverviewData,
  RuntimeRedisAsyncTasksData,
  RuntimeRedisKeySamplesData,
  RuntimeRedisOverviewData,
  RuntimeRedisWorkflowSessionsData
} from '../../types/developer/inference';

export const inferenceAPI = {
  async getWorkersStatus(): Promise<InferenceWorkersStatusData> {
    const response = await apiClient.get<InferenceWorkersStatusData>('/api/v1/config/inference/workers');
    return response.data;
  },

  async getRuntimeDashboard(): Promise<RuntimeDashboardData> {
    const response = await apiClient.get<RuntimeDashboardData>('/api/v1/config/runtime/dashboard');
    return response.data;
  },

  async getRuntimeInferenceOverview(): Promise<RuntimeInferenceOverviewData> {
    const response = await apiClient.get<RuntimeInferenceOverviewData>('/api/v1/config/runtime/inference/overview');
    return response.data;
  },

  async getRuntimeInferencePerformance(): Promise<InferenceTaskPerformanceData> {
    const response = await apiClient.get<InferenceTaskPerformanceData>('/api/v1/config/runtime/inference/performance');
    return response.data;
  },

  async getRuntimeRedisOverview(): Promise<RuntimeRedisOverviewData> {
    const response = await apiClient.get<RuntimeRedisOverviewData>('/api/v1/config/runtime/redis/overview');
    return response.data;
  },

  async getRuntimeRedisWorkflowSessions(): Promise<RuntimeRedisWorkflowSessionsData> {
    const response = await apiClient.get<RuntimeRedisWorkflowSessionsData>('/api/v1/config/runtime/redis/workflow-sessions');
    return response.data;
  },

  async getRuntimeRedisAsyncTasks(): Promise<RuntimeRedisAsyncTasksData> {
    const response = await apiClient.get<RuntimeRedisAsyncTasksData>('/api/v1/config/runtime/redis/async-tasks');
    return response.data;
  },

  async getRuntimeRedisKeySamples(): Promise<RuntimeRedisKeySamplesData> {
    const response = await apiClient.get<RuntimeRedisKeySamplesData>('/api/v1/config/runtime/redis/key-samples');
    return response.data;
  },

  async getRuntimeDashboardSplit(): Promise<RuntimeDashboardData> {
    const [
      inferenceOverview,
      inferencePerformance,
      redisOverview,
      redisWorkflowSessions,
      redisAsyncTasks,
      redisKeySamples
    ] = await Promise.all([
      this.getRuntimeInferenceOverview(),
      this.getRuntimeInferencePerformance(),
      this.getRuntimeRedisOverview(),
      this.getRuntimeRedisWorkflowSessions(),
      this.getRuntimeRedisAsyncTasks(),
      this.getRuntimeRedisKeySamples()
    ]);

    return {
      checked_at: new Date().toISOString(),
      inference: {
        summary: inferenceOverview.summary,
        workers: inferenceOverview.workers,
        performance: inferencePerformance
      },
      redis: {
        summary: redisOverview.summary,
        databases: redisOverview.databases,
        workflow_sessions: redisWorkflowSessions.workflow_sessions,
        async_tasks: redisAsyncTasks.async_tasks,
        key_samples: redisKeySamples.key_samples
      }
    };
  }
};

export default inferenceAPI;
