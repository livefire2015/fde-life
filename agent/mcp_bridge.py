"""Bridge between MCP tool discovery and xAI SDK tool format."""

import json
import logging

from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from xai_sdk.chat import tool as xai_tool
from xai_sdk.tools import get_tool_call_type

logger = logging.getLogger(__name__)


class McpBridge:
    """Connects to an MCP server via SSE, discovers tools, and provides
    xAI-compatible tool definitions. Can execute tool calls on the MCP server."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self._tools = []  # list of chat_pb2.Tool
        self._tool_names: set[str] = set()
        self._exit_stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def connect(self):
        """Connect to MCP server and discover tools."""
        self._exit_stack = AsyncExitStack()
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            sse_client(self.server_url)
        )
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

        result = await self._session.list_tools()
        for mcp_tool in result.tools:
            xai_tool_def = xai_tool(
                name=mcp_tool.name,
                description=mcp_tool.description or "",
                parameters=mcp_tool.inputSchema,
            )
            self._tools.append(xai_tool_def)
            self._tool_names.add(mcp_tool.name)
            logger.info(f"Discovered MCP tool: {mcp_tool.name}")

    async def close(self):
        """Close the MCP connection."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self._session = None

    def get_tools(self):
        """Return discovered tools in xAI format."""
        return list(self._tools)

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if a tool name belongs to an MCP-discovered tool."""
        return tool_name in self._tool_names

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool call on the MCP server and return the result as a string."""
        if not self._session:
            raise RuntimeError("MCP bridge not connected")

        logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
        result = await self._session.call_tool(tool_name, arguments)

        # Concatenate text content from the result
        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
            else:
                parts.append(str(content))

        return "\n".join(parts)

    @staticmethod
    def is_client_side_tool_call(tool_call) -> bool:
        """Check if a tool call is a client-side tool (i.e. one we need to handle)."""
        return get_tool_call_type(tool_call) == "client_side_tool"
