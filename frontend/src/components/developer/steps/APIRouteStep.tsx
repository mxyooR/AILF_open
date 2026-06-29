/**
 * API路由管理步骤组件 - 完全符合API文档
 * 支持增删改查和所有API功能
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Button,
  Form,
  Input,
  Select,
  Modal,
  Space,
  Tag,
  Tooltip,
  message,
  Row,
  Col,
  Switch,
  Badge,
  Tabs,
  Divider,
  Alert,
  Descriptions,
  Timeline,
  Empty,
  Statistic,
  Table,
  Collapse,
  Card,
  notification,
  Typography,
  Upload,
  InputNumber,
  Checkbox,
  Radio
} from 'antd';

import { UnifiedCard, StatsCard } from '../common';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  StopOutlined,
  BarChartOutlined,
  ReloadOutlined,
  EyeOutlined,
  HeartOutlined,
  ExclamationCircleOutlined,
  DownloadOutlined,
  PlayCircleOutlined,
  ThunderboltOutlined,
  CameraOutlined,
  FileImageOutlined,
  DatabaseOutlined,
  UploadOutlined,
  InboxOutlined,
  FolderOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { routeAPI } from '../../../services/developer/routeAPI';
import { servicePackageAPI } from '../../../services/developer/servicePackageAPI';
import { authAPI } from '../../../services/developer/authAPI';
import DynamicAPIService from '../../../services/common/dynamicAPI';
import DynamicResponseConfig from '../DynamicResponseConfig';
import { tokenManager } from '../../../services/common/tokenManager';

import type {
  APIRoute,
  APIRouteCreateRequest,
  APIRouteUpdateRequest,
  HandlerType,
  HttpMethod,
  RouteQueryParams,
  RouteHealthResponse,
  APIParameter,
  ResponseDefinition
} from '../../../types/developer/route';
import type { ServicePackageInfo } from '../../../types/developer/servicePackage';
import { HandlerTypeConfigs } from '../../../types/developer/route';
import './APIRouteStep.css';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Text } = Typography;

type ResponseConfigMode = 'direct' | 'document' | 'advanced';

const DIRECT_OUTPUT_HANDLER_TYPES = new Set<HandlerType>(['image_display', 'file_download']);
const DOCUMENT_OUTPUT_HANDLER_TYPES = new Set<HandlerType>(['static_data']);

const getResponseConfigMode = (handlerType?: string): ResponseConfigMode => {
  if (!handlerType) {
    return 'advanced';
  }
  if (DIRECT_OUTPUT_HANDLER_TYPES.has(handlerType as HandlerType)) {
    return 'direct';
  }
  if (DOCUMENT_OUTPUT_HANDLER_TYPES.has(handlerType as HandlerType)) {
    return 'document';
  }
  return 'advanced';
};

const buildDefaultResponses = (): ResponseDefinition => ({
  '200': {
    description: 'Success',
    schema: {
      type: 'object',
      properties: {
        code: { type: 'integer', example: 200 },
        message: { type: 'string', example: 'Success' },
        data: { type: 'object' }
      }
    }
  }
});

const extractStaticResponseExample = (responses?: any): Record<string, any> | null => {
  if (!responses || typeof responses !== 'object') {
    return null;
  }
  const response200 = responses['200'] || responses[200];
  if (!response200 || typeof response200 !== 'object') {
    return null;
  }
  const schema = response200.schema || response200.response_schema;
  if (schema && typeof schema === 'object' && schema.example && typeof schema.example === 'object') {
    return schema.example;
  }
  return null;
};

interface APIRouteStepProps {
  onNext?: () => void;
  onPrev?: () => void;
}

const APIRouteStep: React.FC<APIRouteStepProps> = ({ onNext, onPrev }) => {
  const [routes, setRoutes] = useState<APIRoute[]>([]);
  const [servicePackages, setServicePackages] = useState<ServicePackageInfo[]>([]);
  const [loadingServicePackages, setLoadingServicePackages] = useState(false);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRoute, setEditingRoute] = useState<APIRoute | null>(null);
  const [entities, setEntities] = useState<any[]>([]);
  const [loadingEntities, setLoadingEntities] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState<APIRoute | null>(null);
  const [healthModalVisible, setHealthModalVisible] = useState(false);
  const [healthData, setHealthData] = useState<RouteHealthResponse | null>(null);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [testingRoute, setTestingRoute] = useState<APIRoute | null>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const previousPreviewUrlRef = useRef<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [batchTestModalVisible, setBatchTestModalVisible] = useState(false);
  const [batchTestLoading, setBatchTestLoading] = useState(false);
  const [batchTestResults, setBatchTestResults] = useState<any[]>([]);
  const [selectedBatchRouteIds, setSelectedBatchRouteIds] = useState<string[]>([]);
  const [batchRoutes, setBatchRoutes] = useState<APIRoute[]>([]);
  const [form] = Form.useForm();
  const [testForm] = Form.useForm();
  const [queryParams, setQueryParams] = useState<RouteQueryParams>({});
  const [summary, setSummary] = useState({
    total_routes: 0,
    active_routes: 0,
    inactive_routes: 0,
    total_calls: 0,
    avg_response_time: 0,
    healthy_routes: 0,
    warning_routes: 0,
    unhealthy_routes: 0,
    overall_success_rate: 0
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
    pages: 0,
    has_next: false,
    has_prev: false
  });

  const updateEntityCrudConfig = (overrides: Record<string, any> = {}) => {
    const entityName = overrides.entity_name ?? form.getFieldValue('entity_name');
    if (!entityName) {
      return;
    }
    const operation = overrides.operation ?? form.getFieldValue('crud_operation') ?? 'list';
    const queryField = overrides.query_field ?? form.getFieldValue('query_field');
    const queryParam = overrides.query_param ?? form.getFieldValue('query_param');
    const queryLocation = overrides.query_location ?? form.getFieldValue('query_location');

    const config: Record<string, any> = {
      entity_name: entityName,
      operation,
      pagination: (operation === 'list' || operation === 'search') ? {
        page_size: 20,
        max_page_size: 100
      } : undefined,
      filters_enabled: operation === 'list' || operation === 'search',
      sorting_enabled: operation === 'list' || operation === 'search'
    };

    if (operation === 'get') {
      if (queryField) {
        config.query_field = queryField;
      }
      if (queryParam) {
        config.query_param = queryParam;
      }
      if (queryLocation) {
        config.query_location = queryLocation;
      }
    }

    form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
  };

  const updateCustomFunctionConfig = (serviceName?: string, methodName?: string) => {
    if (!serviceName || !methodName) {
      return;
    }
    let currentConfig: Record<string, any> = {};
    try {
      const rawConfig = form.getFieldValue('handler_config');
      if (typeof rawConfig === 'string' && rawConfig.trim()) {
        const parsed = JSON.parse(rawConfig);
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          currentConfig = parsed;
        }
      }
    } catch {
      currentConfig = {};
    }
    form.setFieldValue(
      'handler_config',
      JSON.stringify({ ...currentConfig, service: serviceName, method: methodName }, null, 2)
    );
  };

  const updateProxyConfig = (targetUrl?: string) => {
    if (!targetUrl) {
      return;
    }
    form.setFieldValue('handler_config', JSON.stringify({ target_url: targetUrl }, null, 2));
  };

  const updateScriptConfig = (language?: string, script?: string) => {
    if (!script) {
      return;
    }
    form.setFieldValue('handler_config', JSON.stringify({ language: language || 'python', script }, null, 2));
  };

  const updateStaticDataConfig = (dataText?: string) => {
    if (!dataText) {
      return;
    }
    try {
      const parsed = JSON.parse(dataText);
      form.setFieldValue('handler_config', JSON.stringify({ data: parsed }, null, 2));
    } catch {
      // ignore parse errors here; validation happens on save
    }
  };


  // HTTP方法选项
  const httpMethods: HttpMethod[] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

  // 加载API路由列表
  const loadRoutes = useCallback(async () => {
    setLoading(true);
    try {
      const response = await routeAPI.getRoutes({
        ...queryParams,
        page: pagination.page,
        limit: pagination.limit
      });

      if (response.code === 200 && response.data) {
        setRoutes(response.data.routes || []);
        setSummary(prevSummary => ({
          ...prevSummary,
          ...response.data.summary
        }));
        setPagination(prevPagination => response.data.pagination || prevPagination);
      } else {
        message.error(response.message || '加载API路由失败');
      }
    } catch (error: any) {
      console.error('加载API路由失败:', error);
      const errorMsg = error.response?.data?.message || error.message || '加载API路由失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [queryParams, pagination.page, pagination.limit]);

  // 加载实体列表
  const loadServicePackages = async () => {
    setLoadingServicePackages(true);
    try {
      const response = await servicePackageAPI.listPackages();
      if (response.code === 200 && response.data) {
        setServicePackages(response.data.services || []);
      }
    } catch (error: any) {
      console.error('load service packages failed:', error);
    } finally {
      setLoadingServicePackages(false);
    }
  };

  const loadEntities = async () => {
    setLoadingEntities(true);
    try {
      const token = tokenManager.getToken();
      if (!token) {
        console.error('No developer token available');
        setLoadingEntities(false);
        return;
      }

      const response = await fetch('/api/v1/entities?include_fields=false&status=active', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.code === 200 && data.data) {
          // 转换为选项格式
          const options = data.data.entities.map((entity: any) => ({
            value: entity.name,
            label: entity.displayName,
            description: entity.description,
            field_count: entity.field_count,
            record_count: entity.record_count
          }));
          setEntities(options);
        } else {
          console.error('获取实体列表失败:', data.message);
        }
      } else {
        console.error('获取实体列表失败');
      }
    } catch (error: any) {
      console.error('获取实体列表失败:', error);
    } finally {
      setLoadingEntities(false);
    }
  };

  // 加载健康检查数据
  const loadHealthData = async () => {
    try {
      const response = await routeAPI.getRoutesHealth();
      if (response.code === 200 && response.data) {
        setHealthData(response.data);
      }
    } catch (error: any) {
      console.error('加载健康检查数据失败:', error);
    }
  };

  useEffect(() => {
    // 初始化认证并加载数据
    const initializeData = async () => {
      try {
        const authSuccess = await authAPI.initAuth();
        if (authSuccess) {
          console.log('✅ 开发者认证成功');
          loadRoutes();
          loadHealthData();
          loadEntities();
          loadServicePackages();
        } else {
          message.error('开发者认证失败，请检查配置');
        }
      } catch (error) {
        console.error('初始化失败:', error);
        message.error('初始化失败');
      }
    };

    initializeData();
  }, [loadRoutes]);

  

  // 获取HTTP方法颜色
  const getMethodColor = (method: HttpMethod) => {
    const colors: Record<HttpMethod, string> = {
      GET: 'green',
      POST: 'blue',
      PUT: 'orange',
      DELETE: 'red',
      PATCH: 'purple'
    };
    return colors[method] || 'default';
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'success',
      inactive: 'error',
      maintenance: 'warning',
      deprecated: 'default'
    };
    return colors[status] || 'default';
  };

  // 获取健康状态颜色
  const getHealthColor = (health: string) => {
    const colors: Record<string, string> = {
      healthy: 'success',
      warning: 'warning',
      unhealthy: 'error',
      unknown: 'default'
    };
    return colors[health] || 'default';
  };

  // 动态API测试功能
  const handleTestRoute = (route: APIRoute) => {
    setTestingRoute(route);
    setTestResult(null);
    setTestModalVisible(true);
    
    // 根据路由参数预填测试表单
    if (route.parameters && route.parameters.length > 0) {
      const formData: any = {};
      route.parameters.forEach((param: any) => {
        // 如果参数有选项（select类型），使用第一个选项作为默认值
        if (param.options && Array.isArray(param.options) && param.options.length > 0) {
          formData[param.name] = param.options[0];
        }
        // 为不同类型的参数设置默认值
        else if (param.type === 'string') {
          if (param.name === 'name') formData[param.name] = '测试用户';
          else if (param.name === 'id_card') formData[param.name] = '110101199001011234';
          else if (param.name === 'phone') formData[param.name] = '13800138000';
          else if (param.name === 'email') formData[param.name] = 'test@example.com';
          else if (param.name === 'gender') formData[param.name] = '男';
          else if (param.name === 'passenger_type') formData[param.name] = '成人';
          else formData[param.name] = '测试数据';
        } else if (param.type === 'integer' || param.type === 'number') {
          if (param.name === 'age') formData[param.name] = 25;
          else if (param.name === 'page') formData[param.name] = 1;
          else if (param.name === 'limit') formData[param.name] = 10;
          else formData[param.name] = 1;
        } else if (param.type === 'boolean') {
          formData[param.name] = true;
        } else if (param.type === 'select') {
          // select类型但没有options时，尝试使用常见默认值
          if (param.name === 'gender') formData[param.name] = '男';
          else if (param.name === 'passenger_type') formData[param.name] = '成人';
          else if (param.name === 'status') formData[param.name] = '正常';
        }
      });
      testForm.setFieldsValue(formData);
    }
  };

  const executeAPITest = async (values: any) => {
    if (!testingRoute) return;
    
    setTestLoading(true);
    setTestResult(null);
    let resolvedEndpoint = testingRoute.endpoint;
    
    try {
      const startTime = Date.now();
      
      // 准备请求参数
      const pathParams: any = {};
      const requestParams: any = {};
      const requestData: any = {};
      
      // 根据参数位置分类数据
      if (testingRoute.parameters) {
        testingRoute.parameters.forEach((param: any) => {
          const value = values[param.name];
          if (value !== undefined && value !== null && value !== '') {
            if (param.location === 'query') {
              requestParams[param.name] = value;
            } else if (param.location === 'path') {
              pathParams[param.name] = value;
            } else if (param.location === 'body') {
              requestData[param.name] = value;
            }
          }
        });
      }

      Object.entries(pathParams).forEach(([key, value]) => {
        resolvedEndpoint = resolvedEndpoint.replace(`{${key}}`, encodeURIComponent(String(value)));
      });

      const handlerType = testingRoute.handler_type || testingRoute.handler?.type;
      if (handlerType === 'image_display') {
        const imageId =
          pathParams.image_id ||
          pathParams.id ||
          requestParams.image_id ||
          requestParams.id ||
          requestParams.filename ||
          requestParams.file;

        if (imageId && !resolvedEndpoint.includes('{') && !resolvedEndpoint.endsWith(`/${imageId}`)) {
          resolvedEndpoint = `${resolvedEndpoint.replace(/\/$/, '')}/${encodeURIComponent(String(imageId))}`;
        }

        const searchParams = new URLSearchParams();
        Object.entries(requestParams).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            searchParams.append(key, String(value));
          }
        });

        const requestUrl = `${resolvedEndpoint}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
        const token = tokenManager.getToken();
        const response = await fetch(requestUrl, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined
        });

        if (!response.ok) {
          throw new Error(`请求失败 (${response.status})`);
        }

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.startsWith('image/')) {
          const text = await response.text();
          throw new Error(`响应不是图片: ${contentType || 'unknown'}${text ? ` - ${text}` : ''}`);
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const endTime = Date.now();
        const executionTime = endTime - startTime;

        setTestResult({
          success: true,
          data: {
            image_url: objectUrl,
            source_url: requestUrl,
            content_type: contentType,
            size: blob.size
          },
          statusCode: response.status,
          headers: {},
          executionTime,
          timestamp: new Date().toISOString(),
          request: {
            method: testingRoute.method,
            endpoint: resolvedEndpoint,
            params: requestParams,
            data: requestData
          }
        });

        notification.success({
          message: 'API测试成功',
          description: `${testingRoute.method} ${resolvedEndpoint} 执行时间: ${executionTime}ms`,
          duration: 3
        });
        return;
      }

      if (handlerType === 'file_download' || handlerType === 'media_streaming') {
        const searchParams = new URLSearchParams();
        Object.entries(requestParams).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            searchParams.append(key, String(value));
          }
        });

        const requestUrl = `${resolvedEndpoint}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
        const token = tokenManager.getToken();
        const response = await fetch(requestUrl, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined
        });

        if (!response.ok) {
          throw new Error(`请求失败 (${response.status})`);
        }

        const contentType = response.headers.get('content-type') || 'application/octet-stream';
        const disposition = response.headers.get('content-disposition') || '';
        const matchedName =
          disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1] ||
          disposition.match(/filename=\"?([^\";]+)\"?/i)?.[1] ||
          '';
        const filename = matchedName ? decodeURIComponent(matchedName) : '';

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const endTime = Date.now();
        const executionTime = endTime - startTime;

        setTestResult({
          success: true,
          data: {
            file_url: objectUrl,
            source_url: requestUrl,
            filename,
            content_type: contentType,
            disposition,
            size: blob.size
          },
          statusCode: response.status,
          headers: {},
          executionTime,
          timestamp: new Date().toISOString(),
          request: {
            method: testingRoute.method,
            endpoint: resolvedEndpoint,
            params: requestParams,
            data: requestData
          }
        });

        notification.success({
          message: 'API测试成功',
          description: `${testingRoute.method} ${resolvedEndpoint} 执行时间: ${executionTime}ms`,
          duration: 3
        });
        return;
      }
      
      // 调用动态API
      const result = await DynamicAPIService.callDynamicAPI({
        method: testingRoute.method,
        endpoint: resolvedEndpoint,
        params: requestParams,
        data: requestData
      });
      
      const endTime = Date.now();
      const executionTime = endTime - startTime;
      
      setTestResult({
        ...result,
        executionTime,
        timestamp: new Date().toISOString(),
        request: {
          method: testingRoute.method,
          endpoint: resolvedEndpoint,
          params: requestParams,
          data: requestData
        }
      });
      
      if (result.success) {
        notification.success({
          message: 'API测试成功',
          description: `${testingRoute.method} ${resolvedEndpoint} 执行时间: ${executionTime}ms`,
          duration: 3
        });
      } else {
        notification.error({
          message: 'API测试失败',
          description: result.error || '未知错误',
          duration: 5
        });
      }
      
    } catch (error: any) {
      console.error('API测试失败:', error);
      setTestResult({
        success: false,
        error: error.message || '测试执行失败',
        statusCode: 500,
        executionTime: 0,
        timestamp: new Date().toISOString(),
        request: {
          method: testingRoute.method,
          endpoint: resolvedEndpoint || testingRoute.endpoint,
          params: {},
          data: values
        }
      });
      
      notification.error({
        message: 'API测试异常',
        description: error.message || '测试执行过程中发生错误',
        duration: 5
      });
    } finally {
      setTestLoading(false);
    }
  };

  useEffect(() => {
    const nextUrl = testResult?.data?.image_url || testResult?.data?.file_url;
    if (
      previousPreviewUrlRef.current &&
      previousPreviewUrlRef.current !== nextUrl &&
      previousPreviewUrlRef.current.startsWith('blob:')
    ) {
      URL.revokeObjectURL(previousPreviewUrlRef.current);
    }
    previousPreviewUrlRef.current = nextUrl || null;
  }, [testResult]);

  useEffect(() => {
    return () => {
      if (previousPreviewUrlRef.current && previousPreviewUrlRef.current.startsWith('blob:')) {
        URL.revokeObjectURL(previousPreviewUrlRef.current);
      }
    };
  }, []);

  const getDefaultBatchParamValue = (param: any): any => {
    if (param == null || typeof param !== 'object') return '';
    if (param.default !== undefined && param.default !== null && param.default !== '') return param.default;
    if (param.example !== undefined && param.example !== null && param.example !== '') return param.example;

    if (Array.isArray(param.options) && param.options.length > 0) {
      const first = param.options[0];
      if (typeof first === 'object' && first !== null) {
        return first.value ?? first.label ?? '';
      }
      return first;
    }
    if (Array.isArray(param.enum) && param.enum.length > 0) {
      return param.enum[0];
    }

    const name = String(param.name || '').toLowerCase();
    const type = String(param.type || 'string').toLowerCase();

    if (type === 'boolean') return true;
    if (type === 'integer') return 1;
    if (type === 'number') return 1;

    if (name.includes('id_card')) return '110101199001011234';
    if (name.includes('phone')) return '13800138000';
    if (name.includes('email')) return 'test@example.com';
    if (name.includes('ticket_number') || name.includes('ticket_no') || name === 'ticket_id') return 'T260211035136';
    if (name.includes('train_number')) return 'G1001';
    if (name.includes('station_code')) return 'SHH';
    if (name.includes('passenger_type')) return '成人';
    if (name.includes('gender')) return '男';
    if (name.includes('city')) return '上海';
    if (name.includes('province')) return '上海';
    if (name.includes('date')) return '2026-02-14';
    if (name.includes('status')) return '正常';
    if (name.includes('name')) return '测试用户';
    if (name.includes('page')) return 1;
    if (name.includes('limit')) return 10;
    return type === 'string' ? '测试数据' : '';
  };

  const buildBatchTestRequest = (route: APIRoute) => {
    let resolvedEndpoint = route.endpoint;
    const requestParams: Record<string, any> = {};
    const requestData: Record<string, any> = {};
    const missingRequired: string[] = [];
    const parameters = Array.isArray(route.parameters) ? route.parameters : [];

    parameters.forEach((param: any) => {
      const value = getDefaultBatchParamValue(param);
      const isEmpty = value === undefined || value === null || value === '';
      if (param?.required && isEmpty) {
        missingRequired.push(param.name);
        return;
      }
      if (isEmpty) return;

      const location = param.location || 'body';
      if (location === 'path') {
        const encoded = encodeURIComponent(String(value));
        resolvedEndpoint = resolvedEndpoint.replace(`{${param.name}}`, encoded);
      } else if (location === 'query') {
        requestParams[param.name] = value;
      } else if (location === 'body') {
        requestData[param.name] = value;
      }
    });

    const unresolvedPathParams = Array.from(resolvedEndpoint.matchAll(/\{([^}]+)\}/g)).map(match => match[1]);
    unresolvedPathParams.forEach((name) => {
      if (!missingRequired.includes(name)) {
        missingRequired.push(name);
      }
    });

    return {
      resolvedEndpoint,
      requestParams,
      requestData,
      missingRequired
    };
  };

  const loadAllActiveRoutesForBatch = async (): Promise<APIRoute[]> => {
    const allRoutes: APIRoute[] = [];
    let page = 1;
    const limit = 100;
    let hasNext = true;
    let guard = 0;

    while (hasNext && guard < 100) {
      const response = await routeAPI.getRoutes({ status: 'active', page, limit });
      if (response.code !== 200 || !response.data) {
        throw new Error(response.message || '加载批量测试路由失败');
      }
      const pageRoutes = response.data.routes || [];
      allRoutes.push(...pageRoutes);
      hasNext = Boolean(response.data.pagination?.has_next);
      page += 1;
      guard += 1;
      if (!response.data.pagination && pageRoutes.length < limit) {
        hasNext = false;
      }
    }

    const uniqueMap = new Map<string, APIRoute>();
    allRoutes.forEach((route) => uniqueMap.set(route.id, route));
    return Array.from(uniqueMap.values());
  };

  const openBatchTestModal = async () => {
    try {
      setBatchTestLoading(true);
      const activeRoutes = await loadAllActiveRoutesForBatch();
      if (activeRoutes.length === 0) {
        message.warning('没有可测试的活跃路由');
        return;
      }
      setBatchRoutes(activeRoutes);
      const defaultSelected = activeRoutes.filter(route => route.method === 'GET').map(route => route.id);
      setSelectedBatchRouteIds(defaultSelected);
      setBatchTestResults([]);
      setBatchTestModalVisible(true);
    } catch (error: any) {
      message.error(error?.message || '加载批量测试路由失败');
    } finally {
      setBatchTestLoading(false);
    }
  };

  // 批量测试API
  const handleBatchTest = async () => {
    const activeRoutes = batchRoutes;
    if (activeRoutes.length === 0) {
      message.warning('没有可测试的活跃路由');
      return;
    }

    const selectedRoutes = activeRoutes.filter(route => selectedBatchRouteIds.includes(route.id));
    if (selectedRoutes.length === 0) {
      message.warning('请先勾选要测试的路由');
      return;
    }

    setBatchTestLoading(true);
    setBatchTestResults([]);

    const results: any[] = [];
    try {
      for (const route of selectedRoutes) {
        const { resolvedEndpoint, requestParams, requestData, missingRequired } = buildBatchTestRequest(route);
        if (missingRequired.length > 0) {
          results.push({
            key: route.id,
            routeName: route.name,
            method: route.method,
            endpoint: route.endpoint,
            success: false,
            statusCode: 400,
            executionTime: 0,
            error: `缺少必填参数: ${missingRequired.join(', ')}`,
            data: { missingRequired }
          });
          continue;
        }

        const handlerType = route.handler_type || route.handler?.type;
        const isDirectOutput =
          handlerType === 'image_display' ||
          handlerType === 'file_download' ||
          handlerType === 'media_streaming';

        if (isDirectOutput) {
          const startTime = Date.now();
          try {
            const searchParams = new URLSearchParams();
            Object.entries(requestParams).forEach(([key, value]) => {
              if (value !== undefined && value !== null && value !== '') {
                searchParams.append(key, String(value));
              }
            });
            const requestUrl = `${resolvedEndpoint}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
            const token = tokenManager.getToken();
            const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
            const methodHasBody = !['GET', 'DELETE'].includes(route.method);
            if (methodHasBody && Object.keys(requestData).length > 0) {
              headers['Content-Type'] = 'application/json';
            }
            const response = await fetch(requestUrl, {
              method: route.method,
              headers,
              body: methodHasBody && Object.keys(requestData).length > 0 ? JSON.stringify(requestData) : undefined
            });
            results.push({
              key: route.id,
              routeName: route.name,
              method: route.method,
              endpoint: requestUrl,
              success: response.ok,
              statusCode: response.status,
              executionTime: Date.now() - startTime,
              error: response.ok ? undefined : `HTTP ${response.status}`,
              data: {
                handlerType,
                request: {
                  method: route.method,
                  endpoint: requestUrl,
                  params: requestParams,
                  data: requestData
                }
              }
            });
          } catch (error: any) {
            results.push({
              key: route.id,
              routeName: route.name,
              method: route.method,
              endpoint: resolvedEndpoint,
              success: false,
              statusCode: 500,
              executionTime: Date.now() - startTime,
              error: error?.message || '请求失败'
            });
          }
        } else {
          const result = await DynamicAPIService.callDynamicAPI({
            method: route.method,
            endpoint: resolvedEndpoint,
            params: requestParams,
            data: requestData
          });
          results.push({
            key: route.id,
            routeName: route.name,
            method: route.method,
            endpoint: resolvedEndpoint,
            success: result.success,
            statusCode: result.statusCode,
            executionTime: result.executionTime || 0,
            error: result.error,
            data: result.data
          });
        }
      }

      setBatchTestResults(results);
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;
      message.success(`批量测试完成：成功 ${successCount}，失败 ${failCount}`);
    } catch (error: any) {
      message.error('批量测试失败: ' + error.message);
    } finally {
      setBatchTestLoading(false);
    }
  };

  // 处理查看详情
  const handleViewDetail = async (route: APIRoute) => {
    try {
      const response = await routeAPI.getRoute(route.id);
      if (response.code === 200 && response.data) {
        setSelectedRoute(response.data.route);
        setDetailModalVisible(true);
      } else {
        message.error(response.message || '获取路由详情失败');
      }
    } catch (error: any) {
      console.error('获取路由详情失败:', error);
      message.error('获取路由详情失败');
    }
  };

  // 处理编辑路由
  const handleEditRoute = (route: APIRoute) => {
    setEditingRoute(route);
    
    // 确保参数格式正确
    let parametersStr = '';
    if (route.parameters && Array.isArray(route.parameters)) {
      parametersStr = JSON.stringify(route.parameters, null, 2);
    }
    
    // 处理响应数据 - 直接传递对象给DynamicResponseConfig
    let responsesData: any = {};
    if (route.responses && typeof route.responses === 'object') {
      responsesData = route.responses;
    }
    if (route.dynamic_rules && Array.isArray(route.dynamic_rules)) {
      responsesData = {
        ...responsesData,
        dynamic_rules: route.dynamic_rules
      };
    }
    const hasDynamicRules = Array.isArray(route.dynamic_rules) && route.dynamic_rules.length > 0;
    const staticResponseExample = extractStaticResponseExample(route.responses);
    
    // 在编辑时，显示去掉 /api/v1/ 前缀的简洁路径
    let displayEndpoint = route.endpoint;
    if (displayEndpoint.startsWith('/api/v1/')) {
      displayEndpoint = '/api' + displayEndpoint.substring('/api/v1'.length);
    }

    // 从handler_config中解析entity_name和crud_operation
    let entityName = '';
    let crudOperation = 'list';
    let queryField = '';
    let queryParam = '';
    let queryLocation = '';
    let serviceName = '';
    let serviceMethod = '';
    let proxyTargetUrl = '';
    let scriptLanguage = 'python';
    let scriptCode = '';
    let staticDataPayload = '';
    if (route.handler?.config) {
      const config = route.handler.config;
      // 兼容两种字段名: entity_name 和 entity
      entityName = config.entity_name || config.entity || '';
      crudOperation = config.operation || 'list';
      queryField = config.query_field || config.queryField || '';
      queryParam = config.query_param || config.queryParam || '';
      serviceName = config.service || config.service_name || '';
      serviceMethod = config.method || config.method_name || '';
      proxyTargetUrl = config.target_url || config.targetUrl || '';
      scriptLanguage = config.language || 'python';
      scriptCode = config.script || config.code || '';
      if (config.data && typeof config.data === 'object') {
        staticDataPayload = JSON.stringify(config.data, null, 2);
      }
      queryLocation = config.query_location || config.queryLocation || '';
    }

    form.setFieldsValue({
      api_id: route.api_id,
      name: route.name,
      endpoint: displayEndpoint,
      method: route.method,
      description: route.description,
      auth_required: route.auth_required,
      handler_type: route.handler?.type || 'entity_crud',
      handler_config: route.handler?.config ? JSON.stringify(route.handler.config, null, 2) : '',
      entity_name: entityName,
      crud_operation: crudOperation,
      query_field: queryField,
      query_param: queryParam,
      query_location: queryLocation,
      service_name: serviceName,
      service_method: serviceMethod,
      proxy_target_url: proxyTargetUrl,
      script_language: scriptLanguage,
      script_code: scriptCode,
      static_data_payload: staticDataPayload,
      parameters: parametersStr,
      responses: responsesData,  // 直接传递对象
      response_type: hasDynamicRules ? 'dynamic' : 'static',
      static_response: staticResponseExample ? JSON.stringify(staticResponseExample, null, 2) : ''
    });
    setModalVisible(true);
  };

  // 处理删除路由
  const handleDeleteRoute = (route: APIRoute) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除API路由 "${route.name}" 吗？此操作不可恢复。`,
      icon: <ExclamationCircleOutlined />,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await routeAPI.deleteRoute(route.id);
          if (response.code === 200) {
            message.success('API路由删除成功');
            loadRoutes();
          } else {
            message.error(response.message || 'API路由删除失败');
          }
        } catch (error: any) {
          console.error('删除API路由失败:', error);
          message.error('API路由删除失败');
        }
      }
    });
  };

  // 处理切换状态
  const handleToggleStatus = async (route: APIRoute) => {
    try {
      let response;
      if (route.status === 'active') {
        response = await routeAPI.deactivateRoute(route.id);
        if (response.code === 200) {
          message.success('API路由已停用');
        }
      } else {
        response = await routeAPI.activateRoute(route.id);
        if (response.code === 200) {
          message.success('API路由已激活');
        }
      }
      
      if (response && response.code !== 200) {
        message.error(response.message || '状态切换失败');
      } else {
        loadRoutes();
      }
    } catch (error: any) {
      console.error('状态切换失败:', error);
      message.error('状态切换失败');
    }
  };

  // 处理从模板导入API路由
  const handleImportFromTemplate = async () => {
    Modal.confirm({
      title: '从模板导入API路由',
      content: '这将清空现有的API路由并从医院管理模板导入新的API路由。确定要继续吗？',
      icon: <ExclamationCircleOutlined />,
      okText: '确认导入',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true);

          // 调用从模板导入API
          const response = await fetch('/api/v1/routes/import-from-template?template_key=hospital_management&clear_existing=true', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer dev-token-12345'
            }
          });

          const result = await response.json();

          if (response.ok && result.code === 200) {
            message.success(`成功导入 ${result.data.imported_count} 个API路由`);
            // 重新加载路由列表
            await loadRoutes();
          } else {
            message.error(result.message || '导入失败');
          }
        } catch (error: any) {
          console.error('导入API路由失败:', error);
          message.error('导入API路由失败');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 处理保存路由
  const handleSaveRoute = async (values: any) => {
    try {
      console.log('🔧 提交的表单数据:', values);
      
      // 如果Ant Design表单未正确收集字段，手动从DOM获取
      const formData = {
        ...values,
        handler_type: values.handler_type || document.querySelector<HTMLInputElement>('input[id="handler_type"]')?.value || 'entity_crud',
        auth_required: values.auth_required ?? document.querySelector<HTMLInputElement>('input[id="auth_required"]')?.checked ?? false,
        handler_config: values.handler_config || document.querySelector<HTMLTextAreaElement>('textarea[id="handler_config"]')?.value || '{}',
        parameters: values.parameters || document.querySelector<HTMLTextAreaElement>('textarea[id="parameters"]')?.value || '[]',
        responses: values.responses || document.querySelector<HTMLTextAreaElement>('textarea[id="responses"]')?.value || '{}'
      };
      
      console.log('🔧 修正后的表单数据:', formData);
      
      // 验证必填字段
      if (!formData.handler_type) {
        message.error('请选择处理器类型');
        return;
      }

      // 解析参数列表
      let parameters: APIParameter[] = [];
      if (formData.parameters) {
        try {
          const parsed = JSON.parse(formData.parameters);
          if (Array.isArray(parsed)) {
            parameters = parsed;
          } else {
            message.error('参数格式错误，必须是数组格式');
            return;
          }
        } catch (e) {
          message.error('参数格式错误，请检查JSON格式');
          return;
        }
      }

      // 解析处理器配置
      let handlerConfig = {};
      if (formData.handler_config) {
        try {
          handlerConfig = JSON.parse(formData.handler_config);
        } catch (e) {
          message.error('处理器配置格式错误，请检查JSON格式');
          return;
        }
      }

      // 处理响应配置（按处理器类型分组）
      const handlerType = formData.handler_type as HandlerType;
      const responseConfigMode = getResponseConfigMode(handlerType);
      if (handlerType === 'custom_function') {
        const serviceName = values.service_name || form.getFieldValue('service_name');
        const serviceMethod = values.service_method || form.getFieldValue('service_method');
        if (!serviceName || !serviceMethod) {
          message.error('请选择服务包和方法');
          return;
        }
        const customConfig =
          handlerConfig && typeof handlerConfig === 'object' && !Array.isArray(handlerConfig)
            ? handlerConfig
            : {};
        handlerConfig = { ...customConfig, service: serviceName, method: serviceMethod };
      } else if (handlerType === 'proxy') {
        const targetUrl = values.proxy_target_url || form.getFieldValue('proxy_target_url');
        if (!targetUrl) {
          message.error('请填写目标URL');
          return;
        }
        handlerConfig = { target_url: targetUrl };
      } else if (handlerType === 'script') {
        const scriptCode = values.script_code || form.getFieldValue('script_code');
        const scriptLanguage = values.script_language || form.getFieldValue('script_language') || 'python';
        if (!scriptCode) {
          message.error('请填写脚本内容');
          return;
        }
        handlerConfig = { language: scriptLanguage, script: scriptCode };
      } else if (handlerType === 'static_data') {
        const payloadText = values.static_data_payload || form.getFieldValue('static_data_payload');
        if (!payloadText) {
          message.error('请填写静态数据');
          return;
        }
        try {
          const parsed = JSON.parse(payloadText);
          handlerConfig = { data: parsed };
        } catch (e) {
          message.error('静态数据格式错误，请检查JSON格式');
          return;
        }
      }


      let responses: ResponseDefinition = {};
      let dynamicRules: any[] = [];

      if (responseConfigMode !== 'direct') {
        const responseType = formData.response_type || 'static';

        if (responseConfigMode === 'advanced' && responseType === 'dynamic' && formData.responses) {
          // 动态响应配置
          if (typeof formData.responses === 'object') {
            const responseConfig = formData.responses as any;
            // 提取dynamic_rules
            dynamicRules = responseConfig.dynamic_rules || [];
            // 移除dynamic_rules，剩下的作为responses
            const { dynamic_rules, ...cleanResponses } = responseConfig;
            responses = cleanResponses;
          } else if (typeof formData.responses === 'string') {
            // 如果是字符串，尝试解析JSON
            try {
              const parsed = JSON.parse(formData.responses);
              if (typeof parsed === 'object' && !Array.isArray(parsed)) {
                const { dynamic_rules, ...cleanResponses } = parsed;
                dynamicRules = dynamic_rules || [];
                responses = cleanResponses;
              } else {
                message.error('响应定义格式错误，必须是对象格式');
                return;
              }
            } catch (e) {
              message.error('响应定义格式错误，请检查JSON格式');
              return;
            }
          }
        } else if (responseType === 'static' && formData.static_response) {
          // 响应样例（文档）
          try {
            const staticResponseData = typeof formData.static_response === 'string'
              ? JSON.parse(formData.static_response)
              : formData.static_response;

            responses = {
              "200": {
                description: "Success",
                schema: {
                  type: "object",
                  example: staticResponseData
                }
              }
            };
          } catch (e) {
            message.error('响应样例格式错误，请检查JSON格式');
            return;
          }
        }
      }
      
      // 如果没有有效的responses，使用默认格式
      if (Object.keys(responses).length === 0) {
        responses = buildDefaultResponses();
      }
      
      // 只有高级模式才允许动态规则
      if (responseConfigMode === 'advanced' && formData.dynamic_rules && Array.isArray(formData.dynamic_rules)) {
        dynamicRules = formData.dynamic_rules;
      }

      // 确保endpoint以/api/v1/开头
      let endpoint = formData.endpoint;
      if (!endpoint.startsWith('/api/v1/')) {
        // 如果以/api/开头，替换为/api/v1/
        if (endpoint.startsWith('/api/')) {
          endpoint = '/api/v1' + endpoint.substring('/api'.length);
        } else {
          // 如果不以/api/开头，添加/api/v1前缀
          endpoint = '/api/v1' + (endpoint.startsWith('/') ? endpoint : '/' + endpoint);
        }
      }

      const routeData: APIRouteCreateRequest | APIRouteUpdateRequest = {
        api_id: formData.api_id,
        name: formData.name,
        endpoint: endpoint,
        method: formData.method,
        description: formData.description || '',
        auth_required: formData.auth_required || false,
        handler: {
          type: formData.handler_type as HandlerType,
          config: handlerConfig
        },
        parameters: parameters,
        responses: responses,
        // 使用正确提取的动态响应规则
        dynamic_rules: dynamicRules
      };

      console.log('🚀 发送的API数据:', routeData);

      let response;
      if (editingRoute) {
        response = await routeAPI.updateRoute(editingRoute.id, routeData as APIRouteUpdateRequest);
        if (response.code === 200) {
          message.success('API路由更新成功');
        }
      } else {
        response = await routeAPI.createRoute(routeData as APIRouteCreateRequest);
        if (response.code === 201) {
          message.success('API路由创建成功');
        }
      }

      if (response && (response.code === 200 || response.code === 201)) {
        setModalVisible(false);
        setEditingRoute(null);
        form.resetFields();
        loadRoutes();
      } else {
        message.error(response?.message || (editingRoute ? 'API路由更新失败' : 'API路由创建失败'));
      }
    } catch (error: any) {
      console.error('保存API路由失败:', error);
      const errorMsg = error.response?.data?.message || (editingRoute ? 'API路由更新失败' : 'API路由创建失败');
      message.error(errorMsg);
    }
  };

  // 表格列定义
  const columns: ColumnsType<APIRoute> = [
    {
      title: 'API信息',
      key: 'api_info',
      render: (_, record: APIRoute) => (
        <div className="api-info-cell">
          <div className="api-name">{record.name}</div>
          <div className="api-id">{record.api_id}</div>
          <div className="api-description">{record.description}</div>
        </div>
      )
    },
    {
      title: '端点',
      key: 'endpoint',
      render: (_, record: APIRoute) => (
        <div className="endpoint-cell">
          <div className="endpoint-method">
            <Tag color={getMethodColor(record.method)}>{record.method}</Tag>
          </div>
          <code className="endpoint-path">{record.endpoint}</code>
        </div>
      )
    },
    {
      title: '处理器',
      dataIndex: ['handler', 'type'],
      key: 'handler_type',
      render: (type: HandlerType) => (
        <Tag color="blue">
          {HandlerTypeConfigs[type]?.label || type}
        </Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge
          status={getStatusColor(status) as any}
          text={status === 'active' ? '活跃' : status === 'inactive' ? '停用' : status}
        />
      )
    },
    {
      title: '认证',
      dataIndex: 'auth_required',
      key: 'auth_required',
      render: (required: boolean) => (
        <Tag color={required ? 'orange' : 'default'}>
          {required ? '需要' : '无需'}
        </Tag>
      )
    },
    {
      title: '统计信息',
      key: 'statistics',
      render: (_, record: APIRoute) => (
        <div className="statistics-cell">
          <div className="stat-item">
            <span className="stat-label">调用:</span>
            <span className="stat-value">{record.call_count || 0}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">响应:</span>
            <span className="stat-value">{record.avg_response_time || 0}ms</span>
          </div>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: APIRoute) => (
        <div className="actions-cell">
          <Space size="small">
          <Tooltip title="测试API">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => handleTestRoute(record)}
              style={{ color: '#1890ff' }}
            />
          </Tooltip>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditRoute(record)}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? '停用' : '激活'}>
            <Button
              type="text"
              icon={record.status === 'active' ? <StopOutlined /> : <CheckCircleOutlined />}
              onClick={() => handleToggleStatus(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteRoute(record)}
            />
          </Tooltip>
          </Space>
        </div>
      )
    }
  ];
  const activeRoutesForBatch = batchRoutes;
  const selectedBatchCount = selectedBatchRouteIds.length;

  return (
    <div className="api-route-step">
      {/* 步骤头部 */}
      <UnifiedCard variant="header" className="unified-step-header">
        <div className="unified-step-content">
          <div className="unified-step-title-section">
            <div className="unified-step-icon">
              <ApiOutlined />
            </div>
            <div className="unified-step-text">
              <h2 className="unified-step-title">API路由管理</h2>
              <p className="unified-step-description">配置和管理系统的API接口路由，支持完整的增删改查操作</p>
            </div>
          </div>
          <div className="unified-step-actions">
            <Button
              icon={<ThunderboltOutlined />}
              onClick={openBatchTestModal}
              loading={loading}
            >
              批量测试
            </Button>
            <Button
              icon={<HeartOutlined />}
              onClick={() => setHealthModalVisible(true)}
            >
              健康检查
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadRoutes}
              loading={loading}
            >
              刷新
            </Button>

            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingRoute(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              添加API路由
            </Button>
          </div>
        </div>
      </UnifiedCard>

      <div className="step-statistics">
        <StatsCard
          title="总路由数"
          value={summary.total_routes}
          icon={<ApiOutlined />}
          color="primary"
        />
        <StatsCard
          title="活跃路由"
          value={summary.active_routes}
          icon={<CheckCircleOutlined />}
          color="success"
        />
        <StatsCard
          title="平均响应时间"
          value={summary.avg_response_time}
          suffix="ms"
          icon={<BarChartOutlined />}
          color="warning"
        />
        <StatsCard
          title="健康路由"
          value={summary.healthy_routes}
          icon={<HeartOutlined />}
          color="success"
        />
      </div>

      {/* 筛选器 */}
      <div className="step-filters">
        <UnifiedCard>
          <Row gutter={16}>
            <Col span={6}>
              <Select
                placeholder="筛选状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => setQueryParams({ ...queryParams, status: value })}
                value={queryParams.status}
              >
                <Option value="active">活跃</Option>
                <Option value="inactive">停用</Option>
                <Option value="maintenance">维护</Option>
                <Option value="deprecated">已弃用</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Select
                placeholder="筛选方法"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => setQueryParams({ ...queryParams, method: value })}
                value={queryParams.method}
              >
                {httpMethods.map(method => (
                  <Option key={method} value={method}>
                    <Tag color={getMethodColor(method)}>{method}</Tag>
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Input
                placeholder="搜索名称/端点"
                allowClear
                value={queryParams.search}
                onChange={(e) => setQueryParams({ ...queryParams, search: e.target.value })}
              />
            </Col>
            <Col span={6}>
              <Button
                onClick={() => {
                  setQueryParams({});
                  loadRoutes();
                }}
              >
                重置筛选
              </Button>
            </Col>
          </Row>
        </UnifiedCard>
      </div>

      {/* 路由表格 */}
      <div className="step-content">
        <UnifiedCard variant="content">
          <div className="unified-table">
            <Table
              columns={columns}
              dataSource={routes}
              rowKey="id"
              loading={loading}
              size="middle"
              bordered={false}
              pagination={{
                current: pagination.page,
                pageSize: pagination.limit,
                total: pagination.total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
                onChange: (page, pageSize) => {
                  setPagination({ ...pagination, page, limit: pageSize || 10 });
                }
              }}
            />
          </div>
        </UnifiedCard>
      </div>

      {/* 步骤底部 */}
      <div className="step-footer">
        <Space>
          <Button size="large" onClick={onPrev}>
            上一步
          </Button>
          <Button type="primary" size="large" onClick={onNext}>
            下一步
          </Button>
        </Space>
      </div>

      {/* 创建/编辑API路由模态框 */}
      <Modal
        title={editingRoute ? '编辑API路由' : '创建API路由'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingRoute(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
        className="api-route-modal"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveRoute}
          className="api-route-form"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="api_id"
                label="API ID"
                rules={[{ required: true, message: '请输入API ID' }]}
              >
                <Input placeholder="例如: product_list_api" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="API名称"
                rules={[{ required: true, message: '请输入API名称' }]}
              >
                <Input placeholder="例如: 商品列表API" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="method"
                label="HTTP方法"
                rules={[{ required: true, message: '请选择HTTP方法' }]}
                initialValue="POST"
              >
                <Select placeholder="选择HTTP方法">
                  {httpMethods.map(method => (
                    <Option key={method} value={method}>
                      <Tag color={getMethodColor(method)}>{method}</Tag>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item
                name="endpoint"
                label="端点路径"
                rules={[{ required: true, message: '请输入端点路径' }]}
              >
                <Input placeholder="例如: /api/products" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="API功能描述" />
          </Form.Item>

          <Form.Item
            name="auth_required"
            label="访问控制"
            valuePropName="checked"
            initialValue={true}
            tooltip="公开路由：无需登录即可访问，不进行权限检查；私有路由：需要登录认证和角色权限检查"
          >
            <Switch 
              checkedChildren="私有路由" 
              unCheckedChildren="公开路由"
            />
          </Form.Item>

          <Form.Item
            name="handler_type"
            label="处理器类型"
            rules={[{ required: true, message: '请选择处理器类型' }]}
            initialValue="entity_crud"
          >
            <Select
              placeholder="选择处理器类型"
              options={Object.entries(HandlerTypeConfigs).map(([key, config]) => ({
                value: key,
                label: config.label || key
              }))}
              optionLabelProp="label"
              optionRender={(option) => <span>{option.label}</span>}
            />
          </Form.Item>

          {/* 实体CRUD操作特殊配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'entity_crud' ? (
                <>
                  <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="entity_name"
                      label="选择实体"
                      rules={[{ required: true, message: '请选择要操作的实体' }]}
                    >
                      <Select 
                        placeholder="选择实体" 
                        loading={loadingEntities}
                        onChange={(value) => {
                          updateEntityCrudConfig({ entity_name: value });
                        }}
                      >
                        {entities.map(entity => (
                          <Option key={entity.value} value={entity.value}>
                            <Space>
                              <DatabaseOutlined />
                              {entity.label || entity.value}
                            </Space>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="crud_operation"
                      label="CRUD操作"
                      rules={[{ required: true, message: '请选择CRUD操作' }]}
                      initialValue="list"
                    >
                      <Select 
                        placeholder="选择操作类型"
                        onChange={(value) => {
                          updateEntityCrudConfig({ operation: value });
                        }}
                      >
                        <Option value="list">查询列表 (GET)</Option>
                        <Option value="search">搜索查询 (GET)</Option>
                        <Option value="get">获取单个 (GET)</Option>
                        <Option value="create">创建 (POST)</Option>
                        <Option value="update">更新 (PUT)</Option>
                        <Option value="delete">删除 (DELETE)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item
                  noStyle
                  shouldUpdate={(prevValues, currentValues) =>
                    prevValues.crud_operation !== currentValues.crud_operation
                  }
                >
                  {({ getFieldValue }) => {
                    const operation = getFieldValue('crud_operation');
                    if (operation !== 'get') {
                      return null;
                    }
                    return (
                      <Row gutter={16}>
                        <Col span={8}>
                          <Form.Item
                            name="query_field"
                            label="查询字段"
                            tooltip="实体表中用于匹配的字段名"
                          >
                            <Input
                              placeholder="例如: ticket_number"
                              onChange={(e) => {
                                updateEntityCrudConfig({ query_field: e.target.value });
                              }}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item
                            name="query_param"
                            label="参数名"
                            tooltip="请求参数名（可选）"
                          >
                            <Input
                              placeholder="例如: ticket_id"
                              onChange={(e) => {
                                updateEntityCrudConfig({ query_param: e.target.value });
                              }}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item
                            name="query_location"
                            label="参数位置"
                            tooltip="从路径或查询参数读取"
                          >
                            <Select
                              placeholder="选择参数位置"
                              onChange={(value) => {
                                updateEntityCrudConfig({ query_location: value });
                              }}
                              allowClear
                            >
                              <Option value="path">路径参数</Option>
                              <Option value="query">查询参数</Option>
                              <Option value="body">请求体</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>
                    );
                  }}
                </Form.Item>
                </>
              ) : null;
            }}
          </Form.Item>

          {/* 自定义函数配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type ||
              prevValues.service_name !== currentValues.service_name ||
              prevValues.service_method !== currentValues.service_method
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              if (handlerType !== 'custom_function') {
                return null;
              }
              const selectedService = getFieldValue('service_name');
              const serviceMeta = servicePackages.find(service => service.name === selectedService);
              const serviceMethods = serviceMeta?.methods || [];
              return (
                <Card title="自定义函数" size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="service_name"
                        label="服务包"
                        rules={[{ required: true, message: '请选择服务包' }]}
                      >
                        <Select
                          placeholder="选择服务包"
                          loading={loadingServicePackages}
                          onChange={(value) => {
                            updateCustomFunctionConfig(value, form.getFieldValue('service_method'));
                          }}
                        >
                          {servicePackages.map(service => (
                            <Option key={service.name} value={service.name}>
                              {service.display_name || service.name}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="service_method"
                        label="方法"
                        rules={[{ required: true, message: '请选择方法' }]}
                      >
                        {serviceMethods.length > 0 ? (
                          <Select
                            placeholder="选择方法"
                            onChange={(value) => {
                              updateCustomFunctionConfig(form.getFieldValue('service_name'), value);
                            }}
                          >
                            {serviceMethods.map((method: string) => (
                              <Option key={method} value={method}>{method}</Option>
                            ))}
                          </Select>
                        ) : (
                          <Input
                            placeholder="输入方法名"
                            onChange={(e) => {
                              updateCustomFunctionConfig(form.getFieldValue('service_name'), e.target.value);
                            }}
                          />
                        )}
                      </Form.Item>
                    </Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={24}>
                      <Space>
                        <Upload
                          accept=".zip,.py"
                          showUploadList={false}
                          customRequest={async ({ file, onSuccess, onError }) => {
                            try {
                              await servicePackageAPI.uploadPackage(file as File, true);
                              message.success('服务包上传成功');
                              await loadServicePackages();
                              if (onSuccess) onSuccess({}, new XMLHttpRequest());
                            } catch (error: any) {
                              message.error(error?.message || '上传失败');
                              if (onError) onError(error);
                            }
                          }}
                        >
                          <Button icon={<UploadOutlined />} loading={loadingServicePackages}>上传服务包</Button>
                        </Upload>
                        <Button icon={<ReloadOutlined />} onClick={loadServicePackages} loading={loadingServicePackages}>刷新</Button>
                      </Space>
                    </Col>
                  </Row>
                </Card>
              );
            }}
          </Form.Item>

          {/* 代理配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'proxy' ? (
                <Card title="代理模式" size="small" style={{ marginBottom: 16 }}>
                  <Form.Item
                    name="proxy_target_url"
                    label="目标URL"
                    rules={[{ required: true, message: '请填写目标URL' }]}
                  >
                    <Input
                      placeholder="https://api.example.com"
                      onChange={(e) => updateProxyConfig(e.target.value)}
                    />
                  </Form.Item>
                </Card>
              ) : null;
            }}
          </Form.Item>

          {/* 脚本配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'script' ? (
                <Card title="脚本执行" size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item
                        name="script_language"
                        label="语言"
                        initialValue="python"
                      >
                        <Select
                          onChange={(value) => updateScriptConfig(value, form.getFieldValue('script_code'))}
                        >
                          <Option value="python">python</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                  <Form.Item
                    name="script_code"
                    label="脚本内容"
                    rules={[{ required: true, message: '请填写脚本内容' }]}
                  >
                    <TextArea
                      rows={6}
                      placeholder='result = {"message": "ok"}'
                      onChange={(e) => updateScriptConfig(form.getFieldValue('script_language'), e.target.value)}
                    />
                  </Form.Item>
                </Card>
              ) : null;
            }}
          </Form.Item>

          {/* 静态数据配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'static_data' ? (
                <Card title="静态数据" size="small" style={{ marginBottom: 16 }}>
                  <Form.Item
                    name="static_data_payload"
                    label="静态数据(JSON)"
                    rules={[{ required: true, message: '请填写静态数据' }]}
                  >
                    <TextArea
                      rows={6}
                      placeholder='{"message": "ok"}'
                      onChange={(e) => updateStaticDataConfig(e.target.value)}
                    />
                  </Form.Item>
                </Card>
              ) : null;
            }}
          </Form.Item>


          {/* 文件上传配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'file_upload' ? (
                <Card title="文件上传配置" size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="upload_path"
                        label="上传路径"
                        initialValue="/uploads"
                      >
                        <Input
                          placeholder="/uploads"
                          prefix={<FolderOutlined />}
                          onChange={(e) => {
                            const config = {
                              upload_path: e.target.value || "/uploads",
                              max_file_size: form.getFieldValue('max_file_size') || "10MB",
                              allowed_extensions: form.getFieldValue('allowed_extensions') || [".jpg", ".png", ".pdf", ".doc"],
                              auto_rename: form.getFieldValue('auto_rename') ?? true
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="max_file_size"
                        label="最大文件大小"
                        initialValue="10MB"
                      >
                        <Select
                          placeholder="选择文件大小限制"
                          onChange={(value) => {
                            const config = {
                              upload_path: form.getFieldValue('upload_path') || "/uploads",
                              max_file_size: value,
                              allowed_extensions: form.getFieldValue('allowed_extensions') || [".jpg", ".png", ".pdf", ".doc"],
                              auto_rename: form.getFieldValue('auto_rename') ?? true
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        >
                          <Option value="1MB">1MB</Option>
                          <Option value="5MB">5MB</Option>
                          <Option value="10MB">10MB</Option>
                          <Option value="20MB">20MB</Option>
                          <Option value="50MB">50MB</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="allowed_extensions"
                        label="允许的文件类型"
                        initialValue={[".jpg", ".png", ".pdf", ".doc"]}
                      >
                        <Select
                          mode="multiple"
                          placeholder="选择允许的文件类型"
                          onChange={(value) => {
                            const config = {
                              upload_path: form.getFieldValue('upload_path') || "/uploads",
                              max_file_size: form.getFieldValue('max_file_size') || "10MB",
                              allowed_extensions: value,
                              auto_rename: form.getFieldValue('auto_rename') ?? true
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        >
                          <Option value=".jpg">JPG图片</Option>
                          <Option value=".png">PNG图片</Option>
                          <Option value=".gif">GIF图片</Option>
                          <Option value=".pdf">PDF文档</Option>
                          <Option value=".doc">Word文档</Option>
                          <Option value=".docx">Word文档(新)</Option>
                          <Option value=".txt">文本文件</Option>
                          <Option value=".csv">CSV文件</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="auto_rename"
                        label="自动重命名"
                        valuePropName="checked"
                        initialValue={true}
                      >
                        <Switch
                          checkedChildren="开启"
                          unCheckedChildren="关闭"
                          onChange={(checked) => {
                            const config = {
                              upload_path: form.getFieldValue('upload_path') || "/uploads",
                              max_file_size: form.getFieldValue('max_file_size') || "10MB",
                              allowed_extensions: form.getFieldValue('allowed_extensions') || [".jpg", ".png", ".pdf", ".doc"],
                              auto_rename: checked
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider orientation="left" plain>测试文件上传</Divider>
                  <Form.Item label="上传测试文件">
                    <Upload.Dragger
                      name="file"
                      multiple
                      action="/api/v1/files/upload"
                      headers={{
                        'Authorization': `Bearer ${tokenManager.getToken()}`
                      }}
                      data={{
                        category: 'general'
                      }}
                      onChange={(info) => {
                        const { status } = info.file;
                        if (status === 'done') {
                          message.success(`${info.file.name} 文件上传成功`);
                          console.log('上传成功:', info.file.response);
                        } else if (status === 'error') {
                          message.error(`${info.file.name} 文件上传失败`);
                        }
                      }}
                      beforeUpload={(file) => {
                        const allowedExtensions = form.getFieldValue('allowed_extensions') || [".jpg", ".png", ".pdf", ".doc"];
                        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

                        if (!allowedExtensions.includes(fileExtension)) {
                          message.error(`不支持的文件类型: ${fileExtension}`);
                          return false;
                        }

                        const maxSize = form.getFieldValue('max_file_size') || "10MB";
                        const maxSizeBytes = parseInt(maxSize) * 1024 * 1024;

                        if (file.size > maxSizeBytes) {
                          message.error(`文件大小超过限制: ${maxSize}`);
                          return false;
                        }

                        return true;
                      }}
                    >
                      <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                      </p>
                      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                      <p className="ant-upload-hint">
                        支持单个或批量上传，严格按照上述配置的文件类型和大小限制
                      </p>
                    </Upload.Dragger>
                  </Form.Item>
                </Card>
              ) : null;
            }}
          </Form.Item>

          {/* 文件下载配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'file_download' ? (
                <Card title="文件下载配置" size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="file_root"
                        label="文件根目录"
                        initialValue="/files"
                      >
                        <Input
                          placeholder="/files"
                          prefix={<FolderOutlined />}
                          onChange={(e) => {
                            const config = {
                              file_root: e.target.value || "/files",
                              security_check: form.getFieldValue('security_check') ?? true,
                              disposition: form.getFieldValue('disposition') || "attachment"
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="disposition"
                        label="下载方式"
                        initialValue="attachment"
                      >
                        <Select
                          placeholder="选择下载方式"
                          onChange={(value) => {
                            const config = {
                              file_root: form.getFieldValue('file_root') || "/files",
                              security_check: form.getFieldValue('security_check') ?? true,
                              disposition: value
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        >
                          <Option value="attachment">下载到本地</Option>
                          <Option value="inline">在浏览器中打开</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={24}>
                      <Form.Item
                        name="security_check"
                        label="安全检查"
                        valuePropName="checked"
                        initialValue={true}
                      >
                        <Switch
                          checkedChildren="开启"
                          unCheckedChildren="关闭"
                          onChange={(checked) => {
                            const config = {
                              file_root: form.getFieldValue('file_root') || "/files",
                              security_check: checked,
                              disposition: form.getFieldValue('disposition') || "attachment"
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '-16px' }}>
                        开启后将防止路径穿越攻击，建议保持开启
                      </div>
                    </Col>
                  </Row>

                  <Divider orientation="left" plain>上传可下载文件</Divider>
                  <Form.Item label="上传文件">
                    <Upload.Dragger
                      name="file"
                      multiple
                      action="/api/v1/files/upload"
                      headers={{
                        'Authorization': `Bearer ${tokenManager.getToken()}`
                      }}
                      data={{
                        category: 'documents'
                      }}
                      onChange={(info) => {
                        const { status } = info.file;
                        if (status === 'done') {
                          message.success(`${info.file.name} 文件上传成功`);
                          console.log('文件上传成功:', info.file.response);
                        } else if (status === 'error') {
                          message.error(`${info.file.name} 文件上传失败`);
                        }
                      }}
                      beforeUpload={(file) => {
                        const isLt10M = file.size / 1024 / 1024 < 10;
                        if (!isLt10M) {
                          message.error('文件大小不能超过10MB!');
                          return false;
                        }
                        return true;
                      }}
                    >
                      <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                      </p>
                      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                      <p className="ant-upload-hint">
                        上传要提供下载的文件，支持各种文件类型
                      </p>
                    </Upload.Dragger>
                  </Form.Item>

                  <Divider orientation="left" plain>可下载文件列表</Divider>
                  <Form.Item label="文件管理">
                    <Button
                      type="primary"
                      icon={<ReloadOutlined />}
                      onClick={async () => {
                        try {
                          const response = await fetch('/api/v1/files/list', {
                            headers: {
                              'Authorization': `Bearer ${tokenManager.getToken()}`
                            }
                          });
                          const result = await response.json();
                          if (result.success) {
                            message.success(`找到 ${result.data.files.length} 个文件`);
                            console.log('文件列表:', result.data.files);
                          }
                        } catch (error) {
                          message.error('获取文件列表失败');
                        }
                      }}
                    >
                      刷新文件列表
                    </Button>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                      点击刷新查看当前可下载的文件列表
                    </div>
                  </Form.Item>
                </Card>
              ) : null;
            }}
          </Form.Item>

          {/* 图片显示配置 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = getFieldValue('handler_type');
              return handlerType === 'image_display' ? (
                <Card title="图片显示配置" size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="image_root"
                        label="图片根目录"
                        initialValue="/images"
                      >
                        <Input
                          placeholder="/images"
                          prefix={<FileImageOutlined />}
                          onChange={(e) => {
                            const config = {
                              image_root: e.target.value || "/images",
                              resize_options: form.getFieldValue('resize_options') || {
                                width: 800,
                                height: 600,
                                quality: 85
                              },
                              cache_duration: form.getFieldValue('cache_duration') || 3600
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="cache_duration"
                        label="缓存时间(秒)"
                        initialValue={3600}
                      >
                        <InputNumber
                          min={0}
                          max={86400}
                          placeholder="3600"
                          style={{ width: '100%' }}
                          onChange={(value) => {
                            const config = {
                              image_root: form.getFieldValue('image_root') || "/images",
                              resize_options: form.getFieldValue('resize_options') || {
                                width: 800,
                                height: 600,
                                quality: 85
                              },
                              cache_duration: value || 3600
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Divider orientation="left" plain>图片缩放选项</Divider>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item
                        name="resize_width"
                        label="宽度"
                        initialValue={800}
                      >
                        <InputNumber
                          min={1}
                          max={4096}
                          placeholder="800"
                          style={{ width: '100%' }}
                          onChange={(value) => {
                            const config = {
                              image_root: form.getFieldValue('image_root') || "/images",
                              resize_options: {
                                width: value || 800,
                                height: form.getFieldValue('resize_height') || 600,
                                quality: form.getFieldValue('resize_quality') || 85
                              },
                              cache_duration: form.getFieldValue('cache_duration') || 3600
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="resize_height"
                        label="高度"
                        initialValue={600}
                      >
                        <InputNumber
                          min={1}
                          max={4096}
                          placeholder="600"
                          style={{ width: '100%' }}
                          onChange={(value) => {
                            const config = {
                              image_root: form.getFieldValue('image_root') || "/images",
                              resize_options: {
                                width: form.getFieldValue('resize_width') || 800,
                                height: value || 600,
                                quality: form.getFieldValue('resize_quality') || 85
                              },
                              cache_duration: form.getFieldValue('cache_duration') || 3600
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="resize_quality"
                        label="质量"
                        initialValue={85}
                      >
                        <InputNumber
                          min={1}
                          max={100}
                          placeholder="85"
                          style={{ width: '100%' }}
                          onChange={(value) => {
                            const config = {
                              image_root: form.getFieldValue('image_root') || "/images",
                              resize_options: {
                                width: form.getFieldValue('resize_width') || 800,
                                height: form.getFieldValue('resize_height') || 600,
                                quality: value || 85
                              },
                              cache_duration: form.getFieldValue('cache_duration') || 3600
                            };
                            form.setFieldValue('handler_config', JSON.stringify(config, null, 2));
                          }}
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider orientation="left" plain>图片上传测试</Divider>
                  <Form.Item label="上传测试图片">
                    <Upload
                      name="file"
                      listType="picture-card"
                      action="/api/v1/files/upload"
                      headers={{
                        'Authorization': `Bearer ${tokenManager.getToken()}`
                      }}
                      data={{
                        category: 'images'
                      }}
                      accept="image/*"
                      onChange={(info) => {
                        const { status } = info.file;
                        if (status === 'done') {
                          message.success(`${info.file.name} 图片上传成功`);
                          console.log('图片上传成功:', info.file.response);
                        } else if (status === 'error') {
                          message.error(`${info.file.name} 图片上传失败`);
                        }
                      }}
                      beforeUpload={(file) => {
                        const isImage = file.type.startsWith('image/');
                        if (!isImage) {
                          message.error('只能上传图片文件!');
                          return false;
                        }

                        const isLt10M = file.size / 1024 / 1024 < 10;
                        if (!isLt10M) {
                          message.error('图片大小不能超过10MB!');
                          return false;
                        }

                        return true;
                      }}
                    >
                      <div>
                        <PlusOutlined />
                        <div style={{ marginTop: 8 }}>上传图片</div>
                      </div>
                    </Upload>
                  </Form.Item>
                </Card>
              ) : null;
            }}
          </Form.Item>

          <Form.Item
            name="handler_config"
            label="处理器配置 (JSON)"
          >
            <TextArea
              rows={4}
              placeholder='{"entity": "product", "operation": "list", "default_limit": 20, "max_limit": 100}'
            />
          </Form.Item>

          <Form.Item
            name="parameters"
            label="参数定义 (JSON)"
          >
            <TextArea
              rows={6}
              placeholder={`[
  {
    "name": "page",
    "type": "integer",
    "location": "query",
    "required": false,
    "description": "页码，默认为1"
  }
]`}
            />
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.handler_type !== currentValues.handler_type ||
              prevValues.response_type !== currentValues.response_type
            }
          >
            {({ getFieldValue }) => {
              const handlerType = (getFieldValue('handler_type') || 'entity_crud') as HandlerType;
              const responseConfigMode = getResponseConfigMode(handlerType);
              const responseType = getFieldValue('response_type') || 'static';

              if (responseConfigMode === 'direct') {
                return (
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="直出类型接口"
                    description="当前处理器为文件/图片直出，响应内容由处理器直接返回，不需要配置静态响应或动态响应规则。"
                  />
                );
              }

              if (responseConfigMode === 'document') {
                return (
                  <>
                    <Alert
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                      message="文档型配置"
                      description="此类型建议仅维护“响应样例”，用于文档展示和AI字段提示。"
                    />
                    <Form.Item
                      name="static_response"
                      label="响应样例 (JSON)"
                    >
                      <TextArea
                        rows={6}
                        placeholder={`{
  "success": true,
  "message": "操作成功",
  "data": {
    "result": "这是响应样例"
  }
}`}
                      />
                    </Form.Item>
                  </>
                );
              }

              return (
                <>
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="业务执行型配置"
                    description="默认只需配置处理器；响应配置用于文档样例或高级响应重写规则。"
                  />
                  <Form.Item
                    name="response_type"
                    label="响应配置"
                    initialValue="static"
                  >
                    <Radio.Group>
                      <Radio value="static">响应样例（文档）</Radio>
                      <Radio value="dynamic">响应重写规则（高级）</Radio>
                    </Radio.Group>
                  </Form.Item>

                  {responseType === 'dynamic' ? (
                    <Form.Item
                      name="responses"
                      label="动态响应配置"
                    >
                      <DynamicResponseConfig />
                    </Form.Item>
                  ) : (
                    <Form.Item
                      name="static_response"
                      label="响应样例 (JSON)"
                    >
                      <TextArea
                        rows={6}
                        placeholder={`{
  "success": true,
  "message": "操作成功",
  "data": {
    "result": "这是响应样例"
  }
}`}
                      />
                    </Form.Item>
                  )}
                </>
              );
            }}
          </Form.Item>

          <div className="form-actions">
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingRoute ? '更新' : '创建'}
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>

      {/* 路由详情模态框 */}
      <Modal
        title={`API路由详情 - ${selectedRoute?.name}`}
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedRoute(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={900}
      >
        {selectedRoute && (
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="API ID">{selectedRoute.api_id}</Descriptions.Item>
                <Descriptions.Item label="名称">{selectedRoute.name}</Descriptions.Item>
                <Descriptions.Item label="端点">{selectedRoute.endpoint}</Descriptions.Item>
                <Descriptions.Item label="方法">
                  <Tag color={getMethodColor(selectedRoute.method)}>{selectedRoute.method}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Badge
                    status={getStatusColor(selectedRoute.status) as any}
                    text={selectedRoute.status === 'active' ? '活跃' : '停用'}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="认证">
                  <Tag color={selectedRoute.auth_required ? 'orange' : 'default'}>
                    {selectedRoute.auth_required ? '需要' : '无需'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="处理器类型">
                  <Tag color="blue">
                    {HandlerTypeConfigs[selectedRoute.handler?.type as HandlerType]?.label || selectedRoute.handler?.type}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="调用次数">{selectedRoute.call_count || 0}</Descriptions.Item>
                <Descriptions.Item label="平均响应时间">{selectedRoute.avg_response_time || 0}ms</Descriptions.Item>
                <Descriptions.Item label="最后调用">{selectedRoute.last_called || '从未调用'}</Descriptions.Item>
                <Descriptions.Item label="创建时间">{selectedRoute.created_at}</Descriptions.Item>
                <Descriptions.Item label="更新时间">{selectedRoute.updated_at}</Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>{selectedRoute.description}</Descriptions.Item>
              </Descriptions>
            </TabPane>
            <TabPane tab="处理器配置" key="handler">
              <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                {JSON.stringify(selectedRoute.handler?.config || {}, null, 2)}
              </pre>
            </TabPane>
            <TabPane tab="参数定义" key="parameters">
              <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                {JSON.stringify(selectedRoute.parameters || [], null, 2)}
              </pre>
            </TabPane>
            <TabPane tab="响应定义" key="responses">
              {(selectedRoute.dynamic_rules && Array.isArray(selectedRoute.dynamic_rules)) || (selectedRoute.responses?.dynamic_rules && Array.isArray(selectedRoute.responses.dynamic_rules)) ? (
                <div>
                  <Alert
                    message="动态响应已配置"
                    description={`已配置 ${Array.isArray(selectedRoute.dynamic_rules) ? selectedRoute.dynamic_rules.length : Array.isArray(selectedRoute.responses?.dynamic_rules) ? selectedRoute.responses?.dynamic_rules.length : 0} 个动态响应规则`}
                    type="success"
                    style={{ marginBottom: 16 }}
                  />
                  <DynamicResponseConfig 
                    value={{ dynamic_rules: selectedRoute.dynamic_rules || selectedRoute.responses?.dynamic_rules || [] }}
                    onChange={() => {}} // 只读模式
                  />
                </div>
              ) : (
                <div>
                  <Alert
                    message="标准响应配置"
                    description="使用传统JSON响应定义"
                    type="info"
                    style={{ marginBottom: 16 }}
                  />
                  <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                    {JSON.stringify(selectedRoute.responses || {}, null, 2)}
                  </pre>
                </div>
              )}
            </TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 健康检查模态框 */}
      <Modal
        title="API路由健康检查"
        open={healthModalVisible}
        onCancel={() => {
          setHealthModalVisible(false);
        }}
        footer={[
          <Button key="refresh" icon={<ReloadOutlined />} onClick={loadHealthData}>
            刷新
          </Button>,
          <Button key="close" onClick={() => setHealthModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        {healthData ? (
          <div>
            <Alert
              message={`系统整体状态: ${healthData.overall_status}`}
              type={healthData.overall_status === 'healthy' ? 'success' :
                    healthData.overall_status === 'warning' ? 'warning' : 'error'}
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Statistic title="总路由数" value={healthData.total_routes} />
              </Col>
              <Col span={6}>
                <Statistic title="健康路由" value={healthData.healthy_routes} valueStyle={{ color: '#3f8600' }} />
              </Col>
              <Col span={6}>
                <Statistic title="警告路由" value={healthData.warning_routes} valueStyle={{ color: '#faad14' }} />
              </Col>
              <Col span={6}>
                <Statistic title="异常路由" value={healthData.unhealthy_routes} valueStyle={{ color: '#f5222d' }} />
              </Col>
            </Row>

            <Divider>系统指标</Divider>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Statistic title="总请求数" value={healthData.system_metrics.total_requests} />
              </Col>
              <Col span={6}>
                <Statistic title="成功率" value={healthData.system_metrics.success_rate} suffix="%" />
              </Col>
              <Col span={6}>
                <Statistic title="错误率" value={healthData.system_metrics.error_rate} suffix="%" />
              </Col>
              <Col span={6}>
                <Statistic title="平均响应时间" value={healthData.system_metrics.avg_response_time} suffix="ms" />
              </Col>
            </Row>

            <Divider>路由状态详情</Divider>
            <Table
              dataSource={healthData.route_status}
              rowKey="id"
              size="small"
              columns={[
                {
                  title: 'API ID',
                  dataIndex: 'api_id',
                  key: 'api_id'
                },
                {
                  title: '端点',
                  key: 'endpoint',
                  render: (_, record) => (
                    <div>
                      <Tag color={getMethodColor(record.method)}>{record.method}</Tag>
                      <code>{record.endpoint}</code>
                    </div>
                  )
                },
                {
                  title: '健康状态',
                  dataIndex: 'health',
                  key: 'health',
                  render: (health: string) => (
                    <Badge status={getHealthColor(health) as any} text={health} />
                  )
                },
                {
                  title: '成功率',
                  dataIndex: 'success_rate',
                  key: 'success_rate',
                  render: (rate: number) => `${rate}%`
                },
                {
                  title: '平均响应时间',
                  dataIndex: 'avg_response_time',
                  key: 'avg_response_time',
                  render: (time: number) => `${time}ms`
                }
              ]}
            />

            {healthData.recommendations && healthData.recommendations.length > 0 && (
              <>
                <Divider>建议</Divider>
                <Timeline>
                  {healthData.recommendations.map((recommendation, index) => (
                    <Timeline.Item key={index} color="blue">
                      {typeof recommendation === 'string' ? recommendation : (recommendation as any).description || JSON.stringify(recommendation)}
                    </Timeline.Item>
                  ))}
                </Timeline>
              </>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Empty description="暂无健康检查数据" />
          </div>
        )}
      </Modal>

      {/* API测试模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <PlayCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            API测试 - {testingRoute?.name}
          </div>
        }
        open={testModalVisible}
        onCancel={() => {
          setTestModalVisible(false);
          setTestingRoute(null);
          setTestResult(null);
          testForm.resetFields();
        }}
        width={900}
        footer={null}
      >
        {testingRoute && (
          <div className="api-test-content">
            <Tabs defaultActiveKey="request" type="card">
              <TabPane tab="请求参数" key="request">
                <div style={{ marginBottom: 16 }}>
                  <Tag color={getMethodColor(testingRoute.method)} style={{ marginRight: 8 }}>
                    {testingRoute.method}
                  </Tag>
                  <Text code>{testingRoute.endpoint}</Text>
                </div>
                
                <Form
                  form={testForm}
                  layout="vertical"
                  onFinish={executeAPITest}
                >
                  {testingRoute.parameters && testingRoute.parameters.length > 0 ? (
                    <Row gutter={16}>
                      {testingRoute.parameters.map((param: any, index: number) => (
                        <Col span={12} key={index}>
                          <Form.Item
                            label={
                              <div>
                                <span>{param.description || param.name}</span>
                                <Tag color="blue" style={{ marginLeft: 8, fontSize: '12px' }}>
                                  {param.location}
                                </Tag>
                                {param.required && <Tag color="red" style={{ fontSize: '12px' }}>必填</Tag>}
                              </div>
                            }
                            name={param.name}
                            rules={[
                              { required: param.required, message: `请输入${param.description || param.name}` }
                            ]}
                          >
                            {param.type === 'boolean' ? (
                              <Switch />
                            ) : (param.type === 'select' || param.options) && param.options && param.options.length > 0 ? (
                              <Select placeholder={`请选择${param.description || param.name}`}>
                                {param.options.map((option: string) => (
                                  <Option key={option} value={option}>{option}</Option>
                                ))}
                              </Select>
                            ) : param.type === 'textarea' ? (
                              <TextArea rows={3} />
                            ) : (
                              <Input 
                                placeholder={`请输入${param.description || param.name}`}
                                type={param.type === 'number' || param.type === 'integer' ? 'number' : 'text'}
                              />
                            )}
                          </Form.Item>
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <Alert
                      message="该API无需参数"
                      description="此API不需要任何输入参数，可以直接测试。"
                      type="info"
                      showIcon
                    />
                  )}
                  
                  <div style={{ textAlign: 'center', marginTop: 24 }}>
                    <Button 
                      type="primary" 
                      htmlType="submit" 
                      loading={testLoading}
                      icon={<PlayCircleOutlined />}
                      size="large"
                    >
                      执行测试
                    </Button>
                  </div>
                </Form>
              </TabPane>
              
              <TabPane tab="响应结果" key="response">
                {testResult ? (
                  <div className="test-result">
                    <Card 
                      size="small" 
                      title={
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          {testResult.success ? (
                            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                          ) : (
                            <ExclamationCircleOutlined style={{ color: '#f5222d', marginRight: 8 }} />
                          )}
                          测试结果
                        </div>
                      }
                    >
                      <Row gutter={16}>
                        <Col span={6}>
                          <Statistic 
                            title="状态码" 
                            value={testResult.statusCode} 
                            valueStyle={{ color: testResult.success ? '#3f8600' : '#cf1322' }}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic 
                            title="执行时间" 
                            value={testResult.executionTime} 
                            suffix="ms"
                          />
                        </Col>
                        <Col span={12}>
                          <div>
                            <div style={{ marginBottom: 8, fontWeight: 'bold' }}>测试状态</div>
                            <Tag color={testResult.success ? 'success' : 'error'} style={{ fontSize: 14 }}>
                              {testResult.success ? '成功' : '失败'}
                            </Tag>
                          </div>
                        </Col>
                      </Row>
                    </Card>
                    
                    <Collapse style={{ marginTop: 16 }}>
                      <Panel header="请求详情" key="request">
                        <pre style={{ background: '#f5f5f5', padding: 12, overflow: 'auto' }}>
                          {JSON.stringify(testResult.request, null, 2)}
                        </pre>
                      </Panel>
                      <Panel header="响应数据" key="response">
                        {testResult?.data?.image_url ? (
                          <div style={{ textAlign: 'center', marginBottom: 12 }}>
                            <img
                              src={testResult.data.image_url}
                              alt="API图片预览"
                              style={{ maxWidth: '100%', maxHeight: 360, borderRadius: 6 }}
                            />
                          </div>
                        ) : null}
                        {testResult?.data?.file_url ? (
                          <div style={{ marginBottom: 12 }}>
                            {String(testResult?.data?.content_type || '').includes('pdf') ? (
                              <iframe
                                title="API文件预览"
                                src={testResult.data.file_url}
                                style={{ width: '100%', height: 360, border: '1px solid #f0f0f0', borderRadius: 6, marginBottom: 8 }}
                              />
                            ) : null}
                            <Space>
                              <Button
                                icon={<EyeOutlined />}
                                onClick={() => window.open(testResult.data.file_url, '_blank', 'noopener,noreferrer')}
                              >
                                查看文件
                              </Button>
                              <Button
                                type="primary"
                                icon={<DownloadOutlined />}
                                onClick={() => {
                                  const anchor = document.createElement('a');
                                  anchor.href = testResult.data.file_url;
                                  if (testResult?.data?.filename) {
                                    anchor.download = testResult.data.filename;
                                  }
                                  document.body.appendChild(anchor);
                                  anchor.click();
                                  document.body.removeChild(anchor);
                                }}
                              >
                                下载文件
                              </Button>
                            </Space>
                          </div>
                        ) : null}
                        <pre style={{ background: '#f5f5f5', padding: 12, overflow: 'auto' }}>
                          {JSON.stringify(testResult.data || { error: testResult.error }, null, 2)}
                        </pre>
                      </Panel>
                    </Collapse>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Empty 
                      description="尚未执行测试"
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                  </div>
                )}
              </TabPane>
            </Tabs>
          </div>
        )}
      </Modal>

      {/* 批量测试模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <ThunderboltOutlined style={{ marginRight: 8, color: '#722ed1' }} />
            批量API测试
          </div>
        }
        open={batchTestModalVisible}
        onCancel={() => setBatchTestModalVisible(false)}
        width={1200}
        footer={[
          <Button key="cancel" onClick={() => setBatchTestModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="test" 
            type="primary" 
            loading={batchTestLoading}
            onClick={handleBatchTest}
            disabled={activeRoutesForBatch.length === 0 || selectedBatchCount === 0}
            icon={<ThunderboltOutlined />}
          >
            开始批量测试
          </Button>
        ]}
      >
        <div className="batch-test-content">
          <Alert
            message="批量测试说明"
            description="先勾选要测试的路由。默认勾选 GET 路由；其余路由可按需手动勾选，避免误触发写操作。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Card title="选择测试路由" size="small" style={{ marginBottom: 16 }}>
            <Space style={{ marginBottom: 12 }}>
              <Button
                size="small"
                onClick={() => setSelectedBatchRouteIds(activeRoutesForBatch.map(route => route.id))}
                disabled={activeRoutesForBatch.length === 0}
              >
                全选
              </Button>
              <Button
                size="small"
                onClick={() => setSelectedBatchRouteIds(activeRoutesForBatch.filter(route => route.method === 'GET').map(route => route.id))}
                disabled={activeRoutesForBatch.length === 0}
              >
                仅选 GET
              </Button>
              <Button
                size="small"
                onClick={() => setSelectedBatchRouteIds([])}
                disabled={selectedBatchCount === 0}
              >
                清空
              </Button>
              <Text type="secondary">
                已选 {selectedBatchCount} / {activeRoutesForBatch.length}
              </Text>
            </Space>

            {activeRoutesForBatch.length > 0 ? (
              <Checkbox.Group
                style={{ width: '100%' }}
                value={selectedBatchRouteIds}
                onChange={(values) => setSelectedBatchRouteIds(values as string[])}
              >
                <div style={{ maxHeight: 220, overflowY: 'auto', border: '1px solid #f0f0f0', borderRadius: 6, padding: 10 }}>
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    {activeRoutesForBatch.map((route) => (
                      <Checkbox key={route.id} value={route.id}>
                        <Space size={8}>
                          <Tag color={getMethodColor(route.method)}>{route.method}</Tag>
                          <span>{route.name}</span>
                          <Text code>{route.endpoint}</Text>
                        </Space>
                      </Checkbox>
                    ))}
                  </Space>
                </div>
              </Checkbox.Group>
            ) : (
              <Empty description="暂无可测试的活跃路由" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
          
          {batchTestResults.length > 0 && (
            <div className="batch-test-results">
              <Card title="测试结果" size="small">
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                  <Col span={6}>
                    <Statistic 
                      title="总测试数" 
                      value={batchTestResults.length}
                      prefix={<ApiOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic 
                      title="成功" 
                      value={batchTestResults.filter(r => r.success).length}
                      valueStyle={{ color: '#3f8600' }}
                      prefix={<CheckCircleOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic 
                      title="失败" 
                      value={batchTestResults.filter(r => !r.success).length}
                      valueStyle={{ color: '#cf1322' }}
                      prefix={<ExclamationCircleOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic 
                      title="成功率" 
                      value={Math.round(batchTestResults.filter(r => r.success).length / batchTestResults.length * 100)}
                      suffix="%"
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                </Row>
                
                <Table
                  size="small"
                  dataSource={batchTestResults}
                  columns={[
                    {
                      title: 'API名称',
                      dataIndex: 'routeName',
                      key: 'routeName',
                    },
                    {
                      title: '方法',
                      dataIndex: 'method',
                      key: 'method',
                      render: (method: string) => (
                        <Tag color={getMethodColor(method as HttpMethod)}>{method}</Tag>
                      )
                    },
                    {
                      title: '端点',
                      dataIndex: 'endpoint',
                      key: 'endpoint',
                      render: (endpoint: string) => <Text code>{endpoint}</Text>
                    },
                    {
                      title: '状态',
                      dataIndex: 'success',
                      key: 'success',
                      render: (success: boolean) => (
                        <Tag color={success ? 'success' : 'error'}>
                          {success ? '成功' : '失败'}
                        </Tag>
                      )
                    },
                    {
                      title: '状态码',
                      dataIndex: 'statusCode',
                      key: 'statusCode',
                      render: (code: number) => (
                        <Tag color={code >= 200 && code < 300 ? 'success' : 'error'}>
                          {code}
                        </Tag>
                      )
                    },
                    {
                      title: '执行时间',
                      dataIndex: 'executionTime',
                      key: 'executionTime',
                      render: (time: number) => `${time}ms`
                    },
                    {
                      title: '操作',
                      key: 'action',
                      render: (_, record: any) => (
                        <Button 
                          size="small" 
                          onClick={() => {
                            Modal.info({
                              title: `${record.routeName} 测试详情`,
                              width: 600,
                              content: (
                                <div>
                                  <Descriptions size="small" column={2}>
                                    <Descriptions.Item label="方法">{record.method}</Descriptions.Item>
                                    <Descriptions.Item label="端点">{record.endpoint}</Descriptions.Item>
                                    <Descriptions.Item label="状态码">{record.statusCode}</Descriptions.Item>
                                    <Descriptions.Item label="执行时间">{record.executionTime}ms</Descriptions.Item>
                                  </Descriptions>
                                  <Divider />
                                  <div>
                                    <h4>响应数据：</h4>
                                    <pre style={{ background: '#f5f5f5', padding: 12, overflow: 'auto', maxHeight: 300 }}>
                                      {JSON.stringify(record.data || { error: record.error }, null, 2)}
                                    </pre>
                                  </div>
                                </div>
                              )
                            });
                          }}
                        >
                          查看详情
                        </Button>
                      )
                    }
                  ]}
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            </div>
          )}
          
          {batchTestResults.length === 0 && (
            <Empty 
              description="尚未执行批量测试"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </div>
      </Modal>
    </div>
  );
};

export default APIRouteStep;
