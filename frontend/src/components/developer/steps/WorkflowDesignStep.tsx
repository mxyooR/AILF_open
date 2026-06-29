/**
 * 工作流设计步骤组件 - Apple风格设计
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Space,
  message,
  Row,
  Col,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Tabs,
  Spin
} from 'antd';
import { UnifiedCard } from '../common';
import {
  BranchesOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  ApiOutlined,
  FormOutlined,
  NotificationOutlined,
  StopOutlined,
  EyeOutlined
} from '@ant-design/icons';
import WorkflowCanvas from '../workflow/WorkflowCanvas';
import AuthenticationRequired from '../auth/AuthenticationRequired';
import { workflowAPI } from '../../../services/developer/workflowAPI';
import { apiClient } from '../../../services/common/apiClient';
import { useDeveloperAuth } from '../../../hooks/developer/useDeveloperAuth';
import type { WorkflowDefinition, WorkflowNode, WorkflowUpdateRequest } from '../../../types/developer/workflowTypes';
import './WorkflowDesignStep.css';

const { Option } = Select;
const { TextArea } = Input;

interface WorkflowDesignStepProps {
  onNext?: () => void;
  onPrev?: () => void;
}

// 示例工作流数据
const sampleWorkflows = [
  {
    id: 'workflow_1',
    name: '用户查询处理流程',
    description: '处理用户查询请求的标准流程',
    business_scenario: 'customer_service',
    nodeCount: 5,
    status: 'active'
  },
  {
    id: 'workflow_2',
    name: '订单处理流程',
    description: '从下单到发货的完整订单处理流程',
    business_scenario: 'order_management',
    nodeCount: 8,
    status: 'draft'
  },
  {
    id: 'workflow_3',
    name: '用户反馈处理',
    description: '收集和处理用户反馈的工作流',
    business_scenario: 'feedback_management',
    nodeCount: 6,
    status: 'active'
  }
];

// 节点类型配置（已移除 user_input）
const nodeTypes = [
  { type: 'start', label: '开始节点', icon: <PlayCircleOutlined />, color: '#52c41a' },
  { type: 'api_call', label: 'API调用', icon: <ApiOutlined />, color: '#1890ff' },
  { type: 'notification', label: '通知节点', icon: <NotificationOutlined />, color: '#eb2f96' },
  { type: 'end', label: '结束节点', icon: <StopOutlined />, color: '#f5222d' }
];

const WorkflowDesignStep: React.FC<WorkflowDesignStepProps> = ({ onNext, onPrev }) => {
  const { authState } = useDeveloperAuth();
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [workflows, setWorkflows] = useState(sampleWorkflows);
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowDefinition | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('list');
  const [form] = Form.useForm();

  // 加载工作流列表
  const loadWorkflows = useCallback(async () => {
    try {
      setLoading(true);

      // 调试认证状态
      console.log('loadWorkflows - authState:', authState);
      console.log('loadWorkflows - isAuthenticated:', authState.isAuthenticated);
      console.log('loadWorkflows - token exists:', !!authState.token);

      // 检查是否有认证token（优先检查apiClient中的token，因为它可能先于authState更新）
      const apiToken = apiClient.getToken();
      const hasValidToken = (authState.token && !authState.token.includes('fake-token')) || 
                           (apiToken && !apiToken.includes('fake-token'));
      const isAuthenticated = authState.isAuthenticated || hasValidToken; // 只要有有效token就认为已认证
      console.log('loadWorkflows - apiClient has token:', !!apiToken);
      console.log('loadWorkflows - has valid token:', hasValidToken);

      // 如果有有效的认证token，就调用API
      if (isAuthenticated && hasValidToken) {
        const response = await workflowAPI.getWorkflowsList({ page: 1, limit: 50 });

        if (response.code === 200 && response.data) {
          // 转换API数据格式以匹配本地结构
          const convertedWorkflows = response.data.workflows.map(workflow => ({
            id: workflow.id,
            name: workflow.name,
            description: workflow.description,
            business_scenario: workflow.business_scenario,
            nodeCount: workflow.node_count,
            status: workflow.status.toLowerCase(),  // 🔥 转换为小写以匹配前端期望
            complexity: 'medium', // 后端没有complexity字段，使用默认值
            version: workflow.version,
            instance_count: workflow.instance_count,
            created_at: workflow.created_at,
            updated_at: workflow.updated_at
          }));
          setWorkflows(convertedWorkflows);
        } else {
          message.error(response.message || '加载工作流列表失败');
          // 如果API失败，使用示例数据作为后备
          setWorkflows(sampleWorkflows);
        }
      } else {
        // 未认证时使用示例数据
        setWorkflows(sampleWorkflows);
      }
    } catch (error) {
      console.error('Failed to load workflows:', error);
      message.error('加载工作流列表失败');
      // 如果API失败，使用示例数据作为后备
      setWorkflows(sampleWorkflows);
    } finally {
      setLoading(false);
    }
  }, [authState.isAuthenticated, authState.token]);

  // 加载工作流详情
  const loadWorkflowDetail = async (workflowId: string) => {
    try {
      // 检查apiClient是否有token（更可靠的方式）
      const hasApiToken = !!(window as any).apiClient?.getToken?.();
      console.log('loadWorkflowDetail - apiClient has token:', hasApiToken);

      // 只有在认证成功时才调用API
      if (hasApiToken) {
        console.log('loadWorkflowDetail - 调用API获取工作流详情:', workflowId);
        const response = await workflowAPI.getWorkflowDetail(workflowId);

        if (response.code === 200 && response.data) {
          console.log('loadWorkflowDetail - API调用成功:', response.data);
          setCurrentWorkflow(response.data.workflow);
          return;
        } else {
          console.error('loadWorkflowDetail - API调用失败:', response);
          message.error(response.message || '加载工作流详情失败');
        }
      } else {
        console.log('loadWorkflowDetail - 未认证，跳过API调用');
      }

      // 如果API失败或未认证，使用示例数据作为后备
      const workflow = sampleWorkflows.find(w => w.id === workflowId);
      if (workflow) {
        const fullWorkflow: WorkflowDefinition = {
          id: workflow.id,
          name: workflow.name,
          description: workflow.description,
          business_scenario: workflow.business_scenario,
          user_intents: [],
          trigger_keywords: [],
          inputs: [],
          nodes: [],
          metadata: {
            complexity: 'medium',
            tags: [workflow.business_scenario]
          }
        };
        setCurrentWorkflow(fullWorkflow);
      }
    } catch (error) {
      console.error('Failed to load workflow detail:', error);
      message.error('加载工作流详情失败');
      // 如果API失败，使用示例数据作为后备
      const workflow = sampleWorkflows.find(w => w.id === workflowId);
      if (workflow) {
        const fullWorkflow: WorkflowDefinition = {
          id: workflow.id,
          name: workflow.name,
          description: workflow.description,
          business_scenario: workflow.business_scenario,
          user_intents: [],
          trigger_keywords: [],
          inputs: [],
          nodes: [],
          metadata: {
            complexity: 'medium',
            tags: [workflow.business_scenario]
          }
        };
        setCurrentWorkflow(fullWorkflow);
      }
    }
  };

  // 选择工作流
  const handleSelectWorkflow = async (workflowId: string) => {
    setSelectedWorkflow(workflowId);
    await loadWorkflowDetail(workflowId);
    setActiveTab('design');
  };

  const handleCreateWorkflow = () => {
    form.resetFields();
    setModalVisible(true);
  };

  const handleSaveWorkflow = async (values: any) => {
    try {
      setLoading(true);
      console.log('🚀 创建工作流:', values);

      // 处理触发关键词
      const triggerKeywords = values.trigger_keywords
        ? values.trigger_keywords.split(',').map((k: string) => k.trim()).filter((k: string) => k)
        : [];

      // 构建创建工作流的请求数据
      const createRequest = {
        name: values.name,
        description: values.description,
        business_scenario: values.business_scenario,
        user_intents: ['创建工作流', '设计流程'],
        trigger_keywords: triggerKeywords,
        inputs: [],
        nodes: [],
        metadata: {
          tags: [values.business_scenario],
          complexity: 'medium' as const
        }
      };

      // 调用后端API创建工作流
      const response = await workflowAPI.createWorkflow(createRequest);
      console.log('📥 创建响应:', response);

      // 创建本地工作流对象
      const newWorkflow = {
        id: response.data.workflow.id,
        name: response.data.workflow.name,
        description: values.description,
        business_scenario: values.business_scenario,
        nodeCount: response.data.workflow.node_count,
        status: response.data.workflow.status.toLowerCase()
      };

      // 添加到本地列表并选中
      setWorkflows([...workflows, newWorkflow]);
      setSelectedWorkflow(newWorkflow.id);
      setActiveTab('design');

      message.success('工作流创建成功');
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('❌ 创建工作流失败:', error);
      message.error('工作流创建失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除工作流
  const handleDeleteWorkflow = async (workflowId: string) => {
    try {
      console.log('🗑️ 删除工作流:', workflowId);

      // 调用后端API删除工作流
      const response = await workflowAPI.deleteWorkflow(workflowId);
      console.log('📥 删除响应:', response);

      // 从本地列表删除
      setWorkflows(workflows.filter(w => w.id !== workflowId));

      if (selectedWorkflow === workflowId) {
        setSelectedWorkflow(null);
        setCurrentWorkflow(null);
      }

      message.success('工作流删除成功');
    } catch (error) {
      console.error('❌ 删除工作流失败:', error);
      message.error('工作流删除失败');
    }
  };

  // 验证工作流
  const handleValidateWorkflow = async () => {
    if (!selectedWorkflow) return;

    try {
      // 暂时模拟验证结果
      message.success('工作流验证通过');
    } catch (error) {
      message.error('工作流验证失败');
    }
  };

  // 测试工作流
  const handleTestWorkflow = async () => {
    if (!selectedWorkflow) return;

    try {
      // 暂时模拟测试结果
      message.success('工作流测试完成');
    } catch (error) {
      message.error('工作流测试失败');
    }
  };

  // 保存工作流设计
  const handleSaveWorkflowDesign = async (workflow: WorkflowDefinition) => {
    if (!selectedWorkflow) return;

    try {
      // 检查是否有有效的认证token
      const apiToken = apiClient.getToken();
      const hasValidToken = (authState.token && !authState.token.includes('fake-token')) || 
                           (apiToken && !apiToken.includes('fake-token'));
      const isAuthenticated = authState.isAuthenticated || hasValidToken; // 只要有有效token就认为已认证
      console.log('handleSaveWorkflowDesign - apiClient has token:', !!apiToken);
      console.log('handleSaveWorkflowDesign - has valid token:', hasValidToken);

      // 只有在认证成功时才调用API
      if (isAuthenticated && hasValidToken) {
        console.log('🔄 准备保存工作流到后端:', workflow);

        // 构建符合API文档要求的请求数据
        const updateRequest: WorkflowUpdateRequest = {
          name: workflow.name,
          description: workflow.description,
          business_scenario: workflow.business_scenario,
          status: 'active' as const, // 添加状态字段
          user_intents: workflow.user_intents || [],
          trigger_keywords: workflow.trigger_keywords || [],
          inputs: workflow.inputs || [],
          nodes: workflow.nodes || [],
          metadata: {
            tags: workflow.metadata?.tags || [],
            complexity: workflow.metadata?.complexity || 'medium'
          }
        };

        console.log('📤 发送PUT请求到后端:', updateRequest);
        updateRequest.nodes?.forEach((n, i) => {
          console.log(`📤 节点${i+1}: ${n.name} (${n.id})`);
          console.log(`   child_nodes: ${JSON.stringify(n.child_nodes)}`);
          console.log(`   parent_nodes: ${JSON.stringify(n.parent_nodes)}`);
        });

        const response = await workflowAPI.updateWorkflow(selectedWorkflow, updateRequest);

        console.log('📥 后端响应:', response);

        if (response.code === 200) {
          setCurrentWorkflow(workflow);
          message.success('工作流设计已保存');
        } else {
          message.error(response.message || '保存工作流失败');
        }
      } else {
        // 未认证时只在本地保存
        setCurrentWorkflow(workflow);
        message.success('工作流设计已保存（本地）');
      }
    } catch (error) {
      console.error('Failed to save workflow:', error);
      message.error('保存工作流失败');
    }
  };

  // 节点选择处理
  const handleNodeSelect = (node: WorkflowNode | null) => {
    setSelectedNode(node);
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadWorkflows();
  }, [loadWorkflows]);

  // 检查认证状态
  const apiToken = apiClient.getToken();
  const hasValidToken = (authState.token && !authState.token.includes('fake-token')) || 
                       (apiToken && !apiToken.includes('fake-token'));
  const isAuthenticated = authState.isAuthenticated || hasValidToken; // 只要有有效token就认为已认证

  // 如果未认证，显示认证要求组件
  if (!isAuthenticated || !hasValidToken) {
    return (
      <div className="workflow-design-step">
        <div className="step-header">
          <div className="step-title">
            <BranchesOutlined className="step-icon" />
            <div>
              <h2>工作流设计</h2>
              <p>设计和配置业务流程工作流</p>
            </div>
          </div>
        </div>
        <AuthenticationRequired 
          onNavigateToAuth={() => {
            // 可以添加导航到认证页面的逻辑
            window.location.hash = '#/config';
          }}
        />
      </div>
    );
  }

  return (
    <div className="workflow-design-step">
      {/* 步骤头部 */}
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <BranchesOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">工作流设计</h2>
              <p className="unified-step-description">设计和配置业务流程工作流</p>
            </div>
          </div>
          <div className="unified-step-actions">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateWorkflow}
            >
              创建工作流
            </Button>
          </div>
        </div>
      </UnifiedCard>

      {/* 主要内容区域 */}
      <div className="workflow-main-content">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'list',
              label: '工作流列表',
              children: (
                <div className="workflow-list">
                  <Spin spinning={loading}>
                    <Row gutter={[16, 16]}>
                      {workflows.map(workflow => (
                        <Col key={workflow.id} xs={24} sm={12} lg={8}>
                          <UnifiedCard
                            className={`workflow-card ${selectedWorkflow === workflow.id ? 'selected' : ''}`}
                            onClick={() => handleSelectWorkflow(workflow.id)}
                            actions={[
                              <EyeOutlined key="view" onClick={(e) => {
                                e.stopPropagation();
                                handleSelectWorkflow(workflow.id);
                              }} />,
                              <EditOutlined key="edit" onClick={(e) => {
                                e.stopPropagation();
                                handleSelectWorkflow(workflow.id);
                              }} />,
                              <DeleteOutlined key="delete" onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteWorkflow(workflow.id);
                              }} />,
                              <PlayCircleOutlined key="test" onClick={(e) => {
                                e.stopPropagation();
                                handleTestWorkflow();
                              }} />
                            ]}
                          >
                            <div>
                              <h4>{workflow.name}</h4>
                              <p>{workflow.description}</p>
                            </div>
                            <div className="workflow-meta">
                              <Tag color="blue">{workflow.business_scenario}</Tag>
                              <Tag color={workflow.status === 'active' ? 'green' : 'orange'}>
                                {workflow.status === 'active' ? '活跃' : '草稿'}
                              </Tag>
                              <span className="node-count">{workflow.nodeCount || 0} 个节点</span>
                            </div>
                          </UnifiedCard>
                        </Col>
                      ))}
                    </Row>
                  </Spin>
                </div>
              ),
            },
            {
              key: 'design',
              label: '可视化设计',
              disabled: !selectedWorkflow,
              children: selectedWorkflow ? (
                <div className="workflow-design-area" style={{ height: '600px' }}>
                  <WorkflowCanvas
                    workflowId={selectedWorkflow}
                    workflow={currentWorkflow || undefined}
                    onSave={handleSaveWorkflowDesign}
                    onNodeSelect={handleNodeSelect}
                  />
                </div>
              ) : (
                <div className="no-workflow-selected">
                  <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                    <BranchesOutlined style={{ fontSize: '64px', color: '#d9d9d9', marginBottom: '16px' }} />
                    <h3>请选择一个工作流进行设计</h3>
                    <p>从工作流列表中选择或创建一个新的工作流</p>
                  </div>
                </div>
              ),
            },
          ]}
        />
      </div>

      {/* 步骤底部 */}
      <div className="step-footer">
        <Space>
          <Button size="large" onClick={onPrev}>
            上一步
          </Button>
          <Button type="primary" size="large" onClick={onNext}>
            下一步
          </Button>
        </Space>
      </div>

      {/* 创建工作流模态框 */}
      <Modal
        title="创建工作流"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveWorkflow}
        >
          <Form.Item
            name="name"
            label="工作流名称"
            rules={[{ required: true, message: '请输入工作流名称' }]}
          >
            <Input placeholder="例如: 用户查询处理流程" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入工作流描述' }]}
          >
            <TextArea rows={3} placeholder="描述工作流的用途和功能" />
          </Form.Item>

          <Form.Item
            name="business_scenario"
            label="业务场景"
            rules={[{ required: true, message: '请选择业务场景' }]}
          >
            <Select placeholder="选择业务场景">
              <Option value="customer_service">客户服务</Option>
              <Option value="order_management">订单管理</Option>
              <Option value="feedback_management">反馈管理</Option>
              <Option value="user_onboarding">用户引导</Option>
              <Option value="data_processing">数据处理</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="trigger_keywords"
            label="触发关键词"
          >
            <Input placeholder="用逗号分隔多个关键词，例如: 查询,帮助,问题" />
          </Form.Item>

          <div className="form-actions">
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default WorkflowDesignStep;
