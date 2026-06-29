"""
AMIS Schema 规则生成器 V3 - Slot-Filling 架构

核心思想：
- 规则生成器：提供 AMIS 模板骨架（100% 正确）
- AI 模型：只填充动态内容（标题、描述、字段标签等）

架构改进：
1. 使用策略模式处理不同节点类型，避免 if-else 树
2. 使用 Jinja2 模板引擎管理 AMIS Schema 模板
3. 使用 Slot-Filling 让 AI 填充动态文案
4. 支持模板热更新和配置外部化

优势：
- 合规性：规则保证 AMIS 语法 100% 正确
- 符合意图性：AI 提供个性化文案，提升用户体验
- 性能：AI 只生成 200 tokens（vs 1500 tokens），推理时间减少 90%+
- 易于扩展：新增节点类型只需添加新策略
- 易于维护：每个策略独立，职责单一
- 易于测试：策略可以单独测试
"""
import random
import re
from typing import Dict, List, Any, Optional

from app.core.logging_config import get_logger
from app.services.schema_strategies import (
    NodeStrategy,
    ApiCallStrategy,
    StartNodeStrategy,
    EndNodeStrategy,
    ConditionNodeStrategy,
    NotificationNodeStrategy,
    ChartStrategy
)
from app.services.schema_templates import TemplateLoader
from app.services.slot_filling_service import slot_filling_service

logger = get_logger(__name__)


class AmisSchemaGenerator:
    """AMIS Schema 规则生成器 V3 - Slot-Filling 架构"""
    
    def __init__(self):
        # 模板加载器
        self.template_loader = TemplateLoader()
        
        # 槽填充服务
        self.slot_filling_service = slot_filling_service
        
        # 注册所有策略
        self.strategies: List[NodeStrategy] = [
            StartNodeStrategy(self.template_loader),
            EndNodeStrategy(self.template_loader),
            ConditionNodeStrategy(self.template_loader),
            NotificationNodeStrategy(self.template_loader),
            ChartStrategy(self.template_loader),  # 图表策略（在 API Call 之前）
            ApiCallStrategy(self.template_loader),  # 放最后，作为默认策略
        ]
        
        # 配置
        self.form_modes = ["normal", "horizontal", "inline"]
        self.label_aligns = ["right", "left"]
        
        logger.info(f"AMIS Schema 生成器初始化完成（Slot-Filling 架构），已注册 {len(self.strategies)} 个策略")

    @staticmethod
    def _resolve_workflow_id(workflow: Dict[str, Any]) -> str:
        """兼容 workflow.id 与 workflow.workflow_id。"""
        return workflow.get("id") or workflow.get("workflow_id") or ""

    def _normalize_workflow_for_template(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """保证模板渲染时 workflow.id 一定可读。"""
        workflow_id = self._resolve_workflow_id(workflow)
        if workflow.get("id") or not workflow_id:
            return workflow
        normalized = dict(workflow)
        normalized["id"] = workflow_id
        return normalized
    
    def generate_workflow_entry_form(
        self, 
        workflow: Dict[str, Any], 
        first_node: Dict[str, Any],
        context_data: Dict[str, Any] = None,
        user_instruction: str = "",
        slot_values: Dict[str, Any] = None  # 🔥 新增：AI 输出的槽位值
    ) -> Dict[str, Any]:
        """
        生成工作流入口表单（Slot-Filling 架构）
        
        流程：
        1. 规则生成器提取表单字段
        2. 根据节点类型选择模板（GET 用 wizard，POST 用 form）
        3. 使用 AI 输出的槽位值（如果提供）
        4. 合并生成最终 Schema
        
        Args:
            workflow: 工作流定义
            first_node: 第一个节点
            context_data: 上下文数据
            user_instruction: 用户指令
            slot_values: AI 输出的槽位值（可选）
        """
        logger.info(f"📝 生成工作流入口表单（Slot-Filling）: {workflow.get('name')}")
        
        try:
            # 🔥 检查第一个节点的类型
            node_type = first_node.get("type", "form")
            node_config = first_node.get("config", {})
            http_method = node_config.get("method", "POST").upper() if node_type == "api_call" else "POST"
            
            logger.info(f"第一个节点类型: {node_type}, HTTP方法: {http_method}")
            
            # 🔥 如果是 GET 类型的 api_call 节点，使用 wizard 模板
            if node_type == "api_call" and http_method == "GET":
                logger.info("使用 Wizard 模板生成入口界面")
                return self._generate_wizard_entry(workflow, first_node, context_data, slot_values)
            
            # 否则使用 form 模板
            logger.info("使用 Form 模板生成入口界面")
            
            # 1. 提取表单字段（规则）
            form_fields = self._extract_form_fields_from_node(first_node, context_data)
            
            # 2. 获取 AI 指令
            ai_instructions = first_node.get("ai_instructions", {})
            user_message = ai_instructions.get("user_message", "")
            
            # 3. 🔥 如果没有 AI 输出的槽位值，使用默认值
            if not slot_values:
                logger.warning("⚠️ 未提供 AI 槽位值，使用默认值")
                slot_values = {
                    "page_title": workflow.get("name", "")[:6],
                    "user_message": user_message or f"请填写{workflow.get('name', '')}所需信息",
                    "submit_button_text": "提交",
                    "reset_button_text": "重置"
                }
            else:
                logger.info(f"使用 AI 输出的槽位值: {list(slot_values.keys())}")
            
            # 4. 🔥 将字段标签从 slot_values 应用到 form_fields
            for field in form_fields:
                field_label_key = f"field_label_{field['name']}"
                if field_label_key in slot_values:
                    old_label = field.get("label")
                    if field.get("label_source") == "api_description":
                        continue
                    ai_label = slot_values[field_label_key]
                    if not self._should_override_field_label(old_label, ai_label):
                        continue
                    field['label'] = ai_label
                    # Keep placeholder in sync when it was generated from label.
                    placeholder = field.get("placeholder")
                    if placeholder and isinstance(old_label, str):
                        if placeholder in (f"请输入{old_label}", f"请选择{old_label}"):
                            field["placeholder"] = f"请输入{field['label']}"
                    logger.debug(f"应用 AI 标签: {field['name']} -> {field['label']}")
            
            # 5. 🔥 提取 API URL 和方法（如果有）
            api_url = None
            api_method = None
            if slot_values:
                if 'api_url' in slot_values:
                    api_url = slot_values['api_url']
                    logger.info(f"使用 AI 输出的 api_url: {api_url}")
                if 'api_method' in slot_values:
                    api_method = slot_values['api_method']
                    logger.info(f"使用 AI 输出的 api_method: {api_method}")
            
            template_values = {
                "workflow": workflow,
                "node": first_node,
                "form_fields": form_fields,
                "user_message": user_message,
                "form_mode": random.choice(self.form_modes),
                "label_align": random.choice(self.label_aligns),
                "api_url": api_url,  # 🔥 传递 API URL
                "api_method": api_method,  # 🔥 传递 API 方法
                **slot_values  # AI 填充的槽位值
            }
            
            # 6. 渲染最终 Schema
            schema = self.template_loader.render("workflow_entry.json.j2", **template_values)
            
            logger.info(f"✅ 工作流入口表单生成完成（含 {len(slot_values)} 个 AI 槽位）")
            return schema
            
        except Exception as e:
            logger.error(f"❌ 生成工作流入口表单失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_schema(str(e))
    
    def generate_workflow_step_form(
        self, 
        workflow: Dict[str, Any], 
        node: Dict[str, Any],
        context_data: Dict[str, Any] = None,
        user_instruction: str = "",
        slot_values: Dict[str, Any] = None  # 🔥 新增：AI 输出的槽位值
    ) -> Dict[str, Any]:
        """
        生成工作流步骤界面（Slot-Filling 架构）
        
        使用策略模式选择合适的策略，策略内部使用 Slot-Filling
        
        Args:
            workflow: 工作流定义
            node: 当前节点
            context_data: 上下文数据
            user_instruction: 用户指令
            slot_values: AI 输出的槽位值（可选）
        """
        logger.info(f"📝 生成工作流步骤界面（Slot-Filling）: {node.get('name')}")
        
        try:
            # 选择策略
            strategy = self._select_strategy(node)
            
            if not strategy:
                logger.warning(f"⚠️ 未找到合适的策略处理节点: {node.get('type')}")
                return self._create_error_schema(f"不支持的节点类型: {node.get('type')}")
            
            # 🔥 如果有槽位值，记录日志
            if slot_values:
                logger.info(f"使用 AI 输出的槽位值: {list(slot_values.keys())}")
                if 'api_url' in slot_values:
                    logger.info(f"  api_url: {slot_values['api_url']}")
                if 'api_method' in slot_values:
                    logger.info(f"  api_method: {slot_values['api_method']}")
            
            # 使用策略生成 Schema（策略内部会调用 Slot-Filling）
            schema = strategy.generate_schema(
                workflow, 
                node, 
                context_data,
                user_instruction=user_instruction,
                slot_values=slot_values  # 🔥 传递槽位值给策略
            )
            
            logger.info(f"✅ 工作流步骤界面生成完成")
            return schema
            
        except Exception as e:
            logger.error(f"❌ 生成工作流步骤界面失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_schema(str(e))
    
    def generate_direct_api_form(self, api: Dict[str, Any], slot_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成直接 API 调用表单
        
        使用模板引擎渲染
        
        Args:
            api: API 定义
            slot_values: AI 输出的槽位值（可选）
        """
        logger.info(f"📝 生成直接 API 表单: {api.get('description', api.get('desc'))}")
        
        try:
            import json
            request_fields = api.get("request", api.get("parameters", []))
            response_fields = api.get("response_fields", api.get("responseFields", []))
            handler_cfg: Any = api.get("handler_config") or api.get("handlerConfig") or {}
            if not handler_cfg and isinstance(api.get("handler"), dict):
                handler_cfg = api.get("handler", {}).get("config") or {}
            if isinstance(handler_cfg, str):
                try:
                    handler_cfg = json.loads(handler_cfg)
                except Exception:
                    handler_cfg = {}

            entity_name = None
            if isinstance(handler_cfg, dict):
                entity_name = (
                    handler_cfg.get("entity")
                    or handler_cfg.get("entity_name")
                    or handler_cfg.get("entityName")
                )
            if not entity_name:
                entity_name = api.get("entity") or api.get("entity_name")
            if not entity_name:
                endpoint = api.get("endpoint", api.get("path", "")) or ""
                if isinstance(endpoint, str):
                    import re
                    match = re.match(r"^/api/v1/([a-zA-Z_]+)$", endpoint)
                    if match:
                        candidate = match.group(1)
                        if candidate.endswith("s") and len(candidate) > 1:
                            candidate = candidate[:-1]
                        entity_name = candidate

            form_fields = [
                self._convert_field_to_form_config(f, entity_name=entity_name)
                for f in request_fields
            ]
            api_desc = api.get("description", api.get("desc", "")) or ""

            def _has_cn(value: Any) -> bool:
                if not isinstance(value, str) or not value:
                    return False
                return any("\u4e00" <= ch <= "\u9fff" for ch in value)

            # Build user-facing field labels for response rendering (entity metadata + common meta fields).
            field_label_map: Dict[str, str] = {
                "total": "总数",
                "page": "页码",
                "limit": "每页数量",
                "has_next": "是否有下一页",
                "has_prev": "是否有上一页"
            }
            hidden_fields: List[str] = [
                "id",
                "created_at",
                "updated_at",
                "request_id",
                "api_info"
            ]
            handler_type = ""
            try:
                handler_type = self._extract_handler_type(api, handler_cfg)
                from app.services.entity_service import entity_service
                if entity_name:
                    field_label_map.update(entity_service.get_field_label_map(entity_name=entity_name))
                else:
                    field_label_map.update(entity_service.get_field_label_map())
            except Exception:
                pass

            # Merge AI-generated response labels when provided.
            if isinstance(slot_values, dict):
                for key, value in slot_values.items():
                    if not isinstance(key, str) or not key.startswith("resp_label_"):
                        continue
                    if not isinstance(value, str) or not value.strip():
                        continue
                    field_name = key[len("resp_label_"):]
                    if not field_name:
                        continue
                    existing_label = field_label_map.get(field_name)
                    if not existing_label or not _has_cn(existing_label):
                        field_label_map[field_name] = value.strip()

            # Prefer static list columns when handler config exposes fields.
            list_columns: List[Dict[str, str]] = []
            allowed_fields = None
            if isinstance(handler_cfg, dict):
                allowed_fields = (
                    handler_cfg.get("allowed_fields")
                    or handler_cfg.get("fields")
                    or handler_cfg.get("select_fields")
                )
            if not allowed_fields and entity_name:
                try:
                    from app.services.entity_service import entity_service
                    entity_resp = entity_service.get_entity_by_name(entity_name)
                    entity_data = (entity_resp or {}).get("data", {}).get("entity")
                    fields = None
                    if hasattr(entity_data, "fields"):
                        fields = entity_data.fields
                    elif isinstance(entity_data, dict):
                        fields = entity_data.get("fields")
                    if isinstance(fields, list):
                        allowed_fields = [f.name for f in fields if getattr(f, "name", None)]
                except Exception:
                    allowed_fields = None
            if isinstance(allowed_fields, list):
                for field_name in allowed_fields:
                    if not isinstance(field_name, str) or field_name in hidden_fields:
                        continue
                    list_columns.append({
                        "name": field_name,
                        "label": field_label_map.get(field_name, field_name),
                        "type": "text"
                    })
            if not list_columns:
                list_columns = None
            
            # 如果没有 AI 槽位值，使用默认值
            if not slot_values:
                logger.warning("⚠️ 未提供 AI 槽位值，使用默认值")
                slot_values = {
                    "page_title": api_desc[:6] if api_desc else "API调用",
                    "user_message": f"请填写{api_desc}所需信息" if api_desc else "请填写信息",
                    "submit_button_text": "提交"
                }
            
            api_url = api.get('endpoint', api.get('path', ''))
            api_method = api.get('method', 'GET')

            # Prefer AI-normalized api_url/api_method when provided (e.g. ${param} normalization).
            if isinstance(slot_values, dict):
                if isinstance(slot_values.get("api_url"), str) and slot_values.get("api_url"):
                    api_url = slot_values["api_url"]
                if isinstance(slot_values.get("api_method"), str) and slot_values.get("api_method"):
                    api_method = slot_values["api_method"]
            api_method = (api_method or "GET").upper()
            
            import json
            label_map_json = json.dumps(field_label_map, ensure_ascii=False)
            hidden_json = json.dumps(hidden_fields, ensure_ascii=False)

            api_adaptor = (
                "var labelMap = " + label_map_json + "; "
                "var hiddenKeys = " + hidden_json + "; "
                "function _isHidden(k){ return hiddenKeys && hiddenKeys.indexOf(k) >= 0; } "
                "var raw = payload; var safeRaw = raw; try { safeRaw = JSON.parse(JSON.stringify(raw)); } catch (e) { safeRaw = raw; } "
                "var ok = false; if (raw && typeof raw === 'object') { ok = (raw.code === 200) || (raw.status === 0) || (raw.success === true); } "
                "var status = ok ? 0 : ((raw && typeof raw === 'object' && raw.status != null) ? raw.status : ((raw && typeof raw === 'object' && raw.code != null) ? raw.code : 1)); "
                "var msg = (raw && typeof raw === 'object') ? (raw.message || raw.msg || '') : ''; "
                "var hasCn = msg && /[\\u4e00-\\u9fff]/.test(msg); "
                "var data = (raw && typeof raw === 'object' && 'data' in raw) ? raw.data : raw; "
                "var guard = 0; "
                "while (data && typeof data === 'object' && 'data' in data && guard < 3) { "
                "  if (data.items || data.list || data.records || data.rows) { break; } "
                "  data = data.data; guard++; "
                "} "
                "var out = data; if (out == null || typeof out !== 'object') { out = { value: out }; } "
                "out.__api_code__ = (raw && typeof raw === 'object' && raw.code != null) ? raw.code : null; "
                "out.__api_message__ = (ok ? (hasCn ? msg : '请求成功') : (hasCn ? msg : '请求失败')); "
                "var kv = []; try { "
                "var keys = Object.keys(out).filter(function(k){ return k && k.indexOf('__api_') !== 0 && !_isHidden(k); }); keys.sort(); "
                "for (var i=0; i<keys.length; i++) { "
                "var k = keys[i]; var v = out[k]; if (k === 'items' && Array.isArray(v)) { continue; } "
                "var s = ''; if (v == null) { s = ''; } else if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') { s = String(v); } else { continue; } "
                "if (s && s.length > 200) { s = s.slice(0, 200) + '...'; } "
                "var label = (labelMap && labelMap[k]) ? labelMap[k] : k; "
                "kv.push({ key: k, label: label, value: s }); } "
                "} catch (e) {} out.__api_kv__ = kv; "
                "var itemsFlat = []; var itemsRows = []; var itemsColumns = []; var itemsTotal = 0; var itemsTruncated = false; try { "
                "var items = (out && typeof out === 'object') ? out.items : null; if (Array.isArray(items)) { "
                "itemsTotal = items.length; var maxItems = 10; var maxKeys = 12; var maxCols = 8; var colKeys = []; "
                "if (items.length > 0 && items[0] && typeof items[0] === 'object') { try { colKeys = Object.keys(items[0]); } catch (e) { colKeys = []; } } "
                "colKeys.sort(); colKeys = colKeys.filter(function(k){ return !_isHidden(k); }); if (colKeys.length > maxCols) { colKeys = colKeys.slice(0, maxCols); } "
                "itemsColumns = colKeys.map(function(k){ return { name: k, label: (labelMap && labelMap[k]) ? labelMap[k] : k, type: 'text' }; }); "
                "for (var ii=0; ii<items.length && ii<maxItems; ii++) { var it = items[ii] || {}; var row = {}; "
                "for (var ci=0; ci<colKeys.length; ci++) { var ck = colKeys[ci]; var vv = it[ck]; "
                "if (vv == null) { row[ck] = ''; } else if (typeof vv === 'string' || typeof vv === 'number' || typeof vv === 'boolean') { row[ck] = String(vv); } "
                "else { try { row[ck] = JSON.stringify(vv); } catch (e) { row[ck] = String(vv); } } "
                "if (row[ck] && row[ck].length > 200) { row[ck] = row[ck].slice(0, 200) + '...'; } } "
                "itemsRows.push(row); "
                "var keys2 = []; try { keys2 = Object.keys(it); } catch (e) { keys2 = []; } keys2.sort(); var keyCount = 0; "
                "for (var kk=0; kk<keys2.length && keyCount<maxKeys; kk++) { var k2 = keys2[kk]; if (_isHidden(k2)) { continue; } var v2 = it[k2]; "
                "var s2 = ''; if (v2 == null) { s2 = ''; } else if (typeof v2 === 'string' || typeof v2 === 'number' || typeof v2 === 'boolean') { s2 = String(v2); } "
                "else { try { s2 = JSON.stringify(v2); } catch (e) { s2 = String(v2); } } "
                "if (s2 && s2.length > 200) { s2 = s2.slice(0, 200) + '...'; } "
                "var label2 = (labelMap && labelMap[k2]) ? labelMap[k2] : k2; itemsFlat.push({ index: ii + 1, key: k2, label: label2, value: s2 }); keyCount++; } } "
                "if (items.length > maxItems) { itemsTruncated = true; } } } catch (e) {} "
                "out.__api_items_flat__ = itemsFlat; out.__api_items_rows__ = itemsRows; out.__api_items_columns__ = itemsColumns; "
                "out.__api_items_total__ = itemsTotal; out.__api_items_truncated__ = itemsTruncated; "
                "var pdfUrl = ''; try { "
                "var candidates = ['pdf_url','policy_pdf_url','file_url','document_url','url']; "
                "for (var pi=0; pi<candidates.length; pi++) { var ck = candidates[pi]; var cv = out[ck]; "
                "if (typeof cv === 'string' && /\\.pdf(\\?|$)/i.test(cv)) { pdfUrl = cv; break; } } "
                "if (!pdfUrl) { var outKeys = Object.keys(out || {}); "
                "for (var pj=0; pj<outKeys.length; pj++) { var k = outKeys[pj]; var v = out[k]; "
                "if (typeof v === 'string' && /\\.pdf(\\?|$)/i.test(v)) { pdfUrl = v; break; } } } "
                "} catch (e) {} "
                "out.__api_pdf_url__ = pdfUrl; "
                "out.__api_pdf_preview_url__ = pdfUrl ? (pdfUrl + (pdfUrl.indexOf('?') >= 0 ? '&' : '?') + 'download=false') : ''; "
                "var imageUrl = ''; try { "
                "var imageCandidates = ['image_url','img_url','thumbnail_url','cover_url','picture_url','avatar_url','url']; "
                "for (var ii2=0; ii2<imageCandidates.length; ii2++) { var ik = imageCandidates[ii2]; var iv = out[ik]; "
                "if (typeof iv === 'string' && /\\.(png|jpg|jpeg|gif|webp|bmp|svg)(\\?|$)/i.test(iv)) { imageUrl = iv; break; } } "
                "if (!imageUrl) { var imageKeys = Object.keys(out || {}); "
                "for (var ij=0; ij<imageKeys.length; ij++) { var kk2 = imageKeys[ij]; var vv2 = out[kk2]; "
                "if (typeof vv2 === 'string' && /\\.(png|jpg|jpeg|gif|webp|bmp|svg)(\\?|$)/i.test(vv2)) { imageUrl = vv2; break; } } } "
                "} catch (e) {} "
                "out.__api_image_url__ = imageUrl; "
                "out.__api_image_preview_url__ = imageUrl ? (imageUrl + (imageUrl.indexOf('?') >= 0 ? '&' : '?') + 'download=false') : ''; "
                "var audioUrl = ''; try { "
                "var audioCandidates = ['audio_url','voice_url','sound_url','media_url','file_url','url']; "
                "for (var ai=0; ai<audioCandidates.length; ai++) { var ak = audioCandidates[ai]; var av = out[ak]; "
                "if (typeof av === 'string' && /\\.(mp3|wav|ogg|m4a|aac|flac)(\\?|$)/i.test(av)) { audioUrl = av; break; } } "
                "if (!audioUrl) { var audioKeys = Object.keys(out || {}); "
                "for (var aj=0; aj<audioKeys.length; aj++) { var ak2 = audioKeys[aj]; var av2 = out[ak2]; "
                "if (typeof av2 === 'string' && /\\.(mp3|wav|ogg|m4a|aac|flac)(\\?|$)/i.test(av2)) { audioUrl = av2; break; } } } "
                "} catch (e) {} "
                "out.__api_audio_url__ = audioUrl; "
                "out.__api_audio_preview_url__ = audioUrl ? (audioUrl + (audioUrl.indexOf('?') >= 0 ? '&' : '?') + 'download=false') : ''; "
                "return {status: status, msg: msg, data: out};"
            )

            media_kind = self._detect_media_kind(
                handler_type=handler_type,
                handler_config=handler_cfg,
                api_url=api_url,
                api_desc=api_desc,
            )
            use_chart_view_template = self._should_use_chart_view_template(
                api_method=api_method,
                request_fields=request_fields,
                api_desc=api_desc,
                response_fields=response_fields,
                handler_type=handler_type,
                handler_config=handler_cfg,
            )
            use_media_view_template = self._should_use_media_view_template(
                api_method=api_method,
                form_fields=form_fields,
                handler_type=handler_type,
                handler_config=handler_cfg,
                media_kind=media_kind,
            )

            if use_chart_view_template:
                schema = self.template_loader.render(
                    "api_chart_view.json.j2",
                    api=api,
                    api_url=api_url,
                    api_method=api_method,
                    slot_values=slot_values,
                    api_adaptor=api_adaptor,
                )
                logger.info("Direct API schema rendered with chart view template")
                return schema

            if use_media_view_template:
                media_direct = self._is_media_handler(handler_type, handler_cfg)
                schema = self.template_loader.render(
                    "api_media_view.json.j2",
                    api=api,
                    api_url=api_url,
                    api_method=api_method,
                    slot_values=slot_values,
                    api_adaptor=api_adaptor,
                    media_direct=media_direct,
                    media_kind=media_kind or "file",
                    media_url=api_url,
                    media_preview_url=self._build_media_preview_url(api_url, media_kind or "file"),
                )
                logger.info("Direct API schema rendered with media view template")
                return schema

            schema = self.template_loader.render(
                "api_form.json.j2",
                api=api,
                api_url=api_url,
                api_method=api_method,
                form_fields=form_fields,
                form_mode=random.choice(self.form_modes),
                label_align=random.choice(self.label_aligns),
                slot_values=slot_values,
                field_label_map=field_label_map,
                hidden_fields=hidden_fields,
                api_adaptor=api_adaptor,
                list_columns=list_columns
            )
            
            logger.info(f"✅ 直接 API 表单生成完成")
            return schema
            
        except Exception as e:
            logger.error(f"❌ 生成直接 API 表单失败: {str(e)}")
            return self._create_error_schema(str(e))

    def _extract_handler_type(self, api: Dict[str, Any], handler_cfg: Any) -> str:
        handler_type = api.get("handler_type") or api.get("handlerType") or ""
        if not handler_type and isinstance(api.get("handler"), dict):
            handler_type = api.get("handler", {}).get("type") or ""
        if isinstance(handler_type, str) and handler_type.strip():
            return handler_type.strip().lower()

        if not isinstance(handler_cfg, dict):
            return ""
        if any(k in handler_cfg for k in ("image_source", "image_identifier", "default_image")):
            return "image_display"
        if any(k in handler_cfg for k in ("file_root", "disposition", "security_check")):
            return "file_download"
        if any(k in handler_cfg for k in ("media_root", "supported_formats")):
            return "media_streaming"
        return ""

    def _is_media_handler(self, handler_type: str, handler_cfg: Any) -> bool:
        if isinstance(handler_type, str) and handler_type.lower() in {"image_display", "file_download", "media_streaming"}:
            return True
        if isinstance(handler_cfg, dict):
            if any(k in handler_cfg for k in ("image_source", "image_identifier")):
                return True
            if any(k in handler_cfg for k in ("file_root", "disposition")):
                return True
            if any(k in handler_cfg for k in ("media_root", "supported_formats")):
                return True
        return False

    def _detect_media_kind(
        self,
        handler_type: str,
        handler_config: Any,
        api_url: str,
        api_desc: str,
    ) -> Optional[str]:
        url = (api_url or "").lower()
        desc = (api_desc or "").lower()
        handler = (handler_type or "").lower()

        if handler == "image_display":
            return "image"
        if handler == "media_streaming":
            return "audio"
        if handler == "file_download":
            if ".pdf" in url or "pdf" in desc or "policy" in desc:
                return "pdf"
            if any(ext in url for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")):
                return "image"
            if any(ext in url for ext in (".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")):
                return "audio"
            return "file"

        if any(ext in url for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")):
            return "image"
        if any(ext in url for ext in (".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")):
            return "audio"
        if ".pdf" in url:
            return "pdf"

        if isinstance(handler_config, dict):
            if any(k in handler_config for k in ("image_source", "image_identifier")):
                return "image"
            if any(k in handler_config for k in ("media_root", "supported_formats")):
                return "audio"
            if any(k in handler_config for k in ("file_root", "disposition")):
                return "pdf" if ("pdf" in desc or "policy" in desc) else "file"

        keyword_map = {
            "pdf": ("pdf", "policy", "document"),
            "image": ("image", "picture", "photo", "avatar", "cover"),
            "audio": ("audio", "voice", "sound", "music"),
        }
        for kind, words in keyword_map.items():
            if any(word in desc for word in words):
                return kind
        return None

    def _should_use_media_view_template(
        self,
        api_method: str,
        form_fields: List[Dict[str, Any]],
        handler_type: str,
        handler_config: Any,
        media_kind: Optional[str],
    ) -> bool:
        if (api_method or "").upper() != "GET":
            return False
        if form_fields:
            return False
        if self._is_media_handler(handler_type, handler_config):
            return True
        return media_kind is not None

    def _build_media_preview_url(self, api_url: str, media_kind: str) -> str:
        if not isinstance(api_url, str) or not api_url:
            return ""
        if media_kind not in {"pdf", "image", "audio"}:
            return api_url
        if "download=" in api_url:
            return api_url
        connector = "&" if "?" in api_url else "?"
        return f"{api_url}{connector}download=false"

    def _should_use_chart_view_template(
        self,
        api_method: str,
        request_fields: Any,
        api_desc: str,
        response_fields: Any,
        handler_type: str,
        handler_config: Any,
    ) -> bool:
        if (api_method or "").upper() != "GET":
            return False
        if self._has_required_request_fields(request_fields):
            return False
        return self._is_chart_like_api(
            api_desc=api_desc,
            response_fields=response_fields,
            handler_type=handler_type,
            handler_config=handler_config,
        )

    def _has_required_request_fields(self, request_fields: Any) -> bool:
        if not isinstance(request_fields, list):
            return False
        for field in request_fields:
            if not isinstance(field, dict):
                continue
            required = field.get("required", False)
            if isinstance(required, str):
                required = required.strip().lower() in {"true", "1", "yes", "y"}
            if bool(required):
                return True
        return False

    def _is_chart_like_api(
        self,
        api_desc: str,
        response_fields: Any,
        handler_type: str,
        handler_config: Any,
    ) -> bool:
        if self._response_declares_chart_type(response_fields):
            return True

        desc = (api_desc or "").lower()
        if any(word in desc for word in ["统计", "分析", "图表", "趋势", "报表", "dashboard", "chart", "analytics"]):
            return True

        response_names = self._extract_response_field_names(response_fields)
        if {"categories", "values"}.issubset(response_names):
            return True
        if any(name in response_names for name in ("pie_data", "series", "trend_data", "chart_data")):
            return True

        if (handler_type or "").lower() == "script" and isinstance(handler_config, dict):
            script = str(handler_config.get("script", "")).lower()
            if any(marker in script for marker in ('"type":"chart"', '"type": "chart"', "'type':'chart'", "'type': 'chart'", "type=chart")):
                return True
            if any(word in script for word in ("pie_data", "categories", "values", "chart", "echart")):
                return True

        return False

    def _response_declares_chart_type(self, response_fields: Any) -> bool:
        def _is_chart_value(value: Any) -> bool:
            if not isinstance(value, str):
                return False
            normalized = value.strip().lower().replace(" ", "")
            return normalized in {"chart", "type=chart", "type:chart"}

        def _walk(node: Any) -> bool:
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(key, str) and key.strip().lower() == "type":
                        if _is_chart_value(value):
                            return True
                        if isinstance(value, dict):
                            for k in ("const", "default", "example"):
                                if _is_chart_value(value.get(k)):
                                    return True
                            enum_values = value.get("enum")
                            if isinstance(enum_values, list) and any(_is_chart_value(item) for item in enum_values):
                                return True
                    if _walk(value):
                        return True
            elif isinstance(node, list):
                for item in node:
                    if _walk(item):
                        return True
            return False

        return _walk(response_fields)

    def _extract_response_field_names(self, response_fields: Any) -> set[str]:
        names: set[str] = set()
        if isinstance(response_fields, list):
            for item in response_fields:
                if isinstance(item, str) and item.strip():
                    names.add(item.strip().lower())
                    continue
                if isinstance(item, dict):
                    candidate = item.get("name") or item.get("field") or item.get("key")
                    if isinstance(candidate, str) and candidate.strip():
                        names.add(candidate.strip().lower())
        elif isinstance(response_fields, dict):
            for key in response_fields.keys():
                if isinstance(key, str) and key.strip():
                    names.add(key.strip().lower())
        return names
    
    def generate_rejection_response(
        self, 
        domain: str,
        instruction: str,
        available_actions: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成拒绝响应
        """
        logger.info(f"📝 生成拒绝响应: {instruction}")
        
        available_actions = available_actions or []
        
        message = f"抱歉，我无法理解您的指令：{instruction}"
        if available_actions:
            message += f"\n\n您可以尝试以下操作：\n" + "\n".join([f"- {action}" for action in available_actions[:5]])
        
        schema = {
            "type": "page",
            "title": "无法处理",
            "body": {
                "type": "alert",
                "level": "warning",
                "body": message,
                "showIcon": True
            }
        }
        
        logger.info(f"✅ 拒绝响应生成完成")
        return schema
    
    def _select_strategy(self, node: Dict[str, Any]) -> Optional[NodeStrategy]:
        """
        选择合适的策略处理节点
        
        Args:
            node: 节点定义
        
        Returns:
            策略实例，如果没有找到返回 None
        """
        for strategy in self.strategies:
            if strategy.can_handle(node):
                logger.debug(f"选择策略: {strategy.__class__.__name__}")
                return strategy
        return None
    
    def _generate_wizard_entry(
        self,
        workflow: Dict[str, Any],
        first_node: Dict[str, Any],
        context_data: Dict[str, Any] = None,
        slot_values: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        生成 Wizard 入口界面（用于 GET 类型的第一个节点）
        
        对于 GET 节点，需要先收集输入参数，然后用这些参数调用 initApi
        
        Args:
            workflow: 工作流定义
            first_node: 第一个节点（GET 类型的 api_call）
            context_data: 上下文数据
            slot_values: AI 输出的槽位值
        """
        logger.debug(f"🔍 _generate_wizard_entry 调用: slot_values={slot_values}")
        
        config = first_node.get("config", {})
        api_id = config.get("api_id")
        api_method = (config.get("method") or "GET").upper()
        
        # 🔥 优先使用 AI 输出的 api_url，否则使用节点配置的 api_endpoint
        api_endpoint = config.get("api_endpoint", "")
        logger.debug(f"🔍 config.api_endpoint={api_endpoint}")
        
        if slot_values and "api_url" in slot_values:
            api_endpoint = slot_values["api_url"]
            logger.info(f"使用 AI 输出的 api_url: {api_endpoint}")
        else:
            logger.warning(f"⚠️ slot_values 中没有 api_url: slot_values={slot_values}")

        # 统一将 {param} 规范为 ${param}，便于 AMIS 变量替换
        import re
        if api_endpoint:
            api_endpoint = re.sub(r'(?<!\$)\{(\w+)\}', r'${\1}', api_endpoint)

        route_meta = self._load_route_metadata(
            api_id=api_id,
            api_endpoint=api_endpoint,
            api_method=api_method
        )
        handler_type = route_meta.get("handler_type", "")
        handler_cfg = route_meta.get("handler_config", {})
        media_kind = self._detect_media_kind(
            handler_type=handler_type,
            handler_config=handler_cfg,
            api_url=api_endpoint,
            api_desc=first_node.get("description", "")
        )
        
        inputs = first_node.get("inputs", [])
        outputs = first_node.get("outputs", [])
        # ???????????????/??
        array_outputs = [o for o in outputs if o.get("type") == "array" and o.get("name")]
        list_field = (first_node.get("config", {}) or {}).get("list_field") or (first_node.get("config", {}) or {}).get("array_field")
        if not list_field and array_outputs:
            list_field = array_outputs[0].get("name")
        import json
        init_api_adaptor = (
            "var raw = payload; var safeRaw = raw; try { safeRaw = JSON.parse(JSON.stringify(raw)); } catch (e) { safeRaw = raw; } "
            "var data = payload; if (data && typeof data === 'object' && 'data' in data) { data = data.data; } "
            "if (data == null || typeof data !== 'object') { data = { value: data }; } "
            + f"var listField = {json.dumps(list_field or '')}; "
            "if (data.items && listField && data[listField] == null) { data[listField] = data.items; } "
            "var request = (api && api.data) ? api.data : {}; "
            "if (request && typeof request === 'object') { for (var k in request) { if (Object.prototype.hasOwnProperty.call(request, k)) { if (data[k] == null || data[k] === '') { data[k] = request[k]; } } } } "
            "data.__api_response__ = safeRaw; return {status: 0, msg: '', data: data};"
        )
        
        # 🔥 检查 API endpoint 是否包含参数（如 ${ticket_id}）
        has_params = bool(re.search(r'\$\{[^}]+\}', api_endpoint))

        use_media_entry = self._should_use_media_view_template(
            api_method=api_method,
            form_fields=[],
            handler_type=handler_type,
            handler_config=handler_cfg,
            media_kind=media_kind
        )
        if use_media_entry and not has_params and not inputs:
            logger.info("Media GET node matched: render direct media entry with next action")
            return self._generate_media_workflow_entry(
                workflow=workflow,
                first_node=first_node,
                api_endpoint=api_endpoint,
                slot_values=slot_values,
                handler_type=handler_type,
                handler_cfg=handler_cfg,
                media_kind=media_kind
            )
        
        logger.info(f"API endpoint: {api_endpoint}, has_params: {has_params}")
        
        # 🔥 如果 API 包含参数，或者有 inputs 定义，需要先收集参数
        if has_params or inputs:
            logger.info(f"GET 节点需要参数（has_params={has_params}, inputs={len(inputs)}），使用两步 Wizard")
            
            # 提取表单字段
            form_fields = self._extract_form_fields_from_node(first_node, context_data)
            
            # 🔥 如果没有 form_fields，从 API endpoint 中提取参数
            if not form_fields and has_params:
                # 从 ${param_name} 中提取参数名
                param_names = re.findall(r'\$\{([^}]+)\}', api_endpoint)
                for param_name in param_names:
                    form_fields.append({
                        "type": "input-text",
                        "name": param_name,
                        "label": param_name.replace("_", " ").title(),
                        "required": True,
                        "placeholder": f"请输入{param_name}"
                    })
                logger.info(f"从 API endpoint 提取了 {len(form_fields)} 个参数字段: {[f['name'] for f in form_fields]}")
            
            # 应用 AI 标签
            if slot_values:
                for field in form_fields:
                    field_label_key = f"field_label_{field['name']}"
                    if field_label_key in slot_values:
                        old_label = field.get("label")
                        if field.get("label_source") == "api_description":
                            continue
                        ai_label = slot_values[field_label_key]
                        if not self._should_override_field_label(old_label, ai_label):
                            continue
                        field['label'] = ai_label
                        placeholder = field.get("placeholder")
                        if placeholder and isinstance(old_label, str):
                            if placeholder in (f"请输入{old_label}", f"请选择{old_label}"):
                                field["placeholder"] = f"请输入{field['label']}"
                        logger.info(f"应用 AI 标签: {field['name']} -> {field['label']}")
            
            # 构建展示字段
            display_fields = []
            for output in outputs:
                display_fields.append({
                    "name": output.get("name", ""),
                    "label": output.get("label") or output.get("description") or output.get("name", ""),
                    "type": output.get("type", "string")
                })
            
            # 使用 AI 槽位值或默认值
            if not slot_values:
                slot_values = {
                    "page_title": workflow.get("name", "工作流")[:6],
                    "user_message": first_node.get("description", "请输入信息"),
                    "next_button_text": "下一步"
                }

            # 生成 initApi 请求参数（用于 GET 查询参数）
            init_api_data = {
                field.get("name"): f"${{{field.get('name')}}}"
                for field in form_fields
                if field.get("name")
            }
            hidden_output_fields = [
                {
                    "type": "hidden",
                    "name": output.get("name", ""),
                    "value": f"${{{output.get('name')}}}"
                }
                for output in outputs
                if output.get("name")
            ]
            api_request_context = {
                "method": "GET",
                "url": api_endpoint
            }
            if init_api_data:
                api_request_context["params"] = init_api_data
            
            workflow_id = self._resolve_workflow_id(workflow)

            # 生成两步 Wizard
            schema = {
                "type": "page",
                "title": slot_values.get("page_title", workflow.get("name", "")[:6]),
                "workflow_id": workflow_id,
                "current_node_id": first_node.get("id"),
                "body": {
                    "type": "wizard",
                    "mode": "horizontal",
                    "steps": [
                        {
                            "title": "输入信息",
                            "body": [
                                {
                                    "type": "alert",
                                    "level": "info",
                                    "body": slot_values.get("user_message", "请输入信息"),
                                    "showIcon": True
                                }
                            ] + [
                                {
                                    "type": field["type"],
                                    "name": field["name"],
                                    "label": field["label"],
                                    "required": field.get("required", False),
                                    "placeholder": field.get("placeholder", "")
                                }
                                for field in form_fields
                            ]
                        },
                        {
                            "title": first_node.get("description", "数据详情"),
                            "initApi": {
                                "method": "get",
                                "url": api_endpoint,
                                "data": init_api_data,
                                "adaptor": init_api_adaptor
                            },
                            "body": (
                                [
                                    {
                                        "type": "static",
                                        "label": field["label"],
                                        "name": field["name"]
                                    }
                                    for field in display_fields
                                ] + hidden_output_fields
                            ) if display_fields else ([
                                {
                                    "type": "tpl",
                                    "tpl": "<div>数据已加载</div>"
                                }
                            ] + hidden_output_fields),
                            "api": {
                                "method": "post",
                                "url": "/api/v1/workflow/state",
                                "data": {
                                    "workflow_id": workflow_id,
                                    "node_id": first_node.get("id"),
                                    "action": "next",
                                    "api_request": api_request_context,
                                    "api_response": "${__api_response__}"
                                }
                            }
                        }
                    ],
                    "actionFinishLabel": slot_values.get("next_button_text", "完成")
                }
            }
            
            logger.info(f"✅ 两步 Wizard 入口界面生成完成")
            return schema
        
        else:
            # 🔥 没有参数，直接调用 initApi
            logger.info("GET 节点无参数，直接调用 initApi")
            
            # 构建展示字段
            display_fields = []
            for output in outputs:
                display_fields.append({
                    "name": output.get("name", ""),
                    "label": output.get("label") or output.get("description") or output.get("name", ""),
                    "type": output.get("type", "string")
                })
            
            # 使用 AI 槽位值或默认值
            if not slot_values:
                slot_values = {
                    "page_title": workflow.get("name", "工作流")[:6],
                    "user_message": first_node.get("description", "正在获取数据..."),
                    "next_button_text": "下一步"
                }
            
            # 合并模板值
            template_values = {
                "workflow": self._normalize_workflow_for_template(workflow),
                "node": first_node,
                "api_url": api_endpoint,
                "display_fields": display_fields,
                "list_field": list_field,
                "init_api_adaptor": init_api_adaptor,
                **slot_values
            }
            
            # 渲染 Wizard Schema
            schema = self.template_loader.render("workflow_wizard_get.json.j2", **template_values)
            
            logger.info(f"✅ 单步 Wizard 入口界面生成完成")
            return schema
    
    def _generate_media_workflow_entry(
        self,
        workflow: Dict[str, Any],
        first_node: Dict[str, Any],
        api_endpoint: str,
        slot_values: Optional[Dict[str, Any]],
        handler_type: str,
        handler_cfg: Any,
        media_kind: Optional[str]
    ) -> Dict[str, Any]:
        """Generate workflow entry for media API without wizard, but keep next-step action."""
        if not slot_values:
            slot_values = {
                "page_title": workflow.get("name", "工作流")[:6],
                "user_message": first_node.get("description", "请查看相关文件后继续"),
                "next_button_text": "下一步",
            }

        media_direct = self._is_media_handler(handler_type, handler_cfg)
        schema = self.template_loader.render(
            "api_media_view.json.j2",
            api={"description": first_node.get("description", "")},
            api_url=api_endpoint,
            api_method="GET",
            slot_values=slot_values,
            api_adaptor="",
            media_direct=media_direct,
            media_kind=media_kind or "file",
            media_url=api_endpoint,
            media_preview_url=self._build_media_preview_url(api_endpoint, media_kind or "file"),
        )

        workflow_id = self._resolve_workflow_id(workflow)
        schema["workflow_id"] = workflow_id
        schema["current_node_id"] = first_node.get("id")

        body = schema.get("body")
        if not isinstance(body, list):
            body = [body] if body else []

        body.append(
            {
                "type": "form",
                "api": {
                    "method": "post",
                    "url": "/api/v1/workflow/state",
                    "data": {
                        "workflow_id": workflow_id,
                        "node_id": first_node.get("id"),
                        "action": "next",
                        "api_request": {
                            "method": "GET",
                            "url": api_endpoint
                        },
                        "api_response": "${__api_response__}"
                    }
                },
                "body": [],
                "actions": [
                    {
                        "type": "submit",
                        "label": slot_values.get("next_button_text", "下一步"),
                        "level": "primary"
                    }
                ]
            }
        )
        schema["body"] = body
        return schema

    def _extract_form_fields_from_node(
        self,
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        从节点配置中提取表单字段
        
        Args:
            node: 节点定义
            context_data: 上下文数据
        
        Returns:
            表单字段列表
        """
        import re
        
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        api_id = config.get("api_id")
        api_endpoint = config.get("api_endpoint")
        api_method = (config.get("method") or "POST").upper()

        fields = []
        template_pattern = re.compile(r'^\$\{(\w+)\}$')
        seen_vars = set()
        context_data = context_data or {}

        route_params = []
        route_param_map: Dict[str, Dict[str, Any]] = {}
        if node.get("type") == "api_call":
            route_params = self._load_route_parameters_config(
                api_id=api_id,
                api_endpoint=api_endpoint,
                api_method=api_method
            )
            route_param_map = {
                p.get("name"): p
                for p in route_params
                if isinstance(p, dict) and isinstance(p.get("name"), str)
            }
        
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                match = template_pattern.match(param_value)
                if match:
                    var_name = match.group(1)
                    if var_name not in seen_vars and var_name not in context_data:
                        seen_vars.add(var_name)
                        param_meta = route_param_map.get(var_name)
                        if isinstance(param_meta, dict):
                            fields.append(
                                self._build_field_config_from_param(
                                    field_name=var_name,
                                    param=param_meta,
                                    default_required=True
                                )
                            )
                        else:
                            fields.append(self._create_field_config(var_name))

        # Fallback: API 节点未配置 parameters 时，从 api_routes.parameters_config 推导表单字段
        if not fields and node.get("type") == "api_call":
            try:
                for param in route_params:
                    if not isinstance(param, dict):
                        continue

                    field_name = param.get("name")
                    if not field_name or field_name in seen_vars or field_name in context_data:
                        continue

                    fields.append(
                        self._build_field_config_from_param(
                            field_name=field_name,
                            param=param,
                            default_required=False
                        )
                    )
                    seen_vars.add(field_name)

                if fields:
                    logger.info(
                        f"从 API 路由参数配置提取到 {len(fields)} 个表单字段: {[f.get('name') for f in fields]}"
                    )
            except Exception as e:
                logger.warning(f"从 API 路由参数配置提取字段失败: {e}")

        return fields

    def _load_route_parameters_config(
        self,
        api_id: Optional[str],
        api_endpoint: Optional[str],
        api_method: str
    ) -> List[Dict[str, Any]]:
        """从 API 路由表加载参数配置。"""
        try:
            from app.core.database import SessionLocal
            from app.models.api_route import APIRouteDBModel

            db = SessionLocal()
            try:
                route = None
                if api_id:
                    route = db.query(APIRouteDBModel).filter(
                        APIRouteDBModel.api_id == api_id
                    ).first()
                if not route and api_endpoint:
                    route = db.query(APIRouteDBModel).filter(
                        APIRouteDBModel.endpoint == api_endpoint,
                        APIRouteDBModel.method == api_method
                    ).first()
                if route and isinstance(route.parameters_config, list):
                    return route.parameters_config
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"加载 API 路由参数配置失败: {e}")
        return []

    def _load_route_metadata(
        self,
        api_id: Optional[str],
        api_endpoint: Optional[str],
        api_method: str
    ) -> Dict[str, Any]:
        """Load route handler metadata for media/chart detection."""
        result: Dict[str, Any] = {"handler_type": "", "handler_config": {}}
        try:
            import json
            from app.core.database import SessionLocal
            from app.models.api_route import APIRouteDBModel

            db = SessionLocal()
            try:
                route = None
                if api_id:
                    route = db.query(APIRouteDBModel).filter(
                        APIRouteDBModel.api_id == api_id
                    ).first()
                if not route and api_endpoint:
                    route = db.query(APIRouteDBModel).filter(
                        APIRouteDBModel.endpoint == api_endpoint,
                        APIRouteDBModel.method == api_method
                    ).first()
                if not route:
                    return result

                handler_type = route.handler_type
                if handler_type is not None:
                    result["handler_type"] = str(handler_type).strip().lower()

                handler_cfg = route.handler_config
                if isinstance(handler_cfg, dict):
                    result["handler_config"] = handler_cfg
                elif isinstance(handler_cfg, str) and handler_cfg.strip():
                    try:
                        parsed_cfg = json.loads(handler_cfg)
                        if isinstance(parsed_cfg, dict):
                            result["handler_config"] = parsed_cfg
                    except Exception:
                        pass
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Load route metadata failed: {e}")
        return result

    def _build_field_config_from_param(
        self,
        field_name: str,
        param: Dict[str, Any],
        default_required: bool
    ) -> Dict[str, Any]:
        """将路由参数定义转换为 AMIS 表单字段配置。"""
        raw_type = str(param.get("type") or "string").lower()
        options = self._extract_param_options(param, field_name)

        if options:
            normalized_type = "select"
        elif raw_type in ("int", "integer", "float", "double", "number", "decimal"):
            normalized_type = "number"
        elif raw_type in ("date", "datetime", "time", "textarea", "switch", "checkbox", "radio", "select"):
            normalized_type = raw_type
        else:
            normalized_type = "string"

        field_label = self._get_field_label(field_name)
        description = param.get("description")
        if isinstance(description, str) and description.strip():
            field_label = description.strip()

        field_meta: Dict[str, Any] = {
            "name": field_name,
            "type": normalized_type,
            "label": field_label,
            "required": bool(param.get("required", default_required)),
        }
        if options:
            field_meta["options"] = options

        field = self._convert_field_to_form_config(field_meta)
        if isinstance(description, str) and description.strip():
            field["label_source"] = "api_description"
        return field

    def _extract_param_options(
        self,
        param: Dict[str, Any],
        field_name: str
    ) -> List[Dict[str, Any]]:
        """提取参数可选项，优先使用 API 配置，其次回落到实体字段 options。"""
        options = self._normalize_options(param.get("options"))
        if options:
            return options

        options = self._normalize_options(param.get("enum"))
        if options:
            return options

        validation = param.get("validation")
        if isinstance(validation, dict):
            options = self._normalize_options(validation.get("enum"))
            if options:
                return options
            options = self._normalize_options(validation.get("in"))
            if options:
                return options
            rule = validation.get("rule")
            if isinstance(rule, str):
                options = self._extract_options_from_in_rule(rule)
                if options:
                    return options
        elif isinstance(validation, str):
            options = self._extract_options_from_in_rule(validation)
            if options:
                return options

        return self._load_entity_field_options(field_name)

    def _extract_options_from_in_rule(self, rule: str) -> List[Dict[str, Any]]:
        """从 `in:a,b,c` 规则中提取选项。"""
        if not isinstance(rule, str) or "in:" not in rule:
            return []
        match = re.search(r"in:([^|]+)", rule)
        if not match:
            return []
        values = [v.strip() for v in match.group(1).split(",") if v.strip()]
        return [{"label": v, "value": v} for v in values]

    def _normalize_options(self, raw_options: Any) -> List[Dict[str, Any]]:
        """将 options 统一为 [{label, value}] 结构。"""
        if not isinstance(raw_options, list):
            return []
        normalized: List[Dict[str, Any]] = []
        for opt in raw_options:
            if isinstance(opt, str):
                normalized.append({"label": opt, "value": opt})
            elif isinstance(opt, dict):
                label = opt.get("label")
                value = opt.get("value")
                if value is None and "name" in opt:
                    value = opt.get("name")
                if label is None and value is not None:
                    label = str(value)
                if label is not None and value is not None:
                    normalized.append({"label": label, "value": value})
        return normalized

    def _load_entity_field_options(
        self,
        field_name: str,
        entity_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """从实体建模字段定义中加载 options（与数据库字段定义保持一致）。"""
        try:
            from app.core.database import SessionLocal
            from app.models.entity import EntityFieldDBModel, EntityDBModel

            db = SessionLocal()
            try:
                query = db.query(EntityFieldDBModel).filter(
                    EntityFieldDBModel.name == field_name
                )
                if entity_name:
                    query = query.join(
                        EntityDBModel,
                        EntityDBModel.id == EntityFieldDBModel.entity_id
                    ).filter(EntityDBModel.name == entity_name)

                fields = query.order_by(EntityFieldDBModel.updated_at.desc()).all()
                if not fields:
                    return []

                for field in fields:
                    normalized = self._normalize_options(field.options)
                    if normalized:
                        return normalized

                # 回退：未指定实体或指定实体为空时，尝试全局同名字段
                if entity_name:
                    fallback_fields = db.query(EntityFieldDBModel).filter(
                        EntityFieldDBModel.name == field_name
                    ).order_by(EntityFieldDBModel.updated_at.desc()).all()
                    for field in fallback_fields:
                        normalized = self._normalize_options(field.options)
                        if normalized:
                            return normalized
                return []
            finally:
                db.close()
        except Exception:
            return []
    
    def _create_field_config(self, field_name: str) -> Dict[str, Any]:
        """
        创建字段配置
        
        根据字段名推断字段类型和标签
        """
        # 字段类型推断
        if "date" in field_name.lower() and "time" not in field_name.lower():
            field_type = "input-date"
            field_format = "YYYY-MM-DD"
        elif "datetime" in field_name.lower():
            field_type = "input-datetime"
            field_format = "YYYY-MM-DD HH:mm:ss"
        elif any(kw in field_name.lower() for kw in ["amount", "price", "quantity", "number"]):
            field_type = "input-number"
            field_format = None
        else:
            field_type = "input-text"
            field_format = None
        
        # 字段标签
        label = self._get_field_label(field_name)
        
        config = {
            "type": field_type,
            "name": field_name,
            "label": label,
            "required": True,
            "placeholder": f"请输入{label}"
        }
        
        if field_format:
            config["format"] = field_format
        
        return config

    def _should_override_field_label(self, current_label: Any, ai_label: Any) -> bool:
        """
        是否允许使用 AI 标签覆盖已有标签。

        规则：
        - AI 标签为空：不覆盖
        - 当前标签为空：覆盖
        - 当前标签不含中文：覆盖（让 AI 补中文）
        - 当前标签已含中文：不覆盖（优先使用配置里的确定性中文标签）
        """
        import re

        if not isinstance(ai_label, str) or not ai_label.strip():
            return False
        if not isinstance(current_label, str) or not current_label.strip():
            return True
        if not re.search(r"[\u4e00-\u9fff]", current_label):
            return True
        return False
    
    def _convert_field_to_form_config(
        self,
        field: Dict[str, Any],
        entity_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将字段定义转换为表单配置
        
        Args:
            field: 字段定义
        
        Returns:
            表单字段配置
        """
        field_type = field.get("type", "string")
        field_name = field.get("name", "")
        field_label = field.get("label", field.get("description", field.get("displayName", field_name)))
        required = field.get("required", False)
        
        # 🔥 根据字段类型映射到 AMIS 组件
        if field_type == "select":
            amis_type = "select"
        elif field_type in ("file", "upload"):
            amis_type = "input-file"
        elif field_type == "image":
            amis_type = "input-image"
        elif field_type in ("date", "date-picker"):
            amis_type = "input-date"
        elif field_type in ("datetime", "datetime-picker"):
            amis_type = "input-datetime"
        elif field_type == "time":
            amis_type = "input-time"
        elif field_type == "number":
            amis_type = "input-number"
        elif field_type == "textarea":
            amis_type = "textarea"
        elif field_type == "switch":
            amis_type = "switch"
        elif field_type == "checkbox":
            amis_type = "checkbox"
        elif field_type == "radio":
            amis_type = "radios"
        elif field_type in ("string", "text"):
            amis_type = "input-text"
        else:
            amis_type = "input-text"
        
        config = {
            "type": amis_type,
            "name": field_name,
            "label": field_label,
            "required": required,
            "placeholder": f"请输入{field_label}" if amis_type.startswith("input") else f"请选择{field_label}"
        }
        
        # 🔥 处理 select/radios 的 options，若接口未给则回退实体建模字段定义
        if amis_type in ("select", "radios", "checkbox"):
            options = field.get("options", [])
            if (not isinstance(options, list) or not options) and field_name:
                options = self._load_entity_field_options(field_name, entity_name=entity_name)

            if isinstance(options, list) and options:
                # 如果是简单数组，转换为 {label, value} 格式
                if isinstance(options[0], str):
                    config["options"] = [{"label": opt, "value": opt} for opt in options]
                else:
                    config["options"] = options
        
        # 🔥 处理文件上传的额外配置
        if amis_type in ("input-file", "input-image"):
            config["receiver"] = "/api/v1/files/upload"
            if amis_type == "input-image":
                config["accept"] = "image/*"
                config["limit"] = {"maxSize": 5242880}  # 5MB
        
        # 🔥 处理日期时间的格式
        if amis_type == "input-date":
            config["format"] = "YYYY-MM-DD"
            config["inputFormat"] = "YYYY-MM-DD"
        elif amis_type == "input-datetime":
            config["format"] = "YYYY-MM-DD HH:mm:ss"
            config["inputFormat"] = "YYYY-MM-DD HH:mm:ss"
        elif amis_type == "input-time":
            config["format"] = "HH:mm:ss"
            config["inputFormat"] = "HH:mm:ss"
        
        # 🔥 处理数字输入的额外配置
        if amis_type == "input-number":
            if "min" in field:
                config["min"] = field["min"]
            if "max" in field:
                config["max"] = field["max"]
            if "step" in field:
                config["step"] = field["step"]
        
        return config
    
    def _get_field_label(self, field_name: str) -> str:
        """根据字段名生成标签（优先实体元数据，失败则人性化处理）"""
        if not field_name:
            return ""

        try:
            from app.services.entity_service import entity_service
            label = entity_service.get_field_label(field_name)
            if label:
                return label
        except Exception:
            pass

        return self._humanize_field_name(field_name)

    def _humanize_field_name(self, field_name: str) -> str:
        if not field_name:
            return ""
        base = field_name.split(".")[-1].strip()
        if any("\u4e00" <= ch <= "\u9fff" for ch in base):
            return base
        import re
        base = re.sub(r"[_\\-]+", " ", base).strip()
        if not base:
            return field_name
        return base.title()
    
    def _create_error_schema(self, error_message: str) -> Dict[str, Any]:
        """创建错误 Schema"""
        return {
            "type": "page",
            "title": "错误",
            "body": {
                "type": "alert",
                "level": "danger",
                "body": f"生成界面失败：{error_message}",
                "showIcon": True
            }
        }


# 全局实例
amis_schema_generator = AmisSchemaGenerator()



