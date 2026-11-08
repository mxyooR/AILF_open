import axios from 'axios';

export type AsyncCommandResult = { schema: any; responseText: string; message: string; raw: any };
type Options = { baseURL?: string; timeoutMs?: number; pollIntervalMs?: number; signal?: AbortSignal; requirePollToken?: boolean };

function cancellationError() {
  const error = new Error('已取消请求');
  error.name = 'AbortError';
  return error;
}

function assertActive(signal?: AbortSignal) {
  if (signal?.aborted) throw cancellationError();
}

/** 取消等待时同时清理定时器与监听器，避免关掉界面后继续轮询。 */
function waitForPoll(delay: number, signal?: AbortSignal) {
  assertActive(signal);
  return new Promise<void>((resolve, reject) => {
    const cancel = () => {
      clearTimeout(timer);
      signal?.removeEventListener('abort', cancel);
      reject(cancellationError());
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', cancel);
      resolve();
    }, delay);
    signal?.addEventListener('abort', cancel, { once: true });
  });
}

/** 查询凭据仅保存在内存和请求头；两个仓库分别兼容带凭据和原有私有任务接口。 */
export async function runAsyncCommand(command: string, context: Record<string, any>, headers: Record<string, string> = {}, options: Options = {}): Promise<AsyncCommandResult> {
  const { baseURL = '', timeoutMs = 600000, pollIntervalMs = 1200, signal, requirePollToken = true } = options;
  try {
    assertActive(signal);
    const endpoint = `${baseURL}/api/v1/command/async`;
    const submitted = await axios.post(endpoint, { command, context }, { timeout: 30000, headers, signal });
    assertActive(signal);
    const { task_id: taskId, poll_token: pollToken } = submitted?.data?.data || {};
    if (!taskId || (requirePollToken && !pollToken)) throw new Error('异步任务提交失败：未返回任务查询凭据');
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      assertActive(signal);
      const response = await axios.get(`${endpoint}/${encodeURIComponent(taskId)}`, { timeout: Math.min(30000, Math.max(1, deadline - Date.now())), signal, headers: { ...headers, ...(pollToken ? { 'X-Task-Token': pollToken } : {}) } });
      assertActive(signal);
      const task = response?.data?.data || {};
      if (task.status === 'SUCCESS') {
        const result = task.result || {};
        return { schema: result.amis_schema || result.schema || null, responseText: result.response_text || '', message: response?.data?.message || '', raw: result };
      }
      if (task.status === 'FAILURE') throw new Error(task.error || '异步任务执行失败');
      await waitForPoll(Math.min(pollIntervalMs, Math.max(0, deadline - Date.now())), signal);
    }
    throw new Error('AI推理超时，请稍后重试');
  } catch (error) {
    assertActive(signal);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message;
      throw new Error(typeof message === 'string' ? message : 'AI任务请求失败，请检查服务状态');
    }
    throw error;
  }
}
