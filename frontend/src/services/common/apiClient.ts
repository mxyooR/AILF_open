/**
 * 统一API客户端
 */

import { API_BASE_URL } from '../../config/api';

export interface APIResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Token刷新回调类型
export type TokenRefreshCallback = () => Promise<string | null>;

class APIClient {
  private baseURL: string;
  // 双Token机制：开发者token和普通用户token
  private developerToken: string | null = null;
  private userToken: string | null = null;
  private tokenRefreshCallback: TokenRefreshCallback | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * 设置开发者Token
   */
  setDeveloperToken(token: string | null) {
    this.developerToken = token;
    console.log('[APIClient] Developer token updated:', token ? token.substring(0, 20) + '...' : 'null');
  }

  /**
   * 设置普通用户Token
   */
  setUserToken(token: string | null) {
    this.userToken = token;
    console.log('[APIClient] User token updated:', token ? token.substring(0, 20) + '...' : 'null');
  }

  /**
   * 获取当前激活的Token（优先使用开发者token）
   */
  private getActiveToken(): string | null {
    // 开发者token优先级更高
    return this.developerToken || this.userToken;
  }

  /**
   * 兼容旧代码的setToken方法（已废弃，建议使用setDeveloperToken或setUserToken）
   * @deprecated 使用 setDeveloperToken 或 setUserToken 替代
   */
  setToken(token: string | null) {
    console.warn('[APIClient] setToken is deprecated. Use setDeveloperToken or setUserToken instead.');
    this.userToken = token;
  }

  /**
   * 兼容旧代码的getToken方法
   * @deprecated 使用 getActiveToken 替代
   */
  getToken(): string | null {
    return this.getActiveToken();
  }

  /**
   * 获取开发者Token
   */
  getDeveloperToken(): string | null {
    return this.developerToken;
  }

  /**
   * 获取用户Token
   */
  getUserToken(): string | null {
    return this.userToken;
  }

  setTokenRefreshCallback(callback: TokenRefreshCallback | null) {
    this.tokenRefreshCallback = callback;
  }

  private async refreshTokenIfNeeded(): Promise<string | null> {
    if (!this.tokenRefreshCallback) {
      return this.getActiveToken();
    }

    if (this.isRefreshing) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.tokenRefreshCallback();

    try {
      const newToken = await this.refreshPromise;
      // 注意：刷新回调需要自行决定更新哪个token
      return newToken;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // 添加认证头（优先使用开发者token）
    const activeToken = this.getActiveToken();
    if (activeToken) {
      headers.Authorization = `Bearer ${activeToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      // 认证接口自身不走自动刷新，避免 refresh 请求递归
      const isAuthEndpoint = endpoint.startsWith('/api/v1/auth/');

      // 处理401错误（token过期）
      if (response.status === 401 && retryCount === 0 && this.tokenRefreshCallback && !isAuthEndpoint) {
        console.log('Token expired, attempting refresh...');
        const newToken = await this.refreshTokenIfNeeded();

        if (newToken) {
          // 使用新token重试请求
          return this.request(endpoint, options, retryCount + 1);
        }
      }

      if (!response.ok) {
        throw new APIError(
          data.message || '请求失败',
          response.status,
          data.data?.error || 'UNKNOWN_ERROR'
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError('网络请求失败', 0, 'NETWORK_ERROR');
    }
  }

  async get<T>(endpoint: string, options?: { params?: Record<string, any> }): Promise<APIResponse<T>> {
    let url = endpoint;
    if (options?.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (endpoint.includes('?') ? '&' : '?') + queryString;
      }
    }
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string, options?: { params?: Record<string, any> }): Promise<APIResponse<T>> {
    let url = endpoint;
    if (options?.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (endpoint.includes('?') ? '&' : '?') + queryString;
      }
    }
    return this.request<T>(url, { method: 'DELETE' });
  }
}

export const apiClient = new APIClient();

// 设置token刷新回调
apiClient.setTokenRefreshCallback(async () => {
  // 动态导入避免循环依赖
  const { tokenManager } = await import('./tokenManager');
  const tokenInfo = tokenManager.getTokenInfo();

  if (tokenInfo?.refreshToken) {
    try {
      const { authAPI } = await import('../developer/authAPI');
      const response = await authAPI.refreshToken({
        refresh_token: tokenInfo.refreshToken,
      });

      if (response.code === 200) {
        tokenManager.setToken(response.data);
        return response.data.token;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
  }

  // 如果刷新失败，清除token
  tokenManager.clearToken();
  return null;
});

// 在开发环境中将apiClient暴露到window对象，便于调试
if (process.env.NODE_ENV === 'development') {
  (window as any).apiClient = apiClient;
}

export default apiClient;
