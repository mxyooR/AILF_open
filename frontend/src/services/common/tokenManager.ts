/**
 * 统一Token管理服务
 * 开发者认证token管理（支持“记住登录状态”）
 */

import { authAPI } from '../developer/authAPI';
import type { DeveloperAuthResponse } from '../../types/developer/auth';

export interface TokenInfo {
  token: string;
  refreshToken: string;
  expiresAt: string;
  issuedAt: string;
  expiresIn: number;
  tokenType: string;
}

type StorageMode = 'local' | 'session';

export interface TokenManagerConfig {
  storageKey?: string;
  autoRefresh?: boolean;
  refreshThreshold?: number; // 提前多少秒刷新token
}

interface SetTokenOptions {
  rememberMe?: boolean;
}

export class TokenManager {
  private tokenInfo: TokenInfo | null = null;
  private refreshPromise: Promise<string | null> | null = null;
  private config: Required<TokenManagerConfig>;
  private refreshTimer: NodeJS.Timeout | null = null;
  private listeners: Array<(isAuthenticated: boolean) => void> = [];
  private storageMode: StorageMode = 'local';
  private localStorageKey: string;
  private sessionStorageKey: string;

  constructor(config: TokenManagerConfig = {}) {
    this.config = {
      storageKey: config.storageKey || 'ailf_developer_token',
      autoRefresh: config.autoRefresh ?? true,
      refreshThreshold: config.refreshThreshold || 300, // 5分钟
    };
    this.localStorageKey = this.config.storageKey;
    this.sessionStorageKey = `${this.config.storageKey}_session`;

    // 初始化时从存储中恢复token
    try {
      this.loadFromStorage();
    } catch (error) {
      console.error('Failed to initialize token manager from storage:', error);
      this.clearStorage();
      authAPI.setAuthToken(null);
    }
  }

  private getStorage(mode: StorageMode): Storage {
    return mode === 'local' ? localStorage : sessionStorage;
  }

  private parseStoredToken(raw: string | null, mode: StorageMode): { tokenInfo: TokenInfo; mode: StorageMode } | null {
    if (!raw) {
      return null;
    }
    try {
      const tokenInfo = JSON.parse(raw) as TokenInfo;
      if (!tokenInfo?.token || !tokenInfo?.refreshToken || !tokenInfo?.expiresAt) {
        return null;
      }
      return { tokenInfo, mode };
    } catch {
      return null;
    }
  }

  private pickLatestValidToken(): { tokenInfo: TokenInfo; mode: StorageMode } | null {
    const localToken = this.parseStoredToken(localStorage.getItem(this.localStorageKey), 'local');
    const sessionToken = this.parseStoredToken(sessionStorage.getItem(this.sessionStorageKey), 'session');
    const candidates = [localToken, sessionToken].filter((item): item is { tokenInfo: TokenInfo; mode: StorageMode } => Boolean(item));

    if (candidates.length === 0) {
      return null;
    }

    candidates.sort((a, b) => {
      const at = new Date(a.tokenInfo.issuedAt || 0).getTime();
      const bt = new Date(b.tokenInfo.issuedAt || 0).getTime();
      return bt - at;
    });

    return candidates[0];
  }

  /**
   * 从本地存储加载token
   */
  private loadFromStorage(): void {
    const selected = this.pickLatestValidToken();
    if (!selected) {
      authAPI.setAuthToken(null);
      return;
    }

    const { tokenInfo, mode } = selected;
    this.storageMode = mode;

    if (this.isTokenValid(tokenInfo)) {
      this.tokenInfo = tokenInfo;
      this.scheduleRefresh();
      authAPI.setAuthToken(tokenInfo.token);
      console.log(`Token restored from ${mode}Storage`);
      return;
    }

    // 启动时发现 access token 过期，尝试用 refresh token 续期
    if (tokenInfo.refreshToken) {
      this.tokenInfo = tokenInfo;
      authAPI.setAuthToken(null);
      console.log(`Expired token restored from ${mode}Storage, attempting refresh...`);
      void this.refreshToken();
      return;
    }

    this.clearStorage();
    authAPI.setAuthToken(null);
  }

  /**
   * 保存token到存储（localStorage 或 sessionStorage）
   */
  private saveToStorage(): void {
    if (!this.tokenInfo) {
      return;
    }

    try {
      const selectedStorage = this.getStorage(this.storageMode);
      const otherStorage = this.getStorage(this.storageMode === 'local' ? 'session' : 'local');
      const selectedKey = this.storageMode === 'local' ? this.localStorageKey : this.sessionStorageKey;
      const otherKey = this.storageMode === 'local' ? this.sessionStorageKey : this.localStorageKey;

      selectedStorage.setItem(selectedKey, JSON.stringify(this.tokenInfo));
      otherStorage.removeItem(otherKey);
    } catch (error) {
      console.error('Failed to save token to storage:', error);
    }
  }

  /**
   * 清除存储
   */
  private clearStorage(): void {
    localStorage.removeItem(this.localStorageKey);
    sessionStorage.removeItem(this.sessionStorageKey);
  }

  /**
   * 检查token是否有效（未过期）
   */
  private isTokenValid(tokenInfo: TokenInfo): boolean {
    const now = new Date();
    const expiresAt = new Date(tokenInfo.expiresAt);
    return expiresAt > now;
  }

  /**
   * 计算token剩余时间（秒）
   */
  private getRemainingTime(tokenInfo: TokenInfo): number {
    const now = new Date();
    const expiresAt = new Date(tokenInfo.expiresAt);
    return Math.max(0, Math.floor((expiresAt.getTime() - now.getTime()) / 1000));
  }

  /**
   * 安排token刷新
   */
  private scheduleRefresh(): void {
    if (!this.config.autoRefresh || !this.tokenInfo) {
      return;
    }

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    const remainingTime = this.getRemainingTime(this.tokenInfo);
    const refreshTime = Math.max(1, remainingTime > this.config.refreshThreshold
      ? remainingTime - this.config.refreshThreshold : Math.floor(remainingTime / 2));

    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(() => {
        void this.refreshToken();
      }, refreshTime * 1000);
      console.log(`Token refresh scheduled in ${refreshTime} seconds`);
      return;
    }

    void this.refreshToken();
  }

  /** 定时刷新和 401 重试共用一个请求；旧会话响应不能复活已退出的开发者身份。 */
  refreshToken(): Promise<string | null> {
    if (this.refreshPromise) return this.refreshPromise;
    const snapshot = this.tokenInfo;
    if (!snapshot?.refreshToken) { this.clearToken(); return Promise.resolve(null); }
    const attempt = (async () => {
      try {
        const response = await authAPI.refreshToken({ refresh_token: snapshot.refreshToken });
        if (this.tokenInfo !== snapshot) return null;
        if (response.code !== 200) { this.clearToken(); return null; }
        this.setToken(response.data);
        return response.data.token;
      } catch (error: any) {
        if (this.tokenInfo !== snapshot) return null;
        if ([400, 401, 403].includes(error.status) || !this.isTokenValid(snapshot)) this.clearToken();
        else if (this.config.autoRefresh) {
          const remaining = this.getRemainingTime(snapshot);
          this.refreshTimer = setTimeout(() => { void this.refreshToken(); }, Math.max(1, Math.min(30, remaining)) * 1000);
        }
        return null;
      }
    })();
    this.refreshPromise = attempt;
    void attempt.finally(() => { if (this.refreshPromise === attempt) this.refreshPromise = null; });
    return attempt;
  }

  /**
   * 设置token
   */
  setToken(authData: DeveloperAuthResponse['data'], options: SetTokenOptions = {}): void {
    this.refreshPromise = null;
    const rememberMe = options.rememberMe;
    if (rememberMe !== undefined) {
      this.storageMode = rememberMe ? 'local' : 'session';
    } else if (!this.tokenInfo) {
      this.storageMode = 'local';
    }

    this.tokenInfo = {
      token: authData.token,
      refreshToken: authData.refresh_token,
      expiresAt: authData.expires_at,
      issuedAt: authData.issued_at,
      expiresIn: authData.expires_in,
      tokenType: authData.token_type,
    };

    this.saveToStorage();
    this.scheduleRefresh();
    authAPI.setAuthToken(authData.token);
    this.notifyListeners(true);
  }

  /**
   * 清除token
   */
  clearToken(): void {
    this.tokenInfo = null;
    this.refreshPromise = null;
    this.clearStorage();

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }

    authAPI.setAuthToken(null);
    this.notifyListeners(false);
  }

  /**
   * 获取当前token
   */
  getToken(): string | null {
    return this.tokenInfo?.token || null;
  }

  /**
   * 获取token信息
   */
  getTokenInfo(): TokenInfo | null {
    return this.tokenInfo;
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
   * 验证当前token
   */
  async verifyCurrentToken(): Promise<boolean> {
    const snapshot = this.tokenInfo;
    if (!snapshot) {
      return false;
    }

    try {
      const response = await authAPI.verifyToken({
        token: snapshot.token,
      });

      // 校验期间已退出、刷新或重新登录时，旧结果不能修改新会话。
      if (this.tokenInfo !== snapshot) return false;

      if (response.code === 200 && response.data.valid) {
        return true;
      }

      this.clearToken();
      return false;
    } catch (error: any) {
      console.error('Token verification failed:', error);
      if (this.tokenInfo === snapshot && ([400, 401, 403].includes(error.status) || !this.isTokenValid(snapshot))) {
        this.clearToken();
      }
      return false;
    }
  }

  /**
   * 添加认证状态监听器
   */
  addListener(listener: (isAuthenticated: boolean) => void): void {
    this.listeners.push(listener);
  }

  /**
   * 移除认证状态监听器
   */
  removeListener(listener: (isAuthenticated: boolean) => void): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  /**
   * 通知所有监听器
   */
  private notifyListeners(isAuthenticated: boolean): void {
    this.listeners.forEach(listener => {
      try {
        listener(isAuthenticated);
      } catch (error) {
        console.error('Error in token listener:', error);
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

// 全局token管理器实例
export const tokenManager = new TokenManager();

export default tokenManager;
