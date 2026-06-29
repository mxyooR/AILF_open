/**
 * 运行监控独立页面
 */

import React, { useEffect } from 'react';
import { ClusterOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import InferenceWorkerStep from '../components/developer/steps/InferenceWorkerStep';
import AuthenticationRequired from '../components/developer/auth/AuthenticationRequired';
import { useDeveloperAuth } from '../hooks/developer/useDeveloperAuth';
import './RuntimeMonitorPage.css';

const RuntimeMonitorPage: React.FC = () => {
  const navigate = useNavigate();
  const { authState } = useDeveloperAuth();

  useEffect(() => {
    document.body.className = 'runtime-monitor-body';
    document.body.style.animation = 'none';
    document.body.style.background = '#f3f6fb';
    document.body.style.backgroundImage = 'none';

    return () => {
      document.body.className = '';
      document.body.style.animation = '';
      document.body.style.background = '';
      document.body.style.backgroundImage = '';
    };
  }, []);

  const tokenExpireText = authState.expiresAt ? new Date(authState.expiresAt).toLocaleString() : '-';

  return (
    <div className="runtime-monitor-page">
      <button
        className="runtime-monitor-back-button"
        onClick={() => navigate('/config')}
        aria-label="返回开发者配置"
        title="返回开发者配置"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
        </svg>
      </button>

      <div className="runtime-monitor-shell">
        <section className="runtime-monitor-hero">
          <div className="runtime-monitor-title-wrap">
            <span className="runtime-monitor-badge">
              <ClusterOutlined />
              运行监控
            </span>
            <h1>AILF Runtime Dashboard</h1>
            <p>集中查看推理机在线状态、Redis 连接质量与关键业务运行样本。</p>
          </div>

          <div className="runtime-monitor-token-panel">
            <span className={`runtime-auth-pill ${authState.isAuthenticated ? 'ok' : 'warn'}`}>
              {authState.isAuthenticated ? '开发者令牌已验证' : '需要开发者认证'}
            </span>
            <div className="runtime-token-expire">
              <span>令牌到期</span>
              <strong>{tokenExpireText}</strong>
            </div>
          </div>
        </section>

        <section className="runtime-monitor-main-panel">
          {authState.isAuthenticated ? (
            <InferenceWorkerStep />
          ) : (
            <div className="runtime-auth-required-wrap">
              <AuthenticationRequired onNavigateToAuth={() => navigate('/config')} />
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default RuntimeMonitorPage;
