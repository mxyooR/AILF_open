/**
 * AILF Config Page - 开发者配置页面
 */

import React, { useEffect } from 'react';
import DeveloperConfigMain from '../components/developer/DeveloperConfigMain';

const ConfigPage: React.FC = () => {
  useEffect(() => {
    // 强制设置body类名以禁用呼吸效果
    document.body.className = 'config-page-body';
    document.body.style.animation = 'none';
    document.body.style.background = '#f5f5f7';
    document.body.style.backgroundImage = 'none';

    return () => {
      // 清理body类名和样式
      document.body.className = '';
      document.body.style.animation = '';
      document.body.style.background = '';
      document.body.style.backgroundImage = '';
    };
  }, []);

  return (
    <div className="config-page">
      <DeveloperConfigMain />
    </div>
  );
};

export default ConfigPage;
