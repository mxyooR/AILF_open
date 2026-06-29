export type InferenceWorkerStatus = 'online' | 'offline' | 'unreachable';

export interface InferenceWorkerItem {
  worker_name: string;
  status: InferenceWorkerStatus;
  connected: boolean;
  is_expected: boolean;
  pid: number | null;
  max_concurrency: number | null;
  process_count: number | null;
  uptime_seconds: number | null;
  processed_tasks: number;
  queue_names: string[];
  broker_transport?: string | null;
  broker_host?: string | null;
}

export interface InferenceWorkerSummary {
  checked_at: string;
  queue: string;
  broker_connected: boolean;
  total_workers: number;
  online_workers: number;
  offline_workers: number;
  expected_workers: number;
  unexpected_workers: number;
  inspect_error?: string | null;
}

export interface InferenceWorkersStatusData {
  summary: InferenceWorkerSummary;
  workers: InferenceWorkerItem[];
  performance?: InferenceTaskPerformanceData;
}

export interface InferenceTaskPerformanceSummary {
  total_tasks: number;
  success_tasks: number;
  fail_tasks: number;
  avg_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
  p50_duration_ms: number;
  p90_duration_ms: number;
  p95_duration_ms: number;
  p99_duration_ms: number;
  std_duration_ms: number;
  last_duration_ms: number;
  last_timestamp?: string | null;
  last_worker_name?: string | null;
  sampled_tasks: number;
  sample_success_rate: number;
  sample_window_start?: string | null;
  sample_window_end?: string | null;
  error?: string | null;
}

export interface InferenceTaskDurationItem {
  timestamp: string;
  duration_ms: number;
  worker_name?: string | null;
  method?: string | null;
  service?: string | null;
  task_id?: string | null;
  success: boolean;
}

export interface InferenceTaskPerformanceData {
  summary: InferenceTaskPerformanceSummary;
  recent_tasks: InferenceTaskDurationItem[];
  timeline?: InferenceTaskTimelineItem[];
  by_method?: InferenceTaskGroupStatItem[];
  by_worker?: InferenceTaskGroupStatItem[];
}

export interface InferenceTaskTimelineItem {
  timestamp: string;
  task_count: number;
  success_tasks: number;
  fail_tasks: number;
  success_rate: number;
  avg_duration_ms: number;
  p95_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
}

export interface InferenceTaskGroupStatItem {
  name: string;
  total_tasks: number;
  success_tasks: number;
  fail_tasks: number;
  success_rate: number;
  avg_duration_ms: number;
  p95_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
}

export interface RedisRuntimeSummary {
  checked_at: string;
  backend_connected: boolean;
  broker_connected: boolean;
  backend_db_key_count: number;
  broker_db_key_count: number;
  workflow_session_count: number;
  async_task_count: number;
  errors: string[];
}

export interface RedisDatabaseStatus {
  name: string;
  host: string;
  db_index: number;
  connected: boolean;
  key_count: number;
  sample_key_count: number;
  error?: string | null;
}

export interface RedisWorkflowSessionItem {
  key: string;
  user_id?: string;
  workflow_id?: string;
  current_step?: string;
  status?: string;
  updated_at?: string;
  step_data_keys: string[];
}

export interface RedisAsyncTaskItem {
  key: string;
  task_id?: string;
  status?: string;
  updated_at?: string;
  error?: string;
}

export interface RedisKeySampleItem {
  database: 'backend' | 'broker' | string;
  key: string;
  type: string;
  ttl: number | null;
  preview: string;
}

export interface RedisRuntimeData {
  summary: RedisRuntimeSummary;
  databases: RedisDatabaseStatus[];
  workflow_sessions: RedisWorkflowSessionItem[];
  async_tasks: RedisAsyncTaskItem[];
  key_samples: RedisKeySampleItem[];
}

export interface RuntimeDashboardData {
  checked_at: string;
  inference: InferenceWorkersStatusData;
  redis: RedisRuntimeData;
}

export interface RuntimeInferenceOverviewData {
  summary: InferenceWorkerSummary;
  workers: InferenceWorkerItem[];
}

export interface RuntimeRedisOverviewData {
  summary: RedisRuntimeSummary;
  databases: RedisDatabaseStatus[];
}

export interface RuntimeRedisWorkflowSessionsData {
  workflow_sessions: RedisWorkflowSessionItem[];
}

export interface RuntimeRedisAsyncTasksData {
  async_tasks: RedisAsyncTaskItem[];
}

export interface RuntimeRedisKeySamplesData {
  key_samples: RedisKeySampleItem[];
}
