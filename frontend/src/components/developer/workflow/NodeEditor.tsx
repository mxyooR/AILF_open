/**
 * 工作流节点编辑器组件 - Apple风格设计
 * 支持编辑不同类型节点的属性和配置
 */

import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Space,
  Card,
  Row,
  Col,
  Typography,
  Alert,
  message,
} from 'antd';

import {
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import type {
  WorkflowNode,
  NodeType,
  APICallConfig,
  NotificationConfig
} from '../../../types/developer/workflowTypes';
import { routeAPI } from '../../../services/developer/routeAPI';
import type { APIRoute } from '../../../types/developer/route';
import './NodeEditor.css';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;

interface NodeEditorProps {
  node: WorkflowNode;
  onSave: (updatedNode: WorkflowNode) => void;
  onCancel: () => void;
  availableRoutes?: APIRoute[];
}

const NodeEditor: React.FC<NodeEditorProps> = ({ node, onSave, onCancel, availableRoutes }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [apiRoutes, setApiRoutes] = useState<APIRoute[]>([]);
  const [loadingRoutes, setLoadingRoutes] = useState(false);

  // Routes may be injected for the standalone editor demo.
  useEffect(() => {
    if (node.type !== 'api_call') return;
    if (availableRoutes !== undefined) {
      setApiRoutes(availableRoutes);
      return;
    }
    let cancelled = false;
    setLoadingRoutes(true);
    routeAPI.getRoutes({ status: 'active', page: 1, limit: 100 }).then(response => {
      if (cancelled) return;
      if (response.code === 200 && response.data) {
        setApiRoutes(response.data.routes || []);
      } else {
        message.error(response.message || '获取API路由列表失败');
      }
    }).catch(() => { if (!cancelled) message.error('获取API路由列表失败'); })
      .finally(() => { if (!cancelled) setLoadingRoutes(false); });
    return () => { cancelled = true; };
  }, [node.type, availableRoutes]);

  // 初始化表单数据
  useEffect(() => {
    const config = node.config as any;
    // 🔧 修复：为ai_instructions提供安全的默认值，防止undefined错误
    const aiInstructions = node.ai_instructions || {
      purpose: '',
      action: '',
      user_message: '',
      success_handling: '',
      error_handling: ''
    };

    const formValues: any = {
      name: node.name,
      description: node.description,
      outputs: node.outputs || [],
      selected_route: undefined,
      ai_purpose: aiInstructions.purpose,
      ai_action: aiInstructions.action,
      ai_user_message: aiInstructions.user_message,
      ai_success_handling: aiInstructions.success_handling,
      ai_error_handling: aiInstructions.error_handling,
    };

    // 根据节点类型设置特定字段
    if (node.type === 'api_call' && config) {
      formValues.api_id = config.api_id;
      formValues.api_endpoint = config.api_endpoint;
      formValues.method = config.method;
      formValues.parameters = JSON.stringify(config.parameters || {}, null, 2);
      formValues.ui_mode = config.ui_mode || 'auto';
      formValues.context_fields = config.context_fields || [];
    } else if (node.type === 'condition' && config) {
      formValues.conditions = config.conditions || [];
      formValues.logic = config.logic || 'and';
      formValues.evaluation_expression = config.evaluation_expression;
    } else if (node.type === 'notification') {
      formValues.message = config?.message || '';
      formValues.notification_type = config?.type || 'info';
      formValues.channels = config?.channels || [];
    } else {
      // 其他节点类型的配置
      Object.assign(formValues, config);
    }

    form.setFieldsValue(formValues);
  }, [node, form]);

  // 🔧 修复：当API路由加载完成后，根据api_id设置selected_route字段
  useEffect(() => {
    if (node.type === 'api_call' && apiRoutes.length > 0) {
      const config = node.config as any;
      if (config && config.api_id) {
        // 根据api_id找到对应的路由
        const matchingRoute = apiRoutes.find(route => route.api_id === config.api_id);
        if (matchingRoute) {
          form.setFieldsValue({ selected_route: matchingRoute.id });
        }
      }
    }
  }, [apiRoutes, node, form]);

  // 保存节点
  const handleSave = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      const updatedNode: WorkflowNode = {
        ...node,
        name: values.name,
        description: values.description,
        config: extractConfig(values, node.type),
        outputs: values.outputs || node.outputs || [],
        ai_instructions: {
          ...node.ai_instructions,
          purpose: values.ai_purpose,
          action: values.ai_action,
          user_message: values.ai_user_message,
          success_handling: values.ai_success_handling,
          error_handling: values.ai_error_handling,
        },
      };

      onSave(updatedNode);
    } catch (error) {
      if (error instanceof SyntaxError) message.error('请求参数必须是有效的 JSON');
    } finally {
      setLoading(false);
    }
  };

  // 根据节点类型提取配置
  const extractConfig = (values: any, nodeType: NodeType) => {
    switch (nodeType) {
      case 'api_call':
        return {
          api_id: values.api_id,
          api_endpoint: values.api_endpoint,
          method: values.method,
          parameters: values.parameters ? JSON.parse(values.parameters || '{}') : {},
          ui_mode: values.ui_mode || 'auto',
          context_fields: values.context_fields || [],
        } as APICallConfig;
      
      // user_input 已废弃，所有用户输入通过 api_call 的 POST 表单完成
      case 'condition':
        // Branch routing is configured on outgoing edges. Preserve legacy node metadata.
        return { ...node.config };
      
      case 'notification':
        return {
          message: values.message,
          type: values.notification_type,
          channels: values.channels || [],
        } as NotificationConfig;
      
      default:
        return {};
    }
  };

  // 渲染节点类型特定的配置表单
  // 处理API路由选择变化
  const handleApiRouteChange = (routeId: string) => {
    const selectedRoute = apiRoutes.find(route => route.id === routeId);
    if (selectedRoute) {
      form.setFieldsValue({
        api_id: selectedRoute.api_id,
        api_endpoint: selectedRoute.endpoint,
        method: selectedRoute.method,
      });
    }
  };

  const renderNodeSpecificConfig = () => {
    switch (node.type) {
      case 'api_call':
        return (
          <Card title="API调用配置" size="small" className="config-section">
            <Form.Item
              name="selected_route"
              label="选择API路由"
              rules={[{ required: true, message: '请选择API路由' }]}
            >
              <Select
                placeholder="选择要调用的API路由"
                loading={loadingRoutes}
                onChange={handleApiRouteChange}
                showSearch
                optionFilterProp="label"
                filterOption={(input, option) =>
                  (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                }
              >
                {apiRoutes.map(route => (
                  <Option
                    key={route.id}
                    value={route.id}
                    label={`${route.name} ${route.method} ${route.endpoint}`}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>{route.name}</span>
                      <span style={{ color: '#666', fontSize: '12px' }}>
                        {route.method} {route.endpoint}
                      </span>
                    </div>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="api_id"
                  label="API标识"
                  rules={[{ required: true, message: '请输入API标识' }]}
                >
                  <Input placeholder="例如: user_search_api" disabled />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="method"
                  label="请求方法"
                  rules={[{ required: true, message: '请选择请求方法' }]}
                >
                  <Select disabled>
                    <Option value="GET">GET</Option>
                    <Option value="POST">POST</Option>
                    <Option value="PUT">PUT</Option>
                    <Option value="DELETE">DELETE</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="api_endpoint"
              label="API端点"
              rules={[{ required: true, message: '请输入API端点' }]}
            >
              <Input placeholder="例如: /api/users/search" disabled />
            </Form.Item>

            <Form.Item
              name="parameters"
              label="请求参数 (JSON)"
            >
              <Input.TextArea
                rows={6}
                placeholder='{"department": "${department}"}'
              />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="ui_mode"
                  label="交互模式"
                >
                  <Select>
                    <Option value="auto">自动执行（无表单）</Option>
                    <Option value="form">渲染表单</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="context_fields"
                  label="上下文展示白名单"
                >
                  <Select
                    mode="tags"
                    tokenSeparators={[',', ' ']}
                    placeholder="ticket_number, refund_amount"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Alert
              message="数据引用语法"
              description={
                <div>
                  <p>使用 <code>{'${字段名}'}</code> 引用会话数据，也可以读取前置 API 的结果：</p>
                  <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                    <li><code>{'${department}'}</code> — 引用输入的科室</li>
                    <li><code>{'${lookup_result.total}'}</code> — 引用 lookup 节点的结果字段</li>
                    <li><code>{'${last_api_result.total}'}</code> — 引用最近一次 API 的结果字段</li>
                  </ul>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Alert
              message="API路由信息"
              description="选择API路由后，API标识、请求方法和端点将自动填充。您只需要配置请求参数即可。"
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Card>
        );

      // user_input 已废弃，所有用户输入通过 api_call 的 POST 表单完成

      case 'condition':
        return (
          <Card title="条件判断配置" size="small" className="config-section">
            <Alert
              message="在出边上设置分支条件"
              description="关闭此面板，点击连线标签编辑条件。系统按出边顺序选择第一个满足条件的步骤；将“总是执行”的兜底分支放在最后。支持 total > 0、verified == true 等单字段比较。"
              type="info"
              showIcon
              className="syntax-tip"
            />
            {(node.child_nodes || []).map(child => <p key={child.node_id} style={{ margin: '16px 0 0' }}>
              <code>{child.condition.expression || child.condition.type}</code> → {child.node_id}<br />
              <Text type="secondary">{child.condition.description}</Text>
            </p>)}
          </Card>
        );

      case 'notification':
        return (
          <Card title="通知配置" size="small" className="config-section">
            <Row gutter={16}>
              <Col span={16}>
                <Form.Item
                  name="message"
                  label="通知消息"
                  rules={[{ required: true, message: '请输入通知消息' }]}
                >
                  <TextArea 
                    rows={3} 
                    placeholder="通知用户的消息内容"
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="notification_type"
                  label="消息类型"
                  rules={[{ required: true, message: '请选择消息类型' }]}
                >
                  <Select>
                    <Option value="info">信息</Option>
                    <Option value="success">成功</Option>
                    <Option value="warning">警告</Option>
                    <Option value="error">错误</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="node-editor">
      <Form form={form} layout="vertical" className="editor-form">
        {/* 基本信息 */}
        <Card title="基本信息" size="small" className="config-section">
          <Form.Item
            name="name"
            label="节点名称"
            rules={[{ required: true, message: '请输入节点名称' }]}
          >
            <Input placeholder="请输入节点名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="节点描述"
            rules={[{ required: true, message: '请输入节点描述' }]}
          >
            <TextArea rows={2} placeholder="描述节点的功能和用途" />
          </Form.Item>
        </Card>

        {/* 节点特定配置 */}
        {renderNodeSpecificConfig()}

        {/* AI指令配置 */}
        <Card title="AI执行指令" size="small" className="config-section">
          <Form.Item
            name="ai_purpose"
            label="执行目的"
            rules={[{ required: true, message: '请输入执行目的' }]}
          >
            <TextArea rows={2} placeholder="描述这个节点的执行目的" />
          </Form.Item>
          <Form.Item
            name="ai_action"
            label="执行动作"
            rules={[{ required: true, message: '请输入执行动作' }]}
          >
            <TextArea rows={2} placeholder="描述AI应该执行的具体动作" />
          </Form.Item>
          <Form.Item
            name="ai_user_message"
            label="用户消息"
          >
            <TextArea rows={2} placeholder="向用户显示的消息" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="ai_success_handling"
                label="结束页成功文案（可选）"
              >
                <TextArea rows={2} placeholder="例如：校验通过，已进入下一步处理。" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="ai_error_handling"
                label="结束页失败文案（可选）"
              >
                <TextArea rows={2} placeholder="例如：身份验证失败：{failure_reason}" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 操作按钮 */}
        <div className="editor-actions">
          <Space>
            <Button onClick={onCancel}>
              <CloseOutlined /> 取消
            </Button>
            <Button 
              type="primary" 
              loading={loading}
              onClick={handleSave}
            >
              <SaveOutlined /> 保存
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );
};

export default NodeEditor; 
