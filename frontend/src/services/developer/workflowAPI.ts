/**
 * 工作流设计API服务
 */

import { apiClient } from '../common/apiClient';
import type {
  WorkflowDefinition,
  WorkflowCreateRequest,
  WorkflowUpdateRequest,
  WorkflowNode,
  NodeCreateRequest,
  NodeUpdateRequest,
} from '../../types/developer/workflowTypes';

// API响应类型
interface APIResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp?: string;
}

// 工作流列表响应
interface WorkflowListResponse {
  workflows: Array<{
    id: string;
    name: string;
    description: string;
    business_scenario: string;
    status: 'active' | 'draft' | 'inactive';
    version: string;
    node_count: number;
    instance_count: number;
    created_at: string;
    updated_at: string;
  }>;
  pagination: {
    current_page: number;
    per_page: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// 工作流详情响应
interface WorkflowDetailResponse {
  workflow: WorkflowDefinition & {
    node_relationships: Record<string, {
      parents?: string[];
      children?: string[];
      conditions?: Array<{ type: string; [key: string]: any }>;
    }>;
  };
}

export const workflowAPI = {
  /**
   * 创建工作流
   * POST /api/v1/workflow
   */
  async createWorkflow(request: WorkflowCreateRequest): Promise<APIResponse<{ workflow: { id: string; name: string; status: string; created_at: string; node_count: number; complexity: string } }>> {
    const response = await apiClient.post<APIResponse<{ workflow: { id: string; name: string; status: string; created_at: string; node_count: number; complexity: string } }>['data']>(
      '/api/v1/workflow',
      request
    );
    return response;
  },

  /**
   * 获取工作流列表
   * GET /api/v1/workflow
   */
  async getWorkflowsList(params?: {
    page?: number;
    limit?: number;
    status?: string;
    business_scenario?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<APIResponse<WorkflowListResponse>> {
    const queryParams = new URLSearchParams();

    if (params?.page) {
      queryParams.append('page', params.page.toString());
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.business_scenario) {
      queryParams.append('business_scenario', params.business_scenario);
    }
    if (params?.search) {
      queryParams.append('search', params.search);
    }
    if (params?.sort_by) {
      queryParams.append('sort_by', params.sort_by);
    }
    if (params?.sort_order) {
      queryParams.append('sort_order', params.sort_order);
    }

    const url = `/api/v1/workflow${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiClient.get<APIResponse<WorkflowListResponse>['data']>(url);
    return response;
  },

  /**
   * 获取工作流详情
   * GET /api/v1/workflow/{workflow_id}
   */
  async getWorkflowDetail(workflowId: string): Promise<APIResponse<WorkflowDetailResponse>> {
    const response = await apiClient.get<APIResponse<WorkflowDetailResponse>['data']>(
      `/api/v1/workflow/${workflowId}`
    );
    return response;
  },

  /**
   * 更新工作流
   * PUT /api/v1/workflow/{workflow_id}
   */
  async updateWorkflow(workflowId: string, request: WorkflowUpdateRequest): Promise<APIResponse<{ workflow: WorkflowDefinition }>> {
    const response = await apiClient.put<APIResponse<{ workflow: WorkflowDefinition }>['data']>(
      `/api/v1/workflow/${workflowId}`,
      request
    );
    return response;
  },

  /**
   * 删除工作流
   * DELETE /api/v1/workflow/{workflow_id}
   */
  async deleteWorkflow(workflowId: string): Promise<APIResponse<{ deleted: boolean }>> {
    const response = await apiClient.delete<APIResponse<{ deleted: boolean }>['data']>(
      `/api/v1/workflow/${workflowId}`
    );
    return response;
  },

  /**
   * 获取工作流节点列表
   * GET /api/v1/workflow/{workflow_id}/nodes
   */
  async getWorkflowNodes(workflowId: string): Promise<APIResponse<{ nodes: WorkflowNode[] }>> {
    const response = await apiClient.get<APIResponse<{ nodes: WorkflowNode[] }>['data']>(
      `/api/v1/workflow/${workflowId}/nodes`
    );
    return response;
  },

  /**
   * 添加节点
   * POST /api/v1/workflow/{workflow_id}/nodes
   */
  async addNode(workflowId: string, request: NodeCreateRequest): Promise<APIResponse<{ node: WorkflowNode; workflow_updated: boolean }>> {
    const response = await apiClient.post<APIResponse<{ node: WorkflowNode; workflow_updated: boolean }>['data']>(
      `/api/v1/workflow/${workflowId}/nodes`,
      request
    );
    return response;
  },

  /**
   * 更新节点
   * PUT /api/v1/workflow/{workflow_id}/nodes/{node_id}
   */
  async updateNode(workflowId: string, nodeId: string, request: NodeUpdateRequest): Promise<APIResponse<{ node: WorkflowNode; workflow_updated: boolean }>> {
    const response = await apiClient.put<APIResponse<{ node: WorkflowNode; workflow_updated: boolean }>['data']>(
      `/api/v1/workflow/${workflowId}/nodes/${nodeId}`,
      request
    );
    return response;
  },

  /**
   * 删除节点
   * DELETE /api/v1/workflow/{workflow_id}/nodes/{node_id}
   */
  async deleteNode(workflowId: string, nodeId: string): Promise<APIResponse<{ deleted: boolean; workflow_updated: boolean }>> {
    const response = await apiClient.delete<APIResponse<{ deleted: boolean; workflow_updated: boolean }>['data']>(
      `/api/v1/workflow/${workflowId}/nodes/${nodeId}`
    );
    return response;
  },

  /**
   * 验证工作流定义
   */
  async validateWorkflow(workflowId: string): Promise<APIResponse<{ valid: boolean; errors: string[] }>> {
    const response = await apiClient.post<APIResponse<{ valid: boolean; errors: string[] }>['data']>(
      `/api/v1/workflow/${workflowId}/validate`
    );
    return response;
  },

  /**
   * 测试工作流执行
   */
  async testWorkflow(workflowId: string, inputs: Record<string, any>): Promise<APIResponse<{ result: any; execution_log: any[] }>> {
    const response = await apiClient.post<APIResponse<{ result: any; execution_log: any[] }>['data']>(
      `/api/v1/workflow/${workflowId}/test`,
      { inputs }
    );
    return response;
  },
};

export default workflowAPI; 