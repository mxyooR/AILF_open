"""
Chart 节点策略

处理图表展示（饼图、折线图、柱状图、混合仪表盘）
"""
from typing import Dict, Any, Optional, List
from .base import NodeStrategy
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ChartStrategy(NodeStrategy):
    """Chart 节点策略"""
    
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """
        判断是否为图表节点
        
        判断依据：
        1. 节点类型为 chart
        2. 或者 API 响应包含统计数据（array 类型）
        """
        node_type = node.get("type", "")
        if node_type == "chart":
            return True
        
        # 检查是否是统计类 API（响应包含 array）
        if node_type == "api_call":
            config = node.get("config", {})
            method = config.get("method", "GET").upper()
            outputs = node.get("outputs", [])
            
            # GET 请求 + 有 array 类型输出 = 可能是图表
            if method == "GET" and any(o.get("type") == "array" for o in outputs):
                # 检查是否包含统计关键词
                desc = node.get("description", "").lower()
                if any(kw in desc for kw in ["统计", "分析", "图表", "报表", "dashboard"]):
                    return True
        
        return False
    
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成图表 Schema
        
        根据数据类型自动选择图表类型：
        - 饼图：适合占比数据
        - 折线图：适合趋势数据
        - 柱状图：适合对比数据
        - 混合仪表盘：适合多维度数据
        """
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        outputs = node.get("outputs", [])
        
        # 推断图表类型
        chart_type = self._infer_chart_type(node, outputs)
        
        # 生成对应的图表 Schema
        if chart_type == "pie":
            chart_body = self._generate_pie_chart(api_endpoint, outputs)
        elif chart_type == "line":
            chart_body = self._generate_line_chart(api_endpoint, outputs)
        elif chart_type == "bar":
            chart_body = self._generate_bar_chart(api_endpoint, outputs)
        else:  # mixed
            chart_body = self._generate_mixed_dashboard(api_endpoint, outputs)
        logger.info(f"生成 Chart 节点 Schema: {node.get('id', '')}, type={chart_type}")
        
        body_content = [
            {
                "type": "alert",
                "level": "info",
                "body": node.get("description", "数据统计"),
                "showIcon": True
            },
            chart_body,
            {
                "type": "form",
                "api": self.build_workflow_api(
                    workflow_id=workflow["id"],
                    node_id=node.get("id", ""),
                    action="next"
                ),
                "body": self._build_hidden_fields_for_outputs(outputs),
                "actions": [
                    {
                        "type": "submit",
                        "label": "继续",
                        "level": "primary"
                    }
                ]
            }
        ]
        
        return self.build_base_page(workflow, node, body_content)
    
    def _infer_chart_type(
        self,
        node: Dict[str, Any],
        outputs: List[Dict[str, Any]]
    ) -> str:
        """
        推断图表类型
        
        Returns:
            "pie" | "line" | "bar" | "mixed"
        """
        desc = node.get("description", "").lower()
        
        # 关键词匹配
        if any(kw in desc for kw in ["占比", "比例", "分布", "pie"]):
            return "pie"
        elif any(kw in desc for kw in ["趋势", "变化", "时间", "line"]):
            return "line"
        elif any(kw in desc for kw in ["对比", "排名", "bar"]):
            return "bar"
        elif any(kw in desc for kw in ["仪表盘", "dashboard", "概览"]):
            return "mixed"
        
        # 默认柱状图
        return "bar"
    
    def _generate_pie_chart(
        self,
        api_endpoint: str,
        outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成饼图 Schema"""
        # 找到 array 类型的输出
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        data_field = array_output.get("name", "data") if array_output else "data"
        
        return {
            "type": "chart",
            "api": {
                "method": "get",
                "url": api_endpoint
            },
            "config": {
                "title": {
                    "text": "数据分布",
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{b}: {c} ({d}%)"
                },
                "legend": {
                    "orient": "vertical",
                    "left": "left"
                },
                "series": [
                    {
                        "name": "数据",
                        "type": "pie",
                        "radius": "50%",
                        "data": f"${{{data_field}}}",
                        "emphasis": {
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)"
                            }
                        }
                    }
                ]
            }
        }
    
    def _generate_line_chart(
        self,
        api_endpoint: str,
        outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成折线图 Schema"""
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        data_field = array_output.get("name", "data") if array_output else "data"
        
        return {
            "type": "chart",
            "api": {
                "method": "get",
                "url": api_endpoint
            },
            "config": {
                "title": {
                    "text": "趋势分析",
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "axis"
                },
                "xAxis": {
                    "type": "category",
                    "data": f"${{{data_field}}}"
                },
                "yAxis": {
                    "type": "value"
                },
                "series": [
                    {
                        "name": "数据",
                        "type": "line",
                        "data": f"${{values}}",
                        "smooth": True,
                        "itemStyle": {
                            "color": "#5470c6"
                        }
                    }
                ]
            }
        }
    
    def _generate_bar_chart(
        self,
        api_endpoint: str,
        outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成柱状图 Schema"""
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        data_field = array_output.get("name", "data") if array_output else "data"
        
        return {
            "type": "chart",
            "api": {
                "method": "get",
                "url": api_endpoint
            },
            "config": {
                "title": {
                    "text": "数据对比",
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "shadow"
                    }
                },
                "xAxis": {
                    "type": "category",
                    "data": f"${{{data_field}}}"
                },
                "yAxis": {
                    "type": "value"
                },
                "series": [
                    {
                        "name": "数据",
                        "type": "bar",
                        "data": f"${{values}}",
                        "itemStyle": {
                            "color": "#5470c6"
                        }
                    }
                ]
            }
        }
    
    def _generate_mixed_dashboard(
        self,
        api_endpoint: str,
        outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成混合仪表盘 Schema（数字卡片 + 图表）"""
        # 提取非 array 类型的输出作为卡片
        cards = []
        for output in outputs:
            if output.get("type") != "array":
                cards.append({
                    "type": "card",
                    "header": {
                        "title": output.get("description", output.get("name", ""))
                    },
                    "body": {
                        "type": "tpl",
                        "tpl": f"<div style='font-size:32px;font-weight:bold;color:#5470c6;'>${{{output.get('name')}}}</div>"
                    }
                })
        
        # 找到 array 类型的输出作为图表
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        
        body_items = []
        
        # 添加卡片
        if cards:
            body_items.append({
                "type": "grid",
                "columns": cards
            })
        
        # 添加图表
        if array_output:
            body_items.append(self._generate_bar_chart(api_endpoint, outputs))
        
        return {
            "type": "service",
            "api": {
                "method": "get",
                "url": api_endpoint
            },
            "body": body_items
        }
    
    def _build_hidden_fields_for_outputs(
        self,
        outputs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """为 outputs 构建隐藏字段"""
        hidden_fields = []
        for output in outputs:
            output_name = output.get("name", "")
            output_type = output.get("type", "string")
            if output_name and output_type != "array":
                hidden_fields.append({
                    "type": "hidden",
                    "name": output_name,
                    "value": f"${{{output_name}}}"
                })
        return hidden_fields
