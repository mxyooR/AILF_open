/**
 * 场景管理API服务
 */

import { apiClient } from '../common/apiClient';
import type {
  CreateScenarioRequest,
  ScenarioResponse,
  GetScenarioResponse,
  Scenario,
} from '../../types/developer/scenario';

export const scenarioAPI = {
  /**
   * 获取当前活跃场景配置
   * GET /api/v1/scenario
   */
  async getCurrent(includeDetails: boolean = true): Promise<GetScenarioResponse> {
    const response = await apiClient.get<GetScenarioResponse['data']>(
      `/api/v1/scenario?include_details=${includeDetails}`
    );
    return response;
  },

  /**
   * 创建或更新场景配置
   * POST /api/v1/scenario
   */
  async createOrUpdate(request: CreateScenarioRequest): Promise<ScenarioResponse> {
    const response = await apiClient.post<ScenarioResponse['data']>(
      '/api/v1/scenario',
      request
    );
    return response;
  },

  /**
   * 获取特定场景配置
   * GET /api/v1/scenario/{scenario_id}
   */
  async getById(scenarioId: string): Promise<GetScenarioResponse> {
    const response = await apiClient.get<GetScenarioResponse['data']>(
      `/api/v1/scenario/${scenarioId}`
    );
    return response;
  },

  /**
   * 验证当前场景配置的有效性
   * POST /api/v1/scenario/validate
   */
  async validate(scenarioId: string, checkDependencies: boolean = true, checkCompleteness: boolean = true): Promise<{ code: number; message: string; data: { valid: boolean; errors?: string[] } }> {
    const response = await apiClient.post<{ valid: boolean; errors?: string[] }>(
      '/api/v1/scenario/validate',
      {
        scenario_id: scenarioId,
        check_dependencies: checkDependencies,
        check_completeness: checkCompleteness
      }
    );
    return response;
  },

  /**
   * 从预设模板创建场景配置
   * POST /api/v1/scenario/from-template
   */
  async createFromTemplate(templateKey: string, name: string, description?: string, customizations?: Record<string, any>): Promise<ScenarioResponse> {
    const response = await apiClient.post<ScenarioResponse['data']>(
      '/api/v1/scenario/from-template',
      {
        template_key: templateKey,
        name: name,
        description: description,
        customizations: customizations || {}
      }
    );
    return response;
  },


};

export default scenarioAPI;
