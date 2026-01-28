# 自定义工具开发指南

本指南说明如何为 GeoMind 开发自定义工具。

## 工具类型

GeoMind 支持两种类型的工具：

1. **MCP 工具**: 通过 MCP 协议注册的工具
2. **Python 函数工具**: 直接实现的 Python 函数

## 创建 Python 函数工具

### 基本示例

```python
from geomind.tools import register_tool
from geomind.tools.base import ToolResult

@register_tool(
    name="my_tool",
    description="工具描述",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"},
            "param2": {"type": "number", "description": "参数2"}
        },
        "required": ["param1"]
    }
)
def my_tool(param1: str, param2: int = 10) -> ToolResult:
    """工具实现"""
    try:
        # 执行工具逻辑
        result = do_something(param1, param2)
        
        return ToolResult(
            success=True,
            data=result
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=str(e)
        )
```

### ToolResult 格式

```python
from geomind.tools.base import ToolResult

# 成功结果
result = ToolResult(
    success=True,
    data={
        "key": "value",
        # 任何可序列化的数据
    }
)

# 失败结果
result = ToolResult(
    success=False,
    error="错误信息"
)
```

## 注册工具

### 方式 1: 装饰器注册（推荐）

```python
@register_tool(...)
def my_tool(...):
    pass
```

### 方式 2: 手动注册

```python
from geomind.tools import ToolRegistry

registry = ToolRegistry()
registry.register(my_tool)
```

## 工具参数 Schema

工具参数使用 JSON Schema 格式定义：

```python
parameters = {
    "type": "object",
    "properties": {
        "required_param": {
            "type": "string",
            "description": "必需参数"
        },
        "optional_param": {
            "type": "number",
            "description": "可选参数",
            "default": 0
        }
    },
    "required": ["required_param"]
}
```

## 在 Agent 中使用

```python
from geomind import GeoMindAgent
from geomind.tools import ToolRegistry

# 创建注册表并注册工具
registry = ToolRegistry()
registry.register(my_tool)

# 使用工具创建 Agent
agent = GeoMindAgent(tools=registry)
```

## 最佳实践

1. **错误处理**: 始终使用 try-except 捕获异常
2. **类型提示**: 为函数参数和返回值添加类型提示
3. **文档字符串**: 编写清晰的文档说明工具用途
4. **参数验证**: 在工具内部验证参数有效性
5. **返回格式**: 保持返回数据格式一致

## 示例：地理编码工具

```python
import httpx
from geomind.tools import register_tool
from geomind.tools.base import ToolResult

@register_tool(
    name="google_geocode",
    description="使用 Google Maps API 进行地理编码",
    parameters={
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "要查询的地址"
            }
        },
        "required": ["address"]
    }
)
async def google_geocode(address: str) -> ToolResult:
    """Google Maps 地理编码工具"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return ToolResult(
            success=False,
            error="未配置 Google Maps API Key"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                location = data["results"][0]["geometry"]["location"]
                return ToolResult(
                    success=True,
                    data={
                        "lat": location["lat"],
                        "lon": location["lng"],
                        "formatted_address": data["results"][0]["formatted_address"]
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"地理编码失败: {data.get('status')}"
                )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"请求错误: {str(e)}"
        )
```

## 测试工具

```python
import pytest
from geomind.tools import ToolRegistry

def test_my_tool():
    registry = ToolRegistry()
    registry.register(my_tool)
    
    result = my_tool("test_param", 42)
    assert result.success
    assert "expected_key" in result.data
```

更多示例请参考 `examples/custom_tools.py`。

