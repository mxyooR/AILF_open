import { useState, useRef, useEffect } from 'react';

// 语音识别类型定义
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }

  interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
    onend: ((this: SpeechRecognition, ev: Event) => any) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
    start(): void;
    stop(): void;
    abort(): void;
  }
}

interface UseVoiceReturn {
  isListening: boolean;
  transcript: string;
  isSupported: boolean;
  isSpeaking: boolean;
  volume: number; // 音量级别 (0-1)
  startListening: () => Promise<void>;
  stopListening: () => void;
  speak: (text: string) => void;
  stopSpeaking: () => void;
  checkMicrophonePermission: () => Promise<boolean>;
  setTranscript: (text: string) => void;
  voiceError: string | null;
}

export const useVoice = (): UseVoiceReturn => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);
  const [voiceError, setVoiceError] = useState<string | null>(null); // 新增错误状态

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null); // 保存 MediaStream 引用以便正确释放
  const isListeningRef = useRef(false); // 使用 ref 跟踪监听状态，避免闭包问题
  const isStartingRef = useRef(false); // 防止重复启动

  useEffect(() => {
    // 检查浏览器支持
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;
    
    if (SpeechRecognition && speechSynthesis) {
      setIsSupported(true);
      
      // 初始化语音识别
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';
      
      recognition.onstart = () => {
        isListeningRef.current = true;
        isStartingRef.current = false;
        setIsListening(true);
        console.log('[语音] 开始语音识别');
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript || interimTranscript);
      };

      recognition.onend = () => {
        isListeningRef.current = false;
        isStartingRef.current = false;
        setIsListening(false);
        console.log('[语音] 语音识别结束');
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('[语音] 语音识别错误:', event.error);
        isListeningRef.current = false;
        isStartingRef.current = false;
        setIsListening(false);

        // 根据错误类型给出不同的提示
        switch (event.error) {
          case 'network':
            const netMsg = '网络连接失败，无法连接到语音服务(可能需要代理)';
            console.warn('[语音]', netMsg);
            setVoiceError(netMsg);
            break;
          case 'not-allowed':
            const permMsg = '麦克风权限被拒绝';
            console.warn('[语音]', permMsg);
            setVoiceError(permMsg);
            break;
          case 'no-speech':
            // no-speech 只是没听到声音，不算严重错误
            console.warn('[语音] 未检测到语音');
            break;
          case 'audio-capture':
            setVoiceError('音频捕获失败，请检查麦克风');
            break;
          case 'aborted':
            console.warn('[语音] 语音识别被中止');
            break;
          default:
            setVoiceError(`语音识别错误: ${event.error}`);
        }
      };
      
      recognitionRef.current = recognition;
      synthRef.current = speechSynthesis;
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // 音量分析函数 - 使用 ref 避免闭包问题
  const analyzeVolume = () => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // 计算平均音量
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength;

    // 将音量标准化到0-1范围，并应用平滑处理
    const normalizedVolume = Math.min(average / 128, 1);
    setVolume(prev => prev * 0.8 + normalizedVolume * 0.2); // 平滑处理

    // 使用 ref 来检查监听状态，避免闭包捕获旧值
    if (isListeningRef.current) {
      animationFrameRef.current = requestAnimationFrame(analyzeVolume);
    }
  };

  // 启动音频分析
  const startVolumeAnalysis = async () => {
    try {
      // 先清理之前的资源
      stopVolumeAnalysis();
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream; // 保存引用以便后续释放

      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);

      analyserRef.current.fftSize = 256;
      microphoneRef.current.connect(analyserRef.current);

      analyzeVolume();
    } catch (error) {
      console.error('[语音] 音频分析启动失败:', error);
    }
  };

  // 停止音频分析
  const stopVolumeAnalysis = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (microphoneRef.current) {
      microphoneRef.current.disconnect();
      microphoneRef.current = null;
    }

    // 正确释放 MediaStream 的所有 tracks
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('[语音] 停止音频轨道:', track.label);
      });
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(err => {
        console.warn('[语音] 关闭 AudioContext 失败:', err);
      });
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setVolume(0);
  };

  const checkMicrophonePermission = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('[语音] 麦克风权限被拒绝:', error);
      return false;
    }
  };

  const startListening = async (): Promise<void> => {
    if (!recognitionRef.current || !isSupported) {
      console.warn('[语音] 语音识别不可用');
      return;
    }

    // 防止重复启动
    if (isListeningRef.current || isStartingRef.current) {
      console.warn('[语音] 语音识别已在运行或正在启动中');
      return;
    }

    isStartingRef.current = true;
    console.log('[语音] 准备启动语音识别...');
    
    // 立即设置监听状态，提供即时UI反馈
    setIsListening(true);
    setVoiceError(null); // 开始时清除错误

    const hasPermission = await checkMicrophonePermission();
    if (!hasPermission) {
      isStartingRef.current = false;
      setIsListening(false); // 权限被拒，重置状态
      console.warn('[语音] 没有麦克风权限');
      setVoiceError('没有麦克风权限');
      return;
    }

    setTranscript('');

    try {
      // 先确保之前的识别已经停止
      try {
        recognitionRef.current.abort();
      } catch (e) {
        // 忽略 abort 错误
      }
      
      // 短暂延迟确保之前的识别完全停止
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 启动音量分析
      await startVolumeAnalysis();
      
      // 启动语音识别
      recognitionRef.current.start();
      console.log('[语音] 语音识别启动命令已发送');
    } catch (error: any) {
      isStartingRef.current = false;
      isListeningRef.current = false;
      setIsListening(false);
      
      // 特殊处理 "already started" 错误
      if (error.message?.includes('already started')) {
        console.warn('[语音] 语音识别已在运行中，尝试重启');
        try {
          recognitionRef.current.stop();
          await new Promise(resolve => setTimeout(resolve, 200));
          recognitionRef.current.start();
        } catch (retryError) {
          console.error('[语音] 重启语音识别失败:', retryError);
          stopVolumeAnalysis();
          setVoiceError('重启语音识别失败');
        }
      } else {
        console.error('[语音] 启动语音识别失败:', error);
        stopVolumeAnalysis();
        setVoiceError('启动语音识别失败');
      }
    }
  };

  const stopListening = (): void => {
    console.log('[语音] 停止语音识别');
    isStartingRef.current = false;
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (error) {
        console.warn('[语音] 停止语音识别时出错:', error);
        // 如果 stop 失败，尝试 abort
        try {
          recognitionRef.current.abort();
        } catch (abortError) {
          console.warn('[语音] 中止语音识别时出错:', abortError);
        }
      }
    }
    
    isListeningRef.current = false;
    setIsListening(false);
    // 停止音量分析
    stopVolumeAnalysis();
  };

  const speak = (text: string): void => {
    if (!synthRef.current || !text.trim()) return;
    
    // 停止当前播放
    synthRef.current.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    
    utterance.onstart = () => {
      setIsSpeaking(true);
      console.log('[语音] 开始语音合成');
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
      console.log('[语音] 语音合成结束');
    };
    
    utterance.onerror = (event) => {
      console.error('[语音] 语音合成错误:', event.error);
      setIsSpeaking(false);
    };
    
    synthRef.current.speak(utterance);
  };

  const stopSpeaking = (): void => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  return {
    isListening,
    transcript,
    isSupported,
    isSpeaking,
    volume,
    voiceError, // 导出错误状态
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    checkMicrophonePermission,
    setTranscript
  };
};
