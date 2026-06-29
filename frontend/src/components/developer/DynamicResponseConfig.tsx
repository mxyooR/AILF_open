/**
 * 动态响应配置组件 - 可视化配置复杂的动态响应逻辑
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Button,
  Space,
  Modal,
  Select,
  Input,
  InputNumber,
  Switch,
  Row,
  Col,
  Alert,
  Divider,
  Tag,
  Tooltip,
  message,
  Typography,
  List,
  Badge
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  CodeOutlined,
  BulbOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;
const { Text } = Typography;

interface ResponseRule {
  id: string;
  name: string;
  priority: number;
  conditions: ResponseCondition[];
  response_template: ResponseTemplate;
  enabled: boolean;
}

interface ResponseCondition {
  type: 'parameter' | 'header' | 'user_role' | 'time' | 'random' | 'data_count';
  field?: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'in' | 'not_in' | 'contains' | 'exists' | 'not_exists';
  value: any;
  logic?: 'and' | 'or';
}

interface ResponseTemplate {
  status_code: number;
  headers: { [key: string]: string };
  body_template: any;
  transformations?: any[];
}

interface DynamicResponseConfigProps {
  value?: any;
  onChange?: (value: any) => void;
  disabled?: boolean;
}

// 默认条件类型
const CONDITION_TYPES = [
  { value: 'parameter', label: '参数条件', description: '基于请求参数的条件' },
  { value: 'header', label: '请求头条件', description: '基于HTTP头部的条件' },
  { value: 'user_role', label: '用户角色', description: '基于用户角色的条件' },
  { value: 'time', label: '时间条件', description: '基于时间的条件' },
  { value: 'random', label: '随机条件', description: '基于随机数的条件' },
  { value: 'data_count', label: '数据数量', description: '基于数据数量的条件' }
];

// 默认操作符选项
const OPERATORS = [
  { value: 'eq', label: '等于 (=)' },
  { value: 'ne', label: '不等于 (≠)' },
  { value: 'gt', label: '大于 (>)' },
  { value: 'gte', label: '大于等于 (≥)' },
  { value: 'lt', label: '小于 (<)' },
  { value: 'lte', label: '小于等于 (≤)' },
  { value: 'between', label: '区间 (between)' },
  { value: 'in', label: '包含在' },
  { value: 'not_in', label: '不包含在' },
  { value: 'contains', label: '包含' },
  { value: 'exists', label: '存在' },
  { value: 'not_exists', label: '不存在' }
];

const DynamicResponseConfig: React.FC<DynamicResponseConfigProps> = ({
  value,
  onChange,
  disabled = false
}) => {
  const [rules, setRules] = useState<ResponseRule[]>([]);
  const [editingRule, setEditingRule] = useState<ResponseRule | null>(null);
  const [ruleModalVisible, setRuleModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewData, setPreviewData] = useState('');
  const [loading, setLoading] = useState(false);

  const [form] = Form.useForm();

  useEffect(() => {
    if (value && value.dynamic_rules) {
      setRules(value.dynamic_rules);
    }
  }, [value]);

  const handleRulesChange = (newRules: ResponseRule[]) => {
    setRules(newRules);
    const config = {
      ...value,
      dynamic_rules: newRules
    };
    onChange?.(config);
  };

  const addRule = () => {
    setEditingRule(null);
    form.resetFields();
    setRuleModalVisible(true);
  };

  const editRule = (rule: ResponseRule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      ...rule,
      conditions: (rule.conditions || []).map((condition) => ({
        ...condition,
        value: Array.isArray(condition.value) ? condition.value.join(',') : condition.value
      })),
      response_template: {
        ...rule.response_template,
        body_template: typeof rule.response_template.body_template === 'string' 
          ? rule.response_template.body_template 
          : JSON.stringify(rule.response_template.body_template, null, 2)
      }
    });
    setRuleModalVisible(true);
  };

  const deleteRule = (ruleId: string) => {
    const newRules = rules.filter(r => r.id !== ruleId);
    handleRulesChange(newRules);
    message.success('响应规则已删除');
  };

  const saveRule = async () => {
    try {
      const values = await form.validateFields();
      
      // 处理响应模板
      let bodyTemplate = values.response_template.body_template;
      try {
        bodyTemplate = typeof bodyTemplate === 'string' ? JSON.parse(bodyTemplate) : bodyTemplate;
      } catch (e) {
        // 如果解析失败，保持字符串格式
      }

      const normalizedConditions = (values.conditions || []).map((condition: ResponseCondition) => {
        if (condition.operator === 'in' || condition.operator === 'not_in' || condition.operator === 'between') {
          if (typeof condition.value === 'string') {
            const parts = condition.value
              .split(',')
              .map((item: string) => item.trim())
              .filter((item: string) => item.length > 0);
            if (condition.operator === 'between' && parts.length >= 2) {
              const [lower, upper] = parts;
              return {
                ...condition,
                value: [lower, upper].map((v) => {
                  const num = Number(v);
                  return Number.isNaN(num) ? v : num;
                })
              };
            }
            return {
              ...condition,
              value: parts
            };
          }
        }
        return condition;
      });

      const rule: ResponseRule = {
        id: editingRule?.id || Date.now().toString(),
        ...values,
        conditions: normalizedConditions,
        response_template: {
          ...values.response_template,
          body_template: bodyTemplate
        },
        enabled: values.enabled !== false
      };

      let newRules;
      if (editingRule) {
        newRules = rules.map(r => r.id === editingRule.id ? rule : r);
      } else {
        newRules = [...rules, rule];
      }

      handleRulesChange(newRules);
      setRuleModalVisible(false);
      message.success(`响应规则已${editingRule ? '更新' : '创建'}`);
    } catch (error) {
      message.error('保存失败，请检查输入');
    }
  };

  const previewConfig = () => {
    const config = { dynamic_rules: rules };
    setPreviewData(JSON.stringify(config, null, 2));
    setPreviewModalVisible(true);
  };

  // 快速添加预设规则
  const addPresetRule = (preset: string) => {
    const presetRules: { [key: string]: Partial<ResponseRule> } = {
      admin_rule: {
        name: '管理员专用响应',
        priority: 90,
        conditions: [{
          type: 'user_role',
          operator: 'in',
          value: ['admin', 'super_admin'],
          logic: 'and'
        }],
        response_template: {
          status_code: 200,
          headers: {},
          body_template: {
            code: 200,
            message: '管理员专用响应',
            data: '{{original_data}}',
            meta: {
              user_role: '{{user_role}}',
              access_level: 'full',
              timestamp: '{{timestamp}}'
            }
          }
        },
        enabled: true
      },
      guest_rule: {
        name: '访客限制访问',
        priority: 10,
        conditions: [{
          type: 'user_role',
          operator: 'in',
          value: ['guest', 'anonymous'],
          logic: 'or'
        }],
        response_template: {
          status_code: 200,
          headers: {},
          body_template: {
            code: 200,
            message: '访客模式 - 部分数据可见',
            data: '{{original_data}}',
            access_level: 'limited',
            login_required: true
          }
        },
        enabled: true
      }
    };

    const rule = presetRules[preset];
    if (rule) {
      const newRule: ResponseRule = {
        id: Date.now().toString(),
        ...rule
      } as ResponseRule;
      
      handleRulesChange([...rules, newRule]);
      message.success('预设规则已添加');
    }
  };

  return (
    <div className="dynamic-response-config">
      <Card
        title={
          <Space>
            <SettingOutlined />
            <span>动态响应配置</span>
            <Badge count={rules.length} showZero color="blue" />
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<CodeOutlined />}
              onClick={previewConfig}
              disabled={disabled}
            >
              预览配置
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={addRule}
              disabled={disabled}
            >
              添加响应规则
            </Button>
          </Space>
        }
      >
        <Alert
          message="动态响应说明"
          description="通过配置条件和响应模板，可以根据不同的请求参数、用户角色、时间等条件返回不同的响应内容。规则按优先级从高到低执行，第一个匹配的规则将被应用。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {/* 快速预设按钮 */}
        <div style={{ marginBottom: 16 }}>
          <Text strong>快速预设: </Text>
          <Space>
            <Button size="small" onClick={() => addPresetRule('admin_rule')} disabled={disabled}>
              管理员规则
            </Button>
            <Button size="small" onClick={() => addPresetRule('guest_rule')} disabled={disabled}>
              访客规则
            </Button>
          </Space>
        </div>

        {rules.length === 0 ? (
          <Card size="small">
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <BulbOutlined style={{ fontSize: 48, color: '#ccc' }} />
              <div style={{ marginTop: 16, color: '#666' }}>
                还没有配置响应规则，点击上方按钮或使用快速预设添加规则
              </div>
            </div>
          </Card>
        ) : (
          <List
            dataSource={rules.sort((a, b) => b.priority - a.priority)}
            renderItem={(rule) => (
              <List.Item
                key={rule.id}
                actions={[
                  <Button
                    icon={<EditOutlined />}
                    onClick={() => editRule(rule)}
                    disabled={disabled}
                  >
                    编辑
                  </Button>,
                  <Button
                    icon={<DeleteOutlined />}
                    danger
                    onClick={() => deleteRule(rule.id)}
                    disabled={disabled}
                  >
                    删除
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span>{rule.name}</span>
                      <Tag color={rule.enabled ? 'green' : 'red'}>
                        {rule.enabled ? '启用' : '禁用'}
                      </Tag>
                      <Tag color="blue">优先级: {rule.priority}</Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text type="secondary">
                        条件: {rule.conditions?.length || 0} 个 | 
                        状态码: {rule.response_template?.status_code || 200}
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      {/* 规则编辑模态框 */}
      <Modal
        title={editingRule ? '编辑响应规则' : '新建响应规则'}
        open={ruleModalVisible}
        onOk={saveRule}
        onCancel={() => setRuleModalVisible(false)}
        width={800}
        maskClosable={false}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            enabled: true,
            priority: 50,
            conditions: [],
            response_template: {
              status_code: 200,
              headers: {},
              body_template: JSON.stringify({
                code: 200,
                message: '成功',
                data: '{{original_data}}',
                timestamp: '{{timestamp}}'
              }, null, 2)
            }
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="规则名称"
                rules={[{ required: true, message: '请输入规则名称' }]}
              >
                <Input placeholder="请输入规则名称" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="priority"
                label="优先级"
                rules={[{ required: true, message: '请输入优先级' }]}
              >
                <InputNumber
                  min={0}
                  max={100}
                  placeholder="0-100"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="enabled" label="启用状态" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>触发条件</Divider>
          <Form.List name="conditions">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Card key={field.key} size="small" style={{ marginBottom: 8 }}>
                    <Row gutter={8}>
                      <Col span={6}>
                        <Form.Item
                          {...field}
                          name={[field.name, 'type']}
                          label="条件类型"
                          rules={[{ required: true }]}
                        >
                          <Select placeholder="条件类型">
                            {CONDITION_TYPES.map((type: any) => (
                              <Option key={type.value} value={type.value}>
                                <Tooltip title={type.description}>
                                  {type.label}
                                </Tooltip>
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={4}>
                        <Form.Item
                          {...field}
                          name={[field.name, 'field']}
                          label="字段名"
                        >
                          <Input placeholder="字段名" />
                        </Form.Item>
                      </Col>
                      <Col span={4}>
                        <Form.Item
                          {...field}
                          name={[field.name, 'operator']}
                          label="操作符"
                          rules={[{ required: true }]}
                        >
                          <Select placeholder="操作符">
                            {OPERATORS.map((op: any) => (
                              <Option key={op.value} value={op.value}>
                                {op.label}
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item
                        {...field}
                        name={[field.name, 'value']}
                        label="比较值"
                      >
                          <Input placeholder="值，多个值用逗号分隔（between: min,max）" />
                      </Form.Item>
                      </Col>
                      <Col span={4}>
                        <Form.Item label=" ">
                          <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => remove(field.name)}
                          >
                            删除
                          </Button>
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                ))}
                <Button
                  type="dashed"
                  onClick={() => add()}
                  block
                  icon={<PlusOutlined />}
                >
                  添加条件
                </Button>
              </>
            )}
          </Form.List>

          <Divider>响应模板</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name={['response_template', 'status_code']}
                label="HTTP状态码"
              >
                <InputNumber min={200} max={599} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name={['response_template', 'body_template']}
            label={
              <Space>
                <span>响应体模板</span>
                <Tooltip title="支持变量: {{original_data}}, {{user_role}}, {{user_id}}, {{timestamp}}, {{data_count}}, {{api_id}}">
                  <InfoCircleOutlined />
                </Tooltip>
              </Space>
            }
            rules={[{ required: true, message: '请输入响应体模板' }]}
          >
            <TextArea 
              rows={8} 
              placeholder='响应体JSON模板，支持变量替换，例如:
{
  "code": 200,
  "message": "成功",
  "data": "{{original_data}}",
  "user_role": "{{user_role}}",
  "timestamp": "{{timestamp}}"
}'
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 预览模态框 */}
      <Modal
        title="配置预览"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <pre style={{ 
          background: '#f5f5f5', 
          padding: '16px', 
          borderRadius: '4px',
          maxHeight: '500px',
          overflow: 'auto'
        }}>
          {previewData}
        </pre>
      </Modal>
    </div>
  );
};

export default DynamicResponseConfig;
