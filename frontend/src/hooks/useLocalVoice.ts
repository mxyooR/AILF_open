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
  isTranscribing: boolean;
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
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mountedRef = useRef(true);
  const captureVersion = useRef(0);
  const startingRef = useRef(false);
  const transcribingRef = useRef(false);
  const finalTranscriptRef = useRef('');
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
    mountedRef.current = true;
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

        for (let i = 0; i < event.results.length; i++) {
          const text = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += text;
          } else {
            interimTranscript += text;
          }
        }

        finalTranscriptRef.current = finalTranscript;
        // 临时文字仅用于录音预览，结束时只提交真正的最终识别结果。
        if (finalTranscript) {
          setTranscript(finalTranscript);
        } else if (interimTranscript) {
          setTranscript(interimTranscript + '...');
        }
      };

      recognition.onend = () => {
        console.log('[语音] Web Speech API 识别结束');
        setTranscript(finalTranscriptRef.current);
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
        finalTranscriptRef.current = '';
        setTranscript('');
        isListeningRef.current = false;
        setIsListening(false);
        stopVolumeAnalysis();
        
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
      // 页面关闭时释放录音与音量分析资源，且禁止迟到的模型/音频响应更新页面。
      mountedRef.current = false;
      captureVersion.current += 1;
      isListeningRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.abort();
      }
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.ondataavailable = null;
        mediaRecorderRef.current.onstop = null;
        if (mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop();
      }
      stopVolumeAnalysis();
      synthRef.current?.cancel();
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
  const startVolumeAnalysis = async (version: number) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mountedRef.current || version !== captureVersion.current) {
        stream.getTracks().forEach(track => track.stop());
        return null;
      }
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
    if (mountedRef.current) setVolume(0);
  };

  // 将 Blob 转换为 Float32Array
  const blobToFloat32Array = async (blob: Blob): Promise<Float32Array> => {
    const arrayBuffer = await blob.arrayBuffer();
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: 16000
    });
    try {
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      return audioBuffer.getChannelData(0);
    } finally { await audioContext.close(); }
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

      const loadedPipeline = await pipeline(
        'automatic-speech-recognition',
        WHISPER_MODEL,
        {
          quantized: true,
          progress_callback: (progress: any) => {
            if (!mountedRef.current) return;
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

      if (!mountedRef.current) { void loadedPipeline.dispose(); return; }
      pipelineRef.current = loadedPipeline;

      setModelLoadProgress(100);
      console.log('[本地语音] Whisper 模型加载完成！');
    } catch (error: any) {
      if (!mountedRef.current) return;
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
          await Promise.all(cacheKeys.filter(key => key.startsWith('transformers')).map(key => caches.delete(key)));
          setVoiceError('缓存已清除，请刷新页面重试');
        } catch (clearError) {
          setVoiceError('请手动清除浏览器缓存后重试');
        }
      } else {
        setVoiceError(`模型加载失败: ${error.message}`);
      }
    } finally {
      if (mountedRef.current) setIsModelLoading(false);
    }
  }, []);

  // 使用本地 Whisper 进行识别（一次性识别）
  const startLocalRecognition = useCallback(async (version: number) => {
    console.log('[本地语音] 启动本地识别模式');
    setRecognitionMode('local');
    
    // 如果模型未加载，先加载
    if (!pipelineRef.current) {
      await loadModel();
      if (!mountedRef.current || version !== captureVersion.current) return;
      if (!pipelineRef.current) {
        setVoiceError('模型加载失败，无法启动识别');
        return;
      }
    }

    if (!mountedRef.current || version !== captureVersion.current) return;
    try {
      setVoiceError(null);
      setTranscript('');
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { channelCount: 1, sampleRate: 16000, echoCancellation: true, noiseSuppression: true } 
      });
      if (!mountedRef.current || version !== captureVersion.current) {
        stream.getTracks().forEach(track => track.stop());
        return;
      }
      mediaStreamRef.current = stream;

      // 启动音量分析
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current.fftSize = 256;
      microphoneRef.current.connect(analyserRef.current);
      analyzeVolume();

      // 创建 MediaRecorder
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
        .find(type => MediaRecorder.isTypeSupported(type));
      
      mediaRecorderRef.current = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        console.log('[本地语音] 录音结束，开始一次性转录...');
        if (!mountedRef.current || version !== captureVersion.current) return;
        transcribingRef.current = true;
        setIsTranscribing(true);
        setTranscript('');
        
        if (audioChunksRef.current.length === 0) {
          transcribingRef.current = false;
          setIsTranscribing(false);
          setTranscript('');
          return;
        }

        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
          const audioData = await blobToFloat32Array(audioBlob);

          if (pipelineRef.current && mountedRef.current && version === captureVersion.current) {
            const result = await pipelineRef.current(audioData, {
              language: 'chinese',
              task: 'transcribe',
              chunk_length_s: 30,
              stride_length_s: 5
            });

            if (!mountedRef.current || version !== captureVersion.current) return;
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
          if (mountedRef.current && version === captureVersion.current) {
            setVoiceError(`转录失败: ${error.message}`);
            setTranscript('');
          }
        } finally {
          transcribingRef.current = false;
          if (mountedRef.current && version === captureVersion.current) setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current.start(1000);
      isListeningRef.current = true;
      setIsListening(true);
      console.log('[本地语音] 开始录音');
    } catch (error: any) {
      stopVolumeAnalysis();
      isListeningRef.current = false;
      if (!mountedRef.current || version !== captureVersion.current) return;
      setIsListening(false);
      console.error('[本地语音] 启动录音失败:', error);
      setVoiceError(error.name === 'NotAllowedError' ? '麦克风权限被拒绝' : `启动录音失败: ${error.message}`);
    }
  }, [loadModel, analyzeVolume]);

  // 异步申请权限/下载模型时也加锁，防止快速点击产生多个录音实例。
  const startListening = useCallback(async () => {
    if (isListeningRef.current || startingRef.current || transcribingRef.current) return;
    const version = ++captureVersion.current;
    startingRef.current = true;
    finalTranscriptRef.current = '';
    setVoiceError(null);
    setTranscript('');
    try {
      if (useLocalModeRef.current || !recognitionRef.current) {
        useLocalModeRef.current = true;
        await startLocalRecognition(version);
        return;
      }
      isListeningRef.current = true;
      setIsListening(true);
      const stream = await startVolumeAnalysis(version);
      if (!mountedRef.current || version !== captureVersion.current) return;
      if (!stream) {
        isListeningRef.current = false;
        setIsListening(false);
        setVoiceError('无法访问麦克风，请检查浏览器权限');
        return;
      }
      try {
        recognitionRef.current.start();
      } catch {
        stopVolumeAnalysis();
        isListeningRef.current = false;
        setIsListening(false);
        useLocalModeRef.current = true;
        await startLocalRecognition(version);
      }
    } finally { startingRef.current = false; }
  }, [startLocalRecognition]);

  // 停止监听
  const stopListening = useCallback(() => {
    console.log('[语音] 停止监听');
    if (startingRef.current) captureVersion.current += 1;
    isListeningRef.current = false;
    setIsListening(false);

    // 停止 Web Speech API
    if (recognitionRef.current && !useLocalModeRef.current) {
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
    isTranscribing,
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
