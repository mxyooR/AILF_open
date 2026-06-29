/**
 * 场景配置Hook
 */

import { useState, useCallback, useEffect } from 'react';
import { scenarioAPI } from '../../services/developer/scenarioAPI';
import type { 
  Scenario, 
  ScenarioFormData, 
  CreateScenarioRequest,
  ScenarioType 
} from '../../types/developer/scenario';
import { APIError } from '../../services/common/apiClient';

interface ScenarioState {
  currentScenario: Scenario | null;
  isLoading: boolean;
  error: string | null;
  isValidating: boolean;
  validationErrors: string[];
}

export const useScenarioConfig = () => {
  const [scenarioState, setScenarioState] = useState<ScenarioState>({
    currentScenario: null,
    isLoading: false,
    error: null,
    isValidating: false,
    validationErrors: [],
  });

  // 获取当前场景
  const loadCurrentScenario = useCallback(async () => {
    setScenarioState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await scenarioAPI.getCurrent(true);
      setScenarioState(prev => ({
        ...prev,
        currentScenario: response.data.scenario,
        isLoading: false,
      }));
      return { success: true, data: response.data.scenario };
    } catch (error) {
      const errorMessage = error instanceof APIError 
        ? error.message 
        : '获取场景配置失败';

      setScenarioState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      return { success: false, error: errorMessage };
    }
  }, []);

  // 创建或更新场景
  const saveScenario = useCallback(async (formData: ScenarioFormData) => {
    setScenarioState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const request: CreateScenarioRequest = {
        name: formData.name,
        type: formData.type,
        description: formData.description,
        config: {
          business_domain: formData.business_domain,
          target_users: formData.target_users,
          key_features: formData.key_features,
          example_instructions: formData.example_instructions,
          custom_settings: formData.custom_settings,
        },
      };

      const response = await scenarioAPI.createOrUpdate(request);
      
      setScenarioState(prev => ({
        ...prev,
        currentScenario: response.data.scenario,
        isLoading: false,
      }));

      return { success: true, data: response.data.scenario };
    } catch (error) {
      const errorMessage = error instanceof APIError 
        ? error.message 
        : '保存场景配置失败';

      setScenarioState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      return { success: false, error: errorMessage };
    }
  }, []);

  // 验证场景配置
  const validateScenario = useCallback(async (scenarioId?: string) => {
    setScenarioState(prev => ({ ...prev, isValidating: true, validationErrors: [] }));

    try {
      // 如果没有提供scenarioId，使用当前场景的ID
      const targetScenarioId = scenarioId || scenarioState.currentScenario?.id;
      if (!targetScenarioId) {
        throw new Error('没有可验证的场景ID');
      }

      const response = await scenarioAPI.validate(targetScenarioId);

      setScenarioState(prev => ({
        ...prev,
        isValidating: false,
        validationErrors: response.data.errors || [],
      }));

      return {
        success: true,
        valid: response.data.valid,
        errors: response.data.errors || []
      };
    } catch (error) {
      const errorMessage = error instanceof APIError
        ? error.message
        : '验证场景配置失败';

      setScenarioState(prev => ({
        ...prev,
        isValidating: false,
        error: errorMessage,
      }));

      return { success: false, error: errorMessage };
    }
  }, [scenarioState.currentScenario?.id]);

  // 从模板创建场景
  const createFromTemplate = useCallback(async (templateKey: string, name: string, description?: string, customizations?: Record<string, any>) => {
    setScenarioState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await scenarioAPI.createFromTemplate(templateKey, name, description, customizations);

      setScenarioState(prev => ({
        ...prev,
        currentScenario: response.data.scenario,
        isLoading: false,
      }));

      return { success: true, data: response.data.scenario };
    } catch (error) {
      const errorMessage = error instanceof APIError
        ? error.message
        : '从模板创建场景失败';

      setScenarioState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      return { success: false, error: errorMessage };
    }
  }, []);



  // 清除错误
  const clearError = useCallback(() => {
    setScenarioState(prev => ({ ...prev, error: null }));
  }, []);

  // 组件挂载时加载当前场景
  useEffect(() => {
    loadCurrentScenario();
  }, [loadCurrentScenario]);

  return {
    scenarioState,
    loadCurrentScenario,
    saveScenario,
    validateScenario,
    createFromTemplate,
    clearError,
  };
};
