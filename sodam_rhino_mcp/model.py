"""Build semantic architectural mesh components in a native 3DM archive."""

from __future__ import annotations

import json
import math
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import rhino3dm as r3d

MAX_MESH_COORDINATE = 3.4028234663852886e38  # rhino3dm Mesh.Vertices use float32

UNIT_SYSTEMS = {
    "meters": r3d.UnitSystem.Meters,
    "millimeters": r3d.UnitSystem.Millimeters,
    "centimeters": r3d.UnitSystem.Centimeters,
    "feet": r3d.UnitSystem.Feet,
}


def _finite(values: list[object], label: str) -> list[float]:
    if not isinstance(values, list) or not values or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) for value in values
    ):
        raise ValueError(f"{label} must contain finite numbers")
    numbers = []
    for value in values:
        try:
            number = float(cast(float, value))
        except OverflowError as exc:
            raise ValueError(f"{label} must contain finite numbers") from exc
        if not math.isfinite(number):
            raise ValueError(f"{label} must contain finite numbers")
        numbers.append(number)
    return numbers


def _vec(value: object, label: str, length: int = 3) -> list[float]:
    values = _finite(value, label)  # type: ignore[arg-type]
    if len(values) != length:
        raise ValueError(f"{label} needs {length} numbers")
    return values


def _box_mesh(origin: list[float], size: list[float]) -> r3d.Mesh:
    x, y, z = origin
    dx, dy, dz = size
    if min(size) <= 0:
        raise ValueError("box size must be positive")
    corners = [
        (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
        (x, y, z + dz), (x + dx, y, z + dz),
        (x + dx, y + dy, z + dz), (x, y + dy, z + dz),
    ]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _mesh(corners, faces)


def _mesh(vertices: list[tuple[float, float, float]], faces: Sequence[tuple[int, ...]]) -> r3d.Mesh:
    mesh = r3d.Mesh()
    for vertex in vertices:
        if len(vertex) != 3 or any(not math.isfinite(value) or abs(value) > MAX_MESH_COORDINATE for value in vertex):
            raise ValueError("computed mesh vertex must be finite")
        mesh.Vertices.Add(*vertex)
    stored_vertices = [(float(v.X), float(v.Y), float(v.Z)) for v in mesh.Vertices]
    if any(max(vertex[axis] for vertex in stored_vertices) == min(vertex[axis] for vertex in stored_vertices) for axis in range(3)):
        raise ValueError("mesh dimension collapses at 3DM vertex precision")
    for face in faces:
        if len(face) == 3 or len(face) == 4:
            mesh.Faces.AddFace(*face)
        else:
            raise ValueError("faces need 3 or 4 indices")
    mesh.Normals.ComputeNormals()
    return mesh


def _gable_roof(origin: list[float], size: list[float], ridge_height: float) -> r3d.Mesh:
    x, y, z = origin
    dx, dy, thickness = size
    if dx <= 0 or dy <= 0 or thickness <= 0 or ridge_height <= 0:
        raise ValueError("roof dimensions and ridge_height must be positive")
    top = [
        (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
        (x, y + dy / 2, z + ridge_height),
        (x + dx, y + dy / 2, z + ridge_height),
    ]
    vertices = top + [(vx, vy, z - thickness) for vx, vy, _ in top[:4]]
    faces = [
        (0, 1, 5, 4), (3, 4, 5, 2),  # top slopes
        (9, 8, 7, 6),  # flat underside preserves the filled gable mass
        (6, 7, 1, 0), (3, 2, 8, 9),  # eave edges
        (0, 4, 3), (6, 0, 3, 9),  # left gable
        (1, 2, 5), (1, 7, 8, 2),  # right gable
    ]
    mesh = _mesh(vertices, faces)
    if any(mesh.Vertices[i].Z == mesh.Vertices[i + 6].Z for i in range(4)):
        raise ValueError("roof thickness collapses at 3DM vertex precision")
    return mesh



def _cylinder(origin: list[float], size: list[float], segments: int) -> r3d.Mesh:
    """Closed vertical circular column; origin is its lower bounding-box corner."""
    x, y, z = origin
    dx, dy, height = size
    if not math.isclose(dx, dy, rel_tol=1e-9, abs_tol=0.0):
        raise ValueError("cylinder width and depth must match")
    if type(segments) is not int or not 12 <= segments <= 256:
        raise ValueError("cylinder segments must be an integer in 12..256")
    cx, cy, radius = x + dx / 2, y + dy / 2, dx / 2
    ring = [(cx + radius * math.cos(2 * math.pi * i / segments),
             cy + radius * math.sin(2 * math.pi * i / segments))
            for i in range(segments)]
    vertices = [(vx, vy, z) for vx, vy in ring]
    vertices += [(vx, vy, z + height) for vx, vy in ring]
    vertices += [(cx, cy, z), (cx, cy, z + height)]
    bottom_center, top_center = 2 * segments, 2 * segments + 1
    faces: list[tuple[int, ...]] = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append((i, nxt, segments + nxt, segments + i))
        faces.append((bottom_center, nxt, i))
        faces.append((top_center, segments + i, segments + nxt))
    return _mesh(vertices, faces)


def _parts(item: dict) -> list[tuple[str, r3d.Mesh]]:
    kind = item.get("kind")
    origin = _vec(item.get("origin"), "origin")
    size = _vec(item.get("size"), "size")
    if min(size) <= 0:
        raise ValueError("component size must be positive")
    if kind == "box":
        return [(item["name"], _box_mesh(origin, size))]
    if kind == "cylinder":
        return [(item["name"], _cylinder(origin, size, item.get("segments", 48)))]
    if kind == "gable_roof":
        ridge_height = _finite([item.get("ridge_height")], "ridge_height")[0]
        if ridge_height <= 0:
            raise ValueError("ridge_height must be a finite positive number")
        return [(item["name"], _gable_roof(origin, size, ridge_height))]
    if kind != "wall_opening":
        raise ValueError(f"unsupported kind: {kind}")
    axis = item.get("axis")
    if axis not in ("x", "y"):
        raise ValueError("wall_opening axis must be x or y")
    opening = item.get("opening")
    if not isinstance(opening, dict):
        raise TypeError("wall_opening needs opening")
    start, bottom = _vec(opening.get("start_bottom"), "opening.start_bottom", 2)
    width, height = _vec(opening.get("size"), "opening.size", 2)
    horizontal = size[0 if axis == "x" else 1]
    if min(size) <= 0 or min(width, height) <= 0 or start < 0 or bottom < 0:
        raise ValueError("wall/opening dimensions must be positive")
    if start + width >= horizontal or bottom + height >= size[2]:
        raise ValueError("opening must be inside the wall")
    spans = [
        (0, start, 0, size[2], "left"),
        (start + width, horizontal - start - width, 0, size[2], "right"),
        (start, width, 0, bottom, "sill"),
        (start, width, bottom + height, size[2] - bottom - height, "header"),
    ]
    result = []
    for offset, extent, z_offset, z_extent, suffix in spans:
        if extent <= 0 or z_extent <= 0:
            continue
        local_origin = origin.copy()
        local_size = size.copy()
        index = 0 if axis == "x" else 1
        local_origin[index] += offset
        local_origin[2] += z_offset
        local_size[index] = extent
        local_size[2] = z_extent
        result.append((f"{item['name']}:{suffix}", _box_mesh(local_origin, local_size)))
    return result


def validate_spec(spec: dict) -> None:
    if not isinstance(spec, dict) or spec.get("units") not in UNIT_SYSTEMS:
        raise ValueError(f"units must be one of {', '.join(UNIT_SYSTEMS)}")
    items = spec.get("components")
    if not isinstance(items, list) or not items:
        raise ValueError("components must be a nonempty list")
    names = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
            raise ValueError("every component needs a name")
        if item["name"] in names:
            raise ValueError(f"duplicate component name: {item['name']}")
        names.add(item["name"])
        if not isinstance(item.get("layer"), str) or not item["layer"].strip():
            raise ValueError(f"{item['name']} needs a layer")
        color = _vec(item.get("color", [180, 180, 180]), "color")
        if any(v < 0 or v > 255 or not v.is_integer() for v in color):
            raise ValueError("color channels must be integers in 0..255")
        if item.get("evidence", "inferred") not in ("given", "measured", "inferred"):
            raise ValueError("evidence must be given, measured or inferred")
        _parts(item)


def build_model(spec_path: str | Path, output_path: str | Path) -> dict:
    source = Path(spec_path).resolve(strict=True)
    target = Path(output_path).resolve()
    if source.suffix.lower() != ".json" or target.suffix.lower() != ".3dm":
        raise ValueError("input must be JSON and output must be .3dm")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite: {target}")
    spec = json.loads(source.read_text(encoding="utf-8"))
    validate_spec(spec)
    model = r3d.File3dm()
    model.Settings.ModelUnitSystem = UNIT_SYSTEMS[spec["units"]]
    layer_ids: dict[str, int] = {}
    material_ids: dict[tuple[int, int, int], int] = {}
    for item in spec["components"]:
        layer_name = item["layer"]
        if layer_name not in layer_ids:
            layer = r3d.Layer()
            layer.Name = layer_name
            layer_ids[layer_name] = model.Layers.Add(layer)
        channels = item.get("color", [180, 180, 180])
        color = (int(channels[0]), int(channels[1]), int(channels[2]))
        if color not in material_ids:
            material = r3d.Material()
            material.Name = f"RGB_{color[0]}_{color[1]}_{color[2]}"
            material.DiffuseColor = (*color, 255)
            material_ids[color] = model.Materials.Add(material)
        for name, geometry in _parts(item):
            attributes = r3d.ObjectAttributes()
            attributes.Name = name
            attributes.LayerIndex = layer_ids[layer_name]
            attributes.ObjectColor = (*color, 255)
            attributes.ColorSource = r3d.ObjectColorSource.ColorFromObject
            attributes.MaterialIndex = material_ids[color]
            attributes.MaterialSource = r3d.ObjectMaterialSource.MaterialFromObject
            attributes.SetUserString("source_component", item["name"])
            attributes.SetUserString("evidence", item.get("evidence", "inferred"))
            attributes.SetUserString("color_rgb", ",".join(str(x) for x in color))
            attributes.SetUserString("control_json", json.dumps(item, ensure_ascii=False))
            model.Objects.AddMesh(geometry, attributes)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as directory:
        staged = Path(directory) / "model.3dm"
        if not model.Write(str(staged), 8):
            raise OSError("rhino3dm failed to write the model")
        summary = inspect_model(staged)
        if summary["objects"] == 0:
            raise OSError("written model has no geometry")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"refusing to overwrite: {target}")
        staged.rename(target)
    summary["path"] = str(target)
    return summary


def inspect_model(path: str | Path) -> dict:
    source = Path(path).resolve(strict=True)
    model = r3d.File3dm.Read(str(source))
    if model is None:
        raise ValueError("not a readable 3DM file")
    objects = list(model.Objects)
    bounds = []
    names = []
    for obj in objects:
        names.append(obj.Attributes.Name)
        if isinstance(obj.Geometry, r3d.Mesh):
            for vertex in obj.Geometry.Vertices:
                point = (float(vertex.X), float(vertex.Y), float(vertex.Z))
                if any(not math.isfinite(value) for value in point):
                    raise ValueError("3DM contains non-finite mesh vertices")
                bounds.append(point)
    bbox = None
    if bounds:
        bbox = {"min": [min(v[i] for v in bounds) for i in range(3)],
                "max": [max(v[i] for v in bounds) for i in range(3)]}
    return {"path": str(source), "units": str(model.Settings.ModelUnitSystem),
            "objects": len(objects), "layers": [layer.Name for layer in model.Layers],
            "names": names, "bbox": bbox}
