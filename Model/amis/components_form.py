"""
AMIS 表单组件知识库
包含 Form、各种输入组件、表单校验等知识
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FormComponent:
    """Form 表单组件"""
    
    type_name: str = "form"
    description: str = "表单组件，用于数据输入和提交"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "title": "表单标题",
        "body": "表单项集合",
        "mode": "展示模式：normal/horizontal/inline",
        "horizontal": "水平模式配置",
        "labelAlign": "标签对齐：right/left",
        "labelWidth": "标签宽度",
        "wrapWithPanel": "是否用 panel 包裹",
        "panelClassName": "panel 的 CSS 类名",
        "api": "提交接口",
        "initApi": "初始化接口",
        "interval": "轮询间隔",
        "silentPolling": "静默轮询",
        "stopAutoRefreshWhen": "停止轮询条件",
        "initFetch": "是否初始拉取",
        "initFetchOn": "初始拉取条件",
        "initAsyncApi": "异步初始化接口",
        "initFinishedField": "异步完成标识字段",
        "initCheckInterval": "异步检查间隔",
        "asyncApi": "异步提交接口",
        "checkInterval": "异步检查间隔",
        "finishedField": "异步完成标识字段",
        "submitText": "提交按钮文本",
        "submitOnChange": "值变化即提交",
        "submitOnInit": "初始化即提交",
        "resetAfterSubmit": "提交后重置",
        "clearAfterSubmit": "提交后清空",
        "preventEnterSubmit": "禁用回车提交",
        "trimValues": "去除空格",
        "promptPageLeave": "页面离开提示",
        "columnCount": "列数",
        "inheritData": "继承父级数据",
        "canAccessSuperData": "可访问父级数据",
        "persistData": "持久化存储",
        "persistDataKeys": "持久化字段",
        "clearPersistDataAfterSubmit": "提交后清除持久化",
        "debug": "开启调试",
        "redirect": "提交后跳转",
        "reload": "提交后刷新目标",
        "target": "提交后刷新目标",
        "feedback": "提交后反馈",
        "messages": "消息提示配置",
        "actions": "底部按钮",
        "rules": "组合校验规则"
    })
    
    mode_types: Dict[str, str] = field(default_factory=lambda: {
        "normal": "默认模式，标签在上，控件在下",
        "horizontal": "水平模式，标签在左，控件在右",
        "inline": "内联模式，所有表单项在一行"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "form",
        "api": "/api/submit",
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
    })
    
    horizontal_mode_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "form",
        "mode": "horizontal",
        "horizontal": {
            "left": 3,
            "right": 9
        },
        "body": [
            {
                "type": "input-text",
                "name": "name",
                "label": "姓名"
            }
        ]
    })
    
    with_init_api_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "form",
        "initApi": "/api/form/init",
        "api": "/api/form/submit",
        "body": [
            {
                "type": "input-text",
                "name": "name",
                "label": "姓名"
            }
        ]
    })


@dataclass
class InputTextComponent:
    """InputText 文本输入框"""
    
    type_name: str = "input-text"
    description: str = "文本输入框"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "name": "字段名",
        "label": "标签",
        "placeholder": "占位符",
        "value": "默认值",
        "clearable": "是否可清除",
        "disabled": "是否禁用",
        "readOnly": "是否只读",
        "required": "是否必填",
        "validations": "校验规则",
        "validationErrors": "校验错误提示",
        "addOn": "输入框附加组件",
        "prefix": "前缀",
        "suffix": "后缀",
        "showCounter": "显示计数器",
        "maxLength": "最大长度",
        "minLength": "最小长度",
        "trimContents": "去除空格",
        "transform": "值转换",
        "autoComplete": "自动完成",
        "options": "自动完成选项",
        "source": "自动完成数据源",
        "multiple": "多选",
        "delimiter": "分隔符",
        "valueType": "值类型"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-text",
        "name": "name",
        "label": "姓名",
        "placeholder": "请输入姓名",
        "required": True
    })
    
    with_validation_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-text",
        "name": "phone",
        "label": "手机号",
        "validations": {
            "isPhoneNumber": True
        },
        "validationErrors": {
            "isPhoneNumber": "请输入有效的手机号"
        }
    })


@dataclass
class InputNumberComponent:
    """InputNumber 数字输入框"""
    
    type_name: str = "input-number"
    description: str = "数字输入框"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "min": "最小值",
        "max": "最大值",
        "step": "步长",
        "precision": "精度",
        "showSteps": "显示步进按钮",
        "prefix": "前缀",
        "suffix": "后缀",
        "kilobitSeparator": "千分位分隔符",
        "unitOptions": "单位选项"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-number",
        "name": "age",
        "label": "年龄",
        "min": 0,
        "max": 150
    })


@dataclass
class InputEmailComponent:
    """InputEmail 邮箱输入框"""
    
    type_name: str = "input-email"
    description: str = "邮箱输入框，自动校验邮箱格式"
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-email",
        "name": "email",
        "label": "邮箱",
        "required": True
    })


@dataclass
class InputPasswordComponent:
    """InputPassword 密码输入框"""
    
    type_name: str = "input-password"
    description: str = "密码输入框"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "revealPassword": "是否显示密码切换按钮"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-password",
        "name": "password",
        "label": "密码",
        "required": True
    })


@dataclass
class TextareaComponent:
    """Textarea 多行文本输入框"""
    
    type_name: str = "textarea"
    description: str = "多行文本输入框"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "minRows": "最小行数",
        "maxRows": "最大行数",
        "trimContents": "去除空格",
        "showCounter": "显示计数器",
        "maxLength": "最大长度"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "textarea",
        "name": "description",
        "label": "描述",
        "minRows": 3,
        "maxRows": 10
    })


@dataclass
class SelectComponent:
    """Select 下拉选择框"""
    
    type_name: str = "select"
    description: str = "下拉选择框"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "options": "选项列表",
        "source": "动态选项接口",
        "multiple": "是否多选",
        "searchable": "是否可搜索",
        "clearable": "是否可清除",
        "checkAll": "是否显示全选",
        "checkAllLabel": "全选文本",
        "defaultCheckAll": "默认全选",
        "delimiter": "分隔符",
        "extractValue": "提取值",
        "joinValues": "拼接值",
        "autoComplete": "自动完成接口",
        "addApi": "新增接口",
        "addControls": "新增表单项",
        "creatable": "是否可新增",
        "createBtnLabel": "新增按钮文本",
        "editable": "是否可编辑",
        "editApi": "编辑接口",
        "editControls": "编辑表单项",
        "removable": "是否可删除",
        "deleteApi": "删除接口"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "select",
        "name": "city",
        "label": "城市",
        "options": [
            {"label": "北京", "value": "beijing"},
            {"label": "上海", "value": "shanghai"},
            {"label": "广州", "value": "guangzhou"}
        ]
    })
    
    with_source_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "select",
        "name": "category",
        "label": "分类",
        "source": "/api/categories",
        "searchable": True
    })


@dataclass
class CheckboxesComponent:
    """Checkboxes 复选框组"""
    
    type_name: str = "checkboxes"
    description: str = "复选框组"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "options": "选项列表",
        "source": "动态选项接口",
        "delimiter": "分隔符",
        "extractValue": "提取值",
        "joinValues": "拼接值",
        "columnsCount": "列数",
        "checkAll": "是否显示全选",
        "defaultCheckAll": "默认全选",
        "inline": "是否内联"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "checkboxes",
        "name": "hobbies",
        "label": "爱好",
        "options": [
            {"label": "阅读", "value": "reading"},
            {"label": "运动", "value": "sports"},
            {"label": "音乐", "value": "music"}
        ]
    })


@dataclass
class RadiosComponent:
    """Radios 单选框组"""
    
    type_name: str = "radios"
    description: str = "单选框组"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "options": "选项列表",
        "source": "动态选项接口",
        "columnsCount": "列数",
        "inline": "是否内联"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "radios",
        "name": "gender",
        "label": "性别",
        "options": [
            {"label": "男", "value": "male"},
            {"label": "女", "value": "female"}
        ]
    })


@dataclass
class SwitchComponent:
    """Switch 开关"""
    
    type_name: str = "switch"
    description: str = "开关组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "option": "选项说明",
        "trueValue": "开启时的值",
        "falseValue": "关闭时的值",
        "onText": "开启时显示的文本",
        "offText": "关闭时显示的文本"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "switch",
        "name": "enabled",
        "label": "是否启用",
        "onText": "启用",
        "offText": "禁用"
    })


@dataclass
class DateComponent:
    """Date 日期选择器"""
    
    type_name: str = "input-date"
    description: str = "日期选择器"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "format": "日期格式",
        "inputFormat": "输入格式",
        "valueFormat": "值格式",
        "placeholder": "占位符",
        "shortcuts": "快捷键",
        "minDate": "最小日期",
        "maxDate": "最大日期",
        "clearable": "是否可清除",
        "embed": "是否内嵌"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-date",
        "name": "date",
        "label": "日期",
        "format": "YYYY-MM-DD"
    })


@dataclass
class DatetimeComponent:
    """Datetime 日期时间选择器"""
    
    type_name: str = "input-datetime"
    description: str = "日期时间选择器"
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-datetime",
        "name": "datetime",
        "label": "日期时间",
        "format": "YYYY-MM-DD HH:mm:ss"
    })


@dataclass
class DateRangeComponent:
    """DateRange 日期范围选择器"""
    
    type_name: str = "input-date-range"
    description: str = "日期范围选择器"
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-date-range",
        "name": "dateRange",
        "label": "日期范围"
    })


@dataclass
class FileComponent:
    """File 文件上传"""
    
    type_name: str = "input-file"
    description: str = "文件上传组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "receiver": "上传接口",
        "accept": "接受的文件类型",
        "maxSize": "最大文件大小",
        "maxLength": "最大文件数量",
        "multiple": "是否多选",
        "drag": "是否支持拖拽",
        "autoUpload": "是否自动上传",
        "hideUploadButton": "隐藏上传按钮",
        "downloadUrl": "下载地址",
        "useChunk": "是否分块上传",
        "chunkSize": "分块大小",
        "startChunkApi": "开始分块接口",
        "chunkApi": "分块上传接口",
        "finishChunkApi": "完成分块接口"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-file",
        "name": "file",
        "label": "文件",
        "receiver": "/api/upload",
        "accept": ".jpg,.png,.pdf"
    })


@dataclass
class ImageComponent:
    """Image 图片上传"""
    
    type_name: str = "input-image"
    description: str = "图片上传组件"
    
    properties: Dict[str, str] = field(default_factory=lambda: {
        "receiver": "上传接口",
        "accept": "接受的图片类型",
        "maxSize": "最大文件大小",
        "maxLength": "最大图片数量",
        "multiple": "是否多选",
        "crop": "裁剪配置",
        "cropFormat": "裁剪格式",
        "cropQuality": "裁剪质量",
        "limit": "限制配置",
        "frameImage": "边框图片",
        "fixedSize": "固定尺寸",
        "fixedSizeClassName": "固定尺寸类名"
    })
    
    basic_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "input-image",
        "name": "avatar",
        "label": "头像",
        "receiver": "/api/upload/image",
        "accept": ".jpg,.png"
    })


@dataclass
class FormValidation:
    """表单校验"""
    
    validation_types: Dict[str, str] = field(default_factory=lambda: {
        "isRequired": "必填",
        "isEmail": "邮箱格式",
        "isUrl": "URL 格式",
        "isInt": "整数",
        "isAlpha": "字母",
        "isNumeric": "数字",
        "isAlphanumeric": "字母或数字",
        "isFloat": "浮点数",
        "isWords": "单词",
        "isUrlPath": "URL 路径",
        "isPhoneNumber": "手机号",
        "isTelNumber": "电话号码",
        "isZipcode": "邮编",
        "isId": "身份证号",
        "isJson": "JSON 格式",
        "isLength": "长度",
        "minLength": "最小长度",
        "maxLength": "最大长度",
        "minimum": "最小值",
        "maximum": "最大值",
        "equals": "等于",
        "equalsField": "等于某个字段",
        "matchRegexp": "正则匹配"
    })
    
    validation_example: Dict[str, Any] = field(default_factory=lambda: {
        "type": "form",
        "body": [
            {
                "type": "input-text",
                "name": "username",
                "label": "用户名",
                "required": True,
                "validations": {
                    "minLength": 3,
                    "maxLength": 20,
                    "matchRegexp": "/^[a-zA-Z0-9_]+$/"
                },
                "validationErrors": {
                    "minLength": "用户名至少3个字符",
                    "maxLength": "用户名最多20个字符",
                    "matchRegexp": "用户名只能包含字母、数字和下划线"
                }
            },
            {
                "type": "input-password",
                "name": "password",
                "label": "密码",
                "required": True,
                "validations": {
                    "minLength": 6
                }
            },
            {
                "type": "input-password",
                "name": "confirmPassword",
                "label": "确认密码",
                "required": True,
                "validations": {
                    "equalsField": "password"
                },
                "validationErrors": {
                    "equalsField": "两次密码输入不一致"
                }
            }
        ]
    })


# 导出所有表单组件
FORM_COMPONENTS = {
    "form": FormComponent(),
    "input-text": InputTextComponent(),
    "input-number": InputNumberComponent(),
    "input-email": InputEmailComponent(),
    "input-password": InputPasswordComponent(),
    "textarea": TextareaComponent(),
    "select": SelectComponent(),
    "checkboxes": CheckboxesComponent(),
    "radios": RadiosComponent(),
    "switch": SwitchComponent(),
    "input-date": DateComponent(),
    "input-datetime": DatetimeComponent(),
    "input-date-range": DateRangeComponent(),
    "input-file": FileComponent(),
    "input-image": ImageComponent(),
    "validation": FormValidation()
}


def get_form_components_summary() -> List[Dict[str, str]]:
    """获取表单组件摘要"""
    return [
        {"type": "form", "name": "表单", "description": "表单容器"},
        {"type": "input-text", "name": "文本框", "description": "单行文本输入"},
        {"type": "input-number", "name": "数字框", "description": "数字输入"},
        {"type": "input-email", "name": "邮箱框", "description": "邮箱输入"},
        {"type": "input-password", "name": "密码框", "description": "密码输入"},
        {"type": "textarea", "name": "多行文本", "description": "多行文本输入"},
        {"type": "select", "name": "下拉框", "description": "下拉选择"},
        {"type": "checkboxes", "name": "复选框", "description": "多项选择"},
        {"type": "radios", "name": "单选框", "description": "单项选择"},
        {"type": "switch", "name": "开关", "description": "开关切换"},
        {"type": "input-date", "name": "日期", "description": "日期选择"},
        {"type": "input-datetime", "name": "日期时间", "description": "日期时间选择"},
        {"type": "input-date-range", "name": "日期范围", "description": "日期范围选择"},
        {"type": "input-file", "name": "文件上传", "description": "文件上传"},
        {"type": "input-image", "name": "图片上传", "description": "图片上传"}
    ]
