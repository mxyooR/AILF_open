/**
 * 注册配置API服务
 */

import { apiClient } from '../common/apiClient';

export interface RegistrationConfig {
  default_role_code: string;
  default_role_info: {
    id: string;
    name: string;
    code: string;
    description: string;
  } | null;
  default_role_fields: Array<{
    name: string;
    display_name: string;
    type: string;
    required: boolean;
    description: string;
  }>;
  allow_public_registration: boolean;
  available_roles: Array<{
    id: string;
    name: string;
    code: string;
    description: string;
    user_count: number;
  }>;
}

export interface UpdateRegistrationConfigRequest {
  default_role_code: string;
  allow_public_registration: boolean;
}

export interface RegistrationConfigResponse {
  success: boolean;
  data: RegistrationConfig;
}

export interface UpdateRegistrationConfigResponse {
  success: boolean;
  message: string;
  data: {
    default_role_code: string;
    allow_public_registration: boolean;
    updated_at: string;
  };
}

export class RegistrationConfigAPI {
  /**
   * 获取当前注册配置
   */
  static async getRegistrationConfig(): Promise<RegistrationConfig> {
    try {
      const response = await apiClient.get<RegistrationConfig>('/api/v1/registration-config/');
      return response.data;
    } catch (error) {
      console.error('获取注册配置失败:', error);
      throw error;
    }
  }

  /**
   * 更新注册配置
   */
  static async updateRegistrationConfig(config: UpdateRegistrationConfigRequest): Promise<UpdateRegistrationConfigResponse> {
    try {
      const response = await apiClient.put<UpdateRegistrationConfigResponse>('/api/v1/registration-config/', config);
      return response.data;
    } catch (error) {
      console.error('更新注册配置失败:', error);
      throw error;
    }
  }

  /**
   * 获取可用于注册的角色列表
   */
  static async getAvailableRoles(): Promise<Array<{
    id: string;
    name: string;
    code: string;
    description: string;
    user_count: number;
    is_default: boolean;
  }>> {
    try {
      const response = await apiClient.get<{
        success: boolean;
        data: Array<{
          id: string;
          name: string;
          code: string;
          description: string;
          user_count: number;
          is_default: boolean;
        }>;
      }>('/registration-config/roles');
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error('获取可用角色列表失败');
      }
    } catch (error) {
      console.error('获取可用角色列表失败:', error);
      throw error;
    }
  }
}
