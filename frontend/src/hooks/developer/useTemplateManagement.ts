/**
 * 模板管理Hook
 */

import { useState, useCallback, useEffect } from 'react';
import { templateAPI } from '../../services/developer/templateAPI';
import type { 
  TemplateSelectionState, 
  TemplateListItem, 
  TemplateCategory,
  TemplateDetail 
} from '../../types/developer/template';
import { APIError } from '../../services/common/apiClient';

export const useTemplateManagement = () => {
  const [state, setState] = useState<TemplateSelectionState>({
    selectedTemplate: null,
    templates: [],
    categories: [],
    selectedCategory: null,
    isLoading: false,
    error: null,
  });

  // 加载模板列表
  const loadTemplates = useCallback(async (category?: TemplateCategory) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await templateAPI.getTemplates({
        category,
        include_preview: true,
      });

      setState(prev => ({
        ...prev,
        templates: response.data.templates,
        categories: response.data.categories,
        selectedCategory: category || null,
        isLoading: false,
      }));

      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error instanceof APIError 
        ? error.message 
        : '加载模板列表失败，请重试';

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      return { success: false, error: errorMessage };
    }
  }, []);

  // 选择模板
  const selectTemplate = useCallback((template: TemplateListItem | null) => {
    setState(prev => ({
      ...prev,
      selectedTemplate: template,
    }));
  }, []);

  // 获取模板详情
  const getTemplateDetail = useCallback(async (templateKey: string): Promise<{
    success: boolean;
    data?: TemplateDetail;
    error?: string;
  }> => {
    try {
      const response = await templateAPI.getTemplateDetail(templateKey);
      return { success: true, data: response.data.template };
    } catch (error) {
      const errorMessage = error instanceof APIError 
        ? error.message 
        : '获取模板详情失败，请重试';
      return { success: false, error: errorMessage };
    }
  }, []);

  // 筛选模板
  const filterTemplates = useCallback((category: TemplateCategory | null) => {
    loadTemplates(category || undefined);
  }, [loadTemplates]);

  // 清除错误
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // 重置状态
  const resetState = useCallback(() => {
    setState({
      selectedTemplate: null,
      templates: [],
      categories: [],
      selectedCategory: null,
      isLoading: false,
      error: null,
    });
  }, []);

  // 初始化时加载模板列表
  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  return {
    // 状态
    state,
    
    // 操作方法
    loadTemplates,
    selectTemplate,
    getTemplateDetail,
    filterTemplates,
    clearError,
    resetState,
    
    // 便捷访问
    selectedTemplate: state.selectedTemplate,
    templates: state.templates,
    categories: state.categories,
    selectedCategory: state.selectedCategory,
    isLoading: state.isLoading,
    error: state.error,
  };
};
