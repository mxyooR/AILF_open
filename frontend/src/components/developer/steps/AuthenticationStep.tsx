/**
 * 开发者认证步骤组件
 */

import React, { useEffect, useRef } from 'react';
import { Form, Input, Button, Checkbox, Alert, Space, Typography } from 'antd';
import { EyeInvisibleOutlined, EyeTwoTone, LockOutlined, UserOutlined } from '@ant-design/icons';
import { useDeveloperAuth } from '../../../hooks/developer/useDeveloperAuth';
import type { AuthFormData } from '../../../types/developer/auth';

const { Title, Text } = Typography;

interface AuthenticationStepProps {
  onSuccess: () => void;
}

const AuthenticationStep: React.FC<AuthenticationStepProps> = ({ onSuccess }) => {
  const [form] = Form.useForm();
  const { authState, authenticate, clearError } = useDeveloperAuth();
  const isMountedRef = useRef(true);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const handleSubmit = async (values: AuthFormData) => {
    if (!isMountedRef.current) return;
    
    clearError();
    const result = await authenticate(values);

    if (isMountedRef.current && result.success) {
      onSuccess();
    }
  };

  const handleFormChange = () => {
    if (isMountedRef.current && authState.error) {
      clearError();
    }
  };

  return (
    <div className="authentication-step">
      <div className="auth-card">
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          {/* Apple-style icon with glassmorphism effect */}
          <div className="auth-icon-wrapper">
            <div className="auth-icon-highlight" />
            <UserOutlined style={{
              fontSize: 40,
              color: 'white',
              zIndex: 1
            }} />
          </div>

          <Title level={2} className="auth-title">
            开发者认证
          </Title>
          <Text className="auth-subtitle">
            请输入开发者密码以继续配置
          </Text>
        </div>

        {authState.error && (
          <Alert
            message="认证失败"
            description={authState.error}
            type="error"
            showIcon
            closable
            onClose={clearError}
            className="apple-alert"
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          onValuesChange={handleFormChange}
          autoComplete="off"
          initialValues={{ rememberMe: true }}
        >
          <Form.Item
            name="password"
            label={
              <span style={{
                fontSize: 14,
                fontWeight: 600,
                color: '#1d1d1f',
                letterSpacing: '-0.2px'
              }}>
                开发者密码
              </span>
            }
            rules={[
              { required: true, message: '请输入开发者密码' },
              { min: 6, message: '密码长度至少6位' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#86868b', fontSize: 18, marginRight: 8 }} />}
              placeholder="请输入开发者密码"
              size="large"
              className="auth-input"
              iconRender={(visible) =>
                visible ? <EyeTwoTone twoToneColor="#007aff" /> : <EyeInvisibleOutlined style={{ color: '#86868b' }} />
              }
            />
          </Form.Item>

          <Form.Item name="rememberMe" valuePropName="checked" style={{ marginBottom: 32 }}>
            <Checkbox
              style={{
                fontSize: 14,
                color: '#86868b',
                fontWeight: 500
              }}
            >
              <span style={{ marginLeft: 8 }}>记住登录状态</span>
            </Checkbox>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={authState.isLoading}
              block
              className="auth-button"
            >
              {authState.isLoading ? '认证中...' : '开始配置'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 32 }}>
          <Space direction="vertical" size={4}>
            <Text style={{
              fontSize: 13,
              color: '#86868b',
              fontWeight: 500
            }}>
              认证成功后将进入配置流程
            </Text>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default AuthenticationStep;
