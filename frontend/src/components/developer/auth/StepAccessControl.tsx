/**
 * 步骤访问控制组件
 * 根据认证状态和步骤完成情况控制步骤访问权限
 */

import React from 'react';
import { Alert, Button, Card, Typography } from 'antd';
import { LockOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import AuthGuard from './AuthGuard';

const { Title, Text } = Typography;

interface StepAccessControlProps {
  stepId: number;
  stepTitle: string;
  stepDescription: string;
  isCompleted: boolean;
  isEnabled: boolean;
  requiresAuth: boolean;
  children: React.ReactNode;
  onNavigateToAuth?: () => void;
  completedSteps?: number[];
}

const StepAccessControl: React.FC<StepAccessControlProps> = ({
  stepId,
  stepTitle,
  stepDescription,
  isCompleted,
  isEnabled,
  requiresAuth,
  children,
  onNavigateToAuth,
  completedSteps = []
}) => {
  // 检查前置步骤是否完成 - 临时关闭步骤限制用于测试
  const checkPrerequisites = (): { canAccess: boolean; missingSteps: number[] } => {
    // 临时关闭所有步骤限制，允许直接访问任何步骤
    return { canAccess: true, missingSteps: [] };

    // 原始逻辑（已注释）
    // if (stepId === 1) {
    //   // 第一步（认证步骤）总是可以访问
    //   return { canAccess: true, missingSteps: [] };
    // }

    // const missingSteps: number[] = [];

    // // 检查前面的步骤是否都已完成
    // for (let i = 1; i < stepId; i++) {
    //   if (!completedSteps.includes(i)) {
    //     missingSteps.push(i);
    //   }
    // }

    // return {
    //   canAccess: missingSteps.length === 0,
    //   missingSteps
    // };
  };

  const { canAccess, missingSteps } = checkPrerequisites();

  // 如果需要认证但未认证，显示认证要求
  if (requiresAuth) {
    return (
      <AuthGuard
        onAuthRequired={onNavigateToAuth}
        fallback={
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '400px',
            padding: '40px 20px'
          }}>
            <Card style={{ width: '100%', maxWidth: '500px', textAlign: 'center' }}>
              <div style={{ marginBottom: '24px' }}>
                <LockOutlined style={{ fontSize: '48px', color: '#ff4d4f', marginBottom: '16px' }} />
                <Title level={4}>需要开发者认证</Title>
                <Text style={{ color: '#666' }}>
                  访问"{stepTitle}"需要先完成开发者认证
                </Text>
              </div>
              
              <Alert
                message="认证要求"
                description="请先完成第一步的开发者认证，然后才能访问此配置步骤。"
                type="warning"
                showIcon
                style={{ marginBottom: '24px', textAlign: 'left' }}
              />

              {onNavigateToAuth && (
                <Button 
                  type="primary" 
                  icon={<LockOutlined />}
                  onClick={onNavigateToAuth}
                >
                  前往认证
                </Button>
              )}
            </Card>
          </div>
        }
      >
        {/* 认证成功后继续检查其他条件 */}
        <StepContentWithPrerequisites
          stepId={stepId}
          stepTitle={stepTitle}
          stepDescription={stepDescription}
          canAccess={canAccess}
          missingSteps={missingSteps}
          isEnabled={isEnabled}
          isCompleted={isCompleted}
        >
          {children}
        </StepContentWithPrerequisites>
      </AuthGuard>
    );
  }

  // 不需要认证的步骤，直接检查前置条件
  return (
    <StepContentWithPrerequisites
      stepId={stepId}
      stepTitle={stepTitle}
      stepDescription={stepDescription}
      canAccess={canAccess}
      missingSteps={missingSteps}
      isEnabled={isEnabled}
      isCompleted={isCompleted}
    >
      {children}
    </StepContentWithPrerequisites>
  );
};

interface StepContentWithPrerequisitesProps {
  stepId: number;
  stepTitle: string;
  stepDescription: string;
  canAccess: boolean;
  missingSteps: number[];
  isEnabled: boolean;
  isCompleted: boolean;
  children: React.ReactNode;
}

const StepContentWithPrerequisites: React.FC<StepContentWithPrerequisitesProps> = ({
  stepId,
  stepTitle,
  stepDescription,
  canAccess,
  missingSteps,
  isEnabled,
  isCompleted,
  children
}) => {
  // 如果不能访问，显示前置条件提示
  if (!canAccess) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        padding: '40px 20px'
      }}>
        <Card style={{ width: '100%', maxWidth: '500px', textAlign: 'center' }}>
          <div style={{ marginBottom: '24px' }}>
            <ExclamationCircleOutlined style={{ fontSize: '48px', color: '#faad14', marginBottom: '16px' }} />
            <Title level={4}>需要完成前置步骤</Title>
            <Text style={{ color: '#666' }}>
              访问"{stepTitle}"需要先完成前面的配置步骤
            </Text>
          </div>
          
          <Alert
            message="前置条件"
            description={
              <div>
                <Text>请先完成以下步骤：</Text>
                <ul style={{ textAlign: 'left', marginTop: '8px', marginBottom: 0 }}>
                  {missingSteps.map(step => (
                    <li key={step}>
                      <Text>第 {step} 步</Text>
                    </li>
                  ))}
                </ul>
              </div>
            }
            type="warning"
            showIcon
            style={{ textAlign: 'left' }}
          />
        </Card>
      </div>
    );
  }

  // 如果步骤被禁用，显示禁用提示
  if (!isEnabled) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        padding: '40px 20px'
      }}>
        <Card style={{ width: '100%', maxWidth: '500px', textAlign: 'center' }}>
          <div style={{ marginBottom: '24px' }}>
            <LockOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
            <Title level={4} style={{ color: '#999' }}>步骤暂不可用</Title>
            <Text style={{ color: '#999' }}>
              "{stepTitle}"功能正在开发中
            </Text>
          </div>
          
          <Alert
            message="开发中"
            description="此配置步骤正在开发中，敬请期待。"
            type="info"
            showIcon
          />
        </Card>
      </div>
    );
  }

  // 显示步骤完成状态
  if (isCompleted) {
    return (
      <div style={{ position: 'relative' }}>
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          zIndex: 10,
          background: '#f6ffed',
          border: '1px solid #b7eb8f',
          borderRadius: '6px',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
          <Text style={{ color: '#52c41a', fontSize: '12px', margin: 0 }}>
            已完成
          </Text>
        </div>
        {children}
      </div>
    );
  }

  // 正常显示步骤内容
  return <>{children}</>;
};

export default StepAccessControl;
