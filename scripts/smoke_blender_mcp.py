"""Exercise the optional Blender MCP tool through the real stdio protocol."""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    root = Path(__file__).parents[1]
    blender = os.environ["SODAM_BLENDER_EXE"]
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        (work / "house.json").write_text(
            (root / "examples" / "small_house.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "sodam_rhino_mcp.server"],
            cwd=str(root),
            env={**os.environ, "SODAM_RHINO_WORKSPACE": str(work),
                 "SODAM_BLENDER_EXE": blender},
        )
        async with stdio_client(server) as streams, ClientSession(*streams) as session:
            await session.initialize()
            built = await session.call_tool("build_architectural_model", {
                "spec_json": "house.json", "output_3dm": "house.3dm"})
            assert not built.isError, built
            rendered = await session.call_tool("render_blender_model", {
                "model_3dm": "house.3dm", "output_folder": "blender",
                "front_azimuth": 300, "front_elevation": 32,
                "rear_azimuth": 120, "rear_elevation": 20})
            assert not rendered.isError, rendered
            cameras = json.loads(rendered.content[0].text)["cameras"]
            assert cameras["front"] == {"azimuth": 300, "elevation": 32}, cameras
            assert cameras["rear"] == {"azimuth": 120, "elevation": 20}, cameras
            for name in ("front.png", "rear.png", "scene.blend"):
                assert (work / "blender" / name).stat().st_size > 1000, name
            shutil.copy2(work / "blender" / "scene.blend", work / "scene.blend")
            imported = await session.call_tool("import_blender_scene", {
                "blend_file": "scene.blend", "output_3dm": "roundtrip.3dm"})
            assert not imported.isError, imported
            details = await session.call_tool("inspect_architectural_model", {
                "model_3dm": "roundtrip.3dm"})
            assert not details.isError, details
            assert (work / "roundtrip.3dm").stat().st_size > 1000
            summary = json.loads(details.content[0].text)
            assert "roof" in summary["names"], details
            assert "render_ground" not in summary["names"], details
            assert "02_Walls" in summary["layers"], details
            print("MCP Blender render/import: 2 PNG + scene.blend + roundtrip.3dm verified")


if __name__ == "__main__":
    asyncio.run(main())
