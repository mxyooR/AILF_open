"""
AMIS 数据展示组件知识库
包含 CRUD、Table、List、Cards 等数据展示组件
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CRUDComponent:
    """CRUD 增删改查组件"""
    
    type_name: str = "crud"
    description: str = "增删改查组件，用于列表数据的展示和操作"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "api": "数据接口",
        "initFetch": "是否初始拉取",
        "interval": "刷新间隔",
        "silentPolling": "静默刷新",
        "stopAutoRefreshWhen": "停止刷新条件",
        "syncLocation": "同步地址栏",
        "draggable": "是否可拖拽排序",
        "itemDraggableOn": "拖拽条件",
        "saveOrderApi": "保存排序接口",
        "quickSaveApi": "快速保存接口",
        "quickSaveItemApi": "快速保存单项接口",
        "bulkActions": "批量操作",
        "defaultParams": "默认参数",
        "pageField": "页码字段",
        "perPageField": "每页条数字段",
        "orderField": "排序字段",
        "filter": "过滤器",
        "filterTogglable": "过滤器可切换",
        "filterDefaultVisible": "过滤器默认显示",
        "headerToolbar": "顶部工具栏",
        "footerToolbar": "底部工具栏",
        "columns": "列配置",
        "columnsTogglable": "列显隐",
        "placeholder": "无数据提示",
        "perPage": "每页条数",
        "perPageAvailable": "每页条数选项",
        "messages": "消息配置",
        "primaryField": "主键字段",
        "keepItemSelectionOnPageChange": "翻页保持选中",
        "labelTpl": "单条描述模板",
        "loadDataOnce": "一次性加载",
        "source": "数据源",
        "hideQuickSaveBtn": "隐藏快速保存按钮",
        "autoJumpToTopOnPagerChange": "翻页自动跳转顶部",
        "syncResponse2Query": "同步响应到查询参数",
        "itemActions": "单条操作"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "crud",
        "api": "/api/users",
        "columns": [
            {
                "name": "id",
                "label": "ID"
            },
            {
                "name": "name",
                "label": "姓名"
            },
            {
                "name": "email",
                "label": "邮箱"
            },
            {
                "type": "operation",
                "label": "操作",
                "buttons": [
                    {
                        "type": "button",
                        "label": "编辑",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "编辑",
                            "body": {
                                "type": "form",
                                "api": "/api/users/${id}",
                                "body": [
                                    {
                                        "type": "input-text",
                                        "name": "name",
                                        "label": "姓名"
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "type": "button",
                        "label": "删除",
                        "actionType": "ajax",
                        "confirmText": "确认删除？",
                        "api": "delete:/api/users/${id}"
                    }
                ]
            }
        ]
    })
    
    with_filter_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "crud",
        "api": "/api/users",
        "filter": {
            "title": "条件搜索",
            "body": [
                {
                    "type": "input-text",
                    "name": "keywords",
                    "label": "关键字",
                    "placeholder": "请输入关键字"
                },
                {
                    "type": "select",
                    "name": "status",
                    "label": "状态",
                    "options": [
                        {"label": "全部", "value": ""},
                        {"label": "启用", "value": "1"},
                        {"label": "禁用", "value": "0"}
                    ]
                }
            ]
        },
        "columns": [
            {"name": "id", "label": "ID"},
            {"name": "name", "label": "姓名"}
        ]
    })
    
    with_bulk_actions_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "crud",
        "api": "/api/users",
        "bulkActions": [
            {
                "label": "批量删除",
                "actionType": "ajax",
                "api": "delete:/api/users/batch",
                "confirmText": "确认删除选中的数据？"
            },
            {
                "label": "批量导出",
                "actionType": "download",
                "api": "/api/users/export"
            }
        ],
        "columns": [
            {"name": "id", "label": "ID"},
            {"name": "name", "label": "姓名"}
        ]
    })


@dataclass
class TableComponent:
    """Table 表格组件"""
    
    type_name: str = "table"
    description: str = "表格组件，用于展示表格数据"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "columns": "列配置",
        "columnsTogglable": "列显隐",
        "affixHeader": "固定表头",
        "footable": "底部工具栏",
        "expandConfig": "展开配置",
        "itemActions": "单条操作",
        "itemCheckableOn": "可选条件",
        "itemDraggableOn": "可拖拽条件",
        "checkOnItemClick": "点击行选中",
        "rowClassName": "行样式",
        "rowClassNameExpr": "行样式表达式",
        "prefixRow": "顶部总结行",
        "affixRow": "底部总结行",
        "placeholder": "无数据提示",
        "showHeader": "显示表头",
        "showFooter": "显示表尾",
        "footerClassName": "表尾样式",
        "toolbarClassName": "工具栏样式",
        "combineNum": "合并单元格数",
        "combineFromIndex": "合并起始列"
    })
    
    column_properties: Dict[str, str] = field(default_factory=lambda: {
        "name": "字段名",
        "label": "列标题",
        "type": "列类型",
        "width": "列宽",
        "fixed": "固定列：left/right",
        "popOver": "弹出框",
        "copyable": "可复制",
        "sortable": "可排序",
        "searchable": "可搜索",
        "quickEdit": "快速编辑",
        "quickEditOnUpdate": "更新时快速编辑",
        "toggled": "默认显示",
        "breakpoint": "响应式断点",
        "remark": "提示信息",
        "className": "列样式",
        "innerClassName": "内容样式",
        "labelClassName": "标题样式",
        "filterable": "可过滤",
        "filters": "过滤选项"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "table",
        "data": {
            "items": [
                {"id": 1, "name": "张三", "age": 25},
                {"id": 2, "name": "李四", "age": 30}
            ]
        },
        "columns": [
            {"name": "id", "label": "ID"},
            {"name": "name", "label": "姓名"},
            {"name": "age", "label": "年龄"}
        ]
    })
    
    with_operations_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "table",
        "data": {
            "items": [
                {"id": 1, "name": "张三"},
                {"id": 2, "name": "李四"}
            ]
        },
        "columns": [
            {"name": "id", "label": "ID"},
            {"name": "name", "label": "姓名"},
            {
                "type": "operation",
                "label": "操作",
                "buttons": [
                    {
                        "type": "button",
                        "label": "查看",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "详情",
                            "body": "ID: ${id}, 姓名: ${name}"
                        }
                    }
                ]
            }
        ]
    })


@dataclass
class ListComponent:
    """List 列表组件"""
    
    type_name: str = "list"
    description: str = "列表组件，用于展示列表数据"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "listItem": "列表项配置",
        "source": "数据源",
        "placeholder": "无数据提示",
        "headerClassName": "头部样式",
        "footerClassName": "底部样式",
        "itemClassName": "列表项样式"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "list",
        "source": "${items}",
        "listItem": {
            "body": [
                {
                    "type": "tpl",
                    "tpl": "<div>${name} - ${email}</div>"
                }
            ],
            "actions": [
                {
                    "type": "button",
                    "label": "查看",
                    "actionType": "dialog",
                    "dialog": {
                        "title": "详情",
                        "body": "姓名：${name}"
                    }
                }
            ]
        }
    })


@dataclass
class CardsComponent:
    """Cards 卡片组件"""
    
    type_name: str = "cards"
    description: str = "卡片组件，用于展示卡片列表"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "card": "卡片配置",
        "source": "数据源",
        "placeholder": "无数据提示",
        "columnsCount": "列数",
        "itemClassName": "卡片样式",
        "checkOnItemClick": "点击卡片选中",
        "masonryLayout": "瀑布流布局"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "cards",
        "source": "${items}",
        "columnsCount": 3,
        "card": {
            "header": {
                "title": "${name}",
                "subTitle": "${email}"
            },
            "body": [
                {
                    "type": "tpl",
                    "tpl": "年龄：${age}"
                }
            ],
            "actions": [
                {
                    "type": "button",
                    "label": "查看",
                    "actionType": "dialog",
                    "dialog": {
                        "title": "详情",
                        "body": "姓名：${name}"
                    }
                }
            ]
        }
    })


@dataclass
class ChartComponent:
    """Chart 图表组件"""
    
    type_name: str = "chart"
    description: str = "图表组件，基于 ECharts"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "config": "ECharts 配置",
        "api": "数据接口",
        "source": "数据源",
        "initFetch": "是否初始拉取",
        "interval": "刷新间隔",
        "width": "宽度",
        "height": "高度",
        "replaceChartOption": "替换配置",
        "trackExpression": "追踪表达式",
        "dataFilter": "数据过滤"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "chart",
        "api": "/api/chart/data",
        "config": {
            "title": {
                "text": "销售统计"
            },
            "tooltip": {},
            "xAxis": {
                "type": "category",
                "data": ["周一", "周二", "周三", "周四", "周五"]
            },
            "yAxis": {
                "type": "value"
            },
            "series": [
                {
                    "name": "销量",
                    "type": "line",
                    "data": [120, 200, 150, 80, 70]
                }
            ]
        }
    })


@dataclass
class ServiceComponent:
    """Service 功能型容器"""
    
    type_name: str = "service"
    description: str = "功能型容器，可以用来加载数据或者加载渲染器配置"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "api": "数据接口",
        "ws": "WebSocket 地址",
        "initFetch": "是否初始拉取",
        "initFetchOn": "初始拉取条件",
        "schemaApi": "Schema 接口",
        "initFetchSchema": "是否初始拉取 Schema",
        "interval": "刷新间隔",
        "silentPolling": "静默刷新",
        "stopAutoRefreshWhen": "停止刷新条件",
        "body": "内容",
        "messages": "消息配置"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "service",
        "api": "/api/service/data",
        "body": {
            "type": "tpl",
            "tpl": "用户名：${username}"
        }
    })
    
    with_schema_api_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "service",
        "schemaApi": "/api/service/schema"
    })


@dataclass
class PaginationComponent:
    """Pagination 分页组件"""
    
    type_name: str = "pagination"
    description: str = "分页组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "mode": "模式：normal/simple",
        "layout": "布局：total,perpage,pager,go",
        "maxButtons": "最大按钮数",
        "lastPage": "总页数",
        "total": "总条数",
        "activePage": "当前页",
        "perPage": "每页条数",
        "showPerPage": "显示每页条数选择",
        "perPageAvailable": "每页条数选项",
        "showPageInput": "显示页码输入",
        "disabled": "是否禁用"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "pagination",
        "layout": "total,perpage,pager,go",
        "mode": "normal",
        "activePage": 1,
        "lastPage": 10,
        "total": 100,
        "perPage": 10,
        "maxButtons": 7,
        "showPerPage": True,
        "perPageAvailable": [10, 20, 50, 100]
    })


# 导出所有数据展示组件
DATA_COMPONENTS = {
    "crud": CRUDComponent(),
    "table": TableComponent(),
    "list": ListComponent(),
    "cards": CardsComponent(),
    "chart": ChartComponent(),
    "service": ServiceComponent(),
    "pagination": PaginationComponent()
}


def get_data_components_summary() -> List[Dict[str, str]]:
    """获取数据展示组件摘要"""
    return [
        {"type": "crud", "name": "增删改查", "description": "完整的 CRUD 功能"},
        {"type": "table", "name": "表格", "description": "数据表格展示"},
        {"type": "list", "name": "列表", "description": "列表数据展示"},
        {"type": "cards", "name": "卡片", "description": "卡片列表展示"},
        {"type": "chart", "name": "图表", "description": "ECharts 图表"},
        {"type": "service", "name": "服务", "description": "功能型容器"},
        {"type": "pagination", "name": "分页", "description": "分页组件"}
    ]
