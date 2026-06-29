/**
 * AILF Main Page - 主页面组件
 * 遵循单一文件规则，包含原有的主界面逻辑
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';
import '../styles/apple-style.css';
import axios from 'axios';
// 移除amis相关导入，使用原生通知
import copy from 'copy-to-clipboard';
import GeneratedInterface from '../components/GeneratedInterface';
import SiriOrb from '../components/SiriOrb';
import ConfigurationIncompleteWarning from '../components/common/ConfigurationIncompleteWarning';
import UserStatusIndicator from '../components/user/UserStatusIndicator';
import { useLocalVoice } from '../hooks/useLocalVoice';
import { useUserAuth } from '../hooks/user/useUserAuth';
import { userTokenManager } from '../services/common/userTokenManager';
import { useConfigurationStatus } from '../hooks/useConfigurationStatus';
import { appConfigAPI, AppConfig } from '../services/appConfig';
import AppleRibbonBackground from '../components/AppleRibbonBackground';

// AILF 配置
const AILF_CONFIG = {
  apiBaseUrl: '',
  amisTheme: 'cxd'
};

const AI_COMMAND_ASYNC_ENDPOINT = '/api/v1/command/async';
const AI_COMMAND_POLL_INTERVAL_MS = 1200;
const AI_COMMAND_MAX_WAIT_MS = 600000;

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

type AsyncCommandResult = {
  schema: any;
  responseText: string;
  message: string;
  raw: any;
};

const MainPage: React.FC = () => {
  const navigate = useNavigate();

  // 用户认证状态
  const { authState } = useUserAuth();

  // 配置状态检查
  const {
    status: configStatus,
    loading: configLoading,
    canUseFeatures,
    isConfigurationCompleted,
    isBackendAvailable,
    checkStatus: recheckConfigStatus
  } = useConfigurationStatus();

  // 控制body样式以启用呼吸效果
  useEffect(() => {
    // 确保主页面有正确的样式
    document.body.className = 'main-page-body';
    document.body.style.background = '';
    document.body.style.animation = '';

    return () => {
      // 清理body类名，让其他页面可以设置自己的样式
      document.body.className = '';
      document.body.style.background = '';
      document.body.style.animation = '';
    };
  }, []);

  // 加载应用配置
  useEffect(() => {
    const loadAppConfig = async () => {
      try {
        const config = await appConfigAPI.getAppConfig();
        setAppConfig(config);
      } catch (error) {
        console.error('加载应用配置失败:', error);
        // 保持默认配置
      }
    };

    loadAppConfig();
  }, []);

  // 状态管理
  const [amisSchema, setAmisSchema] = useState<any>(null);
  const [amisKey, setAmisKey] = useState(0);
  const [responseText, setResponseText] = useState('');
  const [errorText, setErrorText] = useState('');
  const [menuCommand, setMenuCommand] = useState('');
  const [isCommandModalOpen, setIsCommandModalOpen] = useState(false);
  const menuInputRef = useRef<HTMLInputElement | null>(null);

  const [appConfig, setAppConfig] = useState<AppConfig>({ title: 'AILF', subtitle: '开发者配置面板', backgroundStyle: 'mesh' });

  // 语音相关状态 - 混合模式：优先 Web Speech API，失败时切换到本地 Whisper
  const {
    isListening,
    transcript,
    isSpeaking,
    volume,
    isModelLoading,
    modelLoadProgress,
    startListening,
    stopListening,
    speak,
    setTranscript,
    voiceError,
    recognitionMode,
    loadModel
  } = useLocalVoice();

  // 监听语音识别错误
  useEffect(() => {
    if (voiceError) {
      setErrorText(voiceError);
      // 如果是网络错误，不要一直播报以免烦人，只显示文字即可
      if (!voiceError.includes('网络')) {
        speak(voiceError);
      }
    }
  }, [voiceError, speak]);

  const submitAsyncCommand = useCallback(async (
    command: string,
    context: Record<string, any>,
    headers: Record<string, string> = {},
    timeoutMs: number = AI_COMMAND_MAX_WAIT_MS
  ): Promise<AsyncCommandResult> => {
    const submitResponse = await axios.post(
      `${AILF_CONFIG.apiBaseUrl}${AI_COMMAND_ASYNC_ENDPOINT}`,
      { command, context },
      { timeout: 30000, headers }
    );

    const taskId = submitResponse?.data?.data?.task_id;
    if (!taskId) {
      throw new Error('异步任务提交失败：未返回 task_id');
    }

    const pollUrl = `${AILF_CONFIG.apiBaseUrl}${AI_COMMAND_ASYNC_ENDPOINT}/${taskId}`;
    const deadline = Date.now() + timeoutMs;

    while (Date.now() < deadline) {
      const statusResponse = await axios.get(pollUrl, {
        timeout: 30000,
        headers
      });

      const taskData = statusResponse?.data?.data || {};
      const taskStatus = taskData.status;

      if (taskStatus === 'SUCCESS') {
        const result = taskData.result || {};
        return {
          schema: result.amis_schema || result.schema || null,
          responseText: result.response_text || '',
          message: statusResponse?.data?.message || '',
          raw: result
        };
      }

      if (taskStatus === 'FAILURE') {
        throw new Error(taskData.error || '异步任务执行失败');
      }

      await sleep(AI_COMMAND_POLL_INTERVAL_MS);
    }

    throw new Error('AI推理超时，请稍后重试');
  }, []);

  // Amis 环境配置
  const amisEnv = {
    fetcher: async (api: any) => {
      console.log('[AILF] Amis fetcher called:', api);
      try {
        // 处理认证头
        let headers = { ...api.headers };

        // 处理 amis 本地存储语法 ${ls:access_token}
        if (headers.Authorization && headers.Authorization.includes('${ls:access_token}')) {
          const userToken = userTokenManager.getToken();
          if (userToken) {
            headers.Authorization = `Bearer ${userToken}`;
            console.log('[AILF] 已添加用户认证头:', headers.Authorization.substring(0, 20) + '...');
          } else {
            console.log('[AILF] 警告：需要认证但用户未登录');
            delete headers.Authorization;
          }
        }

        // 如果没有认证头但用户已登录，自动添加
        if (!headers.Authorization && userTokenManager.isAuthenticated()) {
          const userToken = userTokenManager.getToken();
          if (userToken) {
            headers.Authorization = `Bearer ${userToken}`;
            console.log('[AILF] 自动添加用户认证头:', headers.Authorization.substring(0, 20) + '...');
          }
        }

        const response = await axios({
          method: api.method || 'get',
          url: api.url,
          data: api.data,
          headers: headers
        });

        // 检查是否是登录API的响应
        if (api.url && api.url.includes('/login') && response.data && response.data.code === 200) {
          const loginData = response.data.data;
          console.log('[AILF] 检测到登录成功响应:', loginData);

          if (loginData.access_token) {
            console.log('[AILF] 保存登录token:', loginData.access_token);

            // 使用新的用户token管理器
            userTokenManager.setToken({
              access_token: loginData.access_token,
              refresh_token: loginData.refresh_token,
              token_type: loginData.token_type || 'bearer',
              expires_in: loginData.expires_in || 3600,
              user: loginData.user,
              permissions: loginData.permissions || { apis: [], features: [] }
            });

            // 登录成功，不在这里处理待处理命令
            // 待处理命令由 useEffect 监听 authState.isAuthenticated 变化统一处理
            console.log('[AILF] 登录成功，等待 useEffect 处理待处理命令');
            
            // 检查是否有待处理的命令
            const pendingCommand = localStorage.getItem('pendingCommand');
            
            if (!pendingCommand) {
              // 没有待处理命令，返回主界面并提示
              setTimeout(() => {
                setAmisSchema(null);
                speak('登录成功！请告诉我您需要什么功能。');
              }, 1000);
            } else {
              // 🔥 有待处理命令，关闭登录界面，等待 useEffect 处理
              // 不要在这里说话，让 useEffect 统一处理语音提示
              setTimeout(() => {
                setAmisSchema(null);
              }, 500);
            }
          }
        }

        // 🔥 检查是否是 workflow/state API 的响应（返回新的 AMIS schema）
        if (api.url?.includes('/workflow/state') && response.data) {
          console.log('[AILF] 检测到 workflow/state 响应:', response.data);
          
          // workflow/state 返回格式: { status: 0, msg: "success", data: { type: "page", ... } }
          const newSchema = response.data.data;
          if (newSchema && newSchema.type === 'page') {
            console.log('[AILF] 工作流返回新界面，更新 schema');
            // 延迟更新，让当前表单提交完成
            setTimeout(() => {
              setAmisKey(prev => prev + 1);
              setAmisSchema(newSchema);
              speak('已进入下一步');
            }, 300);
            
            // 🔥 返回特殊响应，告诉 AMIS 不要显示成功提示（我们自己处理）
            return {
              status: 0,
              msg: '',  // 空消息，避免 AMIS 显示默认成功提示
              data: { __workflow_handled: true }  // 标记已处理
            };
          } else if (response.data.msg === '工作流已完成') {
            console.log('[AILF] 工作流已完成');
            setTimeout(() => {
              setAmisSchema(null);
              speak('工作流已完成！');
            }, 500);
            
            return {
              status: 0,
              msg: '工作流已完成',
              data: { __workflow_handled: true }
            };
          }
        }

        // 检查是否是工作流步骤完成的API响应（排除登录/注册/认证/命令/workflow相关API）
        const isExcludedApi = api.url?.includes('/login') || 
                              api.url?.includes('/register') || 
                              api.url?.includes('/auth') ||
                              api.url?.includes('/refresh-token') ||
                              api.url?.includes('/command') ||
                              api.url?.includes('/workflow/state');  // 排除 workflow/state，已单独处理
        if (response.data && response.data.code === 200 &&
            (api.url?.includes('/api/') && api.method?.toLowerCase() === 'post') &&
            !isExcludedApi) {
          console.log('[AILF] 检测到API操作成功，检查是否需要自动推进工作流');

          // 延迟一下让当前操作完成，然后检查是否需要自动推进
          setTimeout(async () => {
            try {
              // 调用后端检查是否有活跃的工作流会话需要推进
              const progressHeaders: Record<string, string> = {
                'Content-Type': 'application/json'
              };
              const token = userTokenManager.getToken();
              if (token) {
                progressHeaders['Authorization'] = `Bearer ${token}`;
              }

              const progressResult = await submitAsyncCommand('继续下一步', {
                auto_progress: true,
                step_completed: true,
                user_id: userTokenManager.getUserInfo()?.id || 'anonymous'
              }, progressHeaders);

              if (progressResult?.schema) {
                console.log('[AILF] 工作流自动推进成功，更新界面');
                setAmisKey(prev => prev + 1);
                setAmisSchema(progressResult.schema);

                // 语音反馈
                if (progressResult.responseText) {
                  speak(progressResult.responseText);
                }
              }
            } catch (error) {
              console.log('[AILF] 工作流自动推进检查失败或无需推进:', error);
              // 这是正常情况，不是所有API调用都需要推进工作流
            }
          }, 1000);
        }

        // AMIS expects `status: 0` for success. Our backend often returns `{code: 200, ...}`,
        // so normalize here to avoid "success but UI doesn't update" issues.
        const payload = response.data;
        let status = 0;
        let msg = response.statusText;
        if (payload && typeof payload === 'object') {
          const payloadStatus =
            payload.status != null && !Number.isNaN(Number(payload.status))
              ? Number(payload.status)
              : null;
          const payloadCode =
            payload.code != null && !Number.isNaN(Number(payload.code))
              ? Number(payload.code)
              : null;

          if (payloadStatus != null) {
            // 兼容 AMIS(status=0 成功) 与后端 code 风格(2xx 成功)
            status = payloadStatus === 0 || (payloadStatus >= 200 && payloadStatus < 300) ? 0 : payloadStatus;
          } else if (payloadCode != null) {
            status = payloadCode >= 200 && payloadCode < 300 ? 0 : payloadCode;
          }
          msg = payload.msg || payload.message || msg;
        }
        return { status, msg, data: payload };
      } catch (error: any) {
        console.error('[AILF] Amis fetcher error:', error);
        // 返回错误响应，包含错误信息供 AMIS 显示
        const errorData = error.response?.data || {
          code: error.response?.status || 500,
          message: error.response?.data?.detail || error.message || '请求失败',
          data: null
        };
        return {
          status: error.response?.status || 500,
          msg: errorData.message || error.message,
          data: errorData
        };
      }
    },
    copy: (text: string) => {
      copy(text);
      console.log('已复制到剪贴板');
    },
    notify: (type: string, msg: string) => {
      console.log(`[AILF Notify] ${type}: ${msg}`);

      const text = String(msg || '');
      const hasSuccessHint = /(成功|完成|已完成|ok|succeed|created|updated|deleted)/i.test(text);
      const hasErrorHint = /(失败|错误|异常|不存在|无效|拒绝|forbidden|unauthorized|error|fail|invalid)/i.test(text);

      let level: 'success' | 'warning' | 'error';
      if (type === 'warning') level = 'warning';
      else if (type === 'success' || type === 'info') level = 'success';
      else level = 'error';

      // 某些接口返回 201 时，AMIS 可能传 error；若文案明确成功则强制按成功提示
      if (hasSuccessHint && !hasErrorHint) {
        level = 'success';
      }

      // 创建通知元素
      const notification = document.createElement('div');
      const bgColor = level === 'success'
        ? 'rgba(52, 199, 89, 0.95)'
        : level === 'warning'
          ? 'rgba(255, 149, 0, 0.95)'
          : 'rgba(255, 59, 48, 0.95)';
      const icon = level === 'success' ? '✓' : level === 'warning' ? '!' : '✕';
      
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        font-size: 14px;
        z-index: 10000;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        max-width: 400px;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideIn 0.3s ease-out;
      `;
      
      notification.innerHTML = `
        <span style="font-size: 18px; font-weight: bold;">${icon}</span>
        <span>${msg}</span>
      `;
      
      // 添加动画样式
      const style = document.createElement('style');
      style.textContent = `
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
          from { transform: translateX(0); opacity: 1; }
          to { transform: translateX(100%); opacity: 0; }
        }
      `;
      document.head.appendChild(style);
      
      document.body.appendChild(notification);
      
      // 3秒后移除通知
      setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => {
          if (document.body.contains(notification)) {
            document.body.removeChild(notification);
          }
          if (document.head.contains(style)) {
            document.head.removeChild(style);
          }
        }, 300);
      }, 3000);
    }
  };

  // 检查用户是否已登录
  const isUserLoggedIn = useCallback(() => {
    return userTokenManager.isAuthenticated();
  }, []);

  // 添加处理状态防护
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastProcessedCommand, setLastProcessedCommand] = useState('');

  // 处理语音命令
  const handleVoiceCommand = useCallback(async (command: string) => {
    if (!command.trim()) return;

    // 防止在处理过程中重复触发
    if (isProcessing) {
      console.log('[AILF] 正在处理中，跳过命令:', command);
      return;
    }

    console.log('[AILF] 处理语音命令:', command);
    setIsProcessing(true);
    setLastProcessedCommand(command);
    setErrorText('');
    setResponseText('正在处理您的请求...');

    // 首先检查配置是否完成
    if (!canUseFeatures) {
      const errorMsg = '系统配置未完成，请先完成七步配置才能使用AI功能';
      setErrorText(errorMsg);
      speak(errorMsg);
      console.log('[AILF] 配置未完成，禁止使用功能');
      setIsProcessing(false);
      return;
    }

    // 检查用户登录状态
    const isLoggedIn = isUserLoggedIn();
    console.log('[AILF] 用户登录状态:', isLoggedIn);

    // 如果用户未登录，保存命令并显示登录界面
    if (!isLoggedIn) {
      console.log('[AILF] 用户未登录，保存命令并显示登录界面');
      localStorage.setItem('pendingCommand', command);
      localStorage.setItem('pendingCommandTime', Date.now().toString());

      // 调用后端获取登录界面
      await handleLoginRequired(command);
      return;
    }

    // 用户已登录且配置完成，正常处理命令
    await processAuthenticatedCommand(command);
  }, [isUserLoggedIn, canUseFeatures, speak]);

  // 处理需要登录的情况
  const handleLoginRequired = useCallback(async (command: string) => {
    try {
      const result = await submitAsyncCommand(command, {
        user_id: "anonymous_user",
        session_id: `session_${Date.now()}`,
        require_auth: true
      }, {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      });

      if (result?.schema) {
        console.log('[AILF] 收到登录界面响应:', result.raw);
        setAmisKey(prev => prev + 1);
        setAmisSchema(result.schema);
        setResponseText('');
        speak('请先登录以继续处理您的需求');
      } else {
        setErrorText('无法生成登录界面');
        speak('无法生成登录界面，请稍后重试');
      }
    } catch (error: any) {
      console.error('[AILF] 获取登录界面失败:', error);
      setErrorText('获取登录界面失败');
      speak('获取登录界面失败，请稍后重试');
    } finally {
      setIsProcessing(false);
    }
  }, [speak, submitAsyncCommand]);

  // 未登录状态下，点击“登录”按钮直接拉起登录界面
  const handleDirectLoginClick = useCallback(() => {
    if (isProcessing) {
      return;
    }
    setErrorText('');
    setResponseText('正在打开登录界面...');
    setIsProcessing(true);
    void handleLoginRequired('登录');
  }, [handleLoginRequired, isProcessing]);

  // 处理已认证用户的命令
  const processAuthenticatedCommand = useCallback(async (command: string) => {
    try {
      const headers: any = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };

      // 添加JWT token到请求头
      const token = userTokenManager.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // 获取用户信息
      const userInfo = userTokenManager.getUserInfo();
      let userId = "anonymous_user";
      if (userInfo) {
        userId = userInfo.id?.toString() || userInfo.username || "anonymous_user";
      }

      const result = await submitAsyncCommand(command, {
        user_id: userId,
        session_id: `session_${Date.now()}`,
        authenticated: true
      }, headers, 600000);

      const schema = result.schema;
      const responseText = result.responseText;

      if (schema) {
        console.log('[AILF] 收到异步API响应:', result.raw);
        setAmisKey(prev => prev + 1);
        setAmisSchema(schema);
        setResponseText('');

        // 语音反馈
        if (responseText) {
          speak(responseText);
        } else if (result.message) {
          speak(result.message);
        } else {
          speak('界面已生成完成');
        }
      } else {
        const errorMsg = result.message || '未能生成有效的界面配置';
        setErrorText(errorMsg);
        speak(errorMsg);
      }
    } catch (error: any) {
      console.error('[AILF] API调用失败:', error);
      let errorMessage = '抱歉，处理您的请求时出现了问题';

      if (error.code === 'ECONNREFUSED') {
        errorMessage = '无法连接到后端服务，请确保后端服务正在运行';
      } else if (error.response?.status === 404) {
        errorMessage = 'API端点不存在，请检查后端配置';
      } else if (error.response?.status >= 500) {
        errorMessage = '服务器内部错误，请稍后重试';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      setErrorText(errorMessage);
      setResponseText('');
      speak(errorMessage);
    } finally {
      // 确保处理状态被重置
      setIsProcessing(false);
    }
  }, [speak, submitAsyncCommand]);

  // 监听语音识别结果
  useEffect(() => {
    // 调试日志：监控状态变化
    if (transcript || !isListening) {
      console.log(`[AILF 状态监控] transcript="${transcript}", isListening=${isListening}, isProcessing=${isProcessing}`);
    }

    if (transcript && !isListening && !isProcessing) {
      console.log('[AILF] 检测到语音输入完成，自动提交命令');
      handleVoiceCommand(transcript);
      // 立即清除transcript，防止重复处理
      setTranscript('');
    }
  }, [transcript, isListening, isProcessing, handleVoiceCommand]);

  // 监听登录状态变化，登录成功后处理待处理的命令
  useEffect(() => {
    const checkPendingCommand = async () => {
      const isAuthenticated = userTokenManager.isAuthenticated();
      const pendingCommand = localStorage.getItem('pendingCommand');
      const pendingCommandTime = localStorage.getItem('pendingCommandTime');

      if (isAuthenticated && pendingCommand && pendingCommandTime) {
        // 检查命令是否过期（5分钟内有效）
        const commandTime = parseInt(pendingCommandTime);
        const now = Date.now();
        const fiveMinutes = 5 * 60 * 1000;

        if (now - commandTime < fiveMinutes) {
          console.log('[AILF] 检测到登录成功，处理待处理的命令:', pendingCommand);
          
          // 立即清除 localStorage，防止重复执行
          localStorage.removeItem('pendingCommand');
          localStorage.removeItem('pendingCommandTime');
          
          // 🔥 语音提示正在处理
          speak(`登录成功！正在处理您的请求：${pendingCommand}`);
          
          // 延迟一下确保登录状态完全更新
          setTimeout(() => {
            processAuthenticatedCommand(pendingCommand);
          }, 1000);
        } else {
          // 命令已过期，清除
          localStorage.removeItem('pendingCommand');
          localStorage.removeItem('pendingCommandTime');
          console.log('[AILF] 待处理命令已过期，已清除');
        }
      }
    };

    checkPendingCommand();
  }, [authState.isAuthenticated, processAuthenticatedCommand]);

  // 诊断连接函数
  const handleDiagnoseConnection = useCallback(async () => {
    const diagnosticNotification = document.createElement('div');
    diagnosticNotification.style.cssText = `
      position: fixed;
      top: 20px;
      left: 20px;
      background: rgba(255, 149, 0, 0.95);
      color: white;
      padding: 20px;
      border-radius: 12px;
      font-size: 14px;
      z-index: 1000;
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      max-width: 420px;
      min-width: 320px;
    `;

    document.body.appendChild(diagnosticNotification);
    const healthEndpoint = `${AILF_CONFIG.apiBaseUrl}/health`;

    diagnosticNotification.innerHTML = `
      <div style="font-weight: 600; margin-bottom: 12px;">🔍 连接诊断</div>
      <div style="font-size: 12px; line-height: 1.6;">正在检查健康接口 ${healthEndpoint} ...</div>
    `;

    try {
      const start = performance.now();
      const response = await fetch(healthEndpoint, {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });
      const elapsed = Math.round(performance.now() - start);

      let detailText = `${response.status} ${response.statusText} · ${elapsed}ms`;
      try {
        const payload = await response.json();
        const msg = payload?.message || payload?.msg;
        if (msg) detailText = `${detailText} · ${msg}`;
      } catch {
        // 非 JSON 响应无需额外处理
      }

      const ok = response.ok;
      diagnosticNotification.style.background = ok ? 'rgba(52, 199, 89, 0.95)' : 'rgba(255, 59, 48, 0.95)';
      diagnosticNotification.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 12px;">🔍 连接诊断</div>
        <div style="font-size: 12px; line-height: 1.6;">
          <div>health 接口: ${ok ? '✅ 正常' : '❌ 异常'}</div>
          <div style="opacity: 0.85; margin-top: 6px;">${detailText}</div>
        </div>
      `;
    } catch (error: any) {
      diagnosticNotification.style.background = 'rgba(255, 59, 48, 0.95)';
      diagnosticNotification.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 12px;">🔍 连接诊断</div>
        <div style="font-size: 12px; line-height: 1.6;">
          <div>health 接口: ❌ 无法连接</div>
          <div style="opacity: 0.85; margin-top: 6px;">${error?.message || '未知错误'}</div>
        </div>
      `;
    }

    // 8秒后移除通知
    setTimeout(() => {
      if (document.body.contains(diagnosticNotification)) {
        document.body.removeChild(diagnosticNotification);
      }
    }, 8000);
  }, []);

  // 切换语音监听状态
  const toggleListening = useCallback(() => {
    // 检查配置是否完成
    if (!canUseFeatures) {
      const errorMsg = '系统配置未完成，请先完成七步配置才能使用语音功能';
      setErrorText(errorMsg);
      speak(errorMsg);
      return;
    }

    if (isListening) {
      stopListening();
    } else {
      // 每次开始录音前，强制重置处理状态，防止卡死
      setIsProcessing(false);
      setErrorText('');
      setResponseText('');
      startListening();
    }
  }, [isListening, startListening, stopListening, canUseFeatures, speak]);

  // 手动发送当前转录内容
  const handleManualSend = useCallback(() => {
    if (transcript && !isProcessing) {
      handleVoiceCommand(transcript);
      setTranscript('');
    }
  }, [transcript, isProcessing, handleVoiceCommand, setTranscript]);

  const handleMenuCommandSend = useCallback(() => {
    const trimmed = menuCommand.trim();
    if (!trimmed || isProcessing) return;
    handleVoiceCommand(trimmed);
    setMenuCommand('');
    setIsCommandModalOpen(false);
  }, [menuCommand, isProcessing, handleVoiceCommand]);

  useEffect(() => {
    if (isCommandModalOpen && menuInputRef.current) {
      menuInputRef.current.focus();
    }
  }, [isCommandModalOpen]);

  // 关闭生成的界面
  const closeGeneratedInterface = useCallback(() => {
    setAmisSchema(null);
    setResponseText('');
    setErrorText('');
  }, []);

  // 如果配置状态正在加载，显示加载状态
  if (configLoading) {
    return (
      <div className="App main-page">
        <div className="siri-container">
          <div className="app-name">AILF</div>
          <div className="response-area">
            <div className="placeholder-text">正在检查系统配置...</div>
          </div>
        </div>
      </div>
    );
  }

  // 如果后端服务未启动，显示苹果风格提示
  if (!isBackendAvailable) {
    return (
      <div className="App main-page">
        <div className="siri-container">
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '80vh',
            gap: 24
          }}>
            {/* SF Symbol 风格图标 */}
            <svg width="88" height="88" viewBox="0 0 88 88" fill="none" style={{ opacity: 0.95 }}>
              <circle cx="44" cy="44" r="42" stroke="url(#warnGradient)" strokeWidth="3" fill="none" />
              <rect x="41" y="22" width="6" height="28" rx="3" fill="url(#warnGradient)" />
              <circle cx="44" cy="62" r="4" fill="url(#warnGradient)" />
              <defs>
                <linearGradient id="warnGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ff9500" />
                  <stop offset="100%" stopColor="#ff3b30" />
                </linearGradient>
              </defs>
            </svg>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12
            }}>
              <span style={{
                color: 'rgba(255, 255, 255, 0.9)',
                fontSize: 28,
                fontWeight: 600,
                fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif'
              }}>无法连接</span>
              <span style={{
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: 18,
                fontWeight: 400,
                fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif'
              }}>后端服务未启动</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 如果配置未完成，显示配置警告
  if (!canUseFeatures && configStatus) {
    return (
      <div className="App main-page">
        <div className="siri-container">
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '60vh',
            padding: '20px'
          }}>
            <ConfigurationIncompleteWarning
              status={configStatus}
              size="large"
              showDetails={true}
            />
          </div>
        </div>
      </div>
    );
  }

  // 如果系统未配置，显示配置提示（保留原有逻辑作为fallback）
  if (false) {
    return null;
  }

  const bgClassName = appConfig.backgroundStyle === 'ribbon' ? 'App main-page ribbon-bg-style' : 'App main-page';

  return (
    <div className={bgClassName}>
      {appConfig.backgroundStyle === 'ribbon' && <AppleRibbonBackground />}
      <UserStatusIndicator onLoginClick={handleDirectLoginClick} />
      <div className="siri-container">
        <div className="header-section">
          <div className="app-name">{appConfig.title}</div>
        </div>

        <div className="response-area">
          {errorText && <div className="error-message">{errorText}</div>}

          {responseText && <div className="ai-response">{responseText}</div>}

          {transcript && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
              <div className="user-transcript">"{transcript}"</div>
              {!isListening && !isProcessing && transcript.trim() && (
                <button
                  onClick={handleManualSend}
                  style={{
                    padding: '6px 16px',
                    borderRadius: '20px',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    background: 'rgba(0, 122, 255, 0.6)',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '14px',
                    backdropFilter: 'blur(10px)',
                    animation: 'fadeInUp 0.3s ease-out'
                  }}
                >
                  发送命令
                </button>
              )}
            </div>
          )}

          {!responseText && !transcript && !errorText && (
            <div className="placeholder-text">
              {isModelLoading ? (
                <>
                  正在加载语音识别模型...<br />
                  <div style={{
                    marginTop: '15px',
                    width: '200px',
                    height: '4px',
                    background: 'rgba(255,255,255,0.2)',
                    borderRadius: '2px',
                    overflow: 'hidden',
                    margin: '15px auto 10px'
                  }}>
                    <div style={{
                      width: `${modelLoadProgress}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #4cd964, #5ac8fa)',
                      borderRadius: '2px',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <span style={{ fontSize: '0.9rem', opacity: 0.7 }}>{modelLoadProgress}% (首次下载约40MB)</span>
                </>
              ) : (
                <>
                  {appConfig.subtitle}<br />
                  点击麦克风，告诉我您需要什么界面
                  <div style={{ fontSize: '0.8rem', opacity: 0.5, marginTop: '10px' }}>
                    {recognitionMode === 'local' ? '🔒 本地识别模式' : '🌐 在线识别模式'}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="mic-button-container">
          <SiriOrb
            isListening={isListening}
            isLoading={isModelLoading}
            disabled={isModelLoading}
            volume={volume}
            onClick={toggleListening}
          />
        </div>
      </div>

      {/* 右下角隐蔽开发者菜单 */}
      <div className="dev-menu-container">
        <button className="dev-menu-button" aria-label="开发者菜单">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
          </svg>
        </button>
        <div className="dev-menu-dropdown">
          <button
            className="dev-menu-item"
            onClick={() => navigate('/config')}
          >
            开发者配置
          </button>

          <button
            className="dev-menu-item"
            onClick={() => navigate('/about')}
          >
            关于
          </button>

          <button
            className="dev-menu-item"
            onClick={handleDiagnoseConnection}
          >
            🔍 诊断连接
          </button>

          <div className="dev-menu-divider" />
          <button
            className="dev-menu-item dev-menu-toggle"
            onClick={() => setIsCommandModalOpen(true)}
          >
            输入语音指令
          </button>
        </div>
      </div>

      {isCommandModalOpen && (
        <div
          className="global-command-overlay"
          onClick={() => setIsCommandModalOpen(false)}
        >
          <div
            className="global-command-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="global-command-header">
              <span>输入语音指令</span>
              <button
                className="global-command-close"
                onClick={() => setIsCommandModalOpen(false)}
                aria-label="关闭"
              >
                ×
              </button>
            </div>
            <div className="global-command-body">
              <input
                ref={menuInputRef}
                className="global-command-input"
                placeholder="输入文本指令（如：我要买票）"
                value={menuCommand}
                onChange={(e) => setMenuCommand(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleMenuCommandSend();
                  }
                  if (e.key === 'Escape') {
                    e.preventDefault();
                    setIsCommandModalOpen(false);
                  }
                }}
              />
              <div className="global-command-actions">
                <button
                  className="global-command-cancel"
                  onClick={() => setIsCommandModalOpen(false)}
                >
                  取消
                </button>
                <button
                  className="global-command-send"
                  onClick={handleMenuCommandSend}
                  disabled={!menuCommand.trim() || isProcessing}
                >
                  发送
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* 生成的界面 */}
      <GeneratedInterface
        schema={amisSchema}
        amisKey={amisKey}
        amisEnv={amisEnv}
        onClose={closeGeneratedInterface}
        onToggleListening={toggleListening}
        isListening={isListening}
      />
    </div>
  );
};

export default MainPage;
