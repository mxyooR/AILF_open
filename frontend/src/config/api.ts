/**
 * API配置文件
 */

// API基础URL - 使用相对路径，通过代理访问后端
export const API_BASE_URL = '';

// API端点
export const API_ENDPOINTS = {
  // 认证模块
  AUTH: {
    DEVELOPER: '/api/v1/auth/developer',
    VERIFY_TOKEN: '/api/v1/auth/developer/verify-token',
  },

  // 场景管理
  SCENARIO: {
    BASE: '/api/v1/scenario',
    BY_ID: (id: string) => `/api/v1/scenario/${id}`,
    LIST: '/api/v1/scenario',
    ACTIVATE: (id: string) => `/api/v1/scenario/${id}/activate`,
    FROM_TEMPLATE: '/api/v1/scenario/from-template',
    VALIDATE: '/api/v1/scenario/validate',
  },

  // 模板管理
  TEMPLATES: {
    BASE: '/api/v1/templates',
    BY_KEY: (key: string) => `/api/v1/templates/${key}`,
    CATEGORIES: '/api/v1/templates/categories',
    BY_CATEGORY: (category: string) => `/api/v1/templates/category/${category}`,
    SEARCH: (keyword: string) => `/api/v1/templates/search/${keyword}`,
    RELOAD: '/api/v1/templates/reload',
  },



  // 路由管理
  ROUTES: {
    BASE: '/api/v1/routes',
    REGISTER: '/api/v1/routes/register',
    BY_ID: (id: string) => `/api/v1/routes/${id}`,
  },

  // 角色管理
  ROLES: {
    BASE: '/api/v1/roles',
    BY_ID: (id: string) => `/api/v1/roles/${id}`,
  },

  // 权限管理
  PERMISSIONS: {
    BASE: '/api/v1/permissions',
    CHECK: '/api/v1/permissions/check',
    USER_APIS: '/api/v1/permissions/user-apis',
    ROLE_API: '/api/v1/permissions/role-api',
    BATCH_UPDATE: '/api/v1/permissions/batch-update',
  },

  // AI交互
  AI: {
    COMMAND_ASYNC: '/api/v1/command/async',
    COMMAND_ASYNC_STATUS: (taskId: string) => `/api/v1/command/async/${taskId}`,
  },

  // 配置状态
  CONFIGURATION_STATUS: {
    CHECK: '/api/v1/configuration/status/check',
    DETAIL: '/api/v1/configuration/status',
    UPDATE_STEP: '/api/v1/configuration/status/step',
    RESET: '/api/v1/configuration/status/reset',
  },

  // 健康检查
  HEALTH: '/api/v1/health',
};

// 构建完整URL的辅助函数
export const buildUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};

// 常用的API调用函数
export const apiUrls = {
  // 认证
  developerAuth: () => buildUrl(API_ENDPOINTS.AUTH.DEVELOPER),
  verifyToken: () => buildUrl(API_ENDPOINTS.AUTH.VERIFY_TOKEN),
  
  // 场景管理
  scenario: () => buildUrl(API_ENDPOINTS.SCENARIO.BASE),
  scenarioById: (id: string) => buildUrl(API_ENDPOINTS.SCENARIO.BY_ID(id)),
  scenarios: () => buildUrl(API_ENDPOINTS.SCENARIO.LIST),
  activateScenario: (id: string) => buildUrl(API_ENDPOINTS.SCENARIO.ACTIVATE(id)),
  scenarioFromTemplate: () => buildUrl(API_ENDPOINTS.SCENARIO.FROM_TEMPLATE),
  validateScenario: () => buildUrl(API_ENDPOINTS.SCENARIO.VALIDATE),
  
  // 模板管理
  templates: () => buildUrl(API_ENDPOINTS.TEMPLATES.BASE),
  templateByKey: (key: string) => buildUrl(API_ENDPOINTS.TEMPLATES.BY_KEY(key)),
  templateCategories: () => buildUrl(API_ENDPOINTS.TEMPLATES.CATEGORIES),
  templatesByCategory: (category: string) => buildUrl(API_ENDPOINTS.TEMPLATES.BY_CATEGORY(category)),
  searchTemplates: (keyword: string) => buildUrl(API_ENDPOINTS.TEMPLATES.SEARCH(keyword)),
  reloadTemplates: () => buildUrl(API_ENDPOINTS.TEMPLATES.RELOAD),
  

  
  // 路由管理
  routes: () => buildUrl(API_ENDPOINTS.ROUTES.BASE),
  registerRoute: () => buildUrl(API_ENDPOINTS.ROUTES.REGISTER),
  routeById: (id: string) => buildUrl(API_ENDPOINTS.ROUTES.BY_ID(id)),
  
  // 角色管理
  roles: () => buildUrl(API_ENDPOINTS.ROLES.BASE),
  roleById: (id: string) => buildUrl(API_ENDPOINTS.ROLES.BY_ID(id)),
  
  // 权限管理
  permissions: () => buildUrl(API_ENDPOINTS.PERMISSIONS.BASE),
  checkPermission: () => buildUrl(API_ENDPOINTS.PERMISSIONS.CHECK),
  userApis: () => buildUrl(API_ENDPOINTS.PERMISSIONS.USER_APIS),
  roleApiPermission: () => buildUrl(API_ENDPOINTS.PERMISSIONS.ROLE_API),
  batchUpdatePermissions: () => buildUrl(API_ENDPOINTS.PERMISSIONS.BATCH_UPDATE),
  
  // AI交互
  aiCommandAsync: () => buildUrl(API_ENDPOINTS.AI.COMMAND_ASYNC),
  aiCommandAsyncStatus: (taskId: string) => buildUrl(API_ENDPOINTS.AI.COMMAND_ASYNC_STATUS(taskId)),

  // 配置状态
  configurationStatusCheck: () => buildUrl(API_ENDPOINTS.CONFIGURATION_STATUS.CHECK),
  configurationStatusDetail: () => buildUrl(API_ENDPOINTS.CONFIGURATION_STATUS.DETAIL),
  configurationStatusUpdateStep: () => buildUrl(API_ENDPOINTS.CONFIGURATION_STATUS.UPDATE_STEP),
  configurationStatusReset: () => buildUrl(API_ENDPOINTS.CONFIGURATION_STATUS.RESET),

  // 健康检查
  health: () => buildUrl(API_ENDPOINTS.HEALTH),
};
