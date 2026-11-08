import axios from 'axios';

export type AsyncCommandResult = { schema: any; responseText: string; message: string; raw: any };
type Options = { baseURL?: string; timeoutMs?: number; pollIntervalMs?: number };

/** Keeps the per-task polling credential in memory and out of URLs and Axios error logs. */
export async function runAsyncCommand(command: string, context: Record<string, any>, headers: Record<string, string> = {}, options: Options = {}): Promise<AsyncCommandResult> {
  const { baseURL = '', timeoutMs = 600000, pollIntervalMs = 1200 } = options;
  try {
    const endpoint = `${baseURL}/api/v1/command/async`;
    const submitted = await axios.post(endpoint, { command, context }, { timeout: 30000, headers });
    const { task_id: taskId, poll_token: pollToken } = submitted?.data?.data || {};
    if (!taskId || !pollToken) throw new Error('异步任务提交失败：未返回任务查询凭据');
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const response = await axios.get(`${endpoint}/${encodeURIComponent(taskId)}`, { timeout: 30000, headers: { ...headers, 'X-Task-Token': pollToken } });
      const task = response?.data?.data || {};
      if (task.status === 'SUCCESS') {
        const result = task.result || {};
        return { schema: result.amis_schema || result.schema || null, responseText: result.response_text || '', message: response?.data?.message || '', raw: result };
      }
      if (task.status === 'FAILURE') throw new Error(task.error || '异步任务执行失败');
      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
    }
    throw new Error('AI推理超时，请稍后重试');
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message;
      throw new Error(typeof message === 'string' ? message : 'AI任务请求失败，请检查服务状态');
    }
    throw error;
  }
}
