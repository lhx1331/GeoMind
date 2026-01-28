"""
工具基类和注册表单元测试
"""

import pytest

from geomind.tools.base import (
    BaseTool,
    ToolError,
    ToolParameter,
    ToolResult,
    ToolSchema,
    ToolStatus,
)
from geomind.tools.registry import ToolRegistry, get_registry, register_tool


class TestToolResult:
    """测试 ToolResult"""

    def test_success_result(self):
        """测试成功结果"""
        result = ToolResult.success(
            output={"data": "test"},
            metadata={"tool": "test_tool"},
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output == {"data": "test"}
        assert result.error_message is None
        assert result.is_success()
        assert not result.is_error()

    def test_error_result(self):
        """测试错误结果"""
        result = ToolResult.error(
            error="Something went wrong",
            metadata={"tool": "test_tool"},
        )

        assert result.status == ToolStatus.ERROR
        assert result.output is None
        assert result.error_message == "Something went wrong"
        assert not result.is_success()
        assert result.is_error()

    def test_timeout_result(self):
        """测试超时结果"""
        result = ToolResult.timeout(
            error="Execution timeout",
            metadata={"tool": "test_tool"},
        )

        assert result.status == ToolStatus.TIMEOUT
        assert result.is_error()


class TestToolParameter:
    """测试 ToolParameter"""

    def test_create_parameter(self):
        """测试创建参数"""
        param = ToolParameter(
            name="location",
            type="string",
            description="Location name",
            required=True,
        )

        assert param.name == "location"
        assert param.type == "string"
        assert param.required is True

    def test_parameter_with_default(self):
        """测试带默认值的参数"""
        param = ToolParameter(
            name="limit",
            type="integer",
            description="Result limit",
            required=False,
            default=10,
        )

        assert param.default == 10
        assert param.required is False


class TestToolSchema:
    """测试 ToolSchema"""

    def test_create_schema(self):
        """测试创建 Schema"""
        schema = ToolSchema(
            name="geocode",
            description="Geocode a location",
            parameters=[
                ToolParameter(
                    name="location",
                    type="string",
                    description="Location name",
                    required=True,
                )
            ],
            returns="Coordinates",
            category="geo",
            tags=["geocoding"],
        )

        assert schema.name == "geocode"
        assert len(schema.parameters) == 1
        assert schema.category == "geo"
        assert "geocoding" in schema.tags


class SimpleTool(BaseTool):
    """简单测试工具"""

    @property
    def name(self) -> str:
        return "simple_tool"

    @property
    def description(self) -> str:
        return "A simple test tool"

    async def execute(self, text: str = "default") -> ToolResult:
        return ToolResult.success(output=text.upper())


class CategorizedTool(BaseTool):
    """带分类的测试工具"""

    @property
    def name(self) -> str:
        return "categorized_tool"

    @property
    def description(self) -> str:
        return "A categorized tool"

    @property
    def category(self) -> str:
        return "test"

    @property
    def tags(self) -> list[str]:
        return ["test", "example"]

    async def execute(self, value: int) -> ToolResult:
        return ToolResult.success(output=value * 2)


class TestBaseTool:
    """测试 BaseTool"""

    @pytest.mark.asyncio
    async def test_simple_tool(self):
        """测试简单工具"""
        tool = SimpleTool()

        assert tool.name == "simple_tool"
        assert tool.description == "A simple test tool"

        result = await tool.execute(text="hello")
        assert result.is_success()
        assert result.output == "HELLO"

    @pytest.mark.asyncio
    async def test_tool_with_default_param(self):
        """测试带默认参数的工具"""
        tool = SimpleTool()

        result = await tool.execute()
        assert result.is_success()
        assert result.output == "DEFAULT"

    def test_tool_schema(self):
        """测试工具 Schema"""
        tool = SimpleTool()
        schema = tool.get_schema()

        assert schema.name == "simple_tool"
        assert schema.description == "A simple test tool"
        assert len(schema.parameters) == 1
        assert schema.parameters[0].name == "text"

    def test_categorized_tool(self):
        """测试带分类的工具"""
        tool = CategorizedTool()

        assert tool.category == "test"
        assert "test" in tool.tags
        assert "example" in tool.tags

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """测试参数验证"""
        tool = SimpleTool()

        # 有效参数
        await tool.validate_parameters(text="test")

        # 未知参数（应该只是警告）
        await tool.validate_parameters(text="test", unknown_param="value")


class TestToolRegistry:
    """测试 ToolRegistry"""

    def setup_method(self):
        """每个测试前清空注册表"""
        registry = ToolRegistry()
        registry.clear()

    def test_registry_singleton(self):
        """测试注册表单例"""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        assert registry1 is registry2

    def test_register_tool(self):
        """测试注册工具"""
        registry = ToolRegistry()
        tool = SimpleTool()

        registry.register(tool)

        assert registry.has("simple_tool")
        assert len(registry) == 1

    def test_register_duplicate_tool(self):
        """测试注册重复工具"""
        registry = ToolRegistry()
        tool1 = SimpleTool()
        tool2 = SimpleTool()

        registry.register(tool1)

        # 不允许覆盖
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2, override=False)

        # 允许覆盖
        registry.register(tool2, override=True)
        assert len(registry) == 1

    def test_register_class(self):
        """测试注册工具类"""
        registry = ToolRegistry()

        registry.register_class(SimpleTool)

        assert registry.has("simple_tool")
        tool = registry.get("simple_tool")
        assert isinstance(tool, SimpleTool)

    def test_get_tool(self):
        """测试获取工具"""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)

        retrieved = registry.get("simple_tool")
        assert retrieved is tool

        # 不存在的工具
        assert registry.get("nonexistent") is None

    def test_unregister_tool(self):
        """测试注销工具"""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)

        assert registry.has("simple_tool")

        registry.unregister("simple_tool")

        assert not registry.has("simple_tool")
        assert len(registry) == 0

    def test_list_tools(self):
        """测试列出工具"""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.register(CategorizedTool())

        tools = registry.list_tools()
        assert len(tools) == 2
        assert "simple_tool" in tools
        assert "categorized_tool" in tools

    def test_list_tools_by_category(self):
        """测试按分类列出工具"""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.register(CategorizedTool())

        tools = registry.list_tools(category="test")
        assert len(tools) == 1
        assert "categorized_tool" in tools

    def test_list_tools_by_tag(self):
        """测试按标签列出工具"""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.register(CategorizedTool())

        tools = registry.list_tools(tag="example")
        assert len(tools) == 1
        assert "categorized_tool" in tools

    def test_get_schemas(self):
        """测试获取 Schema"""
        registry = ToolRegistry()
        registry.register(SimpleTool())
        registry.register(CategorizedTool())

        schemas = registry.get_schemas()
        assert len(schemas) == 2
        assert "simple_tool" in schemas
        assert isinstance(schemas["simple_tool"], ToolSchema)

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """测试执行工具"""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        result = await registry.execute("simple_tool", text="hello")

        assert result.is_success()
        assert result.output == "HELLO"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具"""
        registry = ToolRegistry()

        with pytest.raises(ToolError, match="not found"):
            await registry.execute("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """测试带超时的执行"""
        import asyncio

        class SlowTool(BaseTool):
            @property
            def name(self) -> str:
                return "slow_tool"

            @property
            def description(self) -> str:
                return "A slow tool"

            async def execute(self) -> ToolResult:
                await asyncio.sleep(2)
                return ToolResult.success(output="done")

        registry = ToolRegistry()
        registry.register(SlowTool())

        result = await registry.execute("slow_tool", timeout=0.1)

        assert result.status == ToolStatus.TIMEOUT
        assert "timeout" in result.error_message.lower()

    def test_contains(self):
        """测试 __contains__"""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        assert "simple_tool" in registry
        assert "nonexistent" not in registry


class TestRegisterToolDecorator:
    """测试 @register_tool 装饰器"""

    def setup_method(self):
        """每个测试前清空注册表"""
        registry = get_registry()
        registry.clear()

    def test_register_tool_class(self):
        """测试装饰工具类"""

        @register_tool()
        class DecoratedTool(BaseTool):
            @property
            def name(self) -> str:
                return "decorated_tool"

            @property
            def description(self) -> str:
                return "A decorated tool"

            async def execute(self, value: str) -> ToolResult:
                return ToolResult.success(output=value)

        registry = get_registry()
        assert registry.has("decorated_tool")

    def test_register_tool_with_custom_name(self):
        """测试使用自定义名称"""

        @register_tool(name="custom_name", category="custom")
        class MyTool(BaseTool):
            @property
            def name(self) -> str:
                return "original_name"

            @property
            def description(self) -> str:
                return "My tool"

            async def execute(self) -> ToolResult:
                return ToolResult.success(output="done")

        registry = get_registry()
        assert registry.has("custom_name")
        tool = registry.get("custom_name")
        assert tool.category == "custom"

    @pytest.mark.asyncio
    async def test_register_function(self):
        """测试装饰函数"""

        @register_tool(name="func_tool")
        async def my_function(text: str) -> ToolResult:
            """My function tool"""
            return ToolResult.success(output=text.lower())

        registry = get_registry()
        assert registry.has("func_tool")

        result = await registry.execute("func_tool", text="HELLO")
        assert result.is_success()
        assert result.output == "hello"

    @pytest.mark.asyncio
    async def test_register_sync_function(self):
        """测试装饰同步函数"""

        @register_tool(name="sync_func")
        def sync_function(value: int) -> int:
            """Sync function"""
            return value * 2

        registry = get_registry()
        assert registry.has("sync_func")

        result = await registry.execute("sync_func", value=5)
        assert result.is_success()
        assert result.output == 10

    def test_register_invalid_type(self):
        """测试装饰无效类型"""

        # 装饰非 BaseTool 类会创建一个 FunctionTool 包装
        # 所以不会抛出 TypeError，这个测试需要调整
        
        # 测试装饰非类非函数的对象
        with pytest.raises(TypeError):
            decorator = register_tool()
            decorator(123)  # 数字不能被装饰


class TestGetRegistry:
    """测试 get_registry"""

    def test_get_registry(self):
        """测试获取全局注册表"""
        registry = get_registry()

        assert isinstance(registry, ToolRegistry)
        assert registry is get_registry()  # 应该返回同一实例

