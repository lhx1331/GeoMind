"""
自定义工具示例

演示如何注册和使用自定义 MCP 工具。
"""

from geomind import GeoMindAgent
from geomind.tools import register_tool, ToolRegistry
from geomind.tools.base import ToolResult
from typing import Dict, Any


@register_tool(
    name="custom_geocode",
    description="自定义地理编码工具，将地名转换为坐标",
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
def custom_geocode(address: str) -> ToolResult:
    """
    自定义地理编码实现
    
    这里可以集成您自己的地理编码服务，例如：
    - 公司内部地图服务
    - 第三方 API（Google Maps, Bing Maps 等）
    - 本地数据库查询
    """
    # 示例：模拟地理编码结果
    # 实际实现中应该调用真实的地理编码服务
    mock_results = {
        "东京": {"lat": 35.6762, "lon": 139.6503},
        "北京": {"lat": 39.9042, "lon": 116.4074},
        "纽约": {"lat": 40.7128, "lon": -74.0060},
    }
    
    if address in mock_results:
        coords = mock_results[address]
        return ToolResult(
            success=True,
            data={
                "lat": coords["lat"],
                "lon": coords["lon"],
                "address": address,
                "source": "custom_geocode"
            }
        )
    else:
        return ToolResult(
            success=False,
            error=f"未找到地址: {address}"
        )


@register_tool(
    name="custom_poi_search",
    description="自定义 POI 搜索工具",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "lat": {"type": "number"},
            "lon": {"type": "number"},
            "radius": {"type": "number", "default": 1000}
        },
        "required": ["query", "lat", "lon"]
    }
)
def custom_poi_search(query: str, lat: float, lon: float, radius: float = 1000) -> ToolResult:
    """
    自定义 POI 搜索实现
    """
    # 实际实现中应该调用真实的 POI 搜索服务
    return ToolResult(
        success=True,
        data={
            "results": [
                {
                    "name": f"{query} 示例结果 1",
                    "lat": lat + 0.001,
                    "lon": lon + 0.001,
                    "distance": 100
                }
            ],
            "source": "custom_poi_search"
        }
    )


def main():
    """使用自定义工具的示例"""
    
    # 创建工具注册表并注册自定义工具
    tool_registry = ToolRegistry()
    tool_registry.register(custom_geocode)
    tool_registry.register(custom_poi_search)
    
    # 使用自定义工具创建 Agent
    agent = GeoMindAgent(tools=tool_registry)
    
    # 正常使用 Agent，它会自动使用注册的自定义工具
    result = agent.geolocate("path/to/image.jpg")
    
    print(f"定位结果: {result.final.answer}")
    print("使用了自定义工具进行地理编码和 POI 搜索")


if __name__ == "__main__":
    main()

