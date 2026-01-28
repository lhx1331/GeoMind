"""
POI (Point of Interest) 搜索工具

实现兴趣点搜索功能，支持多种地理服务提供商。
"""

from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from geomind.config import get_settings
from geomind.tools.base import BaseTool, ToolResult
from geomind.tools.mcp.geocode import GeoProvider
from geomind.tools.registry import register_tool
from geomind.utils.logging import get_logger
from geomind.utils.retry import retry

logger = get_logger(__name__)


class POI(BaseModel):
    """兴趣点"""

    name: str = Field(description="POI 名称")
    lat: float = Field(description="纬度")
    lon: float = Field(description="经度")
    category: Optional[str] = Field(default=None, description="类别")
    address: Optional[str] = Field(default=None, description="地址")
    distance: Optional[float] = Field(default=None, description="距离（米）")
    rating: Optional[float] = Field(default=None, description="评分")
    phone: Optional[str] = Field(default=None, description="电话")
    website: Optional[str] = Field(default=None, description="网站")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tokyo Station",
                "lat": 35.6812,
                "lon": 139.7671,
                "category": "train_station",
                "address": "1 Chome Marunouchi, Chiyoda City, Tokyo",
                "distance": 150.5,
            }
        }
    )


class POISearchProvider:
    """POI 搜索提供商基类"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def search(
        self,
        query: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[int] = None,
        limit: int = 10,
        **kwargs,
    ) -> List[POI]:
        """搜索 POI"""
        raise NotImplementedError


class NominatimPOIProvider(POISearchProvider):
    """Nominatim POI 搜索提供商"""

    BASE_URL = "https://nominatim.openstreetmap.org"

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def search(
        self,
        query: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[int] = None,
        limit: int = 10,
        **kwargs,
    ) -> List[POI]:
        """搜索 POI

        Args:
            query: 搜索关键词
            lat: 中心纬度（可选）
            lon: 中心经度（可选）
            radius: 搜索半径（米，可选）
            limit: 返回结果数量限制

        Returns:
            POI 列表
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
        }

        # 如果提供了坐标，添加视点偏好
        if lat is not None and lon is not None:
            params["viewbox"] = f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}"
            params["bounded"] = 1

        logger.debug(f"Searching POI", query=query, lat=lat, lon=lon, provider="nominatim")

        response = await self._client.get(
            f"{self.BASE_URL}/search",
            params=params,
            headers={"User-Agent": "GeoMind/0.1.0"},
        )
        response.raise_for_status()

        data = response.json()
        pois = []

        for item in data:
            poi = POI(
                name=item.get("display_name", "").split(",")[0],
                lat=float(item["lat"]),
                lon=float(item["lon"]),
                category=item.get("type"),
                address=item.get("display_name"),
            )
            pois.append(poi)

        logger.info(f"Found POIs", query=query, results=len(pois))

        return pois


class OverpassPOIProvider(POISearchProvider):
    """Overpass API POI 搜索提供商（OpenStreetMap）"""

    BASE_URL = "https://overpass-api.de/api/interpreter"

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def search(
        self,
        query: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[int] = None,
        limit: int = 10,
        **kwargs,
    ) -> List[POI]:
        """搜索 POI

        Args:
            query: 搜索关键词
            lat: 中心纬度
            lon: 中心经度
            radius: 搜索半径（米）
            limit: 返回结果数量限制

        Returns:
            POI 列表
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        if lat is None or lon is None:
            raise ValueError("Latitude and longitude are required for Overpass search")

        radius = radius or 1000  # 默认 1km

        # 构建 Overpass QL 查询
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["name"~"{query}",i](around:{radius},{lat},{lon});
          way["name"~"{query}",i](around:{radius},{lat},{lon});
        );
        out center {limit};
        """

        logger.debug(f"Searching POI with Overpass", query=query, lat=lat, lon=lon, radius=radius)

        response = await self._client.post(
            self.BASE_URL,
            data={"data": overpass_query},
        )
        response.raise_for_status()

        data = response.json()
        pois = []

        for element in data.get("elements", []):
            # 获取坐标
            if "lat" in element and "lon" in element:
                poi_lat = element["lat"]
                poi_lon = element["lon"]
            elif "center" in element:
                poi_lat = element["center"]["lat"]
                poi_lon = element["center"]["lon"]
            else:
                continue

            tags = element.get("tags", {})
            poi = POI(
                name=tags.get("name", "Unknown"),
                lat=poi_lat,
                lon=poi_lon,
                category=tags.get("amenity") or tags.get("shop") or tags.get("tourism"),
                address=tags.get("addr:full") or tags.get("addr:street"),
                phone=tags.get("phone"),
                website=tags.get("website"),
            )
            pois.append(poi)

        logger.info(f"Found POIs with Overpass", query=query, results=len(pois))

        return pois


def get_poi_provider(
    provider: GeoProvider = GeoProvider.NOMINATIM,
    api_key: Optional[str] = None,
) -> POISearchProvider:
    """获取 POI 搜索提供商

    Args:
        provider: 提供商类型
        api_key: API 密钥

    Returns:
        提供商实例
    """
    if provider == GeoProvider.NOMINATIM:
        return NominatimPOIProvider()
    else:
        # 默认使用 Overpass API（更强大）
        return OverpassPOIProvider()


@register_tool(name="poi_search", category="geo", tags=["poi", "search", "location"])
class POISearchTool(BaseTool):
    """POI 搜索工具

    搜索兴趣点（餐厅、商店、景点等）。
    """

    @property
    def name(self) -> str:
        return "poi_search"

    @property
    def description(self) -> str:
        return "Search for points of interest (POI) like restaurants, shops, landmarks, etc."

    async def execute(
        self,
        query: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[int] = None,
        provider: str = "overpass",
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """执行 POI 搜索

        Args:
            query: 搜索关键词
            lat: 中心纬度（可选）
            lon: 中心经度（可选）
            radius: 搜索半径（米，可选）
            provider: 提供商 (nominatim, overpass)
            limit: 返回结果数量限制

        Returns:
            工具执行结果
        """
        try:
            # 选择提供商
            if provider == "overpass":
                poi_provider = OverpassPOIProvider()
            else:
                poi_provider = NominatimPOIProvider()

            async with poi_provider:
                pois = await poi_provider.search(
                    query=query,
                    lat=lat,
                    lon=lon,
                    radius=radius,
                    limit=limit,
                )

            if not pois:
                return ToolResult.error(
                    error=f"No POIs found for query: {query}",
                    metadata={
                        "query": query,
                        "lat": lat,
                        "lon": lon,
                        "provider": provider,
                    },
                )

            # 转换为字典列表
            results = [poi.model_dump() for poi in pois]

            return ToolResult.success(
                output=results,
                metadata={
                    "query": query,
                    "lat": lat,
                    "lon": lon,
                    "provider": provider,
                    "count": len(results),
                },
            )

        except Exception as e:
            logger.error(f"POI search failed", query=query, error=str(e), exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={
                    "query": query,
                    "lat": lat,
                    "lon": lon,
                    "provider": provider,
                },
            )


async def search_poi(
    query: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: Optional[int] = None,
    provider: GeoProvider = GeoProvider.NOMINATIM,
    limit: int = 10,
) -> List[POI]:
    """便捷函数：搜索 POI

    Args:
        query: 搜索关键词
        lat: 中心纬度
        lon: 中心经度
        radius: 搜索半径（米）
        provider: 提供商
        limit: 返回结果数量限制

    Returns:
        POI 列表
    """
    poi_provider = get_poi_provider(provider)
    async with poi_provider:
        return await poi_provider.search(
            query=query,
            lat=lat,
            lon=lon,
            radius=radius,
            limit=limit,
        )


__all__ = [
    "POI",
    "POISearchProvider",
    "NominatimPOIProvider",
    "OverpassPOIProvider",
    "get_poi_provider",
    "POISearchTool",
    "search_poi",
]

