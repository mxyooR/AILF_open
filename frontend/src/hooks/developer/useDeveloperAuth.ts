/**
 * 开发者认证Hook
 * 使用统一的TokenManager进行token管理
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { authAPI } from '../../services/developer/authAPI';
import { tokenManager } from '../../services/common/tokenManager';
import type { AuthState, AuthFormData } from '../../types/developer/auth';
import { APIError } from '../../services/common/apiClient';

export const useDeveloperAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    token: null,
    expiresAt: null,
    isLoading: false,
    error: null,
  });
  const isMountedRef = useRef(true);
  const authRequestIdRef = useRef(0);

  // 初始化认证状态和监听token变化
  useEffect(() => {
    isMountedRef.current = true;
    // 从tokenManager获取当前认证状态
    const updateAuthState = () => {
      if (!isMountedRef.current) return;
      
      const isAuthenticated = tokenManager.isAuthenticated();
      const tokenInfo = tokenManager.getTokenInfo();

      setAuthState(prev => ({
        ...prev,
        isAuthenticated,
        token: tokenInfo?.token || null,
        expiresAt: tokenInfo?.expiresAt || null,
        isLoading: false,
        error: null,
      }));
    };

    // 初始化状态
    updateAuthState();

    // 监听token变化
    const handleTokenChange = () => {
      updateAuthState();
    };

    tokenManager.addListener(handleTokenChange);

    // 清理函数
    return () => {
      isMountedRef.current = false;
      authRequestIdRef.current++;
      tokenManager.removeListener(handleTokenChange);
    };
  }, []);

  // 开发者认证
  const authenticate = useCallback(async (formData: AuthFormData) => {
    if (!isMountedRef.current) return { success: false, error: '组件已卸载' };
    const requestId = ++authRequestIdRef.current;
    const snapshot = tokenManager.getTokenInfo();
    
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authAPI.authenticate({
        password: formData.password,
      });

      // 已取消、卸载或有较新的身份时，迟到的认证不能重新建立旧会话。
      if (!isMountedRef.current || requestId !== authRequestIdRef.current || tokenManager.getTokenInfo() !== snapshot) {
        return { success: false, error: '认证请求已失效' };
      }

      // 使用tokenManager管理token
      tokenManager.setToken(response.data, {
        rememberMe: formData.rememberMe ?? true,
      });

      if (isMountedRef.current && requestId === authRequestIdRef.current) {
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          error: null,
        }));
      }

      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error instanceof APIError
        ? error.message
        : '认证失败，请重试';

      if (isMountedRef.current && requestId === authRequestIdRef.current && tokenManager.getTokenInfo() === snapshot) {
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));
      }

      return { success: false, error: errorMessage };
    }
  }, []);

  // 退出登录
  const logout = useCallback(async () => {
    authRequestIdRef.current++;
    const token = tokenManager.getToken();
    // 立即清理本地状态；旧登出响应不再修改当前身份。
    tokenManager.clearToken();
    try {
      if (token) {
        await authAPI.logout(token);
      }
    } catch (error) {
      console.error('Developer logout API call failed:', error);
    }
  }, []);

  // 清除错误
  const clearError = useCallback(() => {
    if (isMountedRef.current) {
      setAuthState(prev => ({ ...prev, error: null }));
    }
  }, []);

  // 验证当前token
  const verifyToken = useCallback(async () => {
    return await tokenManager.verifyCurrentToken();
  }, []);

  return {
    authState,
    authenticate,
    logout,
    clearError,
    verifyToken,
  };
};
