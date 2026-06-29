/**
 * 基于Butterfly-DAG的工作流可视化编辑画布
 * 支持拖拽创建节点、连接节点、编辑节点属性
 */

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { message, Modal, Drawer, Form, Input, Select, AutoComplete, Button } from 'antd';
import { Canvas } from 'butterfly-dag';
import type { WorkflowNode, WorkflowDefinition, ButterflyData } from '../../../types/developer/workflowTypes';
import { workflowAPI } from '../../../services/developer/workflowAPI';
import { apiClient } from '../../../services/common/apiClient';
import { useDeveloperAuth } from '../../../hooks/developer/useDeveloperAuth';
import NodeEditor from './NodeEditor';
import NodePalette from './NodePalette';
import WorkflowButterflyNode from './WorkflowButterflyNode';
import WorkflowButterflyEdge from './WorkflowButterflyEdge';
import './WorkflowCanvas.css';
import 'butterfly-dag/dist/index.css';

// Butterfly相关类型 (临时定义，等安装完成后使用真实的)
interface ButterflyCanvas {
  draw: (data: any) => void;
  addNode: (nodeData: any) => void;
  addEdge: (edgeData: any) => void;
  removeNode: (nodeId: string) => void;
  removeEdge: (edgeId: string) => void;
  getDataMap: () => any;
  on: (event: string, callback: Function) => void;
  off: (event: string, callback: Function) => void;
  redraw: () => void;
  destroy: () => void;
  clear?: () => void;  // 清除画布内容
}

interface WorkflowCanvasProps {
  workflowId?: string;
  workflow?: WorkflowDefinition;
  readonly?: boolean;
  onSave?: (workflow: WorkflowDefinition) => void;
  onNodeSelect?: (node: WorkflowNode | null) => void;
}

interface SelectedEdgeMeta {
  edgeId?: string;
  sourceNodeId: string;
  targetNodeId: string;
}

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({
  workflowId,
  workflow,
  readonly = false,
  onSave,
  onNodeSelect,
}) => {
  const { authState } = useDeveloperAuth();
  const canvasRef = useRef<HTMLDivElement>(null);
  const butterflyRef = useRef<ButterflyCanvas | null>(null);
  const lastWorkflowIdRef = useRef<string | undefined>(undefined); // 追踪当前加载的工作流ID
  const [workflowData, setWorkflowData] = useState<WorkflowDefinition | null>(workflow || null);
  const [nodes, setNodes] = useState<WorkflowNode[]>(workflow?.nodes || []);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [showNodeEditor, setShowNodeEditor] = useState(false);
  const [loading, setLoading] = useState(false);
  const [canvasInitialized, setCanvasInitialized] = useState(false);
  const [editorVisible, setEditorVisible] = useState(false);
  const [edgeEditorVisible, setEdgeEditorVisible] = useState(false);
  const [selectedEdge, setSelectedEdge] = useState<SelectedEdgeMeta | null>(null);
  const [edgeForm] = Form.useForm();
  // 使用ref来保存最新的节点状态，解决React状态更新异步性问题
  const latestNodesRef = useRef<WorkflowNode[]>(workflow?.nodes || []);

  const extractTemplateFields = useCallback((value: unknown): string[] => {
    if (typeof value === 'string') {
      const matches = value.match(/\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g) || [];
      return matches.map(m => m.slice(2, -1));
    }
    if (Array.isArray(value)) {
      return value.flatMap(item => extractTemplateFields(item));
    }
    if (value && typeof value === 'object') {
      return Object.values(value as Record<string, unknown>).flatMap(item => extractTemplateFields(item));
    }
    return [];
  }, []);

  const edgeFieldCandidates = useMemo(() => {
    const fields = new Set<string>();
    const nodesSnapshot = latestNodesRef.current.length > 0 ? latestNodesRef.current : nodes;

    const commonFields = [
      'verified',
      'failure_reason',
      'payment_success',
      'ticket_number',
      'ticket_id',
      'order_id',
      'passenger_id',
      'name',
      'phone',
      'id_card'
    ];
    commonFields.forEach(f => fields.add(f));

    (workflowData?.inputs || []).forEach(input => {
      if (input?.name) fields.add(input.name);
    });

    nodesSnapshot.forEach(node => {
      if (node.id) fields.add(`${node.id}_result`);

      (node.outputs || []).forEach(output => {
        if (output?.name) fields.add(output.name);
      });

      const config = (node.config || {}) as Record<string, unknown>;
      extractTemplateFields(config).forEach(f => fields.add(f));

      (node.child_nodes || []).forEach(child => {
        const exp = child?.condition?.expression || '';
        const tokens = exp.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || [];
        tokens.forEach(token => {
          if (!['true', 'false', 'null', 'and', 'or'].includes(token.toLowerCase())) {
            fields.add(token);
          }
        });
      });
    });

    return Array.from(fields).sort();
  }, [extractTemplateFields, nodes, workflowData?.inputs]);

  const expressionAutoCompleteOptions = useMemo(() => {
    return edgeFieldCandidates.slice(0, 120).flatMap(field => ([
      { value: `${field} == true` },
      { value: `${field} == false` },
      { value: `${field} != null` }
    ]));
  }, [edgeFieldCandidates]);

  // 同步nodes状态到ref
  useEffect(() => {
    latestNodesRef.current = nodes;
  }, [nodes]);

  // 获取节点端点配置
  const getNodeEndpoints = useCallback((nodeType: string) => {
    // 根据节点类型返回不同的端点配置
    switch (nodeType) {
      case 'start':
        // 开始节点：只有右侧输出
        return [{ id: 'right', orientation: [1, 0], pos: [0, 0.5] }];

      case 'end':
        // 结束节点：只有左侧输入
        return [{ id: 'left', orientation: [-1, 0], pos: [0, 0.5] }];

      case 'condition':
        // 条件节点：左侧输入，右侧"是"输出，底部"否"输出
        return [
          { id: 'left', orientation: [-1, 0], pos: [0, 0.5] },      // 输入
          { id: 'right', orientation: [1, 0], pos: [0, 0.5] },     // "是"输出
          { id: 'bottom', orientation: [0, 1], pos: [0.5, 0] }     // "否"输出
        ];

      default:
        // 其他节点：标准的四个方向端点
        return [
          { id: 'left', orientation: [-1, 0], pos: [0, 0.5] },
          { id: 'right', orientation: [1, 0], pos: [0, 0.5] },
          { id: 'top', orientation: [0, -1], pos: [0.5, 0] },
          { id: 'bottom', orientation: [0, 1], pos: [0.5, 0] }
        ];
    }
  }, []);

  // 从后端加载工作流数据
  const loadWorkflowData = useCallback(async () => {
    if (!workflowId) return;

    setLoading(true);
    try {
      // 检查是否有有效的认证token
      const apiToken = apiClient.getToken();
      const hasValidToken = (authState.token && !authState.token.includes('fake-token')) || 
                           (apiToken && !apiToken.includes('fake-token'));
      const isAuthenticated = authState.isAuthenticated || hasValidToken; // 只要有有效token就认为已认证
      
      console.log('loadWorkflowData - authState:', authState);
      console.log('loadWorkflowData - isAuthenticated:', isAuthenticated);
      console.log('loadWorkflowData - token exists:', !!authState.token);
      console.log('loadWorkflowData - apiClient has token:', !!apiToken);
      console.log('loadWorkflowData - has valid token:', hasValidToken);
      
      if (isAuthenticated && hasValidToken) {
        console.log('loadWorkflowDetail - apiClient has token:', !!apiClient.getToken());
        console.log('loadWorkflowDetail - 调用API获取工作流详情:', workflowId);
        const response = await workflowAPI.getWorkflowDetail(workflowId);
        if (response.code === 200 && response.data) {
          const workflowDetail = response.data.workflow;
          setWorkflowData(workflowDetail);
          setNodes(workflowDetail.nodes || []);
          console.log('✅ 工作流数据加载成功:', workflowDetail);
        } else {
          message.error(response.message || '加载工作流数据失败');
        }
      } else {
        // 未认证时不调用API，使用传入的数据或示例数据
        console.log('未认证，跳过API调用');
      }
    } catch (error) {
      console.error('Failed to load workflow data:', error);
      message.error('加载工作流数据失败');
    } finally {
      setLoading(false);
    }
  }, [workflowId, authState.isAuthenticated, authState.token]);

  // 将工作流节点转换为Butterfly数据格式
  const convertWorkflowToButterflyData = useCallback((workflowNodes: WorkflowNode[]) => {
    console.log('🔍 开始转换工作流数据到Butterfly格式，节点数:', workflowNodes.length);
    console.log('🔍 原始节点数据:', workflowNodes.map(n => ({
      id: n.id,
      name: n.name,
      parent_nodes: n.parent_nodes,
      child_nodes: n.child_nodes
    })));

    const butterflyNodes = workflowNodes.map(node => ({
      id: node.id,
      label: node.name,
      left: Math.round(node.position?.x || 100),
      top: Math.round(node.position?.y || 100),
      Class: WorkflowButterflyNode,
      nodeType: node.type,
      endpoints: getNodeEndpoints(node.type),
      options: {
        nodeType: node.type,
        label: node.name,
        name: node.name,
        // 🔧 修复：保存完整的节点数据到options中，确保刷新后不丢失
        nodeData: node
      }
    }));

    // 根据节点的parent_nodes和child_nodes关系生成连线
    const butterflyEdges: any[] = [];
    let edgeIndex = 0;

    workflowNodes.forEach(node => {
      console.log(`🔍 处理节点 ${node.id} 的连线，child_nodes:`, node.child_nodes);
      if (node.child_nodes && node.child_nodes.length > 0) {
        node.child_nodes.forEach((childRelation, index) => {
          const targetNode = workflowNodes.find(n => n.id === childRelation.node_id);
          console.log(`🔍 查找目标节点 ${childRelation.node_id}:`, targetNode ? '找到' : '未找到');
          if (targetNode) {
            // 根据节点类型确定连接端点
            let sourceEndpoint = 'right';
            let targetEndpoint = 'left';

            // 条件节点的特殊处理
            if (node.type === 'condition') {
              if (index === 0) {
                sourceEndpoint = 'right'; // "是"分支
              } else {
                sourceEndpoint = 'bottom'; // "否"分支
              }
            }

            const edge = {
              id: `edge-${edgeIndex++}`,
              source: sourceEndpoint,
              target: targetEndpoint,
              sourceNode: node.id,
              targetNode: childRelation.node_id,
              type: 'endpoint',
              arrow: true,
              Class: WorkflowButterflyEdge,
              label: childRelation.condition?.description || ''
            };
            
            console.log(`🔍 创建连线:`, edge);
            butterflyEdges.push(edge);
          }
        });
      }
    });

    console.log('🔍 生成的连线数组:', butterflyEdges);

    return {
      nodes: butterflyNodes,
      edges: butterflyEdges
    };
  }, [getNodeEndpoints]);

  // 创建示例数据（当没有workflowId时使用）
  const createSampleData = useCallback(() => {
    return {
      nodes: [
        {
          id: 'start-1',
          label: '开始',
          left: 100,
          top: 150,
          Class: WorkflowButterflyNode,
          nodeType: 'start',
          endpoints: getNodeEndpoints('start'),
          options: { nodeType: 'start', label: '开始', name: '开始' }
        },
        {
          id: 'condition-1',
          label: '条件判断',
          left: 300,
          top: 150,
          Class: WorkflowButterflyNode,
          nodeType: 'condition',
          endpoints: getNodeEndpoints('condition'),
          options: { nodeType: 'condition', label: '条件判断', name: '条件判断' }
        },
        {
          id: 'api-success',
          label: 'API调用',
          left: 500,
          top: 100,
          Class: WorkflowButterflyNode,
          nodeType: 'api_call',
          endpoints: getNodeEndpoints('api_call'),
          options: { nodeType: 'api_call', label: 'API调用', name: 'API调用' }
        },
        {
          id: 'notification-fail',
          label: '失败通知',
          left: 500,
          top: 250,
          Class: WorkflowButterflyNode,
          nodeType: 'notification',
          endpoints: getNodeEndpoints('notification'),
          options: { nodeType: 'notification', label: '失败通知', name: '失败通知' }
        },
        {
          id: 'end-1',
          label: '结束',
          left: 700,
          top: 150,
          Class: WorkflowButterflyNode,
          nodeType: 'end',
          endpoints: getNodeEndpoints('end'),
          options: { nodeType: 'end', label: '结束', name: '结束' }
        }
      ],
      edges: [
        {
          id: 'edge-1',
          source: 'right',
          target: 'left',
          sourceNode: 'start-1',
          targetNode: 'condition-1',
          type: 'endpoint',
          arrow: true,
          Class: WorkflowButterflyEdge
        },
        {
          id: 'edge-2',
          source: 'right',
          target: 'left',
          sourceNode: 'condition-1',
          targetNode: 'api-success',
          type: 'endpoint',
          arrow: true,
          Class: WorkflowButterflyEdge,
          label: '满足条件'
        },
        {
          id: 'edge-3',
          source: 'bottom',
          target: 'left',
          sourceNode: 'condition-1',
          targetNode: 'notification-fail',
          type: 'endpoint',
          arrow: true,
          Class: WorkflowButterflyEdge,
          label: '不满足条件'
        },
        {
          id: 'edge-4',
          source: 'right',
          target: 'left',
          sourceNode: 'api-success',
          targetNode: 'end-1',
          type: 'endpoint',
          arrow: true,
          Class: WorkflowButterflyEdge
        },
        {
          id: 'edge-5',
          source: 'right',
          target: 'left',
          sourceNode: 'notification-fail',
          targetNode: 'end-1',
          type: 'endpoint',
          arrow: true,
          Class: WorkflowButterflyEdge
        }
      ]
    };
  }, [getNodeEndpoints]);

  // 初始化Butterfly画布
  const initCanvas = useCallback(() => {
    if (!canvasRef.current) {
      console.warn('⚠️ Canvas ref不存在，延迟初始化');
      return;
    }

    // 🔧 修复：在工作流切换时强制重新初始化画布
    // 检查是否需要强制重新初始化（工作流切换）
    const needsForceReinit = workflowData?.id !== lastWorkflowIdRef.current && lastWorkflowIdRef.current !== undefined;

    if (butterflyRef.current && canvasInitialized && !needsForceReinit) {
      console.log('🎨 画布已初始化且正常工作，跳过重新初始化');
      return;
    }

    if (needsForceReinit) {
      console.log('🔄 工作流切换，强制重新初始化画布:', lastWorkflowIdRef.current, '->', workflowData?.id);
    }

    console.log('🎨 开始初始化Butterfly画布...');

    try {
      // 清理现有的画布
      if (butterflyRef.current) {
        console.log('🧹 清理现有画布');
        try {
          if (typeof butterflyRef.current.destroy === 'function') {
            butterflyRef.current.destroy();
          }
        } catch (e) {
          console.warn('清理画布时出错:', e);
        }
        butterflyRef.current = null;
      }

      // 确保容器可见
      const container = canvasRef.current;
      container.innerHTML = ''; // 清空容器内容
      container.style.minHeight = '500px';
      container.style.backgroundColor = '#ffffff';

      // 直接使用已导入的Canvas
      const canvas = new Canvas({
        root: container,
        disLinkable: readonly, // 只读模式下禁止连线
        linkable: !readonly,   // 只读模式下禁止连线
        draggable: !readonly,  // 只读模式下禁止拖拽
        zoomable: true,        // 允许缩放
        moveable: true,        // 允许平移
        theme: {
          edge: {
            shapeType: 'AdvancedBezier',
            arrow: true,
            arrowPosition: 0.5,
          },
          endpoint: {
            position: ['Top', 'Right', 'Bottom', 'Left'],
          },
        },
      });

      butterflyRef.current = canvas as any;
      console.log('✅ Butterfly画布创建成功:', canvas);

      // 绑定事件
      if (!readonly) {
        canvas.on('events', (data: any) => {
          handleCanvasEvent(data);
        });
      }

      // 标记画布已初始化
      setCanvasInitialized(true);
      console.log('✅ 画布初始化完成');

      // 延迟加载数据，确保画布完全准备好
      setTimeout(() => {
        // 加载数据 - 优先使用传入的workflow数据
        if (workflowData && workflowData.nodes && workflowData.nodes.length > 0) {
          // 如果有传入的workflow数据，优先使用传入的数据
          console.log('🎨 初始化：使用传入的workflow数据:', workflowData.name);
          const butterflyData = convertWorkflowToButterflyData(workflowData.nodes);
          canvas.draw(butterflyData);
          lastWorkflowIdRef.current = workflowData.id;
        } else if (workflowId && workflowId !== 'sample') {
          // 如果没有传入数据但有真实的workflowId，从后端加载数据
          console.log('🎨 初始化：从后端加载workflow数据:', workflowId);
          loadWorkflowData();
        } else {
          // 否则使用示例数据
          console.log('🎨 初始化：使用示例数据');
          const sampleData = createSampleData();
          canvas.draw(sampleData);
          lastWorkflowIdRef.current = undefined;
        }
      }, 100);

    } catch (error) {
      console.error('❌ 画布初始化失败:', error);
      message.error('画布初始化失败，可能需要安装butterfly-dag依赖');
      setCanvasInitialized(false);
    }
  }, [readonly, createSampleData, workflowId, loadWorkflowData, workflowData, convertWorkflowToButterflyData, canvasInitialized]);

  // 处理画布事件
  const handleCanvasEvent = (data: any) => {
    // 过滤掉频繁的事件日志，避免日志刷屏
    if (data.type !== 'drag:move' && data.type !== 'drag:start' && data.type !== 'drag:end' &&
        data.type !== 'node:move' && data.type !== 'canvas:resize' && data.type !== 'nodes:add' &&
        data.type !== 'nodes:delete' && data.type !== 'canvas.zoom' && data.type !== 'system.canvas.move') {
      console.log('🎯 Canvas事件触发:', data.type, data);
    }

    switch (data.type) {
      case 'node:click':
        console.log('🎯 节点点击事件:', data.node);
        handleNodeClick(data.node);
        break;
      case 'edge:click':
      case 'link:click':
      case 'system.link.click':
        console.log('🎯 边点击事件:', data.edge);
        handleEdgeClick(data.edge || data.link);
        break;
      case 'canvas:click':
        console.log('🎯 画布点击事件');
        setSelectedNode(null);
        onNodeSelect?.(null);
        setSelectedEdge(null);
        break;
      case 'node:delete':
        console.log('🎯 节点删除事件:', data.node);
        handleNodeDelete(data.node);
        break;
      case 'edge:connect':
      case 'link:connect':
      case 'connection:create':
      case 'system.link.connect':
      case 'system.canvas.link':
        console.log('🎯 边连接事件:', data.type, data);
        // 尝试从不同的数据结构中获取边信息
        let edgeToConnect = null;
        if (data.edge) {
          edgeToConnect = data.edge;
        } else if (data.link) {
          edgeToConnect = data.link;
        } else if (data.links && data.links.length > 0) {
          const link = data.links[0]; // 处理第一个连接
          console.log('🎯 处理边连接:', link);

          // 从Butterfly边对象中提取节点ID
          if (link && typeof link === 'object') {
            // 检查是否是Butterfly边对象
            if (link.sourceNode && link.targetNode) {
              // 如果sourceNode和targetNode是对象，提取其id属性
              const sourceId = typeof link.sourceNode === 'object' ? link.sourceNode.id : link.sourceNode;
              const targetId = typeof link.targetNode === 'object' ? link.targetNode.id : link.targetNode;

              edgeToConnect = {
                sourceNode: sourceId,
                targetNode: targetId,
                source: link.source,
                target: link.target,
                label: link.label || ''
              };
            } else {
              edgeToConnect = link;
            }
          }
        } else if (data.sourceNode && data.targetNode) {
          // 直接从事件数据构造边对象
          edgeToConnect = {
            sourceNode: data.sourceNode,
            targetNode: data.targetNode,
            source: data.source,
            target: data.target,
            label: data.label || ''
          };
        }

        if (edgeToConnect) {
          console.log('🎯 处理边连接:', edgeToConnect);
          handleEdgeConnect(edgeToConnect);
        } else {
          console.warn('🎯 无法从事件数据中提取边信息:', data);
        }
        break;
      case 'edge:disconnect':
      case 'link:disconnect':
      case 'connection:delete':
      case 'system.link.disconnect':
        console.log('🎯 边断开事件:', data.type, data);
        let edgeToDisconnect = null;
        if (data.edge) {
          edgeToDisconnect = data.edge;
        } else if (data.link) {
          edgeToDisconnect = data.link;
        } else if (data.sourceNode && data.targetNode) {
          // 直接从事件数据构造边对象
          edgeToDisconnect = {
            sourceNode: data.sourceNode,
            targetNode: data.targetNode,
            source: data.source,
            target: data.target
          };
        }

        if (edgeToDisconnect) {
          console.log('🎯 处理边断开:', edgeToDisconnect);
          handleEdgeDisconnect(edgeToDisconnect);
        } else {
          console.warn('🎯 无法从事件数据中提取边信息:', data);
        }
        break;
      default:
        console.log('🎯 未处理的事件类型:', data.type, data);
        break;
    }
  };

  // 处理节点点击
  const handleNodeClick = (butterflyNode: any) => {
    const workflowNode = nodes.find(n => n.id === butterflyNode.id);
    if (workflowNode) {
      setSelectedNode(workflowNode);
      onNodeSelect?.(workflowNode);
    }
  };

  // 处理边点击
  const handleEdgeClick = (edge: any) => {
    const sourceNodeId = resolveEdgeNodeId(edge, 'source');
    const targetNodeId = resolveEdgeNodeId(edge, 'target');

    if (!sourceNodeId || !targetNodeId) {
      message.error('无法识别连线节点，请重试');
      return;
    }

    const sourceNode = getNodesSnapshot().find(n => n.id === sourceNodeId);
    const relation = sourceNode?.child_nodes?.find(c => c.node_id === targetNodeId);
    const condition = relation?.condition || {
      type: 'always',
      description: '总是执行'
    };

    setSelectedEdge({
      edgeId: edge?.id,
      sourceNodeId,
      targetNodeId
    });

    edgeForm.setFieldsValue({
      condition_type: condition.type || 'always',
      expression: condition.expression || '',
      description: condition.description || ''
    });
    setEdgeEditorVisible(true);
  };

  const buildConditionDescription = (type: string, expression?: string) => {
    if (type === 'expression') return expression ? `满足条件: ${expression}` : '满足表达式条件时执行';
    if (type === 'form_completed') return '表单完成后执行';
    return '总是执行';
  };

  const handleInsertExpressionField = (field: string) => {
    const current = (edgeForm.getFieldValue('expression') || '').trim();
    if (!current) {
      edgeForm.setFieldValue('expression', `${field} == true`);
      return;
    }

    // 只输入了一个字段名时，自动补全为布尔判断，减少手工输入。
    if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(current)) {
      edgeForm.setFieldValue('expression', `${current} == true`);
      return;
    }

    edgeForm.setFieldValue('expression', `${current} ${field}`);
  };

  const handleSaveEdgeCondition = async () => {
    if (!selectedEdge) return;

    try {
      const values = await edgeForm.validateFields();
      const conditionType = values.condition_type;
      const expression = (values.expression || '').trim();

      if (conditionType === 'expression' && !expression) {
        message.error('表达式条件不能为空');
        return;
      }

      const condition: any = {
        type: conditionType,
        description: (values.description || '').trim() || buildConditionDescription(conditionType, expression)
      };

      if (conditionType === 'expression') {
        condition.expression = expression;
      }

      const currentNodes = getNodesSnapshot();
      const updatedNodes = currentNodes.map(node => {
        if (node.id !== selectedEdge.sourceNodeId) return node;
        return {
          ...node,
          child_nodes: (node.child_nodes || []).map(child => {
            if (child.node_id !== selectedEdge.targetNodeId) return child;
            return {
              ...child,
              condition
            };
          })
        };
      });

      setNodes(updatedNodes);
      latestNodesRef.current = updatedNodes;
      if (workflowData) {
        setWorkflowData({
          ...workflowData,
          nodes: updatedNodes
        });
      }

      setEdgeEditorVisible(false);
      setSelectedEdge(null);
      edgeForm.resetFields();
      message.success('连线条件已更新，请保存工作流以生效');
    } catch (error) {
      console.error('保存连线条件失败:', error);
    }
  };

  const isEndpointId = (value: string) => ['left', 'right', 'top', 'bottom'].includes(value);

  const extractNodeId = (value: any): string | undefined => {
    if (!value) return undefined;
    if (typeof value === 'string') return value;
    if (typeof value === 'object') {
      return (
        value.id ||
        value.nodeId ||
        value.node_id ||
        value.options?.id ||
        value.options?.nodeId ||
        value.options?.node_id ||
        value.node?.id
      );
    }
    return undefined;
  };

  const resolveEdgeNodeId = (edge: any, side: 'source' | 'target'): string | undefined => {
    const candidates = [
      edge?.[`${side}Node`],
      edge?.[`${side}NodeId`],
      edge?.[`${side}NodeID`],
      edge?.[side]?.node,
      edge?.[side]?.nodeId,
      edge?.[side]?.node_id,
      edge?.[side]
    ];

    for (const candidate of candidates) {
      const id = extractNodeId(candidate);
      if (id && !isEndpointId(id)) return id;
    }
    return undefined;
  };

  const buildNodeFromButterfly = (butterflyNode: any): WorkflowNode => {
    const nodeData = butterflyNode?.options?.nodeData;
    if (nodeData) return nodeData as WorkflowNode;

    return {
      id: butterflyNode.id,
      name: butterflyNode.options?.label || butterflyNode.id,
      description: '',
      type: (butterflyNode.options?.nodeType || 'api_call') as any,
      position: {
        x: Math.round(butterflyNode.left || 0),
        y: Math.round(butterflyNode.top || 0)
      },
      parent_nodes: [],
      child_nodes: [],
      config: {},
      outputs: [],
      ai_instructions: {
        purpose: '',
        action: '',
        user_message: '',
        success_handling: '',
        error_handling: ''
      }
    };
  };

  const getNodesSnapshot = (): WorkflowNode[] => {
    if (latestNodesRef.current.length > 0) return latestNodesRef.current;
    if (nodes.length > 0) return nodes;
    if (workflowData?.nodes?.length) return workflowData.nodes;

    const canvasNodes = butterflyRef.current?.getDataMap()?.nodes;
    if (canvasNodes && canvasNodes.length > 0) {
      return canvasNodes.map(buildNodeFromButterfly);
    }
    return [];
  };

  // 处理节点删除（本地操作，不调用API）
  const handleNodeDelete = async (butterflyNode: any) => {
    // 本地删除节点，不调用API
    const updatedNodes = nodes.filter(n => n.id !== butterflyNode.id);
    setNodes(updatedNodes);

    if (selectedNode?.id === butterflyNode.id) {
      setSelectedNode(null);
      onNodeSelect?.(null);
    }

    message.success('节点已删除，请保存工作流以提交更改');
  };

  // 处理边连接
  const handleEdgeConnect = async (edge: any) => {
    try {
      console.log('🔗 处理边连接事件，边数据:', edge);

      // 从边数据中正确获取源节点和目标节点ID
      const sourceNodeId = resolveEdgeNodeId(edge, 'source');
      const targetNodeId = resolveEdgeNodeId(edge, 'target');

      if (!sourceNodeId || !targetNodeId) {
        console.error('❌ 解析节点ID失败:', edge);
        message.error('断开连接失败：无法解析节点');
        return;
      }

      if (!sourceNodeId || !targetNodeId) {
        console.error('❌ 解析节点ID失败:', edge);
        message.error('连接失败：无法解析节点');
        return;
      }

      console.log('🔗 源节点ID:', sourceNodeId, '目标节点ID:', targetNodeId);

      // 更新父子节点关系 - 使用最新的节点状态
      console.log('🔍 当前nodes状态节点数:', nodes.length);
      console.log('🔍 latestNodesRef节点数:', latestNodesRef.current.length);

      // 优先使用latestNodesRef中的最新节点数据
      const currentNodes = getNodesSnapshot();
      console.log('🔍 使用节点数据源:', currentNodes.length > 0 ? 'latestNodesRef' : 'nodes状态');
      console.log('🔍 当前工作流节点ID列表:', currentNodes.map(n => n.id));

      const sourceNode = currentNodes.find(n => n.id === sourceNodeId);
      const targetNode = currentNodes.find(n => n.id === targetNodeId);

      console.log('🔍 查找结果 - 源节点:', sourceNode ? `${sourceNode.name} (${sourceNode.id})` : '未找到');
      console.log('🔍 查找结果 - 目标节点:', targetNode ? `${targetNode.name} (${targetNode.id})` : '未找到');

      // 检查节点是否属于当前工作流
      if (!sourceNode) {
        console.error('❌ 源节点不存在于当前工作流中，可能是工作流切换导致的状态不同步');
        console.error('❌ 尝试连接的源节点ID:', sourceNodeId);
        console.error('❌ 当前工作流:', workflowData?.name || '未知');
        message.error('连接失败：源节点不存在于当前工作流中，请刷新页面重试');
        return;
      }

      if (!targetNode) {
        console.error('❌ 目标节点不存在于当前工作流中，可能是工作流切换导致的状态不同步');
        console.error('❌ 尝试连接的目标节点ID:', targetNodeId);
        console.error('❌ 当前工作流:', workflowData?.name || '未知');
        message.error('连接失败：目标节点不存在于当前工作流中，请刷新页面重试');
        return;
      }

      if (sourceNode && targetNode) {
        console.log('🔗 找到源节点:', sourceNode.name, '目标节点:', targetNode.name);

        // 检查是否重复连接 - 但允许不同类型的连线（手动vs程序）共存
        const existingConnection = sourceNode.child_nodes.find(c => c.node_id === targetNode.id);
        if (existingConnection) {
          // 如果是相同的连线类型，跳过重复连接
          console.log('⚠️ 本地状态中节点已经连接');

          // 检查是否是不同类型的连线（手动 vs 程序创建）
          const isManualConnection = !edge.label || edge.label === '';
          const isProgrammaticConnection = edge.label && edge.label.includes('测试');

          if (isManualConnection && existingConnection.condition?.description?.includes('测试')) {
            console.log('✅ 手动连线替换程序测试连线，更新连线信息');
            // 允许手动连线替换测试连线，继续处理
          } else if (isProgrammaticConnection && !existingConnection.condition?.description?.includes('测试')) {
            console.log('✅ 程序连线替换手动连线，更新连线信息');
            // 允许程序连线替换手动连线，继续处理
          } else {
            console.log('⚠️ 相同类型的连线已存在，跳过重复连接');
            return;
          }
        }

        console.log('✅ 开始更新本地节点连线关系');

        // 更新源节点的子节点列表
        const updatedSourceNode = {
          ...sourceNode,
          child_nodes: [
            ...sourceNode.child_nodes,
            {
              node_id: targetNode.id,
              condition: {
                type: 'always' as const,
                description: edge.label || '总是执行'
              }
            }
          ]
        };

        // 更新目标节点的父节点列表
        const updatedTargetNode = {
          ...targetNode,
          parent_nodes: [...targetNode.parent_nodes, sourceNode.id]
        };

        // 更新本地状态但不触发重绘
        const updatedNodes = currentNodes.map(n => {
          if (n.id === sourceNode.id) return updatedSourceNode;
          if (n.id === targetNode.id) return updatedTargetNode;
          return n;
        });

        setNodes(updatedNodes);
        latestNodesRef.current = updatedNodes;
        latestNodesRef.current = updatedNodes; // 同步更新ref，确保保存时能获取到最新状态

        // 更新workflowData但不触发重绘
        if (workflowData) {
          const updatedWorkflowData = {
            ...workflowData,
            nodes: updatedNodes
          };
          setWorkflowData(prevData => ({ ...updatedWorkflowData }));
        }

        // 检查Butterfly画布中是否已存在相同的边，如果不存在才创建
        if (butterflyRef.current) {
          try {
            const currentData = butterflyRef.current.getDataMap();
            const existingEdge = currentData?.edges?.find((e: any) => {
              const sourceId = e.sourceNode?.id || e.sourceNode;
              const targetId = e.targetNode?.id || e.targetNode;
              return sourceId === sourceNode.id && targetId === targetNode.id;
            });

            if (!existingEdge) {
              const newEdge = {
                id: `edge-${sourceNode.id}-${targetNode.id}-${Date.now()}`,
                source: 'right',  // 源节点的右端点
                target: 'left',   // 目标节点的左端点
                sourceNode: sourceNode.id,
                targetNode: targetNode.id,
                type: 'endpoint',
                arrow: true,
                Class: WorkflowButterflyEdge,
                label: edge.label || '连接'
              };

              console.log('🔗 在Butterfly画布中创建边:', newEdge);
              butterflyRef.current.addEdge(newEdge);
              console.log('✅ Butterfly画布边创建成功');
            } else {
              console.log('✅ Butterfly画布中已存在连线，跳过创建，但本地状态已更新');
            }
          } catch (canvasError) {
            console.warn('⚠️ Butterfly画布边创建失败，但节点关系已更新:', canvasError);
          }
        }

        console.log('✅ 节点连接成功:', `${sourceNode.id} -> ${targetNode.id}`);
        console.log('✅ 更新后的源节点child_nodes:', updatedSourceNode.child_nodes);
        console.log('✅ 更新后的目标节点parent_nodes:', updatedTargetNode.parent_nodes);
        message.success('节点连接成功，请保存工作流以提交更改');
      } else {
        console.error('❌ 找不到源节点或目标节点:', { sourceNodeId, targetNodeId, sourceNode, targetNode });
        message.error('连接失败：找不到对应的节点');
      }
    } catch (error) {
      console.error('❌ 节点连接失败:', error);
      message.error('节点连接失败');
    }
  };

  // 处理边断开
  const handleEdgeDisconnect = async (edge: any) => {
    try {
      console.log('🔗 处理边断开事件，边数据:', edge);

      // 从边数据中正确获取源节点和目标节点ID
      const sourceNodeId = resolveEdgeNodeId(edge, 'source');
      const targetNodeId = resolveEdgeNodeId(edge, 'target');

      console.log('🔗 断开连接 - 源节点ID:', sourceNodeId, '目标节点ID:', targetNodeId);

      const currentNodes = getNodesSnapshot();
      const sourceNode = currentNodes.find(n => n.id === sourceNodeId);
      const targetNode = currentNodes.find(n => n.id === targetNodeId);

      if (sourceNode && targetNode) {
        console.log('🔗 找到要断开的节点:', sourceNode.name, '->', targetNode.name);

        // 更新源节点的子节点列表
        const updatedSourceNode = {
          ...sourceNode,
          child_nodes: sourceNode.child_nodes.filter(c => c.node_id !== targetNode.id)
        };

        // 更新目标节点的父节点列表
        const updatedTargetNode = {
          ...targetNode,
          parent_nodes: targetNode.parent_nodes.filter(p => p !== sourceNode.id)
        };

        // 更新本地状态但不触发重绘
        const updatedNodes = nodes.map(n => {
          if (n.id === sourceNode.id) return updatedSourceNode;
          if (n.id === targetNode.id) return updatedTargetNode;
          return n;
        });

        setNodes(updatedNodes);

        // 更新workflowData但不触发重绘
        if (workflowData) {
          const updatedWorkflowData = {
            ...workflowData,
            nodes: updatedNodes
          };
          setWorkflowData(prevData => ({ ...updatedWorkflowData }));
        }

        console.log('✅ 节点连接已断开:', `${sourceNode.id} -X- ${targetNode.id}`);
        console.log('✅ 更新后的源节点child_nodes:', updatedSourceNode.child_nodes);
        console.log('✅ 更新后的目标节点parent_nodes:', updatedTargetNode.parent_nodes);
        message.success('节点连接已断开，请保存工作流以提交更改');
      } else {
        console.error('❌ 找不到要断开的源节点或目标节点:', { sourceNodeId, targetNodeId, sourceNode, targetNode });
        message.error('断开连接失败：找不到对应的节点');
      }
    } catch (error) {
      console.error('❌ 断开连接失败:', error);
      message.error('断开连接失败');
    }
  };

  // 获取节点标签
  const getNodeLabel = useCallback((nodeType: string) => {
    const labels = {
      start: '开始',
      api_call: 'API调用',
      condition: '条件判断',
      notification: '通知',
      end: '结束'
    };
    return labels[nodeType as keyof typeof labels] || nodeType;
  }, []);

  // 添加节点到画布
  const addNodeToCanvas = useCallback(async (nodeType: string, position?: { x: number; y: number }) => {
    if (!butterflyRef.current || !canvasInitialized) {
      console.warn('⚠️ 画布未初始化，无法添加节点');
      return;
    }

    const nodeId = `${nodeType}-${Date.now()}`;
    // 计算更好的位置：避免重叠，根据现有节点数量调整位置
    const baseX = 100;
    const baseY = 100;
    const spacing = 200;
    const nodesInRow = 4;
    const nodeIndex = nodes.length;
    const row = Math.floor(nodeIndex / nodesInRow);
    const col = nodeIndex % nodesInRow;
    
    // 优先使用传入的位置，如果没有则使用计算的位置，确保坐标是整数
    const pos = position ? {
      x: Math.round(position.x),
      y: Math.round(position.y)
    } : { 
      x: baseX + col * spacing, 
      y: baseY + row * spacing 
    };
    
    console.log(`🎯 添加节点 ${nodeType}，位置计算:`, {
      nodeIndex,
      row,
      col,
      calculatedPos: { x: baseX + col * spacing, y: baseY + row * spacing },
      finalPos: pos,
      passedPosition: position
    });

    // 创建完整的WorkflowNode对象
    const workflowNode: WorkflowNode = {
      id: nodeId,
      name: getNodeLabel(nodeType),
      description: `${getNodeLabel(nodeType)}节点`,
      type: nodeType as any,
      position: pos,
      parent_nodes: [],
      child_nodes: [],
      config: {},
      outputs: [],
      ai_instructions: {
        purpose: `执行${getNodeLabel(nodeType)}操作`,
        action: `处理${getNodeLabel(nodeType)}逻辑`,
        user_message: '',
        success_handling: '',
        error_handling: ''
      }
    };

    // 创建Butterfly节点对象
    const butterflyNode = {
      id: nodeId,
      label: getNodeLabel(nodeType),
      left: pos.x,
      top: pos.y,
      Class: WorkflowButterflyNode,
      nodeType: nodeType,
      endpoints: getNodeEndpoints(nodeType),
      options: {
        nodeType: nodeType,
        label: getNodeLabel(nodeType),
        name: getNodeLabel(nodeType),
        nodeData: workflowNode  // 添加完整的节点数据
      }
    };

    try {
      // 先更新本地状态
      const updatedNodes = [...nodes, workflowNode];
      setNodes(updatedNodes);

      // 更新workflowData
      if (workflowData) {
        const updatedWorkflowData = {
          ...workflowData,
          nodes: updatedNodes
        };
        setWorkflowData(updatedWorkflowData);
      }

      // 添加到Butterfly画布（不重绘整个画布）
      butterflyRef.current.addNode(butterflyNode);
      console.log('✅ 添加节点成功:', butterflyNode);
      message.success(`节点已添加到画布，请保存工作流以提交更改`);
    } catch (error) {
      console.error('❌ 添加节点失败:', error);
      message.error('添加节点失败');
    }
  }, [nodes, workflowData, getNodeLabel, getNodeEndpoints, canvasInitialized]);

  // 删除节点（本地操作，不调用API）
  const removeNodeFromCanvas = useCallback(async (nodeId: string) => {
    if (!butterflyRef.current || !canvasInitialized) {
      console.warn('⚠️ 画布未初始化，无法删除节点');
      return;
    }

    try {
      // 先从Butterfly画布删除
      butterflyRef.current.removeNode(nodeId);
      
      // 再更新本地状态
      const updatedNodes = nodes.filter(n => n.id !== nodeId);
      setNodes(updatedNodes);

      // 更新workflowData
      if (workflowData) {
        const updatedWorkflowData = {
          ...workflowData,
          nodes: updatedNodes
        };
        setWorkflowData(updatedWorkflowData);
      }

      // 如果删除的是当前选中的节点，清空选择
      if (selectedNode?.id === nodeId) {
        setSelectedNode(null);
        onNodeSelect?.(null);
      }

      console.log('✅ 删除节点成功:', nodeId);
      message.success('节点已删除，请保存工作流以提交更改');
    } catch (error) {
      console.error('❌ 删除节点失败:', error);
      message.error('删除节点失败');
    }
  }, [nodes, workflowData, selectedNode, onNodeSelect, canvasInitialized]);

  const updateNodesAfterEdgeRemoval = useCallback(
    (sourceNodeId?: string, targetNodeId?: string) => {
      if (!sourceNodeId || !targetNodeId) return false;

      let changed = false;
      const currentNodes = getNodesSnapshot();
      const updatedNodes = currentNodes.map(node => {
        let nextNode = node;

        if (node.id === sourceNodeId) {
          const nextChildren = (node.child_nodes || []).filter(child => child.node_id !== targetNodeId);
          if (nextChildren.length !== (node.child_nodes || []).length) {
            changed = true;
            nextNode = {
              ...nextNode,
              child_nodes: nextChildren
            };
          }
        }

        if (node.id === targetNodeId) {
          const nextParents = (node.parent_nodes || []).filter(parentId => parentId !== sourceNodeId);
          if (nextParents.length !== (node.parent_nodes || []).length) {
            changed = true;
            nextNode = {
              ...nextNode,
              parent_nodes: nextParents
            };
          }
        }

        return nextNode;
      });

      if (changed) {
        setNodes(updatedNodes);
        latestNodesRef.current = updatedNodes;
        setWorkflowData(prev => (prev ? { ...prev, nodes: updatedNodes } : prev));
      }

      return changed;
    },
    []
  );

  // 删除连线（画布 + 本地状态）
  const removeEdgeFromCanvas = useCallback((edgeInput: string | { edgeId?: string; sourceNodeId?: string; targetNodeId?: string }) => {
    if (!butterflyRef.current || !canvasInitialized) {
      console.warn('⚠️ 画布未初始化，无法删除连线');
      return;
    }

    try {
      let edgeId: string | undefined;
      let sourceNodeId: string | undefined;
      let targetNodeId: string | undefined;

      if (typeof edgeInput === 'string') {
        edgeId = edgeInput;
      } else {
        edgeId = edgeInput.edgeId;
        sourceNodeId = edgeInput.sourceNodeId;
        targetNodeId = edgeInput.targetNodeId;
      }

      if ((!sourceNodeId || !targetNodeId) && edgeId) {
        const currentData = butterflyRef.current.getDataMap?.();
        const targetEdge = currentData?.edges?.find((edge: any) => edge?.id === edgeId);
        if (targetEdge) {
          sourceNodeId = resolveEdgeNodeId(targetEdge, 'source');
          targetNodeId = resolveEdgeNodeId(targetEdge, 'target');
        }
      }

      const removedFromState = updateNodesAfterEdgeRemoval(sourceNodeId, targetNodeId);

      if (edgeId) {
        butterflyRef.current.removeEdge(edgeId);
      }

      if (selectedEdge) {
        const sameById = Boolean(edgeId && selectedEdge.edgeId && selectedEdge.edgeId === edgeId);
        const sameByNodes = Boolean(
          sourceNodeId &&
          targetNodeId &&
          selectedEdge.sourceNodeId === sourceNodeId &&
          selectedEdge.targetNodeId === targetNodeId
        );
        if (sameById || sameByNodes) {
          setSelectedEdge(null);
          setEdgeEditorVisible(false);
          edgeForm.resetFields();
        }
      }

      console.log('✅ 删除连线成功:', edgeId);
      if (removedFromState) {
        message.success('连线已删除，请保存工作流以提交更改');
      } else {
        message.success('连线已删除');
      }
    } catch (error) {
      console.error('❌ 删除连线失败:', error);
      message.error('删除连线失败');
    }
  }, [canvasInitialized, selectedEdge, edgeForm, updateNodesAfterEdgeRemoval]);

  const handleDeleteSelectedEdge = useCallback(() => {
    if (!selectedEdge) return;
    removeEdgeFromCanvas({
      edgeId: selectedEdge.edgeId,
      sourceNodeId: selectedEdge.sourceNodeId,
      targetNodeId: selectedEdge.targetNodeId
    });
  }, [selectedEdge, removeEdgeFromCanvas]);

  // 保存工作流
  const saveWorkflow = async () => {
    if (!onSave || !workflowData) return;

    try {
      // 获取当前画布数据
      const currentData = butterflyRef.current?.getDataMap();
      console.log('💾 获取到的画布数据:', currentData);
      console.log('💾 画布节点数:', currentData?.nodes?.length || 0);
      console.log('💾 画布边数:', currentData?.edges?.length || 0);
      if (currentData?.edges?.length > 0) {
        console.log('💾 边数据详情:', currentData.edges);
      }

      // 将画布数据转换为WorkflowNode格式，保留节点位置
      const updatedNodes: WorkflowNode[] = [];

      if (currentData && currentData.nodes) {
        // 使用ref中的最新节点状态，而不是可能过时的nodes状态
        const latestNodes = latestNodesRef.current;
        console.log('💾 使用最新节点状态，节点数:', latestNodes.length);

        currentData.nodes.forEach((butterflyNode: any) => {
          // 🔧 修复：优先从Butterfly的options.nodeData中获取完整节点数据，然后才从latestNodes中查找
          const butterflyNodeData = butterflyNode.options?.nodeData;
          const existingNode = latestNodes.find(n => n.id === butterflyNode.id);

          // 使用Butterfly中保存的完整节点数据，如果没有则使用latestNodes中的数据
          const sourceNode = butterflyNodeData || existingNode;

          // 调试：检查现有节点的连线关系
          if (sourceNode) {
            console.log(`💾 检查节点 ${sourceNode.name} (${sourceNode.id}) 的连线关系:`, {
              child_nodes: sourceNode.child_nodes,
              parent_nodes: sourceNode.parent_nodes,
              description: sourceNode.description,
              config: sourceNode.config,
              ai_instructions: sourceNode.ai_instructions
            });
          }

          const workflowNode: WorkflowNode = {
            id: butterflyNode.id,
            name: sourceNode?.name || butterflyNode.options?.label || butterflyNode.id,
            type: sourceNode?.type || butterflyNode.options?.nodeType || 'api_call',
            description: sourceNode?.description || '',
            config: sourceNode?.config || {},
            ai_instructions: sourceNode?.ai_instructions || {
              purpose: '',
              action: '',
              user_message: '',
              success_handling: '',
              error_handling: ''
            },
            // 保存实际的画布位置，确保坐标是整数
            position: {
              x: Math.round(butterflyNode.left || 0),
              y: Math.round(butterflyNode.top || 0)
            },
            // 保留本地状态中的连线关系，不重置
            parent_nodes: sourceNode?.parent_nodes || [],
            child_nodes: sourceNode?.child_nodes || [],
            outputs: sourceNode?.outputs || []
          };
          updatedNodes.push(workflowNode);
        });

        // 不再从画布边数据重建连线关系，因为我们已经保留了本地状态中的连线关系
        console.log('💾 保留本地状态中的连线关系，节点连线详情:');
        let hasConnections = false;
        updatedNodes.forEach(node => {
          if (node.child_nodes.length > 0 || node.parent_nodes.length > 0) {
            hasConnections = true;
            console.log(`💾 节点 ${node.name} (${node.id}):`, {
              child_nodes: node.child_nodes,
              parent_nodes: node.parent_nodes
            });
          }
        });

        if (!hasConnections) {
          console.warn('💾 ⚠️ 没有找到任何连线关系！这可能是问题所在');
          console.log('💾 所有节点的连线状态:');
          updatedNodes.forEach(node => {
            console.log(`💾 节点 ${node.name} (${node.id}):`, {
              child_nodes: node.child_nodes,
              parent_nodes: node.parent_nodes
            });
          });
        }
      } else {
        // 如果没有画布数据，使用本地节点数据
        updatedNodes.push(...nodes);
      }

      // 创建更新后的工作流定义，确保符合API文档要求
      const updatedWorkflow: WorkflowDefinition = {
        id: workflowData.id,
        name: workflowData.name || '未命名工作流',
        description: workflowData.description || '',
        business_scenario: workflowData.business_scenario || 'general',
        user_intents: workflowData.user_intents || [],
        trigger_keywords: workflowData.trigger_keywords || [],
        inputs: workflowData.inputs || [],
        nodes: updatedNodes,
        metadata: {
          tags: workflowData.metadata?.tags || [],
          complexity: workflowData.metadata?.complexity || 'medium',
          created_by: workflowData.metadata?.created_by,
          created_at: workflowData.metadata?.created_at,
          updated_at: new Date().toISOString()
        }
      };

      console.log('💾 保存工作流，节点数:', updatedNodes.length);
      console.log('💾 节点位置信息:', updatedNodes.map(n => ({ id: n.id, position: n.position })));

      // 调用保存回调
      onSave(updatedWorkflow);

    } catch (error) {
      console.error('保存工作流失败:', error);
      message.error('保存工作流失败');
    }
  };

  // 添加新节点（本地操作，不调用API）
  const addNode = async (nodeType: string, position: { x: number; y: number }) => {
    if (!workflowId) return;

    const newNode: WorkflowNode = {
      id: `node_${Date.now()}`,
      name: `新${getNodeTypeName(nodeType)}`,
      description: `描述新的${getNodeTypeName(nodeType)}`,
      type: nodeType as any,
      position,
      parent_nodes: [],
      child_nodes: [],
      config: {},
      outputs: [],
      ai_instructions: {
        purpose: '',
        action: '',
      },
    };

    // 本地添加节点，不调用API
    const updatedNodes = [...nodes, newNode];
    setNodes(updatedNodes);

    // 更新画布（使用现有的addNodeToCanvas逻辑）
    addNodeToCanvas(nodeType, position);

    message.success('节点已添加到画布，请保存工作流以提交更改');
  };

  // 获取节点类型名称
  const getNodeTypeName = (nodeType: string) => {
    const nameMap: Record<string, string> = {
      start: '开始节点',
      api_call: 'API调用',
      condition: '条件判断',
      notification: '通知节点',
      end: '结束节点',
    };
    return nameMap[nodeType] || '节点';
  };

  // 保存节点编辑（本地操作，不调用API，不触发重绘）
  const handleSaveNode = async (updatedNode: WorkflowNode) => {
    // 只更新本地状态，不调用API，不触发重绘
    const updatedNodes = nodes.map(n => n.id === updatedNode.id ? updatedNode : n);
    setNodes(updatedNodes);

    // 🔧 修复：同步更新latestNodesRef，确保保存工作流时能获取到最新的节点数据
    latestNodesRef.current = updatedNodes;

    // 更新workflowData但不触发重绘
    if (workflowData) {
      const updatedWorkflowData = {
        ...workflowData,
        nodes: updatedNodes
      };
      setWorkflowData(prevData => ({ ...updatedWorkflowData }));
    }

    setEditorVisible(false);
    message.success('节点已更新，请保存工作流以提交更改');
  };

  // 处理拖拽放置
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const nodeType = e.dataTransfer.getData('application/workflow-node');
    if (nodeType && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const position = {
        x: Math.round(e.clientX - rect.left),
        y: Math.round(e.clientY - rect.top)
      };
      addNodeToCanvas(nodeType, position);
    }
  }, [addNodeToCanvas]);

  // 处理节点调色板的节点添加
  const handleNodeDrop = useCallback((nodeType: string, position: { x: number; y: number }) => {
    addNodeToCanvas(nodeType, position);
  }, [addNodeToCanvas]);

  // 监听节点删除事件
  useEffect(() => {
    const handleNodeDeleteEvent = (e: any) => {
      const { nodeId } = e.detail;
      removeNodeFromCanvas(nodeId);
    };

    document.addEventListener('node-delete', handleNodeDeleteEvent);

    return () => {
      document.removeEventListener('node-delete', handleNodeDeleteEvent);
    };
  }, [removeNodeFromCanvas]);

  // 监听节点编辑事件
  useEffect(() => {
    const handleNodeEditEvent = (e: any) => {
      const { nodeId, nodeType } = e.detail;

      // 🔧 修复：从实际的节点数据中查找节点，而不是创建模拟对象
      let actualNode = latestNodesRef.current.find(n => n.id === nodeId);

      // 如果在latestNodesRef中没找到，尝试从Butterfly画布的options.nodeData中获取
      if (!actualNode && butterflyRef.current) {
        try {
          // 使用类型断言来访问getNode方法
          const canvas = butterflyRef.current as any;
          const butterflyNode = canvas.getNode(nodeId);
          if (butterflyNode && butterflyNode.options && butterflyNode.options.nodeData) {
            actualNode = butterflyNode.options.nodeData;
            console.log('🔍 从Butterfly画布获取节点数据:', actualNode);
          }
        } catch (error) {
          console.warn('⚠️ 无法从Butterfly画布获取节点数据:', error);
        }
      }

      // 如果还是没找到，才创建模拟对象（向后兼容）
      if (!actualNode) {
        console.warn('⚠️ 未找到节点数据，创建模拟对象:', nodeId);
        actualNode = {
          id: nodeId,
          name: getNodeLabel(nodeType),
          type: nodeType as any,
          description: '',
          config: {},
          ai_instructions: {
            purpose: '',
            action: '',
            user_message: '',
            success_handling: '',
            error_handling: ''
          },
          position: { x: 0, y: 0 },
          parent_nodes: [],
          child_nodes: [],
          outputs: []
        };
      } else {
        console.log('✅ 找到实际节点数据:', actualNode.name, actualNode.description);
      }

      setSelectedNode(actualNode);
      setEditorVisible(true);
    };

    document.addEventListener('node-edit', handleNodeEditEvent);

    return () => {
      document.removeEventListener('node-edit', handleNodeEditEvent);
    };
  }, [getNodeLabel]);

  // 监听连线删除事件
  useEffect(() => {
    const handleEdgeDeleteEvent = (e: any) => {
      const detail = e.detail || {};
      removeEdgeFromCanvas({
        edgeId: detail.edgeId,
        sourceNodeId: extractNodeId(detail.sourceNode) || detail.sourceNodeId,
        targetNodeId: extractNodeId(detail.targetNode) || detail.targetNodeId
      });
    };

    document.addEventListener('edge-delete', handleEdgeDeleteEvent);

    return () => {
      document.removeEventListener('edge-delete', handleEdgeDeleteEvent);
    };
  }, [removeEdgeFromCanvas]);

  // 监听连线点击事件（来自自定义Edge标签）
  useEffect(() => {
    const handleEdgeClickEvent = (e: any) => {
      const detail = e.detail || {};
      handleEdgeClick({
        id: detail.edgeId,
        sourceNode: detail.sourceNode || detail.sourceNodeId,
        targetNode: detail.targetNode || detail.targetNodeId
      });
    };

    document.addEventListener('edge-click', handleEdgeClickEvent);

    return () => {
      document.removeEventListener('edge-click', handleEdgeClickEvent);
    };
  }, [nodes, workflowData]);

  // 初始化画布
  useEffect(() => {
    initCanvas();

    // 清理函数
    return () => {
      if (butterflyRef.current) {
        // Butterfly可能没有destroy方法，使用其他清理方式
        try {
          if (typeof butterflyRef.current.destroy === 'function') {
            butterflyRef.current.destroy();
          } else {
            // 清理事件监听器
            butterflyRef.current.off?.('node:click', () => {});
            butterflyRef.current.off?.('edge:click', () => {});
            butterflyRef.current.off?.('canvas:click', () => {});
          }
        } catch (error) {
          console.warn('Failed to destroy butterfly canvas:', error);
        }
      }
    };
  }, [initCanvas]);

  // 监听工作流数据变化，避免不必要的完整重绘
  useEffect(() => {
    if (!canvasInitialized || !butterflyRef.current) {
      console.log('🎨 画布未初始化，跳过绘制');
      return;
    }

    // 只在初始化时或工作流ID变化时进行完整重绘
    const isInitialLoad = workflowData && !butterflyRef.current.getDataMap()?.nodes?.length;
    const workflowIdChanged = workflowData?.id !== lastWorkflowIdRef.current;

    if (isInitialLoad || workflowIdChanged) {
      console.log('🎨 初始加载或工作流切换，进行完整重绘:', workflowData?.name || 'local nodes');

      // 🔧 修复：工作流切换时重新初始化画布，而不是清空
      if (workflowIdChanged && lastWorkflowIdRef.current) {
        console.log('🔄 工作流切换，重新初始化画布以确保完全清空');
        // 强制重新初始化画布
        setCanvasInitialized(false);
        initCanvas();
        return; // 重新初始化后会自动绘制新数据
      }

      // 绘制工作流数据
      if (workflowData && workflowData.nodes && workflowData.nodes.length > 0 && butterflyRef.current) {
        console.log('🎨 绘制工作流节点:', workflowData.nodes.length, '个节点');
        const butterflyData = convertWorkflowToButterflyData(workflowData.nodes);
        butterflyRef.current.draw(butterflyData);
        lastWorkflowIdRef.current = workflowData.id; // 记录当前工作流ID

        // 更新React状态以保持同步
        setNodes(workflowData.nodes);
        latestNodesRef.current = workflowData.nodes;
      } else if (nodes.length > 0 && !workflowData && butterflyRef.current) {
        console.log('🎨 绘制本地节点:', nodes.length, '个节点');
        const butterflyData = convertWorkflowToButterflyData(nodes);
        butterflyRef.current.draw(butterflyData);
        lastWorkflowIdRef.current = undefined;
      }
    } else {
      console.log('🎨 跳过重绘，避免破坏现有连线和位置');
    }
  }, [workflowData?.id, canvasInitialized]); // 移除nodes.length依赖，避免每次节点变化都重绘

  // 监听外部传入的workflow prop变化 - 只在真正变化时更新
  useEffect(() => {
    if (workflow && workflow !== workflowData) {
      console.log('🔄 外部workflow变化，更新状态:', workflow.name, '节点数:', workflow.nodes?.length || 0);
      setWorkflowData(workflow);
      setNodes(workflow.nodes || []);
    } else if (!workflow && workflowData) {
      // 如果外部传入空workflow，清空所有状态
      console.log('🔄 外部workflow为空，清空所有状态');
      setWorkflowData(null);
      setNodes([]);
    }
  }, [workflow?.id, workflow?.nodes?.length]); // 只依赖关键标识符，避免无限循环

  return (
    <div className="workflow-canvas-container">
      {/* 左侧工具区域 */}
      {!readonly && (
        <div className="workflow-sidebar">
          {/* 节点调色板 */}
          <NodePalette
            onNodeDrop={handleNodeDrop}
            loading={loading}
            existingNodes={nodes.map(node => ({
              nodeType: node.type,
              id: node.id
            }))}
          />

          {/* 保存按钮 */}
          {onSave && (
            <div className="workflow-actions">
              <button
                onClick={saveWorkflow}
                className="save-workflow-btn"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  backgroundColor: '#1890ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'all 0.2s ease',
                  marginTop: '16px'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#40a9ff';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(24, 144, 255, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#1890ff';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                💾 保存工作流
              </button>
            </div>
          )}
        </div>
      )}

      {/* 画布区域 */}
      <div
        ref={canvasRef}
        className={`workflow-canvas ${readonly ? 'readonly' : ''}`}
        style={{ 
          width: '100%', 
          height: '500px', 
          border: '1px solid #d9d9d9', 
          borderRadius: '8px',
          backgroundColor: '#ffffff',
          position: 'relative',
          overflow: 'visible'
        }}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {/* 调试信息 */}
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '5px 10px',
          borderRadius: '4px',
          fontSize: '12px',
          zIndex: 1000
        }}>
          画布状态: {canvasInitialized ? '已初始化' : '未初始化'} | 节点数: {nodes.length}
        </div>
      </div>

      {/* 节点编辑器 */}
      <Drawer
        title="编辑节点"
        placement="right"
        width={500}
        open={editorVisible}
        onClose={() => setEditorVisible(false)}
        destroyOnHidden
      >
        {selectedNode && (
          <NodeEditor
            node={selectedNode}
            onSave={handleSaveNode}
            onCancel={() => setEditorVisible(false)}
          />
        )}
      </Drawer>

      <Modal
        title="编辑连线条件"
        open={edgeEditorVisible}
        onCancel={() => {
          setEdgeEditorVisible(false);
          setSelectedEdge(null);
          edgeForm.resetFields();
        }}
        footer={[
          <Button key="delete" danger onClick={handleDeleteSelectedEdge} disabled={!selectedEdge}>
            删除连线
          </Button>,
          <Button
            key="cancel"
            onClick={() => {
              setEdgeEditorVisible(false);
              setSelectedEdge(null);
              edgeForm.resetFields();
            }}
          >
            取消
          </Button>,
          <Button key="save" type="primary" onClick={handleSaveEdgeCondition}>
            保存
          </Button>
        ]}
        destroyOnHidden
      >
        <Form form={edgeForm} layout="vertical">
          <Form.Item label="条件类型" name="condition_type" rules={[{ required: true, message: '请选择条件类型' }]}>
            <Select
              options={[
                { label: '总是执行', value: 'always' },
                { label: '表达式条件', value: 'expression' },
                { label: '表单完成后执行', value: 'form_completed' }
              ]}
            />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.condition_type !== cur.condition_type}>
            {({ getFieldValue }) =>
              getFieldValue('condition_type') === 'expression' ? (
                <>
                  <Form.Item label="字段候选">
                    <Select
                      showSearch
                      placeholder="选择字段自动插入表达式"
                      optionFilterProp="label"
                      onSelect={(value) => handleInsertExpressionField(String(value))}
                      options={edgeFieldCandidates.map(field => ({
                        label: field,
                        value: field
                      }))}
                    />
                  </Form.Item>
                  <Form.Item
                    label="表达式"
                    name="expression"
                    rules={[{ required: true, message: '请输入表达式，例如 verified == true' }]}
                  >
                    <AutoComplete options={expressionAutoCompleteOptions} filterOption>
                      <Input placeholder="例如：verified == true" />
                    </AutoComplete>
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>
          <Form.Item label="条件说明（可选）" name="description">
            <Input placeholder="例如：验证通过后执行" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 画布加载状态 */}
      {!canvasInitialized && (
        <div className="canvas-loading">
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔧</div>
            <h3>正在初始化画布...</h3>
            <p>如果长时间未响应，请确保已安装butterfly-dag依赖包</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowCanvas; 
