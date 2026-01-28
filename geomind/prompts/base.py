"""
提示模板基类

定义统一的提示模板接口和加载机制。
"""

import json
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field

from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class PromptTemplate(BaseModel):
    """提示模板

    使用 Python string.Template 进行变量替换。
    """

    name: str = Field(description="模板名称")
    version: str = Field(default="1.0.0", description="模板版本")
    description: Optional[str] = Field(default=None, description="模板描述")
    template: str = Field(description="模板内容")
    variables: List[str] = Field(default_factory=list, description="模板变量列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "perception",
                "version": "1.0.0",
                "description": "Perception stage prompt",
                "template": "Analyze the image and extract: $features",
                "variables": ["features"],
            }
        }
    )

    def render(self, **kwargs: Any) -> str:
        """渲染模板

        Args:
            **kwargs: 模板变量

        Returns:
            渲染后的文本

        Raises:
            KeyError: 缺少必需的变量
        """
        # 检查必需变量
        missing_vars = set(self.variables) - set(kwargs.keys())
        if missing_vars:
            logger.warning(
                f"Missing template variables",
                template=self.name,
                missing=list(missing_vars),
            )

        try:
            # 使用 Template 进行替换
            template = Template(self.template)
            rendered = template.substitute(kwargs)

            logger.debug(
                f"Template rendered",
                template=self.name,
                variables=list(kwargs.keys()),
            )

            return rendered

        except KeyError as e:
            logger.error(
                f"Template rendering failed",
                template=self.name,
                error=str(e),
            )
            raise

    def safe_render(self, **kwargs: Any) -> str:
        """安全渲染模板

        缺少的变量会保留为 ${variable} 格式。

        Args:
            **kwargs: 模板变量

        Returns:
            渲染后的文本
        """
        try:
            template = Template(self.template)
            rendered = template.safe_substitute(kwargs)

            logger.debug(
                f"Template safely rendered",
                template=self.name,
                variables=list(kwargs.keys()),
            )

            return rendered

        except Exception as e:
            logger.error(
                f"Template safe rendering failed",
                template=self.name,
                error=str(e),
            )
            raise

    def validate_variables(self, **kwargs: Any) -> bool:
        """验证变量

        Args:
            **kwargs: 模板变量

        Returns:
            是否所有必需变量都提供
        """
        missing_vars = set(self.variables) - set(kwargs.keys())
        return len(missing_vars) == 0

    def get_missing_variables(self, **kwargs: Any) -> List[str]:
        """获取缺失的变量

        Args:
            **kwargs: 模板变量

        Returns:
            缺失的变量列表
        """
        missing_vars = set(self.variables) - set(kwargs.keys())
        return list(missing_vars)


class PromptTemplateLoader:
    """提示模板加载器

    支持从 YAML 和 JSON 文件加载模板。
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """初始化加载器

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self._cache: Dict[str, PromptTemplate] = {}

    def load_from_file(self, file_path: Union[str, Path]) -> PromptTemplate:
        """从文件加载模板

        Args:
            file_path: 文件路径

        Returns:
            提示模板

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Template file not found: {file_path}")

        logger.debug(f"Loading template from file", file=str(file_path))

        # 根据文件扩展名选择加载方式
        if file_path.suffix in [".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        template = PromptTemplate(**data)

        logger.info(
            f"Template loaded",
            name=template.name,
            version=template.version,
            file=str(file_path),
        )

        return template

    def load_from_dict(self, data: Dict[str, Any]) -> PromptTemplate:
        """从字典加载模板

        Args:
            data: 模板数据

        Returns:
            提示模板
        """
        template = PromptTemplate(**data)

        logger.debug(f"Template loaded from dict", name=template.name)

        return template

    def load(self, name: str, use_cache: bool = True) -> PromptTemplate:
        """加载模板

        从模板目录加载指定名称的模板。

        Args:
            name: 模板名称
            use_cache: 是否使用缓存

        Returns:
            提示模板

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        # 检查缓存
        if use_cache and name in self._cache:
            logger.debug(f"Template loaded from cache", name=name)
            return self._cache[name]

        # 尝试加载 YAML 或 JSON 文件
        for ext in [".yaml", ".yml", ".json"]:
            file_path = self.template_dir / f"{name}{ext}"
            if file_path.exists():
                template = self.load_from_file(file_path)
                # 缓存模板
                if use_cache:
                    self._cache[name] = template
                return template

        raise FileNotFoundError(f"Template not found: {name}")

    def list_templates(self) -> List[str]:
        """列出所有可用的模板

        Returns:
            模板名称列表
        """
        if not self.template_dir.exists():
            return []

        templates = []
        for file_path in self.template_dir.glob("*"):
            if file_path.suffix in [".yaml", ".yml", ".json"]:
                templates.append(file_path.stem)

        return sorted(templates)

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.debug("Template cache cleared")


# 全局加载器实例
_loader: Optional[PromptTemplateLoader] = None


def get_loader(template_dir: Optional[Path] = None) -> PromptTemplateLoader:
    """获取全局模板加载器

    Args:
        template_dir: 模板目录路径

    Returns:
        模板加载器
    """
    global _loader
    if _loader is None:
        _loader = PromptTemplateLoader(template_dir)
    return _loader


def load_template(name: str, use_cache: bool = True) -> PromptTemplate:
    """便捷函数：加载模板

    Args:
        name: 模板名称
        use_cache: 是否使用缓存

    Returns:
        提示模板
    """
    loader = get_loader()
    return loader.load(name, use_cache=use_cache)


def render_template(template_name: str, **kwargs: Any) -> str:
    """便捷函数：加载并渲染模板

    Args:
        template_name: 模板名称
        **kwargs: 模板变量

    Returns:
        渲染后的文本
    """
    template = load_template(template_name)
    return template.render(**kwargs)


__all__ = [
    "PromptTemplate",
    "PromptTemplateLoader",
    "get_loader",
    "load_template",
    "render_template",
]

