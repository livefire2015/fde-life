import datetime
import json
import math
import os

from mcp.server.fastmcp import FastMCP

port = int(os.environ.get("MCP_SERVER_PORT", "8090"))
host = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")

mcp = FastMCP("FDE Life Demo Tools", host=host, port=port)


@mcp.tool()
def get_current_time(timezone: str = "UTC") -> str:
    """Get the current date and time.

    Args:
        timezone: IANA timezone name (e.g. "UTC", "US/Eastern", "Asia/Tokyo").
    """
    try:
        import zoneinfo

        tz = zoneinfo.ZoneInfo(timezone)
    except (KeyError, Exception):
        tz = datetime.timezone.utc
        timezone = "UTC (fallback)"

    now = datetime.datetime.now(tz)
    return json.dumps(
        {
            "timezone": timezone,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
        }
    )


@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Supports basic arithmetic (+, -, *, /, **), math functions (sin, cos, sqrt, log, etc.),
    and constants (pi, e).

    Args:
        expression: A mathematical expression to evaluate (e.g. "sqrt(144) + 2**3").
    """
    allowed_names = {
        name: getattr(math, name)
        for name in dir(math)
        if not name.startswith("_")
    }
    allowed_names["abs"] = abs
    allowed_names["round"] = round
    allowed_names["min"] = min
    allowed_names["max"] = max

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return json.dumps({"expression": expression, "result": result})
    except Exception as e:
        return json.dumps({"expression": expression, "error": str(e)})


@mcp.tool()
def get_system_info() -> str:
    """Get information about the FDE Life demo system architecture.

    Returns a description of how the system components are connected.
    """
    return json.dumps(
        {
            "name": "FDE Life",
            "description": "AI chat application with MCP tool integration",
            "components": [
                {
                    "name": "Frontend",
                    "tech": "SolidJS + Vite + TailwindCSS",
                    "port": 3000,
                    "role": "Chat UI with real-time streaming",
                },
                {
                    "name": "Backend",
                    "tech": "Go + Chi router",
                    "port": 8080,
                    "role": "HTTP-to-gRPC bridge with SSE streaming",
                },
                {
                    "name": "Agent",
                    "tech": "Python + gRPC + xAI SDK",
                    "port": 50051,
                    "role": "AI model integration with tool routing",
                },
                {
                    "name": "MCP Server",
                    "tech": "Python + FastMCP",
                    "port": 8090,
                    "role": "Tool discovery and execution via MCP protocol",
                },
            ],
            "flow": "Frontend -> HTTP/SSE -> Backend -> gRPC -> Agent -> MCP Server / xAI API",
        }
    )


if __name__ == "__main__":
    mcp.run(transport="sse")
