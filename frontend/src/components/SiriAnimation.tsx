import React, { useEffect, useRef } from 'react';

// 导入SiriWave类型定义
interface SiriWaveOptions {
  container: HTMLElement;
  style?: 'ios' | 'ios9';
  ratio?: number;
  speed?: number;
  amplitude?: number;
  frequency?: number;
  color?: string;
  cover?: boolean;
  width?: number;
  height?: number;
  autostart?: boolean;
  pixelDepth?: number;
  lerpSpeed?: number;
  curveDefinition?: any[];
  ranges?: any;
  globalCompositeOperation?: string;
}

// SiriWave类的简化声明
declare class SiriWave {
  constructor(options: SiriWaveOptions);
  start(): void;
  stop(): void;
  dispose(): void;
  setAmplitude(amplitude: number): void;
  setSpeed(speed: number): void;
}

interface SiriAnimationProps {
  isActive: boolean;
  amplitude?: number; // 振幅控制 (0-1)
  style?: 'ios' | 'ios9'; // 使用官方SiriWave样式
  height?: number; // 高度
}

const SiriAnimation: React.FC<SiriAnimationProps> = ({
  isActive,
  amplitude = 0.8,
  style = 'ios9', // 默认使用iOS9样式
  height = 80
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const siriWaveRef = useRef<SiriWave | null>(null);

  // 初始化SiriWave实例
  const initSiriWave = () => {
    const container = containerRef.current;
    if (!container || siriWaveRef.current) return;

    try {
      // 动态导入SiriWave库
      import('../lib/siriwave.js').then((SiriWaveModule: any) => {
        console.log('SiriWave module loaded:', SiriWaveModule);
        const SiriWave = SiriWaveModule.default || SiriWaveModule;

        if (!SiriWave) {
          console.error('SiriWave constructor not found in module');
          return;
        }

        // 创建SiriWave实例 - 调整速度和幅度参数
        try {
          siriWaveRef.current = new SiriWave({
            container: container,
            style: style, // 'ios9' 样式
            width: container.offsetWidth || window.innerWidth,
            height: height,
            speed: 0.05, // 回归原来的速度
            amplitude: amplitude * 1.5, // 适中的振幅
            autostart: false,
            cover: true,
            globalCompositeOperation: 'lighter',
            pixelDepth: 0.02, // 还原精度
            lerpSpeed: 0.05,
            // 还原经典 Siri 配色：深色调 + 白色支撑线
            curveDefinition: style === 'ios9' ? [
              {
                color: "255,255,255", // 白色支撑线
                supportLine: true,
              },
              {
                color: "15, 82, 169", // 深蓝
              },
              {
                color: "173, 57, 76", // 深红
              },
              {
                color: "48, 220, 155", // 翠绿
              }
            ] : undefined,
            // 调整范围参数
            ranges: style === 'ios9' ? {
              noOfCurves: [3, 5], // 还原原来的曲线数量
              amplitude: [0.5, 1.5], 
              offset: [-5, 5], 
              width: [1, 4], 
              speed: [0.1, 0.4], // 还原速度范围
              despawnTimeout: [1000, 3000]
            } : undefined
          });

          // 根据当前状态启动或停止动画
          if (isActive) {
            siriWaveRef.current?.start();
          }
        } catch (err) {
          console.error('Error creating SiriWave instance:', err);
          createFallbackAnimation();
        }
      }).catch((error) => {
        console.error('Failed to load SiriWave:', error);
        // 如果加载失败，使用简单的fallback动画
        createFallbackAnimation();
      });
    } catch (error) {
      console.error('Error initializing SiriWave:', error);
      createFallbackAnimation();
    }
  };

  // 简单的fallback动画
  const createFallbackAnimation = () => {
    console.log('Using fallback animation');
    // 这里可以实现一个简单的fallback动画
  };

  // 初始化SiriWave
  useEffect(() => {
    const timer = setTimeout(() => {
      initSiriWave();
    }, 100); // 延迟初始化确保容器已渲染

    return () => {
      clearTimeout(timer);
      if (siriWaveRef.current) {
        siriWaveRef.current.dispose();
        siriWaveRef.current = null;
      }
    };
  }, [style, height]);

  // 控制动画状态
  useEffect(() => {
    if (!siriWaveRef.current) return;

    if (isActive) {
      siriWaveRef.current.start();
    } else {
      siriWaveRef.current.stop();
    }
  }, [isActive]);

  // 控制振幅
  useEffect(() => {
    if (!siriWaveRef.current) return;
    siriWaveRef.current.setAmplitude(amplitude);
  }, [amplitude]);

  return (
    <div
      ref={containerRef}
      className="siri-wave-container"
      style={{
        width: '100%',
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      {/* SiriWave会自动创建canvas并添加到这个容器中 */}
    </div>
  );
};

export default SiriAnimation;
