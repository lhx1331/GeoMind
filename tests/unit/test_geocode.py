"""
地理编码工具单元测试
"""

import httpx
import pytest
from pytest_mock import MockerFixture

from geomind.tools.base import ToolStatus
from geomind.tools.mcp.geocode import (
    GeoLocation,
    GeoProvider,
    GeocodeTool,
    GoogleProvider,
    NominatimProvider,
    ReverseGeocodeTool,
    geocode,
    get_provider,
    reverse_geocode,
)
from geomind.tools.mcp.poi_search import (
    POI,
    NominatimPOIProvider,
    OverpassPOIProvider,
    POISearchTool,
    search_poi,
)
from geomind.tools.registry import get_registry


class TestGeoLocation:
    """测试 GeoLocation 数据模型"""

    def test_create_geolocation(self):
        """测试创建地理位置"""
        location = GeoLocation(
            lat=35.6762,
            lon=139.6503,
            display_name="Tokyo Station",
        )

        assert location.lat == 35.6762
        assert location.lon == 139.6503
        assert location.display_name == "Tokyo Station"

    def test_geolocation_with_address(self):
        """测试带地址的地理位置"""
        location = GeoLocation(
            lat=35.6762,
            lon=139.6503,
            address={"city": "Tokyo", "country": "Japan"},
        )

        assert location.address["city"] == "Tokyo"
        assert location.address["country"] == "Japan"


class TestNominatimProvider:
    """测试 Nominatim 提供商"""

    @pytest.fixture
    def mock_http_client(self, mocker: MockerFixture):
        """模拟 HTTP 客户端"""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_geocode(self, mock_http_client):
        """测试地理编码"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json=[
                {
                    "lat": "35.6812",
                    "lon": "139.7671",
                    "display_name": "Tokyo Station, Tokyo, Japan",
                    "address": {"city": "Tokyo", "country": "Japan"},
                    "importance": 0.9,
                }
            ],
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/search"),
        )
        mock_http_client.get.return_value = mock_response

        provider = NominatimProvider()
        async with provider:
            locations = await provider.geocode("Tokyo Station")

        assert len(locations) == 1
        assert locations[0].lat == 35.6812
        assert locations[0].lon == 139.7671
        assert "Tokyo" in locations[0].display_name

    @pytest.mark.asyncio
    async def test_reverse_geocode(self, mock_http_client):
        """测试反向地理编码"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json={
                "lat": "35.6812",
                "lon": "139.7671",
                "display_name": "Tokyo Station, Tokyo, Japan",
                "address": {"city": "Tokyo", "country": "Japan"},
                "importance": 0.9,
            },
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/reverse"),
        )
        mock_http_client.get.return_value = mock_response

        provider = NominatimProvider()
        async with provider:
            location = await provider.reverse_geocode(35.6812, 139.7671)

        assert location is not None
        assert location.lat == 35.6812
        assert location.lon == 139.7671
        assert "Tokyo" in location.display_name

    @pytest.mark.asyncio
    async def test_reverse_geocode_not_found(self, mock_http_client):
        """测试反向地理编码未找到"""
        # 模拟错误响应
        mock_response = httpx.Response(
            200,
            json={"error": "Unable to geocode"},
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/reverse"),
        )
        mock_http_client.get.return_value = mock_response

        provider = NominatimProvider()
        async with provider:
            location = await provider.reverse_geocode(0, 0)

        assert location is None


class TestGoogleProvider:
    """测试 Google 提供商"""

    @pytest.fixture
    def mock_http_client(self, mocker: MockerFixture):
        """模拟 HTTP 客户端"""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_geocode(self, mock_http_client):
        """测试地理编码"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json={
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Tokyo Station, Tokyo, Japan",
                        "geometry": {"location": {"lat": 35.6812, "lng": 139.7671}},
                        "address_components": [
                            {"types": ["locality"], "long_name": "Tokyo"}
                        ],
                    }
                ],
            },
            request=httpx.Request("GET", "https://maps.googleapis.com/maps/api/geocode/json"),
        )
        mock_http_client.get.return_value = mock_response

        provider = GoogleProvider(api_key="test_key")
        async with provider:
            locations = await provider.geocode("Tokyo Station")

        assert len(locations) == 1
        assert locations[0].lat == 35.6812
        assert locations[0].lon == 139.7671

    @pytest.mark.asyncio
    async def test_geocode_no_results(self, mock_http_client):
        """测试地理编码无结果"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json={"status": "ZERO_RESULTS", "results": []},
            request=httpx.Request("GET", "https://maps.googleapis.com/maps/api/geocode/json"),
        )
        mock_http_client.get.return_value = mock_response

        provider = GoogleProvider(api_key="test_key")
        async with provider:
            locations = await provider.geocode("Invalid Address")

        assert len(locations) == 0


class TestGetProvider:
    """测试 get_provider 函数"""

    def test_get_nominatim_provider(self):
        """测试获取 Nominatim 提供商"""
        provider = get_provider(GeoProvider.NOMINATIM)
        assert isinstance(provider, NominatimProvider)

    def test_get_google_provider(self, mocker: MockerFixture):
        """测试获取 Google 提供商"""
        # Mock settings
        mock_settings = mocker.MagicMock()
        mock_settings.geocode.google_api_key = "test_key"
        mocker.patch("geomind.tools.mcp.geocode.get_settings", return_value=mock_settings)

        provider = get_provider(GeoProvider.GOOGLE)
        assert isinstance(provider, GoogleProvider)
        assert provider.api_key == "test_key"


class TestGeocodeTool:
    """测试 GeocodeTool"""

    @pytest.fixture
    def mock_http_client(self, mocker: MockerFixture):
        """模拟 HTTP 客户端"""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_http_client):
        """测试成功执行"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json=[
                {
                    "lat": "35.6812",
                    "lon": "139.7671",
                    "display_name": "Tokyo Station",
                    "address": {},
                    "importance": 0.9,
                }
            ],
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/search"),
        )
        mock_http_client.get.return_value = mock_response

        tool = GeocodeTool()
        result = await tool.execute(address="Tokyo Station")

        assert result.status == ToolStatus.SUCCESS
        assert len(result.output) == 1
        assert result.output[0]["lat"] == 35.6812

    @pytest.mark.asyncio
    async def test_execute_no_results(self, mock_http_client):
        """测试无结果"""
        # 模拟空响应
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/search"),
        )
        mock_http_client.get.return_value = mock_response

        tool = GeocodeTool()
        result = await tool.execute(address="Invalid Address")

        assert result.status == ToolStatus.ERROR
        assert "No results found" in result.error_message


class TestReverseGeocodeTool:
    """测试 ReverseGeocodeTool"""

    @pytest.fixture
    def mock_http_client(self, mocker: MockerFixture):
        """模拟 HTTP 客户端"""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_http_client):
        """测试成功执行"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json={
                "lat": "35.6812",
                "lon": "139.7671",
                "display_name": "Tokyo Station",
                "address": {},
                "importance": 0.9,
            },
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/reverse"),
        )
        mock_http_client.get.return_value = mock_response

        tool = ReverseGeocodeTool()
        result = await tool.execute(lat=35.6812, lon=139.7671)

        assert result.status == ToolStatus.SUCCESS
        assert result.output["lat"] == 35.6812
        assert result.output["lon"] == 139.7671


class TestPOI:
    """测试 POI 数据模型"""

    def test_create_poi(self):
        """测试创建 POI"""
        poi = POI(
            name="Tokyo Station",
            lat=35.6812,
            lon=139.7671,
            category="train_station",
        )

        assert poi.name == "Tokyo Station"
        assert poi.lat == 35.6812
        assert poi.category == "train_station"


class TestPOISearchTool:
    """测试 POISearchTool"""

    @pytest.fixture
    def mock_http_client(self, mocker: MockerFixture):
        """模拟 HTTP 客户端"""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_execute_nominatim(self, mock_http_client):
        """测试使用 Nominatim 搜索"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json=[
                {
                    "lat": "35.6812",
                    "lon": "139.7671",
                    "display_name": "Tokyo Station, Tokyo, Japan",
                    "type": "train_station",
                }
            ],
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/search"),
        )
        mock_http_client.get.return_value = mock_response

        tool = POISearchTool()
        result = await tool.execute(query="station", provider="nominatim")

        assert result.status == ToolStatus.SUCCESS
        assert len(result.output) == 1
        assert result.output[0]["name"] == "Tokyo Station"

    @pytest.mark.asyncio
    async def test_execute_overpass(self, mock_http_client):
        """测试使用 Overpass 搜索"""
        # 模拟响应
        mock_response = httpx.Response(
            200,
            json={
                "elements": [
                    {
                        "lat": 35.6812,
                        "lon": 139.7671,
                        "tags": {
                            "name": "Tokyo Station",
                            "amenity": "train_station",
                        },
                    }
                ]
            },
            request=httpx.Request("POST", "https://overpass-api.de/api/interpreter"),
        )
        mock_http_client.post.return_value = mock_response

        tool = POISearchTool()
        result = await tool.execute(
            query="station",
            lat=35.6812,
            lon=139.7671,
            provider="overpass",
        )

        assert result.status == ToolStatus.SUCCESS
        assert len(result.output) == 1
        assert result.output[0]["name"] == "Tokyo Station"

    @pytest.mark.asyncio
    async def test_execute_no_results(self, mock_http_client):
        """测试无结果"""
        # 模拟空响应
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "https://nominatim.openstreetmap.org/search"),
        )
        mock_http_client.get.return_value = mock_response

        tool = POISearchTool()
        result = await tool.execute(query="nonexistent", provider="nominatim")

        assert result.status == ToolStatus.ERROR
        assert "No POIs found" in result.error_message


class TestToolRegistration:
    """测试工具注册"""

    def test_geocode_tool_registered(self):
        """测试 geocode 工具已注册"""
        registry = get_registry()
        assert registry.has("geocode")

        tool = registry.get("geocode")
        assert tool is not None
        assert tool.name == "geocode"
        assert tool.category == "geo"

    def test_reverse_geocode_tool_registered(self):
        """测试 reverse_geocode 工具已注册"""
        registry = get_registry()
        assert registry.has("reverse_geocode")

        tool = registry.get("reverse_geocode")
        assert tool is not None
        assert tool.name == "reverse_geocode"

    def test_poi_search_tool_registered(self):
        """测试 poi_search 工具已注册"""
        registry = get_registry()
        assert registry.has("poi_search")

        tool = registry.get("poi_search")
        assert tool is not None
        assert tool.name == "poi_search"

