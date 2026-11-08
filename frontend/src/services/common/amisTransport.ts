import { AxiosRequestConfig } from 'axios';

/** 自动附加的用户令牌仅发往本应用 API，模型生成的外部地址不能带走登录身份。 */
export function canSendUserToken(rawUrl: string): boolean {
  try {
    const url = new URL(rawUrl, window.location.origin);
    const allowed = new Set([window.location.host, 'localhost:3000', '127.0.0.1:3000', 'localhost:5000', '127.0.0.1:5000']);
    return ['http:', 'https:'].includes(url.protocol) && allowed.has(url.host) && url.pathname.startsWith('/api/');
  } catch { return false; }
}

/** GET/HEAD 的 AMIS data 是查询条件，放进请求体会被浏览器或服务端忽略。 */
export function buildAmisRequest(api: any, headers: Record<string, string>): AxiosRequestConfig {
  const method = String(api.method || 'get').toLowerCase() as AxiosRequestConfig['method'];
  const queryOnly = method === 'get' || method === 'head';
  return {
    ...api.config,
    method, url: api.url, headers,
    responseType: api.responseType || api.config?.responseType,
    params: queryOnly ? { ...api.data, ...api.params } : api.params,
    data: queryOnly ? undefined : api.data,
  };
}

/** 保留原业务包裹供既有模板读取，统一判定 HTTP 200 内的业务失败。 */
export function normalizeAmisResponse(payload: any, statusText = '') {
  let status = 0;
  let msg = statusText;
  if (payload && typeof payload === 'object') {
    const rawStatus = payload.status ?? payload.code;
    if (rawStatus != null && rawStatus !== '') {
      const code = Number(rawStatus);
      status = !Number.isFinite(code) ? 1 : code === 0 || (code >= 200 && code < 300) ? 0 : code;
    }
    if (payload.success === false && status === 0) status = 1;
    msg = payload.msg || payload.message || msg;
  }
  return { status, msg, data: payload };
}

/** AMIS fetcher 接收 Axios 形状，状态必须位于 response.data，外层 status 不参与业务判断。 */
export function toAmisFetcherResponse(payload: any, statusText = '') {
  const { status, msg } = normalizeAmisResponse(payload, statusText);
  const data = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? { ...payload, status, msg }
    : { status, msg, data: payload };
  // AMIS 即使判定失败也会合并非空 data；错误详情不能覆盖用户正在编辑的字段。
  if (status !== 0) data.data = null;
  // 保留 code/data 等原有字段，使模板 adaptor 仍可读取原来的后端包裹。
  return { data };
}

/** 新指令或新步骤已经替换界面时，旧请求的响应不能再覆盖当前页面。 */
export function canApplyWorkflowResponse(submitted: any, current: any, data: any): boolean {
  if (submitted !== current) return false;
  if (current?.instance_id && data?.instance_id !== current.instance_id) return false;
  if (current?.current_node_id && data?.node_id !== current.current_node_id) return false;
  return true;
}
