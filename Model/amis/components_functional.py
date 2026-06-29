"""
AMIS 功能组件知识库
包含 Action、Button、Dialog、Drawer 等功能性组件
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ActionComponent:
    """Action 行为按钮"""
    
    type_name: str = "action"
    description: str = "行为按钮，可以触发各种动作"
    
    action_types: Dict[str, str] = field(default_factory=lambda: {
        "ajax": "发送 AJAX 请求",
        "link": "页面跳转",
        "url": "打开外部链接",
        "dialog": "打开弹窗",
        "drawer": "打开抽屉",
        "toast": "显示提示",
        "alert": "显示警告",
        "confirm": "显示确认框",
        "copy": "复制内容",
        "reload": "刷新组件",
        "email": "发送邮件",
        "prev": "上一步",
        "next": "下一步",
        "cancel": "取消",
        "close": "关闭",
        "submit": "提交表单",
        "reset": "重置表单",
        "clear": "清空表单",
        "reset-and-submit": "重置并提交"
    })
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "actionType": "动作类型",
        "label": "按钮文字",
        "level": "按钮样式：primary/secondary/success/info/warning/danger/light/dark/link",
        "size": "按钮大小：xs/sm/md/lg",
        "icon": "按钮图标",
        "iconClassName": "图标样式",
        "rightIcon": "右侧图标",
        "rightIconClassName": "右侧图标样式",
        "active": "是否激活",
        "activeLevel": "激活样式",
        "activeClassName": "激活样式类名",
        "block": "块状按钮",
        "confirmText": "确认文本",
        "reload": "刷新目标",
        "target": "目标组件",
        "link": "跳转链接",
        "blank": "新窗口打开",
        "tooltip": "提示信息",
        "tooltipPlacement": "提示位置",
        "disabledTip": "禁用提示",
        "disabled": "是否禁用",
        "disabledOn": "禁用条件",
        "visibleOn": "显示条件",
        "hiddenOn": "隐藏条件",
        "requireSelected": "需要选中",
        "mergeData": "合并数据",
        "api": "接口地址",
        "asyncApi": "异步接口",
        "redirect": "跳转地址",
        "feedback": "反馈弹窗",
        "messages": "消息配置",
        "close": "是否关闭当前弹窗",
        "countDown": "倒计时",
        "countDownTpl": "倒计时模板"
    })
    
    ajax_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "action",
        "actionType": "ajax",
        "label": "提交",
        "api": "post:/api/submit",
        "confirmText": "确认提交吗？",
        "reload": "window",
        "messages": {
            "success": "提交成功",
            "failed": "提交失败"
        }
    })
    
    dialog_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "action",
        "actionType": "dialog",
        "label": "打开弹窗",
        "dialog": {
            "title": "弹窗标题",
            "body": {
                "type": "form",
                "api": "/api/save",
                "body": [
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "姓名"
                    }
                ]
            }
        }
    })


@dataclass
class ButtonComponent:
    """Button 按钮"""
    
    type_name: str = "button"
    description: str = "按钮组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "label": "按钮文字",
        "type": "按钮类型：button/submit/reset",
        "level": "按钮样式",
        "size": "按钮大小",
        "icon": "图标",
        "iconClassName": "图标样式",
        "rightIcon": "右侧图标",
        "loading": "加载状态",
        "loadingOn": "加载条件",
        "block": "块状按钮",
        "tooltip": "提示信息",
        "disabled": "是否禁用",
        "disabledOn": "禁用条件",
        "className": "样式类名",
        "url": "跳转链接",
        "blank": "新窗口打开",
        "htmlType": "HTML 类型",
        "actionType": "动作类型",
        "confirmText": "确认文本",
        "reload": "刷新目标"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "button",
        "label": "按钮",
        "level": "primary"
    })
    
    with_icon_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "button",
        "label": "保存",
        "icon": "fa fa-save",
        "level": "success"
    })


@dataclass
class DialogComponent:
    """Dialog 弹窗"""
    
    type_name: str = "dialog"
    description: str = "弹窗组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "弹窗标题",
        "body": "弹窗内容",
        "size": "弹窗大小：xs/sm/md/lg/xl/full",
        "bodyClassName": "内容区样式",
        "closeOnEsc": "按 ESC 关闭",
        "closeOnOutside": "点击外部关闭",
        "showCloseButton": "显示关闭按钮",
        "showErrorMsg": "显示错误信息",
        "disabled": "是否禁用",
        "actions": "底部按钮",
        "data": "数据",
        "draggable": "是否可拖拽",
        "position": "位置配置",
        "overlay": "是否显示遮罩",
        "resizable": "是否可调整大小"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "button",
        "label": "打开弹窗",
        "actionType": "dialog",
        "dialog": {
            "title": "提示",
            "body": "这是弹窗内容"
        }
    })
    
    with_form_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "button",
        "label": "编辑",
        "actionType": "dialog",
        "dialog": {
            "title": "编辑信息",
            "size": "lg",
            "body": {
                "type": "form",
                "api": "/api/save",
                "body": [
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "姓名",
                        "required": True
                    },
                    {
                        "type": "input-email",
                        "name": "email",
                        "label": "邮箱",
                        "required": True
                    }
                ]
            }
        }
    })


@dataclass
class DrawerComponent:
    """Drawer 抽屉"""
    
    type_name: str = "drawer"
    description: str = "抽屉组件，从页面边缘滑出"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "抽屉标题",
        "body": "抽屉内容",
        "size": "抽屉大小：xs/sm/md/lg/xl",
        "position": "位置：left/right/top/bottom",
        "overlay": "是否显示遮罩",
        "closeOnEsc": "按 ESC 关闭",
        "closeOnOutside": "点击外部关闭",
        "showCloseButton": "显示关闭按钮",
        "resizable": "是否可调整大小",
        "actions": "底部按钮",
        "data": "数据"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "button",
        "label": "打开抽屉",
        "actionType": "drawer",
        "drawer": {
            "title": "抽屉标题",
            "body": "这是抽屉内容",
            "position": "right"
        }
    })


@dataclass
class ToastComponent:
    """Toast 提示"""
    
    type_name: str = "toast"
    description: str = "轻提示组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "标题",
        "body": "内容",
        "level": "级别：info/success/error/warning",
        "position": "位置：top-right/top-center/top-left/bottom-center/bottom-left/bottom-right",
        "closeButton": "显示关闭按钮",
        "showIcon": "显示图标",
        "timeout": "持续时间（毫秒）"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "button",
        "label": "显示提示",
        "onEvent": {
            "click": {
                "actions": [
                    {
                        "actionType": "toast",
                        "args": {
                            "msg": "操作成功",
                            "level": "success"
                        }
                    }
                ]
            }
        }
    })


@dataclass
class AlertComponent:
    """Alert 提示框"""
    
    type_name: str = "alert"
    description: str = "提示框组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "body": "内容",
        "level": "级别：info/success/warning/danger",
        "showCloseButton": "显示关闭按钮",
        "closeButtonClassName": "关闭按钮样式",
        "showIcon": "显示图标",
        "icon": "自定义图标",
        "className": "样式类名"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "alert",
        "body": "这是一条提示信息",
        "level": "info",
        "showCloseButton": True
    })


@dataclass
class NavComponent:
    """Nav 导航"""
    
    type_name: str = "nav"
    description: str = "导航组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "links": "导航链接",
        "stacked": "是否堆叠",
        "source": "动态数据源",
        "deferApi": "延迟加载接口",
        "itemActions": "链接操作",
        "draggable": "是否可拖拽",
        "saveOrderApi": "保存排序接口",
        "itemBadge": "徽标",
        "overflow": "溢出配置"
    })
    
    link_properties: Dict[str, str] = field(default_factory=lambda: {
        "label": "文字",
        "to": "链接地址",
        "target": "打开方式",
        "icon": "图标",
        "children": "子链接",
        "unfolded": "是否展开",
        "active": "是否激活",
        "activeOn": "激活条件",
        "defer": "是否延迟加载",
        "deferApi": "延迟加载接口"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "nav",
        "stacked": True,
        "links": [
            {
                "label": "首页",
                "to": "/home",
                "icon": "fa fa-home"
            },
            {
                "label": "用户管理",
                "icon": "fa fa-users",
                "children": [
                    {
                        "label": "用户列表",
                        "to": "/users"
                    },
                    {
                        "label": "角色管理",
                        "to": "/roles"
                    }
                ]
            }
        ]
    })


@dataclass
class WizardComponent:
    """Wizard 向导"""
    
    type_name: str = "wizard"
    description: str = "向导组件，用于分步骤完成任务"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "steps": "步骤配置",
        "mode": "模式：horizontal/vertical",
        "api": "提交接口",
        "initApi": "初始化接口",
        "actionPrevLabel": "上一步按钮文本",
        "actionNextLabel": "下一步按钮文本",
        "actionNextSaveLabel": "保存并下一步按钮文本",
        "actionFinishLabel": "完成按钮文本",
        "className": "样式类名",
        "actionClassName": "按钮样式",
        "reload": "提交后刷新目标",
        "redirect": "提交后跳转",
        "target": "提交目标",
        "startStep": "起始步骤"
    })
    
    step_properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "步骤标题",
        "mode": "表单模式",
        "body": "步骤内容",
        "api": "当前步骤保存接口",
        "initApi": "当前步骤初始化接口",
        "jumpable": "是否可跳转",
        "jumpableOn": "可跳转条件"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "wizard",
        "api": "/api/wizard/submit",
        "steps": [
            {
                "title": "第一步",
                "body": [
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "姓名",
                        "required": True
                    }
                ]
            },
            {
                "title": "第二步",
                "body": [
                    {
                        "type": "input-email",
                        "name": "email",
                        "label": "邮箱",
                        "required": True
                    }
                ]
            },
            {
                "title": "第三步",
                "body": [
                    {
                        "type": "static",
                        "label": "确认信息",
                        "tpl": "姓名：${name}<br/>邮箱：${email}"
                    }
                ]
            }
        ]
    })


@dataclass
class CarouselComponent:
    """Carousel 轮播图"""
    
    type_name: str = "carousel"
    description: str = "轮播图组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "options": "轮播项",
        "itemSchema": "轮播项 Schema",
        "auto": "是否自动播放",
        "interval": "播放间隔",
        "duration": "动画时长",
        "width": "宽度",
        "height": "高度",
        "controls": "显示控制按钮",
        "controlsTheme": "控制按钮主题：light/dark",
        "animation": "动画效果：fade/slide",
        "thumbMode": "缩略图模式：contain/cover"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "carousel",
        "auto": True,
        "interval": 3000,
        "options": [
            {
                "image": "https://example.com/image1.jpg",
                "title": "标题1",
                "description": "描述1"
            },
            {
                "image": "https://example.com/image2.jpg",
                "title": "标题2",
                "description": "描述2"
            }
        ]
    })


@dataclass
class IFrameComponent:
    """IFrame 内嵌页面"""
    
    type_name: str = "iframe"
    description: str = "内嵌页面组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "src": "页面地址",
        "width": "宽度",
        "height": "高度",
        "allow": "允许的功能",
        "sandbox": "沙箱模式",
        "referrerpolicy": "引用策略"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "iframe",
        "src": "https://example.com",
        "height": 500
    })


# 导出所有功能组件
FUNCTIONAL_COMPONENTS = {
    "action": ActionComponent(),
    "button": ButtonComponent(),
    "dialog": DialogComponent(),
    "drawer": DrawerComponent(),
    "toast": ToastComponent(),
    "alert": AlertComponent(),
    "nav": NavComponent(),
    "wizard": WizardComponent(),
    "carousel": CarouselComponent(),
    "iframe": IFrameComponent()
}


def get_functional_components_summary() -> List[Dict[str, str]]:
    """获取功能组件摘要"""
    return [
        {"type": "action", "name": "行为按钮", "description": "触发各种动作"},
        {"type": "button", "name": "按钮", "description": "普通按钮"},
        {"type": "dialog", "name": "弹窗", "description": "模态弹窗"},
        {"type": "drawer", "name": "抽屉", "description": "侧边抽屉"},
        {"type": "toast", "name": "轻提示", "description": "轻量级提示"},
        {"type": "alert", "name": "提示框", "description": "警告提示框"},
        {"type": "nav", "name": "导航", "description": "导航菜单"},
        {"type": "wizard", "name": "向导", "description": "分步向导"},
        {"type": "carousel", "name": "轮播图", "description": "图片轮播"},
        {"type": "iframe", "name": "内嵌页面", "description": "嵌入外部页面"}
    ]
