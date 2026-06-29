/**
 * 认证守卫组件
 * 确保只有认证用户才能访问受保护的内容
 */

import React, { useEffect, useState } from 'react';
import { Spin, Alert } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { tokenManager } from '../../../services/common/tokenManager';
import AuthenticationRequired from './AuthenticationRequired';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showAuthPrompt?: boolean;
  onAuthRequired?: () => void;
}

const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  fallback,
  showAuthPrompt = true,
  onAuthRequired
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isVerifying, setIsVerifying] = useState(true);

  useEffect(() => {
    let mounted = true;

    const checkAuth = async () => {
      try {
        // 首先检查本地认证状态
        const localAuth = tokenManager.isAuthenticated();
        
        if (localAuth) {
          // 验证token有效性
          const isValid = await tokenManager.verifyCurrentToken();
          if (mounted) {
            setIsAuthenticated(isValid);
            setIsVerifying(false);
          }
        } else {
          if (mounted) {
            setIsAuthenticated(false);
            setIsVerifying(false);
          }
        }
      } catch (error) {
        console.error('Auth verification failed:', error);
        if (mounted) {
          setIsAuthenticated(false);
          setIsVerifying(false);
        }
      }
    };

    // 监听认证状态变化
    const handleAuthChange = (authenticated: boolean) => {
      if (mounted) {
        setIsAuthenticated(authenticated);
        setIsVerifying(false);
      }
    };

    tokenManager.addListener(handleAuthChange);
    checkAuth();

    return () => {
      mounted = false;
      tokenManager.removeListener(handleAuthChange);
    };
  }, []);

  // 触发认证要求回调
  useEffect(() => {
    if (isAuthenticated === false && onAuthRequired) {
      onAuthRequired();
    }
  }, [isAuthenticated, onAuthRequired]);

  // 验证中显示加载状态
  if (isVerifying) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '200px',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <Spin 
          indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />}
          size="large"
        />
        <div style={{ color: '#666', fontSize: '14px' }}>
          正在验证认证状态...
        </div>
      </div>
    );
  }

  // 未认证时的处理
  if (isAuthenticated === false) {
    // 如果提供了自定义fallback，使用它
    if (fallback) {
      return <>{fallback}</>;
    }

    // 如果不显示认证提示，返回null
    if (!showAuthPrompt) {
      return null;
    }

    // 显示认证要求提示
    return <AuthenticationRequired onNavigateToAuth={onAuthRequired} />;
  }

  // 认证成功，显示受保护的内容
  return <>{children}</>;
};

export default AuthGuard;
