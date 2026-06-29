import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Progress, Segmented, Space, Switch, Table, Tabs, Tag, Tooltip, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ClusterOutlined, ReloadOutlined } from '@ant-design/icons';
import { UnifiedCard } from '../common';
import { inferenceAPI } from '../../../services/developer/inferenceAPI';
import type {
  InferenceTaskDurationItem,
  InferenceTaskGroupStatItem,
  InferenceTaskTimelineItem,
  InferenceWorkerItem,
  RedisAsyncTaskItem,
  RedisDatabaseStatus,
  RedisKeySampleItem,
  RedisWorkflowSessionItem,
  RuntimeDashboardData
} from '../../../types/developer/inference';
import './InferenceWorkerStep.css';

const { Text } = Typography;

interface InferenceWorkerStepProps {
  onPrev?: () => void;
}

const AUTO_REFRESH_INTERVAL_MS = 15000;

const formatUptime = (uptimeSeconds: number | null): string => {
  if (!uptimeSeconds || uptimeSeconds < 0) {
    return '-';
  }
  const days = Math.floor(uptimeSeconds / 86400);
  const hours = Math.floor((uptimeSeconds % 86400) / 3600);
  const minutes = Math.floor((uptimeSeconds % 3600) / 60);

  if (days > 0) {
    return `${days}天 ${hours}小时`;
  }
  if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`;
  }
  return `${minutes}分钟`;
};

const getWorkerStatusTag = (status: InferenceWorkerItem['status']) => {
  if (status === 'online') {
    return <Tag color="success">在线</Tag>;
  }
  if (status === 'offline') {
    return <Tag color="error">离线</Tag>;
  }
  return <Tag color="warning">不可达</Tag>;
};

const getConnectionTag = (connected: boolean) =>
  connected ? <Tag color="success">正常</Tag> : <Tag color="error">异常</Tag>;

const formatDateTime = (iso?: string) => (iso ? new Date(iso).toLocaleString() : '-');

const safePercent = (value: number, total: number): number => {
  if (total <= 0) {
    return 0;
  }
  return Math.round((value / total) * 100);
};

const toSafeNumber = (value: number | null | undefined): number => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 0;
  }
  return value;
};

const formatDurationMs = (value?: number | null): string => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '-';
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(value >= 10000 ? 1 : 2)}s`;
  }
  return `${Math.round(value)}ms`;
};

const formatPercent = (value?: number | null): string => `${toSafeNumber(value).toFixed(1)}%`;

const toTimeLabel = (iso?: string, includeSeconds: boolean = false): string => {
  if (!iso) {
    return '-';
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }
  return date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: includeSeconds ? '2-digit' : undefined
  });
};

interface RuntimeLinePoint {
  key: string;
  label: string;
  value: number;
  tooltip: string;
}

interface RuntimeLineChartProps {
  points: RuntimeLinePoint[];
  color: string;
  emptyText: string;
}

const RuntimeLineChart: React.FC<RuntimeLineChartProps> = ({ points, color, emptyText }) => {
  if (!points.length) {
    return <div className="duration-empty">{emptyText}</div>;
  }

  const chartWidth = Math.max(560, points.length * 72);
  const chartHeight = 250;
  const paddingLeft = 44;
  const paddingRight = 18;
  const paddingTop = 20;
  const paddingBottom = 46;
  const drawWidth = chartWidth - paddingLeft - paddingRight;
  const drawHeight = chartHeight - paddingTop - paddingBottom;
  const maxValue = Math.max(...points.map((item) => item.value), 1);
  const minValue = Math.min(...points.map((item) => item.value), 0);
  const valueRange = Math.max(maxValue - minValue, 1);

  const svgPoints = points.map((point, index) => {
    const x = paddingLeft + (points.length === 1 ? drawWidth / 2 : (index * drawWidth) / (points.length - 1));
    const y = paddingTop + ((maxValue - point.value) / valueRange) * drawHeight;
    return { ...point, x, y };
  });

  const polylinePoints = svgPoints.map((point) => `${point.x},${point.y}`).join(' ');

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const tickValue = maxValue - (maxValue - minValue) * ratio;
    return {
      value: tickValue,
      y: paddingTop + ratio * drawHeight
    };
  });

  return (
    <div className="runtime-line-chart-wrap">
      <svg width={chartWidth} height={chartHeight} className="runtime-line-chart-svg" role="img" aria-label="运行监控折线图">
        <defs>
          <linearGradient id="runtimeLineAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.32" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {yTicks.map((tick, index) => (
          <g key={`y-tick-${index}`}>
            <line
              x1={paddingLeft}
              y1={tick.y}
              x2={chartWidth - paddingRight}
              y2={tick.y}
              className="runtime-line-grid"
            />
            <text x={paddingLeft - 8} y={tick.y + 4} textAnchor="end" className="runtime-line-y-label">
              {Math.round(tick.value)}
            </text>
          </g>
        ))}

        <polyline
          fill="none"
          stroke={color}
          strokeWidth={3}
          points={polylinePoints}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        <polygon
          fill="url(#runtimeLineAreaGradient)"
          points={`${paddingLeft},${chartHeight - paddingBottom} ${polylinePoints} ${chartWidth - paddingRight},${chartHeight - paddingBottom}`}
        />

        {svgPoints.map((point) => (
          <g key={point.key}>
            <circle cx={point.x} cy={point.y} r={4.5} fill="#fff" stroke={color} strokeWidth={2.5}>
              <title>{point.tooltip}</title>
            </circle>
            <text x={point.x} y={chartHeight - 16} textAnchor="middle" className="runtime-line-x-label">
              {point.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};

type RightChartMetric =
  | 'duration_avg_timeline'
  | 'timeline_task_count'
  | 'timeline_success_rate'
  | 'timeline_p95'
  | 'worker_avg_duration'
  | 'method_avg_duration';

const RIGHT_CHART_OPTIONS: Array<{ label: string; value: RightChartMetric }> = [
  { label: '完整任务耗时', value: 'duration_avg_timeline' },
  { label: '分钟任务量', value: 'timeline_task_count' },
  { label: '分钟成功率', value: 'timeline_success_rate' },
  { label: '分钟P95耗时', value: 'timeline_p95' },
  { label: '节点均耗时', value: 'worker_avg_duration' },
  { label: '方法均耗时', value: 'method_avg_duration' }
];

const InferenceWorkerStep: React.FC<InferenceWorkerStepProps> = ({ onPrev }) => {
  const [dashboard, setDashboard] = useState<RuntimeDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [rightChartMetric, setRightChartMetric] = useState<RightChartMetric>('duration_avg_timeline');

  const loadStatus = useCallback(async (silent: boolean = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const status = await inferenceAPI.getRuntimeDashboardSplit();
      setDashboard(status);
      setErrorMessage(null);
    } catch (error: any) {
      const nextError = error?.message || '获取运行监控数据失败';
      setErrorMessage(nextError);
      if (!silent) {
        message.error(nextError);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadStatus(false);
  }, [loadStatus]);

  useEffect(() => {
    if (!autoRefresh) {
      return;
    }
    const timer = setInterval(() => {
      loadStatus(true);
    }, AUTO_REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [autoRefresh, loadStatus]);

  const workerColumns: ColumnsType<InferenceWorkerItem> = useMemo(
    () => [
      {
        title: '推理机',
        dataIndex: 'worker_name',
        key: 'worker_name',
        render: (value: string, record) => (
          <div>
            <div style={{ fontWeight: 600 }}>{value}</div>
            <div style={{ fontSize: 12, color: '#8e8e93' }}>
              {record.is_expected ? '预期节点' : '自动发现节点'}
            </div>
          </div>
        )
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (status: InferenceWorkerItem['status']) => getWorkerStatusTag(status)
      },
      {
        title: '队列',
        dataIndex: 'queue_names',
        key: 'queue_names',
        render: (queues: string[]) =>
          queues && queues.length > 0 ? (
            <Space wrap>
              {queues.map((queue) => (
                <Tag key={queue} color="blue">
                  {queue}
                </Tag>
              ))}
            </Space>
          ) : (
            <Text type="secondary">-</Text>
          )
      },
      {
        title: '并发',
        dataIndex: 'max_concurrency',
        key: 'max_concurrency',
        width: 90,
        render: (value: number | null) => value ?? '-'
      },
      {
        title: '已处理任务',
        dataIndex: 'processed_tasks',
        key: 'processed_tasks',
        width: 120
      },
      {
        title: '运行时长',
        dataIndex: 'uptime_seconds',
        key: 'uptime_seconds',
        width: 140,
        render: (value: number | null) => formatUptime(value)
      },
      {
        title: '详情',
        key: 'details',
        width: 120,
        render: (_, record) => (
          <Tooltip
            title={
              <div>
                <div>PID: {record.pid ?? '-'}</div>
                <div>进程数: {record.process_count ?? '-'}</div>
                <div>Broker: {record.broker_host || '-'}</div>
                <div>传输: {record.broker_transport || '-'}</div>
              </div>
            }
          >
            <Button size="small">查看</Button>
          </Tooltip>
        )
      }
    ],
    []
  );

  const redisDbColumns: ColumnsType<RedisDatabaseStatus> = useMemo(
    () => [
      {
        title: '数据库',
        dataIndex: 'name',
        key: 'name',
        width: 110,
        render: (value: string) => <Tag color={value === 'backend' ? 'blue' : 'purple'}>{value}</Tag>
      },
      {
        title: '地址',
        dataIndex: 'host',
        key: 'host'
      },
      {
        title: 'DB',
        dataIndex: 'db_index',
        key: 'db_index',
        width: 80
      },
      {
        title: '连接',
        dataIndex: 'connected',
        key: 'connected',
        width: 90,
        render: (value: boolean) => getConnectionTag(value)
      },
      {
        title: 'Key总数',
        dataIndex: 'key_count',
        key: 'key_count',
        width: 100
      },
      {
        title: '样本Key数',
        dataIndex: 'sample_key_count',
        key: 'sample_key_count',
        width: 110
      },
      {
        title: '错误信息',
        dataIndex: 'error',
        key: 'error',
        render: (value?: string | null) => value || '-'
      }
    ],
    []
  );

  const sessionColumns: ColumnsType<RedisWorkflowSessionItem> = useMemo(
    () => [
      { title: 'Key', dataIndex: 'key', key: 'key', width: 260, ellipsis: true },
      { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 120, render: (v?: string) => v || '-' },
      { title: '工作流', dataIndex: 'workflow_id', key: 'workflow_id', width: 160, ellipsis: true, render: (v?: string) => v || '-' },
      { title: '当前步骤', dataIndex: 'current_step', key: 'current_step', width: 140, render: (v?: string) => v || '-' },
      { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v?: string) => (v ? <Tag>{v}</Tag> : '-') },
      {
        title: '表单字段',
        dataIndex: 'step_data_keys',
        key: 'step_data_keys',
        render: (keys: string[]) =>
          keys && keys.length > 0 ? (
            <Space wrap>
              {keys.map((key) => (
                <Tag key={key}>{key}</Tag>
              ))}
            </Space>
          ) : (
            '-'
          )
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 180,
        render: (v?: string) => formatDateTime(v)
      }
    ],
    []
  );

  const asyncTaskColumns: ColumnsType<RedisAsyncTaskItem> = useMemo(
    () => [
      { title: 'Key', dataIndex: 'key', key: 'key', width: 240, ellipsis: true },
      { title: 'Task ID', dataIndex: 'task_id', key: 'task_id', width: 260, ellipsis: true, render: (v?: string) => v || '-' },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (status?: string) => {
          if (!status) {
            return '-';
          }
          const color = status === 'SUCCESS' ? 'success' : status === 'FAILURE' ? 'error' : 'processing';
          return <Tag color={color}>{status}</Tag>;
        }
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 180,
        render: (v?: string) => formatDateTime(v)
      },
      {
        title: '错误',
        dataIndex: 'error',
        key: 'error',
        render: (v?: string) => (v ? v : '-')
      }
    ],
    []
  );

  const keySampleColumns: ColumnsType<RedisKeySampleItem> = useMemo(
    () => [
      {
        title: '来源',
        dataIndex: 'database',
        key: 'database',
        width: 90,
        render: (value: string) => <Tag color={value === 'backend' ? 'blue' : 'purple'}>{value}</Tag>
      },
      { title: 'Key', dataIndex: 'key', key: 'key', width: 280, ellipsis: true },
      { title: '类型', dataIndex: 'type', key: 'type', width: 90 },
      {
        title: 'TTL',
        dataIndex: 'ttl',
        key: 'ttl',
        width: 90,
        render: (value: number | null) => (value === null || value === undefined ? '-' : value)
      },
      {
        title: '值预览',
        dataIndex: 'preview',
        key: 'preview',
        render: (value: string) => <div className="redis-preview-cell">{value || '-'}</div>
      }
    ],
    []
  );

  const inferenceSummary = dashboard?.inference?.summary;
  const performanceData = dashboard?.inference?.performance;
  const performanceSummary = performanceData?.summary;
  const redisSummary = dashboard?.redis?.summary;
  const redisErrors = redisSummary?.errors || [];
  const workers = dashboard?.inference?.workers || [];

  const workerOnline = workers.filter((item) => item.status === 'online').length;
  const workerOffline = workers.filter((item) => item.status === 'offline').length;
  const workerUnreachable = workers.filter((item) => item.status === 'unreachable').length;
  const totalWorkers = workers.length;
  const workerOnlineRate = safePercent(workerOnline, totalWorkers);
  const redisConnectedCount = [redisSummary?.backend_connected, redisSummary?.broker_connected].filter(Boolean).length;
  const redisConnectionRate = safePercent(redisConnectedCount, 2);

  const leftDurationPoints = useMemo((): RuntimeLinePoint[] => {
    const timeline = performanceData?.timeline || [];
    if (timeline.length > 0) {
      return timeline.map((item) => ({
        key: item.timestamp,
        label: toTimeLabel(item.timestamp, false),
        value: toSafeNumber(item.avg_duration_ms),
        tooltip: `${formatDateTime(item.timestamp)} · 平均耗时 ${formatDurationMs(item.avg_duration_ms)} · P95 ${formatDurationMs(item.p95_duration_ms)} · 任务 ${item.task_count}`
      }));
    }

    const recentTasks = (performanceData?.recent_tasks || [])
      .filter(
        (item): item is InferenceTaskDurationItem =>
          typeof item?.timestamp === 'string' && typeof item?.duration_ms === 'number'
      )
      .slice(-20);

    return recentTasks.map((item, index) => ({
      key: `${item.timestamp}-${index}`,
      label: toTimeLabel(item.timestamp, true),
      value: toSafeNumber(item.duration_ms),
      tooltip: `${formatDateTime(item.timestamp)} · 耗时 ${formatDurationMs(item.duration_ms)} · ${item.success ? '成功' : '失败'}${item.worker_name ? ` · 节点 ${item.worker_name}` : ''}`
    }));
  }, [performanceData]);

  const rightChartTitle = useMemo(() => {
    const matched = RIGHT_CHART_OPTIONS.find((item) => item.value === rightChartMetric);
    return matched?.label || '指标图表';
  }, [rightChartMetric]);

  const rightChartPoints = useMemo((): RuntimeLinePoint[] => {
    const timeline = performanceData?.timeline || [];
    const workerStats = performanceData?.by_worker || [];
    const methodStats = performanceData?.by_method || [];

    const buildTimelinePoints = (
      items: InferenceTaskTimelineItem[],
      getValue: (item: InferenceTaskTimelineItem) => number,
      getTooltip: (item: InferenceTaskTimelineItem, value: number) => string
    ): RuntimeLinePoint[] =>
      items.map((item) => {
        const value = getValue(item);
        return {
          key: item.timestamp,
          label: toTimeLabel(item.timestamp, false),
          value,
          tooltip: getTooltip(item, value)
        };
      });

    const buildGroupPoints = (
      items: InferenceTaskGroupStatItem[],
      getValue: (item: InferenceTaskGroupStatItem) => number,
      getTooltip: (item: InferenceTaskGroupStatItem, value: number) => string
    ): RuntimeLinePoint[] =>
      items.slice(0, 12).map((item, index) => {
        const value = getValue(item);
        return {
          key: `${item.name}-${index}`,
          label: item.name.length > 12 ? `${item.name.slice(0, 12)}...` : item.name,
          value,
          tooltip: getTooltip(item, value)
        };
      });

    if (rightChartMetric === 'duration_avg_timeline') {
      return leftDurationPoints;
    }
    if (rightChartMetric === 'timeline_task_count') {
      return buildTimelinePoints(
        timeline,
        (item) => toSafeNumber(item.task_count),
        (item, value) =>
          `${formatDateTime(item.timestamp)} · 任务数 ${Math.round(value)} · 成功率 ${formatPercent(item.success_rate)}`
      );
    }
    if (rightChartMetric === 'timeline_success_rate') {
      return buildTimelinePoints(
        timeline,
        (item) => toSafeNumber(item.success_rate),
        (item, value) =>
          `${formatDateTime(item.timestamp)} · 成功率 ${value.toFixed(1)}% · 任务 ${item.task_count}`
      );
    }
    if (rightChartMetric === 'timeline_p95') {
      return buildTimelinePoints(
        timeline,
        (item) => toSafeNumber(item.p95_duration_ms),
        (item, value) =>
          `${formatDateTime(item.timestamp)} · P95 ${formatDurationMs(value)} · 平均 ${formatDurationMs(item.avg_duration_ms)}`
      );
    }
    if (rightChartMetric === 'worker_avg_duration') {
      return buildGroupPoints(
        workerStats,
        (item) => toSafeNumber(item.avg_duration_ms),
        (item, value) =>
          `节点 ${item.name} · 平均 ${formatDurationMs(value)} · P95 ${formatDurationMs(item.p95_duration_ms)} · 成功率 ${formatPercent(item.success_rate)} · 任务 ${item.total_tasks}`
      );
    }
    return buildGroupPoints(
      methodStats,
      (item) => toSafeNumber(item.avg_duration_ms),
      (item, value) =>
        `方法 ${item.name} · 平均 ${formatDurationMs(value)} · P95 ${formatDurationMs(item.p95_duration_ms)} · 成功率 ${formatPercent(item.success_rate)} · 任务 ${item.total_tasks}`
    );
  }, [leftDurationPoints, performanceData, rightChartMetric]);

  const tabItems = [
    {
      key: 'workers',
      label: '推理机状态',
      children: (
        <div>
          <div className="inference-meta-row">
            <Space size={16}>
              <Text type="secondary">推理队列: {inferenceSummary?.queue || '-'}</Text>
              <Text type="secondary">预期节点: {inferenceSummary?.expected_workers ?? 0}</Text>
              <Text type="secondary">自动发现异常节点: {inferenceSummary?.unexpected_workers ?? 0}</Text>
              <Text type="secondary">
                最近检查: {inferenceSummary?.checked_at ? new Date(inferenceSummary.checked_at).toLocaleString() : '-'}
              </Text>
            </Space>
          </div>
          {inferenceSummary?.inspect_error ? (
            <Alert
              type="warning"
              showIcon
              message="Celery inspect 连接异常"
              description={inferenceSummary.inspect_error}
              style={{ marginBottom: 16 }}
            />
          ) : null}
          <Table
            rowKey="worker_name"
            loading={loading}
            columns={workerColumns}
            dataSource={dashboard?.inference?.workers || []}
            pagination={{
              pageSize: 8,
              showTotal: (total) => `共 ${total} 台推理机`
            }}
          />
        </div>
      )
    },
    {
      key: 'redis-overview',
      label: 'Redis数据库',
      children: (
        <Table
          rowKey={(record) => `${record.name}-${record.db_index}`}
          loading={loading}
          columns={redisDbColumns}
          dataSource={dashboard?.redis?.databases || []}
          pagination={false}
        />
      )
    },
    {
      key: 'business-data',
      label: '会话与任务',
      children: (
        <div className="runtime-double-table">
          <UnifiedCard title="工作流会话样本">
            <Table
              rowKey="key"
              loading={loading}
              columns={sessionColumns}
              dataSource={dashboard?.redis?.workflow_sessions || []}
              pagination={{ pageSize: 5, showTotal: (total) => `共 ${total} 条` }}
            />
          </UnifiedCard>
          <UnifiedCard title="异步任务样本">
            <Table
              rowKey="key"
              loading={loading}
              columns={asyncTaskColumns}
              dataSource={dashboard?.redis?.async_tasks || []}
              pagination={{ pageSize: 5, showTotal: (total) => `共 ${total} 条` }}
            />
          </UnifiedCard>
        </div>
      )
    },
    {
      key: 'redis-keys',
      label: 'Redis Key样本',
      children: (
        <Table
          rowKey={(record) => `${record.database}:${record.key}`}
          loading={loading}
          columns={keySampleColumns}
          dataSource={dashboard?.redis?.key_samples || []}
          pagination={{ pageSize: 8, showTotal: (total) => `共 ${total} 条样本` }}
        />
      )
    }
  ];

  return (
    <div className="inference-worker-step">
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <ClusterOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">运行监控</h2>
              <p className="unified-step-description">集中查看推理节点连通性与 Redis 运行数据</p>
            </div>
          </div>
          <div className="unified-step-actions">
            <Space>
              <span className="auto-refresh-label">自动刷新</span>
              <Switch checked={autoRefresh} onChange={setAutoRefresh} />
              <Button icon={<ReloadOutlined />} onClick={() => loadStatus(true)} loading={refreshing}>
                刷新
              </Button>
            </Space>
          </div>
        </div>
      </UnifiedCard>

      {errorMessage && (
        <Alert
          type="error"
          showIcon
          message="运行监控数据获取失败"
          description={errorMessage}
          style={{ marginBottom: 16 }}
        />
      )}

      {redisErrors.length > 0 ? (
        <Alert
          type="warning"
          showIcon
          message="Redis连接告警"
          description={redisErrors.join('；')}
          style={{ marginBottom: 16 }}
        />
      ) : null}

      <div className="runtime-chart-grid">
        <UnifiedCard title="推理机运行统计" className="runtime-chart-card">
          <div className="runtime-gauge-grid">
            <div className="runtime-gauge-item">
              <Progress
                type="dashboard"
                percent={workerOnlineRate}
                strokeColor={workerOnlineRate >= 80 ? '#10b981' : workerOnlineRate >= 40 ? '#f59e0b' : '#ef4444'}
                format={(percent) => `${percent ?? 0}%`}
              />
              <div className="runtime-gauge-label">推理机在线率</div>
              <div className="runtime-gauge-sub">
                在线 {workerOnline} / 总数 {totalWorkers}（离线 {workerOffline}，不可达 {workerUnreachable}）
              </div>
            </div>

            <div className="runtime-gauge-item">
              <Progress
                type="dashboard"
                percent={redisConnectionRate}
                strokeColor={redisConnectionRate === 100 ? '#10b981' : '#f59e0b'}
                format={(percent) => `${percent ?? 0}%`}
              />
              <div className="runtime-gauge-label">Redis 连接健康度</div>
              <div className="runtime-gauge-sub">
                Backend {redisSummary?.backend_connected ? '正常' : '异常'} / Broker {redisSummary?.broker_connected ? '正常' : '异常'}
              </div>
            </div>
          </div>
        </UnifiedCard>

        <UnifiedCard title="可切换运行指标图表" className="runtime-chart-card">
          {performanceSummary?.error ? (
            <Alert
              type="warning"
              showIcon
              message="推理耗时数据读取异常"
              description={performanceSummary.error}
              style={{ marginBottom: 12 }}
            />
          ) : null}
          <div className="runtime-chart-switcher">
            <Segmented
              options={RIGHT_CHART_OPTIONS}
              value={rightChartMetric}
              onChange={(value) => setRightChartMetric(value as RightChartMetric)}
            />
          </div>
          <RuntimeLineChart points={rightChartPoints} color="#0ea5a4" emptyText="暂无该指标图表数据。" />
          <div className="duration-note">
            当前指标：{rightChartTitle}
            {performanceSummary?.last_timestamp ? ` · 最近任务 ${formatDateTime(performanceSummary.last_timestamp)}` : ''}
            {performanceSummary?.last_worker_name ? ` · 节点 ${performanceSummary.last_worker_name}` : ''}
          </div>
        </UnifiedCard>
      </div>

      <UnifiedCard title="运行监控仪表盘">
        <div className="inference-meta-row">
          <Text type="secondary">
            总检查时间: {dashboard?.checked_at ? new Date(dashboard.checked_at).toLocaleString() : '-'}
          </Text>
        </div>
        <Tabs items={tabItems} />
      </UnifiedCard>

      {onPrev ? (
        <div className="step-actions">
          <Space>
            <Button onClick={onPrev}>上一步</Button>
          </Space>
        </div>
      ) : null}
    </div>
  );
};

export default InferenceWorkerStep;
