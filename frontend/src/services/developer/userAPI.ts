/**
 * 用户管理API服务
 */

import { apiClient } from '../common/apiClient';

// 用户数据类型定义
export interface User {
  id: number;
  username: string;
  email: string;
  real_name?: string;
  phone?: string;
  is_active: boolean;
  is_verified?: boolean;
  avatar_url?: string;
  bio?: string;
  settings?: string;
  password_hash?: string;
  role: {
    id: string;
    name: string;
    code: string;
    description?: string;
  };
  created_at: string;
  updated_at?: string;
  last_login?: string;
  created_by?: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  phone?: string;
  real_name?: string;
  role_id: string;
  is_active?: boolean;
}

export interface UpdateUserRequest {
  real_name?: string;
  phone?: string;
  is_active?: boolean;
}

export interface AvailableRole {
  id: string;
  name: string;
  code: string;
  description?: string;
  user_count: number;
}

export interface UsersListResponse {
  users: User[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface AvailableRolesResponse {
  roles: AvailableRole[];
  total: number;
}

export interface UserFormField {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  placeholder?: string;
  options?: Array<{label: string; value: any}>;
  validations?: any;
  minLength?: number;
  maxLength?: number;
  value?: any;
}

export interface UserFormSchema {
  entity_id?: string;
  entity_name: string;
  display_name: string;
  fields: UserFormField[];
}

export interface UserTableColumn {
  name: string;
  label: string;
  type: string;
  map?: any;
}

/**
 * 用户管理API类
 */
export class UserAPI {
  /**
   * 获取用户列表
   */
  static async getUsersList(params?: {
    page?: number;
    limit?: number;
    role_id?: string;
    status?: string;
    search?: string;
  }): Promise<UsersListResponse> {
    const response = await apiClient.get<UsersListResponse>('/api/v1/users', { params });
    return response.data;
  }

  /**
   * 创建用户
   */
  static async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await apiClient.post<User>('/api/v1/users', userData);
    return response.data;
  }

  /**
   * 获取用户详情
   */
  static async getUserDetail(userId: number): Promise<User> {
    const response = await apiClient.get<User>(`/api/v1/users/${userId}`);
    return response.data;
  }

  /**
   * 更新用户角色
   */
  static async updateUserRole(userId: number, roleId: string): Promise<any> {
    const response = await apiClient.put<any>(`/api/v1/users/${userId}/role?role_id=${roleId}`);
    return response.data;
  }

  /**
   * 更新用户状态
   */
  static async updateUserStatus(userId: number, isActive: boolean): Promise<any> {
    const response = await apiClient.put<any>(`/api/v1/users/${userId}/status?is_active=${isActive}`);
    return response.data;
  }

  /**
   * 删除用户
   */
  static async deleteUser(userId: number): Promise<any> {
    const response = await apiClient.delete<any>(`/api/v1/users/${userId}`);
    return response.data;
  }

  /**
   * 更新用户密码
   */
  static async updateUserPassword(userId: number, newPassword: string): Promise<any> {
    const response = await apiClient.put(`/api/v1/users/${userId}/password`, {
      new_password: newPassword
    });
    return response.data;
  }

  /**
   * 获取可用角色列表
   */
  static async getAvailableRoles(): Promise<AvailableRolesResponse> {
    const response = await apiClient.get<AvailableRolesResponse>('/api/v1/users/roles/available');
    return response.data;
  }

  /**
   * 获取用户表单schema
   */
  static async getUserFormSchema(roleId?: string): Promise<UserFormSchema> {
    const params = roleId ? { role_id: roleId } : {};
    const response = await apiClient.get<UserFormSchema>('/api/v1/users/form-schema', { params });
    return response.data;
  }

  /**
   * 获取用户表格列配置
   */
  static async getUserTableColumns(): Promise<UserTableColumn[]> {
    const response = await apiClient.get<{ columns: UserTableColumn[] }>('/api/v1/users/table-columns');
    return response.data.columns;
  }
}
