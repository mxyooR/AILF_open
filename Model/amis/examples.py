"""
AMIS 完整示例集合
包含各种场景的完整配置示例，用于数据集构建
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class UserManagementExample:
    """用户管理系统示例"""
    
    name: str = "用户管理系统"
    description: str = "包含用户列表、新增、编辑、删除等完整功能"
    
    schema: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "title": "用户管理",
        "body": {
            "type": "crud",
            "api": "/api/users",
            "filter": {
                "title": "条件搜索",
                "body": [
                    {
                        "type": "input-text",
                        "name": "keywords",
                        "label": "关键字",
                        "placeholder": "请输入用户名或邮箱"
                    },
                    {
                        "type": "select",
                        "name": "status",
                        "label": "状态",
                        "options": [
                            {"label": "全部", "value": ""},
                            {"label": "正常", "value": "1"},
                            {"label": "禁用", "value": "0"}
                        ]
                    }
                ]
            },
            "headerToolbar": [
                {
                    "type": "button",
                    "label": "新增用户",
                    "icon": "fa fa-plus",
                    "level": "primary",
                    "actionType": "dialog",
                    "dialog": {
                        "title": "新增用户",
                        "size": "lg",
                        "body": {
                            "type": "form",
                            "api": "post:/api/users",
                            "body": [
                                {
                                    "type": "input-text",
                                    "name": "username",
                                    "label": "用户名",
                                    "required": True,
                                    "validations": {
                                        "minLength": 3,
                                        "maxLength": 20
                                    }
                                },
                                {
                                    "type": "input-email",
                                    "name": "email",
                                    "label": "邮箱",
                                    "required": True
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
                                    "type": "select",
                                    "name": "role",
                                    "label": "角色",
                                    "required": True,
                                    "options": [
                                        {"label": "管理员", "value": "admin"},
                                        {"label": "普通用户", "value": "user"}
                                    ]
                                },
                                {
                                    "type": "switch",
                                    "name": "status",
                                    "label": "状态",
                                    "value": 1,
                                    "onText": "启用",
                                    "offText": "禁用"
                                }
                            ]
                        }
                    }
                },
                "bulkActions"
            ],
            "bulkActions": [
                {
                    "label": "批量删除",
                    "actionType": "ajax",
                    "api": "delete:/api/users/batch",
                    "confirmText": "确认删除选中的用户吗？",
                    "level": "danger"
                }
            ],
            "columns": [
                {
                    "name": "id",
                    "label": "ID",
                    "width": 80
                },
                {
                    "name": "username",
                    "label": "用户名",
                    "searchable": True
                },
                {
                    "name": "email",
                    "label": "邮箱",
                    "copyable": True
                },
                {
                    "name": "role",
                    "label": "角色",
                    "type": "mapping",
                    "map": {
                        "admin": "<span class='label label-success'>管理员</span>",
                        "user": "<span class='label label-info'>普通用户</span>"
                    }
                },
                {
                    "name": "status",
                    "label": "状态",
                    "type": "status",
                    "map": {
                        "1": {"value": "启用", "status": "success"},
                        "0": {"value": "禁用", "status": "danger"}
                    }
                },
                {
                    "name": "created_at",
                    "label": "创建时间",
                    "type": "datetime"
                },
                {
                    "type": "operation",
                    "label": "操作",
                    "buttons": [
                        {
                            "type": "button",
                            "label": "编辑",
                            "level": "link",
                            "actionType": "dialog",
                            "dialog": {
                                "title": "编辑用户",
                                "size": "lg",
                                "body": {
                                    "type": "form",
                                    "initApi": "get:/api/users/${id}",
                                    "api": "put:/api/users/${id}",
                                    "body": [
                                        {
                                            "type": "input-text",
                                            "name": "username",
                                            "label": "用户名",
                                            "required": True
                                        },
                                        {
                                            "type": "input-email",
                                            "name": "email",
                                            "label": "邮箱",
                                            "required": True
                                        },
                                        {
                                            "type": "select",
                                            "name": "role",
                                            "label": "角色",
                                            "required": True,
                                            "options": [
                                                {"label": "管理员", "value": "admin"},
                                                {"label": "普通用户", "value": "user"}
                                            ]
                                        },
                                        {
                                            "type": "switch",
                                            "name": "status",
                                            "label": "状态",
                                            "onText": "启用",
                                            "offText": "禁用"
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "type": "button",
                            "label": "删除",
                            "level": "link",
                            "className": "text-danger",
                            "actionType": "ajax",
                            "confirmText": "确认删除该用户吗？",
                            "api": "delete:/api/users/${id}"
                        }
                    ]
                }
            ]
        }
    })


@dataclass
class DashboardExample:
    """仪表盘示例"""
    
    name: str = "数据仪表盘"
    description: str = "包含统计卡片、图表等数据展示"
    
    schema: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "title": "数据仪表盘",
        "initApi": "/api/dashboard/init",
        "body": [
            {
                "type": "grid",
                "columns": [
                    {
                        "md": 3,
                        "body": {
                            "type": "panel",
                            "className": "bg-primary",
                            "body": {
                                "type": "tpl",
                                "tpl": "<div class='text-center'><h2>${totalUsers}</h2><p>总用户数</p></div>"
                            }
                        }
                    },
                    {
                        "md": 3,
                        "body": {
                            "type": "panel",
                            "className": "bg-success",
                            "body": {
                                "type": "tpl",
                                "tpl": "<div class='text-center'><h2>${activeUsers}</h2><p>活跃用户</p></div>"
                            }
                        }
                    },
                    {
                        "md": 3,
                        "body": {
                            "type": "panel",
                            "className": "bg-warning",
                            "body": {
                                "type": "tpl",
                                "tpl": "<div class='text-center'><h2>${totalOrders}</h2><p>总订单数</p></div>"
                            }
                        }
                    },
                    {
                        "md": 3,
                        "body": {
                            "type": "panel",
                            "className": "bg-danger",
                            "body": {
                                "type": "tpl",
                                "tpl": "<div class='text-center'><h2>${revenue}</h2><p>总收入</p></div>"
                            }
                        }
                    }
                ]
            },
            {
                "type": "grid",
                "columns": [
                    {
                        "md": 6,
                        "body": {
                            "type": "panel",
                            "title": "销售趋势",
                            "body": {
                                "type": "chart",
                                "api": "/api/chart/sales",
                                "config": {
                                    "title": {
                                        "text": "月度销售额"
                                    },
                                    "tooltip": {
                                        "trigger": "axis"
                                    },
                                    "xAxis": {
                                        "type": "category",
                                        "data": "${months}"
                                    },
                                    "yAxis": {
                                        "type": "value"
                                    },
                                    "series": [
                                        {
                                            "name": "销售额",
                                            "type": "line",
                                            "data": "${sales}",
                                            "smooth": True
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "md": 6,
                        "body": {
                            "type": "panel",
                            "title": "用户分布",
                            "body": {
                                "type": "chart",
                                "api": "/api/chart/users",
                                "config": {
                                    "title": {
                                        "text": "用户地区分布"
                                    },
                                    "tooltip": {
                                        "trigger": "item"
                                    },
                                    "series": [
                                        {
                                            "name": "用户数",
                                            "type": "pie",
                                            "radius": "50%",
                                            "data": "${userDistribution}"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            },
            {
                "type": "panel",
                "title": "最近订单",
                "body": {
                    "type": "table",
                    "source": "${recentOrders}",
                    "columns": [
                        {"name": "order_no", "label": "订单号"},
                        {"name": "customer", "label": "客户"},
                        {"name": "amount", "label": "金额", "type": "number"},
                        {"name": "status", "label": "状态"},
                        {"name": "created_at", "label": "创建时间", "type": "datetime"}
                    ]
                }
            }
        ]
    })


@dataclass
class FormWizardExample:
    """多步骤表单示例"""
    
    name: str = "多步骤注册表单"
    description: str = "分步骤完成用户注册"
    
    schema: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "title": "用户注册",
        "body": {
            "type": "wizard",
            "api": "/api/register",
            "steps": [
                {
                    "title": "基本信息",
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
                            "type": "input-email",
                            "name": "email",
                            "label": "邮箱",
                            "required": True
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
                },
                {
                    "title": "个人信息",
                    "body": [
                        {
                            "type": "input-text",
                            "name": "realName",
                            "label": "真实姓名",
                            "required": True
                        },
                        {
                            "type": "radios",
                            "name": "gender",
                            "label": "性别",
                            "required": True,
                            "options": [
                                {"label": "男", "value": "male"},
                                {"label": "女", "value": "female"}
                            ]
                        },
                        {
                            "type": "input-date",
                            "name": "birthday",
                            "label": "生日",
                            "format": "YYYY-MM-DD"
                        },
                        {
                            "type": "input-text",
                            "name": "phone",
                            "label": "手机号",
                            "required": True,
                            "validations": {
                                "isPhoneNumber": True
                            }
                        }
                    ]
                },
                {
                    "title": "地址信息",
                    "body": [
                        {
                            "type": "select",
                            "name": "province",
                            "label": "省份",
                            "required": True,
                            "source": "/api/provinces"
                        },
                        {
                            "type": "select",
                            "name": "city",
                            "label": "城市",
                            "required": True,
                            "source": "/api/cities?province=${province}"
                        },
                        {
                            "type": "textarea",
                            "name": "address",
                            "label": "详细地址",
                            "required": True,
                            "minRows": 3
                        }
                    ]
                },
                {
                    "title": "确认信息",
                    "body": [
                        {
                            "type": "static",
                            "label": "用户名",
                            "value": "${username}"
                        },
                        {
                            "type": "static",
                            "label": "邮箱",
                            "value": "${email}"
                        },
                        {
                            "type": "static",
                            "label": "真实姓名",
                            "value": "${realName}"
                        },
                        {
                            "type": "static",
                            "label": "性别",
                            "value": "${gender}"
                        },
                        {
                            "type": "static",
                            "label": "手机号",
                            "value": "${phone}"
                        },
                        {
                            "type": "static",
                            "label": "地址",
                            "tpl": "${province} ${city} ${address}"
                        }
                    ]
                }
            ]
        }
    })


@dataclass
class ComplexFormExample:
    """复杂表单示例"""
    
    name: str = "商品发布表单"
    description: str = "包含各种表单控件的复杂表单"
    
    schema: Dict[str, Any] = field(default_factory=lambda: {
        "type": "page",
        "title": "发布商品",
        "body": {
            "type": "form",
            "api": "/api/products",
            "mode": "horizontal",
            "body": [
                {
                    "type": "tabs",
                    "tabs": [
                        {
                            "title": "基本信息",
                            "body": [
                                {
                                    "type": "input-text",
                                    "name": "name",
                                    "label": "商品名称",
                                    "required": True
                                },
                                {
                                    "type": "select",
                                    "name": "category",
                                    "label": "商品分类",
                                    "required": True,
                                    "source": "/api/categories",
                                    "searchable": True
                                },
                                {
                                    "type": "input-number",
                                    "name": "price",
                                    "label": "价格",
                                    "required": True,
                                    "min": 0,
                                    "precision": 2,
                                    "prefix": "¥"
                                },
                                {
                                    "type": "input-number",
                                    "name": "stock",
                                    "label": "库存",
                                    "required": True,
                                    "min": 0
                                },
                                {
                                    "type": "switch",
                                    "name": "status",
                                    "label": "状态",
                                    "value": 1,
                                    "onText": "上架",
                                    "offText": "下架"
                                }
                            ]
                        },
                        {
                            "title": "详细描述",
                            "body": [
                                {
                                    "type": "textarea",
                                    "name": "summary",
                                    "label": "商品简介",
                                    "required": True,
                                    "minRows": 3,
                                    "maxRows": 6,
                                    "showCounter": True,
                                    "maxLength": 200
                                },
                                {
                                    "type": "input-rich-text",
                                    "name": "description",
                                    "label": "商品详情",
                                    "required": True
                                },
                                {
                                    "type": "checkboxes",
                                    "name": "tags",
                                    "label": "商品标签",
                                    "options": [
                                        {"label": "热销", "value": "hot"},
                                        {"label": "新品", "value": "new"},
                                        {"label": "促销", "value": "sale"},
                                        {"label": "推荐", "value": "recommend"}
                                    ]
                                }
                            ]
                        },
                        {
                            "title": "商品图片",
                            "body": [
                                {
                                    "type": "input-image",
                                    "name": "cover",
                                    "label": "封面图",
                                    "required": True,
                                    "receiver": "/api/upload/image",
                                    "accept": ".jpg,.png",
                                    "maxSize": 2097152,
                                    "crop": {
                                        "aspectRatio": 1
                                    }
                                },
                                {
                                    "type": "input-image",
                                    "name": "images",
                                    "label": "商品图片",
                                    "multiple": True,
                                    "maxLength": 5,
                                    "receiver": "/api/upload/image",
                                    "accept": ".jpg,.png"
                                }
                            ]
                        },
                        {
                            "title": "规格参数",
                            "body": [
                                {
                                    "type": "combo",
                                    "name": "specs",
                                    "label": "商品规格",
                                    "multiple": True,
                                    "draggable": True,
                                    "items": [
                                        {
                                            "type": "input-text",
                                            "name": "name",
                                            "label": "规格名",
                                            "required": True
                                        },
                                        {
                                            "type": "input-text",
                                            "name": "value",
                                            "label": "规格值",
                                            "required": True
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    })


# 导出所有示例
AMIS_EXAMPLES = {
    "user_management": UserManagementExample(),
    "dashboard": DashboardExample(),
    "form_wizard": FormWizardExample(),
    "complex_form": ComplexFormExample()
}


def get_all_examples() -> List[Dict[str, Any]]:
    """获取所有示例"""
    return [
        {
            "name": example.name,
            "description": example.description,
            "schema": example.schema
        }
        for example in AMIS_EXAMPLES.values()
    ]
