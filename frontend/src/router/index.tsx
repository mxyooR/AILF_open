/**
 * AILF Router Configuration
 * 路由配置文件 - 遵循单一文件规则
 */

import React from 'react';
import { createBrowserRouter, createMemoryRouter, Navigate } from 'react-router-dom';
import ErrorPage from '../pages/ErrorPage';

const MainPage = React.lazy(() => import('../pages/MainPage'));
const AboutPage = React.lazy(() => import('../pages/AboutPage'));
const ConfigPage = React.lazy(() => import('../pages/ConfigPage'));
const RuntimeMonitorPage = React.lazy(() => import('../pages/RuntimeMonitorPage'));
const NotificationsPage = React.lazy(() => import('../pages/NotificationsPage'));
const DemoPage = React.lazy(() => import('../pages/DemoPage'));

// The standalone Pages build stays at its static entry URL. Native section anchors
// and refresh work without a server-side SPA rewrite or a backend route.
export const router = process.env.REACT_APP_DEMO_ONLY === 'true'
  ? createMemoryRouter([{ path: '*', element: <DemoPage />, errorElement: <ErrorPage /> }])
  : createBrowserRouter([
  { path: '/demo', element: <DemoPage />, errorElement: <ErrorPage /> },
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
