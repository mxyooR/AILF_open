/**
 * API路由管理相关类型定义
 */

// 处理器类型
export type HandlerType = 'entity_crud' | 'custom_function' | 'proxy' | 'workflow' | 'static_data' | 'script' | 'file_upload' | 'file_download' | 'image_display' | 'media_streaming';

// HTTP方法类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// 路由状态
export type RouteStatus = 'active' | 'inactive' | 'maintenance' | 'deprecated';

// 健康状态
export type HealthStatus = 'healthy' | 'warning' | 'unhealthy' | 'unknown';

// 参数位置
export type ParameterLocation = 'query' | 'path' | 'header' | 'body';

// API参数定义
export interface APIParameter {
  name: string;
  type: string;
  location: ParameterLocation;
  required: boolean;
  description: string;
}

// 处理器配置
export interface HandlerConfig {
  type: HandlerType;
  config: Record<string, any>;
}

// 响应条件
export interface ResponseCondition {
  type: 'parameter' | 'header' | 'user_role' | 'time' | 'random' | 'data_count';
  field?: string; // 支持 field 别名
  field_name?: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'in' | 'not_in' | 'contains' | 'exists' | 'not_exists';
  value: any;
}

// 响应模板
export interface ResponseTemplate {
  status_code: number;
  body_template: Record<string, any>; // 改为 body_template
  headers?: Record<string, string>;
}

// 动态响应规则
export interface DynamicResponseRule {
  id?: string;
  name: string;
  description?: string;
  priority: number;
  enabled: boolean;
  conditions: ResponseCondition[];
  response_template: ResponseTemplate; // 改为 response_template
}

// 响应定义
export interface ResponseDefinition {
  [statusCode: string]: {
    description: string;
    schema: Record<string, any>;
  };
}

// 权限定义
export interface RoutePermission {
  resource: string;
  action: string;
  description: string;
}

// 权限配置
export interface RoutePermissionConfig {
  required_permissions?: RoutePermission[];
  required_roles?: string[];
  min_role_level?: number;
  allow_developer?: boolean;
}



// API路由创建请求
export interface APIRouteCreateRequest {
  api_id: string;
  name: string;
  endpoint: string;
  method: HttpMethod;
  description: string;
  auth_required: boolean;
  permission_config?: RoutePermissionConfig;
  handler: HandlerConfig;
  parameters: APIParameter[];
  responses: ResponseDefinition;
  dynamic_rules?: DynamicResponseRule[];
}

// API路由更新请求
export interface APIRouteUpdateRequest {
  name?: string;
  description?: string;
  auth_required?: boolean;
  permission_config?: RoutePermissionConfig;
  handler?: HandlerConfig;
  parameters?: APIParameter[];
  responses?: ResponseDefinition;
  dynamic_rules?: DynamicResponseRule[];
}

// API路由基本信息
export interface APIRoute {
  id: string;
  api_id: string;
  name: string;
  endpoint: string;
  method: HttpMethod;
  description: string;
  auth_required: boolean;
  permission_config?: RoutePermissionConfig;
  status: RouteStatus;
  handler?: HandlerConfig;
  parameters?: APIParameter[];
  responses?: ResponseDefinition;
  dynamic_rules?: DynamicResponseRule[];
  handler_type?: string;
  call_count?: number;
  last_called?: string;
  avg_response_time?: number;
  created_at: string;
  updated_at: string;
}

// 路由统计信息
export interface RouteStatistics {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  avg_response_time: number;
  min_response_time: number;
  max_response_time: number;
  last_called: string;
  calls_today: number;
  calls_this_hour: number;
}

// 路由性能信息
export interface RoutePerformance {
  health_status: HealthStatus;
  error_rate: number;
  recent_errors: Array<{
    timestamp: string;
    error: string;
    message: string;
  }>;
  response_time_trend: string;
  load_level: string;
}

// 路由状态详情
export interface RouteStatusDetail {
  route: Pick<APIRoute, 'id' | 'api_id' | 'name' | 'endpoint' | 'method' | 'status'>;
  statistics: RouteStatistics;
  performance: RoutePerformance;
}

// 分页信息
export interface Pagination {
  page: number;
  limit: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// 路由列表响应
export interface RouteListResponse {
  routes: APIRoute[];
  pagination: Pagination;
  summary: {
    total_routes: number;
    active_routes: number;
    inactive_routes: number;
    total_calls: number;
    avg_response_time: number;
  };
}

// 路由健康检查响应
export interface RouteHealthResponse {
  overall_status: HealthStatus;
  total_routes: number;
  healthy_routes: number;
  warning_routes: number;
  unhealthy_routes: number;
  inactive_routes: number;
  system_metrics: {
    total_requests: number;
    avg_response_time: number;
    success_rate: number;
    error_rate: number;
  };
  route_status: Array<{
    id: string;
    api_id: string;
    endpoint: string;
    method: HttpMethod;
    status: RouteStatus;
    health: HealthStatus;
    success_rate: number;
    avg_response_time: number;
    issues?: string[];
  }>;
  recommendations: string[];
}

// 路由查询参数
export interface RouteQueryParams {
  status?: RouteStatus;
  method?: HttpMethod;
  entity?: string;
  search?: string;
  page?: number;
  limit?: number;
}

// API响应基础结构
export interface APIResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// 处理器类型配置示例
export const HandlerTypeConfigs: Record<HandlerType, { label: string; example: Record<string, any> }> = {
  entity_crud: {
    label: '实体CRUD操作',
    example: {
      entity: 'product',
      operation: 'list',
      default_limit: 20,
      max_limit: 100,
      allowed_filters: ['category', 'status', 'price_range'],
      allowed_sorts: ['name', 'price', 'created_at'],
      query_field: 'product_number',
      query_param: 'product_id',
      query_location: 'path'
    }
  },
  custom_function: {
    label: '自定义函数',
    example: {
      service: 'payment_service',
      method: 'refund_payment'
    }
  },
  proxy: {
    label: '代理转发',
    example: {
      target_url: 'http://api.example.com',
      timeout: 30,
      headers: {}
    }
  },
  workflow: {
    label: '工作流触发',
    example: {
      workflow_id: 'workflow_123',
      auto_start: true
    }
  },
  static_data: {
    label: '静态数据返回',
    example: {
      data: {
        message: 'Hello World',
        timestamp: '2024-01-20T10:00:00Z'
      }
    }
  },
  script: {
    label: '脚本执行',
    example: {
      language: 'python',
      script: 'result = {"message": "ok"}'
    }
  },
  file_upload: {
    label: '文件上传',
    example: {
      upload_path: '/',
      allowed_extensions: ['.jpg', '.png', '.pdf', '.doc'],
      max_file_size: '10MB',
      auto_rename: true
    }
  },
  file_download: {
    label: '文件下载',
    example: {
      file_root: '/',
      security_check: true,
      disposition: 'attachment'
    }
  },
  image_display: {
    label: '图片显示',
    example: {
      image_root: '/images',
      resize_options: {
        width: 800,
        height: 600,
        quality: 85
      },
      cache_duration: 3600
    }
  },
  media_streaming: {
    label: '媒体流',
    example: {
      media_root: '/media',
      stream_buffer: '1MB',
      supported_formats: ['mp4', 'mp3', 'wav']
    }
  }
};
