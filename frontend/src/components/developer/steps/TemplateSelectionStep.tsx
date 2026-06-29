/**
 * 模板选择步骤组件
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Row,
  Col,
  Button,
  Tag,
  Typography,
  Space,
  Spin,
  Alert,
  Select,
  Input,
  Empty,
  Tooltip,
  Modal,
  Form,
  message,
  Upload,
  Checkbox,
  Divider,
  Popconfirm
} from 'antd';
import { UnifiedCard } from '../common';
import {
  SearchOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  DatabaseOutlined,
  AppstoreOutlined,
  RocketOutlined,
  UploadOutlined,
  DownloadOutlined,
  SaveOutlined,
  FileTextOutlined,
  DeleteOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { useTemplateManagement } from '../../../hooks/developer/useTemplateManagement';
import { useScenarioConfig } from '../../../hooks/developer/useScenarioConfig';
import { templateAPI } from '../../../services/developer/templateAPI';
import { templateApplicationService } from '../../../services/developer/templateApplicationService';
import { scenarioAPI } from '../../../services/developer/scenarioAPI';
import type { TemplateListItem, TemplateCategory } from '../../../types/developer/template';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

interface TemplateSelectionStepProps {
  onTemplateSelect: (template: TemplateListItem) => void;
  onNext: () => void;
}

const TemplateSelectionStep: React.FC<TemplateSelectionStepProps> = ({
  onTemplateSelect,
  onNext,
}) => {
  const {
    selectedTemplate,
    templates,
    categories,
    selectedCategory,
    isLoading,
    error,
    selectTemplate,
    filterTemplates,
    clearError,
  } = useTemplateManagement();

  const { loadCurrentScenario } = useScenarioConfig();

  const [searchText, setSearchText] = useState('');
  const [applyModalVisible, setApplyModalVisible] = useState(false);
  const [applying, setApplying] = useState(false);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [saveLocation, setSaveLocation] = useState<'system' | 'custom'>('system');
  const [sampleDataInfo, setSampleDataInfo] = useState<{
    has_sample_data: boolean;
    entity_count: number;
    total_records: number;
  } | null>(null);
  const [form] = Form.useForm();
  const [saveForm] = Form.useForm();
  const isMountedRef = useRef(true);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 处理模板选择
  const handleTemplateSelect = (template: TemplateListItem) => {
    selectTemplate(template);
    onTemplateSelect(template);
  };

  // 处理分类筛选
  const handleCategoryFilter = (category: TemplateCategory | string) => {
    // 将 'all' 转换为 null 传递给 filterTemplates
    const actualCategory = category === 'all' ? null : category as TemplateCategory;
    filterTemplates(actualCategory);
  };

  // 处理应用模板
  const handleApplyTemplate = async () => {
    if (!selectedTemplate) {
      message.error('请先选择一个模板');
      return;
    }
    
    // 获取示例数据信息
    try {
      const response = await templateAPI.getSampleDataInfo(selectedTemplate.key);
      if (response.code === 200) {
        setSampleDataInfo(response.data);
      } else {
        setSampleDataInfo(null);
      }
    } catch (error) {
      console.warn('获取示例数据信息失败:', error);
      setSampleDataInfo(null);
    }
    
    setApplyModalVisible(true);
  };

  // 确认应用模板
  const handleConfirmApply = async () => {
    if (!selectedTemplate || !isMountedRef.current) return;

    try {
      const values = await form.validateFields();
      if (!isMountedRef.current) return;
      setApplying(true);

      const result = await templateApplicationService.applyTemplate(
        selectedTemplate,
        values.scenarioName,
        values.description,
        values.customizations,
        values.importSampleData
      );

      if (result.success && isMountedRef.current) {
        // 显示应用成功消息，包含清理信息和示例数据导入信息
        const cleanupInfo = result.data?.applied_config?.cleanup_info;
        const sampleDataImport = result.data?.sample_data_import;
        
        let successMessage = '模板应用成功！';
        if (cleanupInfo && cleanupInfo.cleanup_count > 0) {
          successMessage += ` 已清理 ${cleanupInfo.cleanup_count} 个旧数据项。`;
        }
        if (sampleDataImport) {
          if (sampleDataImport.success_count > 0) {
            successMessage += ` 已导入 ${sampleDataImport.success_count} 条示例数据`;
          }
          if (sampleDataImport.skipped_count > 0) {
            successMessage += `，跳过 ${sampleDataImport.skipped_count} 条重复数据`;
          }
          if (sampleDataImport.error_count > 0) {
            successMessage += `，${sampleDataImport.error_count} 条导入失败`;
          }
          if (sampleDataImport.success_count > 0 || sampleDataImport.skipped_count > 0) {
            successMessage += '。';
          }
        }
        message.success(successMessage, 5);

        setApplyModalVisible(false);
        form.resetFields();

        // 等待后端完全处理完成，然后重新加载场景状态
        console.log('🔄 模板应用成功，等待后端处理完成...');
        
        // 等待2秒确保后端完全处理完成
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 多次尝试重新加载场景状态，确保获取到最新的场景ID
        let retryCount = 0;
        let scenarioLoaded = false;
        
        while (retryCount < 5 && !scenarioLoaded && isMountedRef.current) {
          try {
            console.log(`🔄 第${retryCount + 1}次尝试加载最新场景状态...`);
            if (!isMountedRef.current) break;
            await loadCurrentScenario();
            
            // 验证场景是否已更新（检查场景名称是否包含模板相关信息）
            // 重新获取最新的场景状态来验证
            const latestScenarioResponse = await scenarioAPI.getCurrent(true);
            const currentScenario = latestScenarioResponse.data.scenario;
            if (currentScenario && (
              currentScenario.name?.includes('基础电商') || 
              currentScenario.name?.includes('医院管理') ||
              currentScenario.name?.includes('模板') ||
              currentScenario.id !== 'scenario_1754366788026'
            )) {
              console.log('✅ 场景状态已更新:', currentScenario);
              scenarioLoaded = true;
            } else {
              console.log('⚠️ 场景状态尚未更新，继续重试...');
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
          } catch (error) {
            console.warn(`❌ 第${retryCount + 1}次加载场景失败:`, error);
          }
          retryCount++;
        }

        if (!scenarioLoaded) {
          console.warn('⚠️ 场景状态更新超时，但继续下一步');
        }

        // 继续到下一步
        if (isMountedRef.current) {
          onNext();
        }
      } else {
        message.error(result.error || '应用模板失败');
      }
    } catch (error: any) {
      console.error('应用模板失败:', error);
      message.error('应用模板失败，请重试');
    } finally {
      if (isMountedRef.current) {
        setApplying(false);
      }
    }
  };

  // 取消应用模板
  const handleCancelApply = () => {
    setApplyModalVisible(false);
    form.resetFields();
  };

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  // 导出模板
  const handleExport = async (templateKey: string) => {
    try {
      const blob = await templateAPI.exportTemplate(templateKey);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${templateKey}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('模板导出成功');
    } catch (error) {
      message.error('导出模板失败');
    }
  };

  // 导入模板
  const handleImport = async (file: File) => {
    try {
      const response = await templateAPI.importTemplate(file);
      if (response.code === 200) {
        message.success('模板导入成功，正在重新加载...');
        // 重新加载模板列表
        window.location.reload();
      } else {
        message.error(response.message || '导入失败');
      }
    } catch (error) {
      message.error('导入模板失败');
    }
    return false;
  };

  // 保存当前配置为模板
  const handleSaveAsCurrent = async (values: any) => {
    try {
      const response = await templateAPI.saveCurrentAsTemplate({
        name: values.name,
        description: values.description,
        category: values.category,
        difficulty: values.difficulty,
        tags: values.tags ? values.tags.split(',').map((t: string) => t.trim()) : [],
        save_location: values.save_location || 'system',
        custom_path: values.custom_path,
        includeEntities: values.includeEntities,
        includeWorkflows: values.includeWorkflows,
        includeForms: values.includeForms,
        includeAPIs: values.includeAPIs,
        includeRoles: values.includeRoles,
      });

      if (response.code === 200) {
        const preview = response.data.preview;
        message.success(
          `模板保存成功！包含: ${preview.entities}个实体, ${preview.apis}个API, ${preview.forms}个表单, ${preview.workflows}个工作流`,
          5
        );
        setSaveModalVisible(false);
        saveForm.resetFields();
        setSaveLocation('system');
        // 重新加载模板列表
        window.location.reload();
      } else {
        message.error(response.message || '保存失败');
      }
    } catch (error) {
      console.error('保存模板失败:', error);
      message.error('保存模板失败');
    }
  };

  // 删除模板
  const handleDeleteTemplate = async (templateKey: string, templateName: string) => {
    try {
      const response = await templateAPI.deleteTemplate(templateKey);
      if (response.code === 200) {
        message.success(`模板 "${templateName}" 已删除`);
        window.location.reload();
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error: any) {
      if (error.message?.includes('系统模板')) {
        message.error('系统模板不可删除');
      } else {
        message.error('删除模板失败');
      }
    }
  };

  // 下载示例文档
  const handleDownloadExample = async () => {
    try {
      const blob = await templateAPI.downloadTemplateExample();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'template_example.json';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('示例文档下载成功');
    } catch (error) {
      message.error('下载示例文档失败');
    }
  };

  // 过滤模板
  const filteredTemplates = templates.filter(template => {
    if (!searchText) return true;
    const searchLower = searchText.toLowerCase();
    return (
      template.name.toLowerCase().includes(searchLower) ||
      template.description.toLowerCase().includes(searchLower) ||
      template.tags.some(tag => tag.toLowerCase().includes(searchLower))
    );
  });

  // 获取难度标签颜色
  const getDifficultyColor = (difficulty: string) => {
    const info = templateAPI.getDifficultyInfo(difficulty);
    return info.color;
  };

  // 获取分类选项
  const categoryOptions = [
    { value: 'all', label: '全部分类' },
    ...templateAPI.getCategories().map(cat => ({
      value: cat.value,
      label: cat.label,
    })),
  ];

  return (
    <div className="template-selection-step">
      {/* 步骤头部 */}
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <AppstoreOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">模板选择</h2>
              <p className="unified-step-description">从预设模板中选择最适合您业务场景的配置，快速开始系统搭建</p>
            </div>
          </div>
        </div>
      </UnifiedCard>

      {/* 筛选和搜索 */}
      <UnifiedCard style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Search
              placeholder="搜索模板名称、描述或标签..."
              allowClear
              size="large"
              prefix={<SearchOutlined />}
              onSearch={handleSearch}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ maxWidth: 400 }}
            />
          </Col>
          <Col>
            <Select
              placeholder="选择分类"
              size="large"
              style={{ width: 160 }}
              value={selectedCategory}
              onChange={handleCategoryFilter}
              suffixIcon={<FilterOutlined />}
            >
              {categoryOptions.map(option => (
                <Select.Option key={option.value} value={option.value}>
                  {option.label}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Space>
              <Tooltip title="下载模板结构示例文档">
                <Button
                  icon={<QuestionCircleOutlined />}
                  onClick={handleDownloadExample}
                >
                  示例文档
                </Button>
              </Tooltip>
              <Button
                icon={<SaveOutlined />}
                onClick={() => setSaveModalVisible(true)}
              >
                保存为模板
              </Button>
              <Upload
                accept=".json"
                showUploadList={false}
                beforeUpload={handleImport}
              >
                <Button icon={<UploadOutlined />}>
                  导入模板
                </Button>
              </Upload>
              {selectedTemplate && (
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => handleExport(selectedTemplate.key)}
                >
                  导出模板
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </UnifiedCard>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          closable
          onClose={clearError}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 模板列表 */}
      <Spin spinning={isLoading}>
        {filteredTemplates.length === 0 ? (
          <Empty
            description="没有找到匹配的模板"
            style={{ padding: '60px 0' }}
          />
        ) : (
          <div className="template-grid">
            {filteredTemplates.map((template) => {
              const isSelected = selectedTemplate?.key === template.key;
              const SYSTEM_TEMPLATES = ['ecommerce_basic', 'hospital_management', 'railway_ticketing'];
              const isSystemTemplate = SYSTEM_TEMPLATES.includes(template.key);
              
              return (
                <div
                  key={template.key}
                  className={`template-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleTemplateSelect(template)}
                >
                  <div className="template-card-body">
                    {/* 选中标识 */}
                    {isSelected && (
                      <div
                        style={{
                          position: 'absolute',
                          top: 20,
                          right: 20,
                          color: 'var(--brand-primary)',
                          fontSize: 24,
                          zIndex: 2
                        }}
                      >
                        <CheckCircleOutlined />
                      </div>
                    )}

                    {/* 删除按钮（仅自定义模板） */}
                    {!isSystemTemplate && (
                      <Popconfirm
                        title="确定要删除这个模板吗？"
                        description={`将删除模板 "${template.name}"，此操作不可恢复`}
                        onConfirm={(e) => {
                          e?.stopPropagation();
                          handleDeleteTemplate(template.key, template.name);
                        }}
                        onCancel={(e) => e?.stopPropagation()}
                        okText="确定删除"
                        cancelText="取消"
                      >
                        <Button
                          type="text"
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={(e) => e.stopPropagation()}
                          style={{
                            position: 'absolute',
                            top: 12,
                            right: 12,
                            zIndex: 3
                          }}
                        />
                      </Popconfirm>
                    )}

                    {/* Icon & Title */}
                    <div className="template-icon-wrapper">
                      {template.category === 'business' ? <AppstoreOutlined /> :
                       template.category === 'healthcare' ? <DatabaseOutlined /> :
                       <ApiOutlined />}
                    </div>
                    
                    <div className="template-title">
                      {template.name}
                    </div>

                    {/* Description */}
                    <div className="template-desc">
                      {template.description}
                    </div>

                    {/* Tags */}
                    <div className="template-tags">
                      <span className="template-tag">
                        {templateAPI.getDifficultyInfo(template.difficulty).label}
                      </span>
                      {template.tags.slice(0, 2).map(tag => (
                        <span key={tag} className="template-tag">
                          {tag}
                        </span>
                      ))}
                      {template.tags.length > 2 && (
                        <span className="template-tag">+{template.tags.length - 2}</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Spin>

      {/* 底部操作 */}
      {selectedTemplate && (
        <div style={{ marginTop: 32, textAlign: 'center' }}>
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={handleApplyTemplate}
            style={{
              height: 48,
              fontSize: 16,
              fontWeight: 600,
              borderRadius: 8,
              minWidth: 200,
            }}
          >
            应用此模板
          </Button>
        </div>
      )}

      {/* 保存为模板弹窗 */}
      <Modal
        title="保存当前配置为模板"
        open={saveModalVisible}
        onCancel={() => {
          setSaveModalVisible(false);
          saveForm.resetFields();
        }}
        onOk={() => saveForm.submit()}
        width={600}
      >
        <Alert
          message="提示"
          description="将当前系统的配置（实体、工作流、表单、API、角色等）保存为可复用的模板"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form
          form={saveForm}
          layout="vertical"
          onFinish={handleSaveAsCurrent}
          initialValues={{
            difficulty: 'intermediate',
            save_location: 'system',
            includeEntities: true,
            includeWorkflows: true,
            includeForms: true,
            includeAPIs: true,
            includeRoles: true,
          }}
        >
          <Form.Item
            label="模板名称"
            name="name"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="例如：我的电商系统模板" />
          </Form.Item>

          <Form.Item
            label="模板描述"
            name="description"
            rules={[{ required: true, message: '请输入模板描述' }]}
          >
            <Input.TextArea rows={3} placeholder="描述这个模板的用途和特点" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="分类"
                name="category"
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select placeholder="选择模板分类">
                  <Select.Option value="business">商业管理</Select.Option>
                  <Select.Option value="healthcare">医疗健康</Select.Option>
                  <Select.Option value="education">教育培训</Select.Option>
                  <Select.Option value="hospitality">服务行业</Select.Option>
                  <Select.Option value="finance">金融服务</Select.Option>
                  <Select.Option value="logistics">物流运输</Select.Option>
                  <Select.Option value="transportation">交通运输</Select.Option>
                  <Select.Option value="custom">自定义</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="难度等级"
                name="difficulty"
                rules={[{ required: true, message: '请选择难度' }]}
              >
                <Select>
                  <Select.Option value="beginner">初级</Select.Option>
                  <Select.Option value="intermediate">中级</Select.Option>
                  <Select.Option value="advanced">高级</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="标签"
            name="tags"
            extra="多个标签用逗号分隔"
          >
            <Input placeholder="例如：电商,零售,库存管理" />
          </Form.Item>

          <Divider>保存位置</Divider>

          <Form.Item
            label="保存到"
            name="save_location"
            initialValue="system"
          >
            <Select onChange={(value) => setSaveLocation(value as 'system' | 'custom')}>
              <Select.Option value="system">
                <Space>
                  <FileTextOutlined />
                  <span>系统模板目录 (backend/app/templates/)</span>
                </Space>
              </Select.Option>
              <Select.Option value="custom">
                <Space>
                  <SaveOutlined />
                  <span>自定义路径</span>
                </Space>
              </Select.Option>
            </Select>
          </Form.Item>

          {saveLocation === 'custom' && (
            <Form.Item
              label="自定义路径"
              name="custom_path"
              rules={[{ required: true, message: '请输入保存路径' }]}
              extra="例如：E:\\MyTemplates 或 /home/user/templates"
            >
              <Input placeholder="输入完整的文件夹路径" />
            </Form.Item>
          )}

          <Divider>包含内容</Divider>

          <Form.Item name="includeEntities" valuePropName="checked">
            <Checkbox>包含实体定义</Checkbox>
          </Form.Item>

          <Form.Item name="includeWorkflows" valuePropName="checked">
            <Checkbox>包含工作流</Checkbox>
          </Form.Item>

          <Form.Item name="includeForms" valuePropName="checked">
            <Checkbox>包含表单</Checkbox>
          </Form.Item>

          <Form.Item name="includeAPIs" valuePropName="checked">
            <Checkbox>包含API路由</Checkbox>
          </Form.Item>

          <Form.Item name="includeRoles" valuePropName="checked">
            <Checkbox>包含角色权限</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      {/* 应用模板弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <RocketOutlined style={{ color: '#007aff' }} />
            <span>应用模板：{selectedTemplate?.name}</span>
          </div>
        }
        open={applyModalVisible}
        onOk={handleConfirmApply}
        onCancel={handleCancelApply}
        confirmLoading={applying}
        okText="确认应用"
        cancelText="取消"
        width={600}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            scenarioName: selectedTemplate?.name ? `${selectedTemplate.name}场景` : '',
            description: selectedTemplate?.description || '',
            importSampleData: false
          }}
        >
          <Alert
            message="应用模板说明"
            description={
              <div>
                <p>应用模板将会：</p>
                <ul style={{ marginBottom: 8, paddingLeft: 20 }}>
                  <li>创建预定义的实体模型和字段</li>
                  <li>生成相应的API路由和接口</li>
                  <li>配置用户角色和权限</li>
                  <li>设置工作流和表单</li>
                </ul>
                <p style={{ marginTop: 8, marginBottom: 8 }}>
                  <strong>⚠️ 重要提醒：</strong>应用模板前会自动清理同名的旧数据（实体、场景等）以避免冲突。
                </p>
                <p style={{ marginTop: 0, marginBottom: 0 }}>
                  <strong>注意：</strong>应用后可以在后续步骤中进行自定义修改。
                </p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            label="场景名称"
            name="scenarioName"
            rules={[
              { required: true, message: '请输入场景名称' },
              { min: 2, max: 50, message: '场景名称长度应在2-50个字符之间' }
            ]}
          >
            <Input placeholder="请输入场景名称" />
          </Form.Item>

          <Form.Item
            label="场景描述"
            name="description"
          >
            <Input.TextArea
              placeholder="请输入场景描述（可选）"
              rows={3}
              maxLength={200}
              showCount
            />
          </Form.Item>

          {/* 示例数据导入选项 */}
          <Form.Item
            name="importSampleData"
            valuePropName="checked"
          >
            <Checkbox
              disabled={!sampleDataInfo?.has_sample_data}
            >
              导入示例数据
              {sampleDataInfo?.has_sample_data ? (
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  （包含 {sampleDataInfo.entity_count} 个实体，共 {sampleDataInfo.total_records} 条演示记录）
                </Text>
              ) : (
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  （此模板暂无示例数据）
                </Text>
              )}
            </Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TemplateSelectionStep;
