/**
 * 增强的动态API服务
 * 支持动态调用后端注册的API路由
 */

import { apiClient } from '../common/apiClient';
import type { APIResponse } from '../../types/developer/route';

export interface DynamicAPIOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  params?: Record<string, any>;
  data?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
}

export interface DynamicAPIResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode: number;
  headers?: Record<string, string>;
  executionTime?: number;
}

export class DynamicAPIService {
  /**
   * 调用动态API
   */
  static async callDynamicAPI<T = any>(options: DynamicAPIOptions): Promise<DynamicAPIResult<T>> {
    const startTime = Date.now();
    
    try {
      const {
        method,
        endpoint,
        params = {},
        data = {},
        headers = {},
        timeout = 10000
      } = options;

      // 确保endpoint格式正确
      const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      
      let response: APIResponse;

      switch (method) {
        case 'GET':
          response = await apiClient.get(normalizedEndpoint, { params });
          break;
        case 'POST':
          response = await apiClient.post(normalizedEndpoint, data);
          break;
        case 'PUT':
          response = await apiClient.put(normalizedEndpoint, data);
          break;
        case 'DELETE':
          response = await apiClient.delete(normalizedEndpoint, { params });
          break;
        case 'PATCH':
          // PATCH使用POST模拟，添加方法覆盖头
          response = await apiClient.post(normalizedEndpoint, { ...data, _method: 'PATCH' });
          break;
        default:
          throw new Error(`不支持的HTTP方法: ${method}`);
      }

      const executionTime = Date.now() - startTime;

      return {
        success: true,
        data: response.data,
        statusCode: response.code || 200,
        headers: {}, // APIResponse没有headers字段
        executionTime
      };
    } catch (error: any) {
      const executionTime = Date.now() - startTime;
      
      console.error('动态API调用失败:', error);
      
      return {
        success: false,
        error: error.message || '未知错误',
        statusCode: error.response?.status || 500,
        headers: error.response?.headers || {},
        executionTime
      };
    }
  }

  /**
   * 调用实体CRUD API
   */
  static async callEntityAPI(
    entity: string,
    operation: 'list' | 'create' | 'get' | 'update' | 'delete',
    options: {
      id?: string;
      data?: Record<string, any>;
      params?: Record<string, any>;
    } = {}
  ): Promise<DynamicAPIResult> {
    const { id, data = {}, params = {} } = options;
    
    let endpoint = `/api/v1/${entity}s`;
    let method: DynamicAPIOptions['method'] = 'GET';
    let requestData = {};

    switch (operation) {
      case 'list':
        method = 'GET';
        break;
      case 'create':
        method = 'POST';
        requestData = data;
        break;
      case 'get':
        if (!id) throw new Error('获取单个实体需要提供ID');
        endpoint = `${endpoint}/${id}`;
        method = 'GET';
        break;
      case 'update':
        if (!id) throw new Error('更新实体需要提供ID');
        endpoint = `${endpoint}/${id}`;
        method = 'PUT';
        requestData = data;
        break;
      case 'delete':
        if (!id) throw new Error('删除实体需要提供ID');
        endpoint = `${endpoint}/${id}`;
        method = 'DELETE';
        break;
    }

    return this.callDynamicAPI({
      method,
      endpoint,
      params,
      data: requestData
    });
  }

  /**
   * 批量调用API
   */
  static async batchCallAPIs(requests: DynamicAPIOptions[]): Promise<DynamicAPIResult[]> {
    const results = await Promise.allSettled(
      requests.map(request => this.callDynamicAPI(request))
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          success: false,
          error: result.reason?.message || '批量请求失败',
          statusCode: 500,
          executionTime: 0
        };
      }
    });
  }

  /**
   * 测试API连通性
   */
  static async testAPIConnectivity(endpoint: string, method: DynamicAPIOptions['method'] = 'GET'): Promise<{
    accessible: boolean;
    responseTime: number;
    statusCode: number;
    error?: string;
  }> {
    const startTime = Date.now();
    
    try {
      const result = await this.callDynamicAPI({
        method,
        endpoint,
        timeout: 5000
      });

      return {
        accessible: result.success,
        responseTime: result.executionTime || 0,
        statusCode: result.statusCode,
        error: result.error
      };
    } catch (error: any) {
      return {
        accessible: false,
        responseTime: Date.now() - startTime,
        statusCode: 500,
        error: error.message
      };
    }
  }

  /**
   * 上传文件
   */
  static async uploadFile(
    endpoint: string,
    file: File,
    additionalData: Record<string, any> = {}
  ): Promise<DynamicAPIResult> {
    const startTime = Date.now();
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // 添加额外数据
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
      });

      const token = apiClient.getToken();
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      const data = await response.json();
      const executionTime = Date.now() - startTime;

      return {
        success: response.ok,
        data,
        statusCode: response.status,
        executionTime
      };
    } catch (error: any) {
      const executionTime = Date.now() - startTime;
      
      return {
        success: false,
        error: error.message || '文件上传失败',
        statusCode: 500,
        executionTime
      };
    }
  }

  /**
   * 下载文件
   */
  static async downloadFile(
    endpoint: string,
    filename?: string
  ): Promise<{
    success: boolean;
    error?: string;
    blob?: Blob;
  }> {
    try {
      const token = apiClient.getToken();
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      if (!response.ok) {
        throw new Error(`下载失败: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      
      // 如果提供了文件名，自动下载
      if (filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      return {
        success: true,
        blob
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || '文件下载失败'
      };
    }
  }

  /**
   * 获取图片URL（支持动态参数）
   */
  static getImageURL(
    baseEndpoint: string,
    imageId: string,
    options: {
      width?: number;
      height?: number;
      quality?: number;
      format?: 'jpg' | 'png' | 'webp';
    } = {}
  ): string {
    const { width, height, quality, format } = options;
    const params = new URLSearchParams();
    
    if (width) params.append('w', width.toString());
    if (height) params.append('h', height.toString());
    if (quality) params.append('q', quality.toString());
    if (format) params.append('f', format);

    const queryString = params.toString();
    const separator = baseEndpoint.includes('?') ? '&' : '?';
    
    return `${baseEndpoint}/${imageId}${queryString ? separator + queryString : ''}`;
  }
}

export default DynamicAPIService;
