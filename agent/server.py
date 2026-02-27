import asyncio
import json
import logging
import os
import grpc
from concurrent import futures
import sys

# Add the generated proto directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "generated"))

# Import generated classes
import chat_pb2
import chat_pb2_grpc

import xai_sdk
from dotenv import load_dotenv
from xai_sdk.chat import user, tool_result
from xai_sdk.tools import web_search, x_search, code_execution

from mcp_bridge import McpBridge

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, mcp_bridge=None):
        self.client = xai_sdk.Client()
        self.model = "grok-4-fast"  # Default model
        self.mcp_bridge = mcp_bridge

    def _get_tools(self):
        """Get all available tools including MCP-discovered tools."""
        tools = [web_search(), x_search(), code_execution()]
        if self.mcp_bridge:
            tools.extend(self.mcp_bridge.get_tools())
        return tools

    async def StreamChat(self, request, context):
        logger.info(f"Received request with {len(request.messages)} messages")

        try:
            chat = self.client.chat.create(
                model="grok-4-fast",
                tools=self._get_tools(),
            )

            for msg in request.messages:
                if msg.role == "user":
                    chat.append(user(msg.content))

            # Agentic loop: stream, handle client-side tool calls, re-stream
            while True:
                is_thinking = True
                client_tool_calls = []

                # Note: chat.stream() is synchronous in the current SDK version
                for response, chunk in chat.stream():
                    for tool_call in chunk.tool_calls:
                        if (
                            self.mcp_bridge
                            and McpBridge.is_client_side_tool_call(tool_call)
                        ):
                            client_tool_calls.append(tool_call)
                            logger.info(
                                f"MCP tool call: {tool_call.function.name} "
                                f"with arguments: {tool_call.function.arguments}"
                            )
                        else:
                            logger.info(
                                f"Server tool: {tool_call.function.name} "
                                f"with arguments: {tool_call.function.arguments}"
                            )

                    if chunk.content:
                        if is_thinking:
                            is_thinking = False
                        yield chat_pb2.ChatResponse(chunk=chunk.content)

                # If no client-side tool calls, we're done
                if not client_tool_calls:
                    break

                # Append assistant response to history
                chat.append(response)

                # Execute each MCP tool call and append results
                for tc in client_tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = await self.mcp_bridge.call_tool(
                        tc.function.name, args
                    )
                    chat.append(tool_result(result))
                    logger.info(
                        f"MCP tool result for {tc.function.name}: {result[:200]}"
                    )

                # Loop continues — model processes tool results and generates more

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

    async def SampleChat(self, request, context):
        logger.info(f"Received request with {len(request.messages)} messages")

        # Convert proto messages to xAI SDK format
        conversation = []
        for msg in request.messages:
            conversation.append({"role": msg.role, "content": msg.content})

        try:
            # Create sampler
            sampler = self.client.sampler

            # Stream response
            async for token in sampler.sample(
                messages=conversation, model_name=self.model, stream=True
            ):
                content = ""
                if hasattr(token, "token_str"):
                    content = token.token_str
                elif hasattr(token, "text"):
                    content = token.text
                elif isinstance(token, str):
                    content = token
                else:
                    content = str(token)

                yield chat_pb2.ChatResponse(chunk=content)

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))


async def serve():
    # We need to import the generated modules here to avoid import errors before generation
    global chat_pb2, chat_pb2_grpc
    import chat_pb2
    import chat_pb2_grpc

    # Initialize MCP bridge if server URL is configured
    mcp_bridge = None
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    if mcp_server_url:
        mcp_bridge = McpBridge(mcp_server_url)
        try:
            await mcp_bridge.connect()
            logger.info(
                f"Connected to MCP server at {mcp_server_url}, "
                f"discovered {len(mcp_bridge.get_tools())} tools"
            )
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server: {e}")
            mcp_bridge = None
    else:
        logger.info("No MCP_SERVER_URL set, running without MCP tools")

    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(
        ChatServiceServicer(mcp_bridge=mcp_bridge), server
    )
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting server on {listen_addr}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
