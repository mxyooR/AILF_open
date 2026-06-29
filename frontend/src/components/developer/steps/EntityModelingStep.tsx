import React, { useState, useEffect, useRef } from 'react';
import { Button, Modal, Form, Input, Select, Space, Tag, Popconfirm, message, Tabs, Table, Alert, Switch } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, LinkOutlined, DatabaseOutlined, RocketOutlined, TableOutlined } from '@ant-design/icons';
import { UnifiedCard } from '../common';
import { useEntityManagement } from '../../../hooks/developer/useEntityManagement';
import { templateApplicationService } from '../../../services/developer/templateApplicationService';
import { scenarioAPI } from '../../../services/developer/scenarioAPI';
import { Entity, EntityField, EntityRelationship } from '../../../types/developer/entity';
import EntityDataManagementPanel from './EntityDataManagementPanel';

const { Option } = Select;

interface EntityModelingStepProps {
  onNext: () => void;
  onPrev: () => void;
  scenarioId?: string;
}

const EntityModelingStep: React.FC<EntityModelingStepProps> = ({
  onNext,
  onPrev,
  scenarioId
}) => {
  const {
    entities,
    loading,
    createEntity,
    createEntitySilently,
    updateEntity,
    deleteEntity,
    getEntityDetail,
    createRelationship,
    getRelationships,
    deleteRelationship,
    updateRelationship,
    refreshEntities
  } = useEntityManagement();

  const [activeTab, setActiveTab] = useState('entities');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view' | 'fields'>('create');
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [form] = Form.useForm();
  const [templateEntitiesLoaded, setTemplateEntitiesLoaded] = useState(false);

  // 字段管理相关状态
  const [fieldModalVisible, setFieldModalVisible] = useState(false);
  const [fieldModalType, setFieldModalType] = useState<'create' | 'edit'>('create');
  const [editingField, setEditingField] = useState<EntityField | null>(null);
  const [fieldForm] = Form.useForm();

  // 关系管理相关状态
  const [relationships, setRelationships] = useState<EntityRelationship[]>([]);
  const [relationshipModalVisible, setRelationshipModalVisible] = useState(false);
  const [relationshipModalType, setRelationshipModalType] = useState<'create' | 'edit'>('create');
  const [editingRelationship, setEditingRelationship] = useState<EntityRelationship | null>(null);
  const [relationshipForm] = Form.useForm();
  const [relationshipLoading, setRelationshipLoading] = useState(false);
  const isMountedRef = useRef(true);

  // 数据管理相关状态
  const [dataManagementVisible, setDataManagementVisible] = useState(false);
  const [dataManagementEntity, setDataManagementEntity] = useState<Entity | null>(null);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 初始化时加载实体列表
  useEffect(() => {
    refreshEntities();
  }, [refreshEntities]);

  // 初始化模板实体数据
  useEffect(() => {
    const loadTemplateEntities = async () => {
      if (templateEntitiesLoaded) return;

      const templateEntities = templateApplicationService.getEntitiesForStep();
      const appliedTemplateInfo = templateApplicationService.getAppliedTemplateInfo();

      if (templateEntities.length > 0 && appliedTemplateInfo) {
        try {
          // 强制获取最新的场景ID，重试机制确保获取成功
          let currentScenarioId = null;
          let validScenario = null;
          
          for (let i = 0; i < 5; i++) {
            try {
              console.log(`🔄 第${i+1}次尝试获取最新场景ID...`);
              const currentScenarioResponse = await scenarioAPI.getCurrent(true);
              const scenario = currentScenarioResponse.data.scenario;
              
              if (scenario?.id) {
                currentScenarioId = scenario.id;
                validScenario = scenario;
                console.log(`✅ 成功获取场景ID: ${currentScenarioId}`, scenario);
                break;
              } else {
                console.warn(`⚠️ 第${i+1}次获取的场景无效:`, scenario);
              }
            } catch (error) {
              console.warn(`❌ 第${i+1}次获取场景ID失败:`, error);
            }
            
            if (i < 4) {
              await new Promise(resolve => setTimeout(resolve, 1500));
            }
          }
          
          console.log('🎯 动态获取的场景ID:', currentScenarioId);
          console.log('📝 传入的scenarioId prop:', scenarioId);
          console.log('🔍 获取到的完整场景信息:', validScenario);

          // 优先使用动态获取的场景ID
          const finalScenarioId = currentScenarioId || scenarioId;
          
          if (!finalScenarioId) {
            throw new Error('无法获取有效的场景ID，请刷新页面重试');
          }
          
          console.log('✅ 最终使用的场景ID:', finalScenarioId);

          // 先获取当前已有的实体列表，避免重复创建
          let existingEntities: Entity[] = [];
          try {
            await refreshEntities();
            existingEntities = entities;
          } catch (error) {
            console.warn('获取现有实体列表失败，继续创建:', error);
          }

          // 将模板实体转换为系统实体格式并创建（跳过已存在的）
          let createdCount = 0;
          let skippedCount = 0;
          
          for (const templateEntity of templateEntities) {
            const entityName = templateEntity.name || '';
            const displayName = templateEntity.display_name || templateEntity.displayName || '';
            
            // 检查实体是否已存在（根据name或displayName）
            const existsAlready = existingEntities.some(existing => 
              existing.name === entityName || 
              existing.displayName === displayName ||
              existing.name === displayName.toLowerCase().replace(/\s+/g, '_')
            );

            if (existsAlready) {
              console.log(`⏭️ 实体 ${displayName} 已存在，跳过创建`);
              skippedCount++;
              continue;
            }

            const entityData = {
              name: entityName,
              displayName: displayName,
              description: templateEntity.description || '',
              fields: templateEntity.fields?.map((field: any) => ({
                name: field.name,
                displayName: field.display_name || field.displayName,
                type: field.type,
                required: field.required || false,
                unique: field.unique_field || field.unique || false,
                defaultValue: field.default_value || field.defaultValue,
                options: field.options,
                validation: field.validation
              })) || []
            };

            console.log(`🔄 创建实体 ${entityData.displayName}`);
            if (isMountedRef.current) {
              // 使用静默创建方法，避免在console中显示预期的冲突错误
              const result = await createEntitySilently(entityData);
              
              if (result.success) {
                console.log(`✅ 实体 ${entityData.displayName} 创建成功`);
                createdCount++;
              } else if (result.conflict) {
                console.log(`⚠️ 实体 ${entityData.displayName} 已存在，跳过创建`);
                skippedCount++;
              } else {
                console.error(`❌ 创建实体 ${entityData.displayName} 失败:`, result.error);
                // 对于非冲突错误，我们仍然抛出异常
                throw new Error(result.error);
              }
            }
          }

          if (isMountedRef.current) {
            // 显示更详细的结果信息
            if (createdCount > 0 && skippedCount > 0) {
              message.success(`模板"${appliedTemplateInfo.template_key}"处理完成：创建了 ${createdCount} 个新实体，跳过了 ${skippedCount} 个已存在的实体`);
            } else if (createdCount > 0) {
              message.success(`已从模板"${appliedTemplateInfo.template_key}"创建 ${createdCount} 个实体`);
            } else if (skippedCount > 0) {
              message.info(`模板"${appliedTemplateInfo.template_key}"的 ${skippedCount} 个实体已存在，无需重复创建`);
            } else {
              message.info(`模板"${appliedTemplateInfo.template_key}"处理完成`);
            }
            
            setTemplateEntitiesLoaded(true);
            // 创建完实体后重新刷新列表
            await refreshEntities();
          }
        } catch (error) {
          console.error('加载模板实体失败:', error);
          // 如果是重复名称错误，说明数据已存在，不需要显示错误
          if (error instanceof Error && error.message.includes('实体名称已存在')) {
            console.log('实体已存在，跳过创建');
            if (isMountedRef.current) {
              setTemplateEntitiesLoaded(true);
            }
          } else if (isMountedRef.current) {
            message.error('加载模板实体失败，请手动创建');
          }
        }
      }
    };

    loadTemplateEntities();
  }, [createEntity, templateEntitiesLoaded, refreshEntities, scenarioId]);

  // 监听标签切换，加载关系数据
  useEffect(() => {
    if (activeTab === 'relationships' && entities.length > 0) {
      loadRelationships();
    }
  }, [activeTab, entities]);

  // 实体表格列定义
  const entityColumns = [
    {
      title: '实体名称',
      dataIndex: 'displayName',
      key: 'displayName',
      render: (text: string, record: Entity) => (
        <Space>
          <span style={{ fontWeight: 600 }}>{text}</span>
          <Tag color="blue">{record.name}</Tag>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '字段数量',
      dataIndex: 'fields',
      key: 'fieldCount',
      render: (fields: EntityField[]) => (
        <Tag color="green">{fields?.length || 0} 个字段</Tag>
      ),
    },
    {
      title: '关系数量',
      dataIndex: 'relationships',
      key: 'relationshipCount',
      render: (relationships: EntityRelationship[]) => (
        <Tag color="orange">{relationships?.length || 0} 个关系</Tag>
      ),
    },
    {
      title: '角色实体',
      dataIndex: 'isRole',
      key: 'isRole',
      render: (isRole: boolean) => (
        <Tag color={isRole ? 'purple' : 'default'}>
          {isRole ? '角色实体' : '普通实体'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 240,
      fixed: 'right' as const,
      render: (_: any, record: Entity) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewEntity(record)}
            title="查看"
          />
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditEntity(record)}
            title="编辑"
          />
          <Button
            type="link"
            size="small"
            icon={<TableOutlined />}
            onClick={() => handleManageData(record)}
            title="数据"
          />
          <Button
            type="link"
            size="small"
            icon={<LinkOutlined />}
            onClick={() => handleManageRelationships(record)}
            title="关系"
          />
          <Button
            type="link"
            size="small"
            icon={<DatabaseOutlined />}
            onClick={() => handleManageFields(record)}
            title="字段"
          />
          <Popconfirm
            title="确定要删除这个实体吗？"
            onConfirm={() => handleDeleteEntity(record.id)}
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
    },
  ];

  // 加载实体列表
  useEffect(() => {
    refreshEntities();
  }, [refreshEntities]);

  // 处理创建实体
  const handleCreateEntity = () => {
    setModalType('create');
    setSelectedEntity(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  // 处理编辑实体
  const handleEditEntity = (entity: Entity) => {
    setModalType('edit');
    setSelectedEntity(entity);
    form.setFieldsValue({
      displayName: entity.displayName,
      description: entity.description,
      icon: entity.icon,
      isRole: entity.isRole || false,
    });
    setIsModalVisible(true);
  };

  // 处理查看实体
  const handleViewEntity = async (entity: Entity) => {
    try {
      const detail = await getEntityDetail(entity.id);
      setModalType('view');
      setSelectedEntity(detail);
      form.setFieldsValue({
        displayName: detail.displayName,
        description: detail.description,
        icon: detail.icon,
      });
      setIsModalVisible(true);
    } catch (error) {
      message.error('获取实体详情失败');
    }
  };

  // 处理删除实体
  const handleDeleteEntity = async (entityId: string) => {
    try {
      await deleteEntity(entityId);
      message.success('实体删除成功');
      refreshEntities();
    } catch (error) {
      message.error('删除实体失败');
    }
  };

  // 处理管理关系
  const handleManageRelationships = (entity: Entity) => {
    setSelectedEntity(entity);
    setActiveTab('relationships');
  };

  // 处理数据管理
  const handleManageData = (entity: Entity) => {
    setDataManagementEntity(entity);
    setDataManagementVisible(true);
  };

  // 处理字段管理
  const handleManageFields = (entity: Entity) => {
    setSelectedEntity(entity);
    setModalType('fields');
    setIsModalVisible(true);
  };

  // 处理创建字段
  const handleCreateField = () => {
    setFieldModalType('create');
    setEditingField(null);
    fieldForm.resetFields();
    setFieldModalVisible(true);
  };

  // 处理编辑字段
  const handleEditField = (field: EntityField) => {
    setFieldModalType('edit');
    setEditingField(field);
    fieldForm.setFieldsValue({
      name: field.name,
      displayName: field.displayName,
      type: field.type,
      required: field.required,
      unique: field.unique,
      defaultValue: field.defaultValue,
      options: field.options?.join('\n') || '',
      validation: field.validation
    });
    setFieldModalVisible(true);
  };

  // 处理删除字段
  const handleDeleteField = async (fieldId: string) => {
    try {
      // TODO: 调用删除字段API
      message.success('字段删除成功');
      // 刷新实体详情
      if (selectedEntity) {
        const detail = await getEntityDetail(selectedEntity.id);
        setSelectedEntity(detail);
      }
    } catch (error) {
      message.error('字段删除失败');
    }
  };

  // 关系管理处理函数
  const loadRelationships = async () => {
    if (activeTab !== 'relationships') return;

    setRelationshipLoading(true);
    try {
      // 获取所有实体的关系
      const allRelationships: EntityRelationship[] = [];
      for (const entity of entities) {
        const result = await getRelationships(entity.id);
        if (result && result.length > 0) {
          allRelationships.push(...result);
        }
      }
      setRelationships(allRelationships);
    } catch (error) {
      message.error('加载关系失败');
    } finally {
      setRelationshipLoading(false);
    }
  };

  // 处理创建关系
  const handleCreateRelationship = () => {
    setRelationshipModalType('create');
    setEditingRelationship(null);
    relationshipForm.resetFields();
    setRelationshipModalVisible(true);
  };

  // 处理编辑关系
  const handleEditRelationship = (relationship: EntityRelationship) => {
    setRelationshipModalType('edit');
    setEditingRelationship(relationship);
    relationshipForm.setFieldsValue({
      name: relationship.name,
      sourceEntity: relationship.sourceEntity,
      targetEntity: relationship.targetEntity,
      type: relationship.type,
      foreignKey: relationship.foreignKey,
      cascadeDelete: relationship.constraints?.cascadeDelete || false,
      required: relationship.constraints?.required || false,
      unique: relationship.constraints?.unique || false,
    });
    setRelationshipModalVisible(true);
  };

  // 处理删除关系
  const handleDeleteRelationship = async (relationshipId: string) => {
    try {
      // 从关系列表中找到对应的关系
      const relationship = relationships.find(r => r.id === relationshipId);
      if (!relationship) {
        message.error('无法找到对应的关系');
        return;
      }
      
      // 找到源实体ID
      const sourceEntity = entities.find(e => e.name === relationship.sourceEntity);
      if (!sourceEntity) {
        message.error('无法确定源实体');
        return;
      }
      
      await deleteRelationship(sourceEntity.id, relationshipId);
      message.success('关系删除成功');
      loadRelationships();
    } catch (error) {
      message.error('关系删除失败');
    }
  };

  // 处理关系模态框确认
  const handleRelationshipModalOk = async () => {
    try {
      const values = await relationshipForm.validateFields();

      if (relationshipModalType === 'create') {
        // 找到源实体
        const sourceEntity = entities.find(e => e.name === values.sourceEntity);
        if (!sourceEntity) {
          message.error('源实体不存在');
          return;
        }

        await createRelationship(sourceEntity.id, {
          name: values.name,
          targetEntity: values.targetEntity,
          type: values.type,
          foreignKey: values.foreignKey,
          constraints: {
            cascadeDelete: values.cascadeDelete || false,
            required: values.required || false,
            unique: values.unique || false,
          }
        });
        message.success('关系创建成功');
      } else if (relationshipModalType === 'edit' && editingRelationship) {
        await updateRelationship(editingRelationship.id, {
          name: values.name,
          targetEntity: values.targetEntity,
          type: values.type,
          foreignKey: values.foreignKey,
          constraints: {
            cascadeDelete: values.cascadeDelete || false,
            required: values.required || false,
            unique: values.unique || false,
          }
        });
        message.success('关系更新成功');
      }

      setRelationshipModalVisible(false);
      relationshipForm.resetFields();
      loadRelationships();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 处理关系模态框取消
  const handleRelationshipModalCancel = () => {
    setRelationshipModalVisible(false);
    relationshipForm.resetFields();
  };

  // 处理模态框确认
  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (modalType === 'create') {
        await createEntity({
          name: values.displayName.toLowerCase().replace(/\s+/g, '_'),
          displayName: values.displayName,
          description: values.description,
          icon: values.icon,
          isRole: values.isRole || false,
          scenarioId: scenarioId,
          fields: [], // 初始创建时没有字段，后续可以添加
        });
        message.success('实体创建成功');
      } else if (modalType === 'edit' && selectedEntity) {
        await updateEntity(selectedEntity.id, {
          displayName: values.displayName,
          description: values.description,
          icon: values.icon,
          isRole: values.isRole || false,
        });
        message.success('实体更新成功');
      }
      
      setIsModalVisible(false);
      refreshEntities();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 处理模态框取消
  const handleModalCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  return (
    <div className="entity-modeling-step">
      {/* 步骤头部 */}
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <DatabaseOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">实体建模</h2>
              <p className="unified-step-description">定义业务实体的结构和关系，构建完整的数据模型</p>
            </div>
          </div>
        </div>
      </UnifiedCard>

      {/* 模板信息提示 */}
      {templateApplicationService.hasAppliedTemplate() && (
        <Alert
          message={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <RocketOutlined style={{ color: '#007aff' }} />
              <span>已应用模板数据</span>
            </div>
          }
          description={
            (() => {
              const templateInfo = templateApplicationService.getAppliedTemplateInfo();
              const templateEntities = templateApplicationService.getEntitiesForStep();
              return (
                <div>
                  <p>
                    已从模板 <strong>{templateInfo?.template_key}</strong> 加载了 <strong>{templateEntities.length}</strong> 个预定义实体。
                    您可以在此基础上进行修改或添加新的实体。
                  </p>
                </div>
              );
            })()
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        tabBarExtraContent={
          activeTab === 'entities' ? (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateEntity}
            >
              创建实体
            </Button>
          ) : activeTab === 'relationships' ? (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateRelationship}
            >
              创建关系
            </Button>
          ) : null
        }
        items={[
          {
            key: 'entities',
            label: '实体管理',
            children: (
              <UnifiedCard>
                <Table
                  columns={entityColumns}
                  dataSource={entities}
                  loading={loading}
                  rowKey="id"
                  scroll={{ x: '100%' }}
                  size="middle"
                  bordered={false}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 个实体`,
                  }}
                  style={{ width: '100%' }}
                />
              </UnifiedCard>
            )
          },
          {
            key: 'relationships',
            label: '关系管理',
            children: (
              <UnifiedCard>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h4>实体关系</h4>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleCreateRelationship}
                  >
                    创建关系
                  </Button>
                </div>

                <Table
                  dataSource={relationships}
                  loading={relationshipLoading}
                  rowKey="id"
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: '关系名称',
                      dataIndex: 'name',
                      key: 'name',
                      render: (text: string) => (
                        <span style={{ fontWeight: 600 }}>{text}</span>
                      ),
                    },
                    {
                      title: '源实体',
                      dataIndex: 'sourceEntity',
                      key: 'sourceEntity',
                      render: (entity: string) => (
                        <Tag color="blue">{entity}</Tag>
                      ),
                    },
                    {
                      title: '目标实体',
                      dataIndex: 'targetEntity',
                      key: 'targetEntity',
                      render: (entity: string) => (
                        <Tag color="green">{entity}</Tag>
                      ),
                    },
                    {
                      title: '关系类型',
                      dataIndex: 'type',
                      key: 'type',
                      render: (type: string) => {
                        const typeMap = {
                          'one-to-one': { text: '一对一', color: 'purple' },
                          'one-to-many': { text: '一对多', color: 'orange' },
                          'many-to-many': { text: '多对多', color: 'red' },
                          'hierarchy': { text: '层级关系', color: 'cyan' },
                        };
                        const config = typeMap[type as keyof typeof typeMap] || { text: type, color: 'default' };
                        return <Tag color={config.color}>{config.text}</Tag>;
                      },
                    },
                    {
                      title: '外键',
                      dataIndex: 'foreignKey',
                      key: 'foreignKey',
                      render: (key: string) => key || '-',
                    },
                    {
                      title: '约束',
                      dataIndex: 'constraints',
                      key: 'constraints',
                      render: (constraints: any) => (
                        <Space size="small">
                          {constraints?.cascadeDelete && <Tag color="red">级联删除</Tag>}
                          {constraints?.required && <Tag color="orange">必需</Tag>}
                          {constraints?.unique && <Tag color="purple">唯一</Tag>}
                          {!constraints?.cascadeDelete && !constraints?.required && !constraints?.unique && '-'}
                        </Space>
                      ),
                    },
                    {
                      title: '操作',
                      key: 'actions',
                      width: 120,
                      render: (_: any, record: EntityRelationship) => (
                        <Space size="small">
                          <Button
                            type="link"
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => handleEditRelationship(record)}
                            title="编辑"
                          />
                          <Popconfirm
                            title="确定删除这个关系吗？"
                            onConfirm={() => handleDeleteRelationship(record.id)}
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
                    },
                  ]}
                />
              </UnifiedCard>
            )
          }
        ]}
      />

      {/* 实体创建/编辑模态框 */}
      <Modal
        key={`entity-modal-${modalType}-${selectedEntity?.id || 'new'}`}
        title={
          modalType === 'create' ? '创建实体' :
          modalType === 'edit' ? '编辑实体' :
          modalType === 'fields' ? `管理字段 - ${selectedEntity?.displayName}` : '查看实体'
        }
        open={isModalVisible}
        onOk={modalType === 'view' || modalType === 'fields' ? handleModalCancel : handleModalOk}
        onCancel={handleModalCancel}
        okText={modalType === 'view' || modalType === 'fields' ? '关闭' : '确定'}
        cancelText="取消"
        width={modalType === 'fields' ? 800 : 600}
        footer={modalType === 'fields' ? [
          <Button key="close" onClick={handleModalCancel}>
            关闭
          </Button>
        ] : undefined}
      >
        {modalType === 'fields' ? (
          // 字段管理界面
          <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4>字段列表</h4>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleCreateField}
              >
                添加字段
              </Button>
            </div>

            <Table
              dataSource={selectedEntity?.fields || []}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: '字段名称',
                  dataIndex: 'displayName',
                  key: 'displayName',
                  render: (text: string, record: EntityField) => (
                    <Space>
                      <span style={{ fontWeight: 600 }}>{text}</span>
                      <Tag color="blue">{record.name}</Tag>
                    </Space>
                  ),
                },
                {
                  title: '类型',
                  dataIndex: 'type',
                  key: 'type',
                  render: (type: string) => (
                    <Tag color="green">{type}</Tag>
                  ),
                },
                {
                  title: '必填',
                  dataIndex: 'required',
                  key: 'required',
                  render: (required: boolean) => (
                    <Tag color={required ? 'red' : 'default'}>
                      {required ? '必填' : '可选'}
                    </Tag>
                  ),
                },
                {
                  title: '唯一',
                  dataIndex: 'unique',
                  key: 'unique',
                  render: (unique: boolean) => (
                    <Tag color={unique ? 'orange' : 'default'}>
                      {unique ? '唯一' : '普通'}
                    </Tag>
                  ),
                },
                {
                  title: '操作',
                  key: 'actions',
                  width: 120,
                  render: (_: any, record: EntityField) => (
                    <Space size="small">
                      <Button
                        type="link"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleEditField(record)}
                        title="编辑"
                      />
                      <Popconfirm
                        title="确定删除这个字段吗？"
                        onConfirm={() => handleDeleteField(record.id)}
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
                },
              ]}
            />
          </div>
        ) : (
          // 实体基本信息表单
          <Form
            form={form}
            layout="vertical"
            disabled={modalType === 'view'}
          >
            <Form.Item
              label="实体显示名称"
              name="displayName"
              rules={[{ required: true, message: '请输入实体显示名称' }]}
            >
              <Input placeholder="请输入实体显示名称" />
            </Form.Item>

            <Form.Item
              label="实体描述"
              name="description"
              rules={[{ required: true, message: '请输入实体描述' }]}
            >
              <Input.TextArea
                rows={3}
                placeholder="请输入实体描述"
              />
            </Form.Item>

            <Form.Item
              label="图标"
              name="icon"
            >
              <Select placeholder="选择图标">
                <Option value="user">用户</Option>
                <Option value="shopping-cart">购物车</Option>
                <Option value="product">商品</Option>
                <Option value="order">订单</Option>
                <Option value="category">分类</Option>
                <Option value="tag">标签</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="角色实体"
              name="isRole"
              valuePropName="checked"
              tooltip="标记此实体是否为角色实体。角色实体将自动在角色管理中创建对应的角色，用于用户管理。"
            >
              <Switch
                checkedChildren="是"
                unCheckedChildren="否"
                defaultChecked={false}
              />
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* 字段编辑模态框 */}
      <Modal
        key={`field-modal-${fieldModalType}-${editingField?.id || 'new'}`}
        title={fieldModalType === 'create' ? '添加字段' : '编辑字段'}
        open={fieldModalVisible}
        onOk={async () => {
          try {
            const values = await fieldForm.validateFields();
            
            if (!selectedEntity) {
              message.error('未选择实体');
              return;
            }
    
            const newFieldData = {
              name: values.name,
              displayName: values.displayName,
              type: values.type,
              required: values.required || false,
              unique: values.unique || false,
              defaultValue: values.defaultValue,
              options: values.options ? values.options.split('\n') : [],
              validation: values.validation,
            };
    
            let updatedFields: EntityField[];
    
            if (fieldModalType === 'create') {
              const fieldWithId: EntityField = { 
                ...newFieldData, 
                id: `new_${Date.now()}`,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              };
              updatedFields = [...(selectedEntity.fields || []), fieldWithId];
            } else {
              updatedFields = (selectedEntity.fields || []).map(f =>
                f.id === editingField?.id ? { ...f, ...newFieldData } : f
              );
            }
    
            await updateEntity(selectedEntity.id, {
              fields: updatedFields,
            });
    
            message.success(fieldModalType === 'create' ? '字段添加成功' : '字段更新成功');
            setFieldModalVisible(false);
            fieldForm.resetFields();
            
            // 刷新实体详情和列表
            const detail = await getEntityDetail(selectedEntity.id);
            setSelectedEntity(detail);
            refreshEntities();
    
          } catch (error) {
            message.error(fieldModalType === 'create' ? '字段添加失败' : '字段更新失败');
          }
        }}
        onCancel={() => {
          setFieldModalVisible(false);
          fieldForm.resetFields();
        }}
        width={600}
      >
        <Form
          form={fieldForm}
          layout="vertical"
        >
          <Form.Item
            label="字段名称"
            name="name"
            rules={[
              { required: true, message: '请输入字段名称' },
              { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '字段名称必须以字母开头，只能包含字母、数字和下划线' }
            ]}
          >
            <Input placeholder="请输入字段名称（如：user_name）" />
          </Form.Item>

          <Form.Item
            label="显示名称"
            name="displayName"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="请输入显示名称（如：用户名）" />
          </Form.Item>

          <Form.Item
            label="字段类型"
            name="type"
            rules={[{ required: true, message: '请选择字段类型' }]}
          >
            <Select placeholder="请选择字段类型">
              <Option value="text">文本</Option>
              <Option value="number">数字</Option>
              <Option value="boolean">布尔值</Option>
              <Option value="date">日期</Option>
              <Option value="datetime">日期时间</Option>
              <Option value="file">文件</Option>
              <Option value="image">图片</Option>
              <Option value="json">JSON</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="默认值"
            name="defaultValue"
          >
            <Input placeholder="请输入默认值（可选）" />
          </Form.Item>

          <Form.Item
            label="选项列表"
            name="options"
            tooltip="每行一个选项，仅当字段类型为文本且需要下拉选择时使用"
          >
            <Input.TextArea
              rows={4}
              placeholder="选项1&#10;选项2&#10;选项3"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Form.Item
                name="required"
                valuePropName="checked"
                style={{ marginBottom: 0 }}
              >
                <Switch checkedChildren="必填" unCheckedChildren="可选" />
              </Form.Item>
              <Form.Item
                name="unique"
                valuePropName="checked"
                style={{ marginBottom: 0 }}
              >
                <Switch checkedChildren="唯一" unCheckedChildren="普通" />
              </Form.Item>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 关系编辑模态框 */}
      <Modal
        key={`relationship-modal-${relationshipModalType}-${editingRelationship?.id || 'new'}`}
        title={relationshipModalType === 'create' ? '创建关系' : '编辑关系'}
        open={relationshipModalVisible}
        onOk={handleRelationshipModalOk}
        onCancel={handleRelationshipModalCancel}
        width={600}
      >
        <Form
          form={relationshipForm}
          layout="vertical"
        >
          <Form.Item
            label="关系名称"
            name="name"
            rules={[
              { required: true, message: '请输入关系名称' },
              { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '关系名称必须以字母开头，只能包含字母、数字和下划线' }
            ]}
          >
            <Input placeholder="请输入关系名称（如：user_orders）" />
          </Form.Item>

          <Form.Item
            label="源实体"
            name="sourceEntity"
            rules={[{ required: true, message: '请选择源实体' }]}
          >
            <Select placeholder="请选择源实体">
              {entities.map(entity => (
                <Option key={entity.id} value={entity.name}>
                  {entity.displayName} ({entity.name})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="目标实体"
            name="targetEntity"
            rules={[{ required: true, message: '请选择目标实体' }]}
          >
            <Select placeholder="请选择目标实体">
              {entities.map(entity => (
                <Option key={entity.id} value={entity.name}>
                  {entity.displayName} ({entity.name})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="关系类型"
            name="type"
            rules={[{ required: true, message: '请选择关系类型' }]}
          >
            <Select placeholder="请选择关系类型">
              <Option value="one-to-one">一对一</Option>
              <Option value="one-to-many">一对多</Option>
              <Option value="many-to-many">多对多</Option>
              <Option value="hierarchy">层级关系</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="外键字段"
            name="foreignKey"
            tooltip="指定外键字段名称，用于建立关系"
          >
            <Input placeholder="请输入外键字段名称（如：user_id）" />
          </Form.Item>

          <Form.Item label="关系约束">
            <Space>
              <Form.Item
                name="cascadeDelete"
                valuePropName="checked"
                style={{ marginBottom: 0 }}
              >
                <Switch checkedChildren="级联删除" unCheckedChildren="普通删除" />
              </Form.Item>
              <Form.Item
                name="required"
                valuePropName="checked"
                style={{ marginBottom: 0 }}
              >
                <Switch checkedChildren="必需" unCheckedChildren="可选" />
              </Form.Item>
              <Form.Item
                name="unique"
                valuePropName="checked"
                style={{ marginBottom: 0 }}
              >
                <Switch checkedChildren="唯一" unCheckedChildren="普通" />
              </Form.Item>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 底部操作按钮 */}
      <div className="step-actions">
        <Button onClick={onPrev}>上一步</Button>
        <Button 
          type="primary" 
          onClick={onNext}
          disabled={entities.length === 0}
        >
          下一步
        </Button>
      </div>

      {/* 数据管理面板 */}
      <EntityDataManagementPanel
        entity={dataManagementEntity}
        visible={dataManagementVisible}
        onClose={() => {
          setDataManagementVisible(false);
          setDataManagementEntity(null);
        }}
      />
    </div>
  );
};

export default EntityModelingStep;
