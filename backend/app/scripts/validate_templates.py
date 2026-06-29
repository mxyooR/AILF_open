#!/usr/bin/env python3
"""
模板验证器 - 检查模板文件的数据一致性

用法:
    python validate_templates.py                    # 验证所有模板
    python validate_templates.py --fix              # 验证并自动修复
    python validate_templates.py --verbose          # 详细输出
    python validate_templates.py --dir <path>       # 指定目录
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ValidationError:
    """验证错误"""
    file_path: str
    workflow_name: str
    node_id: str
    error_type: str  # invalid_child_ref, invalid_parent_ref, missing_bidirectional, invalid_api_ref, invalid_node_id_format, missing_required_field
    message: str
    suggestion: str


@dataclass
class ValidationWarning:
    """验证警告"""
    file_path: str
    workflow_name: str
    node_id: str
    warning_type: str
    message: str
    suggestion: str


@dataclass
class FileValidationResult:
    """单个文件的验证结果"""
    file_path: str
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)


@dataclass
class ValidationReport:
    """完整的验证报告"""
    total_files: int
    passed_files: int
    failed_files: int
    results: List[FileValidationResult] = field(default_factory=list)


class TemplateValidator:
    """模板验证器 - 检查模板文件的数据一致性"""
    
    # 节点必需字段
    REQUIRED_NODE_FIELDS = {'id', 'name', 'type', 'position', 'parent_nodes', 'child_nodes'}
    
    # 有效的节点类型
    VALID_NODE_TYPES = {'start', 'end', 'user_input', 'api_call', 'condition', 'notification'}
    
    # snake_case 格式正则
    SNAKE_CASE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
    
    # 字段类型到验证函数的映射
    FIELD_TYPE_VALIDATORS = {
        'text': lambda v, f: isinstance(v, str),
        'number': lambda v, f: isinstance(v, (int, float)),
        'select': lambda v, f: v in (f.get('options') or []) if f.get('options') else isinstance(v, str),
        'date': lambda v, f: isinstance(v, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', v),
        'datetime': lambda v, f: isinstance(v, str) and ('T' in v or re.match(r'^\d{4}-\d{2}-\d{2}', v)),
        'email': lambda v, f: isinstance(v, str) and '@' in v,
        'phone': lambda v, f: isinstance(v, str),
        'boolean': lambda v, f: isinstance(v, bool),
    }
    
    def __init__(self, template_dir: str, verbose: bool = False):
        """初始化验证器
        
        Args:
            template_dir: 模板目录路径
            verbose: 是否输出详细信息
        """
        self.template_dir = Path(template_dir)
        self.verbose = verbose
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationWarning] = []
    
    def log(self, message: str) -> None:
        """输出日志（仅在 verbose 模式下）"""
        if self.verbose:
            print(f"  [INFO] {message}")
    
    def validate_all(self) -> ValidationReport:
        """验证目录下所有模板文件
        
        Returns:
            ValidationReport: 验证报告
        """
        results: List[FileValidationResult] = []
        json_files = list(self.template_dir.glob("*.json"))
        
        if not json_files:
            print(f"警告: 在 {self.template_dir} 目录下未找到 JSON 文件")
            return ValidationReport(
                total_files=0,
                passed_files=0,
                failed_files=0,
                results=[]
            )
        
        for file_path in json_files:
            self.log(f"正在验证: {file_path.name}")
            result = self.validate_file(str(file_path))
            results.append(result)
        
        passed = sum(1 for r in results if r.is_valid)
        failed = len(results) - passed
        
        return ValidationReport(
            total_files=len(results),
            passed_files=passed,
            failed_files=failed,
            results=results
        )
    
    def validate_file(self, file_path: str) -> FileValidationResult:
        """验证单个模板文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            FileValidationResult: 文件验证结果
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # 1. 验证 JSON 格式
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(ValidationError(
                file_path=file_path,
                workflow_name="",
                node_id="",
                error_type="invalid_json",
                message=f"JSON 格式无效: {str(e)}",
                suggestion="请检查 JSON 语法是否正确"
            ))
            return FileValidationResult(
                file_path=file_path,
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        except Exception as e:
            errors.append(ValidationError(
                file_path=file_path,
                workflow_name="",
                node_id="",
                error_type="file_read_error",
                message=f"文件读取错误: {str(e)}",
                suggestion="请检查文件是否存在且可读"
            ))
            return FileValidationResult(
                file_path=file_path,
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # 2. 获取 API 路由列表
        api_routes = template.get('api_routes', [])
        api_ids = {api.get('api_id') for api in api_routes if api.get('api_id')}
        self.log(f"  找到 {len(api_ids)} 个 API 定义")
        
        # 3. 验证实体和示例数据
        entities = template.get('entities', [])
        self.log(f"  找到 {len(entities)} 个实体")
        
        for entity in entities:
            entity_name = entity.get('name', '未命名实体')
            sample_data = entity.get('sample_data', [])
            if sample_data:
                self.log(f"  验证实体 '{entity_name}' 的示例数据 ({len(sample_data)} 条)")
                sample_errors = self.validate_sample_data(entity, file_path)
                errors.extend(sample_errors)
        
        # 验证示例数据引用关系
        sample_ref_errors = self.validate_sample_data_references(entities, file_path)
        errors.extend(sample_ref_errors)
        
        # 4. 验证工作流
        workflows = template.get('workflows', [])
        self.log(f"  找到 {len(workflows)} 个工作流")
        
        for workflow in workflows:
            workflow_name = workflow.get('name', '未命名工作流')
            self.log(f"  验证工作流: {workflow_name}")
            
            workflow_errors = self.validate_workflow(workflow, api_routes, file_path)
            errors.extend(workflow_errors)
        
        is_valid = len(errors) == 0
        
        return FileValidationResult(
            file_path=file_path,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def validate_workflow(self, workflow: Dict[str, Any], api_routes: List[Dict[str, Any]], file_path: str) -> List[ValidationError]:
        """验证单个工作流的一致性
        
        Args:
            workflow: 工作流定义
            api_routes: API 路由列表
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        workflow_name = workflow.get('name', '未命名工作流')
        nodes = workflow.get('nodes', [])
        
        if not nodes:
            return errors
        
        # 验证节点引用
        ref_errors = self.validate_node_references(nodes, workflow_name, file_path)
        errors.extend(ref_errors)
        
        # 验证双向引用
        bidir_errors = self.validate_bidirectional_refs(nodes, workflow_name, file_path)
        errors.extend(bidir_errors)
        
        # 验证 API 引用
        api_errors = self.validate_api_references(nodes, api_routes, workflow_name, file_path)
        errors.extend(api_errors)
        
        # 验证节点 ID 格式
        format_errors = self.validate_node_id_format(nodes, workflow_name, file_path)
        errors.extend(format_errors)
        
        # 验证必需字段
        field_errors = self.validate_required_fields(nodes, workflow_name, file_path)
        errors.extend(field_errors)
        
        return errors
    
    def validate_node_references(self, nodes: List[Dict[str, Any]], workflow_name: str, file_path: str) -> List[ValidationError]:
        """验证节点引用的有效性
        
        Args:
            nodes: 节点列表
            workflow_name: 工作流名称
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        
        # 构建节点 ID 集合
        node_ids = {node.get('id') for node in nodes if node.get('id')}
        
        for node in nodes:
            node_id = node.get('id', '未知节点')
            
            # 验证 child_nodes 引用
            child_nodes = node.get('child_nodes', [])
            for child_ref in child_nodes:
                if isinstance(child_ref, dict):
                    ref_node_id = child_ref.get('node_id')
                else:
                    ref_node_id = child_ref
                
                if ref_node_id and ref_node_id not in node_ids:
                    errors.append(ValidationError(
                        file_path=file_path,
                        workflow_name=workflow_name,
                        node_id=node_id,
                        error_type="invalid_child_ref",
                        message=f"child_nodes 引用了不存在的节点: {ref_node_id}",
                        suggestion=f"请检查节点 '{ref_node_id}' 是否存在，或修正引用"
                    ))
            
            # 验证 parent_nodes 引用
            parent_nodes = node.get('parent_nodes', [])
            for parent_id in parent_nodes:
                if parent_id and parent_id not in node_ids:
                    errors.append(ValidationError(
                        file_path=file_path,
                        workflow_name=workflow_name,
                        node_id=node_id,
                        error_type="invalid_parent_ref",
                        message=f"parent_nodes 引用了不存在的节点: {parent_id}",
                        suggestion=f"请检查节点 '{parent_id}' 是否存在，或修正引用"
                    ))
        
        return errors
    
    def validate_bidirectional_refs(self, nodes: List[Dict[str, Any]], workflow_name: str, file_path: str) -> List[ValidationError]:
        """验证双向引用的一致性
        
        如果节点 A 的 child_nodes 包含节点 B，则节点 B 的 parent_nodes 应包含节点 A
        
        Args:
            nodes: 节点列表
            workflow_name: 工作流名称
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        
        # 构建节点映射
        node_map = {node.get('id'): node for node in nodes if node.get('id')}
        
        for node in nodes:
            node_id = node.get('id')
            if not node_id:
                continue
            
            # 检查 child_nodes 的双向引用
            child_nodes = node.get('child_nodes', [])
            for child_ref in child_nodes:
                if isinstance(child_ref, dict):
                    child_id = child_ref.get('node_id')
                else:
                    child_id = child_ref
                
                if child_id and child_id in node_map:
                    child_node = node_map[child_id]
                    parent_nodes = child_node.get('parent_nodes', [])
                    
                    if node_id not in parent_nodes:
                        errors.append(ValidationError(
                            file_path=file_path,
                            workflow_name=workflow_name,
                            node_id=node_id,
                            error_type="missing_bidirectional",
                            message=f"节点 '{node_id}' 的 child_nodes 包含 '{child_id}'，但 '{child_id}' 的 parent_nodes 不包含 '{node_id}'",
                            suggestion=f"请在节点 '{child_id}' 的 parent_nodes 中添加 '{node_id}'"
                        ))
        
        return errors
    
    def validate_api_references(self, nodes: List[Dict[str, Any]], api_routes: List[Dict[str, Any]], workflow_name: str, file_path: str) -> List[ValidationError]:
        """验证 api_call 节点的 api_id 引用
        
        Args:
            nodes: 节点列表
            api_routes: API 路由列表
            workflow_name: 工作流名称
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        
        # 构建 API ID 集合
        api_ids = {api.get('api_id') for api in api_routes if api.get('api_id')}
        
        for node in nodes:
            node_id = node.get('id', '未知节点')
            node_type = node.get('type')
            
            if node_type == 'api_call':
                config = node.get('config', {})
                api_id = config.get('api_id')
                
                if api_id and api_id not in api_ids:
                    errors.append(ValidationError(
                        file_path=file_path,
                        workflow_name=workflow_name,
                        node_id=node_id,
                        error_type="invalid_api_ref",
                        message=f"api_call 节点引用了不存在的 API: {api_id}",
                        suggestion=f"请在 api_routes 中添加 api_id 为 '{api_id}' 的 API 定义，或修正引用"
                    ))
        
        return errors
    
    def validate_node_id_format(self, nodes: List[Dict[str, Any]], workflow_name: str, file_path: str) -> List[ValidationError]:
        """验证节点 ID 格式是否符合 snake_case
        
        Args:
            nodes: 节点列表
            workflow_name: 工作流名称
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表（作为警告处理）
        """
        errors: List[ValidationError] = []
        
        for node in nodes:
            node_id = node.get('id')
            
            if node_id and not self.SNAKE_CASE_PATTERN.match(node_id):
                errors.append(ValidationError(
                    file_path=file_path,
                    workflow_name=workflow_name,
                    node_id=node_id,
                    error_type="invalid_node_id_format",
                    message=f"节点 ID '{node_id}' 不符合 snake_case 格式",
                    suggestion=f"建议将节点 ID 改为 snake_case 格式，如 '{self._to_snake_case(node_id)}'"
                ))
        
        return errors
    
    def validate_required_fields(self, nodes: List[Dict[str, Any]], workflow_name: str, file_path: str) -> List[ValidationError]:
        """验证节点必需字段的完整性
        
        Args:
            nodes: 节点列表
            workflow_name: 工作流名称
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        
        for node in nodes:
            node_id = node.get('id', '未知节点')
            
            missing_fields = self.REQUIRED_NODE_FIELDS - set(node.keys())
            
            if missing_fields:
                errors.append(ValidationError(
                    file_path=file_path,
                    workflow_name=workflow_name,
                    node_id=node_id,
                    error_type="missing_required_field",
                    message=f"节点缺少必需字段: {', '.join(sorted(missing_fields))}",
                    suggestion=f"请为节点添加缺失的字段: {', '.join(sorted(missing_fields))}"
                ))
        
        return errors
    
    def _to_snake_case(self, text: str) -> str:
        """将文本转换为 snake_case 格式"""
        # 处理驼峰命名
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # 替换非字母数字字符为下划线
        s3 = re.sub(r'[^a-zA-Z0-9]', '_', s2)
        # 转小写并去除多余下划线
        s4 = re.sub(r'_+', '_', s3.lower())
        return s4.strip('_')
    
    def validate_sample_data(self, entity: Dict[str, Any], file_path: str) -> List[ValidationError]:
        """验证实体的示例数据
        
        Args:
            entity: 实体定义
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        entity_name = entity.get('name', '未命名实体')
        fields = entity.get('fields', [])
        sample_data = entity.get('sample_data', [])
        
        if not sample_data:
            return errors
        
        # 构建字段映射
        field_map = {f.get('name'): f for f in fields if f.get('name')}
        required_fields = {f.get('name') for f in fields if f.get('required')}
        
        for i, record in enumerate(sample_data):
            record_id = f"sample_data[{i}]"
            
            # 检查必填字段
            for field_name in required_fields:
                if field_name not in record or record[field_name] is None:
                    errors.append(ValidationError(
                        file_path=file_path,
                        workflow_name="",
                        node_id=f"{entity_name}.{record_id}",
                        error_type="sample_data_missing_required",
                        message=f"示例数据缺少必填字段: {field_name}",
                        suggestion=f"请为示例数据添加字段 '{field_name}'"
                    ))
            
            # 验证字段值
            for field_name, value in record.items():
                if field_name not in field_map:
                    continue  # 跳过未定义的字段
                
                field_def = field_map[field_name]
                field_type = field_def.get('type', 'text')
                validation = field_def.get('validation', {})
                
                if value is None:
                    continue  # 空值跳过验证
                
                # 验证字段类型
                validator = self.FIELD_TYPE_VALIDATORS.get(field_type)
                if validator and not validator(value, field_def):
                    errors.append(ValidationError(
                        file_path=file_path,
                        workflow_name="",
                        node_id=f"{entity_name}.{record_id}",
                        error_type="sample_data_type_mismatch",
                        message=f"字段 '{field_name}' 的值类型不匹配，期望 {field_type}，实际值: {value}",
                        suggestion=f"请修正字段 '{field_name}' 的值类型"
                    ))
                
                # 验证正则表达式
                if validation and 'pattern' in validation and isinstance(value, str):
                    pattern = validation['pattern']
                    try:
                        if not re.match(pattern, value):
                            errors.append(ValidationError(
                                file_path=file_path,
                                workflow_name="",
                                node_id=f"{entity_name}.{record_id}",
                                error_type="sample_data_pattern_mismatch",
                                message=f"字段 '{field_name}' 的值 '{value}' 不符合正则表达式: {pattern}",
                                suggestion=f"请修正字段 '{field_name}' 的值以符合格式要求"
                            ))
                    except re.error:
                        pass  # 忽略无效的正则表达式
                
                # 验证最大长度
                if validation and 'maxLength' in validation and isinstance(value, str):
                    max_length = validation['maxLength']
                    if len(value) > max_length:
                        errors.append(ValidationError(
                            file_path=file_path,
                            workflow_name="",
                            node_id=f"{entity_name}.{record_id}",
                            error_type="sample_data_max_length_exceeded",
                            message=f"字段 '{field_name}' 的值长度 {len(value)} 超过最大长度 {max_length}",
                            suggestion=f"请缩短字段 '{field_name}' 的值"
                        ))
                
                # 验证数值范围
                if validation and isinstance(value, (int, float)):
                    if 'min' in validation and value < validation['min']:
                        errors.append(ValidationError(
                            file_path=file_path,
                            workflow_name="",
                            node_id=f"{entity_name}.{record_id}",
                            error_type="sample_data_min_value",
                            message=f"字段 '{field_name}' 的值 {value} 小于最小值 {validation['min']}",
                            suggestion=f"请增大字段 '{field_name}' 的值"
                        ))
                    if 'max' in validation and value > validation['max']:
                        errors.append(ValidationError(
                            file_path=file_path,
                            workflow_name="",
                            node_id=f"{entity_name}.{record_id}",
                            error_type="sample_data_max_value",
                            message=f"字段 '{field_name}' 的值 {value} 大于最大值 {validation['max']}",
                            suggestion=f"请减小字段 '{field_name}' 的值"
                        ))
        
        return errors
    
    def validate_sample_data_references(self, entities: List[Dict[str, Any]], file_path: str) -> List[ValidationError]:
        """验证示例数据之间的引用关系
        
        Args:
            entities: 实体列表
            file_path: 文件路径
            
        Returns:
            List[ValidationError]: 错误列表
        """
        errors: List[ValidationError] = []
        
        # 构建实体映射和示例数据索引
        entity_map = {e.get('name'): e for e in entities if e.get('name')}
        
        # 构建各实体的示例数据值集合（用于引用验证）
        sample_values: Dict[str, Dict[str, Set]] = {}  # entity_name -> field_name -> values
        
        for entity in entities:
            entity_name = entity.get('name')
            if not entity_name:
                continue
            
            sample_data = entity.get('sample_data', [])
            if not sample_data:
                continue
            
            sample_values[entity_name] = {}
            fields = entity.get('fields', [])
            
            for field in fields:
                field_name = field.get('name')
                if not field_name:
                    continue
                
                # 收集该字段的所有示例值
                values = set()
                for record in sample_data:
                    value = record.get(field_name)
                    if value is not None:
                        values.add(value)
                
                sample_values[entity_name][field_name] = values
        
        # 定义引用关系（铁路售票系统特定）
        reference_rules = [
            # (源实体, 源字段, 目标实体, 目标字段)
            ('train', 'departure_station', 'station', 'station_name'),
            ('train', 'arrival_station', 'station', 'station_name'),
            ('ticket', 'train_number', 'train', 'train_number'),
            ('ticket', 'departure_station', 'station', 'station_name'),
            ('ticket', 'arrival_station', 'station', 'station_name'),
            ('ticket', 'passenger_name', 'passenger', 'name'),
            ('ticket', 'passenger_id_card', 'passenger', 'id_card'),
            ('seat', 'train_number', 'train', 'train_number'),
            ('order', 'passenger_name', 'passenger', 'name'),
            ('order', 'passenger_phone', 'passenger', 'phone'),
        ]
        
        for src_entity, src_field, tgt_entity, tgt_field in reference_rules:
            if src_entity not in sample_values or tgt_entity not in sample_values:
                continue
            
            src_values = sample_values.get(src_entity, {}).get(src_field, set())
            tgt_values = sample_values.get(tgt_entity, {}).get(tgt_field, set())
            
            # 检查源实体的值是否都在目标实体中存在
            for value in src_values:
                if value and value not in tgt_values:
                    errors.append(ValidationError(
                        file_path=file_path,
                        workflow_name="",
                        node_id=f"{src_entity}.{src_field}",
                        error_type="sample_data_invalid_reference",
                        message=f"实体 '{src_entity}' 的字段 '{src_field}' 引用了不存在的值: '{value}'（应存在于 {tgt_entity}.{tgt_field}）",
                        suggestion=f"请在实体 '{tgt_entity}' 的示例数据中添加 {tgt_field}='{value}' 的记录，或修正引用"
                    ))
        
        return errors
    
    def fix_issues(self, auto_fix: bool = False) -> int:
        """尝试自动修复问题
        
        Args:
            auto_fix: 是否自动修复
            
        Returns:
            int: 修复的问题数量
        """
        if not auto_fix:
            return 0
        
        fixed_count = 0
        json_files = list(self.template_dir.glob("*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                
                modified = False
                workflows = template.get('workflows', [])
                
                for workflow in workflows:
                    nodes = workflow.get('nodes', [])
                    node_map = {node.get('id'): node for node in nodes if node.get('id')}
                    
                    # 修复双向引用不一致
                    for node in nodes:
                        node_id = node.get('id')
                        if not node_id:
                            continue
                        
                        child_nodes = node.get('child_nodes', [])
                        for child_ref in child_nodes:
                            if isinstance(child_ref, dict):
                                child_id = child_ref.get('node_id')
                            else:
                                child_id = child_ref
                            
                            if child_id and child_id in node_map:
                                child_node = node_map[child_id]
                                parent_nodes = child_node.get('parent_nodes', [])
                                
                                if node_id not in parent_nodes:
                                    parent_nodes.append(node_id)
                                    child_node['parent_nodes'] = parent_nodes
                                    modified = True
                                    fixed_count += 1
                                    print(f"  [FIX] 在 '{child_id}' 的 parent_nodes 中添加了 '{node_id}'")
                
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(template, f, ensure_ascii=False, indent=2)
                    print(f"  [SAVED] 已保存修复后的文件: {file_path}")
            
            except Exception as e:
                print(f"  [ERROR] 修复文件 {file_path} 时出错: {e}")
        
        return fixed_count


def print_report(report: ValidationReport) -> None:
    """打印验证报告"""
    print("\n" + "=" * 60)
    print("模板验证报告")
    print("=" * 60)
    print(f"检查文件数: {report.total_files}")
    print(f"通过文件数: {report.passed_files}")
    print(f"失败文件数: {report.failed_files}")
    print("=" * 60)
    
    for result in report.results:
        status = "✓ 通过" if result.is_valid else "✗ 失败"
        print(f"\n{status}: {result.file_path}")
        
        if result.errors:
            print(f"  错误数: {len(result.errors)}")
            for error in result.errors:
                print(f"    [{error.error_type}] 工作流: {error.workflow_name}, 节点: {error.node_id}")
                print(f"      消息: {error.message}")
                print(f"      建议: {error.suggestion}")
        
        if result.warnings:
            print(f"  警告数: {len(result.warnings)}")
            for warning in result.warnings:
                print(f"    [{warning.warning_type}] 工作流: {warning.workflow_name}, 节点: {warning.node_id}")
                print(f"      消息: {warning.message}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='模板验证器 - 检查模板文件的数据一致性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python validate_templates.py                    # 验证所有模板
  python validate_templates.py --fix              # 验证并自动修复
  python validate_templates.py --verbose          # 详细输出
  python validate_templates.py --dir <path>       # 指定目录
        """
    )
    
    parser.add_argument(
        '--dir',
        type=str,
        default=None,
        help='模板目录路径 (默认: backend/app/templates)'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='尝试自动修复可修复的问题'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='输出详细的验证过程信息'
    )
    
    args = parser.parse_args()
    
    # 确定模板目录
    if args.dir:
        template_dir = args.dir
    else:
        # 尝试找到默认目录
        script_dir = Path(__file__).parent
        possible_dirs = [
            script_dir.parent / 'templates',  # backend/app/templates
            Path('backend/app/templates'),
            Path('app/templates'),
            Path('templates'),
        ]
        
        template_dir = None
        for d in possible_dirs:
            if d.exists():
                template_dir = str(d)
                break
        
        if not template_dir:
            print("错误: 未找到模板目录，请使用 --dir 参数指定")
            sys.exit(1)
    
    print(f"模板目录: {template_dir}")
    
    # 创建验证器并执行验证
    validator = TemplateValidator(template_dir, verbose=args.verbose)
    report = validator.validate_all()
    
    # 打印报告
    print_report(report)
    
    # 如果需要修复
    if args.fix and report.failed_files > 0:
        print("\n正在尝试自动修复...")
        fixed_count = validator.fix_issues(auto_fix=True)
        print(f"已修复 {fixed_count} 个问题")
        
        # 重新验证
        print("\n重新验证...")
        report = validator.validate_all()
        print_report(report)
    
    # 返回退出码
    sys.exit(0 if report.failed_files == 0 else 1)


if __name__ == '__main__':
    main()
