/**
 * 开发者配置主组件 - Apple风格设计
 */

import React, { useState, useEffect } from 'react';
import { Button, Space } from 'antd';
import {
  HomeOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  AppstoreOutlined,
  DatabaseOutlined,
  ApiOutlined,
  TeamOutlined,
  CheckOutlined,
  BranchesOutlined,
  ClusterOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import AuthenticationStep from './steps/AuthenticationStep';
import ScenarioConfigStep from './steps/ScenarioConfigStep';
import TemplateSelectionStep from './steps/TemplateSelectionStep';
import EntityModelingStep from './steps/EntityModelingStep';
import APIRouteStep from './steps/APIRouteStep';
import WorkflowDesignStep from './steps/WorkflowDesignStep';
import RoleManagementStep from './steps/RoleManagementStep';
import StepAccessControl from './auth/StepAccessControl';
import { useDeveloperAuth } from '../../hooks/developer/useDeveloperAuth';
import { useScenarioConfig } from '../../hooks/developer/useScenarioConfig';
import { scenarioAPI } from '../../services/developer/scenarioAPI';
import type { TemplateListItem } from '../../types/developer/template';
import './DeveloperConfigMain.css';
// Import the new global style file to ensure it overrides
import '../../styles/developer/developer-config.css';

interface Step {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  completed: boolean;
  active: boolean;
  enabled: boolean;
}

const DeveloperConfigMain: React.FC = () => {
  const navigate = useNavigate();
  const { authState, logout } = useDeveloperAuth();
  const { scenarioState, loadCurrentScenario } = useScenarioConfig();
  const [currentStep, setCurrentStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [stepRefs, setStepRefs] = useState<{ [key: number]: any }>({});
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateListItem | null>(null);

  // 步骤配置 - 临时关闭访问控制用于测试
  const steps: Step[] = [
    {
      id: 1,
      title: '开发者认证',
      description: '验证开发者身份',
      icon: <UserOutlined />,
      completed: completedSteps.includes(1),
      active: currentStep === 1,
      enabled: true // 认证步骤总是可用
    },
    {
      id: 2,
      title: '场景配置',
      description: '配置业务场景',
      icon: <SettingOutlined />,
      completed: completedSteps.includes(2),
      active: currentStep === 2,
      enabled: true // 临时关闭限制
    },
    {
      id: 3,
      title: '模板选择',
      description: '选择项目模板',
      icon: <AppstoreOutlined />,
      completed: completedSteps.includes(3),
      active: currentStep === 3,
      enabled: true // 临时关闭限制
    },
    {
      id: 4,
      title: '实体建模',
      description: '设计数据模型',
      icon: <DatabaseOutlined />,
      completed: completedSteps.includes(4),
      active: currentStep === 4,
      enabled: true // 临时关闭限制
    },
    {
      id: 5,
      title: 'API路由管理',
      description: '配置接口路由',
      icon: <ApiOutlined />,
      completed: completedSteps.includes(5),
      active: currentStep === 5,
      enabled: true // 临时关闭限制
    },
    {
      id: 6,
      title: '工作流设计',
      description: '设计业务流程',
      icon: <BranchesOutlined />,
      completed: completedSteps.includes(6),
      active: currentStep === 6,
      enabled: true // 临时关闭限制
    },
    {
      id: 7,
      title: '角色管理',
      description: '配置用户角色和权限',
      icon: <TeamOutlined />,
      completed: completedSteps.includes(7),
      active: currentStep === 7,
      enabled: true // 临时关闭限制
    }
  ];

  // 检查认证状态
  useEffect(() => {
    if (authState.isAuthenticated && !completedSteps.includes(1)) {
      setCompletedSteps([1]);
      setCurrentStep(2);
    }
  }, [authState.isAuthenticated, completedSteps]);

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleLogout = () => {
    logout();
    setCurrentStep(1);
    setCompletedSteps([]);
  };

  const handleAuthSuccess = () => {
    setCompletedSteps([1]);
    setCurrentStep(2);
  };

  const handleScenarioSuccess = () => {
    setCompletedSteps(prev => [...prev, 2]);
    setCurrentStep(3);
  };

  const handleTemplateSelect = (template: TemplateListItem) => {
    setSelectedTemplate(template);
  };

  const handleTemplateSuccess = async () => {
    setCompletedSteps(prev => [...prev, 3]);
    
    // 等待并重新加载场景状态以获取最新创建的场景ID
    console.log('🔄 模板成功，重新加载场景状态...');
    
    // 多次尝试重新加载，确保获取到最新的场景
    for (let i = 0; i < 3; i++) {
      try {
        await loadCurrentScenario();
        // 重新获取最新场景状态来验证
        const latestResponse = await scenarioAPI.getCurrent(true);
        const currentScenario = latestResponse.data.scenario;
        if (currentScenario?.id) {
          console.log('✅ 主组件场景状态已更新:', currentScenario.id);
          break;
        }
      } catch (error) {
        console.warn(`❌ 第${i+1}次加载场景状态失败:`, error);
      }
      
      if (i < 2) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    setCurrentStep(4);
  };

  const handleEntityModelingSuccess = () => {
    setCompletedSteps(prev => [...prev, 4]);
    setCurrentStep(5);
  };

  const handleAPIRouteSuccess = () => {
    setCompletedSteps(prev => [...prev, 5]);
    setCurrentStep(6);
  };

  const handleWorkflowDesignSuccess = () => {
    setCompletedSteps(prev => [...prev, 6]);
    setCurrentStep(7);
  };

  const handleRoleManagementSuccess = () => {
    setCompletedSteps(prev => [...prev, 7]);
    setCurrentStep(7);
  };

  const handleStepClick = (stepId: number) => {
    const step = steps.find(s => s.id === stepId);
    if (step && step.enabled) {
      setCurrentStep(stepId);
    }
  };

  const handleNavigateToAuth = () => {
    setCurrentStep(1);
  };

  const handleStepBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSave = () => {
    // 触发当前步骤的保存操作
    const currentStepRef = stepRefs[currentStep];
    if (currentStepRef && currentStepRef.handleSave) {
      currentStepRef.handleSave();
    }
  };

  const getStepTitle = () => {
    const step = steps.find(s => s.id === currentStep);
    return step ? step.title : '配置步骤';
  };

  const renderStepContent = () => {
    const currentStepInfo = steps.find(s => s.id === currentStep);

    if (!currentStepInfo) {
      return null;
    }

    const stepContent = (() => {
      switch (currentStep) {
        case 1:
          return <AuthenticationStep onSuccess={handleAuthSuccess} />;
        case 2:
          return (
            <ScenarioConfigStep
              onSuccess={handleScenarioSuccess}
              onBack={handleStepBack}
            />
          );
        case 3:
          return (
            <TemplateSelectionStep
              onTemplateSelect={handleTemplateSelect}
              onNext={handleTemplateSuccess}
            />
          );
        case 4:
          return (
            <EntityModelingStep
              onNext={handleEntityModelingSuccess}
              onPrev={handleStepBack}
              scenarioId={scenarioState.currentScenario?.id || ""}
            />
          );
        case 5:
          return (
            <APIRouteStep
              onNext={handleAPIRouteSuccess}
              onPrev={handleStepBack}
            />
          );
        case 6:
          return (
            <WorkflowDesignStep
              onNext={handleWorkflowDesignSuccess}
              onPrev={handleStepBack}
            />
          );
        case 7:
          return (
            <RoleManagementStep
              onNext={handleRoleManagementSuccess}
              onPrev={handleStepBack}
            />
          );
        default:
          return (
            <div className="step-placeholder apple-card">
              <div className="placeholder-content" style={{ textAlign: 'center', padding: '40px' }}>
                <div className="placeholder-icon" style={{ fontSize: '48px', color: '#007AFF', marginBottom: '20px' }}>
                  {currentStepInfo.icon}
                </div>
                <h3 className="placeholder-title" style={{ fontSize: '24px', fontWeight: 600, marginBottom: '10px' }}>
                  {currentStepInfo.title}
                </h3>
                <p className="placeholder-description" style={{ color: '#86868b', marginBottom: '30px' }}>
                  该步骤正在开发中，敬请期待
                </p>
                <div className="placeholder-features" style={{ display: 'inline-flex', flexDirection: 'column', gap: '15px', textAlign: 'left' }}>
                  <div className="feature-item" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CheckOutlined style={{ color: '#34C759' }} />
                    <span>功能设计已完成</span>
                  </div>
                  <div className="feature-item" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CheckOutlined style={{ color: '#34C759' }} />
                    <span>界面原型已确定</span>
                  </div>
                  <div className="feature-item" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CheckOutlined style={{ color: '#34C759' }} />
                    <span>即将开始开发</span>
                  </div>
                </div>
              </div>
            </div>
          );
      }
    })();

    // 使用访问控制组件包装步骤内容
    return (
      <StepAccessControl
        stepId={currentStep}
        stepTitle={currentStepInfo.title}
        stepDescription={currentStepInfo.description}
        isCompleted={currentStepInfo.completed}
        isEnabled={currentStepInfo.enabled}
        requiresAuth={currentStep > 1} // 除第一步外都需要认证
        onNavigateToAuth={handleNavigateToAuth}
        completedSteps={completedSteps}
      >
        {stepContent}
      </StepAccessControl>
    );
  };

  return (
    <div className="developer-config-main">
      {/* Apple风格顶部导航栏 */}
      <div className="config-header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo-wrapper">
              <h1 className="main-title">AILF</h1>
            </div>
            <div className="header-divider"></div>
            <span className="subtitle">开发者配置面板</span>
          </div>
          <div className="header-right">
            {authState.isAuthenticated && (
              <Button
                type="text"
                icon={<LogoutOutlined />}
                onClick={handleLogout}
                className="action-button"
              >
                退出登录
              </Button>
            )}
            <Button
              type="text"
              icon={<HomeOutlined />}
              onClick={handleBackToHome}
              className="action-button"
            >
              返回主页
            </Button>
          </div>
        </div>
      </div>

      {/* 主要内容区域 - Apple风格左右布局 */}
      <div className="config-main">
        {/* 左侧步骤导航 */}
        <div className="steps-sidebar">
          <div className="steps-container">
            <Button
              type="default"
              block
              className="runtime-monitor-entry-button"
              icon={<ClusterOutlined />}
              onClick={() => navigate('/config/runtime-monitor')}
            >
              进入运行监控
            </Button>

            <div className="steps-header">
              <h2 className="steps-title">配置步骤</h2>
              <p className="steps-subtitle">完成以下步骤来配置您的AILF项目</p>
            </div>

            <div className="steps-list">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`step-item ${step.active ? 'active' : ''} ${step.completed ? 'completed' : ''} ${
                    step.enabled ? 'enabled' : 'disabled'
                  }`}
                  onClick={() => handleStepClick(step.id)}
                >
                  <div className="step-indicator">
                    <div className="step-dot-container">
                      {step.completed ? (
                        <CheckOutlined className="step-check-icon" />
                      ) : (
                        <div className="step-dot" />
                      )}
                    </div>
                  </div>
                  <div className="step-content">
                    <div className="step-title">{step.title}</div>
                    <p className="step-description">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="steps-footer">
              <div className="progress-info">
                <span className="progress-text">
                  已完成 {completedSteps.length} / {steps.length} 步骤
                </span>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${(completedSteps.length / steps.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧内容区域 */}
        <div className="content-area">
          <div className="content-container">
            {renderStepContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeveloperConfigMain;
