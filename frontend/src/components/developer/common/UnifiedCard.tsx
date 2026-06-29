/**
 * 统一卡片组件 - Apple风格设计
 */

import React from 'react';
import { Card, CardProps } from 'antd';
import './UnifiedCard.css';

interface UnifiedCardProps extends Omit<CardProps, 'variant'> {
  variant?: 'default' | 'header' | 'stats' | 'content';
  children?: React.ReactNode;
}

const UnifiedCard: React.FC<UnifiedCardProps> = ({
  variant = 'default',
  className = '',
  children,
  ...props
}) => {
  const getCardClassName = () => {
    const baseClass = 'unified-card';
    const variantClass = `unified-card--${variant}`;
    return `${baseClass} ${variantClass} ${className}`.trim();
  };

  return (
    <Card
      {...props}
      className={getCardClassName()}
    >
      {children}
    </Card>
  );
};

export default UnifiedCard;
