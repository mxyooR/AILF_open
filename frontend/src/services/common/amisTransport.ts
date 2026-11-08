import { AxiosRequestConfig } from 'axios';

/** GET/HEAD 的 AMIS data 是查询条件，放进请求体会被浏览器或服务端忽略。 */
export function buildAmisRequest(api: any, headers: Record<string, string>): AxiosRequestConfig {
  const method = String(api.method || 'get').toLowerCase() as AxiosRequestConfig['method'];
  const queryOnly = method === 'get' || method === 'head';
  return {
    method, url: api.url, headers,
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

/** 新指令或新步骤已经替换界面时，旧请求的响应不能再覆盖当前页面。 */
export function canApplyWorkflowResponse(submitted: any, current: any, data: any): boolean {
  if (submitted !== current) return false;
  if (current?.instance_id && data?.instance_id !== current.instance_id) return false;
  if (current?.current_node_id && data?.node_id !== current.current_node_id) return false;
  return true;
}
