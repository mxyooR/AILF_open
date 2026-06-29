/* eslint-disable import/first */
import ReactDOM from 'react-dom';
import './index.css'; // Global styles
import App from './App'; // The new Siri-like interface component
// import reportWebVitals from './reportWebVitals';

// AMIS global styles - 使用antd浅色主题
import 'amis/lib/themes/antd.css';
import 'amis/lib/helper.css';
import 'amis/sdk/iconfont.css';

// 全局抑制ResizeObserver错误（这是浏览器的正常行为，不是真正的错误）
const resizeObserverLoopErr = 'ResizeObserver loop';

// 拦截错误事件
window.addEventListener(
  'error',
  (e) => {
    if (e.message?.includes(resizeObserverLoopErr)) {
      e.stopImmediatePropagation();
      e.stopPropagation();
      e.preventDefault();
    }
  },
  true
);

// 覆盖全局错误处理
const originalOnError = window.onerror;
window.onerror = (message, source, lineno, colno, error) => {
  if (typeof message === 'string' && message.includes(resizeObserverLoopErr)) {
    return true; // 阻止错误传播
  }
  if (originalOnError) {
    return originalOnError(message, source, lineno, colno, error);
  }
  return false;
};

// 覆盖console.error以过滤ResizeObserver警告
const originalConsoleError = console.error;
console.error = (...args: any[]) => {
  const message = args[0]?.toString?.() || '';
  if (message.includes(resizeObserverLoopErr)) {
    return;
  }
  originalConsoleError.apply(console, args);
};

// 抑制未捕获的Promise错误中的ResizeObserver错误
window.addEventListener(
  'unhandledrejection',
  (e) => {
    if (e.reason?.message?.includes(resizeObserverLoopErr)) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
  },
  true
);

ReactDOM.render(
  <>
    <App />
  </>,
  document.getElementById('root')
);
