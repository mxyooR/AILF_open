/**
 * AILF Main Page - 主页面组件
 * 遵循单一文件规则，包含原有的主界面逻辑
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';
import '../styles/apple-style.css';
import axios from 'axios';
import { buildAmisRequest, canApplyWorkflowResponse, canSendUserToken, normalizeAmisResponse, toAmisFetcherResponse } from '../services/common/amisTransport';
import { runAsyncCommand, AsyncCommandResult } from '../services/common/asyncCommand';
// 移除amis相关导入，使用原生通知
import copy from 'copy-to-clipboard';
import GeneratedInterface from '../components/GeneratedInterface';
import SiriOrb from '../components/SiriOrb';
import ConfigurationIncompleteWarning from '../components/common/ConfigurationIncompleteWarning';
import UserStatusIndicator from '../components/user/UserStatusIndicator';
import { useLocalVoice } from '../hooks/useLocalVoice';
import { useCommandRequest } from '../hooks/useCommandRequest';
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
  const latestSchemaRef = useRef<any>(amisSchema);
  latestSchemaRef.current = amisSchema;
  const [amisKey, setAmisKey] = useState(0);
  const [responseText, setResponseText] = useState('');
  const [errorText, setErrorText] = useState('');
  const [menuCommand, setMenuCommand] = useState('');
  const [isCommandModalOpen, setIsCommandModalOpen] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuInputRef = useRef<HTMLInputElement | null>(null);

  const [appConfig, setAppConfig] = useState<AppConfig>({ title: 'AILF', subtitle: '开发者配置面板', backgroundStyle: 'mesh' });

  // 语音相关状态 - 混合模式：优先 Web Speech API，失败时切换到本地 Whisper
  const {
    isListening,
    isTranscribing,
    transcript,
    isSpeaking,
    volume,
    isModelLoading,
    modelLoadProgress,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
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

  const submitAsyncCommand = useCallback((
    command: string,
    context: Record<string, any>,
    headers: Record<string, string> = {},
    timeoutMs = 600000,
    signal?: AbortSignal
  ): Promise<AsyncCommandResult> => runAsyncCommand(command, context, headers, {
    baseURL: AILF_CONFIG.apiBaseUrl, timeoutMs, signal
  }), []);

  // Amis 环境配置
  const amisEnv = {
    fetcher: async (api: any) => {
      try {
        // 处理认证头
        let headers = { ...api.headers };

        // 处理 amis 本地存储语法 ${ls:access_token}
        if (headers.Authorization && headers.Authorization.includes('${ls:access_token}')) {
          const userToken = userTokenManager.getToken();
          if (userToken && canSendUserToken(api.url)) {
            headers.Authorization = `Bearer ${userToken}`;
          } else {
            console.log('[AILF] 警告：需要认证但用户未登录');
            delete headers.Authorization;
          }
        }

        // 如果没有认证头但用户已登录，自动添加
        if (canSendUserToken(api.url) && !headers.Authorization && userTokenManager.isAuthenticated()) {
          const userToken = userTokenManager.getToken();
          if (userToken) {
            headers.Authorization = `Bearer ${userToken}`;
          }
        }

        const submittedSchema = amisSchema;
        const submittedUserId = userTokenManager.getUserInfo()?.id;
        const response = await axios(buildAmisRequest(api, headers));
        // 关闭页面或切换账号后，旧表单的登录/业务响应不再改变当前会话。
        if (latestSchemaRef.current !== submittedSchema || submittedUserId !== userTokenManager.getUserInfo()?.id) {
          return toAmisFetcherResponse({ status: 1, msg: '界面或登录状态已更新，请使用当前表单', data: null });
        }
        // 下载接口需要原始 Blob 和 Content-Disposition，不能包装成普通 JSON。
        if (api.responseType === 'blob' || api.config?.responseType === 'blob') return response;
        const normalized = normalizeAmisResponse(response.data, response.statusText);

        // 检查是否是登录API的响应
        if (api.url && api.url.includes('/login') && response.data && response.data.code === 200) {
          const loginData = response.data.data;

          if (loginData.access_token) {

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
                if (latestSchemaRef.current !== submittedSchema) return;
                setAmisSchema(null);
                speak('登录成功！请告诉我您需要什么功能。');
              }, 1000);
            } else {
              // 🔥 有待处理命令，关闭登录界面，等待 useEffect 处理
              // 不要在这里说话，让 useEffect 统一处理语音提示
              setTimeout(() => {
                if (latestSchemaRef.current !== submittedSchema) return;
                setAmisSchema(null);
              }, 500);
            }
          }
        }

        // 🔥 检查是否是 workflow/state API 的响应（返回新的 AMIS schema）
        if (api.url?.includes('/workflow/state') && response.data) {
          // 错误页也有 type=page，必须先检查业务状态，再决定是否替换表单。
          if (normalized.status !== 0) return toAmisFetcherResponse(response.data);
          const canApply = () => canApplyWorkflowResponse(submittedSchema, latestSchemaRef.current, api.data);
          if (!canApply()) return toAmisFetcherResponse({ status: 1, msg: '界面已更新，请使用当前表单', data: null });
          
          // workflow/state 返回格式: { status: 0, msg: "success", data: { type: "page", ... } }
          const newSchema = response.data.data;
          if (newSchema && newSchema.type === 'page') {
            console.log('[AILF] 工作流返回新界面，更新 schema');
            // 延迟更新，让当前表单提交完成
            setTimeout(() => {
              if (!canApply()) return;
              setAmisKey(prev => prev + 1);
              setAmisSchema(newSchema);
              speak(response.data.msg === '工作流已完成' ? '工作流已完成！' : '已进入下一步');
            }, 300);
            
            // 🔥 返回特殊响应，告诉 AMIS 不要显示成功提示（我们自己处理）
            return toAmisFetcherResponse({
              status: 0,
              msg: '',
              data: { __workflow_handled: true }
            });
          } else if (response.data.msg === '工作流已完成') {
            console.log('[AILF] 工作流已完成');
            setTimeout(() => {
              if (!canApply()) return;
              setAmisSchema(null);
              speak('工作流已完成！');
            }, 500);
            
            return toAmisFetcherResponse({
              status: 0,
              msg: '工作流已完成',
              data: { __workflow_handled: true }
            });
          }
        }

        // 工作流表单由 /workflow/state 校验实例并推进；独立 API 成功只反馈本次操作。

        // AMIS expects `status: 0` for success. Our backend often returns `{code: 200, ...}`,
        // so normalize here to avoid "success but UI doesn't update" issues.
        return toAmisFetcherResponse(response.data, response.statusText);
      } catch (error: any) {
        console.error('[AILF] Amis 请求失败，HTTP 状态:', error.response?.status);
        // 返回错误响应，包含错误信息供 AMIS 显示
        const errorData = error.response?.data || {
          code: error.response?.status || 500,
          message: error.response?.data?.detail || error.message || '请求失败',
          data: null
        };
        return toAmisFetcherResponse({
          status: error.response?.status || 500,
          msg: errorData.message || errorData.msg || errorData.detail || error.message,
          data: errorData
        });
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
      
      // 接口消息可能带有用户输入，用文本节点显示，不能把消息当 HTML 执行。
      const iconElement = document.createElement('span');
      iconElement.style.cssText = 'font-size: 18px; font-weight: bold;';
      iconElement.textContent = icon;
      const messageElement = document.createElement('span');
      messageElement.textContent = String(msg || '');
      notification.append(iconElement, messageElement);
      
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

  // 指令用同步锁防重；取消后忽略迟到结果，不能靠录音按钮重置运行状态。
  const { isProcessing, beginRequest, isCurrentRequest, finishRequest, cancelRequest } = useCommandRequest();

  const processCommand = useCallback(async (command: string, authenticated: boolean) => {
    const request = beginRequest();
    if (!request) return;
    const userId = authenticated ? userTokenManager.getUserInfo()?.id : null;
    const canApply = () => isCurrentRequest(request) &&
      (!authenticated || (userTokenManager.isAuthenticated() && userTokenManager.getUserInfo()?.id === userId));
    setErrorText('');
    setResponseText(authenticated ? '正在处理您的请求...' : '正在打开登录界面...');
    latestSchemaRef.current = null;
    setAmisSchema(null);
    try {
      const token = authenticated ? userTokenManager.getToken() : null;
      const result = await submitAsyncCommand(command, {
        user_id: authenticated ? String(userId ?? 'anonymous_user') : 'anonymous_user',
        session_id: `session_${Date.now()}`,
        ...(authenticated ? { authenticated: true } : { require_auth: true })
      }, {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      }, 600000, request.controller.signal);
      if (!canApply()) return;
      setResponseText('');
      if (result.schema) {
        latestSchemaRef.current = result.schema;
        setAmisKey(prev => prev + 1);
        setAmisSchema(result.schema);
        speak(authenticated
          ? result.responseText || result.message || '界面已生成完成'
          : '请先登录以继续处理您的需求');
      } else {
        const message = result.message || '未能生成有效的界面配置';
        setErrorText(message);
        speak(message);
      }
    } catch (error: any) {
      if (!canApply()) return;
      const message = error instanceof Error ? error.message : '处理请求失败，请稍后重试';
      setErrorText(message);
      setResponseText('');
      speak(message);
    } finally {
      finishRequest(request);
    }
  }, [beginRequest, isCurrentRequest, finishRequest, speak, submitAsyncCommand]);

  const processAuthenticatedCommand = useCallback((command: string) =>
    processCommand(command, true), [processCommand]);

  const handleVoiceCommand = useCallback(async (command: string) => {
    const trimmed = command.trim();
    if (!trimmed || isProcessing) return;
    if (!canUseFeatures) {
      const message = '系统配置未完成，请先完成七步配置才能使用AI功能';
      setErrorText(message);
      speak(message);
      return;
    }
    const authenticated = isUserLoggedIn();
    if (!authenticated) {
      localStorage.setItem('pendingCommand', trimmed);
      localStorage.setItem('pendingCommandTime', String(Date.now()));
    }
    await processCommand(trimmed, authenticated);
  }, [isProcessing, canUseFeatures, isUserLoggedIn, processCommand, speak]);

  const handleDirectLoginClick = useCallback(() => {
    void processCommand('登录', false);
  }, [processCommand]);

  // 监听语音识别结果
  useEffect(() => {
    // 调试日志：监控状态变化
    if (transcript || !isListening) {
      console.log(`[AILF 状态监控] transcript="${transcript}", isListening=${isListening}, isProcessing=${isProcessing}`);
    }

    if (transcript && !isListening && !isTranscribing && !isProcessing) {
      console.log('[AILF] 检测到语音输入完成，自动提交命令');
      handleVoiceCommand(transcript);
      // 立即清除transcript，防止重复处理
      setTranscript('');
    }
  }, [transcript, isListening, isTranscribing, isProcessing, handleVoiceCommand]);

  // 登录完成后立即接续一次命令；请求锁同步生效，避免定时回调与手动输入并发。
  useEffect(() => {
    if (!authState.isAuthenticated || isProcessing) return;
    const command = localStorage.getItem('pendingCommand');
    const savedAt = Number(localStorage.getItem('pendingCommandTime'));
    if (!command) return;
    localStorage.removeItem('pendingCommand');
    localStorage.removeItem('pendingCommandTime');
    const age = Date.now() - savedAt;
    if (Number.isFinite(savedAt) && savedAt > 0 && age >= 0 && age < 5 * 60 * 1000) {
      void processAuthenticatedCommand(command);
    }
  }, [authState.isAuthenticated, isProcessing, processAuthenticatedCommand]);

  // 登出或切换账号后清掉旧界面，不能显示上个用户的业务数据。
  const previousUserId = useRef(authState.user?.id);
  useEffect(() => {
    const currentUserId = authState.user?.id;
    if (previousUserId.current != null && previousUserId.current !== currentUserId) {
      cancelRequest();
      latestSchemaRef.current = null;
      setAmisSchema(null);
      setResponseText('');
      setErrorText('');
      localStorage.removeItem('pendingCommand');
      localStorage.removeItem('pendingCommandTime');
    }
    previousUserId.current = currentUserId;
  }, [authState.user?.id, cancelRequest]);

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
      white-space: pre-line;
    `;

    document.body.appendChild(diagnosticNotification);
    const healthEndpoint = `${AILF_CONFIG.apiBaseUrl}/health`;

    diagnosticNotification.textContent = `🔍 连接诊断\n正在检查健康接口 ${healthEndpoint} ...`;

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
      // 健康接口消息也按文本显示，不能执行接口返回的 HTML。
      diagnosticNotification.textContent = `🔍 连接诊断\nhealth 接口: ${ok ? '✅ 正常' : '❌ 异常'}\n${detailText}`;
    } catch (error: any) {
      diagnosticNotification.style.background = 'rgba(255, 59, 48, 0.95)';
      diagnosticNotification.textContent = `🔍 连接诊断\nhealth 接口: ❌ 无法连接\n${error?.message || '未知错误'}`;
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
      if (isProcessing) return;
      setErrorText('');
      setResponseText('');
      startListening();
    }
  }, [isListening, isProcessing, startListening, stopListening, canUseFeatures, speak]);

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
    cancelRequest();
    stopListening();
    stopSpeaking();
    latestSchemaRef.current = null;
    localStorage.removeItem('pendingCommand');
    localStorage.removeItem('pendingCommandTime');
    setAmisSchema(null);
    setResponseText('');
    setErrorText('');
  }, [cancelRequest, stopListening, stopSpeaking]);

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
              <button type="button" onClick={() => navigate('/demo')} style={{ marginTop: 12, padding: '12px 24px', borderRadius: 8, border: '1px solid rgba(255,255,255,.3)', background: 'rgba(255,255,255,.1)', color: '#fff', cursor: 'pointer' }}>体验开源演示 →</button>
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
          {isProcessing && <button type="button" onClick={closeGeneratedInterface}>取消请求</button>}

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
            isLoading={isModelLoading || isProcessing || isTranscribing}
            disabled={isModelLoading || isProcessing || isTranscribing}
            volume={volume}
            onClick={toggleListening}
          />
        </div>
      </div>

      {/* 右下角隐蔽开发者菜单 */}
      <div className={`dev-menu-container ${isMenuOpen ? 'is-open' : ''}`} onKeyDown={event => {
        if (event.key === 'Escape') setIsMenuOpen(false);
      }}>
        <button type="button" className="dev-menu-button" aria-label="开发者菜单"
          aria-expanded={isMenuOpen} aria-controls="main-developer-menu"
          onClick={() => setIsMenuOpen(previous => !previous)}>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
          </svg>
        </button>
        <div className="dev-menu-dropdown" id="main-developer-menu">
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
            onClick={() => { setIsMenuOpen(false); setIsCommandModalOpen(true); }}
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
