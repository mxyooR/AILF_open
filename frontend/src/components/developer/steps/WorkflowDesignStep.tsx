/**
 * 工作流设计步骤组件 - Apple风格设计
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Spin,
  Alert,
  Empty
} from 'antd';
import { UnifiedCard } from '../common';
import {
  BranchesOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
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

interface WorkflowCard {
  id: string;
  name: string;
  description: string;
  business_scenario: string;
  nodeCount: number;
  status: string;
}

const WorkflowDesignStep: React.FC<WorkflowDesignStepProps> = ({ onNext, onPrev }) => {
  const { authState } = useDeveloperAuth();
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [workflows, setWorkflows] = useState<WorkflowCard[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowDefinition | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('list');
  const [form] = Form.useForm();
  const [loadError, setLoadError] = useState('');
  const [detailError, setDetailError] = useState('');
  const [detailLoading, setDetailLoading] = useState(false);
  const selectedIdRef = useRef<string | null>(null);
  const listVersion = useRef(0);
  const detailVersion = useRef(0);
  // 使用正式客户端的开发者身份，生产环境没有调试用的 window.apiClient。
  const isAuthenticated = Boolean((authState.isAuthenticated && authState.token) || apiClient.getDeveloperToken());


  // 列表失败显示可重试错误，不能把虚构示例当成已保存的业务配置。
  const loadWorkflows = useCallback(async () => {
    const version = ++listVersion.current;
    if (!isAuthenticated) { setWorkflows([]); return; }
    setLoading(true);
    setLoadError('');
    try {
      const response = await workflowAPI.getWorkflowsList({ page: 1, limit: 100 });
      if (version !== listVersion.current) return;
      setWorkflows(response.data.workflows.map(workflow => ({
        ...workflow, nodeCount: workflow.node_count, status: workflow.status.toLowerCase()
      })));
    } catch (error) {
      if (version === listVersion.current) {
        setWorkflows([]);
        setLoadError(error instanceof Error ? error.message : '加载工作流列表失败');
      }
    } finally {
      if (version === listVersion.current) setLoading(false);
    }
  }, [isAuthenticated]);

  const handleSelectWorkflow = async (workflowId: string) => {
    const version = ++detailVersion.current;
    selectedIdRef.current = workflowId;
    setSelectedWorkflow(workflowId);
    setCurrentWorkflow(null);
    setDetailError('');
    setDetailLoading(true);
    setActiveTab('design');
    try {
      const response = await workflowAPI.getWorkflowDetail(workflowId);
      // 连续点选时仅接受最后一次请求，防止把 A 的节点保存到 B。
      if (version !== detailVersion.current || selectedIdRef.current !== workflowId) return;
      setCurrentWorkflow(response.data.workflow);
    } catch (error) {
      if (version === detailVersion.current) setDetailError(error instanceof Error ? error.message : '加载工作流详情失败');
    } finally {
      if (version === detailVersion.current) setDetailLoading(false);
    }
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
      setWorkflows(previous => [...previous, newWorkflow]);
      await handleSelectWorkflow(newWorkflow.id);

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
      setWorkflows(previous => previous.filter(w => w.id !== workflowId));

      if (selectedIdRef.current === workflowId) {
        detailVersion.current += 1;
        selectedIdRef.current = null;
        setSelectedWorkflow(null);
        setCurrentWorkflow(null);
      }

      message.success('工作流删除成功');
    } catch (error) {
      console.error('❌ 删除工作流失败:', error);
      message.error('工作流删除失败');
    }
  };

  // 保存设计保留草稿/停用状态；启用由独立按钮触发并接受后端完整校验。
  const handleSaveWorkflowDesign = async (workflow: WorkflowDefinition) => {
    const id = workflow.id;
    if (!isAuthenticated || !id || id !== selectedIdRef.current) throw new Error('请重新选择工作流');
    const updateRequest: WorkflowUpdateRequest = {
      name: workflow.name, description: workflow.description,
      business_scenario: workflow.business_scenario,
      user_intents: workflow.user_intents || [], trigger_keywords: workflow.trigger_keywords || [],
      inputs: workflow.inputs || [], nodes: workflow.nodes || [],
      metadata: { tags: workflow.metadata?.tags || [], complexity: workflow.metadata?.complexity || 'medium' }
    };
    const response = await workflowAPI.updateWorkflow(id, updateRequest);
    if (selectedIdRef.current !== id) return;
    const saved = response.data.workflow;
    setCurrentWorkflow(saved);
    setWorkflows(previous => previous.map(item => item.id === id
      ? { ...item, name: saved.name, description: saved.description, nodeCount: saved.nodes.length } : item));
    message.success('工作流设计已保存');
  };

  const handleToggleStatus = async () => {
    const id = selectedIdRef.current;
    const current = workflows.find(item => item.id === id);
    if (!id || !current || !currentWorkflow) return;
    const status = current.status === 'active' ? 'inactive' : 'active';
    setLoading(true);
    try {
      await workflowAPI.updateWorkflow(id, { status });
      setWorkflows(previous => previous.map(item => item.id === id ? { ...item, status } : item));
      message.success(status === 'active' ? '已保存的工作流已启用' : '工作流已停用');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '工作流状态更新失败');
    } finally { setLoading(false); }
  };

  // 节点选择处理
  const handleNodeSelect = (node: WorkflowNode | null) => {
    setSelectedNode(node);
  };

  // 组件挂载时加载数据
  useEffect(() => {
    void loadWorkflows();
    return () => { listVersion.current += 1; detailVersion.current += 1; };
  }, [loadWorkflows]);

  // 如果未认证，显示认证要求组件
  if (!isAuthenticated) {
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
            {currentWorkflow && <Button loading={loading} onClick={handleToggleStatus}>
              {workflows.find(item => item.id === selectedWorkflow)?.status === 'active' ? '停用工作流' : '启用已保存工作流'}
            </Button>}
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
                  {loadError && <Alert type="error" message={loadError} action={<Button onClick={loadWorkflows}>重试</Button>} />}
                  {!loading && !loadError && workflows.length === 0 && <Empty description="暂无工作流，请创建工作流" />}
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
                                {workflow.status === 'active' ? '活跃' : workflow.status === 'inactive' ? '停用' : '草稿'}
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
                  {detailLoading ? <Spin tip="正在加载工作流..." /> : detailError ? (
                    <Alert type="error" message={detailError} action={<Button onClick={() => handleSelectWorkflow(selectedWorkflow)}>重试</Button>} />
                  ) : currentWorkflow?.id === selectedWorkflow ? (
                    <WorkflowCanvas
                      key={selectedWorkflow}
                      workflowId={selectedWorkflow}
                      workflow={currentWorkflow}
                      onSave={handleSaveWorkflowDesign}
                      onNodeSelect={handleNodeSelect}
                    />
                  ) : null}
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
              <Button type="primary" htmlType="submit" loading={loading}>
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
