"""Local stdio MCP server; file operations stay inside its configured workspace."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .blend_import import import_blend
from .blender_render import render_blender_views
from .evidence import (
    build_verified_model,
    draft_evidence_spec,
    prepare_reference_case,
    validate_reference_case,
)
from .model import build_model, inspect_model
from .render import render_model
from .revision import revise_spec
from .spec_store import write_spec

mcp = FastMCP("sodam-rhino-offline")


@mcp.tool()
def get_architectural_workspace() -> dict:
    """Show the configured workspace and supported model types before writing files."""
    root = Path(os.environ.get("SODAM_RHINO_WORKSPACE", "workspace")).resolve()
    blender_exe = os.environ.get("SODAM_BLENDER_EXE")
    return {
        "workspace": str(root),
        "blender_executable_configured": bool(blender_exe and Path(blender_exe).is_file()),
        "component_kinds": ["box", "wall_opening", "gable_roof", "cylinder"],
        "model_format": "3dm named meshes",
        "blender_import": "evaluated mesh geometry from an editable .blend source",
        "rhino_required": False,
    }


def _workspace_file(name: str, extension: str) -> Path:
    root = Path(os.environ.get("SODAM_RHINO_WORKSPACE", "workspace")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not name or Path(name).name != name or not name.lower().endswith(extension):
        raise ValueError(f"use a simple {extension} file name inside the workspace")
    path = (root / name).resolve()
    if path.parent != root:
        raise ValueError("path escapes workspace")
    return path


@mcp.tool()
def write_architectural_spec(spec_json: str, output_json: str) -> dict:
    """Save a validated component JSON in the workspace without replacing existing files."""
    return write_spec(spec_json, _workspace_file(output_json, ".json"))


@mcp.tool()
def revise_architectural_spec(source_json: str, component_name: str,
                              replacement_json: str, output_json: str) -> dict:
    """Replace one named component in a new JSON spec; preserve the source and all other components."""
    return revise_spec(_workspace_file(source_json, ".json"), component_name,
                       replacement_json, _workspace_file(output_json, ".json"))


@mcp.tool()
def build_architectural_model(spec_json: str, output_3dm: str) -> dict:
    """Build a new editable, layered 3DM from a component JSON. Refuses overwrite."""
    return build_model(_workspace_file(spec_json, ".json"), _workspace_file(output_3dm, ".3dm"))


@mcp.tool()
def inspect_architectural_model(model_3dm: str) -> dict:
    """Read back model objects, names, layers, units and bounds."""
    return inspect_model(_workspace_file(model_3dm, ".3dm"))


@mcp.tool()
def render_architectural_view(model_3dm: str, output_png: str,
                              azimuth: float = 315, elevation: float = 28) -> dict:
    """Render an orthographic inspection PNG from actual saved 3DM mesh geometry."""
    return render_model(_workspace_file(model_3dm, ".3dm"),
                        _workspace_file(output_png, ".png"),
                        azimuth=azimuth, elevation=elevation)


def _workspace_dir(name: str) -> Path:
    root = Path(os.environ.get('SODAM_RHINO_WORKSPACE', 'workspace')).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not name or Path(name).name != name:
        raise ValueError('use a simple folder name inside the workspace')
    path = (root / name).resolve()
    if path.parent != root:
        raise ValueError('path escapes workspace')
    return path


@mcp.tool()
def render_blender_model(model_3dm: str, output_folder: str,
                         front_azimuth: float = 315, front_elevation: float = 28,
                         rear_azimuth: float = 135, rear_elevation: float = 28) -> dict:
    '''Render two adjustable Blender views and an editable blend file from the saved 3DM.'''
    return render_blender_views(
        _workspace_file(model_3dm, '.3dm'), _workspace_dir(output_folder),
        front_azimuth=front_azimuth, front_elevation=front_elevation,
        rear_azimuth=rear_azimuth, rear_elevation=rear_elevation,
    )


@mcp.tool()
def import_blender_scene(blend_file: str, output_3dm: str,
                         meters_per_blender_unit: float | None = None) -> dict:
    """Import a workspace Blender scene as named, layered 3DM meshes; never overwrite."""
    return import_blend(_workspace_file(blend_file, '.blend'),
                        _workspace_file(output_3dm, '.3dm'),
                        meters_per_blender_unit=meters_per_blender_unit)

def main() -> None:
    mcp.run(transport="stdio")




@mcp.tool()
def prepare_architectural_reference(reference_images: list[str], known_dimensions: dict[str, float],
                                    output_json: str, units: str = "meters") -> dict:
    """Record hashes and image sizes plus independently known positive dimensions."""
    output = _workspace_file(output_json, ".json")
    images: list[str | Path] = [_workspace_file(name, Path(name).suffix.lower()) for name in reference_images]
    return prepare_reference_case(images, known_dimensions, output, units)


@mcp.tool()
def draft_architectural_evidence(spec_json: str, reference_json: str, output_json: str) -> dict:
    """Add an explicit inferred marker to every geometric number for manual review."""
    return draft_evidence_spec(_workspace_file(spec_json, ".json"),
                               _workspace_file(reference_json, ".json"),
                               _workspace_file(output_json, ".json"))


@mcp.tool()
def audit_architectural_evidence(spec_json: str, reference_json: str) -> dict:
    """Check source hashes and per-number provenance; does not assert shape accuracy."""
    return validate_reference_case(_workspace_file(spec_json, ".json"),
                                   _workspace_file(reference_json, ".json"))


@mcp.tool()
def build_verified_architectural_model(spec_json: str, reference_json: str,
                                       output_3dm: str) -> dict:
    """Build only after all numeric geometry has evidence or a stated assumption."""
    return build_verified_model(_workspace_file(spec_json, ".json"),
                                _workspace_file(reference_json, ".json"),
                                _workspace_file(output_3dm, ".3dm"))

if __name__ == "__main__":
    main()
