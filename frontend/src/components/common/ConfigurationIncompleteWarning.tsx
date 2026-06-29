/**
 * 配置未完成警告组件
 * 当七步配置未完成时显示警告信息
 */
import React from 'react';
import { Alert, Button, Card, Progress, Space, Typography } from 'antd';
import { SettingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ConfigurationStatus } from '../../hooks/useConfigurationStatus';

const { Title, Text, Paragraph } = Typography;

interface ConfigurationIncompleteWarningProps {
  status: ConfigurationStatus;
  showDetails?: boolean;
  size?: 'small' | 'default' | 'large';
}

const ConfigurationIncompleteWarning: React.FC<ConfigurationIncompleteWarningProps> = ({
  status,
  showDetails = true,
  size = 'default'
}) => {
  const navigate = useNavigate();

  const handleGoToConfig = () => {
    navigate('/config');
  };

  const getStepName = (stepNumber: number): string => {
    const stepNames: Record<number, string> = {
      1: '开发者认证',
      2: '场景配置',
      3: '模板选择',
      4: '实体建模',
      5: 'API路由管理',
      6: '工作流设计',
      7: '角色管理'
    };
    return stepNames[stepNumber] || `步骤${stepNumber}`;
  };

  const completionPercentage = status.configuration_status?.completion_percentage || 0;
  const completedCount = status.configuration_status?.completed_count || 0;
  const totalSteps = status.configuration_status?.total_steps || 7;

  if (size === 'small') {
    return (
      <Alert
        message="配置未完成"
        description={`请先完成七步配置才能使用系统功能 (${completedCount}/${totalSteps})`}
        type="warning"
        showIcon
        icon={<ExclamationCircleOutlined />}
        action={
          <Button size="small" type="primary" onClick={handleGoToConfig}>
            去配置
          </Button>
        }
        closable={false}
        style={{ marginBottom: 16 }}
      />
    );
  }

  return (
    <Card
      style={{ 
        maxWidth: 600, 
        margin: '0 auto',
        textAlign: 'center'
      }}
      bodyStyle={{ padding: size === 'large' ? 32 : 24 }}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 图标和标题 */}
        <div>
          <ExclamationCircleOutlined 
            style={{ 
              fontSize: size === 'large' ? 64 : 48, 
              color: '#faad14',
              marginBottom: 16
            }} 
          />
          <Title level={size === 'large' ? 2 : 3} style={{ margin: 0 }}>
            系统配置未完成
          </Title>
        </div>

        {/* 进度条 */}
        <div style={{ width: '100%' }}>
          <Progress
            percent={completionPercentage}
            status={completionPercentage === 100 ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            format={() => `${completedCount}/${totalSteps}`}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            配置完成度: {completionPercentage.toFixed(1)}%
          </Text>
        </div>

        {/* 主要消息 */}
        <div>
          <Paragraph style={{ fontSize: 16, margin: 0 }}>
            {status.message}
          </Paragraph>
          <Paragraph type="secondary" style={{ margin: '8px 0 0 0' }}>
            完成配置后即可使用AI语音对话和其他系统功能
          </Paragraph>
        </div>

        {/* 未完成步骤详情 */}
        {showDetails && status.incomplete_steps && status.incomplete_steps.length > 0 && (
          <div style={{ textAlign: 'left', width: '100%' }}>
            <Title level={5} style={{ marginBottom: 12 }}>
              待完成步骤:
            </Title>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {status.incomplete_steps.map((stepNumber) => (
                <div key={stepNumber} style={{ 
                  padding: '8px 12px',
                  backgroundColor: '#fff7e6',
                  border: '1px solid #ffd591',
                  borderRadius: 4,
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <span style={{ 
                    display: 'inline-block',
                    width: 20,
                    height: 20,
                    borderRadius: '50%',
                    backgroundColor: '#faad14',
                    color: 'white',
                    textAlign: 'center',
                    lineHeight: '20px',
                    fontSize: 12,
                    marginRight: 8
                  }}>
                    {stepNumber}
                  </span>
                  <Text>{getStepName(stepNumber)}</Text>
                </div>
              ))}
            </Space>
          </div>
        )}

        {/* 操作按钮 */}
        <Button 
          type="primary" 
          size={size === 'large' ? 'large' : 'middle'}
          icon={<SettingOutlined />}
          onClick={handleGoToConfig}
          style={{ minWidth: 120 }}
        >
          开始配置
        </Button>
      </Space>
    </Card>
  );
};

export default ConfigurationIncompleteWarning;
