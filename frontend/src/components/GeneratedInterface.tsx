import React, { useEffect, useMemo, useRef, useState } from 'react';
import { render as renderAmis } from 'amis';
import SiriOrb from './SiriOrb';
import { userTokenManager } from '../services/common/userTokenManager';
import '../styles/generated-interface.css';

interface GeneratedInterfaceProps {
  schema: any;
  amisKey: number;
  amisEnv: any;
  onClose: () => void;
  onToggleListening: () => void;
  isListening: boolean;
}

const GeneratedInterface: React.FC<GeneratedInterfaceProps> = ({
  schema,
  amisKey,
  amisEnv,
  onClose,
  onToggleListening,
  isListening
}) => {
  // 🔥 使用延迟渲染来避免 mobx-state-tree 的状态冲突
  const [shouldRender, setShouldRender] = useState(false);
  const [currentSchema, setCurrentSchema] = useState<any>(null);
  const [currentKey, setCurrentKey] = useState(0);
  const renderAreaRef = useRef<HTMLDivElement>(null);
  const blobUrlCacheRef = useRef<Map<string, string>>(new Map());
  const inflightFetchRef = useRef<Map<string, Promise<string | null>>>(new Map());

  const revokeAllBlobUrls = () => {
    blobUrlCacheRef.current.forEach((blobUrl) => {
      URL.revokeObjectURL(blobUrl);
    });
    blobUrlCacheRef.current.clear();
    inflightFetchRef.current.clear();
  };

  const normalizeProtectedMediaUrl = (rawUrl?: string | null): string | null => {
    if (!rawUrl) return null;
    const trimmed = rawUrl.trim();
    if (!trimmed) return null;
    if (
      trimmed.startsWith('blob:') ||
      trimmed.startsWith('data:') ||
      trimmed.startsWith('javascript:') ||
      trimmed.startsWith('#') ||
      trimmed.includes('${')
    ) {
      return null;
    }

    try {
      const url = new URL(trimmed, window.location.origin);
      const isApiPath = url.pathname.startsWith('/api/');
      const localHosts = new Set([
        window.location.host,
        'localhost:3000',
        '127.0.0.1:3000',
        'localhost:5000',
        '127.0.0.1:5000'
      ]);
      if (!isApiPath || !localHosts.has(url.host)) return null;
      return url.toString();
    } catch (_error) {
      return null;
    }
  };

  const fetchBlobUrlWithToken = async (url: string): Promise<string | null> => {
    const cached = blobUrlCacheRef.current.get(url);
    if (cached) return cached;

    const inflight = inflightFetchRef.current.get(url);
    if (inflight) return inflight;

    const request = (async () => {
      try {
        const token = userTokenManager.getToken();
        const headers: Record<string, string> = {};
        if (token) headers.Authorization = `Bearer ${token}`;

        const resp = await fetch(url, { method: 'GET', headers });
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`);
        }

        const blob = await resp.blob();
        const blobUrl = URL.createObjectURL(blob);
        blobUrlCacheRef.current.set(url, blobUrl);
        return blobUrl;
      } catch (error) {
        console.warn('[AILF] Failed to fetch media with token:', url, error);
        return null;
      } finally {
        inflightFetchRef.current.delete(url);
      }
    })();

    inflightFetchRef.current.set(url, request);
    return request;
  };

  const replaceMediaUrlIfNeeded = async (
    element: Element,
    attrName: 'src' | 'data' | 'href',
    markerKey: string
  ) => {
    const htmlElement = element as HTMLElement;
    const datasetKey = `authOriginal${markerKey}`;
    const fromDataset = (htmlElement.dataset as Record<string, string | undefined>)[datasetKey];
    const currentAttr = element.getAttribute(attrName);
    const origin = fromDataset || currentAttr;
    const normalizedUrl = normalizeProtectedMediaUrl(origin);
    if (!normalizedUrl) return;

    if (!fromDataset) {
      (htmlElement.dataset as Record<string, string>)[datasetKey] = origin || '';
    }

    const blobUrl = await fetchBlobUrlWithToken(normalizedUrl);
    if (!blobUrl) return;

    if (element.getAttribute(attrName) !== blobUrl) {
      element.setAttribute(attrName, blobUrl);
    }
  };

  // 管理 body 样式
  useEffect(() => {
    if (schema) {
      const originalBodyStyle = {
        background: document.body.style.background,
        animation: document.body.style.animation,
        className: document.body.className
      };

      document.body.style.background = '#ffffff';
      document.body.style.animation = 'none';
      document.body.className = 'generated-interface-body';

      return () => {
        document.body.style.background = originalBodyStyle.background;
        document.body.style.animation = originalBodyStyle.animation;
        document.body.className = originalBodyStyle.className;
      };
    }
  }, [schema]);

  // 🔥 延迟更新 schema，避免快速切换导致的状态冲突
  useEffect(() => {
    if (!schema) {
      setShouldRender(false);
      setCurrentSchema(null);
      return;
    }

    // 先隐藏，等待旧实例销毁
    setShouldRender(false);
    
    // 延迟渲染新的 schema
    const timer = setTimeout(() => {
      setCurrentSchema(schema);
      setCurrentKey(amisKey);
      setShouldRender(true);
    }, 100);

    return () => {
      clearTimeout(timer);
    };
  }, [schema, amisKey]);

  useEffect(() => {
    return () => {
      revokeAllBlobUrls();
    };
  }, [currentKey]);

  useEffect(() => {
    if (!shouldRender || !renderAreaRef.current) return;

    const container = renderAreaRef.current;
    let destroyed = false;

    const processMediaElements = () => {
      if (destroyed) return;

      const imageNodes = Array.from(container.querySelectorAll('img[src]'));
      const srcNodes = Array.from(
        container.querySelectorAll('audio[src], video[src], source[src], iframe[src], embed[src]')
      );
      const dataNodes = Array.from(container.querySelectorAll('object[data]'));
      const hrefNodes = Array.from(container.querySelectorAll('a[href]'));

      imageNodes.forEach((el) => void replaceMediaUrlIfNeeded(el, 'src', 'Src'));
      srcNodes.forEach((el) => void replaceMediaUrlIfNeeded(el, 'src', 'Src'));
      dataNodes.forEach((el) => void replaceMediaUrlIfNeeded(el, 'data', 'Data'));
      hrefNodes.forEach((el) => void replaceMediaUrlIfNeeded(el, 'href', 'Href'));
    };

    processMediaElements();

    const observer = new MutationObserver(() => {
      processMediaElements();
    });

    observer.observe(container, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['src', 'data', 'href']
    });

    return () => {
      destroyed = true;
      observer.disconnect();
    };
  }, [shouldRender, currentKey]);

  // 🔥 使用 useMemo 缓存 AMIS 渲染结果，避免不必要的重新渲染
  const amisContent = useMemo(() => {
    if (!shouldRender || !currentSchema) return null;
    
    try {
      return renderAmis(currentSchema, {
        locale: 'zh-CN',
        theme: 'antd'
      }, amisEnv);
    } catch (e) {
      console.error('[AILF] AMIS render error:', e);
      return <div style={{ color: 'red', padding: '20px' }}>界面渲染失败，请重试</div>;
    }
  }, [shouldRender, currentSchema, amisEnv]);

  if (!schema) return null;

  return (
    <>
      {/* 左上角关闭按钮 - 在 amis-render-area 外面 */}
      <button 
        onClick={onClose} 
        style={{
          position: 'fixed',
          top: '24px',
          left: '24px',
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          border: 'none',
          background: 'rgba(0, 0, 0, 0.06)',
          color: 'rgba(0, 0, 0, 0.5)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s ease',
          zIndex: 1002
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(0, 0, 0, 0.1)';
          e.currentTarget.style.color = 'rgba(0, 0, 0, 0.8)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(0, 0, 0, 0.06)';
          e.currentTarget.style.color = 'rgba(0, 0, 0, 0.5)';
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
          <path d="M13.3 0.7c-0.4-0.4-1-0.4-1.4 0L7 5.6 2.1 0.7c-0.4-0.4-1-0.4-1.4 0s-0.4 1 0 1.4L5.6 7l-4.9 4.9c-0.4 0.4-0.4 1 0 1.4 0.2 0.2 0.5 0.3 0.7 0.3s0.5-0.1 0.7-0.3L7 8.4l4.9 4.9c0.2 0.2 0.5 0.3 0.7 0.3s0.5-0.1 0.7-0.3c0.4-0.4 0.4-1 0-1.4L8.4 7l4.9-4.9c0.4-0.4 0.4-1 0-1.4z"/>
        </svg>
      </button>

      {/* 右下角麦克风 - 缩小 1/2，内部改浅蓝色 */}
      <div 
        className="siri-orb-light-mode"
        style={{
          position: 'fixed',
          bottom: '30px',
          right: '30px',
          zIndex: 1002,
          transform: 'scale(0.5)',
          transformOrigin: 'bottom right'
        }}
      >
        <style>{`
          /* 轻微光晕效果 */
          .siri-orb-light-mode .siri-orb-wrapper::before {
            background: radial-gradient(
              circle at center,
              rgba(100, 180, 255, 0.15) 0%,
              rgba(150, 120, 220, 0.08) 35%,
              transparent 60%
            ) !important;
            filter: blur(30px) !important;
          }
          /* 把内部深色改成浅蓝色 */
          .siri-orb-light-mode [class*="rainbowBg"] {
            background: radial-gradient(
              circle at center,
              rgba(180, 210, 240, 0.9) 0%,
              rgba(180, 210, 240, 0.6) 40%,
              rgba(180, 210, 240, 0.3) 65%,
              transparent 100%
            ) !important;
            box-shadow: 0 0 0.3em 0.05em rgba(100, 180, 255, 0.1) !important;
          }
        `}</style>
        <SiriOrb 
          isListening={isListening}
          onClick={onToggleListening}
        />
      </div>

      {/* AMIS 内容区域 */}
      <div className="amis-render-area generated-interface" key={`amis-${currentKey}`} ref={renderAreaRef} style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: '#ffffff',
        zIndex: 1000,
        overflow: 'auto',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif'
      }}>

      {/* 主内容区域 */}
      <div className="amis-content" style={{
        width: '100%',
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '60px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <style>{`
          /* 放大 AMIS 内容 */
          .amis-content .cxd-Page {
            background: transparent !important;
            width: 100%;
            font-size: 16px;
          }
          
          /* 卡片样式优化 */
          .amis-content .cxd-Panel,
          .amis-content .cxd-Card {
            box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
            border: 1px solid #ebebeb !important;
            background: #fff;
            border-radius: 12px !important;
            padding: 24px !important;
          }

          /* 按钮样式微调 - 放大 */
          .amis-content .cxd-Button--primary {
            background: #007aff !important;
            border-color: #007aff !important;
            border-radius: 8px !important;
            height: 40px !important;
            font-size: 16px !important;
            padding: 0 24px !important;
          }
          
          .amis-content .cxd-Button {
            border-radius: 8px !important;
            height: 40px !important;
            font-size: 16px !important;
          }

          /* 输入框样式微调 - 放大 */
          .amis-content .cxd-TextControl-input,
          .amis-content input.cxd-TextControl-input {
            border-radius: 8px !important;
            padding: 10px 16px !important;
            height: 40px !important;
            font-size: 16px !important;
          }
          
          /* 标签文字放大 */
          .amis-content .cxd-Form-label {
            font-size: 16px !important;
            margin-bottom: 8px !important;
          }
          
          /* 标题样式 */
          .amis-content .cxd-Page-title {
            text-align: center;
            margin-bottom: 32px;
            font-weight: 600;
            font-size: 24px !important;
          }
        `}</style>

        {/* 加载中状态 */}
        {!shouldRender && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            minHeight: '200px',
            color: '#999'
          }}>
            加载中...
          </div>
        )}

        {/* AMIS 内容 */}
        {amisContent}
      </div>
      </div>
    </>
  );
};

export default GeneratedInterface;
