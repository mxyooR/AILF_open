"""
模板加载器

使用 Jinja2 加载和渲染 AMIS Schema 模板
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TemplateLoader:
    """AMIS Schema 模板加载器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化模板加载器
        
        Args:
            template_dir: 模板目录路径（可选）
        """
        if template_dir is None:
            # 默认模板目录
            template_dir = str(Path(__file__).parent / "templates")
        
        self.template_dir = template_dir
        
        # 创建 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # AMIS Schema 是 JSON，不需要转义
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 注册自定义过滤器
        self.env.filters['tojson'] = self._to_json_filter
        
        logger.info(f"模板加载器初始化完成，模板目录: {template_dir}")
    
    def render(
        self,
        template_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染模板
        
        Args:
            template_name: 模板名称（如 "workflow_entry.json.j2"）
            **kwargs: 模板变量
        
        Returns:
            渲染后的 AMIS Schema（字典）
        """
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**kwargs)
            
            # 解析为 JSON
            schema = json.loads(rendered)
            
            logger.debug(f"模板渲染成功: {template_name}")
            return schema
            
        except Exception as e:
            logger.error(f"模板渲染失败: {template_name}, 错误: {str(e)}")
            raise
    
    def render_string(
        self,
        template_str: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染模板字符串
        
        Args:
            template_str: 模板字符串
            **kwargs: 模板变量
        
        Returns:
            渲染后的 AMIS Schema（字典）
        """
        try:
            template = Template(template_str)
            rendered = template.render(**kwargs)
            
            # 解析为 JSON
            schema = json.loads(rendered)
            
            return schema
            
        except Exception as e:
            logger.error(f"模板字符串渲染失败, 错误: {str(e)}")
            raise
    
    def get_template_content(self, template_name: str) -> str:
        """
        获取模板内容（不渲染）
        
        Args:
            template_name: 模板名称（如 "workflow_entry.json.j2"）
        
        Returns:
            模板内容字符串
        """
        try:
            template_path = Path(self.template_dir) / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"读取模板内容: {template_name}")
            return content
            
        except Exception as e:
            logger.error(f"读取模板内容失败: {template_name}, 错误: {str(e)}")
            raise
    
    def _to_json_filter(self, value: Any) -> str:
        """
        自定义 JSON 过滤器
        
        将 Python 对象转换为 JSON 字符串
        """
        return json.dumps(value, ensure_ascii=False)


# 全局实例
template_loader = TemplateLoader()
