/**
 * 用户Token管理器
 * 负责最终用户认证token的存储、验证、刷新等功能
 */

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  real_name?: string;
  phone?: string;
  created_at?: string;
  last_login?: string | null;
  role: {
    id: string;
    name: string;
    code: string;
    permissions?: string[];
  };
}

export interface UserPermissions {
  apis: Array<{
    endpoint: string;
    method: string;
    description: string;
    resource: string;
    action: string;
  }>;
  features: string[];
}

export interface UserTokenInfo {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
  permissions: UserPermissions;
  expires_at?: string; // 计算得出的过期时间
  issued_at?: string;  // 签发时间
}

interface UserTokenManagerConfig {
  storageKey?: string;
  userInfoKey?: string;
  autoRefresh?: boolean;
  refreshThreshold?: number; // 提前多少秒刷新token
}

class UserTokenManager {
  private tokenInfo: UserTokenInfo | null = null;
  private config: Required<UserTokenManagerConfig>;
  private refreshTimer: NodeJS.Timeout | null = null;
  private listeners: Array<(isAuthenticated: boolean, userInfo?: UserInfo) => void> = [];

  constructor(config: UserTokenManagerConfig = {}) {
    this.config = {
      storageKey: config.storageKey || 'ailf_user_token',
      userInfoKey: config.userInfoKey || 'ailf_user_info',
      autoRefresh: config.autoRefresh ?? true,
      refreshThreshold: config.refreshThreshold || 300, // 5分钟
    };

    // 初始化时从存储中恢复token
    this.loadFromStorage();
  }

  /**
   * 从本地存储加载token
   */
  private loadFromStorage(): void {
    try {
      const storedToken = localStorage.getItem(this.config.storageKey);
      const storedUserInfo = localStorage.getItem(this.config.userInfoKey);
      
      if (storedToken && storedUserInfo) {
        const tokenData = JSON.parse(storedToken);
        const userData = JSON.parse(storedUserInfo);
        
        // 重构token信息
        const tokenInfo: UserTokenInfo = {
          access_token: tokenData.access_token || tokenData,
          refresh_token: tokenData.refresh_token,
          token_type: tokenData.token_type || 'bearer',
          expires_in: tokenData.expires_in || 3600,
          user: userData,
          permissions: tokenData.permissions || { apis: [], features: [] },
          expires_at: tokenData.expires_at,
          issued_at: tokenData.issued_at
        };
        
        // 检查token是否过期
        if (this.isTokenValid(tokenInfo)) {
          this.tokenInfo = tokenInfo;
          this.scheduleRefresh();
          console.log('[UserTokenManager] Token restored from storage');
          this.setTokenToApiClient(tokenInfo.access_token);
        } else {
          this.clearStorage();
          console.log('[UserTokenManager] Expired token removed from storage');
        }
      }
    } catch (error) {
      console.error('[UserTokenManager] Failed to load token from storage:', error);
      this.clearStorage();
    }
  }

  /**
   * 保存token到本地存储
   */
  private saveToStorage(): void {
    if (this.tokenInfo) {
      try {
        // 分别存储token和用户信息
        const tokenData = {
          access_token: this.tokenInfo.access_token,
          refresh_token: this.tokenInfo.refresh_token,
          token_type: this.tokenInfo.token_type,
          expires_in: this.tokenInfo.expires_in,
          permissions: this.tokenInfo.permissions,
          expires_at: this.tokenInfo.expires_at,
          issued_at: this.tokenInfo.issued_at
        };
        
        localStorage.setItem(this.config.storageKey, JSON.stringify(tokenData));
        localStorage.setItem(this.config.userInfoKey, JSON.stringify(this.tokenInfo.user));
        
        // 兼容现有代码
        localStorage.setItem('access_token', this.tokenInfo.access_token);
        localStorage.setItem('user_info', JSON.stringify(this.tokenInfo.user));
      } catch (error) {
        console.error('[UserTokenManager] Failed to save token to storage:', error);
      }
    }
  }

  /**
   * 清除本地存储
   */
  private clearStorage(): void {
    localStorage.removeItem(this.config.storageKey);
    localStorage.removeItem(this.config.userInfoKey);
    // 兼容现有代码
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
  }

  /**
   * 检查token是否有效（未过期）
   */
  private isTokenValid(tokenInfo: UserTokenInfo): boolean {
    if (!tokenInfo.expires_at) {
      // 如果没有过期时间，假设token有效（可能需要服务器验证）
      return true;
    }
    
    const now = new Date();
    const expiresAt = new Date(tokenInfo.expires_at);
    return expiresAt > now;
  }

  /**
   * 计算token剩余时间（秒）
   */
  private getRemainingTime(tokenInfo: UserTokenInfo): number {
    if (!tokenInfo.expires_at) {
      return tokenInfo.expires_in || 3600; // 默认1小时
    }
    
    const now = new Date();
    const expiresAt = new Date(tokenInfo.expires_at);
    return Math.max(0, Math.floor((expiresAt.getTime() - now.getTime()) / 1000));
  }

  /**
   * 安排token刷新
   */
  private scheduleRefresh(): void {
    if (!this.config.autoRefresh || !this.tokenInfo) {
      return;
    }

    // 清除现有定时器
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    const remainingTime = this.getRemainingTime(this.tokenInfo);
    const refreshTime = Math.max(0, remainingTime - this.config.refreshThreshold);

    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(() => {
        this.refreshToken();
      }, refreshTime * 1000);
      
      console.log(`[UserTokenManager] Token refresh scheduled in ${refreshTime} seconds`);
    } else {
      // 立即刷新
      this.refreshToken();
    }
  }

  /**
   * 刷新token
   */
  private async refreshToken(): Promise<void> {
    if (!this.tokenInfo) {
      console.error('[UserTokenManager] No token available for refresh.');
      this.clearToken();
      return;
    }

    try {
      console.log('[UserTokenManager] Refreshing user token...');
      
      // 调用用户token刷新API
      const response = await fetch('/api/v1/user/refresh-token', {
        method: 'POST',
        headers: {
          ...(this.tokenInfo.access_token ? { 'Authorization': `Bearer ${this.tokenInfo.access_token}` } : {}),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: this.tokenInfo.refresh_token || null
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200) {
          // 更新token信息
          this.tokenInfo.access_token = data.data.access_token;
          this.tokenInfo.refresh_token = data.data.refresh_token || this.tokenInfo.refresh_token;
          this.tokenInfo.expires_in = data.data.expires_in;
          this.tokenInfo.issued_at = new Date().toISOString();
          this.tokenInfo.expires_at = new Date(Date.now() + data.data.expires_in * 1000).toISOString();
          
          this.saveToStorage();
          this.scheduleRefresh();
          this.setTokenToApiClient(this.tokenInfo.access_token);
          console.log('[UserTokenManager] Token refreshed successfully');
        } else {
          console.error('[UserTokenManager] Token refresh failed:', data.message);
          this.clearToken();
        }
      } else {
        console.error('[UserTokenManager] Token refresh request failed:', response.status);
        this.clearToken();
      }
    } catch (error) {
      console.error('[UserTokenManager] Token refresh error:', error);
      this.clearToken();
    }
  }

  /**
   * 设置用户token到apiClient
   */
  private async setTokenToApiClient(token: string | null): Promise<void> {
    try {
      const { apiClient } = await import('./apiClient');
      apiClient.setUserToken(token);
      if (token) {
        console.log('[UserTokenManager] User token set to apiClient:', token.substring(0, 50) + '...');
      } else {
        console.log('[UserTokenManager] User token cleared from apiClient');
      }
    } catch (error) {
      console.error('[UserTokenManager] Failed to set user token to apiClient:', error);
    }
  }

  /**
   * 设置用户token
   */
  setToken(loginData: UserTokenInfo): void {
    const now = new Date();
    const expiresAt = new Date(now.getTime() + loginData.expires_in * 1000);
    
    this.tokenInfo = {
      ...loginData,
      issued_at: now.toISOString(),
      expires_at: expiresAt.toISOString()
    };

    this.saveToStorage();
    this.scheduleRefresh();
    this.notifyListeners(true, this.tokenInfo.user);
    this.setTokenToApiClient(this.tokenInfo.access_token);
    
    console.log('[UserTokenManager] User token set successfully');
  }

  /**
   * 清除token
   */
  clearToken(): void {
    this.tokenInfo = null;
    this.clearStorage();

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }

    this.notifyListeners(false);
    this.setTokenToApiClient(null);
    
    console.log('[UserTokenManager] User token cleared');
  }

  /**
   * 获取当前token
   */
  getToken(): string | null {
    return this.tokenInfo?.access_token || null;
  }

  /**
   * 获取用户信息
   */
  getUserInfo(): UserInfo | null {
    return this.tokenInfo?.user || null;
  }

  /**
   * 获取用户权限
   */
  getUserPermissions(): UserPermissions | null {
    return this.tokenInfo?.permissions || null;
  }

  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return this.tokenInfo !== null && this.isTokenValid(this.tokenInfo);
  }

  /**
   * 获取剩余时间
   */
  getRemainingTimeSeconds(): number {
    return this.tokenInfo ? this.getRemainingTime(this.tokenInfo) : 0;
  }

  /**
   * 检查用户是否有特定权限
   */
  hasPermission(resource: string, action: string): boolean {
    if (!this.tokenInfo?.permissions) {
      return false;
    }
    
    const requiredPermission = `${resource}:${action}`;
    const permissions = this.tokenInfo.user.role.permissions || [];
    
    return permissions.includes(requiredPermission) || 
           permissions.includes(`${resource}:*`) || 
           permissions.includes('*:*');
  }

  /**
   * 检查用户是否可以访问特定API
   */
  canAccessAPI(endpoint: string, method: string): boolean {
    if (!this.tokenInfo?.permissions?.apis) {
      return false;
    }
    
    return this.tokenInfo.permissions.apis.some(api => 
      api.endpoint === endpoint && api.method.toLowerCase() === method.toLowerCase()
    );
  }

  /**
   * 添加认证状态监听器
   */
  addListener(listener: (isAuthenticated: boolean, userInfo?: UserInfo) => void): void {
    this.listeners.push(listener);
  }

  /**
   * 移除认证状态监听器
   */
  removeListener(listener: (isAuthenticated: boolean, userInfo?: UserInfo) => void): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  /**
   * 通知所有监听器
   */
  private notifyListeners(isAuthenticated: boolean, userInfo?: UserInfo): void {
    this.listeners.forEach(listener => {
      try {
        listener(isAuthenticated, userInfo);
      } catch (error) {
        console.error('[UserTokenManager] Error in token listener:', error);
      }
    });
  }

  /**
   * 销毁管理器
   */
  destroy(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    this.listeners = [];
  }
}

// 全局用户token管理器实例
export const userTokenManager = new UserTokenManager();

export default userTokenManager;
