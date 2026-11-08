import { useCallback, useEffect, useRef, useState } from 'react';

export interface CommandRequest {
  controller: AbortController;
}

/** 同一页面只允许一个指令；关闭、退出或卸载后，迟到的响应不能重新打开界面。 */
export function useCommandRequest() {
  const active = useRef<CommandRequest | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const beginRequest = useCallback(() => {
    if (active.current) return null;
    const request = { controller: new AbortController() };
    active.current = request;
    setIsProcessing(true);
    return request;
  }, []);

  const isCurrentRequest = useCallback((request: CommandRequest) =>
    active.current === request && !request.controller.signal.aborted, []);

  const finishRequest = useCallback((request: CommandRequest) => {
    if (active.current !== request) return;
    active.current = null;
    setIsProcessing(false);
  }, []);

  const cancelRequest = useCallback(() => {
    active.current?.controller.abort();
    active.current = null;
    setIsProcessing(false);
  }, []);

  useEffect(() => () => {
    active.current?.controller.abort();
    active.current = null;
  }, []);

  return { isProcessing, beginRequest, isCurrentRequest, finishRequest, cancelRequest };
}
