/**
 * AILF - 智能前端生成框架 (路由模式)
 * 使用React Router进行页面管理
 * 遵循单一文件规则，组件化架构
 */

import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import './styles/breathing-effects.css';
import './styles/developer/developer-config.css';

const App: React.FC = () => {
  return <React.Suspense fallback={<div role="status" style={{ padding: 32 }}>正在加载 AILF…</div>}><RouterProvider router={router} /></React.Suspense>;
};

export default App;
