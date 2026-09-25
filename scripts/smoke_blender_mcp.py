"""Exercise the optional Blender MCP tool through the real stdio protocol."""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image, ImageChops


async def main():
    root = Path(__file__).parents[1]
    sys.path.insert(0, str(root))
    from sodam_rhino_mcp.blender_render import export_scene
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
            with (Image.open(work / "blender" / "front.png") as front,
                  Image.open(work / "blender" / "rear.png") as rear):
                assert front.size == rear.size == (1200, 800)
                assert ImageChops.difference(front.convert("RGB"), rear.convert("RGB")).getbbox(), (
                    "front and rear views are visually identical"
                )
            original_scene = export_scene(work / "house.3dm")
            original_parts = {part["name"]: part for part in original_scene["objects"]}
            shutil.copy2(work / "blender" / "scene.blend", work / "scene.blend")
            edit_script = work / "edit.py"
            edit_script.write_text(
                "import bpy\n"
                "bpy.data.objects['ground_slab'].location.x += 1.0\n"
                "bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)\n",
                encoding="utf-8",
            )
            edited = await asyncio.to_thread(subprocess.run,
                [blender, "-b", "--factory-startup", "--disable-autoexec",
                 str(work / "scene.blend"), "--python", str(edit_script)],
                capture_output=True, text=True, timeout=120, check=False,
                stdin=subprocess.DEVNULL,
            )
            assert edited.returncode == 0, (edited.stderr[-1000:], edited.stdout[-1000:])
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
            edited_parts = {part["name"]: part for part in export_scene(work / "roundtrip.3dm")["objects"]}
            assert set(edited_parts) == set(original_parts)
            for name, original in original_parts.items():
                result = edited_parts[name]
                delta = 1.0 if name == "ground_slab" else 0.0
                assert result["layer"] == original["layer"], name
                for before, after in zip(original["vertices"], result["vertices"]):
                    assert abs(after[0] - before[0] - delta) < 1e-5, name
                    assert abs(after[1] - before[1]) < 1e-5, name
                    assert abs(after[2] - before[2]) < 1e-5, name
            print("MCP Blender edit/import: moved one object by 1 m; other geometry unchanged")


if __name__ == "__main__":
    asyncio.run(main())
