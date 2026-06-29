/**
 * 工作流节点调色板组件 - Apple风格设计
 * 提供各种节点类型的拖拽创建功能
 */

import React, { useState } from 'react';
import { Card, Typography, Button, Space, Tooltip } from 'antd';
import {
  PlayCircleOutlined,
  ApiOutlined,
  NotificationOutlined,
  StopOutlined,
  DragOutlined,
} from '@ant-design/icons';
import type { NodeType } from '../../../types/developer/workflowTypes';
import './NodePalette.css';

const { Text } = Typography;

interface NodePaletteProps {
  onNodeDrop: (nodeType: string, position: { x: number; y: number }) => void;
  loading?: boolean;
  existingNodes?: Array<{ nodeType: string; id: string }>; // 现有节点信息
}

// 节点类型配置（已移除 user_input）
const nodeTypeConfigs = [
  {
    type: 'start',
    label: '开始节点',
    icon: <PlayCircleOutlined />,
    color: '#52c41a',
    description: '工作流的入口点',
  },
  {
    type: 'api_call',
    label: 'API调用',
    icon: <ApiOutlined />,
    color: '#1890ff',
    description: '调用系统中注册的API（POST请求会自动生成表单）',
  },
  {
    type: 'notification',
    label: '通知节点',
    icon: <NotificationOutlined />,
    color: '#eb2f96',
    description: '向用户显示信息或提示',
  },
  {
    type: 'end',
    label: '结束节点',
    icon: <StopOutlined />,
    color: '#f5222d',
    description: '工作流的结束点',
  },
];

const NodePalette: React.FC<NodePaletteProps> = ({ onNodeDrop, loading, existingNodes = [] }) => {
  const [draggedNode, setDraggedNode] = useState<string | null>(null);

  // 检查节点是否被禁用
  const isNodeDisabled = (nodeType: string) => {
    // 开始节点和结束节点只能有一个
    if (nodeType === 'start' || nodeType === 'end') {
      return existingNodes.some(node =>
        node.nodeType === nodeType ||
        (nodeType === 'start' && node.nodeType === 'start_node') ||
        (nodeType === 'end' && node.nodeType === 'end_node')
      );
    }
    return false;
  };

  // 处理拖拽开始
  const handleDragStart = (e: React.DragEvent, nodeType: string) => {
    if (isNodeDisabled(nodeType)) {
      e.preventDefault();
      return;
    }
    setDraggedNode(nodeType);
    e.dataTransfer.setData('application/workflow-node', nodeType);
    e.dataTransfer.effectAllowed = 'copy';
  };

  // 处理拖拽结束
  const handleDragEnd = () => {
    setDraggedNode(null);
  };

  // 处理点击添加节点（备用方案）
  const handleAddNode = (nodeType: string) => {
    if (isNodeDisabled(nodeType)) {
      return;
    }
    // 在画布中心位置添加节点
    const centerPosition = { x: 250, y: 200 };
    onNodeDrop(nodeType, centerPosition);
  };

  return (
    <div className="node-palette">
      <Card 
        title={
          <div className="palette-header">
            <DragOutlined className="palette-icon" />
            <span>节点工具箱</span>
          </div>
        }
        size="small"
        className="palette-card"
      >
        <div className="node-types-grid">
          {nodeTypeConfigs.map((config) => {
            const disabled = isNodeDisabled(config.type);
            const tooltipTitle = disabled
              ? `${config.description}（已存在，只能有一个）`
              : config.description;

            return (
              <Tooltip key={config.type} title={tooltipTitle} placement="right">
                <div
                  className={`node-palette-item ${draggedNode === config.type ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
                  draggable={!disabled}
                  onDragStart={(e) => handleDragStart(e, config.type)}
                  onDragEnd={handleDragEnd}
                  onClick={() => handleAddNode(config.type)}
                  style={{
                    borderColor: disabled ? '#d9d9d9' : config.color,
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'pointer'
                  }}
                >
                  <div className="node-icon" style={{ color: disabled ? '#d9d9d9' : config.color }}>
                    {config.icon}
                  </div>
                  <Text className="node-label" style={{ color: disabled ? '#d9d9d9' : undefined }}>
                    {config.label}
                  </Text>
                </div>
              </Tooltip>
            );
          })}
        </div>

        <div className="palette-tips">
          <Text type="secondary" className="tip-text">
            💡 拖拽节点到画布中创建，或点击直接添加
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default NodePalette; 
