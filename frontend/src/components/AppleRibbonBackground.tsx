/**
 * Apple-style Animated Ribbon Background
 * 苹果风格飘动丝带背景组件
 */

import React from 'react';
import './AppleRibbonBackground.css';

const AppleRibbonBackground: React.FC = () => {
  return (
    <div className="apple-ribbon-bg">
      {/* 基础黑色背景 */}
      <div className="ribbon-base" />
      
      {/* 多层丝带 */}
      <div className="ribbon-container">
        {/* 主要蓝紫色丝带 */}
        <div className="ribbon ribbon-1" />
        <div className="ribbon ribbon-2" />
        <div className="ribbon ribbon-3" />
        <div className="ribbon ribbon-4" />
        <div className="ribbon ribbon-5" />
        
        {/* 辉光层 */}
        <div className="ribbon-glow ribbon-glow-1" />
        <div className="ribbon-glow ribbon-glow-2" />
      </div>
      
      {/* 噪点纹理 */}
      <div className="ribbon-noise" />
    </div>
  );
};

export default AppleRibbonBackground;
