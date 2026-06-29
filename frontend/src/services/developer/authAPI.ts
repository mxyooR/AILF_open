/**
 * 开发者认证API服务
 */

import { apiClient } from '../common/apiClient';
import type {
  DeveloperAuthRequest,
  DeveloperAuthResponse,
  TokenRefreshRequest,
  TokenVerifyRequest,
  TokenVerifyResponse,
} from '../../types/developer/auth';

export const authAPI = {
  /**
   * 开发者认证
   * POST /api/v1/auth/developer
   */
  async authenticate(request: DeveloperAuthRequest): Promise<DeveloperAuthResponse> {
    const response = await apiClient.post<DeveloperAuthResponse['data']>(
      '/api/v1/auth/developer',
      request
    );
    return response;
  },

  /**
   * 验证开发者令牌
   * POST /api/v1/auth/developer/verify-token
   */
  async verifyToken(request: TokenVerifyRequest): Promise<TokenVerifyResponse> {
    const response = await apiClient.post<TokenVerifyResponse['data']>(
      '/api/v1/auth/developer/verify-token',
      request
    );
    return response;
  },

  /**
   * 刷新开发者令牌
   * POST /api/v1/auth/developer/refresh-token
   */
  async refreshToken(request: TokenRefreshRequest): Promise<DeveloperAuthResponse> {
    const response = await apiClient.post<DeveloperAuthResponse['data']>(
      '/api/v1/auth/developer/refresh-token',
      request
    );
    return response;
  },

  /**
   * 开发者登出
   * POST /api/v1/auth/developer/logout
   */
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/developer/logout');
  },

  /**
   * 设置认证令牌到API客户端
   */
  setAuthToken(token: string | null) {
    apiClient.setDeveloperToken(token);
  },

  /**
   * 获取当前认证令牌
   */
  getAuthToken(): string | null {
    return apiClient.getDeveloperToken();
  },

  /**
   * 初始化认证状态 - 检查tokenManager中的认证状态
   */
  async initAuth(): Promise<boolean> {
    // 动态导入避免循环依赖
    const { tokenManager } = await import('../common/tokenManager');

    if (tokenManager.isAuthenticated()) {
      const token = tokenManager.getToken();
      if (token) {
        this.setAuthToken(token);
        return true;
      }
    }

    return false;
  },

};

export default authAPI;
