"""Transfer evaluated Blender geometry to a Rhino-readable 3DM without Rhino."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

import rhino3dm as r3d

from .model import MAX_MESH_COORDINATE, inspect_model


def import_blend(blend_path: str | Path, output_path: str | Path,
                 blender_exe: str | Path | None = None,
                 meters_per_blender_unit: float | None = None) -> dict:
    source = Path(blend_path).resolve(strict=True)
    target = Path(output_path).resolve()
    if source.suffix.lower() != ".blend" or target.suffix.lower() != ".3dm":
        raise ValueError("input must be .blend and output must be .3dm")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite: {target}")
    if meters_per_blender_unit is not None and (isinstance(meters_per_blender_unit, bool) or not math.isfinite(meters_per_blender_unit) or meters_per_blender_unit <= 0):
        raise ValueError("meters_per_blender_unit must be a finite positive number")
    blender = Path(blender_exe or os.environ.get("SODAM_BLENDER_EXE", ""))
    if not blender.is_file():
        raise FileNotFoundError("set SODAM_BLENDER_EXE to an installed blender.exe")
    script = Path(__file__).parents[1] / "scripts" / "export_blend_mesh.py"
    with tempfile.TemporaryDirectory() as directory:
        payload_path = Path(directory) / "meshes.json"
        command = [str(blender), "-b", "--factory-startup", "--disable-autoexec", str(source),
                   "--python", str(script), "--", str(payload_path)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=120,
                                 check=False, stdin=subprocess.DEVNULL)
        if process.returncode != 0 or not payload_path.is_file():
            raise RuntimeError(f"Blender export failed: {process.stderr[-2000:]} {process.stdout[-2000:]}")
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    parts = payload.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Blender export contains no mesh parts")
    if meters_per_blender_unit is None:
        if payload.get("source_units") in ("METRIC", "IMPERIAL"):
            meters_per_blender_unit = float(payload["scene_scale_length"])
            unit_source = "Blender scene unit scale"
        else:
            meters_per_blender_unit = 1.0
            unit_source = "assumed 1 Blender unit = 1 meter (scene has no physical units)"
    else:
        unit_source = "explicit"
    if not math.isfinite(meters_per_blender_unit) or meters_per_blender_unit <= 0:
        raise ValueError("Blender scene scale must be a finite positive number")
    model = r3d.File3dm()
    model.Settings.ModelUnitSystem = r3d.UnitSystem.Meters
    layers = {}
    materials = {}
    for part in parts:
        name = part["name"]
        layer_name = part["layer"]
        color = part["color"]
        vertices = part["vertices"]
        faces = part["faces"]
        if not isinstance(name, str) or not name.strip() or not isinstance(layer_name, str) or not layer_name.strip():
            raise ValueError("Blender mesh part has no name or layer")
        if len(color) != 3 or any(type(channel) is not int or not 0 <= channel <= 255 for channel in color):
            raise ValueError("invalid Blender material color")
        if not vertices or not faces:
            raise ValueError("Blender mesh part is empty")
        if layer_name not in layers:
            layer = r3d.Layer()
            layer.Name = layer_name
            layers[layer_name] = model.Layers.Add(layer)
        material_key = (part["material"], *color)
        if material_key not in materials:
            material = r3d.Material()
            material.Name = str(part["material"])
            material.DiffuseColor = (*color, 255)
            materials[material_key] = model.Materials.Add(material)
        mesh = r3d.Mesh()
        scaled_vertices = []
        for vertex in vertices:
            if len(vertex) != 3 or any(not isinstance(value, (int, float)) or isinstance(value, bool)
                                       or not math.isfinite(value) for value in vertex):
                raise ValueError("Blender mesh has non-finite vertex")
            scaled = [float(value) * meters_per_blender_unit for value in vertex]
            if any(not math.isfinite(value) or abs(value) > MAX_MESH_COORDINATE for value in scaled):
                raise ValueError("scaled Blender vertex must be finite")
            scaled_vertices.append(scaled)
            mesh.Vertices.Add(*scaled)
        stored_vertices = [(float(v.X), float(v.Y), float(v.Z)) for v in mesh.Vertices]
        if any(max(vertex[axis] for vertex in scaled_vertices) > min(vertex[axis] for vertex in scaled_vertices)
               and max(vertex[axis] for vertex in stored_vertices) == min(vertex[axis] for vertex in stored_vertices)
               for axis in range(3)):
            raise ValueError("Blender mesh dimension collapses at 3DM vertex precision")
        for face in faces:
            if len(face) != 3 or any(type(index) is not int or not 0 <= index < len(vertices) for index in face):
                raise ValueError("Blender mesh has invalid triangle")
            mesh.Faces.AddFace(*face)
        mesh.Normals.ComputeNormals()
        attributes = r3d.ObjectAttributes()
        attributes.Name = name
        attributes.LayerIndex = layers[layer_name]
        attributes.ObjectColor = (*color, 255)
        attributes.ColorSource = r3d.ObjectColorSource.ColorFromObject
        attributes.MaterialIndex = materials[material_key]
        attributes.MaterialSource = r3d.ObjectMaterialSource.MaterialFromObject
        attributes.SetUserString("color_rgb", ",".join(str(channel) for channel in color))
        attributes.SetUserString("source_blend_object", name)
        attributes.SetUserString("source_blend_material", str(part["material"]))
        attributes.SetUserString("meters_per_blender_unit", str(meters_per_blender_unit))
        model.Objects.AddMesh(mesh, attributes)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as directory:
        staged = Path(directory) / "imported.3dm"
        if not model.Write(str(staged), 8):
            raise OSError("rhino3dm failed to write the imported model")
        summary = inspect_model(staged)
        if summary["objects"] != len(parts):
            raise OSError("saved 3DM object count differs from Blender export")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"refusing to overwrite: {target}")
        staged.rename(target)
    summary["path"] = str(target)
    return {**summary, "source_blend": str(source), "mesh_parts": len(parts),
            "meters_per_blender_unit": meters_per_blender_unit, "unit_source": unit_source,
            "scene_units": payload.get("source_units"), "scene_scale_length": payload.get("scene_scale_length")}
