/**
 * 模板应用状态管理服务
 * 管理模板应用状态，为后续配置步骤提供数据支持
 */

import { templateAPI } from './templateAPI';
import type { TemplateListItem } from '../../types/developer/template';

export interface AppliedTemplateData {
  template_key: string;
  scenario: {
    name: string;
    description: string;
    type: string;
    business_domain: string;
    target_users: string[];
    key_features: string[];
    example_instructions: string[];
  };
  entities: any[];
  apis: any[];
  roles: any[];
  workflows: any[];
  forms: any[];
  applied_at: string;
}

export interface TemplateApplicationSession {
  session_id: string;
  template_key: string;
  config: AppliedTemplateData;
  applied_at: string;
  status: 'applied' | 'configuring' | 'completed';
}

class TemplateApplicationService {
  private currentSession: string | null = null;
  private appliedData: AppliedTemplateData | null = null;

  /**
   * 应用模板
   */
  async applyTemplate(
    template: TemplateListItem,
    scenarioName: string,
    description?: string,
    customizations?: Record<string, any>,
    importSampleData?: boolean
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const response = await templateAPI.applyTemplate(
        template.key,
        scenarioName,
        description,
        customizations,
        importSampleData
      );

      if (response.data?.applied_config) {
        // 生成会话ID
        this.currentSession = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // 保存应用的数据
        this.appliedData = response.data.applied_config;
        
        // 保存到本地存储
        localStorage.setItem('ailf_template_session', this.currentSession);
        localStorage.setItem(`ailf_template_data_${this.currentSession}`, JSON.stringify(this.appliedData));

        return {
          success: true,
          data: {
            session_id: this.currentSession,
            applied_config: this.appliedData,
            template_info: response.data.template_info
          }
        };
      }

      return {
        success: false,
        error: '应用模板失败：响应数据格式错误'
      };

    } catch (error: any) {
      console.error('应用模板失败:', error);
      return {
        success: false,
        error: error.response?.data?.message || '应用模板失败'
      };
    }
  }

  /**
   * 获取当前应用的模板数据
   */
  getCurrentAppliedData(): AppliedTemplateData | null {
    if (!this.appliedData && this.currentSession) {
      // 尝试从本地存储恢复
      const storedData = localStorage.getItem(`ailf_template_data_${this.currentSession}`);
      if (storedData) {
        try {
          this.appliedData = JSON.parse(storedData);
        } catch (error) {
          console.error('恢复模板数据失败:', error);
        }
      }
    }
    return this.appliedData;
  }

  /**
   * 获取当前会话ID
   */
  getCurrentSession(): string | null {
    if (!this.currentSession) {
      // 尝试从本地存储恢复
      this.currentSession = localStorage.getItem('ailf_template_session');
    }
    return this.currentSession;
  }

  /**
   * 获取实体建模步骤的数据
   */
  getEntitiesForStep(): any[] {
    const data = this.getCurrentAppliedData();
    return data?.entities || [];
  }

  /**
   * 获取API路由步骤的数据
   */
  getApisForStep(): any[] {
    const data = this.getCurrentAppliedData();
    return data?.apis || [];
  }

  /**
   * 获取权限管理步骤的数据
   */
  getRolesForStep(): any[] {
    const data = this.getCurrentAppliedData();
    return data?.roles || [];
  }

  /**
   * 获取工作流步骤的数据
   */
  getWorkflowsForStep(): any[] {
    const data = this.getCurrentAppliedData();
    return data?.workflows || [];
  }

  /**
   * 获取表单配置步骤的数据
   */
  getFormsForStep(): any[] {
    const data = this.getCurrentAppliedData();
    return data?.forms || [];
  }

  /**
   * 更新步骤数据
   */
  updateStepData(stepName: string, stepData: any): void {
    if (this.appliedData) {
      (this.appliedData as any)[stepName] = stepData;
      
      // 更新本地存储
      if (this.currentSession) {
        localStorage.setItem(`ailf_template_data_${this.currentSession}`, JSON.stringify(this.appliedData));
      }
    }
  }

  /**
   * 检查是否有应用的模板
   */
  hasAppliedTemplate(): boolean {
    return this.getCurrentAppliedData() !== null;
  }

  /**
   * 获取应用的模板信息
   */
  getAppliedTemplateInfo(): { template_key: string; scenario_name: string } | null {
    const data = this.getCurrentAppliedData();
    if (data) {
      return {
        template_key: data.template_key,
        scenario_name: data.scenario.name
      };
    }
    return null;
  }

  /**
   * 清除当前会话
   */
  clearSession(): void {
    if (this.currentSession) {
      localStorage.removeItem(`ailf_template_data_${this.currentSession}`);
      localStorage.removeItem('ailf_template_session');
    }
    this.currentSession = null;
    this.appliedData = null;
  }

  /**
   * 检查模板是否已应用
   */
  isTemplateApplied(templateKey: string): boolean {
    const data = this.getCurrentAppliedData();
    return data?.template_key === templateKey;
  }

  /**
   * 获取场景配置数据
   */
  getScenarioData(): any {
    const data = this.getCurrentAppliedData();
    return data?.scenario || null;
  }

  /**
   * 标记配置完成
   */
  markConfigurationComplete(): void {
    if (this.currentSession && this.appliedData) {
      const sessionData = {
        session_id: this.currentSession,
        template_key: this.appliedData.template_key,
        config: this.appliedData,
        applied_at: this.appliedData.applied_at,
        status: 'completed' as const
      };
      
      localStorage.setItem(`ailf_completed_${this.currentSession}`, JSON.stringify(sessionData));
    }
  }

  /**
   * 获取配置进度
   */
  getConfigurationProgress(): {
    total: number;
    completed: number;
    steps: { name: string; completed: boolean }[];
  } {
    const data = this.getCurrentAppliedData();
    if (!data) {
      return { total: 0, completed: 0, steps: [] };
    }

    const steps = [
      { name: 'scenario', completed: !!data.scenario },
      { name: 'entities', completed: data.entities.length > 0 },
      { name: 'apis', completed: data.apis.length > 0 },
      { name: 'roles', completed: data.roles.length > 0 },
      { name: 'workflows', completed: data.workflows.length > 0 },
      { name: 'forms', completed: data.forms.length > 0 }
    ];

    const completed = steps.filter(step => step.completed).length;
    
    return {
      total: steps.length,
      completed,
      steps
    };
  }
}

// 导出单例实例
export const templateApplicationService = new TemplateApplicationService();
export default templateApplicationService;
