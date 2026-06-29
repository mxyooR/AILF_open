/**
 * 用户详情模态框组件
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Descriptions,
  Tag,
  Spin,
  message,
  Avatar,
  Space,
  Typography,
  Divider,
  Card,
  Row,
  Col,
  Button,
  Form,
  Input,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  SafetyOutlined,
  EditOutlined,
  KeyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  PictureOutlined,
  FileTextOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { UserAPI, User } from '../../../services/developer/userAPI';

const { Title, Text } = Typography;

interface UserDetailModalProps {
  visible: boolean;
  userId: number | null;
  onClose: () => void;
}

const UserDetailModal: React.FC<UserDetailModalProps> = ({
  visible,
  userId,
  onClose
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordForm] = Form.useForm();

  // 加载用户详情
  const loadUserDetail = async (id: number) => {
    setLoading(true);
    try {
      const userDetail = await UserAPI.getUserDetail(id);
      setUser(userDetail);
      console.log('Loaded user detail:', userDetail);
    } catch (error) {
      message.error('加载用户详情失败');
      console.error('Load user detail error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 当模态框打开且有用户ID时加载详情
  useEffect(() => {
    if (visible && userId) {
      loadUserDetail(userId);
    } else {
      setUser(null);
    }
  }, [visible, userId]);

  // 打开修改密码模态框
  const openPasswordModal = () => {
    setPasswordModalVisible(true);
    passwordForm.resetFields();
  };

  // 关闭修改密码模态框
  const closePasswordModal = () => {
    setPasswordModalVisible(false);
    passwordForm.resetFields();
  };

  // 处理密码修改
  const handlePasswordUpdate = async () => {
    if (!user) return;

    try {
      const values = await passwordForm.validateFields();
      setPasswordLoading(true);

      await UserAPI.updateUserPassword(user.id, values.newPassword);
      message.success('密码修改成功');
      closePasswordModal();

      // 重新加载用户详情
      loadUserDetail(user.id);
    } catch (error: any) {
      if (error.response?.data?.message) {
        message.error(`密码修改失败: ${error.response.data.message}`);
      } else {
        message.error('密码修改失败');
      }
      console.error('Update password error:', error);
    } finally {
      setPasswordLoading(false);
    }
  };

  // 格式化日期
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '从未';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 获取用户状态标签
  const getUserStatusTag = (isActive: boolean) => {
    return (
      <Tag color={isActive ? 'success' : 'default'}>
        {isActive ? '启用' : '禁用'}
      </Tag>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <UserOutlined />
          <span>用户详情</span>
          {user && (
            <Space style={{ marginLeft: 16 }}>
              <Tooltip title="修改密码">
                <Button
                  type="primary"
                  size="small"
                  icon={<KeyOutlined />}
                  onClick={openPasswordModal}
                >
                  修改密码
                </Button>
              </Tooltip>
            </Space>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1000}
      destroyOnClose
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '16px' }}>正在加载用户详情...</div>
        </div>
      ) : user ? (
        <div>
          {/* 用户基本信息卡片 */}
          <Card style={{ marginBottom: 16 }}>
            <Row gutter={24}>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Avatar 
                    size={80} 
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#1890ff' }}
                  >
                    {user.real_name?.[0] || user.username[0]}
                  </Avatar>
                  <div style={{ marginTop: 8 }}>
                    {getUserStatusTag(user.is_active)}
                  </div>
                </div>
              </Col>
              <Col span={18}>
                <Title level={4} style={{ marginBottom: 8 }}>
                  {user.real_name || user.username}
                </Title>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    <UserOutlined style={{ color: '#666' }} />
                    <Text>用户名: {user.username}</Text>
                  </Space>
                  <Space>
                    <MailOutlined style={{ color: '#666' }} />
                    <Text>邮箱: {user.email}</Text>
                  </Space>
                  {user.phone && (
                    <Space>
                      <PhoneOutlined style={{ color: '#666' }} />
                      <Text>电话: {user.phone}</Text>
                    </Space>
                  )}
                  <Space>
                    <SafetyOutlined style={{ color: '#666' }} />
                    <Text>角色: </Text>
                    <Tag color="blue">{user.role.name}</Tag>
                  </Space>
                </Space>
              </Col>
            </Row>
          </Card>

          <Divider orientation="left">详细信息</Divider>

          {/* 详细信息 */}
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="用户ID" span={1}>
              <Text copyable>{user.id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="用户名" span={1}>
              <Text copyable>{user.username}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="真实姓名" span={1}>
              {user.real_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱地址" span={1}>
              <Text copyable>{user.email}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="手机号码" span={1}>
              <Text copyable={!!user.phone}>{user.phone || '-'}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="账户状态" span={1}>
              {getUserStatusTag(user.is_active)}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱验证" span={1}>
              <Space>
                {user.is_verified ? (
                  <Tag color="success" icon={<CheckCircleOutlined />}>已验证</Tag>
                ) : (
                  <Tag color="warning" icon={<CloseCircleOutlined />}>未验证</Tag>
                )}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="头像URL" span={1}>
              <Space>
                <PictureOutlined style={{ color: '#666' }} />
                {user.avatar_url ? (
                  <Text copyable ellipsis style={{ maxWidth: 200 }}>{user.avatar_url}</Text>
                ) : '-'}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="个人简介" span={2}>
              <Space>
                <FileTextOutlined style={{ color: '#666' }} />
                {user.bio || '-'}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="用户设置" span={2}>
              <Space>
                <SettingOutlined style={{ color: '#666' }} />
                {user.settings ? (
                  <Text code copyable ellipsis style={{ maxWidth: 400 }}>{user.settings}</Text>
                ) : '-'}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="密码哈希" span={2}>
              <Space>
                <KeyOutlined style={{ color: '#666' }} />
                {user.password_hash ? (
                  <Text code copyable ellipsis style={{ maxWidth: 400 }}>{user.password_hash}</Text>
                ) : '-'}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="所属角色" span={2}>
              <Space>
                <Tag color="blue">{user.role.name}</Tag>
                <Text type="secondary">({user.role.code})</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="角色描述" span={2}>
              {user.role.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={1}>
              <Space>
                <CalendarOutlined style={{ color: '#666' }} />
                {formatDate(user.created_at)}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="更新时间" span={1}>
              <Space>
                <CalendarOutlined style={{ color: '#666' }} />
                {formatDate(user.updated_at)}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="最后登录" span={2}>
              <Space>
                <ClockCircleOutlined style={{ color: '#666' }} />
                {formatDate(user.last_login)}
              </Space>
            </Descriptions.Item>
          </Descriptions>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Text type="secondary">未找到用户信息</Text>
        </div>
      )}

      {/* 修改密码模态框 */}
      <Modal
        title={
          <Space>
            <KeyOutlined />
            <span>修改密码</span>
          </Space>
        }
        open={passwordModalVisible}
        onOk={handlePasswordUpdate}
        onCancel={closePasswordModal}
        confirmLoading={passwordLoading}
        okText="确认修改"
        cancelText="取消"
        width={500}
        destroyOnClose
      >
        <Form
          form={passwordForm}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            label="新密码"
            name="newPassword"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码长度不能少于6位' },
              { max: 50, message: '密码长度不能超过50位' }
            ]}
          >
            <Input.Password
              placeholder="请输入新密码（至少6位）"
              autoComplete="new-password"
            />
          </Form.Item>

          <Form.Item
            label="确认密码"
            name="confirmPassword"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              placeholder="请再次输入新密码"
              autoComplete="new-password"
            />
          </Form.Item>

          <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f6f8fa', borderRadius: 6 }}>
            <Space>
              <InfoCircleOutlined style={{ color: '#1890ff' }} />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                密码修改后，用户需要使用新密码重新登录
              </Text>
            </Space>
          </div>
        </Form>
      </Modal>
    </Modal>
  );
};

export default UserDetailModal;
