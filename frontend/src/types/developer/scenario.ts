/**
 * 场景管理相关类型定义
 */

// 场景类型枚举
export type ScenarioType = 
  | 'ecommerce'
  | 'hospital' 
  | 'restaurant'
  | 'education'
  | 'logistics'
  | 'finance'
  | 'custom';

// 场景状态
export type ScenarioStatus = 'active' | 'inactive' | 'draft';

// 场景配置
export interface ScenarioConfig {
  business_domain: string;
  target_users: string[];
  key_features: string[];
  example_instructions: string[];
  custom_settings?: Record<string, any>;
}

// 场景信息
export interface Scenario {
  id: string;
  name: string;
  type: ScenarioType;
  description?: string;
  status: ScenarioStatus;
  created_at: string;
  updated_at: string;
  config: ScenarioConfig;
}

// 创建场景请求
export interface CreateScenarioRequest {
  name: string;
  type: ScenarioType;
  description?: string;
  config: ScenarioConfig;
}

// 场景响应
export interface ScenarioResponse {
  code: number;
  message: string;
  data: {
    scenario: Scenario;
  };
}

// 获取场景响应
export interface GetScenarioResponse {
  code: number;
  message: string;
  data: {
    scenario: Scenario;
  };
}

// 场景错误响应
export interface ScenarioErrorResponse {
  code: number;
  message: string;
  data: {
    error: string;
    details: string | Record<string, string[]>;
  };
}

// 场景表单数据
export interface ScenarioFormData {
  name: string;
  type: ScenarioType;
  description: string;
  business_domain: string;
  target_users: string[];
  key_features: string[];
  example_instructions: string[];
  custom_settings: Record<string, any>;
}

// 场景类型选项
export interface ScenarioTypeOption {
  value: ScenarioType;
  label: string;
  description: string;
  icon: string;
  features: string[];
}

// 预设场景类型
export const SCENARIO_TYPES: ScenarioTypeOption[] = [
  {
    value: 'ecommerce',
    label: '电商系统',
    description: '完整的电子商务管理系统',
    icon: 'shopping-cart',
    features: ['商品管理', '订单处理', '用户管理', '支付系统']
  },
  {
    value: 'hospital',
    label: '医院管理',
    description: '医院信息管理系统',
    icon: 'medicine-box',
    features: ['患者管理', '医生排班', '病历管理', '药品管理']
  },
  {
    value: 'restaurant',
    label: '餐厅管理',
    description: '餐厅运营管理系统',
    icon: 'coffee',
    features: ['菜品管理', '订单管理', '桌台管理', '库存管理']
  },
  {
    value: 'education',
    label: '教育系统',
    description: '教育机构管理系统',
    icon: 'book',
    features: ['学生管理', '课程管理', '成绩管理', '教师管理']
  },
  {
    value: 'logistics',
    label: '物流管理',
    description: '物流运输管理系统',
    icon: 'car',
    features: ['货物管理', '运输管理', '仓库管理', '配送管理']
  },
  {
    value: 'finance',
    label: '金融系统',
    description: '金融服务管理系统',
    icon: 'bank',
    features: ['账户管理', '交易管理', '风控管理', '报表管理']
  },
  {
    value: 'custom',
    label: '自定义',
    description: '自定义业务场景',
    icon: 'setting',
    features: ['灵活配置', '自定义功能', '个性化设置']
  }
];
