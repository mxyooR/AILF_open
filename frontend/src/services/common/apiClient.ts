/**
 * 统一API客户端
 */

import { API_BASE_URL } from '../../config/api';
import { normalizeAmisResponse } from './amisTransport';

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
  }

  /**
   * 设置普通用户Token
   */
  setUserToken(token: string | null) {
    this.userToken = token;
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
    const headers = new Headers(options.headers);
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

    // 用户中心和个人通知始终使用用户身份，防止同一浏览器的开发者登录串入个人页面。
    const isUserEndpoint = /^\/api\/v1\/(?:user(?:\/|$)|notifications(?:[/?]|$))/.test(endpoint);
    const activeToken = isUserEndpoint ? this.userToken : this.getActiveToken();
    if (activeToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${activeToken}`);
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const text = await response.text();
      let data: any = { code: response.status, message: '', data: null };
      if (text) {
        try { data = JSON.parse(text); }
        catch { throw new APIError('服务返回了无效响应', response.status, 'INVALID_RESPONSE'); }
      }

      // 认证接口自身不走自动刷新，避免 refresh 请求递归
      const isAuthEndpoint = endpoint.startsWith('/api/v1/auth/');

      // 处理401错误（token过期）
      if (response.status === 401 && retryCount === 0 && this.tokenRefreshCallback && !isAuthEndpoint && !isUserEndpoint && !new Headers(options.headers).has('Authorization')) {
        console.log('Token expired, attempting refresh...');
        const newToken = await this.refreshTokenIfNeeded();

        if (newToken) {
          // 使用新token重试请求
          return this.request(endpoint, options, retryCount + 1);
        }
      }

      if (!response.ok) {
        throw new APIError(
          data.message || data.msg || data.detail || '请求失败',
          response.status,
          data.data?.error || 'UNKNOWN_ERROR'
        );
      }

      // 统一拦截 HTTP 200 中的业务失败，避免页面误删记录、清空表单或提示保存成功。
      const result = normalizeAmisResponse(data);
      if (result.status !== 0) {
        throw new APIError(result.msg || '业务操作失败', result.status, data.data?.error || 'BUSINESS_ERROR');
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError('网络请求失败', 0, 'NETWORK_ERROR');
    }
  }

  /** 动态路由测试使用真实 HTTP 方法，并保留查询参数、调用方认证头和超时。 */
  async execute<T>(endpoint: string, options: {
    method: string; params?: Record<string, any>; data?: any;
    headers?: Record<string, string>; timeout?: number;
  }): Promise<APIResponse<T>> {
    const query = new URLSearchParams();
    Object.entries(options.params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) query.append(key, String(value));
    });
    const url = query.toString() ? `${endpoint}${endpoint.includes('?') ? '&' : '?'}${query}` : endpoint;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), options.timeout ?? 10000);
    try {
      const method = options.method.toUpperCase();
      return await this.request<T>(url, {
        method, headers: options.headers, signal: controller.signal,
        body: method === 'GET' || method === 'HEAD' || options.data === undefined ? undefined : JSON.stringify(options.data),
      });
    } finally {
      clearTimeout(timer);
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
  return tokenManager.refreshToken();
});

// 在开发环境中将apiClient暴露到window对象，便于调试
if (process.env.NODE_ENV === 'development') {
  (window as any).apiClient = apiClient;
}

export default apiClient;
