/**
 * 用户状态指示器组件
 * 显示用户登录状态、用户信息和提供登出功能
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserAuth } from '../../hooks/user/useUserAuth';
import './UserStatusIndicator.css';

interface UserStatusIndicatorProps {
  className?: string;
  style?: React.CSSProperties;
  showDetails?: boolean;
  onLoginClick?: () => void;
}

const UserStatusIndicator: React.FC<UserStatusIndicatorProps> = ({
  className = '',
  style = {},
  showDetails = true,
  onLoginClick
}) => {
  const { authState, logout, refreshUserInfo } = useUserAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    if (authState.isAuthenticated) {
      refreshUserInfo();
    }
  }, [authState.isAuthenticated, refreshUserInfo]);

  const handleLogout = async () => {
    try {
      await logout();
      setShowDropdown(false);
    } catch (error) {
      console.error('登出失败:', error);
    }
  };

  const toggleDropdown = () => {
    setShowDropdown(!showDropdown);
  };

  const handleOpenNotifications = () => {
    setShowDropdown(false);
    navigate('/notifications');
  };

  const formatDateTime = useMemo(
    () => (value?: string | null) => {
      if (!value) return '未记录';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString('zh-CN', { hour12: false });
    },
    []
  );

  if (!authState.isAuthenticated) {
    const handleLoginClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation();
      onLoginClick?.();
    };

    return (
      <div className={`user-status-indicator not-authenticated ${className}`} style={style}>
        <div className="status-icon">
          <div className="user-avatar guest">
            <span>?</span>
          </div>
        </div>
        {showDetails && (
          <div className="status-text">
            <span className="status-label">未登录</span>
          </div>
        )}
        <button
          type="button"
          className="login-action-button"
          onClick={handleLoginClick}
        >
          登录
        </button>
      </div>
    );
  }

  const user = authState.user;
  if (!user) {
    return null;
  }

  return (
    <div className={`user-status-indicator authenticated ${className}`} style={style}>
      <div className="status-content" onClick={toggleDropdown}>
        <div className="status-icon">
          <div className="user-avatar">
            <span>{user.real_name?.[0] || user.username[0]}</span>
          </div>
          <div className="status-dot online"></div>
        </div>
        {showDetails && (
          <div className="status-text">
            <div className="user-name">{user.real_name || user.username}</div>
            <div className="user-role">{user.role.name}</div>
          </div>
        )}
        <div className="dropdown-arrow">
          <span>▼</span>
        </div>
      </div>

      {showDropdown && (
        <div className="user-dropdown">
          <div className="dropdown-header">
            <div className="user-info">
              <div className="user-avatar large">
                <span>{user.real_name?.[0] || user.username[0]}</span>
              </div>
              <div className="user-details">
                <div className="user-name">{user.real_name || user.username}</div>
                <div className="user-email">{user.email || '未配置邮箱'}</div>
                <div className="user-role-badge">{user.role.name}</div>
              </div>
            </div>
          </div>
          
          <div className="dropdown-divider"></div>

          <div className="profile-meta">
            <div className="profile-row">
              <span className="profile-label">用户ID</span>
              <span className="profile-value">{user.id}</span>
            </div>
            <div className="profile-row">
              <span className="profile-label">用户名</span>
              <span className="profile-value">{user.username}</span>
            </div>
            <div className="profile-row">
              <span className="profile-label">手机号</span>
              <span className="profile-value">{user.phone || '未绑定'}</span>
            </div>
            <div className="profile-row">
              <span className="profile-label">角色编码</span>
              <span className="profile-value">{user.role.code || '未配置'}</span>
            </div>
            <div className="profile-row">
              <span className="profile-label">创建时间</span>
              <span className="profile-value">{formatDateTime(user.created_at)}</span>
            </div>
            <div className="profile-row">
              <span className="profile-label">最近登录</span>
              <span className="profile-value">{formatDateTime(user.last_login)}</span>
            </div>
          </div>

          <div className="dropdown-divider"></div>
          
          <div className="dropdown-menu">
            <div className="menu-item notifications" onClick={handleOpenNotifications}>
              <span className="menu-icon">🔔</span>
              <span className="menu-text">通知中心</span>
            </div>
            <div className="menu-item logout" onClick={handleLogout}>
              <span className="menu-icon">🚪</span>
              <span className="menu-text">退出登录</span>
            </div>
          </div>
        </div>
      )}

      {/* 点击外部关闭下拉菜单 */}
      {showDropdown && (
        <div 
          className="dropdown-overlay" 
          onClick={() => setShowDropdown(false)}
        ></div>
      )}
    </div>
  );
};

export default UserStatusIndicator;
