import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Table, Button, Space, Popconfirm, message, Tag, Tooltip, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, DatabaseOutlined } from '@ant-design/icons';
import { Entity, EntityField, EntityDataRecord } from '../../../types/developer/entity';
import { entityAPI } from '../../../services/developer/entityAPI';
import DynamicRecordForm from './DynamicRecordForm';

interface EntityDataManagementPanelProps {
  entity: Entity | null;
  visible: boolean;
  onClose: () => void;
}

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

const EntityDataManagementPanel: React.FC<EntityDataManagementPanelProps> = ({
  entity,
  visible,
  onClose,
}) => {
  const [records, setRecords] = useState<EntityDataRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    limit: 10,
    total: 0,
    pages: 0,
    has_next: false,
    has_prev: false,
  });

  // 表单模态框状态
  const [formVisible, setFormVisible] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [editingRecord, setEditingRecord] = useState<EntityDataRecord | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  // 获取记录列表
  const fetchRecords = useCallback(async (page: number = 1, limit: number = 10) => {
    if (!entity) return;

    setLoading(true);
    try {
      const response = await entityAPI.getEntityData(entity.id, {
        page,
        limit,
      });

      if (response.code === 200) {
        setRecords(response.data.records);
        setPagination({
          page: response.data.pagination.page,
          limit: response.data.pagination.limit,
          total: response.data.pagination.total,
          pages: response.data.pagination.pages,
          has_next: response.data.pagination.has_next,
          has_prev: response.data.pagination.has_prev,
        });
      } else {
        message.error(response.message || '获取数据记录失败');
      }
    } catch (error) {
      console.error('获取数据记录失败:', error);
      message.error('获取数据记录失败');
    } finally {
      setLoading(false);
    }
  }, [entity]);


  // 当面板打开或实体变化时加载数据
  useEffect(() => {
    if (visible && entity) {
      fetchRecords(1, pagination.limit);
    }
  }, [visible, entity?.id]);

  // 处理创建记录
  const handleCreate = () => {
    setFormMode('create');
    setEditingRecord(null);
    setFormVisible(true);
  };

  // 处理编辑记录
  const handleEdit = (record: EntityDataRecord) => {
    setFormMode('edit');
    setEditingRecord(record);
    setFormVisible(true);
  };

  // 处理删除记录
  const handleDelete = async (recordId: string) => {
    if (!entity) return;

    try {
      const response = await entityAPI.deleteEntityRecord(entity.id, recordId);
      if (response.code === 200) {
        message.success('删除成功');
        fetchRecords(pagination.page, pagination.limit);
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error) {
      console.error('删除记录失败:', error);
      message.error('删除记录失败');
    }
  };

  // 处理表单提交
  const handleFormSubmit = async (data: Record<string, any>) => {
    if (!entity) return;

    setFormLoading(true);
    try {
      if (formMode === 'create') {
        const response = await entityAPI.createEntityRecord(entity.id, data);
        if (response.code === 201) {
          message.success('创建成功');
          setFormVisible(false);
          fetchRecords(1, pagination.limit);
        } else {
          message.error(response.message || '创建失败');
        }
      } else if (editingRecord) {
        const response = await entityAPI.updateEntityRecord(entity.id, editingRecord.id, data);
        if (response.code === 200) {
          message.success('更新成功');
          setFormVisible(false);
          fetchRecords(pagination.page, pagination.limit);
        } else {
          message.error(response.message || '更新失败');
        }
      }
    } catch (error: any) {
      console.error('提交失败:', error);
      message.error(error.message || '操作失败');
    } finally {
      setFormLoading(false);
    }
  };

  // 处理分页变化
  const handleTableChange = (paginationConfig: any) => {
    fetchRecords(paginationConfig.current, paginationConfig.pageSize);
  };

  // 生成表格列
  const generateColumns = () => {
    if (!entity || !entity.fields) return [];

    const columns: any[] = [];

    // 添加ID列
    columns.push({
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      ellipsis: true,
      render: (id: string) => (
        <Tooltip title={id}>
          <span style={{ fontFamily: 'monospace', fontSize: 12 }}>
            {id.substring(0, 8)}...
          </span>
        </Tooltip>
      ),
    });

    // 根据实体字段生成列
    entity.fields.forEach((field: EntityField) => {
      columns.push({
        title: field.displayName,
        dataIndex: field.name,
        key: field.name,
        ellipsis: true,
        render: (value: any) => renderFieldValue(value, field),
      });
    });

    // 添加创建时间列
    columns.push({
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-',
    });

    // 添加操作列
    columns.push({
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: EntityDataRecord) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            title="编辑"
          />
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              title="删除"
            />
          </Popconfirm>
        </Space>
      ),
    });

    return columns;
  };

  // 渲染字段值
  const renderFieldValue = (value: any, field: EntityField) => {
    if (value === null || value === undefined) {
      return <span style={{ color: '#999' }}>-</span>;
    }

    switch (field.type) {
      case 'boolean':
        return <Tag color={value ? 'green' : 'red'}>{value ? '是' : '否'}</Tag>;
      case 'date':
        try {
          return value ? new Date(value).toLocaleDateString('zh-CN') : '-';
        } catch {
          return String(value);
        }
      case 'datetime':
        try {
          return value ? new Date(value).toLocaleString('zh-CN') : '-';
        } catch {
          return String(value);
        }
      case 'number':
      case 'decimal':
        return <span style={{ fontFamily: 'monospace' }}>{value}</span>;
      case 'email':
        return <a href={`mailto:${value}`}>{value}</a>;
      case 'phone':
        return <a href={`tel:${value}`}>{value}</a>;
      case 'select':
        return <Tag color="blue">{value}</Tag>;
      case 'multiselect':
        if (Array.isArray(value)) {
          return (
            <Space size={[0, 4]} wrap>
              {value.map((v, i) => <Tag key={i} color="blue">{v}</Tag>)}
            </Space>
          );
        }
        return <Tag color="blue">{value}</Tag>;
      default:
        return String(value);
    }
  };

  return (
    <>
      <Modal
        title={
          <Space>
            <DatabaseOutlined />
            <span>数据管理 - {entity?.displayName}</span>
          </Space>
        }
        open={visible}
        onCancel={onClose}
        width={1000}
        footer={null}
        destroyOnHidden
      >
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <span style={{ color: '#666' }}>
              共 {pagination.total} 条记录
            </span>
          </Space>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchRecords(pagination.page, pagination.limit)}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              新建记录
            </Button>
          </Space>
        </div>

        {entity && entity.fields && entity.fields.length > 0 ? (
          <Table
            columns={generateColumns()}
            dataSource={records}
            rowKey="id"
            loading={loading}
            scroll={{ x: 'max-content' }}
            pagination={{
              current: pagination.page,
              pageSize: pagination.limit,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            onChange={handleTableChange}
            size="middle"
          />
        ) : (
          <Empty
            description="该实体暂无字段定义，请先添加字段"
            style={{ padding: '40px 0' }}
          />
        )}
      </Modal>

      {/* 创建/编辑表单模态框 */}
      {entity && (
        <DynamicRecordForm
          entity={entity}
          record={editingRecord}
          visible={formVisible}
          mode={formMode}
          loading={formLoading}
          onSubmit={handleFormSubmit}
          onCancel={() => setFormVisible(false)}
        />
      )}
    </>
  );
};

export default EntityDataManagementPanel;
