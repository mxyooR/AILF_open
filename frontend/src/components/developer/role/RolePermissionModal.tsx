/**
 * 角色权限管理模态框组件
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Switch,
  Tag,
  Space,
  Button,
  Input,
  Select,
  message,
  Tabs,
  Card,
  Row,
  Col,
  Statistic,
  Tooltip,
  Badge,
  Divider,
  Alert
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  SaveOutlined,
  ReloadOutlined,
  ApiOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { Role } from '../../../services/developer/roleAPI';
import { PermissionAPI, ApiRoute, PermissionMatrix } from '../../../services/developer/permissionAPI';
import './RolePermissionModal.css';

const { Option } = Select;
const { TabPane } = Tabs;
const { Search } = Input;

interface RolePermissionModalProps {
  visible: boolean;
  role: Role | null;
  onClose: () => void;
  onSave?: (roleId: string, permissions: Record<string, boolean>) => void;
}

const RolePermissionModal: React.FC<RolePermissionModalProps> = ({
  visible,
  role,
  onClose,
  onSave
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [apiRoutes, setApiRoutes] = useState<ApiRoute[]>([]);
  const [permissions, setPermissions] = useState<Record<string, boolean>>({});
  const [originalPermissions, setOriginalPermissions] = useState<Record<string, boolean>>({});
  const [searchText, setSearchText] = useState('');
  const [methodFilter, setMethodFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [activeTab, setActiveTab] = useState('permissions');

  // 统计信息
  const [statistics, setStatistics] = useState({
    total_apis: 0,
    granted_apis: 0,
    denied_apis: 0,
    coverage: 0
  });

  // 获取API端点列表
  const loadApiRoutes = async () => {
    if (!role) return;

    setLoading(true);
    try {
      // 获取权限矩阵，其中包含API端点信息
      const matrixResponse = await PermissionAPI.getPermissionMatrix();
      const apiEndpoints = matrixResponse.matrix.apis || [];
      const rolePermissions = matrixResponse.matrix.permissions[role.id] || {};

      setApiRoutes(apiEndpoints);
      setPermissions(rolePermissions);
      setOriginalPermissions({ ...rolePermissions });

      // 计算统计信息
      const totalApis = apiEndpoints.length;
      const grantedApis = Object.values(rolePermissions).filter(Boolean).length;
      const coverage = totalApis > 0 ? (grantedApis / totalApis) * 100 : 0;

      setStatistics({
        total_apis: totalApis,
        granted_apis: grantedApis,
        denied_apis: totalApis - grantedApis,
        coverage
      });
    } catch (error) {
      message.error('加载API端点失败');
      console.error('Load API endpoints error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && role) {
      loadApiRoutes();
    }
  }, [visible, role]);

  // 权限变更处理
  const handlePermissionChange = (apiId: string, granted: boolean) => {
    // 检查是否为公开路由，公开路由不允许修改
    const route = apiRoutes.find(r => r.id === apiId);
    if (route?.is_public) {
      return; // 公开路由不允许修改
    }
    
    const newPermissions = { ...permissions, [apiId]: granted };
    setPermissions(newPermissions);
    
    // 更新统计信息
    const grantedApis = Object.values(newPermissions).filter(Boolean).length;
    const totalApis = apiRoutes.length;
    const coverage = totalApis > 0 ? (grantedApis / totalApis) * 100 : 0;
    
    setStatistics({
      total_apis: totalApis,
      granted_apis: grantedApis,
      denied_apis: totalApis - grantedApis,
      coverage
    });
  };

  // 批量权限操作
  const handleBatchOperation = (operation: 'grant_all' | 'revoke_all' | 'reset') => {
    let newPermissions: Record<string, boolean> = {};
    
    switch (operation) {
      case 'grant_all':
        newPermissions = apiRoutes.reduce((acc, route) => {
          // 公开路由始终为 true，私有路由设为 true
          acc[route.id] = true;
          return acc;
        }, {} as Record<string, boolean>);
        break;
      case 'revoke_all':
        newPermissions = apiRoutes.reduce((acc, route) => {
          // 公开路由始终为 true，私有路由设为 false
          acc[route.id] = route.is_public ? true : false;
          return acc;
        }, {} as Record<string, boolean>);
        break;
      case 'reset':
        newPermissions = { ...originalPermissions };
        break;
    }
    
    setPermissions(newPermissions);
    
    // 更新统计信息
    const grantedApis = Object.values(newPermissions).filter(Boolean).length;
    const totalApis = apiRoutes.length;
    const coverage = totalApis > 0 ? (grantedApis / totalApis) * 100 : 0;
    
    setStatistics({
      total_apis: totalApis,
      granted_apis: grantedApis,
      denied_apis: totalApis - grantedApis,
      coverage
    });
  };

  // 保存权限
  const handleSave = async () => {
    if (!role) return;
    
    setSaving(true);
    try {
      // 找出变更的权限
      const changes = [];
      for (const [apiId, granted] of Object.entries(permissions)) {
        if (originalPermissions[apiId] !== granted) {
          changes.push({
            role_id: role.id,
            api_id: apiId,
            permission: 'access',
            action: granted ? 'grant' : 'revoke' as 'grant' | 'revoke'
          });
        }
      }
      
      if (changes.length > 0) {
        await PermissionAPI.batchUpdatePermissions({ updates: changes });
        message.success(`成功更新 ${changes.length} 个权限设置`);
        setOriginalPermissions({ ...permissions });
        onSave?.(role.id, permissions);
      } else {
        message.info('没有权限变更需要保存');
      }
    } catch (error) {
      message.error('保存权限失败');
      console.error('Save permissions error:', error);
    } finally {
      setSaving(false);
    }
  };

  // 获取方法标签颜色
  const getMethodColor = (method: string) => {
    const colors = {
      GET: 'blue',
      POST: 'green',
      PUT: 'orange',
      DELETE: 'red',
      PATCH: 'purple'
    };
    return colors[method as keyof typeof colors] || 'default';
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      active: { color: 'success', text: '活跃' },
      inactive: { color: 'default', text: '非活跃' },
      maintenance: { color: 'warning', text: '维护中' },
      deprecated: { color: 'error', text: '已弃用' }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 过滤API端点
  const filteredRoutes = apiRoutes.filter(route => {
    const matchesSearch = !searchText || 
      route.name.toLowerCase().includes(searchText.toLowerCase()) ||
      route.endpoint.toLowerCase().includes(searchText.toLowerCase()) ||
      route.description.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesMethod = !methodFilter || route.method === methodFilter;
    const matchesStatus = !statusFilter || route.status === statusFilter;
    
    return matchesSearch && matchesMethod && matchesStatus;
  });

  // 检查是否有未保存的变更
  const hasChanges = JSON.stringify(permissions) !== JSON.stringify(originalPermissions);

  // 表格列配置
  const columns = [
    {
      title: 'API端点',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ApiRoute) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.endpoint}</div>
        </div>
      )
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 80,
      render: (method: string) => (
        <Tag color={getMethodColor(method)}>{method}</Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '权限',
      key: 'permission',
      width: 120,
      render: (_: any, record: ApiRoute) => (
        <Tooltip title={record.is_public ? '公开路由，所有用户可访问' : ''}>
          <Switch
            checked={permissions[record.id] || false}
            onChange={(checked) => handlePermissionChange(record.id, checked)}
            checkedChildren={<CheckCircleOutlined />}
            unCheckedChildren={<CloseCircleOutlined />}
            disabled={record.is_public}  // 公开路由禁止修改
          />
          {record.is_public && (
            <Tag color="cyan" style={{ marginLeft: 4, fontSize: 10 }}>公开</Tag>
          )}
        </Tooltip>
      )
    }
  ];

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <SafetyOutlined />
          <span>权限管理 - {role?.name}</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={[
        <Button key="reset" onClick={() => handleBatchOperation('reset')}>
          重置
        </Button>,
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="save"
          type="primary"
          loading={saving}
          onClick={handleSave}
          disabled={!hasChanges}
          icon={<SaveOutlined />}
        >
          保存权限
        </Button>
      ]}
    >
      <div className="role-permission-modal">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="权限设置" key="permissions">
            {/* 统计信息 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="总API数"
                    value={statistics.total_apis}
                    prefix={<ApiOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="已授权"
                    value={statistics.granted_apis}
                    valueStyle={{ color: '#3f8600' }}
                    prefix={<CheckCircleOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="未授权"
                    value={statistics.denied_apis}
                    valueStyle={{ color: '#cf1322' }}
                    prefix={<CloseCircleOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="覆盖率"
                    value={statistics.coverage}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: statistics.coverage > 50 ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* 操作栏 */}
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <Search
                  placeholder="搜索API端点名称、路径或描述"
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ width: 250 }}
                  allowClear
                />
                <Select
                  placeholder="方法"
                  value={methodFilter}
                  onChange={setMethodFilter}
                  style={{ width: 100 }}
                  allowClear
                >
                  <Option value="GET">GET</Option>
                  <Option value="POST">POST</Option>
                  <Option value="PUT">PUT</Option>
                  <Option value="DELETE">DELETE</Option>
                  <Option value="PATCH">PATCH</Option>
                </Select>
                <Select
                  placeholder="状态"
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ width: 120 }}
                  allowClear
                >
                  <Option value="active">活跃</Option>
                  <Option value="inactive">非活跃</Option>
                  <Option value="maintenance">维护中</Option>
                  <Option value="deprecated">已弃用</Option>
                </Select>
              </Space>
              
              <Space>
                <Button
                  size="small"
                  onClick={() => handleBatchOperation('grant_all')}
                >
                  全部授权
                </Button>
                <Button
                  size="small"
                  onClick={() => handleBatchOperation('revoke_all')}
                >
                  全部撤销
                </Button>
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={loadApiRoutes}
                  loading={loading}
                >
                  刷新
                </Button>
              </Space>
            </div>

            {/* 变更提示 */}
            {hasChanges && (
              <Alert
                message="您有未保存的权限变更"
                description="请点击「保存权限」按钮保存您的更改，或点击「重置」按钮撤销更改。"
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {/* API权限表格 */}
            <Table
              columns={columns}
              dataSource={filteredRoutes}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
              size="small"
            />
          </TabPane>
        </Tabs>
      </div>

    </Modal>
  );
};

export default RolePermissionModal;
