"""
MCP 客户端实现

实现 MCP (Model Context Protocol) 客户端，用于连接和调用 MCP 服务器的工具。
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

import httpx

from geomind.config import get_settings
from geomind.tools.base import BaseTool, ToolResult, ToolSchema, ToolStatus
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
from geomind.utils.logging import get_logger
from geomind.utils.retry import retry

logger = get_logger(__name__)


class MCPClientError(Exception):
    """MCP 客户端错误"""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class MCPClient:
    """MCP 客户端

    连接到 MCP 服务器，发现和调用工具。
    """

    def __init__(
        self,
        server_url: str,
        client_name: str = "geomind",
        client_version: str = "0.1.0",
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        """初始化 MCP 客户端

        Args:
            server_url: MCP 服务器 URL
            client_name: 客户端名称
            client_version: 客户端版本
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.server_url = server_url.rstrip("/")
        self.client_name = client_name
        self.client_version = client_version

        settings = get_settings()
        self.timeout = timeout or settings.mcp.timeout
        self.max_retries = max_retries or settings.mcp.max_retries

        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self._server_info: Optional[Dict[str, Any]] = None
        self._tools: Dict[str, MCPToolInfo] = {}

    async def __aenter__(self) -> "MCPClient":
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()

    async def connect(self) -> None:
        """连接到 MCP 服务器"""
        if self._client is not None:
            logger.warning("MCP client already connected")
            return

        try:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            # 初始化连接
            await self._initialize()

            logger.info(
                f"MCP client connected",
                server_url=self.server_url,
                server_info=self._server_info,
            )

        except Exception as e:
            logger.error(f"Failed to connect to MCP server", error=str(e))
            if self._client:
                await self._client.aclose()
                self._client = None
            raise MCPClientError(f"Connection failed: {e}", MCPErrorCode.CONNECTION_ERROR)

    async def disconnect(self) -> None:
        """断开连接"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._initialized = False
            self._tools.clear()
            logger.info("MCP client disconnected")

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._client is not None and self._initialized

    @retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """发送 MCP 请求

        Args:
            method: 方法名
            params: 参数

        Returns:
            响应结果

        Raises:
            MCPClientError: 请求失败
        """
        if self._client is None:
            raise MCPClientError("Client not connected", MCPErrorCode.CONNECTION_ERROR)

        message_id = str(uuid.uuid4())
        request = MCPMessage.request(method=method, params=params, message_id=message_id)

        try:
            logger.debug(f"Sending MCP request", method=method, params=params)

            response = await self._client.post(
                self.server_url,
                json=request.model_dump(exclude_none=True),
            )
            response.raise_for_status()

            response_data = response.json()
            response_msg = MCPMessage(**response_data)

            if response_msg.is_error():
                error = response_msg.error or {}
                raise MCPClientError(
                    error.get("message", "Unknown error"),
                    error.get("code", MCPErrorCode.INTERNAL_ERROR),
                )

            logger.debug(f"Received MCP response", method=method, result=response_msg.result)

            return response_msg.result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error in MCP request", method=method, error=str(e))
            raise
        except Exception as e:
            logger.error(f"MCP request failed", method=method, error=str(e))
            raise MCPClientError(str(e), MCPErrorCode.INTERNAL_ERROR)

    async def _initialize(self) -> None:
        """初始化 MCP 连接"""
        init_params = MCPInitializeRequest(
            clientInfo=MCPClientInfo(
                name=self.client_name,
                version=self.client_version,
            )
        )

        result = await self._send_request(
            method="initialize",
            params=init_params.model_dump(),
        )

        self._server_info = result
        self._initialized = True

        logger.info(f"MCP initialized", server_info=result)

    async def discover_tools(self) -> List[MCPToolInfo]:
        """发现服务器上的工具

        Returns:
            工具列表

        Raises:
            MCPClientError: 发现失败
        """
        if not self.is_connected:
            raise MCPClientError("Client not connected", MCPErrorCode.CONNECTION_ERROR)

        result = await self._send_request(method="tools/list")

        response = MCPListToolsResponse(**result)
        self._tools = {tool.name: tool for tool in response.tools}

        logger.info(f"Discovered {len(self._tools)} tools", tools=list(self._tools.keys()))

        return response.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果

        Raises:
            MCPClientError: 调用失败
        """
        if not self.is_connected:
            raise MCPClientError("Client not connected", MCPErrorCode.CONNECTION_ERROR)

        if tool_name not in self._tools:
            raise MCPClientError(
                f"Tool not found: {tool_name}",
                MCPErrorCode.TOOL_NOT_FOUND,
            )

        call_params = MCPCallToolRequest(
            name=tool_name,
            arguments=arguments or {},
        )

        try:
            result = await self._send_request(
                method="tools/call",
                params=call_params.model_dump(),
            )

            tool_result = MCPToolCallResult(**result)

            if tool_result.isError:
                error_text = self._extract_text_from_content(tool_result.content)
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=error_text,
                    metadata={"tool": tool_name, "mcp": True},
                )

            output_text = self._extract_text_from_content(tool_result.content)

            # 尝试解析为 JSON
            try:
                output = json.loads(output_text)
            except json.JSONDecodeError:
                output = output_text

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=output,
                metadata={"tool": tool_name, "mcp": True},
            )

        except MCPClientError as e:
            if e.code == MCPErrorCode.TOOL_NOT_FOUND:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Tool not found: {tool_name}",
                    metadata={"tool": tool_name, "mcp": True},
                )
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=str(e),
                    metadata={"tool": tool_name, "mcp": True},
                )

    def _extract_text_from_content(self, content: List[Dict[str, Any]]) -> str:
        """从内容中提取文本

        Args:
            content: MCP 内容列表

        Returns:
            提取的文本
        """
        texts = []
        for item in content:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
        return "\n".join(texts)

    async def register_tools(self, auto_discover: bool = True) -> int:
        """将 MCP 工具注册到工具注册表

        Args:
            auto_discover: 是否自动发现工具

        Returns:
            注册的工具数量
        """
        if auto_discover:
            await self.discover_tools()

        registry = get_registry()
        registered_count = 0

        for tool_name, tool_info in self._tools.items():
            # 创建工具包装类
            mcp_tool = self._create_tool_wrapper(tool_name, tool_info)
            registry.register(mcp_tool, override=True)
            registered_count += 1

        logger.info(f"Registered {registered_count} MCP tools to registry")

        return registered_count

    def _create_tool_wrapper(self, tool_name: str, tool_info: MCPToolInfo) -> BaseTool:
        """创建工具包装类

        Args:
            tool_name: 工具名称
            tool_info: 工具信息

        Returns:
            工具实例
        """
        client = self

        class MCPToolWrapper(BaseTool):
            @property
            def name(self) -> str:
                return tool_name

            @property
            def description(self) -> str:
                return tool_info.description

            @property
            def category(self) -> Optional[str]:
                return "mcp"

            @property
            def tags(self) -> List[str]:
                return ["mcp", "remote"]

            async def execute(self, **kwargs: Any) -> ToolResult:
                return await client.call_tool(tool_name, kwargs)

        return MCPToolWrapper()

    def get_tool_info(self, tool_name: str) -> Optional[MCPToolInfo]:
        """获取工具信息

        Args:
            tool_name: 工具名称

        Returns:
            工具信息，如果不存在则返回 None
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return f"MCPClient(server={self.server_url}, status={status}, tools={len(self._tools)})"


async def create_mcp_client(
    server_url: Optional[str] = None,
    auto_connect: bool = True,
    auto_register: bool = True,
) -> MCPClient:
    """创建并初始化 MCP 客户端

    Args:
        server_url: MCP 服务器 URL（如果为 None，从配置读取）
        auto_connect: 是否自动连接
        auto_register: 是否自动注册工具

    Returns:
        MCP 客户端实例
    """
    settings = get_settings()
    url = server_url or settings.mcp.server_url

    if not url:
        raise ValueError("MCP server URL not provided")

    client = MCPClient(server_url=url)

    if auto_connect:
        await client.connect()

        if auto_register:
            await client.register_tools()

    return client


__all__ = [
    "MCPClient",
    "MCPClientError",
    "create_mcp_client",
]

