import React, { useState } from 'react';

interface VoiceInputProps {
  onCommand: (command: string) => void;
  isListening: boolean;
  onToggleListening: () => void;
  transcript: string;
  isSupported: boolean;
}

const VoiceInput: React.FC<VoiceInputProps> = ({
  onCommand,
  isListening,
  onToggleListening,
  transcript,
  isSupported
}) => {
  const [textInput, setTextInput] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onCommand(textInput.trim());
      setTextInput('');
      setShowTextInput(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="voice-unsupported">
        <p>您的浏览器不支持语音识别功能</p>
        <p>请使用文本输入或更换浏览器</p>
        <form onSubmit={handleTextSubmit} style={{ marginTop: '20px' }}>
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="请输入您的需求..."
            style={{
              padding: '12px 16px',
              borderRadius: '24px',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              fontSize: '16px',
              width: '300px',
              marginRight: '10px'
            }}
          />
          <button
            type="submit"
            style={{
              padding: '12px 24px',
              borderRadius: '24px',
              border: 'none',
              background: 'rgba(0, 122, 255, 0.8)',
              color: 'white',
              fontSize: '16px',
              cursor: 'pointer'
            }}
          >
            发送
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="voice-input-container">
      {/* 苹果风格麦克风按钮 */}
      <button
        className={`mic-button ${isListening ? 'listening' : ''}`}
        onClick={onToggleListening}
        aria-label={isListening ? '停止录音' : '开始录音'}
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
          <path d="M19 10v1a7 7 0 0 1-14 0v-1"></path>
          <line x1="12" y1="19" x2="12" y2="23"></line>
          <line x1="8" y1="23" x2="16" y2="23"></line>
        </svg>
      </button>



      {/* 语音识别状态文本 */}
      {isListening && (
        <div className="listening-status">
          <p>正在听...</p>
        </div>
      )}

      {/* 转录文本显示 */}
      {transcript && (
        <div className="transcript-display">
          <p>"{transcript}"</p>
        </div>
      )}

      {/* 文本输入备用选项 */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          onClick={() => setShowTextInput(!showTextInput)}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '20px',
            color: 'rgba(255, 255, 255, 0.8)',
            padding: '8px 16px',
            fontSize: '14px',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
        >
          {showTextInput ? '隐藏文本输入' : '使用文本输入'}
        </button>
      </div>

      {/* 文本输入表单 */}
      {showTextInput && (
        <form onSubmit={handleTextSubmit} style={{ marginTop: '15px', textAlign: 'center' }}>
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="请输入您的需求..."
            style={{
              padding: '12px 16px',
              borderRadius: '24px',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              fontSize: '16px',
              width: '300px',
              marginRight: '10px',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            style={{
              padding: '12px 24px',
              borderRadius: '24px',
              border: 'none',
              background: 'rgba(0, 122, 255, 0.8)',
              color: 'white',
              fontSize: '16px',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          >
            发送
          </button>
        </form>
      )}
    </div>
  );
};

export default VoiceInput;
