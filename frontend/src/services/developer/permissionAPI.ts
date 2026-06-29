/**
 * 权限管理 API 服务
 */

import { apiClient } from '../common/apiClient';

// 权限数据类型定义
export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description: string;
  granted_at?: string;
}

export interface ApiRoute {
  id: string;
  api_id: string;
  name: string;
  endpoint: string;
  method: string;
  description: string;
  auth_required: boolean;
  is_public?: boolean;  // 是否为公开路由（不需要权限，所有用户可访问）
  status: 'active' | 'inactive' | 'maintenance' | 'deprecated';
  handler_type: string;
  call_count?: number;
  last_called?: string;
  avg_response_time?: number;
  created_at: string;
  updated_at: string;
}

export interface RolePermission {
  role_id: string;
  api_id: string;
  permission: string;
  granted: boolean;
  granted_at?: string;
  granted_by?: string;
}

export interface PermissionMatrix {
  roles: Array<{
    id: string;
    name: string;
    code: string;
    level: number;
  }>;
  apis: ApiRoute[];
  permissions: Record<string, Record<string, boolean>>;
}

export interface UserApiPermissions {
  user: {
    id: string;
    name: string;
    roles: Array<{
      id: string;
      name: string;
      code: string;
      level: number;
    }>;
  };
  accessible_apis: Array<{
    api_id: string;
    name: string;
    endpoint: string;
    method: string;
    resource: string;
    action: string;
    permission: string;
    granted_by: string;
  }>;
  summary: {
    total_apis: number;
    by_resource: Record<string, number>;
    by_method: Record<string, number>;
    permissions: string[];
  };
}

export interface BatchUpdateRequest {
  updates: Array<{
    role_id: string;
    api_id: string;
    permission: string;
    action: 'grant' | 'revoke';
  }>;
  dry_run?: boolean;
}

export interface BatchUpdateResponse {
  results: Array<{
    role_id: string;
    api_id: string;
    permission: string;
    action: string;
    status: 'success' | 'failed';
    message: string;
    error?: string;
  }>;
  summary: {
    total: number;
    successful: number;
    failed: number;
    granted: number;
    revoked: number;
  };
}

// 权限管理 API 类
export class PermissionAPI {
  /**
   * 检查用户是否有访问特定API的权限
   */
  static async checkPermission(data: {
    user_id: string;
    resource: string;
    action: string;
    context?: Record<string, any>;
  }): Promise<{
    allowed: boolean;
    user: any;
    permission: any;
    context?: any;
    checked_at: string;
  }> {
    const response = await apiClient.post<{
      allowed: boolean;
      user: any;
      permission: any;
      context?: any;
      checked_at: string;
    }>('/api/v1/permissions/check', data);
    return response.data;
  }

  /**
   * 获取指定用户可以访问的API列表
   */
  static async getUserApiPermissions(params: {
    user_id: string;
    resource?: string;
    method?: string;
    include_details?: boolean;
  }): Promise<UserApiPermissions> {
    const response = await apiClient.get<UserApiPermissions>('/api/v1/permissions/user-apis', { params });
    return response.data;
  }

  /**
   * 更新角色对特定API的访问权限
   */
  static async updateRoleApiPermission(data: {
    role_id: string;
    api_id: string;
    permission: string;
    action: 'grant' | 'revoke';
  }): Promise<{
    role: any;
    api: any;
    permission: any;
  }> {
    const response = await apiClient.post<{
      role: any;
      api: any;
      permission: any;
    }>('/api/v1/permissions/role-api', data);
    return response.data;
  }

  /**
   * 批量更新多个角色的API权限
   */
  static async batchUpdatePermissions(data: BatchUpdateRequest): Promise<BatchUpdateResponse> {
    const response = await apiClient.post<BatchUpdateResponse>('/api/v1/permissions/batch-update', data);
    return response.data;
  }

  /**
   * 获取完整的权限矩阵
   */
  static async getPermissionMatrix(): Promise<{
    matrix: PermissionMatrix;
  }> {
    const response = await apiClient.get<{
      matrix: PermissionMatrix;
    }>('/api/v1/permissions/matrix');
    return response.data;
  }


  /**
   * 更新权限矩阵
   */
  static async updatePermissionMatrix(data: {
    matrix: Record<string, Record<string, boolean>>;
    merge_mode?: 'replace' | 'merge';
  }): Promise<{
    updated_permissions: Record<string, any>;
    summary: {
      roles_updated: number;
      permissions_granted: number;
      permissions_revoked: number;
      total_changes: number;
    };
    updated_at: string;
  }> {
    const response = await apiClient.post<{
      updated_permissions: Record<string, any>;
      summary: any;
      updated_at: string;
    }>('/api/v1/permissions/matrix', data);
    return response.data;
  }
}

// API路由管理 API 类
export class ApiRouteAPI {
  private static baseURL = '/api/v1/routes';

  /**
   * 获取所有API路由
   */
  static async getRoutes(params?: {
    status?: string;
    method?: string;
    entity?: string;
    page?: number;
    limit?: number;
  }): Promise<{
    routes: ApiRoute[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
    summary: {
      total_routes: number;
      active_routes: number;
      inactive_routes: number;
      total_calls: number;
      avg_response_time: number;
    };
  }> {
    const response = await apiClient.get<{
      routes: ApiRoute[];
      pagination: any;
      summary: any;
    }>(this.baseURL, { params });
    return response.data;
  }

  /**
   * 获取API路由详情
   */
  static async getRoute(routeId: string): Promise<ApiRoute> {
    const response = await apiClient.get<{ route: ApiRoute }>(`${this.baseURL}/${routeId}`);
    return response.data.route;
  }

  /**
   * 获取API路由状态
   */
  static async getRouteStatus(routeId: string): Promise<{
    route: ApiRoute;
    statistics: any;
    performance: any;
  }> {
    const response = await apiClient.get<{
      route: ApiRoute;
      statistics: any;
      performance: any;
    }>(`${this.baseURL}/${routeId}/status`);
    return response.data;
  }

  /**
   * 检查所有API路由健康状态
   */
  static async getHealthStatus(): Promise<{
    overall_status: string;
    total_routes: number;
    healthy_routes: number;
    warning_routes: number;
    unhealthy_routes: number;
    inactive_routes: number;
    system_metrics: any;
    route_status: any[];
    recommendations: string[];
  }> {
    const response = await apiClient.get<{
      overall_status: string;
      total_routes: number;
      healthy_routes: number;
      warning_routes: number;
      unhealthy_routes: number;
      inactive_routes: number;
      system_metrics: any;
      route_status: any[];
      recommendations: string[];
    }>(`${this.baseURL}/health`);
    return response.data;
  }
}

export default PermissionAPI;
