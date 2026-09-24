"""Exercise the real stdio MCP protocol in an isolated temporary workspace."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image


async def main():
    root = Path(__file__).parents[1]
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        spec_text = (root / "examples" / "small_house.json").read_text(encoding="utf-8")
        Image.new("RGB", (320, 240), (220, 230, 240)).save(work / "reference.png")
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "sodam_rhino_mcp.server"],
            cwd=str(root),
            env={**os.environ, "SODAM_RHINO_WORKSPACE": str(work)},
        )
        async with stdio_client(parameters) as streams, ClientSession(*streams) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            assert names == {
                "get_architectural_workspace", "write_architectural_spec",
                "revise_architectural_spec",
                "build_architectural_model", "inspect_architectural_model",
                "render_architectural_view", "render_blender_model",
                "import_blender_scene",
                "prepare_architectural_reference", "draft_architectural_evidence",
                "audit_architectural_evidence", "build_verified_architectural_model",
            }, names
            workspace = await session.call_tool("get_architectural_workspace", {})
            assert not workspace.isError, workspace
            assert json.loads(workspace.content[0].text)["workspace"] == str(work), workspace
            assert "cylinder" in json.loads(workspace.content[0].text)["component_kinds"]
            column_spec = {"units": "meters", "components": [{
                "kind": "cylinder", "name": "column", "layer": "Columns",
                "origin": [1, 2, 0], "size": [0.6, 0.6, 3.2], "segments": 48}]}
            column_saved = await session.call_tool(
                "write_architectural_spec", {"spec_json": json.dumps(column_spec),
                                             "output_json": "column.json"})
            assert not column_saved.isError, column_saved
            column_built = await session.call_tool(
                "build_architectural_model", {"spec_json": "column.json",
                                               "output_3dm": "column.3dm"})
            assert not column_built.isError, column_built
            column_inspected = await session.call_tool(
                "inspect_architectural_model", {"model_3dm": "column.3dm"})
            assert not column_inspected.isError, column_inspected
            assert json.loads(column_inspected.content[0].text)["names"] == ["column"]
            saved_spec = await session.call_tool(
                "write_architectural_spec", {"spec_json": spec_text, "output_json": "house.json"})
            assert not saved_spec.isError, saved_spec
            assert (work / "house.json").is_file()
            repeated_spec = await session.call_tool(
                "write_architectural_spec", {"spec_json": spec_text, "output_json": "house.json"})
            assert repeated_spec.isError, repeated_spec
            escaped_spec = await session.call_tool(
                "write_architectural_spec", {"spec_json": spec_text, "output_json": "../bad.json"})
            assert escaped_spec.isError, escaped_spec
            original_spec = json.loads(spec_text)
            roof = next(part for part in original_spec["components"] if part["name"] == "roof")
            roof["ridge_height"] = 2.2
            revised = await session.call_tool("revise_architectural_spec", {
                "source_json": "house.json", "component_name": "roof",
                "replacement_json": json.dumps(roof), "output_json": "house_v2.json"})
            assert not revised.isError, revised
            assert json.loads((work / "house_v2.json").read_text(encoding="utf-8"))["components"][-1]["ridge_height"] == 2.2
            revision_collision = await session.call_tool("revise_architectural_spec", {
                "source_json": "house.json", "component_name": "roof",
                "replacement_json": json.dumps(roof), "output_json": "house_v2.json"})
            assert revision_collision.isError, revision_collision
            built = await session.call_tool(
                "build_architectural_model", {"spec_json": "house.json", "output_3dm": "house.3dm"})
            assert not built.isError, built
            revised_model = await session.call_tool(
                "build_architectural_model", {"spec_json": "house_v2.json", "output_3dm": "house_v2.3dm"})
            assert not revised_model.isError, revised_model
            inspected = await session.call_tool(
                "inspect_architectural_model", {"model_3dm": "house.3dm"})
            assert not inspected.isError, inspected
            assert json.loads(revised_model.content[0].text)["bbox"]["max"][2] > json.loads(inspected.content[0].text)["bbox"]["max"][2]
            rendered = await session.call_tool(
                "render_architectural_view", {"model_3dm": "house.3dm", "output_png": "front.png"})
            assert not rendered.isError, rendered
            rear = await session.call_tool(
                "render_architectural_view", {"model_3dm": "house.3dm",
                                                "output_png": "rear.png", "azimuth": 135})
            assert not rear.isError, rear
            assert (work / "front.png").read_bytes() != (work / "rear.png").read_bytes()
            packet = await session.call_tool("prepare_architectural_reference", {
                "reference_images": ["reference.png"], "known_dimensions": {"facade_width": 8.0},
                "output_json": "reference.json"})
            assert not packet.isError, packet
            draft = await session.call_tool("draft_architectural_evidence", {
                "spec_json": "house.json", "reference_json": "reference.json",
                "output_json": "annotated.json"})
            assert not draft.isError, draft
            audit = await session.call_tool("audit_architectural_evidence", {
                "spec_json": "annotated.json", "reference_json": "reference.json"})
            assert not audit.isError, audit
            verified = await session.call_tool("build_verified_architectural_model", {
                "spec_json": "annotated.json", "reference_json": "reference.json",
                "output_3dm": "verified.3dm"})
            assert not verified.isError, verified
            assert (work / "house.3dm").stat().st_size > 1000
            assert (work / "verified.3dm").stat().st_size > 1000
            assert (work / "front.png").stat().st_size > 1000
            refused = await session.call_tool(
                "inspect_architectural_model", {"model_3dm": "../house.3dm"})
            assert refused.isError, refused
            print(json.dumps({
                "tools": sorted(names),
                "3dm_bytes": (work / "verified.3dm").stat().st_size,
                "png_bytes": (work / "front.png").stat().st_size,
                "path_escape_refused": refused.isError,
                "reference_to_verified_3dm": not verified.isError,
            }))


if __name__ == "__main__":
    asyncio.run(main())
