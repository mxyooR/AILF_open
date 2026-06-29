/**
 * 场景配置步骤组件
 */

import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Row,
  Col,
  Space,
  Typography,
  Alert,
  Tag,
  Tabs,
  message
} from 'antd';
import { UnifiedCard } from '../common';
import {
  ShoppingCartOutlined,
  MedicineBoxOutlined,
  CoffeeOutlined,
  BookOutlined,
  CarOutlined,
  BankOutlined,
  SettingOutlined,
  PlusOutlined,
  AppstoreOutlined,
  EditOutlined,
  BgColorsOutlined
} from '@ant-design/icons';
import { useScenarioConfig } from '../../../hooks/developer/useScenarioConfig';
import { appConfigAPI, type AppConfig } from '../../../services/appConfig';
import type { ScenarioFormData, ScenarioType } from '../../../types/developer/scenario';
import { SCENARIO_TYPES } from '../../../types/developer/scenario';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ScenarioConfigStepProps {
  onSuccess: () => void;
  onBack: () => void;
}

const ScenarioConfigStep: React.FC<ScenarioConfigStepProps> = ({ onSuccess, onBack }) => {
  const [form] = Form.useForm();
  const [appConfigForm] = Form.useForm();
  const { scenarioState, saveScenario, clearError } = useScenarioConfig();
  const [selectedType, setSelectedType] = useState<ScenarioType>('ecommerce');
  const [customUsers, setCustomUsers] = useState<string[]>([]);
  const [customFeatures, setCustomFeatures] = useState<string[]>([]);
  const [customExampleInstructions, setCustomExampleInstructions] = useState<string[]>([]);
  const [newUser, setNewUser] = useState('');
  const [newFeature, setNewFeature] = useState('');
  const [newExampleInstruction, setNewExampleInstruction] = useState('');
  const [activeTab, setActiveTab] = useState('scenario');
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null);
  const [appConfigLoading, setAppConfigLoading] = useState(false);

  // 图标映射
  const iconMap = {
    'shopping-cart': <ShoppingCartOutlined />,
    'medicine-box': <MedicineBoxOutlined />,
    'coffee': <CoffeeOutlined />,
    'book': <BookOutlined />,
    'car': <CarOutlined />,
    'bank': <BankOutlined />,
    'setting': <SettingOutlined />,
  };

  // 初始化表单数据
  useEffect(() => {
    if (scenarioState.currentScenario) {
      const scenario = scenarioState.currentScenario;
      form.setFieldsValue({
        name: scenario.name,
        type: scenario.type,
        description: scenario.description,
        business_domain: scenario.config.business_domain,
      });
      setSelectedType(scenario.type);
      setCustomUsers(scenario.config.target_users);
      setCustomFeatures(scenario.config.key_features);
      setCustomExampleInstructions(scenario.config.example_instructions || []);
    }
  }, [scenarioState.currentScenario, form]);

  // 加载应用配置
  useEffect(() => {
    const loadAppConfig = async () => {
      try {
        const config = await appConfigAPI.getAppConfig();
        setAppConfig(config);
        appConfigForm.setFieldsValue({
          ...config,
          backgroundStyle: config.backgroundStyle || 'mesh',
        });
      } catch (error) {
        console.error('加载应用配置失败:', error);
      }
    };
    loadAppConfig();
  }, [appConfigForm]);

  const handleSubmit = async (values: any) => {
    clearError();
    
    const formData: ScenarioFormData = {
      name: values.name,
      type: selectedType,
      description: values.description || '',
      business_domain: values.business_domain,
      target_users: customUsers,
      key_features: customFeatures,
      example_instructions: customExampleInstructions,
      custom_settings: {},
    };

    const result = await saveScenario(formData);
    
    if (result.success) {
      onSuccess();
    }
  };

  const handleTypeChange = (type: ScenarioType) => {
    setSelectedType(type);
    const selectedOption = SCENARIO_TYPES.find(t => t.value === type);
    if (selectedOption) {
      // 预设一些默认值
      setCustomUsers([]);
      setCustomFeatures([]);
      setCustomExampleInstructions([]);
      form.setFieldsValue({
        business_domain: selectedOption.label,
      });
    }
  };

  const addUser = () => {
    if (newUser.trim() && !customUsers.includes(newUser.trim())) {
      setCustomUsers([...customUsers, newUser.trim()]);
      setNewUser('');
    }
  };

  const removeUser = (user: string) => {
    setCustomUsers(customUsers.filter(u => u !== user));
  };

  const addFeature = () => {
    if (newFeature.trim() && !customFeatures.includes(newFeature.trim())) {
      setCustomFeatures([...customFeatures, newFeature.trim()]);
      setNewFeature('');
    }
  };

  const removeFeature = (feature: string) => {
    setCustomFeatures(customFeatures.filter(f => f !== feature));
  };

  const addExampleInstruction = () => {
    const value = newExampleInstruction.trim();
    if (value && !customExampleInstructions.includes(value)) {
      setCustomExampleInstructions([...customExampleInstructions, value]);
      setNewExampleInstruction('');
    }
  };

  const removeExampleInstruction = (instruction: string) => {
    setCustomExampleInstructions(customExampleInstructions.filter(item => item !== instruction));
  };

  // 处理应用配置提交
  const handleAppConfigSubmit = async (values: any) => {
    setAppConfigLoading(true);
    try {
      const updatedConfig = await appConfigAPI.updateAppConfig({
        title: values.title,
        subtitle: values.subtitle,
        backgroundStyle: values.backgroundStyle,
      });
      setAppConfig(updatedConfig);
      message.success('应用配置更新成功');
    } catch (error) {
      message.error('应用配置更新失败');
    } finally {
      setAppConfigLoading(false);
    }
  };

  const selectedTypeOption = SCENARIO_TYPES.find(t => t.value === selectedType);

  const tabItems = [
    {
      key: 'scenario',
      label: (
        <span>
          <SettingOutlined />
          场景配置
        </span>
      ),
      children: renderScenarioConfig(),
    },
    {
      key: 'app',
      label: (
        <span>
          <AppstoreOutlined />
          应用配置
        </span>
      ),
      children: renderAppConfig(),
    },
  ];

  function renderScenarioConfig() {
    return (
      <>
        {scenarioState.error && (
          <Alert
            message="配置失败"
            description={scenarioState.error}
            type="error"
            showIcon
            closable
            onClose={clearError}
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
        >
        <Row gutter={24}>
          <Col span={24}>
            <UnifiedCard title="基本信息" style={{ marginBottom: 24 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="name"
                    label="场景名称"
                    rules={[
                      { required: true, message: '请输入场景名称' },
                      { min: 2, message: '场景名称至少2个字符' },
                    ]}
                  >
                    <Input 
                      placeholder="例如：电商管理系统"
                      size="large"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="business_domain"
                    label="业务领域"
                    rules={[{ required: true, message: '请输入业务领域' }]}
                  >
                    <Input 
                      placeholder="例如：电子商务"
                      size="large"
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item
                name="description"
                label="场景描述"
              >
                <TextArea 
                  placeholder="描述您的业务场景..."
                  rows={3}
                  size="large"
                />
              </Form.Item>
            </UnifiedCard>
          </Col>
        </Row>

        <Row gutter={24}>
          <Col span={24}>
            <UnifiedCard title="场景类型" style={{ marginBottom: 24 }}>
              <Row gutter={16}>
                {SCENARIO_TYPES.map(type => (
                  <Col span={8} key={type.value} style={{ marginBottom: 16 }}>
                    <UnifiedCard
                      hoverable
                      className={selectedType === type.value ? 'selected-type' : ''}
                      onClick={() => handleTypeChange(type.value)}
                      style={{
                        border: selectedType === type.value ? '2px solid #007aff' : '1px solid rgba(0, 0, 0, 0.04)',
                        backgroundColor: selectedType === type.value ? 'rgba(0, 122, 255, 0.05)' : 'white',
                        borderRadius: '16px'
                      }}
                    >
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 32, marginBottom: 8, color: '#007aff' }}>
                          {iconMap[type.icon as keyof typeof iconMap]}
                        </div>
                        <Title level={5} style={{ marginBottom: 4 }}>
                          {type.label}
                        </Title>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {type.description}
                        </Text>
                      </div>
                    </UnifiedCard>
                  </Col>
                ))}
              </Row>
              
              {selectedTypeOption && (
                <div style={{ marginTop: 16, padding: 16, backgroundColor: 'rgba(0, 122, 255, 0.02)', borderRadius: 12, border: '1px solid rgba(0, 122, 255, 0.1)' }}>
                  <Text strong>推荐功能：</Text>
                  <div style={{ marginTop: 8 }}>
                    {selectedTypeOption.features.map(feature => (
                      <Tag key={feature} color="blue" style={{ margin: '2px 4px' }}>
                        {feature}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </UnifiedCard>
          </Col>
        </Row>

        <Row gutter={24}>
          <Col span={12}>
            <UnifiedCard title="目标用户" style={{ marginBottom: 24 }}>
              <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
                <Input
                  placeholder="添加用户角色"
                  value={newUser}
                  onChange={(e) => setNewUser(e.target.value)}
                  onPressEnter={addUser}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={addUser}>
                  添加
                </Button>
              </Space.Compact>
              
              <div>
                {customUsers.map(user => (
                  <Tag
                    key={user}
                    closable
                    onClose={() => removeUser(user)}
                    style={{ margin: '4px 4px' }}
                  >
                    {user}
                  </Tag>
                ))}
              </div>
            </UnifiedCard>
          </Col>
          
          <Col span={12}>
            <UnifiedCard title="关键功能" style={{ marginBottom: 24 }}>
              <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
                <Input
                  placeholder="添加功能模块"
                  value={newFeature}
                  onChange={(e) => setNewFeature(e.target.value)}
                  onPressEnter={addFeature}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={addFeature}>
                  添加
                </Button>
              </Space.Compact>
              
              <div>
                {customFeatures.map(feature => (
                  <Tag
                    key={feature}
                    closable
                    onClose={() => removeFeature(feature)}
                    style={{ margin: '4px 4px' }}
                  >
                    {feature}
                  </Tag>
                ))}
              </div>
            </UnifiedCard>
          </Col>
        </Row>

        <Row gutter={24}>
          <Col span={24}>
            <UnifiedCard title="示例指令" style={{ marginBottom: 24 }}>
              <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
                <Input
                  placeholder="例如：查看今日订单"
                  value={newExampleInstruction}
                  onChange={(e) => setNewExampleInstruction(e.target.value)}
                  onPressEnter={addExampleInstruction}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={addExampleInstruction}>
                  添加
                </Button>
              </Space.Compact>
              
              <div>
                {customExampleInstructions.map(instruction => (
                  <Tag
                    key={instruction}
                    closable
                    onClose={() => removeExampleInstruction(instruction)}
                    style={{ margin: '4px 4px' }}
                  >
                    {instruction}
                  </Tag>
                ))}
              </div>
            </UnifiedCard>
          </Col>
        </Row>

        <div style={{ textAlign: 'center', marginTop: 32 }}>
          <Space size="large">
            <Button
              type="primary"
              size="large"
              htmlType="submit"
              loading={scenarioState.isLoading}
            >
              {scenarioState.isLoading ? '保存中...' : '保存场景配置'}
            </Button>
          </Space>
        </div>
      </Form>
      </>
    );
  }

  function renderAppConfig() {
    return (
      <>
        <Form
          form={appConfigForm}
          layout="vertical"
          onFinish={handleAppConfigSubmit}
          autoComplete="off"
        >
          <UnifiedCard title="应用基本信息" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="title"
                  label="应用标题"
                  rules={[
                    { required: true, message: '请输入应用标题' },
                    { min: 1, max: 100, message: '标题长度为1-100个字符' },
                  ]}
                >
                  <Input
                    placeholder="例如：AILF"
                    size="large"
                    prefix={<AppstoreOutlined />}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="subtitle"
                  label="应用副标题"
                  rules={[
                    { required: true, message: '请输入应用副标题' },
                    { min: 1, max: 200, message: '副标题长度为1-200个字符' },
                  ]}
                >
                  <Input
                    placeholder="例如：AI前端生成系统"
                    size="large"
                    prefix={<EditOutlined />}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Alert
              message="配置说明"
              description="应用标题和副标题将显示在系统的顶部导航栏中，修改后立即生效。"
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </UnifiedCard>

          <UnifiedCard title="主页背景样式" style={{ marginBottom: 24 }}>
            <Form.Item
              name="backgroundStyle"
              label="背景效果"
              initialValue="mesh"
            >
              <Select
                size="large"
                style={{ width: '100%' }}
                options={[
                  {
                    value: 'mesh',
                    label: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                          width: 40,
                          height: 24,
                          borderRadius: 6,
                          background: 'linear-gradient(135deg, #0a0a14 0%, #af52de 30%, #5ac8fa 60%, #30d158 100%)',
                        }} />
                        <span>渐变光晕 (Mesh Gradient)</span>
                      </div>
                    ),
                  },
                  {
                    value: 'ribbon',
                    label: (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                          width: 40,
                          height: 24,
                          borderRadius: 6,
                          background: 'linear-gradient(135deg, #000 0%, #8b5cf6 40%, #3b82f6 70%, #000 100%)',
                        }} />
                        <span>蓝紫丝带 (Apple Ribbon)</span>
                      </div>
                    ),
                  },
                ]}
              />
            </Form.Item>
            <Alert
              message="背景样式说明"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li><strong>渐变光晕</strong>：多彩渐变流动效果，适合清新明亮风格</li>
                  <li><strong>蓝紫丝带</strong>：黑底蓝紫色丝带飘动效果，适合科技酷炫风格</li>
                </ul>
              }
              type="info"
              showIcon
              icon={<BgColorsOutlined />}
              style={{ marginTop: 8 }}
            />
          </UnifiedCard>

          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <Space size="large">
              <Button
                type="primary"
                size="large"
                htmlType="submit"
                loading={appConfigLoading}
                icon={<EditOutlined />}
              >
                {appConfigLoading ? '更新中...' : '更新应用配置'}
              </Button>
            </Space>
          </div>
        </Form>
      </>
    );
  }

  return (
    <div className="scenario-config-step">
      {/* 步骤头部 */}
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <SettingOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">场景配置</h2>
              <p className="unified-step-description">配置您的业务场景和应用基本信息</p>
            </div>
          </div>
        </div>
      </UnifiedCard>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
        style={{ marginTop: 24 }}
      />

      <div style={{ textAlign: 'center', marginTop: 32 }}>
        <Space size="large">
          <Button size="large" onClick={onBack}>
            上一步
          </Button>
          <Button
            type="primary"
            size="large"
            onClick={onSuccess}
            disabled={!scenarioState.currentScenario}
          >
            下一步
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default ScenarioConfigStep;
