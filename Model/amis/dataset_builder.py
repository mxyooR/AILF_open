"""
AMIS 数据集构建器
用于生成训练数据集，包含问题-答案对、Schema 生成任务等
"""

from typing import Dict, List, Any, Tuple
import json
from dataclasses import dataclass, field
import random


@dataclass
class DatasetBuilder:
    """数据集构建器"""
    
    def generate_qa_pairs(self) -> List[Dict[str, str]]:
        """生成问答对数据集"""
        qa_pairs = []
        
        # 基础概念问答
        qa_pairs.extend([
            {
                "question": "什么是 amis？",
                "answer": "amis 是一个低代码前端框架，它使用 JSON 配置来生成页面，可以减少页面开发工作量，极大提升效率。"
            },
            {
                "question": "amis 有哪些优势？",
                "answer": "amis 的主要优势包括：1) 不需要懂前端，无需学习 JavaScript、React/Vue 等；2) 不受前端技术更新影响；3) 享受 amis 的持续升级；4) 支持可视化编辑器；5) 提供 120+ 内置组件；6) 经过实战考验。"
            },
            {
                "question": "amis 的配置格式是什么？",
                "answer": "amis 使用 JSON 格式进行配置。最基本的配置包含 type 字段（指定组件类型）和其他属性字段。"
            },
            {
                "question": "amis 中的 type 字段有什么作用？",
                "answer": "type 字段是 amis 节点中最重要的字段，它告诉 amis 当前节点需要渲染什么组件。例如 type: 'page' 表示渲染 Page 组件。"
            },
            {
                "question": "什么是组件树？",
                "answer": "组件树是通过嵌套的 JSON 结构构建的页面结构。容器型组件（如 Page）的 body 属性可以包含其他组件，形成树形结构。"
            },
            {
                "question": "Page 组件有什么特殊之处？",
                "answer": "Page 是 amis 页面配置中必须且唯一的顶级节点，所有页面都必须以 Page 组件作为根节点。"
            },
            {
                "question": "什么是数据域？",
                "answer": "数据域是每个组件用于存储和访问数据的区域。组件可以访问自己的数据域，也可以通过数据链访问父组件的数据域。"
            },
            {
                "question": "如何在 amis 中使用变量？",
                "answer": "在 amis 中使用 ${变量名} 的语法来引用变量，例如 ${username} 会被替换为数据域中 username 字段的值。"
            },
            {
                "question": "amis 支持哪些表达式？",
                "answer": "amis 支持模板表达式 ${expression}、公式表达式 ${= expression}、条件表达式 ${IF(condition, true, false)} 等多种表达式类型。"
            },
            {
                "question": "什么是联动？",
                "answer": "联动是指一个组件的状态或数据变化会影响其他组件。amis 支持显隐联动、禁用联动、数据联动、选项联动等多种联动方式。"
            }
        ])
        
        # 组件相关问答
        qa_pairs.extend([
            {
                "question": "如何创建一个表单？",
                "answer": "使用 Form 组件创建表单，配置 type: 'form'，在 body 中添加表单项，通过 api 属性指定提交接口。"
            },
            {
                "question": "Form 组件有哪些展示模式？",
                "answer": "Form 组件支持三种展示模式：normal（默认模式，标签在上）、horizontal（水平模式，标签在左）、inline（内联模式，所有表单项在一行）。"
            },
            {
                "question": "如何实现表单校验？",
                "answer": "通过表单项的 validations 属性配置校验规则，validationErrors 属性配置错误提示。支持必填、邮箱、手机号、长度、正则等多种校验类型。"
            },
            {
                "question": "如何创建一个数据表格？",
                "answer": "使用 CRUD 或 Table 组件创建表格。CRUD 组件提供完整的增删改查功能，Table 组件用于纯展示。通过 columns 属性配置列。"
            },
            {
                "question": "CRUD 组件的 filter 属性有什么用？",
                "answer": "filter 属性用于配置查询条件表单，用户可以通过这个表单筛选数据。"
            },
            {
                "question": "如何实现批量操作？",
                "answer": "在 CRUD 组件中配置 bulkActions 属性，定义批量操作按钮。用户选中数据后可以执行批量操作。"
            },
            {
                "question": "如何打开一个弹窗？",
                "answer": "使用 Button 或 Action 组件，设置 actionType: 'dialog'，在 dialog 属性中配置弹窗内容。"
            },
            {
                "question": "Dialog 和 Drawer 有什么区别？",
                "answer": "Dialog 是模态弹窗，显示在页面中央；Drawer 是抽屉，从页面边缘滑出，可以设置 position 属性控制从哪个方向滑出。"
            },
            {
                "question": "如何实现文件上传？",
                "answer": "使用 input-file 或 input-image 组件，配置 receiver 属性指定上传接口。input-image 专门用于图片上传，支持裁剪等功能。"
            },
            {
                "question": "如何显示图表？",
                "answer": "使用 Chart 组件显示图表，基于 ECharts。通过 config 属性配置 ECharts 选项，或通过 api 属性动态加载数据。"
            }
        ])
        
        # 高级功能问答
        qa_pairs.extend([
            {
                "question": "如何实现页面初始化数据加载？",
                "answer": "在 Page 或 Service 组件中配置 initApi 属性，指定初始化接口。组件加载时会自动请求该接口获取数据。"
            },
            {
                "question": "如何实现数据轮询？",
                "answer": "配置 interval 属性设置轮询间隔（毫秒），silentPolling 设置是否静默轮询，stopAutoRefreshWhen 设置停止轮询的条件。"
            },
            {
                "question": "如何实现组件间通信？",
                "answer": "通过事件动作机制实现组件间通信。在组件的 onEvent 中监听事件，在 actions 中配置动作，可以调用其他组件的方法或设置其他组件的值。"
            },
            {
                "question": "如何实现表单联动？",
                "answer": "使用 visibleOn、disabledOn、hiddenOn 等属性配置显隐和禁用条件。使用 source 属性配置动态数据源，实现选项联动。"
            },
            {
                "question": "如何自定义样式？",
                "answer": "通过 className 属性添加自定义 CSS 类名，通过 style 属性添加内联样式，通过 cssVars 属性自定义 CSS 变量。"
            },
            {
                "question": "如何实现响应式布局？",
                "answer": "使用 Grid 组件的响应式配置，通过 xs、sm、md、lg 等属性设置不同屏幕尺寸下的列宽。"
            },
            {
                "question": "如何实现数据映射？",
                "answer": "使用数据映射语法，如 '&': '$$' 引用整个数据域，'newField': '${oldField}' 简单映射，支持表达式和条件映射。"
            },
            {
                "question": "如何实现多步骤表单？",
                "answer": "使用 Wizard 组件实现多步骤表单，在 steps 中配置每个步骤的表单项，支持步骤间跳转和数据保存。"
            },
            {
                "question": "如何实现快速编辑？",
                "answer": "在 Table 或 CRUD 的列配置中添加 quickEdit 属性，配置编辑表单项类型和保存接口，实现单元格快速编辑。"
            },
            {
                "question": "如何实现数据导出？",
                "answer": "在 CRUD 的 headerToolbar 中添加导出按钮，配置 actionType: 'export-csv' 或 'export-excel'，可以导出表格数据。"
            }
        ])
        
        return qa_pairs
    
    def generate_schema_tasks(self) -> List[Dict[str, Any]]:
        """生成 Schema 生成任务数据集"""
        tasks = []
        
        # 简单页面生成任务
        tasks.append({
            "instruction": "创建一个显示 'Hello World' 的页面",
            "output": {
                "type": "page",
                "body": "Hello World"
            }
        })
        
        # 表单生成任务
        tasks.append({
            "instruction": "创建一个用户登录表单，包含用户名和密码输入框，以及提交按钮",
            "output": {
                "type": "page",
                "body": {
                    "type": "form",
                    "title": "用户登录",
                    "api": "/api/login",
                    "body": [
                        {
                            "type": "input-text",
                            "name": "username",
                            "label": "用户名",
                            "required": True
                        },
                        {
                            "type": "input-password",
                            "name": "password",
                            "label": "密码",
                            "required": True
                        }
                    ]
                }
            }
        })
        
        # 表格生成任务
        tasks.append({
            "instruction": "创建一个用户列表页面，显示用户的 ID、姓名、邮箱，并提供编辑和删除操作",
            "output": {
                "type": "page",
                "title": "用户列表",
                "body": {
                    "type": "crud",
                    "api": "/api/users",
                    "columns": [
                        {"name": "id", "label": "ID"},
                        {"name": "name", "label": "姓名"},
                        {"name": "email", "label": "邮箱"},
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
                                                },
                                                {
                                                    "type": "input-email",
                                                    "name": "email",
                                                    "label": "邮箱"
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
                }
            }
        })
        
        # 仪表盘生成任务
        tasks.append({
            "instruction": "创建一个仪表盘页面，显示总用户数、活跃用户数、总订单数三个统计卡片",
            "output": {
                "type": "page",
                "title": "数据仪表盘",
                "initApi": "/api/dashboard",
                "body": {
                    "type": "grid",
                    "columns": [
                        {
                            "md": 4,
                            "body": {
                                "type": "panel",
                                "body": {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><h2>${totalUsers}</h2><p>总用户数</p></div>"
                                }
                            }
                        },
                        {
                            "md": 4,
                            "body": {
                                "type": "panel",
                                "body": {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><h2>${activeUsers}</h2><p>活跃用户数</p></div>"
                                }
                            }
                        },
                        {
                            "md": 4,
                            "body": {
                                "type": "panel",
                                "body": {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><h2>${totalOrders}</h2><p>总订单数</p></div>"
                                }
                            }
                        }
                    ]
                }
            }
        })
        
        # 搜索表单生成任务
        tasks.append({
            "instruction": "创建一个带搜索功能的商品列表，搜索条件包括关键字和分类",
            "output": {
                "type": "page",
                "title": "商品列表",
                "body": {
                    "type": "crud",
                    "api": "/api/products",
                    "filter": {
                        "title": "搜索",
                        "body": [
                            {
                                "type": "input-text",
                                "name": "keywords",
                                "label": "关键字",
                                "placeholder": "请输入商品名称"
                            },
                            {
                                "type": "select",
                                "name": "category",
                                "label": "分类",
                                "source": "/api/categories"
                            }
                        ]
                    },
                    "columns": [
                        {"name": "id", "label": "ID"},
                        {"name": "name", "label": "商品名称"},
                        {"name": "price", "label": "价格", "type": "number"},
                        {"name": "stock", "label": "库存"}
                    ]
                }
            }
        })
        
        return tasks
    
    def generate_component_examples(self) -> List[Dict[str, Any]]:
        """生成组件示例数据集"""
        examples = []
        
        # 为每个常用组件生成示例
        component_templates = [
            {
                "component": "input-text",
                "description": "文本输入框",
                "example": {
                    "type": "input-text",
                    "name": "username",
                    "label": "用户名",
                    "placeholder": "请输入用户名",
                    "required": True
                }
            },
            {
                "component": "select",
                "description": "下拉选择框",
                "example": {
                    "type": "select",
                    "name": "city",
                    "label": "城市",
                    "options": [
                        {"label": "北京", "value": "beijing"},
                        {"label": "上海", "value": "shanghai"}
                    ]
                }
            },
            {
                "component": "checkboxes",
                "description": "复选框组",
                "example": {
                    "type": "checkboxes",
                    "name": "hobbies",
                    "label": "爱好",
                    "options": [
                        {"label": "阅读", "value": "reading"},
                        {"label": "运动", "value": "sports"}
                    ]
                }
            },
            {
                "component": "radios",
                "description": "单选框组",
                "example": {
                    "type": "radios",
                    "name": "gender",
                    "label": "性别",
                    "options": [
                        {"label": "男", "value": "male"},
                        {"label": "女", "value": "female"}
                    ]
                }
            },
            {
                "component": "switch",
                "description": "开关",
                "example": {
                    "type": "switch",
                    "name": "enabled",
                    "label": "是否启用",
                    "onText": "启用",
                    "offText": "禁用"
                }
            },
            {
                "component": "input-date",
                "description": "日期选择器",
                "example": {
                    "type": "input-date",
                    "name": "date",
                    "label": "日期",
                    "format": "YYYY-MM-DD"
                }
            },
            {
                "component": "textarea",
                "description": "多行文本输入",
                "example": {
                    "type": "textarea",
                    "name": "description",
                    "label": "描述",
                    "minRows": 3,
                    "maxRows": 10
                }
            },
            {
                "component": "input-image",
                "description": "图片上传",
                "example": {
                    "type": "input-image",
                    "name": "avatar",
                    "label": "头像",
                    "receiver": "/api/upload/image"
                }
            }
        ]
        
        for template in component_templates:
            examples.append({
                "component": template["component"],
                "description": template["description"],
                "schema": template["example"],
                "usage": f"用于{template['description']}的表单控件"
            })
        
        return examples
    
    def export_dataset(self, output_file: str = "amis_dataset.json"):
        """导出完整数据集"""
        dataset = {
            "qa_pairs": self.generate_qa_pairs(),
            "schema_tasks": self.generate_schema_tasks(),
            "component_examples": self.generate_component_examples()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        return dataset
    
    def generate_training_samples(self, num_samples: int = 100) -> List[Dict[str, Any]]:
        """生成训练样本"""
        samples = []
        
        # 混合不同类型的任务
        qa_pairs = self.generate_qa_pairs()
        schema_tasks = self.generate_schema_tasks()
        
        for _ in range(num_samples):
            # 随机选择任务类型
            task_type = random.choice(['qa', 'schema'])
            
            if task_type == 'qa':
                qa = random.choice(qa_pairs)
                samples.append({
                    "type": "qa",
                    "input": qa["question"],
                    "output": qa["answer"]
                })
            else:
                task = random.choice(schema_tasks)
                samples.append({
                    "type": "schema_generation",
                    "input": task["instruction"],
                    "output": json.dumps(task["output"], ensure_ascii=False, indent=2)
                })
        
        return samples


# 使用示例
if __name__ == "__main__":
    builder = DatasetBuilder()
    
    # 生成并导出数据集
    dataset = builder.export_dataset("amis_knowledge_dataset.json")
    
    print(f"数据集生成完成！")
    print(f"问答对数量: {len(dataset['qa_pairs'])}")
    print(f"Schema 任务数量: {len(dataset['schema_tasks'])}")
    print(f"组件示例数量: {len(dataset['component_examples'])}")
    
    # 生成训练样本
    training_samples = builder.generate_training_samples(100)
    with open("amis_training_samples.json", 'w', encoding='utf-8') as f:
        json.dump(training_samples, f, ensure_ascii=False, indent=2)
    
    print(f"训练样本数量: {len(training_samples)}")
