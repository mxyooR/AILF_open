/**
 * 认证要求提示组件
 */

import React from 'react';
import { Alert, Button, Card, Steps, Typography } from 'antd';
import { LockOutlined, KeyOutlined, ApiOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface AuthenticationRequiredProps {
  onNavigateToAuth?: () => void;
}

const AuthenticationRequired: React.FC<AuthenticationRequiredProps> = ({
  onNavigateToAuth
}) => {
  const steps = [
    {
      title: '访问认证页面',
      description: '点击下方按钮跳转到开发者认证页面',
      icon: <LockOutlined />
    },
    {
      title: '输入开发者密码',
      description: '使用正确的开发者密码进行认证',
      icon: <KeyOutlined />
    },
    {
      title: '获取访问令牌',
      description: '系统将为您生成有效的JWT访问令牌',
      icon: <ApiOutlined />
    }
  ];

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '400px',
      padding: '40px 20px'
    }}>
      <Card 
        style={{ 
          width: '100%', 
          maxWidth: '600px',
          textAlign: 'center'
        }}
        styles={{ body: { padding: '40px' } }}
      >
        <div style={{ marginBottom: '24px' }}>
          <LockOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
          <Title level={3}>需要开发者认证</Title>
          <Paragraph style={{ fontSize: '16px', color: '#666' }}>
            您需要先进行开发者认证才能访问工作流设计功能。
          </Paragraph>
        </div>

        <Alert
          message="认证提示"
          description={
            <div>
              <Text>检测到您当前使用的是测试令牌或无效令牌。</Text>
              <br />
              <Text>请按照以下步骤进行正确的开发者认证：</Text>
            </div>
          }
          type="warning"
          showIcon
          style={{ marginBottom: '32px', textAlign: 'left' }}
        />

        <Steps
          direction="vertical"
          size="small"
          current={-1}
          items={steps}
          style={{ marginBottom: '32px', textAlign: 'left' }}
        />

        <div style={{ marginTop: '32px' }}>
          {onNavigateToAuth && (
            <Button 
              type="primary" 
              size="large"
              icon={<LockOutlined />}
              onClick={onNavigateToAuth}
              style={{ marginRight: '12px' }}
            >
              进行开发者认证
            </Button>
          )}
          <Button 
            size="large"
            onClick={() => window.location.reload()}
          >
            刷新页面
          </Button>
        </div>

        <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid #f0f0f0' }}>
          <Paragraph style={{ fontSize: '14px', color: '#999', margin: 0 }}>
            开发者密码由环境变量安全注入，请向系统管理员获取当前凭据。
          </Paragraph>
        </div>
      </Card>
    </div>
  );
};

export default AuthenticationRequired;
