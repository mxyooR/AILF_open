/**
 * AILF Router Configuration
 * 路由配置文件 - 遵循单一文件规则
 */

import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainPage from '../pages/MainPage';
import AboutPage from '../pages/AboutPage';
import ConfigPage from '../pages/ConfigPage';
import RuntimeMonitorPage from '../pages/RuntimeMonitorPage';
import NotificationsPage from '../pages/NotificationsPage';
import ErrorPage from '../pages/ErrorPage';

// 创建路由配置
export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainPage />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/about',
    element: <AboutPage />,
  },
  {
    path: '/config',
    element: <ConfigPage />,
  },
  {
    path: '/config/runtime-monitor',
    element: <RuntimeMonitorPage />,
  },
  {
    path: '/notifications',
    element: <NotificationsPage />,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export default router;
