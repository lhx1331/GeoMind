"""
工具注册表

管理工具的注册、发现和调用。
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

from geomind.tools.base import BaseTool, ToolError, ToolResult, ToolSchema, ToolStatus
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """工具注册表

    单例模式，管理所有已注册的工具。
    """

    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, BaseTool] = {}
    _tool_classes: Dict[str, Type[BaseTool]] = {}

    def __new__(cls) -> "ToolRegistry":
        """确保单例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(
        self,
        tool: BaseTool,
        override: bool = False,
    ) -> None:
        """注册工具实例

        Args:
            tool: 工具实例
            override: 是否覆盖已存在的工具

        Raises:
            ValueError: 工具名称已存在且 override=False
        """
        name = tool.name

        if name in self._tools and not override:
            raise ValueError(f"Tool '{name}' already registered")

        self._tools[name] = tool
        logger.info(f"Tool registered: {name}", category=tool.category)

    def register_class(
        self,
        tool_class: Type[BaseTool],
        override: bool = False,
    ) -> None:
        """注册工具类

        Args:
            tool_class: 工具类
            override: 是否覆盖已存在的工具

        Raises:
            ValueError: 工具名称已存在且 override=False
        """
        # 创建实例以获取名称
        instance = tool_class()
        name = instance.name

        if name in self._tool_classes and not override:
            raise ValueError(f"Tool class '{name}' already registered")

        self._tool_classes[name] = tool_class
        self._tools[name] = instance
        logger.info(f"Tool class registered: {name}", category=instance.category)

    def unregister(self, name: str) -> None:
        """注销工具

        Args:
            name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Tool unregistered: {name}")

        if name in self._tool_classes:
            del self._tool_classes[name]

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具实例

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在则返回 None
        """
        return self._tools.get(name)

    def get_class(self, name: str) -> Optional[Type[BaseTool]]:
        """获取工具类

        Args:
            name: 工具名称

        Returns:
            工具类，如果不存在则返回 None
        """
        return self._tool_classes.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in self._tools

    def list_tools(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[str]:
        """列出所有工具名称

        Args:
            category: 按分类过滤
            tag: 按标签过滤

        Returns:
            工具名称列表
        """
        tools = []

        for name, tool in self._tools.items():
            # 分类过滤
            if category and tool.category != category:
                continue

            # 标签过滤
            if tag and tag not in tool.tags:
                continue

            tools.append(name)

        return sorted(tools)

    def get_schemas(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, ToolSchema]:
        """获取所有工具的 Schema

        Args:
            category: 按分类过滤
            tag: 按标签过滤

        Returns:
            工具名称到 Schema 的映射
        """
        schemas = {}

        for name in self.list_tools(category=category, tag=tag):
            tool = self._tools[name]
            schemas[name] = tool.get_schema()

        return schemas

    async def execute(
        self,
        name: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """执行工具

        Args:
            name: 工具名称
            timeout: 超时时间（秒）
            **kwargs: 工具参数

        Returns:
            工具执行结果

        Raises:
            ToolError: 工具不存在或执行失败
        """
        tool = self.get(name)
        if tool is None:
            raise ToolError(f"Tool not found: {name}")

        try:
            # 验证参数
            await tool.validate_parameters(**kwargs)

            # 执行工具（带超时）
            if timeout:
                result = await asyncio.wait_for(
                    tool.execute(**kwargs),
                    timeout=timeout,
                )
            else:
                result = await tool.execute(**kwargs)

            logger.debug(
                f"Tool executed successfully",
                tool=name,
                status=result.status,
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Tool execution timeout", tool=name, timeout=timeout)
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                error_message=f"Tool execution timeout after {timeout}s",
                metadata={"tool": name},
            )
        except Exception as e:
            logger.error(
                f"Tool execution failed",
                tool=name,
                error=str(e),
                exc_info=True,
            )
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=str(e),
                metadata={"tool": name},
            )

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        self._tool_classes.clear()
        logger.info("Tool registry cleared")

    def __len__(self) -> int:
        """返回已注册工具数量"""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """检查工具是否存在"""
        return self.has(name)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={len(self._tools)})"


# 全局注册表实例
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """获取全局工具注册表

    Returns:
        工具注册表实例
    """
    return _registry


def register_tool(
    name: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    override: bool = False,
) -> Callable:
    """工具注册装饰器

    可以装饰工具类或函数。

    Args:
        name: 工具名称（如果为 None，使用类名或函数名）
        category: 工具分类
        tags: 工具标签
        override: 是否覆盖已存在的工具

    Returns:
        装饰器函数

    Example:
        ```python
        @register_tool(name="my_tool", category="custom")
        class MyTool(BaseTool):
            @property
            def name(self) -> str:
                return "my_tool"

            @property
            def description(self) -> str:
                return "My custom tool"

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult.success(output="done")
        ```

        或装饰函数：

        ```python
        @register_tool(name="simple_tool")
        async def simple_tool(text: str) -> ToolResult:
            return ToolResult.success(output=text.upper())
        ```
    """

    def decorator(obj: Any) -> Any:
        registry = get_registry()

        # 如果是类
        if isinstance(obj, type) and issubclass(obj, BaseTool):
            # 如果提供了自定义属性，创建子类
            if name or category or tags:

                class CustomTool(obj):
                    @property
                    def name(self) -> str:
                        return name or super().name

                    @property
                    def category(self) -> Optional[str]:
                        return category or super().category

                    @property
                    def tags(self) -> List[str]:
                        return tags or super().tags

                registry.register_class(CustomTool, override=override)
                return CustomTool
            else:
                registry.register_class(obj, override=override)
                return obj

        # 如果是函数
        elif callable(obj):
            # 创建工具类包装函数
            tool_name = name or obj.__name__

            class FunctionTool(BaseTool):
                @property
                def name(self) -> str:
                    return tool_name

                @property
                def description(self) -> str:
                    return obj.__doc__ or f"Function tool: {tool_name}"

                @property
                def category(self) -> Optional[str]:
                    return category

                @property
                def tags(self) -> List[str]:
                    return tags or []

                async def execute(self, **kwargs: Any) -> ToolResult:
                    # 如果是异步函数
                    if asyncio.iscoroutinefunction(obj):
                        result = await obj(**kwargs)
                    else:
                        result = obj(**kwargs)

                    # 如果返回的已经是 ToolResult，直接返回
                    if isinstance(result, ToolResult):
                        return result

                    # 否则包装为 ToolResult
                    return ToolResult.success(output=result)

            registry.register_class(FunctionTool, override=override)

            # 返回原函数（保持可调用）
            @wraps(obj)
            async def wrapper(**kwargs: Any) -> ToolResult:
                tool = registry.get(tool_name)
                return await tool.execute(**kwargs)

            return wrapper

        else:
            raise TypeError(
                f"@register_tool can only decorate BaseTool classes or functions, "
                f"got {type(obj)}"
            )

    return decorator


__all__ = [
    "ToolRegistry",
    "get_registry",
    "register_tool",
]

