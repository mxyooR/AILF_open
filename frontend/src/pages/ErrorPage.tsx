/**
 * AILF Error Page - 错误页面
 * 遵循单一文件规则，处理路由错误
 */

import React from 'react';
import { useNavigate, useRouteError } from 'react-router-dom';

const ErrorPage: React.FC = () => {
  const navigate = useNavigate();
  const error = useRouteError() as any;

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      textAlign: 'center'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.1)',
        borderRadius: '20px',
        padding: '40px',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        maxWidth: '500px'
      }}>
        <div style={{
          fontSize: '64px',
          marginBottom: '20px'
        }}>😵</div>
        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '20px',
          fontWeight: '300'
        }}>页面出错了</h1>
        <p style={{
          fontSize: '1.2rem',
          marginBottom: '20px',
          opacity: 0.9,
          lineHeight: '1.6'
        }}>
          抱歉，访问的页面出现了问题
        </p>
        {error && (
          <p style={{
            fontSize: '0.9rem',
            marginBottom: '30px',
            opacity: 0.7,
            fontFamily: 'monospace',
            background: 'rgba(0, 0, 0, 0.2)',
            padding: '10px',
            borderRadius: '8px'
          }}>
            {error.statusText || error.message || '未知错误'}
          </p>
        )}
        <button
          onClick={handleGoHome}
          style={{
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            border: 'none',
            borderRadius: '25px',
            color: 'white',
            padding: '15px 30px',
            fontSize: '16px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
          }}
        >
          🏠 返回首页
        </button>
      </div>
    </div>
  );
};

export default ErrorPage;
