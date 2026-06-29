/**
 * SiriOrb - Apple Siri 风格的语音按钮
 * 根据音量动态调整大小
 */
import React, { useMemo } from 'react';
import SiriOrbDemo from './SiriOrbDemo/SiriOrb';
import './SiriOrb.css';

interface SiriOrbProps {
  isListening: boolean;
  isLoading?: boolean;
  disabled?: boolean;
  volume?: number; // 0-1 的音量值
  onClick: () => void;
}

const SiriOrb: React.FC<SiriOrbProps> = ({
  isListening,
  isLoading = false,
  disabled = false,
  volume = 0,
  onClick
}) => {
  // 根据音量计算缩放比例：1.0 - 1.35（仅在监听时）
  const scale = useMemo(() => {
    if (!isListening) return null; // 不监听时不设置，让 CSS hover 生效
    return 1 + Math.min(volume * 0.35, 0.35);
  }, [isListening, volume]);

  // 只在监听时应用动态样式，否则让 CSS 控制
  const dynamicStyle = useMemo(() => {
    if (scale === null) return undefined;
    return {
      transform: `scale(${scale})`,
      transition: 'transform 0.1s ease-out'
    };
  }, [scale]);

  return (
    <div className={`siri-orb-wrapper ${isListening ? 'listening' : ''} ${isLoading ? 'loading' : ''}`}>
      <button
        className="siri-orb-button"
        onClick={onClick}
        disabled={disabled || isLoading}
        aria-label={isLoading ? '模型加载中' : (isListening ? '停止录音' : '开始录音')}
        style={dynamicStyle}
      >
        <SiriOrbDemo />
      </button>
    </div>
  );
};

export default SiriOrb;
