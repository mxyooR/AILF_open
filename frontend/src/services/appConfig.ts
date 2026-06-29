/**
 * 应用配置API - 简单版本
 */

import { API_BASE_URL } from '../config/api';

export type BackgroundStyle = 'mesh' | 'ribbon';

export interface AppConfig {
  title: string;
  subtitle: string;
  backgroundStyle?: BackgroundStyle; // 'mesh' = 原版渐变, 'ribbon' = 蓝紫丝带
}

export const appConfigAPI = {
  // 获取应用配置
  async getAppConfig(): Promise<AppConfig> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/app`);
    const data = await response.json();
    return data.data;
  },

  // 更新应用配置
  async updateAppConfig(config: AppConfig): Promise<AppConfig> {
    // 使用统一的TokenManager获取token
    const { tokenManager } = await import('./common/tokenManager');

    // 检查是否已认证
    if (!tokenManager.isAuthenticated()) {
      throw new Error('未认证，请先完成开发者认证');
    }

    const token = tokenManager.getToken();
    if (!token) {
      throw new Error('无效的认证令牌');
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/config/app`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      throw new Error('更新配置失败');
    }

    const data = await response.json();
    return data.data;
  }
};
