/**
 * 统计卡片组件 - Apple风格设计
 */

import React from 'react';
import { Card, Statistic, StatisticProps } from 'antd';
import './StatsCard.css';

interface StatsCardProps extends Omit<StatisticProps, 'title'> {
  title: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  color = 'primary',
  trend,
  suffix,
  prefix,
  precision,
  formatter,
  ...props
}) => {
  const getCardClassName = () => {
    return `stats-card stats-card--${color}`;
  };

  const getTrendElement = () => {
    if (!trend) return null;
    
    const trendClass = trend.isPositive ? 'stats-trend--positive' : 'stats-trend--negative';
    const trendIcon = trend.isPositive ? '↗' : '↘';
    
    return (
      <div className={`stats-trend ${trendClass}`}>
        <span className="stats-trend-icon">{trendIcon}</span>
        <span className="stats-trend-value">{Math.abs(trend.value)}%</span>
      </div>
    );
  };

  return (
    <Card className={getCardClassName()}>
      <div className="stats-content">
        <div className="stats-header">
          <div className="stats-title">{title}</div>
          {icon && <div className="stats-icon">{icon}</div>}
        </div>
        
        <div className="stats-value-container">
          <Statistic
            value={value}
            suffix={suffix}
            prefix={prefix}
            precision={precision}
            formatter={formatter}
            valueStyle={{
              color: 'var(--text-primary)',
              fontSize: '28px',
              fontWeight: '700',
              lineHeight: '1.2',
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif'
            }}
            {...props}
          />
          {getTrendElement()}
        </div>
      </div>
    </Card>
  );
};

export default StatsCard;
