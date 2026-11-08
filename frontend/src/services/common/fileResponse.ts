import { normalizeAmisResponse } from './amisTransport';

/** 文件接口也可能返回 HTTP 200 的 JSON 错误；检查副本，保留原始流供下载或预览。 */
export async function ensureFileResponse(response: Response): Promise<void> {
  const contentType = response.headers.get('content-type') || '';
  let payload: any;
  if (/\bjson\b/i.test(contentType)) {
    try { payload = await response.clone().json(); }
    catch { throw new Error('文件接口返回了无效的 JSON'); }
    // 普通 JSON 文件可以有 status 等业务字段，只识别本项目的响应包裹。
    const envelope = payload && typeof payload === 'object' && !Array.isArray(payload)
      && (payload.code != null || typeof payload.status === 'number' || payload.success === false);
    if (envelope) {
      const result = normalizeAmisResponse(payload);
      if (result.status !== 0) throw new Error(result.msg || '文件操作失败');
    }
  }
  if (!response.ok) throw new Error(payload?.message || payload?.msg || payload?.detail || `文件请求失败 (${response.status})`);
}
