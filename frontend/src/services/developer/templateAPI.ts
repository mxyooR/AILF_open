/**
 * 模板管理API服务
 */

import { apiClient } from '../common/apiClient';
import type {
  GetTemplatesRequest,
  GetTemplatesResponse,
  GetTemplateDetailResponse,
  TemplateCategory,
} from '../../types/developer/template';

export const templateAPI = {
  /**
   * 获取所有可用模板
   * GET /api/v1/templates
   */
  async getTemplates(params?: GetTemplatesRequest): Promise<GetTemplatesResponse> {
    const queryParams = new URLSearchParams();

    if (params?.category) {
      queryParams.append('category', params.category);
    }

    if (params?.include_preview !== undefined) {
      queryParams.append('include_preview', params.include_preview.toString());
    }

    const url = `/api/v1/templates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;

    const response = await apiClient.get<GetTemplatesResponse['data']>(url);
    return response;
  },

  /**
   * 获取特定模板详细配置
   * GET /api/v1/templates/{template_key}
   */
  async getTemplateDetail(templateKey: string): Promise<GetTemplateDetailResponse> {
    const response = await apiClient.get<GetTemplateDetailResponse['data']>(
      `/api/v1/templates/${templateKey}`
    );
    return response;
  },

  /**
   * 获取模板分类列表
   */
  getCategories(): Array<{ value: TemplateCategory; label: string; description: string }> {
    return [
      { value: 'business', label: '商业管理', description: '电商、零售、企业管理等' },
      { value: 'healthcare', label: '医疗健康', description: '医院、诊所、健康管理等' },
      { value: 'education', label: '教育培训', description: '学校、培训机构、在线教育等' },
      { value: 'hospitality', label: '服务行业', description: '餐饮、酒店、旅游等' },
      { value: 'finance', label: '金融服务', description: '银行、保险、投资等' },
      { value: 'logistics', label: '物流运输', description: '货运、仓储、配送等' },
      { value: 'government', label: '政府机构', description: '政务服务、公共管理等' },
      { value: 'custom', label: '自定义', description: '其他特殊业务场景' },
    ];
  },

  /**
   * 获取难度等级信息
   */
  getDifficultyInfo(difficulty: string): { label: string; color: string; description: string } {
    const difficultyMap = {
      beginner: {
        label: '初级',
        color: '#52c41a',
        description: '配置简单，功能基础，适合新手',
      },
      intermediate: {
        label: '中级',
        color: '#faad14',
        description: '功能较全，需要一定配置经验',
      },
      advanced: {
        label: '高级',
        color: '#f5222d',
        description: '功能复杂，需要深入理解业务流程',
      },
    };

    return difficultyMap[difficulty as keyof typeof difficultyMap] || {
      label: '未知',
      color: '#d9d9d9',
      description: '未知难度等级',
    };
  },

  /**
   * 应用模板到系统
   * POST /api/v1/templates/{template_key}/apply
   */
  async applyTemplate(
    templateKey: string, 
    scenarioName: string, 
    description?: string, 
    customizations?: Record<string, any>,
    importSampleData?: boolean
  ): Promise<any> {
    const response = await apiClient.post(
      `/api/v1/templates/${templateKey}/apply`,
      {
        scenario_name: scenarioName,
        description: description,
        customizations: customizations || {},
        import_sample_data: importSampleData || false
      }
    );
    return response;
  },

  /**
   * 获取模板示例数据信息
   * GET /api/v1/templates/{template_key}/sample-data
   */
  async getSampleDataInfo(templateKey: string): Promise<{
    code: number;
    data: {
      has_sample_data: boolean;
      entity_count: number;
      total_records: number;
    };
  }> {
    const response = await apiClient.get<{
      has_sample_data: boolean;
      entity_count: number;
      total_records: number;
    }>(
      `/api/v1/templates/${templateKey}/sample-data`
    );
    return response;
  },

  /**
   * 获取模板数据
   * GET /api/v1/templates/{template_key}/data
   */
  async getTemplateData(templateKey: string): Promise<any> {
    const response = await apiClient.get(
      `/api/v1/templates/${templateKey}/data`
    );
    return response;
  },

  /**
   * 保存当前配置为模板
   * POST /api/v1/templates/save-current
   */
  async saveCurrentAsTemplate(data: {
    name: string;
    description: string;
    category: TemplateCategory;
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    tags?: string[];
    save_location?: 'system' | 'custom';
    custom_path?: string;
    includeEntities?: boolean;
    includeWorkflows?: boolean;
    includeForms?: boolean;
    includeAPIs?: boolean;
    includeRoles?: boolean;
  }): Promise<any> {
    const response = await apiClient.post('/api/v1/templates/save-current', data);
    return response;
  },

  /**
   * 导出模板为JSON文件
   * GET /api/v1/templates/{template_key}/export
   */
  async exportTemplate(templateKey: string): Promise<Blob> {
    const token = apiClient.getToken();
    const baseURL = '/api/v1';
    
    const response = await fetch(`${baseURL}/templates/${templateKey}/export`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('导出模板失败');
    }
    
    return await response.blob();
  },

  /**
   * 导入模板从 JSON文件
   * POST /api/v1/templates/import
   */
  async importTemplate(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const token = apiClient.getToken();
    const baseURL = '/api/v1';
    
    const response = await fetch(`${baseURL}/templates/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '导入模板失败');
    }
    
    return await response.json();
  },

  /**
   * 删除自定义模板
   * DELETE /api/v1/templates/{template_key}
   */
  async deleteTemplate(templateKey: string): Promise<any> {
    const response = await apiClient.delete(`/api/v1/templates/${templateKey}`);
    return response;
  },

  /**
   * 更新模板信息
   * PUT /api/v1/templates/{template_key}
   */
  async updateTemplate(templateKey: string, data: Partial<{
    name: string;
    description: string;
    category: TemplateCategory;
    difficulty: string;
    tags: string[];
  }>): Promise<any> {
    const response = await apiClient.put(`/api/v1/templates/${templateKey}`, data);
    return response;
  },

  /**
   * 下载模板示例文档
   * GET /api/v1/templates/download-example
   */
  async downloadTemplateExample(): Promise<Blob> {
    const token = apiClient.getToken();
    const baseURL = '/api/v1';
    
    const response = await fetch(`${baseURL}/templates/download-example`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('下载示例文档失败');
    }
    
    return await response.blob();
  },
};

export default templateAPI;
