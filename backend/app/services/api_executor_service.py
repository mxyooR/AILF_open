"""
API 执行服务 - 工作流节点的业务 API 调用

核心职责：
- 根据工作流节点配置调用对应的业务 API
- 通过内部 HTTP 请求调用已注册的动态路由
- 处理 API 响应并返回结果
"""
import json
import re
import httpx
from typing import Dict, Any, Optional, List
from app.core.logging_config import get_logger
from app.core.database import get_db_session
from app.models.api_route import APIRouteDBModel

logger = get_logger(__name__)

# 内部 API 调用的基础 URL
INTERNAL_API_BASE_URL = "http://127.0.0.1:5000"


class APIExecutorService:
    """
    API 执行服务
    
    负责在工作流 api_call 节点执行时，调用实际的业务 API
    通过内部 HTTP 请求调用已注册的动态路由
    """
    
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=INTERNAL_API_BASE_URL,
                timeout=30.0,
                trust_env=False  # 内部回环调用禁止读取系统代理，避免被转发到本地代理端口
            )
        return self._http_client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    def _find_api_route(self, api_id: str = None, endpoint: str = None, method: str = None) -> Optional[Dict[str, Any]]:
        """
        从数据库查找 API 路由配置
        
        Args:
            api_id: API 标识符
            endpoint: API 端点路径
            method: HTTP 方法
        
        Returns:
            API 路由配置字典，未找到返回 None
        """
        try:
            with get_db_session() as db:
                query = db.query(APIRouteDBModel)
                
                # 优先通过 api_id 查找
                if api_id:
                    route = query.filter(APIRouteDBModel.api_id == api_id).first()
                    if route:
                        logger.info(f"[APIExec] 通过 api_id 找到路由: {api_id} -> {route.method} {route.endpoint}")
                        return self._route_to_dict(route)
                
                # 通过 endpoint 和 method 查找
                if endpoint:
                    # 标准化 endpoint
                    normalized_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
                    
                    # 精确匹配
                    if method:
                        route = query.filter(
                            APIRouteDBModel.endpoint == normalized_endpoint,
                            APIRouteDBModel.method == method.upper()
                        ).first()
                    else:
                        route = query.filter(APIRouteDBModel.endpoint == normalized_endpoint).first()
                    
                    if route:
                        logger.info(f"[APIExec] 通过 endpoint 找到路由: {route.method} {route.endpoint}")
                        return self._route_to_dict(route)
                    
                    # 模糊匹配（处理路径参数）
                    all_routes = query.all()
                    for route in all_routes:
                        if self._match_endpoint_pattern(route.endpoint, normalized_endpoint):
                            if not method or route.method.upper() == method.upper():
                                logger.info(f"[APIExec] 通过模式匹配找到路由: {route.method} {route.endpoint}")
                                return self._route_to_dict(route)
                
                logger.warning(f"⚠️ [APIExec] 未找到 API 路由: api_id={api_id}, endpoint={endpoint}, method={method}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [APIExec] 查找 API 路由失败: {e}")
            return None
    
    def _route_to_dict(self, route: APIRouteDBModel) -> Dict[str, Any]:
        """将路由模型转换为字典"""
        return {
            "id": route.id,
            "api_id": route.api_id,
            "endpoint": route.endpoint,
            "method": route.method,
            "parameters_config": route.parameters_config,
            "handler_type": route.handler_type.value if hasattr(route.handler_type, 'value') else str(route.handler_type),
            "handler_config": route.handler_config,
            "auth_required": route.auth_required,
            "status": route.status.value if hasattr(route.status, 'value') else str(route.status)
        }
    
    def _match_endpoint_pattern(self, pattern: str, endpoint: str) -> bool:
        """
        匹配带路径参数的 endpoint
        
        例如: /api/v1/orders/{order_id} 匹配 /api/v1/orders/123
        """
        # 将 {param} 转换为正则表达式
        regex_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', pattern)
        regex_pattern = f"^{regex_pattern}$"
        return bool(re.match(regex_pattern, endpoint))
    
    def _substitute_path_params(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        替换路径参数
        
        例如: /api/v1/orders/{order_id} + {order_id: 123} -> /api/v1/orders/123
        """
        result = endpoint
        for key, value in params.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def _resolve_template_variables(
        self,
        value: Any,
        session_data: Dict[str, Any]
    ) -> Any:
        """
        解析模板变量
        
        支持的格式：
        - ${field_name} -> 从 session_data 中获取 field_name（优先）
        - ${input.field_name} -> 从 session_data 中获取 field_name
        - ${node_id_result.field} -> 从之前节点的结果中获取
        - ${last_api_result.field} -> 从最近一次 API 结果中获取
        
        Args:
            value: 要解析的值（可以是字符串、字典或列表）
            session_data: 会话数据
        
        Returns:
            解析后的值
        """
        if isinstance(value, str):
            # 匹配 ${...} 格式的模板变量
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                var_path = match.group(1)
                original = match.group(0)
                
                logger.debug(f"[APIExec] 解析模板变量: {var_path}, session_data keys: {list(session_data.keys())}")

                def _resolve_from_dict(field_name: Optional[str], data: Any) -> Optional[Any]:
                    """Try direct field and prefix-stripped alias (e.g., passenger_name -> name)."""
                    if not field_name or not isinstance(data, dict):
                        return None
                    if field_name in data:
                        return data.get(field_name)
                    if "_" in field_name:
                        alias_name = field_name.split("_", 1)[1]
                        if alias_name in data:
                            logger.debug(f"[APIExec] 别名映射 {field_name} -> {alias_name} = {data.get(alias_name)}")
                            return data.get(alias_name)
                    return None
                
                # 1. 处理 input.xxx 格式（兼容旧格式）
                if var_path.startswith("input."):
                    field_name = var_path[6:]  # 去掉 "input." 前缀
                    if field_name in session_data:
                        resolved_value = session_data[field_name]
                        logger.debug(f"[APIExec] 解析 input.{field_name} = {resolved_value}")
                        return str(resolved_value) if resolved_value is not None else original
                    logger.debug(f"[APIExec] 未找到 input.{field_name}")
                    return original
                
                # 2. 处理 xxx_result.yyy 格式（之前节点的结果）
                if "_result." in var_path:
                    parts = var_path.split(".", 1)
                    result_key = parts[0]
                    field_name = parts[1] if len(parts) > 1 else None
                    
                    result_data = session_data.get(result_key, {})
                    if field_name and isinstance(result_data, dict):
                        if field_name in result_data:
                            resolved_value = result_data[field_name]
                            logger.debug(f"[APIExec] 解析 {result_key}.{field_name} = {resolved_value}")
                            return str(resolved_value) if resolved_value is not None else original
                    elif result_data:
                        logger.debug(f"[APIExec] 解析 {result_key} = {result_data}")
                        return str(result_data)
                    logger.debug(f"[APIExec] 未找到 {var_path}")
                    return original
                
                # 3. 处理 last_api_result.xxx 格式
                if var_path.startswith("last_api_result."):
                    field_name = var_path[16:]  # 去掉 "last_api_result." 前缀
                    last_result = session_data.get("last_api_result", {})
                    if isinstance(last_result, dict) and field_name in last_result:
                        resolved_value = last_result[field_name]
                        logger.debug(f"[APIExec] 解析 last_api_result.{field_name} = {resolved_value}")
                        return str(resolved_value) if resolved_value is not None else original
                    logger.debug(f"[APIExec] 未找到 last_api_result.{field_name}")
                    return original
                
                # 4. 处理 namespace.field 格式的别名映射（通用机制）
                # 例如：${train_query.train_number} -> 如果没有 train_query 对象，但有 train_number 字段
                if "." in var_path:
                    parts = var_path.split(".", 1)
                    namespace = parts[0]
                    field_name = parts[1] if len(parts) > 1 else None
                    
                    # 先尝试从命名空间对象中获取
                    namespace_data = session_data.get(namespace)
                    if isinstance(namespace_data, dict):
                        resolved_value = _resolve_from_dict(field_name, namespace_data)
                        if resolved_value is not None:
                            logger.debug(f"[APIExec] 解析 {namespace}.{field_name} = {resolved_value}")
                            return str(resolved_value) if resolved_value is not None else original

                    # 尝试从 *_result 命名空间中解析（如 n_passenger_verification_result）
                    candidate_keys = [f"{namespace}_result", f"n_{namespace}_result"]
                    for candidate_key in candidate_keys:
                        candidate_data = session_data.get(candidate_key)
                        if isinstance(candidate_data, dict):
                            resolved_value = _resolve_from_dict(field_name, candidate_data)
                            if resolved_value is not None:
                                logger.debug(
                                    f"[APIExec] 别名映射 {namespace}.{field_name} -> {candidate_key}.{field_name} = {resolved_value}"
                                )
                                return str(resolved_value) if resolved_value is not None else original

                    # 再兜底：查找任意以 <namespace>_result 结尾的结果
                    suffix = f"{namespace}_result"
                    for key, value in session_data.items():
                        if key.endswith(suffix) and isinstance(value, dict):
                            resolved_value = _resolve_from_dict(field_name, value)
                            if resolved_value is not None:
                                logger.debug(
                                    f"[APIExec] 别名映射 {namespace}.{field_name} -> {key}.{field_name} = {resolved_value}"
                                )
                                return str(resolved_value) if resolved_value is not None else original

                    # 别名映射：如果命名空间不存在，但字段存在于根级别，则使用根级别的值
                    if field_name and field_name in session_data:
                        resolved_value = session_data[field_name]
                        logger.debug(f"[APIExec] 别名映射 {namespace}.{field_name} -> {field_name} = {resolved_value}")
                        return str(resolved_value) if resolved_value is not None else original

                    # 根级别前缀别名：foo_bar -> bar
                    resolved_value = _resolve_from_dict(field_name, session_data)
                    if resolved_value is not None:
                        logger.debug(f"[APIExec] 别名映射 {namespace}.{field_name} -> {field_name} = {resolved_value}")
                        return str(resolved_value) if resolved_value is not None else original

                    logger.debug(f"[APIExec] 未找到 {var_path}（命名空间或字段不存在）")
                    return original
                
                # 5. 直接从 session_data 获取（最常用的格式：${field_name}）
                if var_path in session_data:
                    resolved_value = session_data[var_path]
                    logger.debug(f"[APIExec] 解析 {var_path} = {resolved_value}")
                    return str(resolved_value) if resolved_value is not None else original

                # 6. 回退：从 last_api_result 或任意 *_result 中查找同名字段
                last_result = session_data.get("last_api_result")
                if isinstance(last_result, dict) and var_path in last_result:
                    resolved_value = last_result[var_path]
                    logger.debug(f"[APIExec] 回退解析 last_api_result.{var_path} = {resolved_value}")
                    return str(resolved_value) if resolved_value is not None else original

                for key, value in session_data.items():
                    if key.endswith("_result") and isinstance(value, dict) and var_path in value:
                        resolved_value = value[var_path]
                        logger.debug(f"[APIExec] 回退解析 {key}.{var_path} = {resolved_value}")
                        return str(resolved_value) if resolved_value is not None else original
                
                logger.debug(f"[APIExec] 未找到变量: {var_path}")
                return original
            
            resolved = re.sub(pattern, replace_var, value)
            
            # 如果整个字符串都是模板变量且解析后仍是原样，返回 None
            template_pattern = r'^\$\{[^}]+\}$'
            if resolved == value and re.match(template_pattern, value):
                return None
            
            return resolved
        
        elif isinstance(value, dict):
            return {k: self._resolve_template_variables(v, session_data) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._resolve_template_variables(item, session_data) for item in value]
        
        return value

    async def execute_api(
        self,
        node_config: Dict[str, Any],
        session_data: Dict[str, Any],
        user_token: str = None,
        accessible_apis: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行 API 调用
        
        Args:
            node_config: 节点配置（包含 api_id, api_endpoint, method, parameters）
            session_data: 会话数据（累积的表单数据）
            user_token: 用户认证 token
            accessible_apis: 用户可访问的 API 列表
        
        Returns:
            API 调用结果
        """
        api_id = node_config.get("api_id")
        api_endpoint = node_config.get("api_endpoint")
        method = node_config.get("method", "GET").upper()
        parameters = node_config.get("parameters", {})
        
        logger.info(f"🔍 [APIExec] 执行 API 调用: api_id={api_id}, endpoint={api_endpoint}, method={method}")
        logger.debug(f"📦 [APIExec] 会话数据: {json.dumps(session_data, ensure_ascii=False, default=str)[:500]}")
        logger.debug(f"📝 [APIExec] 原始参数: {json.dumps(parameters, ensure_ascii=False, default=str)}")
        
        # 1. 解析模板变量
        resolved_params = self._resolve_template_variables(parameters, session_data)
        logger.debug(f"🔄 [APIExec] 解析后参数: {json.dumps(resolved_params, ensure_ascii=False, default=str)}")
        
        # 过滤掉未解析的模板变量（值为 None 或仍包含 ${} 的）
        if isinstance(resolved_params, dict):
            resolved_params = {
                k: v for k, v in resolved_params.items()
                if v is not None and not (isinstance(v, str) and "${" in v)
            }
        
        # 2. 查找 API 路由配置
        route_config = self._find_api_route(api_id=api_id, endpoint=api_endpoint, method=method)
        
        if not route_config:
            # 如果在 accessible_apis 中查找
            if accessible_apis:
                for api in accessible_apis:
                    if api.get("id") == api_id or api.get("api_id") == api_id:
                        route_config = {
                            "endpoint": api.get("endpoint") or api.get("path"),
                            "method": api.get("method", "GET").upper()
                        }
                        break
                    if api.get("endpoint") == api_endpoint or api.get("path") == api_endpoint:
                        route_config = {
                            "endpoint": api.get("endpoint") or api.get("path"),
                            "method": api.get("method", "GET").upper()
                        }
                        break
        
        if not route_config:
            logger.warning(f"⚠️ [APIExec] 未找到 API 路由配置，使用节点配置")
            route_config = {
                "endpoint": api_endpoint,
                "method": method
            }
        
        # 3. 准备请求参数
        endpoint = route_config.get("endpoint", api_endpoint)
        http_method = route_config.get("method", method).upper()
        route_parameters_config = route_config.get("parameters_config") or []
        
        # 合并参数：仅使用配置中声明的参数（避免把上下文全部塞进 query/body）
        request_params = {**resolved_params}
        path_param_keys = set(re.findall(r"\{(\w+)\}", endpoint or ""))
        route_param_keys = set()
        if isinstance(route_parameters_config, list):
            for item in route_parameters_config:
                if isinstance(item, dict) and item.get("name"):
                    route_param_keys.add(item["name"])
        allowed_keys = set(request_params.keys()) | path_param_keys | route_param_keys

        # 优先从会话数据补齐声明参数，确保表单字段可透传到业务 API
        for key in allowed_keys:
            if key in request_params and request_params.get(key) is not None:
                continue
            value = session_data.get(key)
            if value is None:
                continue
            if isinstance(value, str) and "${" in value:
                continue
            request_params[key] = value

        # 🔧 回退：仅为已声明的参数补充值（不扩展参数集合）
        def _merge_result_dict(result: Any) -> None:
            if not isinstance(result, dict):
                return
            for k, v in result.items():
                if k not in allowed_keys:
                    continue
                if k in request_params and request_params.get(k) is not None:
                    continue
                if v is None:
                    continue
                if isinstance(v, str) and "${" in v:
                    continue
                request_params[k] = v

        _merge_result_dict(session_data.get("last_api_result"))
        for key, value in session_data.items():
            if key.endswith("_result"):
                _merge_result_dict(value)
        
        # 4. 替换路径参数
        actual_endpoint = self._substitute_path_params(endpoint, request_params)
        
        # 检查是否还有未替换的路径参数
        if "{" in actual_endpoint:
            logger.warning(f"⚠️ [APIExec] 路径中仍有未替换的参数: {actual_endpoint}")
            # 尝试从会话数据中查找
            for key, value in session_data.items():
                if f"{{{key}}}" in actual_endpoint:
                    actual_endpoint = actual_endpoint.replace(f"{{{key}}}", str(value))
        
        logger.info(f"🚀 [APIExec] 准备调用: {http_method} {actual_endpoint}")
        logger.debug(f"📋 [APIExec] 最终请求参数: {json.dumps(request_params, ensure_ascii=False, default=str)}")
        
        # 5. 执行 HTTP 请求
        try:
            result = await self._make_http_request(
                method=http_method,
                endpoint=actual_endpoint,
                params=request_params,
                token=user_token
            )

            # 文件型政策接口兜底补齐分支字段，避免工作流条件因缺少字段提前结束
            if isinstance(result, dict) and result.get("media_kind") in {"pdf", "file"}:
                if api_id == "refund_policy_api":
                    result.setdefault("can_refund", True)
                    result.setdefault("refund_rate", 0.1)
                    result.setdefault("policy_description", "详见退票政策文件")
                    if request_params.get("ticket_id"):
                        result.setdefault("ticket_id", request_params.get("ticket_id"))
                elif api_id == "change_policy_api":
                    result.setdefault("can_change", True)
                    result.setdefault("change_fee_rate", 0.05)
                    result.setdefault("policy_description", "详见改签政策文件")
            
            logger.info(f"✅ [APIExec] API 调用成功: {http_method} {actual_endpoint}")
            logger.debug(f"📥 [APIExec] 响应数据: {json.dumps(result, ensure_ascii=False, default=str)[:500]}")
            return {
                "success": True,
                "api_id": api_id,
                "endpoint": actual_endpoint,
                "method": http_method,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"❌ [APIExec] API 调用失败: {e}")
            return {
                "success": False,
                "api_id": api_id,
                "endpoint": actual_endpoint,
                "method": http_method,
                "error": str(e),
                "data": None
            }
    
    async def _make_http_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any],
        token: str = None
    ) -> Dict[str, Any]:
        """
        执行实际的 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 请求参数
            token: 认证 token
        
        Returns:
            API 响应数据
        """
        client = await self._get_http_client()
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            # 允许文件流响应（PDF/图片/音频等）
            "Accept": "*/*"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # 添加详细日志
        logger.info(f"🌐 [APIExec] HTTP 请求: {method} {endpoint}")
        logger.debug(f"📤 [APIExec] 请求头: {json.dumps({k: v[:20] + '...' if k == 'Authorization' and len(v) > 20 else v for k, v in headers.items()}, ensure_ascii=False)}")
        logger.debug(f"📤 [APIExec] 请求参数: {json.dumps(params, ensure_ascii=False, default=str)}")
        
        # 根据方法类型发送请求
        try:
            if method == "GET":
                response = await client.get(endpoint, params=params, headers=headers)
            elif method == "POST":
                logger.debug(f"[APIExec] POST 请求体: {json.dumps(params, ensure_ascii=False, default=str)}")
                response = await client.post(endpoint, json=params, headers=headers)
            elif method == "PUT":
                logger.debug(f"[APIExec] PUT 请求体: {json.dumps(params, ensure_ascii=False, default=str)}")
                response = await client.put(endpoint, json=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(endpoint, params=params, headers=headers)
            elif method == "PATCH":
                logger.debug(f"[APIExec] PATCH 请求体: {json.dumps(params, ensure_ascii=False, default=str)}")
                response = await client.patch(endpoint, json=params, headers=headers)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
            
            # 记录响应
            logger.info(f"📨 [APIExec] 响应状态码: {response.status_code}")
            logger.debug(f"📨 [APIExec] 响应头: {dict(response.headers)}")
            content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            
            # 解析响应
            if response.status_code >= 400:
                if self._is_json_content_type(content_type):
                    try:
                        error_json = response.json()
                        error_text = json.dumps(error_json, ensure_ascii=False, default=str)
                    except Exception:
                        error_text = response.content.decode("utf-8", errors="replace")
                else:
                    error_text = response.content.decode("utf-8", errors="replace")
                logger.error(f"❌ [APIExec] HTTP 请求失败: {response.status_code} - {error_text[:200]}")
                raise Exception(f"HTTP {response.status_code}: {error_text[:200]}")
            
            if self._is_json_content_type(content_type):
                # JSON 响应
                response_data = response.json()
                logger.debug(f"📥 [APIExec] 响应数据: {json.dumps(response_data, ensure_ascii=False, default=str)[:1000]}")
                return response_data

            if content_type.startswith("text/"):
                # 文本响应（避免直接用 response.text 触发编码异常）
                response_text = response.content.decode("utf-8", errors="replace")
                logger.debug(f"📄 [APIExec] 响应文本: {response_text[:500]}")
                return {"raw_response": response_text}

            # 二进制/媒体响应（PDF、图片、音频等）
            binary_payload = self._build_binary_payload(response=response, content_type=content_type)
            logger.debug(f"📦 [APIExec] 二进制响应元数据: {json.dumps(binary_payload, ensure_ascii=False, default=str)}")
            return binary_payload
                
        except httpx.RequestError as e:
            logger.error(f"❌ [APIExec] HTTP 请求异常: {e}")
            raise

    def _is_json_content_type(self, content_type: str) -> bool:
        """判断是否 JSON 响应类型。"""
        if not content_type:
            return False
        return content_type == "application/json" or content_type.endswith("+json")

    def _build_binary_payload(self, response: httpx.Response, content_type: str) -> Dict[str, Any]:
        """将二进制响应转换为流程可消费的元数据。"""
        request_url = response.request.url
        query = request_url.query.decode("utf-8", errors="ignore") if isinstance(request_url.query, (bytes, bytearray)) else str(request_url.query or "")
        relative_url = request_url.path + (f"?{query}" if query else "")
        content_disposition = response.headers.get("content-disposition", "")
        filename = None
        match = re.search(r"filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?", content_disposition, re.IGNORECASE)
        if match:
            filename = match.group(1) or match.group(2)

        media_kind = "file"
        if content_type == "application/pdf":
            media_kind = "pdf"
        elif content_type.startswith("image/"):
            media_kind = "image"
        elif content_type.startswith("audio/"):
            media_kind = "audio"

        return {
            "file_url": relative_url,
            "url": relative_url,
            "content_type": content_type,
            "file_name": filename or "",
            "file_size": len(response.content),
            "media_kind": media_kind,
            "message": "文件已就绪"
        }


# 全局实例
api_executor_service = APIExecutorService()
