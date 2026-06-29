// 实体字段类型定义
export interface EntityField {
  id: string;
  name: string;
  displayName: string;
  type: 'text' | 'number' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'email' | 'phone' | 'select' | 'multiselect' | 'json' | 'file' | 'image' | 'reference';
  required: boolean;
  unique: boolean;
  defaultValue?: any;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  options?: string[]; // 用于枚举类型
  referenceTarget?: string; // 引用字段的目标实体
  description?: string;
  created_at: string;
  updated_at: string;
}

// 实体关系类型定义
export interface EntityRelationship {
  id: string;
  name: string;
  sourceEntity: string;
  targetEntity: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many' | 'hierarchy';
  foreignKey?: string;
  constraints?: {
    cascadeDelete: boolean;
    required: boolean;
    unique: boolean;
  };
  created_at: string;
  updated_at?: string;
}

// 实体统计信息
export interface EntityStatistics {
  record_count: number;
  field_count: number;
  relationship_count: number;
  last_updated: string;
}

// 实体定义
export interface Entity {
  id: string;
  name: string;
  displayName: string;
  description: string;
  icon?: string;
  isRole?: boolean;
  status: 'active' | 'inactive';
  fields: EntityField[];
  relationships: EntityRelationship[];
  statistics?: EntityStatistics;
  created_at: string;
  updated_at: string;
}

// 实体数据记录
export interface EntityDataRecord {
  id: string;
  [key: string]: any; // 动态字段
  created_at: string;
  updated_at: string;
}

// 创建实体请求
export interface EntityCreateRequest {
  name: string;
  displayName: string;
  description: string;
  icon?: string;
  isRole?: boolean;
  scenarioId?: string;
  fields: Omit<EntityField, 'id' | 'created_at' | 'updated_at'>[]; // 必填字段
}

// 更新实体请求
export interface EntityUpdateRequest {
  displayName?: string;
  description?: string;
  icon?: string;
  isRole?: boolean;
  fields?: EntityField[];
}

// 创建实体关系请求
export interface EntityRelationshipCreateRequest {
  name: string;
  targetEntity: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many' | 'hierarchy';
  foreignKey?: string;
  constraints?: {
    cascadeDelete: boolean;
    required: boolean;
    unique: boolean;
  };
}

// 实体字段验证规则
export interface FieldValidationRule {
  type: 'required' | 'unique' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

// 实体配置导出格式
export interface EntityConfig {
  name: string;
  displayName: string;
  description: string;
  icon?: string;
  fields: EntityField[];
  relationships: EntityRelationship[];
  version: string;
  exportedAt: string;
}

// 实体模板
export interface EntityTemplate {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: string;
  icon: string;
  fields: Omit<EntityField, 'id' | 'created_at' | 'updated_at'>[];
  relationships: Omit<EntityRelationship, 'id' | 'created_at' | 'updated_at'>[];
  tags: string[];
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedTime: number; // 预估配置时间（分钟）
}

// 实体关系图节点
export interface EntityGraphNode {
  id: string;
  name: string;
  displayName: string;
  type: 'entity';
  position: {
    x: number;
    y: number;
  };
  data: {
    entity: Entity;
    fieldCount: number;
    relationshipCount: number;
  };
}

// 实体关系图边
export interface EntityGraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'relationship';
  data: {
    relationship: EntityRelationship;
    label: string;
    relationshipType: string;
  };
}

// 实体关系图
export interface EntityGraph {
  nodes: EntityGraphNode[];
  edges: EntityGraphEdge[];
}

// 实体验证结果
export interface EntityValidationResult {
  isValid: boolean;
  errors: {
    field: string;
    message: string;
    type: 'error' | 'warning';
  }[];
  warnings: {
    field: string;
    message: string;
  }[];
}

// 实体导入结果
export interface EntityImportResult {
  success: boolean;
  imported: Entity[];
  failed: {
    name: string;
    reason: string;
  }[];
  warnings: string[];
}

// 实体搜索过滤器
export interface EntitySearchFilter {
  keyword?: string;
  status?: 'active' | 'inactive';
  hasFields?: boolean;
  hasRelationships?: boolean;
  createdAfter?: string;
  createdBefore?: string;
  tags?: string[];
}

// 实体排序选项
export interface EntitySortOption {
  field: 'name' | 'displayName' | 'created_at' | 'updated_at' | 'field_count' | 'relationship_count';
  order: 'asc' | 'desc';
}

// 实体分页参数
export interface EntityPaginationParams {
  page: number;
  page_size: number;
  total?: number;
}

// 实体操作历史
export interface EntityOperationHistory {
  id: string;
  entityId: string;
  operation: 'create' | 'update' | 'delete' | 'field_add' | 'field_update' | 'field_delete' | 'relationship_add' | 'relationship_delete';
  operatorId: string;
  operatorName: string;
  changes: {
    field: string;
    oldValue: any;
    newValue: any;
  }[];
  timestamp: string;
  description: string;
}

// 实体权限
export interface EntityPermission {
  entityId: string;
  userId: string;
  permissions: {
    read: boolean;
    write: boolean;
    delete: boolean;
    manage_fields: boolean;
    manage_relationships: boolean;
    manage_data: boolean;
  };
  grantedAt: string;
  grantedBy: string;
}

// 实体备份
export interface EntityBackup {
  id: string;
  entityId: string;
  name: string;
  description: string;
  data: EntityConfig;
  createdAt: string;
  createdBy: string;
  size: number; // 备份大小（字节）
}

// 实体恢复选项
export interface EntityRestoreOptions {
  backupId: string;
  restoreFields: boolean;
  restoreRelationships: boolean;
  restoreData: boolean;
  overwriteExisting: boolean;
}
