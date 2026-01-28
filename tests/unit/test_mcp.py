"""
MCP 客户端单元测试
"""

import json
from typing import Any, Dict

import httpx
import pytest
from pytest_mock import MockerFixture

from geomind.tools.base import ToolStatus
from geomind.tools.mcp.client import MCPClient, MCPClientError, create_mcp_client
from geomind.tools.mcp.protocol import (
    MCPCallToolRequest,
    MCPClientInfo,
    MCPErrorCode,
    MCPInitializeRequest,
    MCPListToolsResponse,
    MCPMessage,
    MCPToolCallResult,
    MCPToolInfo,
)
from geomind.tools.registry import get_registry


class TestMCPProtocol:
    """测试 MCP 协议数据模型"""

    def test_mcp_message_request(self):
        """测试创建请求消息"""
        msg = MCPMessage.request(
            method="tools/list",
            params={"test": "value"},
            message_id="123",
        )

        assert msg.jsonrpc == "2.0"
        assert msg.id == "123"
        assert msg.method == "tools/list"
        assert msg.params == {"test": "value"}
        assert msg.is_request()
        assert not msg.is_response()

    def test_mcp_message_response(self):
        """测试创建响应消息"""
        msg = MCPMessage.response(
            result={"tools": []},
            message_id="123",
        )

        assert msg.jsonrpc == "2.0"
        assert msg.id == "123"
        assert msg.result == {"tools": []}
        assert msg.is_response()
        assert not msg.is_request()

    def test_mcp_message_error(self):
        """测试创建错误响应"""
        msg = MCPMessage.error_response(
            code=-32600,
            message="Invalid request",
            message_id="123",
        )

        assert msg.jsonrpc == "2.0"
        assert msg.id == "123"
        assert msg.error["code"] == -32600
        assert msg.error["message"] == "Invalid request"
        assert msg.is_error()

    def test_mcp_initialize_request(self):
        """测试初始化请求"""
        req = MCPInitializeRequest(
            clientInfo=MCPClientInfo(name="test", version="1.0.0")
        )

        assert req.protocolVersion == "1.0.0"
        assert req.clientInfo.name == "test"
        assert req.capabilities.tools is True

    def test_mcp_tool_info(self):
        """测试工具信息"""
        tool = MCPToolInfo(
            name="geocode",
            description="Geocode a location",
            inputSchema={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        )

        assert tool.name == "geocode"
        assert "location" in tool.inputSchema["properties"]

    def test_mcp_call_tool_request(self):
        """测试工具调用请求"""
        req = MCPCallToolRequest(
            name="geocode",
            arguments={"location": "Tokyo"},
        )

        assert req.name == "geocode"
        assert req.arguments["location"] == "Tokyo"

    def test_mcp_tool_call_result(self):
        """测试工具调用结果"""
        result = MCPToolCallResult(
            content=[{"type": "text", "text": "Success"}],
            isError=False,
        )

        assert len(result.content) == 1
        assert result.isError is False


class TestMCPClient:
    """测试 MCP 客户端"""

    @pytest.fixture
    def mock_http_client(self, mocker: MockerFixture):
        """模拟 HTTP 客户端"""
        mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    @pytest.fixture
    def mock_initialize_response(self) -> Dict[str, Any]:
        """模拟初始化响应"""
        return {
            "protocolVersion": "1.0.0",
            "serverInfo": {
                "name": "test-server",
                "version": "1.0.0",
                "capabilities": {"tools": True},
            },
            "capabilities": {"tools": True},
        }

    @pytest.fixture
    def mock_tools_list_response(self) -> Dict[str, Any]:
        """模拟工具列表响应"""
        return {
            "tools": [
                {
                    "name": "geocode",
                    "description": "Geocode a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                    },
                }
            ]
        }

    @pytest.fixture
    def mock_tool_call_response(self) -> Dict[str, Any]:
        """模拟工具调用响应"""
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"lat": 35.6762, "lon": 139.6503}),
                }
            ],
            "isError": False,
        }

    def test_mcp_client_init(self):
        """测试客户端初始化"""
        client = MCPClient(
            server_url="http://localhost:8000",
            client_name="test",
            client_version="1.0.0",
        )

        assert client.server_url == "http://localhost:8000"
        assert client.client_name == "test"
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_connect(
        self,
        mock_http_client,
        mock_initialize_response,
    ):
        """测试连接"""
        # 模拟 HTTP 响应
        mock_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=httpx.Request("POST", "http://localhost:8000"),
        )
        mock_http_client.post.return_value = mock_response

        client = MCPClient(server_url="http://localhost:8000")
        await client.connect()

        assert client.is_connected
        assert mock_http_client.post.called

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_discover_tools(
        self,
        mock_http_client,
        mock_initialize_response,
        mock_tools_list_response,
    ):
        """测试发现工具"""
        # 创建一个 mock request
        mock_request = httpx.Request("POST", "http://localhost:8000")
        
        # 模拟初始化响应
        init_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        # 模拟工具列表响应
        tools_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_tools_list_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        mock_http_client.post.side_effect = [init_response, tools_response]

        client = MCPClient(server_url="http://localhost:8000")
        await client.connect()

        tools = await client.discover_tools()

        assert len(tools) == 1
        assert tools[0].name == "geocode"
        assert "geocode" in client.list_tools()

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_call_tool(
        self,
        mock_http_client,
        mock_initialize_response,
        mock_tools_list_response,
        mock_tool_call_response,
    ):
        """测试调用工具"""
        mock_request = httpx.Request("POST", "http://localhost:8000")
        
        # 模拟响应序列
        init_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        tools_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_tools_list_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        call_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_tool_call_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        mock_http_client.post.side_effect = [
            init_response,
            tools_response,
            call_response,
        ]

        client = MCPClient(server_url="http://localhost:8000")
        await client.connect()
        await client.discover_tools()

        result = await client.call_tool("geocode", {"location": "Tokyo"})

        assert result.status == ToolStatus.SUCCESS
        assert result.output["lat"] == 35.6762
        assert result.output["lon"] == 139.6503

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_call_tool_not_found(
        self,
        mock_http_client,
        mock_initialize_response,
        mock_tools_list_response,
    ):
        """测试调用不存在的工具"""
        mock_request = httpx.Request("POST", "http://localhost:8000")
        
        init_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        tools_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_tools_list_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        mock_http_client.post.side_effect = [init_response, tools_response]

        client = MCPClient(server_url="http://localhost:8000")
        await client.connect()
        await client.discover_tools()

        with pytest.raises(MCPClientError, match="not found"):
            await client.call_tool("nonexistent", {})

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_call_tool_error(
        self,
        mock_http_client,
        mock_initialize_response,
        mock_tools_list_response,
    ):
        """测试工具调用错误"""
        mock_request = httpx.Request("POST", "http://localhost:8000")
        
        init_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        tools_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_tools_list_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        # 模拟工具执行错误
        error_response = httpx.Response(
            200,
            json=MCPMessage.response(
                {
                    "content": [{"type": "text", "text": "Tool execution failed"}],
                    "isError": True,
                }
            ).model_dump(exclude_none=True),
            request=mock_request,
        )

        mock_http_client.post.side_effect = [
            init_response,
            tools_response,
            error_response,
        ]

        client = MCPClient(server_url="http://localhost:8000")
        await client.connect()
        await client.discover_tools()

        result = await client.call_tool("geocode", {"location": "Invalid"})

        assert result.status == ToolStatus.ERROR
        assert "failed" in result.error_message.lower()

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_register_tools(
        self,
        mock_http_client,
        mock_initialize_response,
        mock_tools_list_response,
    ):
        """测试注册工具到注册表"""
        mock_request = httpx.Request("POST", "http://localhost:8000")
        
        init_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        tools_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_tools_list_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        mock_http_client.post.side_effect = [init_response, tools_response]

        # 清空注册表
        registry = get_registry()
        registry.clear()

        client = MCPClient(server_url="http://localhost:8000")
        await client.connect()

        count = await client.register_tools()

        assert count == 1
        assert registry.has("geocode")

        # 验证工具可以执行
        tool = registry.get("geocode")
        assert tool is not None
        assert tool.category == "mcp"

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_context_manager(
        self,
        mock_http_client,
        mock_initialize_response,
    ):
        """测试上下文管理器"""
        mock_request = httpx.Request("POST", "http://localhost:8000")
        
        init_response = httpx.Response(
            200,
            json=MCPMessage.response(mock_initialize_response).model_dump(
                exclude_none=True
            ),
            request=mock_request,
        )

        mock_http_client.post.return_value = init_response

        async with MCPClient(server_url="http://localhost:8000") as client:
            assert client.is_connected

        # 退出后应该断开连接
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_connection_error(self, mock_http_client):
        """测试连接错误"""
        mock_http_client.post.side_effect = httpx.ConnectError("Connection failed")

        client = MCPClient(server_url="http://localhost:8000")

        with pytest.raises(MCPClientError, match="Connection failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_not_connected_error(self):
        """测试未连接错误"""
        client = MCPClient(server_url="http://localhost:8000")

        with pytest.raises(MCPClientError, match="not connected"):
            await client.discover_tools()

        with pytest.raises(MCPClientError, match="not connected"):
            await client.call_tool("test", {})

    def test_get_tool_info(self):
        """测试获取工具信息"""
        client = MCPClient(server_url="http://localhost:8000")

        # 手动添加工具信息
        tool_info = MCPToolInfo(
            name="test",
            description="Test tool",
            inputSchema={"type": "object"},
        )
        client._tools["test"] = tool_info

        info = client.get_tool_info("test")
        assert info is not None
        assert info.name == "test"

        # 不存在的工具
        assert client.get_tool_info("nonexistent") is None

    def test_repr(self):
        """测试字符串表示"""
        client = MCPClient(server_url="http://localhost:8000")

        repr_str = repr(client)
        assert "localhost:8000" in repr_str
        assert "disconnected" in repr_str

