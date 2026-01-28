"""
工具基类和结果模型

定义统一的工具接口和返回格式。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class ToolStatus(str, Enum):
    """工具执行状态"""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ToolResult(BaseModel):
    """工具执行结果

    统一的工具返回格式。
    """

    status: ToolStatus = Field(description="执行状态")
    output: Any = Field(default=None, description="输出数据")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "output": {"result": "Tokyo, Japan"},
                "metadata": {"execution_time": 1.23, "tool": "geocode"},
            }
        }
    )

    @classmethod
    def success(
        cls,
        output: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ToolResult":
        """创建成功结果"""
        return cls(
            status=ToolStatus.SUCCESS,
            output=output,
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ToolResult":
        """创建错误结果"""
        return cls(
            status=ToolStatus.ERROR,
            error_message=error,
            metadata=metadata or {},
        )

    @classmethod
    def timeout(
        cls,
        error: str = "Tool execution timeout",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ToolResult":
        """创建超时结果"""
        return cls(
            status=ToolStatus.TIMEOUT,
            error_message=error,
            metadata=metadata or {},
        )

    def is_success(self) -> bool:
        """检查是否成功"""
        return self.status == ToolStatus.SUCCESS

    def is_error(self) -> bool:
        """检查是否错误"""
        return self.status in (ToolStatus.ERROR, ToolStatus.TIMEOUT)


class ToolParameter(BaseModel):
    """工具参数定义"""

    name: str = Field(description="参数名称")
    type: str = Field(description="参数类型")
    description: str = Field(description="参数描述")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")
    enum: Optional[List[Any]] = Field(default=None, description="枚举值")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "location",
                "type": "string",
                "description": "Location to geocode",
                "required": True,
            }
        }
    )


class ToolSchema(BaseModel):
    """工具 Schema

    描述工具的元数据和参数。
    """

    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    parameters: List[ToolParameter] = Field(
        default_factory=list, description="参数列表"
    )
    returns: str = Field(description="返回值描述")
    category: Optional[str] = Field(default=None, description="工具分类")
    tags: List[str] = Field(default_factory=list, description="标签")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "geocode",
                "description": "Convert location name to coordinates",
                "parameters": [
                    {
                        "name": "location",
                        "type": "string",
                        "description": "Location name",
                        "required": True,
                    }
                ],
                "returns": "Coordinates (lat, lon)",
                "category": "geo",
                "tags": ["geocoding", "location"],
            }
        }
    )


class BaseTool(ABC):
    """工具基类

    所有工具的抽象基类。
    """

    def __init__(self):
        """初始化工具"""
        self._schema: Optional[ToolSchema] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    def category(self) -> Optional[str]:
        """工具分类"""
        return None

    @property
    def tags(self) -> List[str]:
        """工具标签"""
        return []

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def get_schema(self) -> ToolSchema:
        """获取工具 Schema

        Returns:
            工具 Schema
        """
        if self._schema is None:
            self._schema = self._build_schema()
        return self._schema

    def _build_schema(self) -> ToolSchema:
        """构建工具 Schema

        子类可以重写此方法来自定义 Schema。

        Returns:
            工具 Schema
        """
        # 尝试从类型注解中提取参数
        import inspect

        sig = inspect.signature(self.execute)
        parameters = []

        for param_name, param in sig.parameters.items():
            if param_name == "self" or param_name == "kwargs":
                continue

            param_type = "string"  # 默认类型
            if param.annotation != inspect.Parameter.empty:
                param_type = self._get_type_string(param.annotation)

            parameters.append(
                ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=param.default == inspect.Parameter.empty,
                    default=param.default
                    if param.default != inspect.Parameter.empty
                    else None,
                )
            )

        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters,
            returns="Tool execution result",
            category=self.category,
            tags=self.tags,
        )

    def _get_type_string(self, annotation: Any) -> str:
        """将 Python 类型注解转换为字符串

        Args:
            annotation: 类型注解

        Returns:
            类型字符串
        """
        if annotation == str:
            return "string"
        elif annotation == int:
            return "integer"
        elif annotation == float:
            return "number"
        elif annotation == bool:
            return "boolean"
        elif hasattr(annotation, "__origin__"):
            # 处理泛型类型
            origin = annotation.__origin__
            if origin == list:
                return "array"
            elif origin == dict:
                return "object"
        return "string"

    async def validate_parameters(self, **kwargs: Any) -> None:
        """验证参数

        Args:
            **kwargs: 参数

        Raises:
            ValueError: 参数验证失败
        """
        schema = self.get_schema()

        # 检查必需参数
        for param in schema.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")

        # 检查未知参数
        known_params = {p.name for p in schema.parameters}
        for key in kwargs:
            if key not in known_params:
                logger.warning(f"Unknown parameter: {key}", tool=self.name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class ToolError(Exception):
    """工具错误"""

    def __init__(self, message: str, tool_name: Optional[str] = None):
        self.message = message
        self.tool_name = tool_name
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.tool_name:
            return f"[{self.tool_name}] {self.message}"
        return self.message


class ToolTimeoutError(ToolError):
    """工具超时错误"""

    pass


class ToolValidationError(ToolError):
    """工具验证错误"""

    pass


__all__ = [
    "ToolStatus",
    "ToolResult",
    "ToolParameter",
    "ToolSchema",
    "BaseTool",
    "ToolError",
    "ToolTimeoutError",
    "ToolValidationError",
]

