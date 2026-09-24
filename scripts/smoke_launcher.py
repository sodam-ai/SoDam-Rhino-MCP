"""Verify that the documented Windows launcher speaks MCP over stdio."""

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    root = Path(__file__).parents[1]
    server = StdioServerParameters(
        command="cmd.exe",
        args=["/c", str(root / "start_mcp.cmd")],
        cwd=str(root),
    )
    async with stdio_client(server) as streams, ClientSession(*streams) as session:
        await session.initialize()
        names = {tool.name for tool in (await session.list_tools()).tools}
        assert "build_architectural_model" in names, names
        assert "write_architectural_spec" in names, names
        assert "revise_architectural_spec" in names, names
        assert "render_blender_model" in names, names
        print(f"Launcher MCP tools: {len(names)}")


if __name__ == "__main__":
    asyncio.run(main())
