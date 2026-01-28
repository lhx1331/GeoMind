"""
地理编码工具

实现正向和反向地理编码功能，支持多种地理服务提供商。
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, ConfigDict, Field

from geomind.config import get_settings
from geomind.tools.base import BaseTool, ToolResult
from geomind.tools.registry import register_tool
from geomind.utils.logging import get_logger
from geomind.utils.retry import retry

logger = get_logger(__name__)


class GeoProvider(str, Enum):
    """地理服务提供商"""

    NOMINATIM = "nominatim"  # OpenStreetMap (免费)
    GOOGLE = "google"
    BING = "bing"
    MAPBOX = "mapbox"


class GeoLocation(BaseModel):
    """地理位置"""

    lat: float = Field(description="纬度")
    lon: float = Field(description="经度")
    display_name: Optional[str] = Field(default=None, description="显示名称")
    address: Optional[Dict[str, str]] = Field(default=None, description="地址详情")
    bbox: Optional[List[float]] = Field(default=None, description="边界框 [minlat, maxlat, minlon, maxlon]")
    confidence: Optional[float] = Field(default=None, description="置信度")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lat": 35.6762,
                "lon": 139.6503,
                "display_name": "Tokyo Station, Tokyo, Japan",
                "address": {
                    "city": "Tokyo",
                    "country": "Japan",
                },
            }
        }
    )


class GeocodeProvider:
    """地理编码提供商基类"""

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

    async def geocode(self, address: str, **kwargs) -> List[GeoLocation]:
        """正向地理编码"""
        raise NotImplementedError

    async def reverse_geocode(self, lat: float, lon: float, **kwargs) -> Optional[GeoLocation]:
        """反向地理编码"""
        raise NotImplementedError


class NominatimProvider(GeocodeProvider):
    """Nominatim (OpenStreetMap) 提供商"""

    BASE_URL = "https://nominatim.openstreetmap.org"

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def geocode(self, address: str, limit: int = 5, **kwargs) -> List[GeoLocation]:
        """正向地理编码

        Args:
            address: 地址字符串
            limit: 返回结果数量限制

        Returns:
            地理位置列表
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        params = {
            "q": address,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
        }

        logger.debug(f"Geocoding address", address=address, provider="nominatim")

        response = await self._client.get(
            f"{self.BASE_URL}/search",
            params=params,
            headers={"User-Agent": "GeoMind/0.1.0"},
        )
        response.raise_for_status()

        data = response.json()
        locations = []

        for item in data:
            location = GeoLocation(
                lat=float(item["lat"]),
                lon=float(item["lon"]),
                display_name=item.get("display_name"),
                address=item.get("address"),
                bbox=item.get("boundingbox"),
                confidence=float(item.get("importance", 0.5)),
            )
            locations.append(location)

        logger.info(f"Geocoded address", address=address, results=len(locations))

        return locations

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def reverse_geocode(self, lat: float, lon: float, **kwargs) -> Optional[GeoLocation]:
        """反向地理编码

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            地理位置
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
        }

        logger.debug(f"Reverse geocoding", lat=lat, lon=lon, provider="nominatim")

        response = await self._client.get(
            f"{self.BASE_URL}/reverse",
            params=params,
            headers={"User-Agent": "GeoMind/0.1.0"},
        )
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            logger.warning(f"Reverse geocoding failed", lat=lat, lon=lon, error=data["error"])
            return None

        location = GeoLocation(
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            display_name=data.get("display_name"),
            address=data.get("address"),
            bbox=data.get("boundingbox"),
            confidence=float(data.get("importance", 0.5)),
        )

        logger.info(f"Reverse geocoded", lat=lat, lon=lon, location=location.display_name)

        return location


class GoogleProvider(GeocodeProvider):
    """Google Maps 提供商"""

    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def geocode(self, address: str, **kwargs) -> List[GeoLocation]:
        """正向地理编码"""
        if not self.api_key:
            raise ValueError("Google API key is required")

        if not self._client:
            raise RuntimeError("Client not initialized")

        params = {
            "address": address,
            "key": self.api_key,
        }

        logger.debug(f"Geocoding address", address=address, provider="google")

        response = await self._client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if data["status"] != "OK":
            logger.warning(f"Geocoding failed", address=address, status=data["status"])
            return []

        locations = []
        for result in data["results"]:
            loc = result["geometry"]["location"]
            location = GeoLocation(
                lat=loc["lat"],
                lon=loc["lng"],
                display_name=result.get("formatted_address"),
                address={comp["types"][0]: comp["long_name"] for comp in result.get("address_components", [])},
            )
            locations.append(location)

        logger.info(f"Geocoded address", address=address, results=len(locations))

        return locations

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def reverse_geocode(self, lat: float, lon: float, **kwargs) -> Optional[GeoLocation]:
        """反向地理编码"""
        if not self.api_key:
            raise ValueError("Google API key is required")

        if not self._client:
            raise RuntimeError("Client not initialized")

        params = {
            "latlng": f"{lat},{lon}",
            "key": self.api_key,
        }

        logger.debug(f"Reverse geocoding", lat=lat, lon=lon, provider="google")

        response = await self._client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if data["status"] != "OK" or not data["results"]:
            logger.warning(f"Reverse geocoding failed", lat=lat, lon=lon, status=data["status"])
            return None

        result = data["results"][0]
        loc = result["geometry"]["location"]
        location = GeoLocation(
            lat=loc["lat"],
            lon=loc["lng"],
            display_name=result.get("formatted_address"),
            address={comp["types"][0]: comp["long_name"] for comp in result.get("address_components", [])},
        )

        logger.info(f"Reverse geocoded", lat=lat, lon=lon, location=location.display_name)

        return location


def get_provider(
    provider: GeoProvider = GeoProvider.NOMINATIM,
    api_key: Optional[str] = None,
) -> GeocodeProvider:
    """获取地理编码提供商

    Args:
        provider: 提供商类型
        api_key: API 密钥

    Returns:
        提供商实例
    """
    settings = get_settings()

    if provider == GeoProvider.NOMINATIM:
        return NominatimProvider()
    elif provider == GeoProvider.GOOGLE:
        key = api_key or settings.geocode.google_api_key
        return GoogleProvider(api_key=key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


@register_tool(name="geocode", category="geo", tags=["geocoding", "location"])
class GeocodeTool(BaseTool):
    """地理编码工具

    将地址字符串转换为地理坐标。
    """

    @property
    def name(self) -> str:
        return "geocode"

    @property
    def description(self) -> str:
        return "Convert address to geographic coordinates (latitude, longitude)"

    async def execute(
        self,
        address: str,
        provider: str = "nominatim",
        limit: int = 5,
        **kwargs,
    ) -> ToolResult:
        """执行地理编码

        Args:
            address: 地址字符串
            provider: 提供商 (nominatim, google)
            limit: 返回结果数量限制

        Returns:
            工具执行结果
        """
        try:
            provider_enum = GeoProvider(provider)
            geocode_provider = get_provider(provider_enum)

            async with geocode_provider:
                locations = await geocode_provider.geocode(address, limit=limit)

            if not locations:
                return ToolResult.error(
                    error=f"No results found for address: {address}",
                    metadata={"address": address, "provider": provider},
                )

            # 转换为字典列表
            results = [loc.model_dump() for loc in locations]

            return ToolResult.success(
                output=results,
                metadata={
                    "address": address,
                    "provider": provider,
                    "count": len(results),
                },
            )

        except Exception as e:
            logger.error(f"Geocoding failed", address=address, error=str(e), exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={"address": address, "provider": provider},
            )


@register_tool(name="reverse_geocode", category="geo", tags=["geocoding", "location"])
class ReverseGeocodeTool(BaseTool):
    """反向地理编码工具

    将地理坐标转换为地址字符串。
    """

    @property
    def name(self) -> str:
        return "reverse_geocode"

    @property
    def description(self) -> str:
        return "Convert geographic coordinates to address"

    async def execute(
        self,
        lat: float,
        lon: float,
        provider: str = "nominatim",
        **kwargs,
    ) -> ToolResult:
        """执行反向地理编码

        Args:
            lat: 纬度
            lon: 经度
            provider: 提供商 (nominatim, google)

        Returns:
            工具执行结果
        """
        try:
            provider_enum = GeoProvider(provider)
            geocode_provider = get_provider(provider_enum)

            async with geocode_provider:
                location = await geocode_provider.reverse_geocode(lat, lon)

            if not location:
                return ToolResult.error(
                    error=f"No address found for coordinates: ({lat}, {lon})",
                    metadata={"lat": lat, "lon": lon, "provider": provider},
                )

            return ToolResult.success(
                output=location.model_dump(),
                metadata={
                    "lat": lat,
                    "lon": lon,
                    "provider": provider,
                },
            )

        except Exception as e:
            logger.error(f"Reverse geocoding failed", lat=lat, lon=lon, error=str(e), exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={"lat": lat, "lon": lon, "provider": provider},
            )


async def geocode(
    address: str,
    provider: GeoProvider = GeoProvider.NOMINATIM,
    limit: int = 5,
) -> List[GeoLocation]:
    """便捷函数：地理编码

    Args:
        address: 地址字符串
        provider: 提供商
        limit: 返回结果数量限制

    Returns:
        地理位置列表
    """
    geocode_provider = get_provider(provider)
    async with geocode_provider:
        return await geocode_provider.geocode(address, limit=limit)


async def reverse_geocode(
    lat: float,
    lon: float,
    provider: GeoProvider = GeoProvider.NOMINATIM,
) -> Optional[GeoLocation]:
    """便捷函数：反向地理编码

    Args:
        lat: 纬度
        lon: 经度
        provider: 提供商

    Returns:
        地理位置
    """
    geocode_provider = get_provider(provider)
    async with geocode_provider:
        return await geocode_provider.reverse_geocode(lat, lon)


__all__ = [
    "GeoProvider",
    "GeoLocation",
    "GeocodeProvider",
    "NominatimProvider",
    "GoogleProvider",
    "get_provider",
    "GeocodeTool",
    "ReverseGeocodeTool",
    "geocode",
    "reverse_geocode",
]

