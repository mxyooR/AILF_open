/**
 * 用户管理模态框组件
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Row,
  Col,
  Divider,
  Space,
  Typography,
  Spin,
  InputNumber
} from 'antd';
import { UserAPI, CreateUserRequest, AvailableRole, UserFormSchema, UserFormField } from '../../../services/developer/userAPI';

const { Option } = Select;
const { Text } = Typography;

interface UserManagementModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

const UserManagementModal: React.FC<UserManagementModalProps> = ({
  visible,
  onCancel,
  onSuccess
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [availableRoles, setAvailableRoles] = useState<AvailableRole[]>([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [formSchema, setFormSchema] = useState<UserFormSchema | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);

  // 加载可用角色列表
  const loadAvailableRoles = async () => {
    setRolesLoading(true);
    try {
      const data = await UserAPI.getAvailableRoles();
      console.log('UserAPI.getAvailableRoles response:', data); // 调试日志

      if (data && data.roles) {
        setAvailableRoles(data.roles);
        console.log('Available roles loaded:', data.roles.length); // 调试日志
      } else {
        console.error('Invalid response structure:', data);
        message.error('角色数据格式错误');
      }
    } catch (error) {
      message.error('加载角色列表失败');
      console.error('Load roles error:', error);
    } finally {
      setRolesLoading(false);
    }
  };

  // 加载表单schema
  const loadFormSchema = async (roleId?: string) => {
    setSchemaLoading(true);
    try {
      const schema = await UserAPI.getUserFormSchema(roleId);
      setFormSchema(schema);
      console.log('Loaded form schema:', schema);
    } catch (error) {
      message.error('加载表单配置失败');
      console.error('Load form schema error:', error);
    } finally {
      setSchemaLoading(false);
    }
  };

  // 角色选择变化处理
  const handleRoleChange = (roleId: string) => {
    setSelectedRoleId(roleId);
    // 保存当前的基础字段值
    const currentValues = form.getFieldsValue();
    const preservedValues = {
      role_id: roleId,
      is_active: currentValues.is_active !== undefined ? currentValues.is_active : true,
      username: currentValues.username,
      email: currentValues.email,
      password: currentValues.password,
      phone: currentValues.phone,
      real_name: currentValues.real_name
    };

    // 清除所有字段
    form.resetFields();

    // 使用setTimeout确保resetFields完成后再设置值
    setTimeout(() => {
      form.setFieldsValue(preservedValues);
    }, 0);

    // 重新加载表单schema
    loadFormSchema(roleId);
  };

  // 模态框打开时加载数据
  useEffect(() => {
    if (visible) {
      loadAvailableRoles();
      // 不加载默认schema，等用户选择角色后再加载
      form.resetFields();
      setSelectedRoleId(null);
      setFormSchema(null);
      // 设置默认值
      form.setFieldsValue({
        is_active: true
      });
    }
  }, [visible, form]);

  // 渲染表单字段
  const renderFormField = (field: UserFormField) => {
    const commonProps = {
      placeholder: field.placeholder,
      disabled: loading
    };

    switch (field.type) {
      case 'input-text':
        return <Input {...commonProps} />;

      case 'input-email':
        return <Input type="email" {...commonProps} />;

      case 'input-password':
        return <Input.Password {...commonProps} />;

      case 'textarea':
        return <Input.TextArea {...commonProps} rows={4} />;

      case 'input-number':
        return <Input type="number" {...commonProps} />;

      case 'switch':
        return <Switch checkedChildren="启用" unCheckedChildren="禁用" />;

      case 'select':
        if (field.name === 'role_id') {
          return (
            <Select
              placeholder={field.placeholder}
              loading={rolesLoading}
              showSearch
              optionFilterProp="children"
              disabled={loading}
              onChange={handleRoleChange}
              value={selectedRoleId}
            >
              {availableRoles.map(role => (
                <Select.Option key={role.id} value={role.id}>
                  <Space direction="vertical" size={0}>
                    <Text strong>{role.name}</Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {role.description || role.code} • 当前用户数: {role.user_count}
                    </Text>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          );
        } else if (field.options) {
          return (
            <Select
              placeholder={field.placeholder}
              disabled={loading}
              onChange={(value) => {
                // 确保下拉框的值被正确设置到表单中
                form.setFieldValue(field.name, value);
              }}
            >
              {field.options.map(option => (
                <Select.Option key={option.value} value={option.value}>
                  {option.label}
                </Select.Option>
              ))}
            </Select>
          );
        }
        return <Select {...commonProps} />;

      default:
        return <Input {...commonProps} />;
    }
  };

  // 创建用户
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      // 构建用户数据，包含所有表单字段
      const userData: CreateUserRequest & Record<string, any> = {
        username: values.username,
        email: values.email,
        password: values.password,
        real_name: values.real_name || values.name, // 支持name字段映射到real_name
        phone: values.phone,
        role_id: values.role_id,
        is_active: values.is_active !== undefined ? values.is_active : true
      };

      // 添加动态字段
      if (formSchema?.fields) {
        formSchema.fields.forEach(field => {
          if (values[field.name] !== undefined && !userData.hasOwnProperty(field.name)) {
            // 特殊处理：如果字段名是name，映射到real_name
            if (field.name === 'name' && !userData.real_name) {
              userData.real_name = values[field.name];
            } else {
              userData[field.name] = values[field.name];
            }
          }
        });
      }

      console.log('Creating user with data:', userData);
      await UserAPI.createUser(userData);
      message.success('用户创建成功');
      onSuccess();
      onCancel();
    } catch (error: any) {
      if (error.response?.status === 409) {
        message.error('用户名或邮箱已存在，请使用不同的用户名或邮箱');
      } else if (error.response?.data?.message) {
        message.error(`创建用户失败: ${error.response.data.message}`);
      } else {
        message.error('创建用户失败');
      }
      console.error('Create user error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (schemaLoading) {
    return (
      <Modal
        title="创建用户"
        open={visible}
        onCancel={onCancel}
        footer={null}
        width={600}
      >
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '16px' }}>正在加载表单配置...</div>
        </div>
      </Modal>
    );
  }

  return (
    <Modal
      title={selectedRoleId && formSchema ? `创建${formSchema.display_name}` : '创建用户'}
      open={visible}
      onOk={handleSubmit}
      onCancel={onCancel}
      width={600}
      confirmLoading={loading}
      okText="创建用户"
      cancelText="取消"
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          is_active: true
        }}
      >
        {/* 角色选择字段 */}
        <Form.Item
          label="角色"
          name="role_id"
          rules={[{ required: true, message: '请选择角色' }]}
        >
          <Select
            placeholder="请选择角色"
            loading={rolesLoading}
            showSearch
            optionFilterProp="children"
            disabled={loading}
            onChange={(value) => {
              // 确保角色选择的值被正确设置到表单中
              form.setFieldValue('role_id', value);
              handleRoleChange(value);
            }}
            value={selectedRoleId}
          >
            {availableRoles.map(role => (
              <Select.Option key={role.id} value={role.id}>
                <Space direction="vertical" size={0}>
                  <Text strong>{role.name}</Text>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {role.description || role.code} • 当前用户数: {role.user_count}
                  </Text>
                </Space>
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        {/* 角色选择提示 */}
        {!selectedRoleId && (
          <div style={{
            textAlign: 'center',
            padding: '40px 20px',
            color: '#999',
            background: '#fafafa',
            borderRadius: '6px',
            border: '1px dashed #d9d9d9'
          }}>
            <Text type="secondary">请先选择角色，然后填写对应的用户信息</Text>
          </div>
        )}

        {/* 动态字段 - 只有选择了角色才显示 */}
        {selectedRoleId && formSchema?.fields.map((field, index) => {
          const rules = [];

          // 添加必填验证
          if (field.required) {
            rules.push({ required: true, message: `请输入${field.label}` });
          }

          // 添加长度验证
          if (field.minLength) {
            rules.push({ min: field.minLength, message: `${field.label}长度不能少于${field.minLength}个字符` });
          }
          if (field.maxLength) {
            rules.push({ max: field.maxLength, message: `${field.label}长度不能超过${field.maxLength}个字符` });
          }

          // 添加格式验证
          if (field.validations?.matchRegexp) {
            rules.push({ pattern: new RegExp(field.validations.matchRegexp), message: `${field.label}格式不正确` });
          }

          // 特殊字段验证
          if (field.name === 'email') {
            rules.push({ type: 'email' as const, message: '请输入有效的邮箱地址' });
          }

          const isSwitch = field.type === 'switch';

          return (
            <Form.Item
              key={field.name}
              label={field.label}
              name={field.name}
              rules={rules}
              valuePropName={isSwitch ? 'checked' : 'value'}
            >
              {renderFormField(field)}
            </Form.Item>
          );
        })}
      </Form>
    </Modal>
  );
};

export default UserManagementModal;
