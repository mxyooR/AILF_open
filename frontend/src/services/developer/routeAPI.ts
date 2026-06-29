/**
 * API路由管理服务
 */

import { apiClient } from '../common/apiClient';
import type {
  APIRoute,
  APIRouteCreateRequest,
  APIRouteUpdateRequest,
  RouteListResponse,
  RouteStatusDetail,
  RouteHealthResponse,
  RouteQueryParams,
  APIResponse
} from '../../types/developer/route';

export const routeAPI = {
  /**
   * 创建API路由
   */
  async createRoute(routeData: APIRouteCreateRequest): Promise<APIResponse<{ route: APIRoute }>> {
    return await apiClient.post('/api/v1/routes/register', routeData);
  },

  /**
   * 获取API路由列表
   */
  async getRoutes(params?: RouteQueryParams): Promise<APIResponse<RouteListResponse>> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.method) queryParams.append('method', params.method);
    if (params?.entity) queryParams.append('entity', params.entity);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/v1/routes?${queryString}` : '/api/v1/routes';

    return await apiClient.get(endpoint);
  },

  /**
   * 获取单个API路由详情
   */
  async getRoute(routeId: string): Promise<APIResponse<{ route: APIRoute }>> {
    return await apiClient.get(`/api/v1/routes/${routeId}`);
  },

  /**
   * 更新API路由
   */
  async updateRoute(routeId: string, routeData: APIRouteUpdateRequest): Promise<APIResponse<{ route: APIRoute }>> {
    return await apiClient.put(`/api/v1/routes/${routeId}`, routeData);
  },

  /**
   * 删除API路由
   */
  async deleteRoute(routeId: string, force: boolean = false): Promise<APIResponse<{ route_id: string; api_id: string; endpoint: string; method: string; deleted_at: string }>> {
    const queryParams = new URLSearchParams();
    if (force) queryParams.append('force', 'true');

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/v1/routes/${routeId}?${queryString}` : `/api/v1/routes/${routeId}`;

    return await apiClient.delete(endpoint);
  },

  /**
   * 激活API路由
   */
  async activateRoute(routeId: string): Promise<APIResponse<{ route: Pick<APIRoute, 'id' | 'api_id' | 'name' | 'endpoint' | 'method' | 'status'> & { activated_at: string } }>> {
    return await apiClient.post(`/api/v1/routes/${routeId}/activate`, {});
  },

  /**
   * 停用API路由
   */
  async deactivateRoute(routeId: string): Promise<APIResponse<{ route: Pick<APIRoute, 'id' | 'api_id' | 'name' | 'endpoint' | 'method' | 'status'> & { deactivated_at: string } }>> {
    return await apiClient.post(`/api/v1/routes/${routeId}/deactivate`, {});
  },

  /**
   * 获取API路由状态
   */
  async getRouteStatus(routeId: string): Promise<APIResponse<RouteStatusDetail>> {
    return await apiClient.get(`/api/v1/routes/${routeId}/status`);
  },

  /**
   * 检查所有API路由健康状态
   */
  async getRoutesHealth(): Promise<APIResponse<RouteHealthResponse>> {
    return await apiClient.get('/api/v1/routes/health');
  },

  /**
   * 测试API路由
   */
  async testRoute(routeId: string, testData?: any): Promise<APIResponse<any>> {
    // 这里可以实现API测试功能
    // 实际实现可能需要调用特定的测试端点
    return await apiClient.post(`/api/v1/routes/${routeId}/test`, {
      test_data: testData
    });
  }
};

export default routeAPI;
