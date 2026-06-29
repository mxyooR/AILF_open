import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * 混合语音识别 Hook
 * 策略：优先使用 Web Speech API（实时），网络失败时自动切换到本地 Whisper（一次性识别）
 */

// Web Speech API 类型定义
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

interface UseLocalVoiceReturn {
  isListening: boolean;
  transcript: string;
  isSupported: boolean;
  isSpeaking: boolean;
  volume: number;
  isModelLoading: boolean;
  modelLoadProgress: number;
  voiceError: string | null;
  recognitionMode: 'online' | 'local' | null; // 当前使用的识别模式
  startListening: () => Promise<void>;
  stopListening: () => void;
  speak: (text: string) => void;
  stopSpeaking: () => void;
  setTranscript: (text: string) => void;
  loadModel: () => Promise<void>;
}

// Whisper 模型配置
const WHISPER_MODEL = 'Xenova/whisper-tiny';

export const useLocalVoice = (): UseLocalVoiceReturn => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);
  const [isModelLoading, setIsModelLoading] = useState(false);
  const [modelLoadProgress, setModelLoadProgress] = useState(0);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [recognitionMode, setRecognitionMode] = useState<'online' | 'local' | null>(null);

  // Refs
  const pipelineRef = useRef<any>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const isListeningRef = useRef(false);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const useLocalModeRef = useRef(false); // 是否使用本地模式（Web Speech 失败后切换）

  // 检查浏览器支持
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    const hasSpeechSynthesis = !!window.speechSynthesis;
    
    setIsSupported(hasMediaDevices && hasSpeechSynthesis);
    
    // 初始化 Web Speech API
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';
      
      recognition.onstart = () => {
        console.log('[语音] Web Speech API 开始识别');
        setRecognitionMode('online');
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const text = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += text;
          } else {
            interimTranscript += text;
          }
        }

        // 实时显示（临时结果带...，最终结果不带）
        if (finalTranscript) {
          setTranscript(finalTranscript);
        } else if (interimTranscript) {
          setTranscript(interimTranscript + '...');
        }
      };

      recognition.onend = () => {
        console.log('[语音] Web Speech API 识别结束');
        if (isListeningRef.current && recognitionMode === 'online') {
          // 如果用户没有手动停止，继续监听
          // 不自动重启，让用户手动控制
        }
        isListeningRef.current = false;
        setIsListening(false);
        stopVolumeAnalysis();
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('[语音] Web Speech API 错误:', event.error);
        
        if (event.error === 'network') {
          console.log('[语音] 网络错误，将切换到本地 Whisper 模式');
          useLocalModeRef.current = true;
          setVoiceError('网络不可用，已切换到本地识别模式（首次需下载模型）');
          
          // 停止当前的 Web Speech
          isListeningRef.current = false;
          setIsListening(false);
          stopVolumeAnalysis();
        } else if (event.error === 'not-allowed') {
          setVoiceError('麦克风权限被拒绝');
          isListeningRef.current = false;
          setIsListening(false);
        } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
          setVoiceError(`语音识别错误: ${event.error}`);
        }
      };
      
      recognitionRef.current = recognition;
    }
    
    if (hasSpeechSynthesis) {
      synthRef.current = window.speechSynthesis;
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

  // 音量分析
  const analyzeVolume = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength;
    const normalizedVolume = Math.min(average / 128, 1);
    setVolume(prev => prev * 0.8 + normalizedVolume * 0.2);

    if (isListeningRef.current) {
      animationFrameRef.current = requestAnimationFrame(analyzeVolume);
    }
  }, []);

  // 启动音量分析
  const startVolumeAnalysis = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current.fftSize = 256;
      microphoneRef.current.connect(analyserRef.current);

      analyzeVolume();
      return stream;
    } catch (error) {
      console.error('[语音] 音频分析启动失败:', error);
      return null;
    }
  };

  // 停止音量分析
  const stopVolumeAnalysis = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (microphoneRef.current) {
      microphoneRef.current.disconnect();
      microphoneRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setVolume(0);
  };

  // 将 Blob 转换为 Float32Array
  const blobToFloat32Array = async (blob: Blob): Promise<Float32Array> => {
    const arrayBuffer = await blob.arrayBuffer();
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: 16000
    });
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const channelData = audioBuffer.getChannelData(0);
    audioContext.close();
    return channelData;
  };

  // 加载 Whisper 模型
  const loadModel = useCallback(async () => {
    if (pipelineRef.current) {
      console.log('[本地语音] 模型已加载');
      return;
    }

    try {
      setIsModelLoading(true);
      setModelLoadProgress(0);
      setVoiceError(null);
      console.log('[本地语音] 开始加载 Whisper 模型...');

      const transformers = await import('@xenova/transformers');
      const { pipeline, env } = transformers;
      
      env.allowLocalModels = false;
      env.useBrowserCache = true;
      
      console.log('[本地语音] 使用官方 Hugging Face CDN');

      pipelineRef.current = await pipeline(
        'automatic-speech-recognition',
        WHISPER_MODEL,
        {
          quantized: true,
          progress_callback: (progress: any) => {
            if (progress.status === 'progress') {
              const percent = Math.round((progress.loaded / progress.total) * 100);
              setModelLoadProgress(percent);
              console.log(`[本地语音] 模型下载进度: ${percent}%`);
            } else if (progress.status === 'done') {
              console.log('[本地语音] 模型文件下载完成');
            }
          }
        }
      );

      setModelLoadProgress(100);
      console.log('[本地语音] Whisper 模型加载完成！');
    } catch (error: any) {
      console.error('[本地语音] 模型加载失败:', error);
      
      if (error.message?.includes('Unexpected token') || error.message?.includes('<!DOCTYPE')) {
        console.log('[本地语音] 检测到缓存错误，正在清除缓存...');
        try {
          await new Promise<void>((resolve, reject) => {
            const request = indexedDB.deleteDatabase('transformers-cache');
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
          });
          const cacheKeys = await caches.keys();
          await Promise.all(cacheKeys.map(key => caches.delete(key)));
          setVoiceError('缓存已清除，请刷新页面重试');
        } catch (clearError) {
          setVoiceError('请手动清除浏览器缓存后重试');
        }
      } else {
        setVoiceError(`模型加载失败: ${error.message}`);
      }
    } finally {
      setIsModelLoading(false);
    }
  }, []);

  // 使用本地 Whisper 进行识别（一次性识别）
  const startLocalRecognition = useCallback(async () => {
    console.log('[本地语音] 启动本地识别模式');
    setRecognitionMode('local');
    
    // 如果模型未加载，先加载
    if (!pipelineRef.current) {
      await loadModel();
      if (!pipelineRef.current) {
        setVoiceError('模型加载失败，无法启动识别');
        return;
      }
    }

    try {
      setVoiceError(null);
      setTranscript('正在聆听...');
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { channelCount: 1, sampleRate: 16000, echoCancellation: true, noiseSuppression: true } 
      });
      mediaStreamRef.current = stream;

      // 启动音量分析
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current.fftSize = 256;
      microphoneRef.current.connect(analyserRef.current);
      analyzeVolume();

      // 创建 MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? 'audio/webm;codecs=opus' : 'audio/webm';
      
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        console.log('[本地语音] 录音结束，开始一次性转录...');
        setTranscript('正在识别...');
        
        if (audioChunksRef.current.length === 0) {
          setTranscript('');
          return;
        }

        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
          const audioData = await blobToFloat32Array(audioBlob);

          if (pipelineRef.current) {
            const result = await pipelineRef.current(audioData, {
              language: 'chinese',
              task: 'transcribe',
              chunk_length_s: 30,
              stride_length_s: 5
            });

            if (result && result.text) {
              const text = result.text.trim();
              setTranscript(text || '');
              console.log('[本地语音] 转录结果:', text);
            } else {
              setTranscript('');
            }
          }
        } catch (error: any) {
          console.error('[本地语音] 转录失败:', error);
          setVoiceError(`转录失败: ${error.message}`);
          setTranscript('');
        }
      };

      mediaRecorderRef.current.start(1000);
      isListeningRef.current = true;
      setIsListening(true);
      console.log('[本地语音] 开始录音');
    } catch (error: any) {
      console.error('[本地语音] 启动录音失败:', error);
      setVoiceError(error.name === 'NotAllowedError' ? '麦克风权限被拒绝' : `启动录音失败: ${error.message}`);
    }
  }, [loadModel, analyzeVolume]);

  // 开始监听
  const startListening = useCallback(async () => {
    if (isListeningRef.current) return;
    
    setVoiceError(null);
    setTranscript('');

    // 如果之前因为网络问题切换到了本地模式，直接使用本地模式
    if (useLocalModeRef.current) {
      await startLocalRecognition();
      return;
    }

    // 首先尝试 Web Speech API
    if (recognitionRef.current) {
      try {
        isListeningRef.current = true;
        setIsListening(true);
        setTranscript('正在聆听...');
        
        // 启动音量分析
        await startVolumeAnalysis();
        
        // 启动 Web Speech API
        recognitionRef.current.start();
        console.log('[语音] 启动 Web Speech API');
      } catch (error: any) {
        console.error('[语音] 启动 Web Speech API 失败:', error);
        
        // 如果启动失败，切换到本地模式
        if (error.message?.includes('already started')) {
          // 已经在运行，忽略
        } else {
          useLocalModeRef.current = true;
          await startLocalRecognition();
        }
      }
    } else {
      // 浏览器不支持 Web Speech API，直接使用本地模式
      useLocalModeRef.current = true;
      await startLocalRecognition();
    }
  }, [startLocalRecognition]);

  // 停止监听
  const stopListening = useCallback(() => {
    console.log('[语音] 停止监听');
    isListeningRef.current = false;
    setIsListening(false);

    // 停止 Web Speech API
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // 忽略
      }
    }

    // 停止 MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    // 停止音量分析
    stopVolumeAnalysis();
  }, []);

  // 语音合成
  const speak = useCallback((text: string) => {
    if (!synthRef.current || !text.trim()) return;

    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.speak(utterance);
  }, []);

  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  }, []);

  return {
    isListening,
    transcript,
    isSupported,
    isSpeaking,
    volume,
    isModelLoading,
    modelLoadProgress,
    voiceError,
    recognitionMode,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    setTranscript,
    loadModel
  };
};
