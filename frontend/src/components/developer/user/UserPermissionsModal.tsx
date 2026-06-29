/**
 * 用户权限查看模态框组件
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Spin,
  message,
  Descriptions,
  Tag,
  Table,
  Tabs,
  Empty,
  Space,
  Typography,
  Divider,
  Card,
  Statistic,
  Row,
  Col
} from 'antd';
import {
  SafetyOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  LockOutlined
} from '@ant-design/icons';
import { PermissionAPI, UserApiPermissions } from '../../../services/developer/permissionAPI';
import './UserPermissionsModal.css';

const { Text, Title } = Typography;

interface UserPermissionsModalProps {
  visible: boolean;
  userId: string | null;
  username?: string;
  onCancel: () => void;
}

const UserPermissionsModal: React.FC<UserPermissionsModalProps> = ({
  visible,
  userId,
  username,
  onCancel
}) => {
  const [loading, setLoading] = useState(false);
  const [permissionsData, setPermissionsData] = useState<UserApiPermissions | null>(null);

  // 加载用户权限数据
  const loadUserPermissions = async () => {
    if (!userId) return;

    setLoading(true);
    try {
      const data = await PermissionAPI.getUserApiPermissions({ user_id: userId });
      setPermissionsData(data);
    } catch (error) {
      message.error('加载用户权限失败');
      console.error('Load user permissions error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 模态框打开时加载数据
  useEffect(() => {
    if (visible && userId) {
      loadUserPermissions();
    } else {
      setPermissionsData(null);
    }
  }, [visible, userId]);

  // API表格列配置
  const apiColumns = [
    {
      title: 'API名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      width: 250,
      render: (text: string, record: any) => (
        <Space>
          <Tag color={getMethodColor(record.method)}>{record.method}</Tag>
          <Text code>{text}</Text>
        </Space>
      )
    },
    {
      title: '资源',
      dataIndex: 'resource',
      key: 'resource',
      width: 120,
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (text: string) => <Tag color="green">{text}</Tag>
    },
    {
      title: '授权来源',
      dataIndex: 'granted_by',
      key: 'granted_by',
      width: 150,
      render: (text: string) => (
        <Space>
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
          <Text type="secondary">{text}</Text>
        </Space>
      )
    }
  ];

  // 获取HTTP方法对应的颜色
  const getMethodColor = (method: string) => {
    const colors: Record<string, string> = {
      GET: 'blue',
      POST: 'green',
      PUT: 'orange',
      DELETE: 'red',
      PATCH: 'purple'
    };
    return colors[method] || 'default';
  };

  // 渲染权限列表
  const renderPermissionsList = () => {
    if (!permissionsData?.summary?.permissions || permissionsData.summary.permissions.length === 0) {
      return <Empty description="暂无权限" />;
    }

    return (
      <div className="permissions-list">
        {permissionsData.summary.permissions.map((permission, index) => (
          <Tag
            key={index}
            icon={<SafetyOutlined />}
            color="blue"
            style={{ marginBottom: 8 }}
          >
            {permission}
          </Tag>
        ))}
      </div>
    );
  };

  // 渲染统计信息
  const renderStatistics = () => {
    if (!permissionsData) return null;

    const { summary } = permissionsData;

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="可访问API总数"
              value={summary.total_apis}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="权限数量"
              value={summary.permissions?.length || 0}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="资源类型"
              value={Object.keys(summary.by_resource || {}).length}
              prefix={<LockOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染资源分布
  const renderResourceDistribution = () => {
    if (!permissionsData?.summary?.by_resource) return null;

    const data = Object.entries(permissionsData.summary.by_resource).map(([resource, count]) => ({
      resource,
      count
    }));

    return (
      <div className="resource-distribution">
        <Title level={5}>按资源分布</Title>
        <Space wrap>
          {data.map(item => (
            <Tag key={item.resource} color="blue">
              {item.resource}: {item.count}
            </Tag>
          ))}
        </Space>
      </div>
    );
  };

  // 渲染方法分布
  const renderMethodDistribution = () => {
    if (!permissionsData?.summary?.by_method) return null;

    const data = Object.entries(permissionsData.summary.by_method).map(([method, count]) => ({
      method,
      count
    }));

    return (
      <div className="method-distribution">
        <Title level={5}>按HTTP方法分布</Title>
        <Space wrap>
          {data.map(item => (
            <Tag key={item.method} color={getMethodColor(item.method)}>
              {item.method}: {item.count}
            </Tag>
          ))}
        </Space>
      </div>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <SafetyOutlined />
          <span>用户权限详情 {username && `- ${username}`}</span>
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width={1000}
      footer={null}
      className="user-permissions-modal"
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在加载用户权限信息...</Text>
          </div>
        </div>
      ) : permissionsData ? (
        <div className="permissions-content">
          {/* 用户基本信息 */}
          <Descriptions bordered column={2} size="small" style={{ marginBottom: 24 }}>
            <Descriptions.Item label="用户ID">{permissionsData.user.id}</Descriptions.Item>
            <Descriptions.Item label="用户名">{permissionsData.user.name}</Descriptions.Item>
            <Descriptions.Item label="角色" span={2}>
              {permissionsData.user.roles.map(role => (
                <Tag key={role.id} color="purple">
                  {role.name} ({role.code})
                </Tag>
              ))}
            </Descriptions.Item>
          </Descriptions>

          {/* 统计信息 */}
          {renderStatistics()}

          {/* 标签页 */}
          <Tabs
            defaultActiveKey="apis"
            items={[
              {
                key: 'apis',
                label: (
                  <Space>
                    <ApiOutlined />
                    <span>可访问API ({permissionsData.accessible_apis.length})</span>
                  </Space>
                ),
                children: (
                  <Table
                    columns={apiColumns}
                    dataSource={permissionsData.accessible_apis}
                    rowKey="api_id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showTotal: (total) => `共 ${total} 个API`
                    }}
                    scroll={{ x: 800 }}
                  />
                )
              },
              {
                key: 'permissions',
                label: (
                  <Space>
                    <SafetyOutlined />
                    <span>权限列表 ({permissionsData.summary.permissions?.length || 0})</span>
                  </Space>
                ),
                children: (
                  <div>
                    {renderPermissionsList()}
                    <Divider />
                    {renderResourceDistribution()}
                    <Divider />
                    {renderMethodDistribution()}
                  </div>
                )
              }
            ]}
          />
        </div>
      ) : (
        <Empty description="暂无数据" />
      )}
    </Modal>
  );
};

export default UserPermissionsModal;
