/**
 * 开发者认证相关类型定义
 */

// 开发者认证请求
export interface DeveloperAuthRequest {
  password: string;
}

// 开发者认证响应
export interface DeveloperAuthResponse {
  code: number;
  message: string;
  data: {
    token: string;
    refresh_token: string;
    expires_in: number;
    token_type: string;
    issued_at: string;
    expires_at: string;
  };
}

// Token刷新请求
export interface TokenRefreshRequest {
  refresh_token: string;
}

// 认证错误响应
export interface AuthErrorResponse {
  code: number;
  message: string;
  data: {
    error: string;
    details: string | Record<string, string[]>;
  };
}

// 认证状态
export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: string | null;
  isLoading: boolean;
  error: string | null;
}

// 认证表单数据
export interface AuthFormData {
  password: string;
  rememberMe: boolean;
}

// Token验证请求
export interface TokenVerifyRequest {
  token: string;
}

// Token验证响应
export interface TokenVerifyResponse {
  code: number;
  message: string;
  data: {
    valid: boolean;
    expires_at: string;
    remaining_time: number;
  };
}
