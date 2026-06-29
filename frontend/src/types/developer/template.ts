/**
 * 模板管理相关类型定义
 */

// 模板分类
export type TemplateCategory = 
  | 'business' 
  | 'healthcare' 
  | 'education' 
  | 'hospitality' 
  | 'finance' 
  | 'logistics' 
  | 'government' 
  | 'custom';

// 难度等级
export type TemplateDifficulty = 'beginner' | 'intermediate' | 'advanced';

// 模板预览信息
export interface TemplatePreview {
  entities: number;
  workflows: number;
  forms: number;
  apis: number;
}

// 模板基础信息
export interface TemplateBase {
  key: string;
  name: string;
  description: string;
  category: TemplateCategory;
  difficulty: TemplateDifficulty;
  estimated_setup_time: string;
  features: string[];
  tags: string[];
  created_at: string;
  updated_at: string;
}

// 模板列表项
export interface TemplateListItem extends TemplateBase {
  preview?: TemplatePreview;
}

// 分类统计
export interface CategoryStats {
  category: TemplateCategory;
  name: string;
  count: number;
  description: string;
}

// 获取模板列表请求参数
export interface GetTemplatesRequest {
  category?: TemplateCategory;
  include_preview?: boolean;
}

// 获取模板列表响应
export interface GetTemplatesResponse {
  code: number;
  message: string;
  data: {
    templates: TemplateListItem[];
    total: number;
    categories: CategoryStats[];
  };
}

// 实体字段
export interface EntityField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  validation?: {
    min_length?: number;
    max_length?: number;
    pattern?: string;
    options?: string[];
  };
}

// 实体定义
export interface Entity {
  name: string;
  table_name: string;
  description: string;
  fields: EntityField[];
}

// 工作流步骤
export interface WorkflowStep {
  name: string;
  type: string;
  description: string;
  config: Record<string, any>;
}

// 工作流定义
export interface Workflow {
  name: string;
  description: string;
  trigger: string;
  steps: WorkflowStep[];
}

// 表单字段
export interface FormField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  placeholder?: string;
  validation?: Record<string, any>;
}

// 表单区域
export interface FormSection {
  title: string;
  fields: FormField[];
}

// 表单定义
export interface Form {
  name: string;
  entity: string;
  layout: string;
  sections: FormSection[];
}

// API定义
export interface API {
  path: string;
  method: string;
  description: string;
}

// 角色定义
export interface Role {
  name: string;
  code: string;
  permissions: string[];
}

// 场景配置
export interface ScenarioConfig {
  type: string;
  business_domain: string;
  target_users: string[];
  key_features: string[];
  example_instructions: string[];
}

// 模板配置
export interface TemplateConfig {
  scenario: ScenarioConfig;
  entities: Entity[];
  workflows: Workflow[];
  forms: Form[];
  apis: API[];
  roles: Role[];
}

// 设置指南
export interface SetupGuide {
  steps: string[];
  prerequisites: string[];
  tips: string[];
}

// 模板详情
export interface TemplateDetail extends TemplateBase {
  version: string;
  author: string;
  license: string;
  config: TemplateConfig;
  setup_guide: SetupGuide;
}

// 获取模板详情响应
export interface GetTemplateDetailResponse {
  code: number;
  message: string;
  data: {
    template: TemplateDetail;
  };
}

// 模板选择状态
export interface TemplateSelectionState {
  selectedTemplate: TemplateListItem | null;
  templates: TemplateListItem[];
  categories: CategoryStats[];
  selectedCategory: TemplateCategory | null;
  isLoading: boolean;
  error: string | null;
}
