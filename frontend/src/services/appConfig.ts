/**
 * 应用配置API - 简单版本
 */

import { API_BASE_URL } from '../config/api';
import { normalizeAmisResponse } from './common/amisTransport';

export type BackgroundStyle = 'mesh' | 'ribbon';

export interface AppConfig {
  title: string;
  subtitle: string;
  backgroundStyle?: BackgroundStyle; // 'mesh' = 原版渐变, 'ribbon' = 蓝紫丝带
}

/** 先校验 HTTP、业务状态和字段，避免异常响应把首页默认配置替换成 undefined。 */
async function readAppConfig(response: Response): Promise<AppConfig> {
  const payload = await response.json();
  const result = normalizeAmisResponse(payload);
  if (!response.ok || result.status !== 0) {
    throw new Error(result.msg || payload?.detail || '读取应用配置失败');
  }
  const config = payload?.data;
  if (!config || typeof config.title !== 'string' || typeof config.subtitle !== 'string'
    || (config.backgroundStyle != null && !['mesh', 'ribbon'].includes(config.backgroundStyle))) {
    throw new Error('应用配置格式不正确');
  }
  return { ...config, backgroundStyle: config.backgroundStyle || 'mesh' };
}

export const appConfigAPI = {
  // 获取应用配置
  async getAppConfig(): Promise<AppConfig> {
    const response = await fetch(`${API_BASE_URL}/api/v1/config/app`);
    return readAppConfig(response);
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

    return readAppConfig(response);
  }
};
