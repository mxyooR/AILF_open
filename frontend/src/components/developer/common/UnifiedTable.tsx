/**
 * 统一表格组件 - Apple风格设计
 */

import React from 'react';
import { Table, TableProps } from 'antd';
import './UnifiedTable.css';

interface UnifiedTableProps<T = any> extends TableProps<T> {
  variant?: 'default' | 'compact' | 'bordered';
}

const UnifiedTable = <T extends Record<string, any>>({
  variant = 'default',
  className = '',
  pagination = {
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) => `共 ${total} 条记录`,
    pageSizeOptions: ['10', '20', '50', '100'],
    defaultPageSize: 10,
  },
  ...props
}: UnifiedTableProps<T>) => {
  const getTableClassName = () => {
    const baseClass = 'unified-table';
    const variantClass = `unified-table--${variant}`;
    return `${baseClass} ${variantClass} ${className}`.trim();
  };

  // 抑制ResizeObserver错误
  React.useEffect(() => {
    const handleResizeObserverError = (e: ErrorEvent) => {
      if (e.message === 'ResizeObserver loop completed with undelivered notifications.') {
        e.stopImmediatePropagation();
      }
    };

    window.addEventListener('error', handleResizeObserverError);

    return () => {
      window.removeEventListener('error', handleResizeObserverError);
    };
  }, []);

  return (
    <Table<T>
      {...props}
      className={getTableClassName()}
      pagination={pagination}
      scroll={{ x: 1200 }}
      size="middle"
    />
  );
};

export default UnifiedTable;
