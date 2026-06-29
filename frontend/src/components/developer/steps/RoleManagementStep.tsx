/**
 * 角色管理步骤组件
 */

import React, { useState, useEffect } from 'react';
import {
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Row,
  Col,
  Table,
  Tabs,
  Switch
} from 'antd';
import { UnifiedCard, StatsCard } from '../common';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  SafetyOutlined,
  TeamOutlined,
  ExclamationCircleOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { RoleAPI, Role, CreateRoleRequest, UpdateRoleRequest } from '../../../services/developer/roleAPI';
import { UserAPI, User } from '../../../services/developer/userAPI';
import { RegistrationConfigAPI, RegistrationConfig, UpdateRegistrationConfigRequest } from '../../../services/developer/registrationConfigAPI';
import RolePermissionModal from '../role/RolePermissionModal';
import UserManagementModal from '../user/UserManagementModal';
import UserDetailModal from '../user/UserDetailModal';
import UserPermissionsModal from '../user/UserPermissionsModal';
import './RoleManagementStep.css';

const { Option } = Select;
const { TextArea } = Input;

interface RoleManagementStepProps {
  onNext?: () => void;
  onPrev?: () => void;
}

const RoleManagementStep: React.FC<RoleManagementStepProps> = ({ onNext, onPrev }) => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [usersLoading, setUsersLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [userModalVisible, setUserModalVisible] = useState(false);
  const [userDetailModalVisible, setUserDetailModalVisible] = useState(false);
  const [userPermissionsModalVisible, setUserPermissionsModalVisible] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUserForPermissions, setSelectedUserForPermissions] = useState<{ id: string; username: string } | null>(null);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [activeTab, setActiveTab] = useState<'roles' | 'users' | 'registration'>('roles');
  const [form] = Form.useForm();
  const [registrationConfig, setRegistrationConfig] = useState<RegistrationConfig | null>(null);
  const [registrationConfigLoading, setRegistrationConfigLoading] = useState(false);
  const [summary, setSummary] = useState({
    total_roles: 0,
    active_roles: 0,
    inactive_roles: 0,
    total_users: 0,
    avg_permissions_per_role: 0
  });



  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      active: { color: 'success', text: '活跃' },
      inactive: { color: 'default', text: '非活跃' },
      deprecated: { color: 'warning', text: '已弃用' },
      locked: { color: 'error', text: '已锁定' }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 加载角色列表
  const loadRoles = async () => {
    setLoading(true);
    try {
      const response = await RoleAPI.getRoles();
      console.log('RoleAPI response:', response); // 调试日志

      // RoleAPI.getRoles 返回的是 RoleListResponse 对象，直接包含 roles 和 summary
      setRoles(response.roles || []);
      setSummary(response.summary || {
        total_roles: 0,
        active_roles: 0,
        inactive_roles: 0,
        total_users: 0,
        avg_permissions_per_role: 0
      });

      console.log('Roles loaded:', response.roles?.length || 0); // 调试日志
    } catch (error) {
      message.error('加载角色列表失败');
      console.error('Load roles error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载用户列表
  const loadUsers = async () => {
    setUsersLoading(true);
    try {
      const data = await UserAPI.getUsersList({ page: 1, limit: 100 });
      console.log('UserAPI response:', data); // 调试日志

      // UserAPI.getUsersList 返回的是 UsersListResponse 对象，直接包含 users
      setUsers(data.users || []);

      console.log('Users loaded:', data.users?.length || 0); // 调试日志
    } catch (error) {
      message.error('加载用户列表失败');
      console.error('Load users error:', error);
    } finally {
      setUsersLoading(false);
    }
  };

  // 加载注册配置
  const loadRegistrationConfig = async () => {
    setRegistrationConfigLoading(true);
    try {
      const config = await RegistrationConfigAPI.getRegistrationConfig();
      setRegistrationConfig(config);
      console.log('Registration config loaded:', config);
    } catch (error) {
      message.error('加载注册配置失败');
      console.error('加载注册配置失败:', error);
    } finally {
      setRegistrationConfigLoading(false);
    }
  };

  useEffect(() => {
    loadRoles();
  }, []);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'registration') {
      loadRegistrationConfig();
    }
  }, [activeTab]);

  // 打开创建/编辑模态框
  const openModal = (role?: Role) => {
    setEditingRole(role || null);
    setModalVisible(true);
    if (role) {
      form.setFieldsValue({
        name: role.name,
        code: role.code,
        description: role.description,
        status: role.status
      });
    } else {
      form.resetFields();
    }
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingRole(null);
    form.resetFields();
  };

  // 保存角色
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRole) {
        // 更新角色
        const updateData: UpdateRoleRequest = {
          name: values.name,
          description: values.description,
          status: values.status
        };
        await RoleAPI.updateRole(editingRole.id, updateData);
        message.success('角色更新成功');
      } else {
        // 创建角色
        const createData: CreateRoleRequest = {
          name: values.name,
          code: values.code,
          description: values.description,
          status: values.status || 'active'
        };
        await RoleAPI.createRole(createData);
        message.success('角色创建成功');
      }
      
      closeModal();
      loadRoles();
    } catch (error) {
      message.error(editingRole ? '角色更新失败' : '角色创建失败');
      console.error('Save role error:', error);
    }
  };

  // 删除角色
  const handleDelete = async (roleId: string) => {
    try {
      await RoleAPI.deleteRole(roleId);
      message.success('角色删除成功');
      loadRoles();
    } catch (error) {
      message.error('角色删除失败');
      console.error('Delete role error:', error);
    }
  };

  // 打开权限管理
  const openPermissionModal = (role: Role) => {
    setSelectedRole(role);
    setPermissionModalVisible(true);
  };

  // 关闭权限管理
  const closePermissionModal = () => {
    setPermissionModalVisible(false);
    setSelectedRole(null);
  };

  // 权限保存成功回调
  const handlePermissionSave = (roleId: string, permissions: Record<string, boolean>) => {
    // 可以在这里更新角色的权限数量显示
    loadRoles();
  };

  // 打开用户创建模态框
  const openUserModal = () => {
    setUserModalVisible(true);
  };

  // 关闭用户创建模态框
  const closeUserModal = () => {
    setUserModalVisible(false);
  };

  // 打开用户详情模态框
  const openUserDetailModal = (userId: number) => {
    setSelectedUserId(userId);
    setUserDetailModalVisible(true);
  };

  // 关闭用户详情模态框
  const closeUserDetailModal = () => {
    setUserDetailModalVisible(false);
    setSelectedUserId(null);
  };

  // 打开用户权限模态框
  const openUserPermissionsModal = (user: User) => {
    setSelectedUserForPermissions({
      id: String(user.id),
      username: user.username
    });
    setUserPermissionsModalVisible(true);
  };

  // 关闭用户权限模态框
  const closeUserPermissionsModal = () => {
    setUserPermissionsModalVisible(false);
    setSelectedUserForPermissions(null);
  };

  // 用户创建成功回调
  const handleUserCreateSuccess = () => {
    loadUsers();
    loadRoles(); // 重新加载角色以更新用户数量
  };

  // 删除用户
  const handleDeleteUser = async (userId: number) => {
    try {
      await UserAPI.deleteUser(userId);
      message.success('用户删除成功');
      loadUsers();
      loadRoles(); // 重新加载角色以更新用户数量
    } catch (error) {
      message.error('删除用户失败');
      console.error('Delete user error:', error);
    }
  };

  // 更新注册配置
  const handleUpdateRegistrationConfig = async (values: UpdateRegistrationConfigRequest) => {
    setRegistrationConfigLoading(true);
    try {
      await RegistrationConfigAPI.updateRegistrationConfig(values);
      message.success('注册配置更新成功');
      loadRegistrationConfig(); // 重新加载配置
    } catch (error) {
      message.error('更新注册配置失败');
      console.error('Update registration config error:', error);
    } finally {
      setRegistrationConfigLoading(false);
    }
  };

  // 切换用户状态
  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await UserAPI.updateUserStatus(userId, !currentStatus);
      message.success(`用户已${!currentStatus ? '启用' : '禁用'}`);
      loadUsers();
    } catch (error) {
      message.error('更新用户状态失败');
      console.error('Toggle user status error:', error);
    }
  };

  // 角色表格列配置
  const roleColumns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Role) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>代码: {record.code}</div>
        </div>
      )
    },

    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '用户数量',
      dataIndex: 'user_count',
      key: 'user_count',
      render: (count: number) => (
        <Badge count={count} showZero color="#52c41a" />
      )
    },
    {
      title: '权限数量',
      dataIndex: 'permission_count',
      key: 'permission_count',
      render: (count: number) => (
        <Badge count={count || 0} showZero color="#1890ff" />
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text || '-'}</span>
        </Tooltip>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Role) => (
        <Space size="small">
          <Tooltip title="编辑角色">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openModal(record)}
            />
          </Tooltip>
          <Tooltip title="权限管理">
            <Button
              type="text"
              icon={<SafetyOutlined />}
              onClick={() => openPermissionModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个角色吗？"
            description="删除后将无法恢复，关联用户将被重新分配。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
            icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
          >
            <Tooltip title="删除角色">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 用户表格列配置
  const userColumns = [
    {
      title: '用户信息',
      key: 'userInfo',
      render: (_: any, record: User) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.username}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.email}</div>
          {record.real_name && (
            <div style={{ fontSize: '12px', color: '#999' }}>{record.real_name}</div>
          )}
        </div>
      )
    },
    {
      title: '角色',
      key: 'role',
      render: (_: any, record: User) => (
        <Tag color="blue">{record.role.name}</Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => openUserDetailModal(record.id)}
            />
          </Tooltip>
          <Tooltip title="查看权限">
            <Button
              type="text"
              icon={<SafetyOutlined />}
              onClick={() => openUserPermissionsModal(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_active ? '禁用用户' : '启用用户'}>
            <Button
              type="text"
              icon={record.is_active ? <ExclamationCircleOutlined /> : <UserOutlined />}
              onClick={() => handleToggleUserStatus(record.id, record.is_active)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个用户吗？"
            description="删除后将无法恢复。"
            onConfirm={() => handleDeleteUser(record.id)}
            okText="确定"
            cancelText="取消"
            icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
          >
            <Tooltip title="删除用户">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div className="role-management-step">
      {/* 步骤头部 */}
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <TeamOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">角色管理</h2>
              <p className="unified-step-description">配置用户角色和权限，管理系统访问控制</p>
            </div>
          </div>
        </div>
      </UnifiedCard>

      {/* 统计信息 */}
      <div className="step-statistics">
        <StatsCard
          title="总角色数"
          value={summary.total_roles}
          icon={<TeamOutlined />}
          color="primary"
        />
        <StatsCard
          title="活跃角色"
          value={summary.active_roles}
          icon={<UserOutlined />}
          color="success"
        />
        <StatsCard
          title="总用户数"
          value={summary.total_users}
          icon={<TeamOutlined />}
          color="info"
        />
        <StatsCard
          title="平均权限数"
          value={summary.avg_permissions_per_role}
          precision={1}
          icon={<SafetyOutlined />}
          color="warning"
        />
      </div>

      {/* 角色和用户管理标签页 */}
      <div className="role-tabs-container">
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as 'roles' | 'users')}
          items={[
            {
              key: 'roles',
              label: (
                <Space>
                  <TeamOutlined />
                  <span>角色管理</span>
                </Space>
              ),
              forceRender: true,
              children: (
                <UnifiedCard>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => openModal()}
                    >
                      创建角色
                    </Button>
                  </div>
                  <Table
                    columns={roleColumns}
                    dataSource={roles}
                    rowKey="id"
                    loading={loading}
                    size="middle"
                    bordered={false}
                    pagination={{
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total) => `共 ${total} 个角色`
                    }}
                  />
                </UnifiedCard>
              )
            },
            {
              key: 'users',
              label: (
                <Space>
                  <UserOutlined />
                  <span>用户管理</span>
                </Space>
              ),
              forceRender: true,
              children: (
                <UnifiedCard>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={openUserModal}
                    >
                      创建用户
                    </Button>
                  </div>
                  <Table
                    columns={userColumns}
                    dataSource={users}
                    rowKey="id"
                    loading={usersLoading}
                    size="middle"
                    bordered={false}
                    pagination={{
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total) => `共 ${total} 个用户`
                    }}
                  />
                </UnifiedCard>
              )
            },
            {
              key: 'registration',
              label: (
                <Space>
                  <SafetyOutlined />
                  <span>注册配置</span>
                </Space>
              ),
              forceRender: true,
              children: (
                <UnifiedCard>
                  {registrationConfig && (
                    <Form
                      layout="vertical"
                      initialValues={{
                        default_role_code: registrationConfig.default_role_code,
                        allow_public_registration: registrationConfig.allow_public_registration
                      }}
                      onFinish={handleUpdateRegistrationConfig}
                    >
                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item
                            label="默认注册角色"
                            name="default_role_code"
                            rules={[{ required: true, message: '请选择默认注册角色' }]}
                          >
                            <Select placeholder="请选择默认注册角色">
                              {registrationConfig.available_roles.map(role => (
                                <Option key={role.code} value={role.code}>
                                  {role.name} ({role.code}) - {role.user_count} 个用户
                                </Option>
                              ))}
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            label="允许公开注册"
                            name="allow_public_registration"
                            valuePropName="checked"
                          >
                            <Switch
                              checkedChildren="允许"
                              unCheckedChildren="禁止"
                            />
                          </Form.Item>
                        </Col>
                      </Row>

                      {registrationConfig.default_role_info && (
                        <div style={{ marginBottom: 16, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
                          <h4>当前默认角色信息：</h4>
                          <p><strong>角色名称：</strong>{registrationConfig.default_role_info.name}</p>
                          <p><strong>角色代码：</strong>{registrationConfig.default_role_info.code}</p>
                          <p><strong>角色描述：</strong>{registrationConfig.default_role_info.description}</p>

                          {registrationConfig.default_role_fields && registrationConfig.default_role_fields.length > 0 && (
                            <div style={{ marginTop: 16 }}>
                              <h5>注册表单字段（基于角色实体动态生成）：</h5>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px', marginTop: 8 }}>
                                {registrationConfig.default_role_fields.map((field: any, index: number) => (
                                  <div key={index} style={{
                                    padding: '8px 12px',
                                    backgroundColor: '#fff',
                                    border: '1px solid #d9d9d9',
                                    borderRadius: '4px',
                                    fontSize: '12px'
                                  }}>
                                    <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
                                      {field.display_name}
                                      {field.required && <span style={{ color: '#ff4d4f' }}> *</span>}
                                    </div>
                                    <div style={{ color: '#666', marginTop: '2px' }}>
                                      {field.name} ({field.type})
                                    </div>
                                    {field.description && (
                                      <div style={{ color: '#999', marginTop: '2px', fontSize: '11px' }}>
                                        {field.description}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                                💡 这些字段将自动添加到用户注册表单中，用户注册时需要填写这些信息
                              </div>
                            </div>
                          )}

                          {(!registrationConfig.default_role_fields || registrationConfig.default_role_fields.length === 0) && (
                            <div style={{ marginTop: 16, padding: '8px 12px', backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: '4px' }}>
                              <div style={{ fontSize: '12px', color: '#d46b08' }}>
                                ⚠️ 当前默认角色没有对应的实体字段，注册表单将只包含基础认证字段（用户名、邮箱、密码）
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      <Form.Item>
                        <Button
                          type="primary"
                          htmlType="submit"
                          loading={registrationConfigLoading}
                        >
                          保存配置
                        </Button>
                      </Form.Item>
                    </Form>
                  )}
                </UnifiedCard>
              )
            }
          ]}
        />
      </div>

      {/* 创建/编辑角色模态框 */}
      <Modal
        title={editingRole ? '编辑角色' : '创建角色'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={closeModal}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ status: 'active' }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="角色名称"
                name="name"
                rules={[{ required: true, message: '请输入角色名称' }]}
              >
                <Input placeholder="请输入角色名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="角色代码"
                name="code"
                rules={[
                  { required: true, message: '请输入角色代码' },
                  { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线' }
                ]}
              >
                <Input 
                  placeholder="请输入角色代码" 
                  disabled={!!editingRole}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="角色状态"
            name="status"
            rules={[{ required: true, message: '请选择角色状态' }]}
          >
            <Select placeholder="请选择角色状态">
              <Option value="active">活跃</Option>
              <Option value="inactive">非活跃</Option>
              <Option value="deprecated">已弃用</Option>
              <Option value="locked">已锁定</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="角色描述"
            name="description"
          >
            <TextArea
              rows={3}
              placeholder="请输入角色描述"
              maxLength={200}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 权限管理模态框 */}
      <RolePermissionModal
        visible={permissionModalVisible}
        role={selectedRole}
        onClose={closePermissionModal}
        onSave={handlePermissionSave}
      />

      {/* 用户管理模态框 */}
      <UserManagementModal
        visible={userModalVisible}
        onCancel={closeUserModal}
        onSuccess={handleUserCreateSuccess}
      />

      {/* 用户详情模态框 */}
      <UserDetailModal
        visible={userDetailModalVisible}
        userId={selectedUserId}
        onClose={closeUserDetailModal}
      />

      {/* 用户权限模态框 */}
      <UserPermissionsModal
        visible={userPermissionsModalVisible}
        userId={selectedUserForPermissions?.id || null}
        username={selectedUserForPermissions?.username}
        onCancel={closeUserPermissionsModal}
      />

      {/* 底部操作按钮 */}
      <div className="step-actions">
        <Space>
          {onPrev && (
            <Button onClick={onPrev}>
              上一步
            </Button>
          )}
          {onNext && (
            <Button type="primary" onClick={onNext}>
              下一步
            </Button>
          )}
        </Space>
      </div>
    </div>
  );
};

export default RoleManagementStep;
