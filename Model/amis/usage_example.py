"""
AMIS 知识库使用示例
演示如何使用本知识库进行数据集构建和知识查询
"""

import json
from core_concepts import AMIS_CORE_CONCEPTS, get_concept_summary
from components_layout import LAYOUT_COMPONENTS, get_layout_components_summary
from components_form import FORM_COMPONENTS, get_form_components_summary
from components_data import DATA_COMPONENTS, get_data_components_summary
from components_functional import FUNCTIONAL_COMPONENTS, get_functional_components_summary
from examples import AMIS_EXAMPLES, get_all_examples
from dataset_builder import DatasetBuilder


def demo_core_concepts():
    """演示核心概念查询"""
    print("=" * 60)
    print("1. 核心概念查询")
    print("=" * 60)
    
    # 获取概念摘要
    summary = get_concept_summary()
    print("\n框架名称:", summary['framework_name'])
    print("类型:", summary['type'])
    print("\n核心概念:")
    for concept in summary['core_concepts']:
        print(f"  - {concept}")
    
    # 查看 AMIS 介绍
    intro = AMIS_CORE_CONCEPTS['introduction']
    print(f"\n{intro.name} 描述:")
    print(f"  {intro.description}")
    print("\n主要优势:")
    for i, advantage in enumerate(intro.advantages[:3], 1):
        print(f"  {i}. {advantage}")
    
    # 查看 Schema 基础
    schema = AMIS_CORE_CONCEPTS['schema_basics']
    print("\n最简单的 Schema 配置:")
    print(json.dumps(schema.minimal_schema, indent=2, ensure_ascii=False))


def demo_components():
    """演示组件查询"""
    print("\n" + "=" * 60)
    print("2. 组件查询")
    print("=" * 60)
    
    # 布局组件
    print("\n布局组件列表:")
    layout_summary = get_layout_components_summary()
    for comp in layout_summary[:3]:
        print(f"  - {comp['name']} ({comp['type']}): {comp['description']}")
    
    # 查看 Page 组件详情
    page = LAYOUT_COMPONENTS['page']
    print(f"\n{page.type_name} 组件:")
    print(f"  描述: {page.description}")
    print(f"  主要属性: {', '.join(list(page.properties.keys())[:5])}")
    print("\n基本示例:")
    print(json.dumps(page.basic_example, indent=2, ensure_ascii=False))
    
    # 表单组件
    print("\n表单组件列表:")
    form_summary = get_form_components_summary()
    for comp in form_summary[:5]:
        print(f"  - {comp['name']} ({comp['type']}): {comp['description']}")
    
    # 查看 Form 组件详情
    form = FORM_COMPONENTS['form']
    print(f"\n{form.type_name} 组件展示模式:")
    for mode, desc in form.mode_types.items():
        print(f"  - {mode}: {desc}")


def demo_examples():
    """演示完整示例"""
    print("\n" + "=" * 60)
    print("3. 完整示例")
    print("=" * 60)
    
    # 获取所有示例
    all_examples = get_all_examples()
    print(f"\n共有 {len(all_examples)} 个完整示例:")
    for example in all_examples:
        print(f"  - {example['name']}: {example['description']}")
    
    # 查看用户管理示例
    user_mgmt = AMIS_EXAMPLES['user_management']
    print(f"\n示例: {user_mgmt.name}")
    print(f"描述: {user_mgmt.description}")
    print("\nSchema 结构:")
    schema_str = json.dumps(user_mgmt.schema, indent=2, ensure_ascii=False)
    # 只显示前 500 个字符
    print(schema_str[:500] + "...")


def demo_dataset_generation():
    """演示数据集生成"""
    print("\n" + "=" * 60)
    print("4. 数据集生成")
    print("=" * 60)
    
    builder = DatasetBuilder()
    
    # 生成问答对
    qa_pairs = builder.generate_qa_pairs()
    print(f"\n生成了 {len(qa_pairs)} 个问答对")
    print("\n示例问答对:")
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"\n问题 {i}: {qa['question']}")
        print(f"答案 {i}: {qa['answer'][:100]}...")
    
    # 生成 Schema 任务
    schema_tasks = builder.generate_schema_tasks()
    print(f"\n生成了 {len(schema_tasks)} 个 Schema 任务")
    print("\n示例任务:")
    task = schema_tasks[0]
    print(f"指令: {task['instruction']}")
    print("输出:")
    print(json.dumps(task['output'], indent=2, ensure_ascii=False))
    
    # 生成组件示例
    component_examples = builder.generate_component_examples()
    print(f"\n生成了 {len(component_examples)} 个组件示例")
    print("\n示例组件:")
    comp = component_examples[0]
    print(f"组件: {comp['component']}")
    print(f"描述: {comp['description']}")
    print(f"用途: {comp['usage']}")
    print("Schema:")
    print(json.dumps(comp['schema'], indent=2, ensure_ascii=False))


def demo_training_samples():
    """演示训练样本生成"""
    print("\n" + "=" * 60)
    print("5. 训练样本生成")
    print("=" * 60)
    
    builder = DatasetBuilder()
    
    # 生成训练样本
    samples = builder.generate_training_samples(10)
    print(f"\n生成了 {len(samples)} 个训练样本")
    
    # 统计样本类型
    qa_count = sum(1 for s in samples if s['type'] == 'qa')
    schema_count = sum(1 for s in samples if s['type'] == 'schema_generation')
    print(f"  - 问答类型: {qa_count} 个")
    print(f"  - Schema 生成类型: {schema_count} 个")
    
    # 显示示例
    print("\n示例训练样本:")
    for i, sample in enumerate(samples[:2], 1):
        print(f"\n样本 {i} (类型: {sample['type']}):")
        print(f"输入: {sample['input'][:100]}...")
        print(f"输出: {sample['output'][:100]}...")


def demo_export_dataset():
    """演示数据集导出"""
    print("\n" + "=" * 60)
    print("6. 数据集导出")
    print("=" * 60)
    
    builder = DatasetBuilder()
    
    # 导出数据集
    output_file = "amis_knowledge_dataset.json"
    dataset = builder.export_dataset(output_file)
    
    print(f"\n数据集已导出到: {output_file}")
    print(f"  - 问答对: {len(dataset['qa_pairs'])} 个")
    print(f"  - Schema 任务: {len(dataset['schema_tasks'])} 个")
    print(f"  - 组件示例: {len(dataset['component_examples'])} 个")
    
    # 生成训练样本
    training_file = "amis_training_samples.json"
    training_samples = builder.generate_training_samples(100)
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(training_samples, f, ensure_ascii=False, indent=2)
    
    print(f"\n训练样本已导出到: {training_file}")
    print(f"  - 样本数量: {len(training_samples)} 个")


def demo_knowledge_query():
    """演示知识查询"""
    print("\n" + "=" * 60)
    print("7. 知识查询示例")
    print("=" * 60)
    
    # 查询：如何创建表单？
    print("\n查询: 如何创建表单？")
    form = FORM_COMPONENTS['form']
    print(f"答案: 使用 {form.type_name} 组件")
    print(f"描述: {form.description}")
    print("基本示例:")
    print(json.dumps(form.basic_example, indent=2, ensure_ascii=False))
    
    # 查询：如何实现数据表格？
    print("\n查询: 如何实现数据表格？")
    crud = DATA_COMPONENTS['crud']
    print(f"答案: 使用 {crud.type_name} 组件")
    print(f"描述: {crud.description}")
    print(f"主要属性: {', '.join(list(crud.properties.keys())[:5])}")
    
    # 查询：支持哪些表单校验？
    print("\n查询: 支持哪些表单校验？")
    validation = FORM_COMPONENTS['validation']
    print("答案: 支持以下校验类型:")
    for vtype, desc in list(validation.validation_types.items())[:5]:
        print(f"  - {vtype}: {desc}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AMIS 知识库使用示例")
    print("=" * 60)
    
    # 运行所有演示
    demo_core_concepts()
    demo_components()
    demo_examples()
    demo_dataset_generation()
    demo_training_samples()
    demo_export_dataset()
    demo_knowledge_query()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n提示:")
    print("  1. 查看 README.md 了解知识库结构")
    print("  2. 查看 AMIS_KNOWLEDGE_SUMMARY.md 了解 AMIS 核心知识")
    print("  3. 使用 dataset_builder.py 生成自定义数据集")
    print("  4. 参考 examples.py 学习完整配置示例")


if __name__ == "__main__":
    main()
