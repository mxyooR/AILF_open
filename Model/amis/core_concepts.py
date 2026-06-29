"""
AMIS 核心概念知识库
包含 AMIS 的基础概念、Schema 结构、组件树等核心知识
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AmisIntroduction:
    """AMIS 框架介绍"""
    name: str = "amis"
    description: str = "一个低代码前端框架，使用 JSON 配置来生成页面"
    
    advantages: List[str] = field(default_factory=lambda: [
        "不需要懂前端：无需学习 JavaScript、React/Vue、Webpack 等前端技术",
        "不受前端技术更新影响：JSON 配置长期有效，不会因技术栈更新而过时",
        "享受持续升级：amis 不断优化细节交互，无需修改配置即可获得新特性",
        "可视化编辑器：支持完全可视化的页面制作，生成的页面可直接上线",
        "提供完整界面解决方案：JSON 配置即可完成数据获取、表单提交、验证等完整功能",
        "大量内置组件（120+）：包含富文本编辑器、代码编辑器、条件组合等业务组件",
        "支持扩展：可通过自定义组件扩充，支持低代码与代码开发混合模式",
        "容器无限级嵌套：通过嵌套满足各种布局和展现需求",
        "经过实战考验：百度内部 6 年多时间创建了 5 万页面"
    ])
    
    not_suitable_for: List[str] = field(default_factory=lambda: [
        "大量定制 UI：面向普通客户（toC）追求个性化视觉效果的页面",
        "极为复杂或特殊的交互：依赖原生 DOM 实现的功能，如可视化编辑器的拖拽操作"
    ])
    
    use_cases: List[str] = field(default_factory=lambda: [
        "后台管理系统",
        "数据展示和分析页面",
        "表单密集型应用",
        "CRUD（增删改查）应用",
        "工作流和审批系统",
        "内容管理系统"
    ])


@dataclass
class SchemaBasics:
    """AMIS Schema 基础知识"""
    
    minimal_schema: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "body": "Hello World!"
    })
    
    schema_structure: str = """
    AMIS 配置的基本结构：
    {
        "type": "组件类型",  // 必需，标识当前渲染的组件
        ...其它属性           // 组件的配置属性
    }
    """
    
    key_concepts: Dict[str, str] = field(default_factory=lambda: {
        "type": "组件类型标识，告诉 amis 当前节点需要渲染的组件",
        "body": "容器型组件的内容区域，可以是字符串、对象或数组",
        "组件树": "通过嵌套的 JSON 结构构建复杂页面",
        "Page": "amis 页面配置中必须且唯一的顶级节点"
    })
    
    component_tree_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "body": {
            "type": "tpl",
            "tpl": "Hello World!"
        }
    })
    
    multiple_components_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "body": [
            {
                "type": "tpl",
                "tpl": "第一个组件"
            },
            {
                "type": "divider"
            },
            {
                "type": "form",
                "body": [
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "姓名"
                    }
                ]
            }
        ]
    })


@dataclass
class DataScopeAndChain:
    """数据域与数据链"""
    
    description: str = """
    数据域：每个组件都有自己的数据域，用于存储和访问数据
    数据链：组件可以访问父组件的数据域，形成数据链
    """
    
    data_access_methods: List[str] = field(default_factory=lambda: [
        "直接访问：${fieldName}",
        "访问父级数据：${parentFieldName}",
        "访问根数据：${rootFieldName}",
        "表达式：${IF(condition, trueValue, falseValue)}"
    ])
    
    example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "data": {
            "globalVar": "全局变量"
        },
        "body": {
            "type": "service",
            "data": {
                "localVar": "局部变量"
            },
            "body": {
                "type": "tpl",
                "tpl": "全局：${globalVar}，局部：${localVar}"
            }
        }
    })


@dataclass
class TemplateEngine:
    """模板引擎"""
    
    template_syntax: Dict[str, str] = field(default_factory=lambda: {
        "变量输出": "${变量名}",
        "条件判断": "${IF(条件, 真值, 假值)}",
        "循环": "${ARRAYMAP(数组, item => item.name)}",
        "过滤器": "${变量名 | date:'YYYY-MM-DD'}",
        "默认值": "${变量名 | default: '默认值'}"
    })
    
    filters: List[str] = field(default_factory=lambda: [
        "date: 日期格式化",
        "number: 数字格式化",
        "trim: 去除空格",
        "percent: 百分比",
        "duration: 时长",
        "bytes: 字节",
        "round: 四舍五入",
        "truncate: 截断",
        "url_encode: URL 编码",
        "json: JSON 格式化"
    ])


@dataclass
class DataMapping:
    """数据映射"""
    
    description: str = "将数据从一个格式转换为另一个格式"
    
    mapping_types: Dict[str, str] = field(default_factory=lambda: {
        "简单映射": "直接赋值",
        "表达式映射": "使用表达式计算",
        "函数映射": "使用内置函数处理",
        "条件映射": "根据条件映射不同值"
    })
    
    example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "service",
        "api": "/api/getData",
        "data": {
            "&": "$$",  # 引用整个数据域
            "newField": "${oldField}",  # 简单映射
            "computed": "${field1 + field2}",  # 表达式映射
            "conditional": "${IF(status == 1, '启用', '禁用')}"  # 条件映射
        }
    })


@dataclass
class Expression:
    """表达式"""
    
    expression_types: List[str] = field(default_factory=lambda: [
        "模板表达式：${expression}",
        "公式表达式：${= expression}",
        "条件表达式：${IF(condition, true, false)}",
        "过滤器表达式：${value | filter}"
    ])
    
    built_in_functions: List[str] = field(default_factory=lambda: [
        "IF(条件, 真值, 假值)",
        "AND(条件1, 条件2, ...)",
        "OR(条件1, 条件2, ...)",
        "ISEMPTY(值)",
        "ISNOTEMPTY(值)",
        "ARRAYMAP(数组, 迭代器)",
        "ARRAYFILTER(数组, 条件)",
        "COUNT(数组)",
        "SUM(数组, 字段)",
        "AVG(数组, 字段)",
        "MIN(数组, 字段)",
        "MAX(数组, 字段)",
        "GET(对象, 路径)",
        "DATEFORMAT(日期, 格式)",
        "TIMESTAMP(日期, 格式)"
    ])
    
    operators: List[str] = field(default_factory=lambda: [
        "算术运算：+, -, *, /, %",
        "比较运算：==, !=, >, <, >=, <=",
        "逻辑运算：&&, ||, !",
        "三元运算：condition ? true : false",
        "成员运算：in, not in"
    ])


@dataclass
class Linkage:
    """联动"""
    
    linkage_types: Dict[str, str] = field(default_factory=lambda: {
        "显隐联动": "根据条件控制组件显示/隐藏",
        "禁用联动": "根据条件控制组件启用/禁用",
        "数据联动": "一个组件的值变化影响另一个组件的数据",
        "选项联动": "下拉框等选择器的选项根据其他字段动态变化",
        "校验联动": "根据其他字段的值动态调整校验规则"
    })
    
    visibility_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "form",
        "body": [
            {
                "type": "switch",
                "name": "showDetail",
                "label": "显示详情"
            },
            {
                "type": "input-text",
                "name": "detail",
                "label": "详情",
                "visibleOn": "${showDetail}"  # 显隐联动
            }
        ]
    })
    
    disabled_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "form",
        "body": [
            {
                "type": "switch",
                "name": "editable",
                "label": "允许编辑"
            },
            {
                "type": "input-text",
                "name": "content",
                "label": "内容",
                "disabledOn": "${!editable}"  # 禁用联动
            }
        ]
    })


@dataclass
class EventAction:
    """事件动作"""
    
    description: str = "通过事件触发动作，实现组件间的交互"
    
    common_events: List[str] = field(default_factory=lambda: [
        "click: 点击事件",
        "change: 值变化事件",
        "submit: 表单提交事件",
        "init: 组件初始化事件",
        "inited: 初始化完成事件",
        "focus: 获得焦点事件",
        "blur: 失去焦点事件",
        "mouseenter: 鼠标进入事件",
        "mouseleave: 鼠标离开事件"
    ])
    
    common_actions: List[str] = field(default_factory=lambda: [
        "ajax: 发送 AJAX 请求",
        "dialog: 打开弹窗",
        "drawer: 打开抽屉",
        "toast: 显示提示",
        "alert: 显示警告",
        "confirm: 显示确认框",
        "reload: 重新加载组件",
        "setValue: 设置组件值",
        "show: 显示组件",
        "hide: 隐藏组件",
        "enabled: 启用组件",
        "disabled: 禁用组件",
        "static: 切换到静态展示",
        "nonstatic: 切换到编辑模式",
        "submit: 提交表单",
        "reset: 重置表单",
        "clear: 清空表单",
        "validate: 校验表单",
        "link: 页面跳转",
        "goBack: 返回上一页",
        "refresh: 刷新页面",
        "copy: 复制内容"
    ])
    
    event_action_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "body": [
            {
                "type": "button",
                "label": "点击我",
                "onEvent": {
                    "click": {
                        "actions": [
                            {
                                "actionType": "toast",
                                "args": {
                                    "msg": "按钮被点击了"
                                }
                            },
                            {
                                "actionType": "ajax",
                                "args": {
                                    "api": "/api/log",
                                    "data": {
                                        "action": "button_click"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        ]
    })


@dataclass
class StyleSystem:
    """样式系统"""
    
    css_variables: Dict[str, str] = field(default_factory=lambda: {
        "--primary-color": "主色调",
        "--info-color": "信息色",
        "--success-color": "成功色",
        "--warning-color": "警告色",
        "--danger-color": "危险色",
        "--text-color": "文本颜色",
        "--background-color": "背景颜色",
        "--border-color": "边框颜色",
        "--border-radius": "圆角大小",
        "--font-size-base": "基础字号",
        "--line-height-base": "基础行高"
    })
    
    class_name_types: List[str] = field(default_factory=lambda: [
        "字符串：直接指定类名",
        "对象：根据条件动态添加类名",
        "表达式：使用表达式计算类名"
    ])
    
    utility_classes: List[str] = field(default_factory=lambda: [
        "m-t: margin-top",
        "m-r: margin-right",
        "m-b: margin-bottom",
        "m-l: margin-left",
        "p-t: padding-top",
        "p-r: padding-right",
        "p-b: padding-bottom",
        "p-l: padding-left",
        "text-center: 文本居中",
        "text-right: 文本右对齐",
        "text-left: 文本左对齐",
        "bg-primary: 主色背景",
        "bg-success: 成功色背景",
        "bg-warning: 警告色背景",
        "bg-danger: 危险色背景",
        "text-primary: 主色文本",
        "text-success: 成功色文本",
        "text-warning: 警告色文本",
        "text-danger: 危险色文本"
    ])


# 导出所有知识类
AMIS_CORE_CONCEPTS = {
    "introduction": AmisIntroduction(),
    "schema_basics": SchemaBasics(),
    "data_scope_and_chain": DataScopeAndChain(),
    "template_engine": TemplateEngine(),
    "data_mapping": DataMapping(),
    "expression": Expression(),
    "linkage": Linkage(),
    "event_action": EventAction(),
    "style_system": StyleSystem()
}


def get_concept_summary() -> Dict[str, Any]:
    """获取核心概念摘要"""
    return {
        "framework_name": "amis",
        "type": "低代码前端框架",
        "config_format": "JSON",
        "key_features": [
            "无需前端知识",
            "JSON 配置生成页面",
            "120+ 内置组件",
            "可视化编辑器",
            "完整的数据处理能力"
        ],
        "core_concepts": [
            "Schema（配置）",
            "组件树",
            "数据域与数据链",
            "模板引擎",
            "数据映射",
            "表达式",
            "联动",
            "事件动作",
            "样式系统"
        ]
    }
