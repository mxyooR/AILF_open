/**
 * 权限配置组件 - 用于API路由的权限管理
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Switch,
  Select,
  InputNumber,
  Button,
  Space,
  Row,
  Col,
  Tag,
  Input,
  message,
  Divider,
  Alert,
  Tooltip,
  Badge
} from 'antd';
import {
  SafetyOutlined,
  UserOutlined,
  KeyOutlined,
  SettingOutlined,
  PlusOutlined,
  MinusCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { RoutePermissionConfig, RoutePermission } from '../../../types/developer/route';
import { RoleAPI, Role } from '../../../services/developer/roleAPI';

const { Option } = Select;
const { TextArea } = Input;

interface PermissionConfigProps {
  value?: RoutePermissionConfig;
  onChange?: (config: RoutePermissionConfig) => void;
  disabled?: boolean;
  showAdvanced?: boolean;
}

const PermissionConfigComponent: React.FC<PermissionConfigProps> = ({
  value = {},
  onChange,
  disabled = false,
  showAdvanced = true
}) => {
  const [form] = Form.useForm();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 权限预设选项
  const resourceOptions = [
    { value: 'users', label: '用户管理' },
    { value: 'roles', label: '角色管理' },
    { value: 'permissions', label: '权限管理' },
    { value: 'products', label: '商品管理' },
    { value: 'orders', label: '订单管理' },
    { value: 'customers', label: '客户管理' },
    { value: 'reports', label: '报表管理' },
    { value: 'analytics', label: '数据分析' },
    { value: 'settings', label: '系统设置' },
    { value: 'api_routes', label: 'API路由管理' },
    { value: 'workflows', label: '工作流管理' },
    { value: 'templates', label: '模板管理' },
    { value: 'entities', label: '实体管理' },
    { value: 'forms', label: '表单管理' }
  ];

  const actionOptions = [
    { value: 'read', label: '查看' },
    { value: 'create', label: '创建' },
    { value: 'update', label: '更新' },
    { value: 'delete', label: '删除' },
    { value: 'manage', label: '管理' },
    { value: 'access', label: '访问' },
    { value: 'export', label: '导出' },
    { value: 'import', label: '导入' },
    { value: 'approve', label: '审批' },
    { value: 'execute', label: '执行' }
  ];

  // 加载角色列表
  useEffect(() => {
    loadRoles();
  }, []);

  // 表单值变化时更新父组件
  useEffect(() => {
    const handleFormChange = () => {
      const formValues = form.getFieldsValue();
      const config: RoutePermissionConfig = {
        required_permissions: formValues.required_permissions || [],
        required_roles: formValues.required_roles || [],
        min_role_level: formValues.min_role_level,
        allow_developer: formValues.allow_developer ?? true
      };
      onChange?.(config);
    };

    // 监听表单变化
    const timer = setTimeout(handleFormChange, 100);
    return () => clearTimeout(timer);
  }, [form, onChange]);

  // 设置表单初始值
  useEffect(() => {
    if (value) {
      form.setFieldsValue({
        required_permissions: value.required_permissions || [],
        required_roles: value.required_roles || [],
        min_role_level: value.min_role_level,
        allow_developer: value.allow_developer ?? true
      });
    }
  }, [value, form]);

  const loadRoles = async () => {
    setLoading(true);
    try {
      const response = await RoleAPI.getRoles({ page: 1, limit: 100 });
      setRoles(response.roles || []);
    } catch (error) {
      message.error('加载角色列表失败');
      console.error('Load roles error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFormValuesChange = () => {
    // 表单值变化时触发onChange
    setTimeout(() => {
      const formValues = form.getFieldsValue();
      const config: RoutePermissionConfig = {
        required_permissions: formValues.required_permissions || [],
        required_roles: formValues.required_roles || [],
        min_role_level: formValues.min_role_level,
        allow_developer: formValues.allow_developer ?? true
      };
      onChange?.(config);
    }, 0);
  };

  return (
    <Card 
      title={
        <Space>
          <SafetyOutlined />
          <span>权限配置</span>
          <Badge count={getPermissionCount(value)} showZero={false} />
        </Space>
      }
      size="small"
      style={{ marginBottom: 16 }}
    >
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormValuesChange}
        disabled={disabled}
      >
        <Alert
          message="权限配置说明"
          description="配置此API路由的访问权限要求。只有满足权限要求的用户才能访问此接口。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label={
                <Space>
                  <KeyOutlined />
                  <span>开发者访问</span>
                  <Tooltip title="是否允许开发者Token直接访问此接口">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
              }
              name="allow_developer"
              valuePropName="checked"
            >
              <Switch 
                checkedChildren="允许" 
                unCheckedChildren="禁止"
                defaultChecked={true}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label={
                <Space>
                  <UserOutlined />
                  <span>最低角色级别</span>
                  <Tooltip title="用户角色级别必须达到此数值才能访问">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
              }
              name="min_role_level"
            >
              <InputNumber 
                min={0} 
                max={10} 
                placeholder="如：5"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label={
            <Space>
              <UserOutlined />
              <span>所需角色</span>
              <Tooltip title="用户必须拥有以下任一角色才能访问">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          }
          name="required_roles"
        >
          <Select
            mode="multiple"
            placeholder="选择所需角色"
            loading={loading}
            allowClear
            showSearch
            filterOption={(input, option) => {
              if (!option?.children) return false;
              return option.children.toString().toLowerCase().includes(input.toLowerCase());
            }}
          >
            {roles.map(role => (
              <Option key={role.id} value={role.code}>
                <Space>
                  <Tag color="blue">{role.name}</Tag>
                  <span style={{ fontSize: '12px', color: '#666' }}>({role.code})</span>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label={
            <Space>
              <SafetyOutlined />
              <span>所需权限</span>
              <Tooltip title="用户必须拥有以下任一权限才能访问">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          }
        >
          <Form.List name="required_permissions">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Card key={key} size="small" style={{ marginBottom: 8 }}>
                    <Row gutter={8} align="middle">
                      <Col span={8}>
                        <Form.Item
                          {...restField}
                          name={[name, 'resource']}
                          label="资源"
                          rules={[{ required: true, message: '请选择资源' }]}
                        >
                          <Select 
                            placeholder="选择资源"
                            showSearch
                            allowClear
                          >
                            {resourceOptions.map(option => (
                              <Option key={option.value} value={option.value}>
                                {option.label}
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item
                          {...restField}
                          name={[name, 'action']}
                          label="操作"
                          rules={[{ required: true, message: '请选择操作' }]}
                        >
                          <Select 
                            placeholder="选择操作"
                            showSearch
                            allowClear
                          >
                            {actionOptions.map(option => (
                              <Option key={option.value} value={option.value}>
                                {option.label}
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item
                          {...restField}
                          name={[name, 'description']}
                          label="描述"
                        >
                          <Input placeholder="权限描述" />
                        </Form.Item>
                      </Col>
                      <Col span={2}>
                        <Button
                          type="text"
                          danger
                          icon={<MinusCircleOutlined />}
                          onClick={() => remove(name)}
                          title="删除权限"
                        />
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
                  添加权限要求
                </Button>
              </>
            )}
          </Form.List>
        </Form.Item>

        {showAdvanced && (
          <>
            <Divider />
            <Alert
              message="权限集成状态"
              description="此API路由的权限配置将自动同步到角色权限管理系统，支持动态权限验证。"
              type="success"
              showIcon
              style={{ marginTop: 16 }}
            />
          </>
        )}
      </Form>
    </Card>
  );
};

// 辅助函数：计算权限配置数量
function getPermissionCount(config?: RoutePermissionConfig): number {
  if (!config) return 0;
  
  let count = 0;
  if (config.required_permissions && config.required_permissions.length > 0) {
    count += config.required_permissions.length;
  }
  if (config.required_roles && config.required_roles.length > 0) {
    count += config.required_roles.length;
  }
  if (config.min_role_level) {
    count += 1;
  }
  return count;
}

export default PermissionConfigComponent;
