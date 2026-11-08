/** @jest-environment node */
import axios from 'axios';
import { runAsyncCommand } from './asyncCommand';
jest.mock('axios', () => ({
  __esModule: true,
  default: { post: jest.fn(), get: jest.fn(), isAxiosError: jest.fn() }
}));

beforeEach(() => {
  jest.resetAllMocks();
  axios.post.mockResolvedValue({ data: { data: { task_id: 'test-task', poll_token: 'local-test-poll-credential' } } });
});

test('polls with a task credential in a header and returns the generated schema', async () => {
  axios.get.mockResolvedValue({ data: { data: { status: 'SUCCESS', result: { schema: { type: 'page' } } } } });
  const result = await runAsyncCommand('test command', {}, { Authorization: 'local-test-auth' });
  expect(result.schema).toEqual({ type: 'page' });
  expect(axios.get).toHaveBeenCalledWith('/api/v1/command/async/test-task', expect.objectContaining({ headers: { Authorization: 'local-test-auth', 'X-Task-Token': 'local-test-poll-credential' } }));
  expect(axios.get.mock.calls[0][0]).not.toContain('credential');
});

test('waits through pending states before returning a terminal result', async () => {
  axios.get.mockResolvedValueOnce({ data: { data: { status: 'PENDING' } } }).mockResolvedValueOnce({ data: { data: { status: 'SUCCESS', result: {} } } });
  await runAsyncCommand('test', {}, {}, { pollIntervalMs: 0 });
  expect(axios.get).toHaveBeenCalledTimes(2);
});

test('rejects submissions without a polling credential', async () => {
  axios.post.mockResolvedValue({ data: { data: { task_id: 'test-task' } } });
  await expect(runAsyncCommand('test', {})).rejects.toThrow('查询凭据');
  expect(axios.get).not.toHaveBeenCalled();
});

test('surfaces terminal failures and bounded waiting', async () => {
  axios.get.mockResolvedValue({ data: { data: { status: 'FAILURE', error: '任务已超时' } } });
  await expect(runAsyncCommand('test', {})).rejects.toThrow('任务已超时');
  await expect(runAsyncCommand('test', {}, {}, { timeoutMs: 0 })).rejects.toThrow('推理超时');
});

test('does not propagate Axios request headers when a request fails', async () => {
  const original = { response: { data: { message: '当前任务较多，请稍后重试' } }, config: { headers: { 'X-Task-Token': 'local-test-poll-credential' } } };
  axios.get.mockRejectedValue(original);
  axios.isAxiosError.mockReturnValue(true);
  try { await runAsyncCommand('test', {}); throw new Error('Expected failure'); }
  catch (error) { expect(error.message).toBe('当前任务较多，请稍后重试'); expect(error.config).toBeUndefined(); }
});

test('cancelling during a poll prevents success from reopening the interface', async () => {
  const controller = new AbortController();
  let complete;
  let markPolled;
  const polled = new Promise(resolve => { markPolled = resolve; });
  axios.get.mockImplementation(() => new Promise(resolve => { complete = resolve; markPolled(); }));
  const pending = runAsyncCommand('fixture', {}, {}, { signal: controller.signal });
  const cancelled = expect(pending).rejects.toMatchObject({ name: 'AbortError' });
  await polled;
  controller.abort();
  complete({ data: { data: { status: 'SUCCESS', result: { schema: { type: 'page' } } } } });
  await cancelled;
});
test('an already cancelled command never submits a task', async () => {
  const controller = new AbortController(); controller.abort();
  await expect(runAsyncCommand('fixture', {}, {}, { signal: controller.signal })).rejects.toMatchObject({ name: 'AbortError' });
  expect(axios.post).not.toHaveBeenCalled();
});
