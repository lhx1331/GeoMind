"""
MCP 协议数据模型

定义 MCP (Model Context Protocol) 的消息格式和数据结构。
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MCPMessageType(str, Enum):
    """MCP 消息类型"""

    # 客户端请求
    INITIALIZE = "initialize"
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    PING = "ping"

    # 服务端响应
    INITIALIZED = "initialized"
    TOOLS_LIST = "tools/list_result"
    TOOL_RESULT = "tools/call_result"
    PONG = "pong"
    ERROR = "error"


class MCPCapabilities(BaseModel):
    """MCP 能力声明"""

    tools: bool = Field(default=True, description="是否支持工具")
    prompts: bool = Field(default=False, description="是否支持提示词")
    resources: bool = Field(default=False, description="是否支持资源")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tools": True,
                "prompts": False,
                "resources": False,
            }
        }
    )


class MCPClientInfo(BaseModel):
    """MCP 客户端信息"""

    name: str = Field(description="客户端名称")
    version: str = Field(description="客户端版本")

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "geomind", "version": "0.1.0"}}
    )


class MCPServerInfo(BaseModel):
    """MCP 服务端信息"""

    name: str = Field(description="服务端名称")
    version: str = Field(description="服务端版本")
    capabilities: MCPCapabilities = Field(
        default_factory=MCPCapabilities, description="服务端能力"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "mcp-server",
                "version": "1.0.0",
                "capabilities": {"tools": True},
            }
        }
    )


class MCPToolParameter(BaseModel):
    """MCP 工具参数"""

    name: str = Field(description="参数名称")
    type: str = Field(description="参数类型")
    description: Optional[str] = Field(default=None, description="参数描述")
    required: bool = Field(default=True, description="是否必需")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "location",
                "type": "string",
                "description": "Location name",
                "required": True,
            }
        }
    )


class MCPToolInfo(BaseModel):
    """MCP 工具信息"""

    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    inputSchema: Dict[str, Any] = Field(description="输入 Schema")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "geocode",
                "description": "Convert location to coordinates",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Location name"}
                    },
                    "required": ["location"],
                },
            }
        }
    )


class MCPMessage(BaseModel):
    """MCP 消息基类"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    id: Optional[str] = Field(default=None, description="消息 ID")
    method: Optional[str] = Field(default=None, description="方法名")
    params: Optional[Dict[str, Any]] = Field(default=None, description="参数")
    result: Optional[Any] = Field(default=None, description="结果")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
                "params": {},
            }
        }
    )

    @classmethod
    def request(
        cls,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ) -> "MCPMessage":
        """创建请求消息"""
        return cls(
            id=message_id,
            method=method,
            params=params or {},
        )

    @classmethod
    def response(
        cls,
        result: Any,
        message_id: Optional[str] = None,
    ) -> "MCPMessage":
        """创建响应消息"""
        return cls(
            id=message_id,
            result=result,
        )

    @classmethod
    def error_response(
        cls,
        code: int,
        message: str,
        message_id: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> "MCPMessage":
        """创建错误响应"""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return cls(
            id=message_id,
            error=error,
        )

    def is_request(self) -> bool:
        """是否为请求消息"""
        return self.method is not None

    def is_response(self) -> bool:
        """是否为响应消息"""
        return self.result is not None or self.error is not None

    def is_error(self) -> bool:
        """是否为错误响应"""
        return self.error is not None


class MCPInitializeRequest(BaseModel):
    """初始化请求参数"""

    protocolVersion: str = Field(default="1.0.0", description="协议版本")
    clientInfo: MCPClientInfo = Field(description="客户端信息")
    capabilities: MCPCapabilities = Field(
        default_factory=MCPCapabilities, description="客户端能力"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "protocolVersion": "1.0.0",
                "clientInfo": {"name": "geomind", "version": "0.1.0"},
                "capabilities": {"tools": True},
            }
        }
    )


class MCPInitializeResponse(BaseModel):
    """初始化响应"""

    protocolVersion: str = Field(description="协议版本")
    serverInfo: MCPServerInfo = Field(description="服务端信息")
    capabilities: MCPCapabilities = Field(description="服务端能力")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "protocolVersion": "1.0.0",
                "serverInfo": {
                    "name": "mcp-server",
                    "version": "1.0.0",
                    "capabilities": {"tools": True},
                },
                "capabilities": {"tools": True},
            }
        }
    )


class MCPListToolsResponse(BaseModel):
    """工具列表响应"""

    tools: List[MCPToolInfo] = Field(description="工具列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tools": [
                    {
                        "name": "geocode",
                        "description": "Convert location to coordinates",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "Location name",
                                }
                            },
                            "required": ["location"],
                        },
                    }
                ]
            }
        }
    )


class MCPCallToolRequest(BaseModel):
    """工具调用请求"""

    name: str = Field(description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "geocode", "arguments": {"location": "Tokyo"}}
        }
    )


class MCPToolCallResult(BaseModel):
    """工具调用结果"""

    content: List[Dict[str, Any]] = Field(description="结果内容")
    isError: bool = Field(default=False, description="是否为错误")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": [
                    {
                        "type": "text",
                        "text": '{"lat": 35.6762, "lon": 139.6503}',
                    }
                ],
                "isError": False,
            }
        }
    )


# MCP 错误码
class MCPErrorCode:
    """MCP 错误码"""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # 自定义错误码
    CONNECTION_ERROR = -32000
    TIMEOUT_ERROR = -32001
    TOOL_NOT_FOUND = -32002
    TOOL_EXECUTION_ERROR = -32003


__all__ = [
    "MCPMessageType",
    "MCPCapabilities",
    "MCPClientInfo",
    "MCPServerInfo",
    "MCPToolParameter",
    "MCPToolInfo",
    "MCPMessage",
    "MCPInitializeRequest",
    "MCPInitializeResponse",
    "MCPListToolsResponse",
    "MCPCallToolRequest",
    "MCPToolCallResult",
    "MCPErrorCode",
]

