/**
 * 配置状态检查Hook
 * 用于检查七步配置是否完成
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { apiUrls } from '../config/api';

export interface ConfigurationStatus {
  is_completed: boolean;
  allowed: boolean;
  message: string;
  status: 'completed' | 'incomplete';
  incomplete_steps?: number[];
  incomplete_step_names?: string[];
  configuration_status?: {
    scenario_id: string;
    steps: Record<string, { completed: boolean; completed_at: string | null }>;
    all_completed: boolean;
    all_completed_at: string | null;
    completed_count: number;
    total_steps: number;
    completion_percentage: number;
  };
}

export interface UseConfigurationStatusReturn {
  status: ConfigurationStatus | null;
  loading: boolean;
  error: string | null;
  checkStatus: (options?: { silent?: boolean }) => Promise<void>;
  isConfigurationCompleted: boolean;
  canUseFeatures: boolean;
  isBackendAvailable: boolean;
}

export const useConfigurationStatus = (): UseConfigurationStatusReturn => {
  const [status, setStatus] = useState<ConfigurationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);
  const isCheckingRef = useRef(false);

  const checkStatus = useCallback(async (options?: { silent?: boolean }) => {
    if (isCheckingRef.current) return;
    isCheckingRef.current = true;
    try {
      // 轮询时不闪烁 UI（避免在“后端未启动”页与“检查中...”之间来回跳）
      if (!options?.silent) {
        setLoading(true);
        setError(null);
      }

      const response = await fetch(apiUrls.configurationStatusCheck(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 5xx 错误表示服务器/网关问题，视为后端不可用
        if (response.status >= 500) {
          setIsBackendAvailable(false);
          setError('后端服务未启动或不可用');
          console.error('后端服务不可用，HTTP状态:', response.status);
          setStatus(null);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setStatus(data);
      setIsBackendAvailable(true);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '检查配置状态失败';
      console.error('配置状态检查错误:', err, 'Error type:', typeof err, 'Message:', errorMessage);
      
      // 检测是否是网络错误（后端未启动）
      // fetch 失败通常抛出 TypeError，但不同浏览器行为可能不同
      const isNetworkError = 
        errorMessage.toLowerCase().includes('failed to fetch') ||
        errorMessage.toLowerCase().includes('network') ||
        errorMessage.toLowerCase().includes('fetch') ||
        errorMessage.toLowerCase().includes('econnrefused') ||
        errorMessage.toLowerCase().includes('connection refused') ||
        errorMessage.includes('ERR_CONNECTION_REFUSED') ||
        (err instanceof TypeError);
      
      if (isNetworkError) {
        setIsBackendAvailable(false);
        setError('后端服务未启动');
        console.error('后端服务未启动:', err);
        setStatus(null);
      } else {
        setIsBackendAvailable(true);
        setError(errorMessage);
        console.error('检查配置状态失败:', err);
        
        // 设置默认状态（未完成）
        setStatus({
          is_completed: false,
          allowed: false,
          message: '无法检查配置状态，请稍后重试',
          status: 'incomplete',
          incomplete_steps: [1, 2, 3, 4, 5, 6, 7],
          incomplete_step_names: [
            '开发者认证',
            '场景配置',
            '模板选择',
            '实体建模',
            'API路由管理',
            '工作流设计',
            '角色管理'
          ]
        });
      }
    } finally {
      isCheckingRef.current = false;
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  // 后端未启动时进行轮询，启动后自动停止轮询
  useEffect(() => {
    if (isBackendAvailable) return;

    const intervalMs = 2000;
    const timer = window.setInterval(() => {
      checkStatus({ silent: true });
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [isBackendAvailable, checkStatus]);

  const isConfigurationCompleted = status?.is_completed ?? false;
  const canUseFeatures = status?.allowed ?? false;

  return {
    status,
    loading,
    error,
    checkStatus,
    isConfigurationCompleted,
    canUseFeatures,
    isBackendAvailable,
  };
};

export default useConfigurationStatus;
