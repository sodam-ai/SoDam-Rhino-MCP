"""Optional Blender rendering from the geometry saved in a 3DM file."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

import rhino3dm as r3d


def export_scene(model_path: str | Path) -> dict:
    model = r3d.File3dm.Read(str(model_path))
    if model is None:
        raise ValueError("not a readable 3DM file")
    objects = []
    for obj in model.Objects:
        mesh = obj.Geometry
        if not isinstance(mesh, r3d.Mesh):
            continue
        rgb = obj.Attributes.ObjectColor
        vertices = [[float(v.X), float(v.Y), float(v.Z)] for v in mesh.Vertices]
        if any(not math.isfinite(coordinate) for vertex in vertices for coordinate in vertex):
            raise ValueError("3DM contains non-finite mesh vertices")
        objects.append({
            "name": obj.Attributes.Name,
            "layer": model.Layers[obj.Attributes.LayerIndex].Name,
            "vertices": vertices,
            "faces": [list(face) for face in mesh.Faces],
            "color": [int(rgb[0]), int(rgb[1]), int(rgb[2])],
        })
    if not objects:
        raise ValueError("3DM has no mesh objects")
    return {"objects": objects}


def render_blender_views(model_path: str | Path, output_dir: str | Path,
                         blender_exe: str | Path | None = None, *,
                         front_azimuth: float = 315, front_elevation: float = 28,
                         rear_azimuth: float = 135, rear_elevation: float = 28) -> dict:
    camera_values = (front_azimuth, front_elevation, rear_azimuth, rear_elevation)
    try:
        valid = all(not isinstance(value, bool) and isinstance(value, (int, float)) and
                    math.isfinite(value) for value in camera_values)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("camera angles must be finite numbers")
    if not -90 <= front_elevation <= 90 or not -90 <= rear_elevation <= 90:
        raise ValueError("camera elevation must be within -90..90 degrees")

    def direction(azimuth: float, elevation: float) -> tuple[float, float, float]:
        azimuth_radians = math.radians(azimuth % 360)
        elevation_radians = math.radians(elevation)
        horizontal = math.cos(elevation_radians)
        return (horizontal * math.cos(azimuth_radians),
                horizontal * math.sin(azimuth_radians),
                math.sin(elevation_radians))

    front_direction = direction(front_azimuth, front_elevation)
    rear_direction = direction(rear_azimuth, rear_elevation)
    dot = sum(a * b for a, b in zip(front_direction, rear_direction))
    separation = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
    if separation < 10:
        raise ValueError("front and rear cameras must differ by at least 10 degrees")
    cameras = {
        "front": {"azimuth": front_azimuth, "elevation": front_elevation},
        "rear": {"azimuth": rear_azimuth, "elevation": rear_elevation},
    }
    source = Path(model_path).resolve(strict=True)
    destination = Path(output_dir).resolve()
    if source.suffix.lower() != ".3dm":
        raise ValueError("Blender renderer needs a 3DM model")
    outputs = [destination / name for name in ("front.png", "rear.png", "scene.blend")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("front.png, rear.png or scene.blend already exists")
    blender = Path(blender_exe or os.environ.get("SODAM_BLENDER_EXE", ""))
    if not blender.is_file():
        raise FileNotFoundError("set SODAM_BLENDER_EXE to an installed blender.exe")
    scene = export_scene(source)
    scene["cameras"] = cameras
    script = Path(__file__).parents[1] / "scripts" / "blender_scene.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        stage = Path(directory)
        payload = stage / "scene.json"
        payload.write_text(json.dumps(scene), encoding="utf-8")
        command = [str(blender), "-b", "--factory-startup", "--python", str(script),
                   "--", str(payload), str(stage)]
        process = subprocess.run(command, capture_output=True, text=True,
                                 timeout=90, check=False, stdin=subprocess.DEVNULL)
        staged = [stage / path.name for path in outputs]
        if process.returncode != 0 or any(not path.is_file() or path.stat().st_size == 0 for path in staged):
            raise RuntimeError(f"Blender render failed: {process.stderr[-2000:]} {process.stdout[-2000:]}")
        destination.mkdir(parents=True, exist_ok=True)
        if any(path.exists() for path in outputs):
            raise FileExistsError("front.png, rear.png or scene.blend already exists")
        moved = []
        try:
            for source_path, target_path in zip(staged, outputs):
                source_path.rename(target_path)
                moved.append(target_path)
        except OSError:
            for path in moved:
                path.unlink(missing_ok=True)
            raise
    return {"source": str(source), "front": str(outputs[0]), "rear": str(outputs[1]),
            "blend": str(outputs[2]), "objects": len(scene["objects"]),
            "cameras": cameras}
