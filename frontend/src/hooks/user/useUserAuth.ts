/**
 * 用户认证Hook
 * 提供用户登录、注册、登出等功能
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { userTokenManager, UserInfo, UserTokenInfo } from '../../services/common/userTokenManager';

export interface UserAuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
  isLoading: boolean;
  error: string | null;
}

export interface LoginFormData {
  username: string;
  password: string;
}

export interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  real_name?: string;
  phone?: string;
  role_id?: string;
}

export interface AuthResult {
  success: boolean;
  data?: any;
  error?: string;
}

export const useUserAuth = () => {
  const [authState, setAuthState] = useState<UserAuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: false,
    error: null,
  });

  const isMountedRef = useRef(true);

  // 初始化认证状态
  useEffect(() => {
    const initializeAuth = () => {
      const isAuthenticated = userTokenManager.isAuthenticated();
      const user = userTokenManager.getUserInfo();
      
      if (isMountedRef.current) {
        setAuthState({
          isAuthenticated,
          user,
          isLoading: false,
          error: null,
        });
      }
    };

    initializeAuth();

    // 监听认证状态变化
    const handleAuthChange = (isAuthenticated: boolean, userInfo?: UserInfo) => {
      if (isMountedRef.current) {
        setAuthState(prev => ({
          ...prev,
          isAuthenticated,
          user: userInfo || null,
          isLoading: false,
        }));
      }
    };

    userTokenManager.addListener(handleAuthChange);

    return () => {
      isMountedRef.current = false;
      userTokenManager.removeListener(handleAuthChange);
    };
  }, []);

  /**
   * 用户登录
   */
  const login = useCallback(async (formData: LoginFormData): Promise<AuthResult> => {
    if (!isMountedRef.current) return { success: false, error: 'Component unmounted' };

    setAuthState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await fetch('/api/v1/user/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok && data.code === 200) {
        // 登录成功，设置token
        const loginData: UserTokenInfo = {
          access_token: data.data.access_token,
          refresh_token: data.data.refresh_token,
          token_type: data.data.token_type,
          expires_in: data.data.expires_in,
          user: data.data.user,
          permissions: data.data.permissions,
        };

        userTokenManager.setToken(loginData);

        if (isMountedRef.current) {
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
            error: null,
          }));
        }

        return { success: true, data: loginData };
      } else {
        const errorMessage = data.message || '登录失败';
        
        if (isMountedRef.current) {
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
            error: errorMessage,
          }));
        }

        return { success: false, error: errorMessage };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '网络错误，请重试';

      if (isMountedRef.current) {
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));
      }

      return { success: false, error: errorMessage };
    }
  }, []);

  /**
   * 用户注册
   */
  const register = useCallback(async (formData: RegisterFormData): Promise<AuthResult> => {
    if (!isMountedRef.current) return { success: false, error: 'Component unmounted' };

    setAuthState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await fetch('/api/v1/user/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok && data.code === 200) {
        if (isMountedRef.current) {
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
            error: null,
          }));
        }

        return { success: true, data: data.data };
      } else {
        const errorMessage = data.message || '注册失败';
        
        if (isMountedRef.current) {
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
            error: errorMessage,
          }));
        }

        return { success: false, error: errorMessage };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '网络错误，请重试';

      if (isMountedRef.current) {
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));
      }

      return { success: false, error: errorMessage };
    }
  }, []);

  /**
   * 用户登出
   */
  const logout = useCallback(async (): Promise<void> => {
    if (!isMountedRef.current) return;

    setAuthState(prev => ({
      ...prev,
      isLoading: true,
    }));

    try {
      const token = userTokenManager.getToken();
      if (token) {
        // 调用登出API
        await fetch('/api/v1/user/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // 无论API调用是否成功，都清除本地token
      userTokenManager.clearToken();
      
      if (isMountedRef.current) {
        setAuthState({
          isAuthenticated: false,
          user: null,
          isLoading: false,
          error: null,
        });
      }
    }
  }, []);

  /**
   * 清除错误
   */
  const clearError = useCallback(() => {
    if (isMountedRef.current) {
      setAuthState(prev => ({
        ...prev,
        error: null,
      }));
    }
  }, []);

  /**
   * 检查权限
   */
  const hasPermission = useCallback((resource: string, action: string): boolean => {
    return userTokenManager.hasPermission(resource, action);
  }, []);

  /**
   * 检查API访问权限
   */
  const canAccessAPI = useCallback((endpoint: string, method: string): boolean => {
    return userTokenManager.canAccessAPI(endpoint, method);
  }, []);

  /**
   * 获取用户权限
   */
  const getUserPermissions = useCallback(() => {
    return userTokenManager.getUserPermissions();
  }, []);

  /**
   * 刷新用户信息
   */
  const refreshUserInfo = useCallback(async (): Promise<void> => {
    const token = userTokenManager.getToken();
    if (!token) return;

    try {
      const response = await fetch('/api/v1/user/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200 && isMountedRef.current) {
          setAuthState(prev => ({
            ...prev,
            user: data.data,
          }));
        }
      }
    } catch (error) {
      console.error('Failed to refresh user info:', error);
    }
  }, []);

  return {
    authState,
    login,
    register,
    logout,
    clearError,
    hasPermission,
    canAccessAPI,
    getUserPermissions,
    refreshUserInfo,
  };
};

export default useUserAuth;
