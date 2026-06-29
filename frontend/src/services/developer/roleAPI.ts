/**
 * 角色管理 API 服务
 */

import { apiClient } from '../common/apiClient';

// 角色数据类型定义
export interface Role {
  id: string;
  name: string;
  code: string;
  description?: string;
  status: 'active' | 'inactive' | 'deprecated' | 'locked';
  user_count: number;
  permission_count?: number;
  permissions?: string[] | Permission[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  granted_at?: string;
}

export interface CreateRoleRequest {
  name: string;
  code: string;
  description?: string;
  status?: string;
  permissions?: string[];
  metadata?: Record<string, any>;
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  status?: string;
  metadata?: Record<string, any>;
}

export interface RoleListResponse {
  roles: Role[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  summary: {
    total_roles: number;
    active_roles: number;
    inactive_roles: number;
    total_users: number;
    avg_permissions_per_role: number;
  };
}

export interface RolePermissionsResponse {
  role: {
    id: string;
    name: string;
    code: string;
  };
  permissions: Permission[];
  summary: {
    total_permissions: number;
    by_resource: Record<string, number>;
    by_action: Record<string, number>;
  };
}

export interface AssignPermissionsRequest {
  permissions: string[];
  replace?: boolean;
}

// 角色管理 API 类
export class RoleAPI {
  private static baseURL = '/api/v1/roles';

  /**
   * 创建新角色
   */
  static async createRole(data: CreateRoleRequest): Promise<Role> {
    const response = await apiClient.post<{ role: Role }>(this.baseURL, data);
    return response.data.role;
  }

  /**
   * 获取角色列表
   */
  static async getRoles(params?: {
    status?: string;
    department?: string;
    page?: number;
    limit?: number;
    sort?: string;
  }): Promise<RoleListResponse> {
    const response = await apiClient.get<RoleListResponse>(this.baseURL, { params });
    return response.data;
  }

  /**
   * 获取角色详情
   */
  static async getRole(
    roleId: string,
    params?: {
      include_users?: boolean;
      include_permissions?: boolean;
    }
  ): Promise<Role> {
    const response = await apiClient.get<{ role: Role }>(`${this.baseURL}/${roleId}`, { params });
    return response.data.role;
  }

  /**
   * 更新角色信息
   */
  static async updateRole(roleId: string, data: UpdateRoleRequest): Promise<Role> {
    const response = await apiClient.put<{ role: Role }>(`${this.baseURL}/${roleId}`, data);
    return response.data.role;
  }

  /**
   * 删除角色
   */
  static async deleteRole(
    roleId: string,
    params?: {
      force?: boolean;
      reassign_to?: string;
    }
  ): Promise<void> {
    await apiClient.delete<void>(`${this.baseURL}/${roleId}`, { params });
  }

  /**
   * 获取角色权限列表
   */
  static async getRolePermissions(
    roleId: string,
    params?: {
      resource?: string;
      action?: string;
    }
  ): Promise<RolePermissionsResponse> {
    const response = await apiClient.get<RolePermissionsResponse>(`${this.baseURL}/${roleId}/permissions`, { params });
    return response.data;
  }

  /**
   * 为角色分配权限
   */
  static async assignPermissions(
    roleId: string,
    data: AssignPermissionsRequest
  ): Promise<{
    role: { id: string; name: string; code: string };
    permissions: {
      added: string[];
      existing: string[];
      total: number;
    };
  }> {
    const response = await apiClient.post<{
      role: { id: string; name: string; code: string };
      permissions: {
        added: string[];
        existing: string[];
        total: number;
      };
    }>(`${this.baseURL}/${roleId}/permissions`, data);
    return response.data;
  }

  /**
   * 移除角色权限
   */
  static async removePermission(roleId: string, permissionId: string): Promise<void> {
    await apiClient.delete<void>(`${this.baseURL}/${roleId}/permissions/${permissionId}`);
  }
}

export default RoleAPI;
