"""
随机抽取样本检查脚本

检查项：
1. AMIS Schema 是否符合规范
2. 工作流样本是否只生成对应步骤的 AMIS Schema
3. 图谱是否包含所有需要的节点
4. 是否符合后端架构
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any


def load_samples(path: str, count: int = 10) -> List[Dict]:
    """加载随机样本"""
    all_samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            all_samples.append(json.loads(line))
    
    # 按类型分组
    by_type = {}
    for s in all_samples:
        t = s.get("metadata", {}).get("sample_type", "unknown")
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(s)
    
    # 每种类型抽取样本
    selected = []
    for t, samples in by_type.items():
        n = min(2, len(samples))
        selected.extend(random.sample(samples, n))
    
    return selected


def check_amis_schema(schema: Dict) -> Dict[str, Any]:
    """检查 AMIS Schema 是否符合规范"""
    issues = []
    
    # 1. 必须有 type: page
    if schema.get("type") != "page":
        issues.append("❌ 缺少 type: page")
    else:
        issues.append("✅ type: page 正确")
    
    # 2. 检查 body
    body = schema.get("body")
    if not body:
        issues.append("❌ 缺少 body")
    else:
        issues.append("✅ 有 body")
    
    # 3. 检查表单
    forms = []
    def find_forms(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "form":
                forms.append(obj)
            for v in obj.values():
                find_forms(v)
        elif isinstance(obj, list):
            for item in obj:
                find_forms(item)
    
    find_forms(schema)
    
    if forms:
        for form in forms:
            # 检查 api 配置
            api = form.get("api", {})
            if isinstance(api, dict):
                if "url" in api:
                    issues.append(f"✅ 表单有 api.url: {api['url']}")
                if "method" in api:
                    issues.append(f"✅ 表单有 api.method: {api['method']}")
                if "data" in api and "&" in api["data"]:
                    issues.append("✅ 表单有 '&': '$' 数据合并")
            
            # 检查 body 字段
            form_body = form.get("body", [])
            if form_body:
                issues.append(f"✅ 表单有 {len(form_body)} 个输入字段")
    
    return {
        "valid": not any("❌" in i for i in issues),
        "issues": issues
    }


def check_workflow_sample(sample: Dict) -> Dict[str, Any]:
    """检查工作流样本"""
    issues = []
    sample_type = sample.get("metadata", {}).get("sample_type", "")
    
    # 解析 AMIS Schema
    assistant_content = sample.get("messages", [{}])[-1].get("content", "{}")
    schema = json.loads(assistant_content)
    
    # 解析图谱
    graph = sample.get("graph_input", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    # 解析用户输入
    user_input = sample.get("messages", [{}])[1].get("content", "")
    
    if sample_type == "workflow_entry":
        issues.append("📋 样本类型: workflow_entry (工作流入口)")
        
        # 1. 检查图谱中是否有 Workflow 节点
        workflow_nodes = [n for n in nodes if n.get("type") == "workflow"]
        if workflow_nodes:
            issues.append(f"✅ 图谱包含 {len(workflow_nodes)} 个 Workflow 节点")
            for wf in workflow_nodes:
                issues.append(f"   - {wf.get('id')}: {wf.get('name')}")
        else:
            issues.append("❌ 图谱中没有 Workflow 节点")
        
        # 2. 检查图谱中是否有 API 节点（作为干扰项）
        api_nodes = [n for n in nodes if n.get("type") == "api"]
        if api_nodes:
            issues.append(f"✅ 图谱包含 {len(api_nodes)} 个 API 节点（干扰项，让 AI 学会选择）")
        
        # 3. 检查 AMIS Schema 的 api.url
        forms = []
        def find_forms(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "form":
                    forms.append(obj)
                for v in obj.values():
                    find_forms(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_forms(item)
        find_forms(schema)
        
        if forms:
            form = forms[0]
            api = form.get("api", {})
            url = api.get("url", "")
            
            if url == "/api/v1/workflow/state":
                issues.append("✅ api.url = /api/v1/workflow/state (正确)")
            else:
                issues.append(f"❌ api.url = {url} (应该是 /api/v1/workflow/state)")
            
            # 检查 workflow_id 和 node_id
            data = api.get("data", {})
            if "workflow_id" in data:
                issues.append(f"✅ 包含 workflow_id: {data['workflow_id']}")
                # 验证 workflow_id 是否与图谱中的 Workflow ID 一致
                if workflow_nodes:
                    wf_ids = [wf.get("id") for wf in workflow_nodes]
                    if data["workflow_id"] in wf_ids:
                        issues.append("✅ workflow_id 与图谱中的 Workflow ID 一致")
                    else:
                        issues.append(f"⚠️ workflow_id 不在图谱中: {wf_ids}")
            else:
                issues.append("❌ 缺少 workflow_id")
            
            if "node_id" in data:
                issues.append(f"✅ 包含 node_id: {data['node_id']}")
            else:
                issues.append("❌ 缺少 node_id")
            
            if "action" in data:
                issues.append(f"✅ 包含 action: {data['action']}")
            else:
                issues.append("❌ 缺少 action")
    
    elif sample_type == "workflow_step":
        issues.append("📋 样本类型: workflow_step (工作流步骤)")
        
        # 1. 检查图谱中是否有 WorkflowNode 节点
        wf_node_types = ["user_input", "api_call", "condition", "start", "end", "notification"]
        workflow_nodes = [n for n in nodes if n.get("type") in wf_node_types]
        if workflow_nodes:
            issues.append(f"✅ 图谱包含 {len(workflow_nodes)} 个 WorkflowNode 节点")
            for wn in workflow_nodes:
                issues.append(f"   - {wn.get('id')}: type={wn.get('type')}, name={wn.get('name')}")
        else:
            issues.append("❌ 图谱中没有 WorkflowNode 节点")
        
        # 2. 检查 Field 节点
        field_nodes = [n for n in nodes if n.get("type") == "field"]
        if field_nodes:
            issues.append(f"✅ 图谱包含 {len(field_nodes)} 个 Field 节点")
        
        # 3. 检查边
        if edges:
            issues.append(f"✅ 图谱包含 {len(edges)} 条边")
            for edge in edges[:3]:
                issues.append(f"   - {edge.get('source')} --{edge.get('relation')}--> {edge.get('target')}")
        
        # 4. 检查用户输入中的 workflow_id
        if "工作流ID：" in user_input:
            wf_id_line = [l for l in user_input.split("\n") if "工作流ID：" in l]
            if wf_id_line:
                wf_id = wf_id_line[0].split("：")[1].strip()
                issues.append(f"✅ 用户输入包含 工作流ID: {wf_id}")
                
                # 验证图谱中的节点 ID 是否以 workflow_id 开头
                for wn in workflow_nodes:
                    if wn.get("id", "").startswith(wf_id):
                        issues.append(f"✅ 图谱节点 ID 格式正确: {wn.get('id')}")
                    else:
                        issues.append(f"⚠️ 图谱节点 ID 格式可能不正确: {wn.get('id')}")
        
        # 5. 检查 AMIS Schema
        forms = []
        def find_forms(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "form":
                    forms.append(obj)
                for v in obj.values():
                    find_forms(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_forms(item)
        find_forms(schema)
        
        if forms:
            form = forms[0]
            api = form.get("api", {})
            url = api.get("url", "")
            
            if url == "/api/v1/workflow/state":
                issues.append("✅ api.url = /api/v1/workflow/state (正确)")
            else:
                issues.append(f"❌ api.url = {url} (应该是 /api/v1/workflow/state)")
    
    return {
        "issues": issues
    }


def check_api_only_sample(sample: Dict) -> Dict[str, Any]:
    """检查直接 API 调用样本"""
    issues = []
    issues.append("📋 样本类型: api_only (直接 API 调用)")
    
    # 解析 AMIS Schema
    assistant_content = sample.get("messages", [{}])[-1].get("content", "{}")
    schema = json.loads(assistant_content)
    
    # 解析图谱
    graph = sample.get("graph_input", {})
    nodes = graph.get("nodes", [])
    
    # 1. 检查图谱中的节点类型
    api_nodes = [n for n in nodes if n.get("type") == "api"]
    workflow_nodes = [n for n in nodes if n.get("type") == "workflow"]
    
    issues.append(f"✅ 图谱包含 {len(api_nodes)} 个 API 节点")
    if workflow_nodes:
        issues.append(f"✅ 图谱包含 {len(workflow_nodes)} 个 Workflow 节点（干扰项，让 AI 学会取舍）")
    
    # 2. 检查 AMIS Schema 的 api.url
    forms = []
    def find_forms(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "form":
                forms.append(obj)
            for v in obj.values():
                find_forms(v)
        elif isinstance(obj, list):
            for item in obj:
                find_forms(item)
    find_forms(schema)
    
    if forms:
        form = forms[0]
        api = form.get("api", {})
        url = api.get("url", "")
        method = api.get("method", "")
        
        # 验证 url 是否在图谱的 API 节点中
        api_paths = [n.get("path") for n in api_nodes]
        if url in api_paths:
            issues.append(f"✅ api.url = {url} (存在于图谱中)")
        else:
            issues.append(f"❌ api.url = {url} (不在图谱中: {api_paths})")
        
        # 验证 method 是否正确
        for api_node in api_nodes:
            if api_node.get("path") == url:
                expected_method = api_node.get("method", "GET").lower()
                if method == expected_method:
                    issues.append(f"✅ api.method = {method} (正确)")
                else:
                    issues.append(f"⚠️ api.method = {method} (期望: {expected_method})")
                break
    
    return {
        "issues": issues
    }


def check_rejection_sample(sample: Dict) -> Dict[str, Any]:
    """检查拒绝样本"""
    issues = []
    sample_type = sample.get("metadata", {}).get("sample_type", "")
    
    if sample_type == "rejection":
        issues.append("📋 样本类型: rejection (空图谱拒绝)")
    else:
        issues.append("📋 样本类型: rejection_mismatch (不匹配拒绝)")
    
    # 解析图谱
    graph = sample.get("graph_input", {})
    nodes = graph.get("nodes", [])
    
    if sample_type == "rejection":
        if len(nodes) == 0:
            issues.append("✅ 图谱为空（正确）")
        else:
            issues.append(f"❌ 图谱不为空，有 {len(nodes)} 个节点")
    else:
        if len(nodes) > 0:
            issues.append(f"✅ 图谱非空，有 {len(nodes)} 个节点（用于训练 AI 识别不匹配）")
        else:
            issues.append("❌ 图谱为空（应该非空）")
    
    # 解析 AMIS Schema
    assistant_content = sample.get("messages", [{}])[-1].get("content", "{}")
    schema = json.loads(assistant_content)
    
    # 检查是否有 alert 组件
    alerts = []
    def find_alerts(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "alert":
                alerts.append(obj)
            for v in obj.values():
                find_alerts(v)
        elif isinstance(obj, list):
            for item in obj:
                find_alerts(item)
    find_alerts(schema)
    
    if alerts:
        issues.append(f"✅ 包含 {len(alerts)} 个 alert 组件（拒绝提示）")
        for alert in alerts:
            level = alert.get("level", "")
            body = alert.get("body", "")[:50]
            issues.append(f"   - level={level}, body={body}...")
    
    # 检查 api.url
    forms = []
    def find_forms(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "form":
                forms.append(obj)
            for v in obj.values():
                find_forms(v)
        elif isinstance(obj, list):
            for item in obj:
                find_forms(item)
    find_forms(schema)
    
    if forms:
        form = forms[0]
        api = form.get("api", {})
        url = api.get("url", "")
        if url == "/api/v1/command":
            issues.append("✅ api.url = /api/v1/command (拒绝响应正确)")
        else:
            issues.append(f"⚠️ api.url = {url}")
    
    return {
        "issues": issues
    }


def main():
    """主函数"""
    dataset_path = Path(__file__).parent.parent / "dataset_v5.jsonl"
    
    print("=" * 80)
    print("📊 随机抽取样本检查")
    print("=" * 80)
    
    samples = load_samples(str(dataset_path))
    
    for i, sample in enumerate(samples):
        sample_type = sample.get("metadata", {}).get("sample_type", "unknown")
        domain = sample.get("metadata", {}).get("domain", "unknown")
        
        print(f"\n{'='*80}")
        print(f"样本 {i+1}: {sample_type} | 域: {domain}")
        print("=" * 80)
        
        # 打印用户输入
        user_input = sample.get("messages", [{}])[1].get("content", "")
        print(f"\n📝 用户输入:\n{user_input}")
        
        # 检查 AMIS Schema
        assistant_content = sample.get("messages", [{}])[-1].get("content", "{}")
        schema = json.loads(assistant_content)
        
        print(f"\n🎨 AMIS Schema 检查:")
        amis_check = check_amis_schema(schema)
        for issue in amis_check["issues"]:
            print(f"   {issue}")
        
        # 根据类型进行特定检查
        if sample_type in ["workflow_entry", "workflow_step"]:
            print(f"\n🔄 工作流检查:")
            wf_check = check_workflow_sample(sample)
            for issue in wf_check["issues"]:
                print(f"   {issue}")
        elif sample_type == "api_only":
            print(f"\n🔌 API 调用检查:")
            api_check = check_api_only_sample(sample)
            for issue in api_check["issues"]:
                print(f"   {issue}")
        elif sample_type in ["rejection", "rejection_mismatch"]:
            print(f"\n🚫 拒绝响应检查:")
            rej_check = check_rejection_sample(sample)
            for issue in rej_check["issues"]:
                print(f"   {issue}")
        
        # 打印图谱摘要
        graph = sample.get("graph_input", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        print(f"\n📊 图谱摘要: {len(nodes)} 节点, {len(edges)} 边")
        
        # 打印节点类型统计
        node_types = {}
        for n in nodes:
            t = n.get("type", "unknown")
            node_types[t] = node_types.get(t, 0) + 1
        if node_types:
            print(f"   节点类型: {node_types}")
    
    print("\n" + "=" * 80)
    print("✅ 检查完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
