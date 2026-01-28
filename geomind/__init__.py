"""
GeoMind - 通用地理推理 Agent

基于 PHRV 框架的多模态地理位置推理系统。

示例:
    >>> from geomind import GeoMindAgent
    >>> 
    >>> agent = GeoMindAgent()
    >>> prediction = await agent.geolocate("photo.jpg")
    >>> print(f"位置: ({prediction.lat}, {prediction.lon})")
    >>> print(f"置信度: {prediction.confidence:.2%}")

或使用便捷函数:
    >>> from geomind import geolocate
    >>> 
    >>> prediction = await geolocate("photo.jpg")
    >>> print(f"位置: ({prediction.lat}, {prediction.lon})")
"""

__version__ = "0.1.0"

from geomind.agent import GeoMindAgent, geolocate
from geomind.agent.state import FinalResult

__all__ = [
    "GeoMindAgent",
    "geolocate",
    "FinalResult",
    "__version__",
]
