/**
 * 工作流设计相关类型定义
 */

// 节点类型（已移除 user_input，所有用户输入通过 api_call 的 POST 表单完成）
export type NodeType = 'start' | 'api_call' | 'condition' | 'notification' | 'end';

// 条件类型
export type ConditionType = 'always' | 'expression' | 'form_completed';

// 工作流输入定义
export interface WorkflowInput {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object';
  description: string;
  required: boolean;
  ai_prompt: string;
}

// 节点输出定义
export interface NodeOutput {
  name: string;
  type: string;
  description: string;
}

// 转换条件
export interface TransitionCondition {
  type: ConditionType;
  expression?: string;
  description: string;
}

// 子节点关系
export interface ChildNode {
  node_id: string;
  condition: TransitionCondition;
}

// AI指令
export interface AIInstructions {
  purpose: string;
  action: string;
  user_message?: string;
  success_handling?: string;
  error_handling?: string;
  true_path?: string;
  false_path?: string;
  validation?: string;
}

// 节点位置
export interface NodePosition {
  x: number;
  y: number;
}

// API调用配置
export interface APICallConfig {
  api_id: string;
  api_endpoint: string;
  method: string;
  parameters: Record<string, any>;
  ui_mode?: 'auto' | 'form';
  context_fields?: string[];
}

// 用户输入配置（已废弃，保留类型定义以兼容旧数据）
// @deprecated 所有用户输入现在通过 api_call 的 POST 表单完成
export interface UserInputConfig {
  input_type: 'form' | 'text' | 'choice' | 'number' | 'date' | 'file';
  form_schema?: Record<string, any>;
  choices?: Array<{
    label: string;
    value: string;
    description?: string;
  }>;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  placeholder?: string;
  default_value?: any;
  multiple?: boolean; // 是否支持多选
}

// 条件配置
export interface ConditionConfig {
  conditions: Array<{
    field: string; // 要判断的字段
    operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'not_contains' | 'exists' | 'not_exists';
    value: any; // 比较值
    data_type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  }>;
  logic: 'and' | 'or'; // 多个条件之间的逻辑关系
  evaluation_expression?: string; // 高级表达式（可选）
}

// 通知配置
export interface NotificationConfig {
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  channels?: string[];
}

// 节点配置联合类型
export type NodeConfig = APICallConfig | UserInputConfig | ConditionConfig | NotificationConfig | Record<string, any>;

// 工作流节点定义
export interface WorkflowNode {
  id: string;
  name: string;
  description: string;
  type: NodeType;
  position: NodePosition;
  parent_nodes: string[];
  child_nodes: ChildNode[];
  config: NodeConfig;
  outputs: NodeOutput[];
  ai_instructions: AIInstructions;
}

// 工作流定义
export interface WorkflowDefinition {
  id?: string;
  name: string;
  description: string;
  business_scenario: string;
  user_intents: string[];
  trigger_keywords: string[];
  inputs: WorkflowInput[];
  nodes: WorkflowNode[];
  node_relationships?: Record<string, {
    parents?: string[];
    children?: string[];
    conditions?: Array<{ type: string; [key: string]: any }>;
  }>;
  metadata?: {
    created_by?: string;
    created_at?: string;
    updated_at?: string;
    tags?: string[];
    complexity?: 'low' | 'medium' | 'high';
  };
}

// 工作流创建请求
export interface WorkflowCreateRequest {
  name: string;
  description: string;
  business_scenario: string;
  user_intents: string[];
  trigger_keywords: string[];
  inputs: WorkflowInput[];
  nodes: WorkflowNode[];
  metadata?: {
    tags?: string[];
    complexity?: 'low' | 'medium' | 'high';
  };
}

// 工作流更新请求
export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  business_scenario?: string;
  status?: 'draft' | 'active' | 'inactive' | 'archived';
  user_intents?: string[];
  trigger_keywords?: string[];
  inputs?: WorkflowInput[];
  nodes?: WorkflowNode[];
  metadata?: {
    tags?: string[];
    complexity?: 'low' | 'medium' | 'high';
  };
}

// 节点创建请求
export interface NodeCreateRequest {
  id: string;
  name: string;
  description: string;
  type: NodeType;
  position: NodePosition;
  parent_nodes: string[];
  child_nodes: ChildNode[];
  config: NodeConfig;
  outputs: NodeOutput[];
  ai_instructions: AIInstructions;
}

// 节点更新请求
export interface NodeUpdateRequest {
  name?: string;
  description?: string;
  position?: NodePosition;
  parent_nodes?: string[];
  child_nodes?: ChildNode[];
  config?: NodeConfig;
  outputs?: NodeOutput[];
  ai_instructions?: AIInstructions;
}

// 节点类型配置
export const NodeTypeConfigs: Record<NodeType, { 
  label: string; 
  color: string; 
  icon: string;
  description: string;
  defaultConfig: NodeConfig;
}> = {
  start: {
    label: '开始节点',
    color: '#52c41a',
    icon: 'play-circle',
    description: '工作流的入口点',
    defaultConfig: {}
  },

  api_call: {
    label: 'API调用',
    color: '#1890ff',
    icon: 'api',
    description: '调用系统中注册的API',
    defaultConfig: {
      api_id: '',
      api_endpoint: '',
      method: 'GET',
      parameters: {},
      ui_mode: 'auto',
      context_fields: []
    }
  },
  // user_input 已废弃，所有用户输入通过 api_call 的 POST 表单完成
  condition: {
    label: '条件判断',
    color: '#fa8c16',
    icon: 'branches',
    description: '根据条件决定流程走向',
    defaultConfig: {
      evaluation_expression: ''
    }
  },
  notification: {
    label: '通知节点',
    color: '#eb2f96',
    icon: 'notification',
    description: '向用户显示信息或提示',
    defaultConfig: {
      message: '',
      type: 'info'
    }
  },
  end: {
    label: '结束节点',
    color: '#f5222d',
    icon: 'stop',
    description: '工作流的结束点',
    defaultConfig: {}
  }
};

// Butterfly画布节点数据结构
export interface ButterflyNode {
  id: string;
  top: number;
  left: number;
  endpoints: Array<{
    id: string;
    orientation: [number, number];
    pos: [number, number];
  }>;
  render: (item: any) => React.ReactNode;
  data?: WorkflowNode;
}

// Butterfly画布边数据结构
export interface ButterflyEdge {
  id: string;
  sourceNode: string;
  targetNode: string;
  source: string;
  target: string;
  className?: string;
  arrowClassName?: string;
  labelRender?: () => React.ReactNode;
}

// Butterfly画布数据结构
export interface ButterflyData {
  nodes: ButterflyNode[];
  edges: ButterflyEdge[];
  groups?: any[];
}
