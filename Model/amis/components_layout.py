"""
AMIS 布局组件知识库
包含 Page、Container、Grid、Flex、Panel、Tabs 等布局组件
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PageComponent:
    """Page 页面组件"""
    
    type_name: str = "page"
    description: str = "页面组件，amis 页面配置中必须且唯一的顶级节点"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "页面标题",
        "subTitle": "页面副标题",
        "remark": "标题附近的提示信息",
        "aside": "侧边栏区域",
        "asideResizor": "是否可调整侧边栏宽度",
        "asideSticky": "侧边栏是否固定",
        "toolbar": "工具栏区域",
        "body": "内容区域",
        "className": "外层 CSS 类名",
        "cssVars": "自定义 CSS 变量",
        "toolbarClassName": "工具栏 CSS 类名",
        "bodyClassName": "内容区 CSS 类名",
        "asideClassName": "侧边栏 CSS 类名",
        "headerClassName": "头部区域 CSS 类名",
        "initApi": "页面初始化时请求的接口",
        "initFetch": "是否默认拉取",
        "initFetchOn": "是否默认拉取的表达式",
        "interval": "刷新时间间隔（毫秒）",
        "silentPolling": "静默刷新",
        "stopAutoRefreshWhen": "停止自动刷新的条件"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "title": "页面标题",
        "subTitle": "副标题",
        "body": "这是内容区"
    })
    
    with_toolbar_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "title": "页面标题",
        "toolbar": [
            {
                "type": "button",
                "label": "新增",
                "actionType": "dialog",
                "dialog": {
                    "title": "新增",
                    "body": {
                        "type": "form",
                        "body": [
                            {
                                "type": "input-text",
                                "name": "name",
                                "label": "名称"
                            }
                        ]
                    }
                }
            }
        ],
        "body": "内容区"
    })
    
    with_aside_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "aside": {
            "type": "nav",
            "stacked": True,
            "links": [
                {"label": "菜单1", "to": "/page1"},
                {"label": "菜单2", "to": "/page2"}
            ]
        },
        "body": "主内容区"
    })
    
    with_init_api_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "initApi": "/api/page/init",
        "body": {
            "type": "tpl",
            "tpl": "用户名：${username}"
        }
    })


@dataclass
class ContainerComponent:
    """Container 容器组件"""
    
    type_name: str = "container"
    description: str = "容器组件，用于包裹其他组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "body": "容器内容",
        "bodyClassName": "容器内容区 CSS 类名",
        "className": "外层 CSS 类名",
        "style": "自定义样式",
        "wrapperComponent": "容器标签名"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "container",
        "body": [
            {
                "type": "tpl",
                "tpl": "内容1"
            },
            {
                "type": "tpl",
                "tpl": "内容2"
            }
        ]
    })
    
    with_style_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "container",
        "style": {
            "backgroundColor": "#f5f5f5",
            "padding": "20px",
            "borderRadius": "4px"
        },
        "body": "带样式的容器"
    })


@dataclass
class GridComponent:
    """Grid 水平分栏组件"""
    
    type_name: str = "grid"
    description: str = "水平分栏布局，支持响应式"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "columns": "列配置",
        "gap": "列间距",
        "valign": "垂直对齐方式：top/middle/bottom/between",
        "align": "水平对齐方式：left/center/right/between/around",
        "className": "外层 CSS 类名"
    })
    
    column_properties: Dict[str, str] = field(default_factory=lambda: {
        "body": "列内容",
        "xs": "极小屏幕宽度占比",
        "sm": "小屏幕宽度占比",
        "md": "中等屏幕宽度占比",
        "lg": "大屏幕宽度占比",
        "valign": "垂直对齐",
        "className": "列 CSS 类名"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "grid",
        "columns": [
            {
                "body": "第一列"
            },
            {
                "body": "第二列"
            },
            {
                "body": "第三列"
            }
        ]
    })
    
    responsive_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "grid",
        "columns": [
            {
                "md": 3,
                "body": "占 3/12"
            },
            {
                "md": 9,
                "body": "占 9/12"
            }
        ]
    })


@dataclass
class FlexComponent:
    """Flex 布局组件"""
    
    type_name: str = "flex"
    description: str = "Flex 弹性布局"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "items": "子元素配置",
        "direction": "布局方向：row/column/row-reverse/column-reverse",
        "justify": "主轴对齐：start/end/center/between/around",
        "alignItems": "交叉轴对齐：stretch/start/end/center/baseline",
        "className": "外层 CSS 类名",
        "style": "自定义样式"
    })
    
    item_properties: Dict[str, str] = field(default_factory=lambda: {
        "body": "内容",
        "className": "CSS 类名",
        "style": "自定义样式"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "flex",
        "items": [
            {
                "body": "项目1"
            },
            {
                "body": "项目2"
            },
            {
                "body": "项目3"
            }
        ]
    })
    
    advanced_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "flex",
        "direction": "row",
        "justify": "space-between",
        "alignItems": "center",
        "items": [
            {
                "body": "左侧内容"
            },
            {
                "body": "右侧内容"
            }
        ]
    })


@dataclass
class PanelComponent:
    """Panel 面板组件"""
    
    type_name: str = "panel"
    description: str = "面板组件，可以把相关信息以面板的形式展示"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "标题",
        "header": "头部区域",
        "body": "内容区域",
        "footer": "底部区域",
        "actions": "按钮区域",
        "className": "外层 CSS 类名",
        "headerClassName": "头部 CSS 类名",
        "bodyClassName": "内容 CSS 类名",
        "footerClassName": "底部 CSS 类名",
        "actionsClassName": "按钮区 CSS 类名",
        "affixFooter": "是否固定底部"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "panel",
        "title": "面板标题",
        "body": "面板内容"
    })
    
    with_actions_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "panel",
        "title": "用户信息",
        "body": {
            "type": "form",
            "body": [
                {
                    "type": "input-text",
                    "name": "name",
                    "label": "姓名"
                },
                {
                    "type": "input-email",
                    "name": "email",
                    "label": "邮箱"
                }
            ]
        },
        "actions": [
            {
                "type": "button",
                "label": "保存",
                "actionType": "submit"
            },
            {
                "type": "button",
                "label": "取消"
            }
        ]
    })


@dataclass
class TabsComponent:
    """Tabs 选项卡组件"""
    
    type_name: str = "tabs"
    description: str = "选项卡组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "tabs": "选项卡列表",
        "tabsMode": "展示模式：line/card/radio/vertical/chrome/simple/strong/tiled",
        "activeKey": "激活的选项卡",
        "defaultActiveKey": "默认激活的选项卡",
        "className": "外层 CSS 类名",
        "linksClassName": "选项卡 CSS 类名",
        "contentClassName": "内容区 CSS 类名",
        "mountOnEnter": "只有激活时才渲染",
        "unmountOnExit": "切换时销毁"
    })
    
    tab_properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "选项卡标题",
        "icon": "图标",
        "body": "内容",
        "hash": "URL hash",
        "reload": "是否重新加载",
        "unmountOnExit": "切换时销毁",
        "className": "CSS 类名",
        "closable": "是否可关闭",
        "disabled": "是否禁用",
        "tip": "提示信息"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "tabs",
        "tabs": [
            {
                "title": "选项卡1",
                "body": "内容1"
            },
            {
                "title": "选项卡2",
                "body": "内容2"
            },
            {
                "title": "选项卡3",
                "body": "内容3"
            }
        ]
    })
    
    advanced_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "tabs",
        "tabsMode": "card",
        "tabs": [
            {
                "title": "基本信息",
                "icon": "fa fa-user",
                "body": {
                    "type": "form",
                    "body": [
                        {
                            "type": "input-text",
                            "name": "name",
                            "label": "姓名"
                        }
                    ]
                }
            },
            {
                "title": "详细信息",
                "icon": "fa fa-info-circle",
                "body": "详细信息内容"
            }
        ]
    })


@dataclass
class DividerComponent:
    """Divider 分割线组件"""
    
    type_name: str = "divider"
    description: str = "分割线组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "className": "外层 CSS 类名",
        "lineStyle": "线条样式：dashed/solid"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "divider"
    })


@dataclass
class CollapseComponent:
    """Collapse 折叠器组件"""
    
    type_name: str = "collapse"
    description: str = "折叠器组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "key": "标识",
        "header": "标题",
        "body": "内容",
        "disabled": "是否禁用",
        "collapsed": "是否默认折叠",
        "showArrow": "是否显示箭头",
        "expandIcon": "自定义展开图标",
        "className": "外层 CSS 类名",
        "headingClassName": "标题 CSS 类名",
        "bodyClassName": "内容 CSS 类名"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "collapse",
        "header": "标题",
        "body": "内容"
    })
    
    collapse_group_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "collapse-group",
        "body": [
            {
                "type": "collapse",
                "key": "1",
                "header": "折叠器1",
                "body": "内容1"
            },
            {
                "type": "collapse",
                "key": "2",
                "header": "折叠器2",
                "body": "内容2"
            }
        ]
    })


@dataclass
class WrapperComponent:
    """Wrapper 包裹容器组件"""
    
    type_name: str = "wrapper"
    description: str = "简单的包裹容器"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "body": "内容",
        "className": "外层 CSS 类名",
        "size": "大小：xs/sm/md/lg/none",
        "style": "自定义样式"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "wrapper",
        "body": "包裹的内容"
    })


# 导出所有布局组件
LAYOUT_COMPONENTS = {
    "page": PageComponent(),
    "container": ContainerComponent(),
    "grid": GridComponent(),
    "flex": FlexComponent(),
    "panel": PanelComponent(),
    "tabs": TabsComponent(),
    "divider": DividerComponent(),
    "collapse": CollapseComponent(),
    "wrapper": WrapperComponent()
}


def get_layout_components_summary() -> List[Dict[str, str]]:
    """获取布局组件摘要"""
    return [
        {"type": "page", "name": "页面", "description": "页面组件，顶级节点"},
        {"type": "container", "name": "容器", "description": "通用容器组件"},
        {"type": "grid", "name": "水平分栏", "description": "响应式水平分栏布局"},
        {"type": "flex", "name": "Flex布局", "description": "弹性布局"},
        {"type": "panel", "name": "面板", "description": "面板容器"},
        {"type": "tabs", "name": "选项卡", "description": "选项卡容器"},
        {"type": "divider", "name": "分割线", "description": "分割线"},
        {"type": "collapse", "name": "折叠器", "description": "可折叠的内容区"},
        {"type": "wrapper", "name": "包裹容器", "description": "简单包裹容器"}
    ]
