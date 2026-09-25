"""Draw inspection views from a 3DM mesh with per-pixel depth testing."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rhino3dm as r3d
from PIL import Image

from .model import _finite


def _dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _draw_triangle(image, zbuffer, vertices, color):
    """Rasterize one projected triangle; greater camera depth is nearer."""
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = vertices
    denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denominator) < 1e-9:
        return
    left = max(0, math.floor(min(x0, x1, x2)))
    right = min(image.shape[1] - 1, math.ceil(max(x0, x1, x2)))
    top = max(0, math.floor(min(y0, y1, y2)))
    bottom = min(image.shape[0] - 1, math.ceil(max(y0, y1, y2)))
    if left > right or top > bottom:
        return
    yy, xx = np.mgrid[top:bottom + 1, left:right + 1]
    xx = xx + 0.5
    yy = yy + 0.5
    a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / denominator
    b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / denominator
    c = 1.0 - a - b
    depth = a * z0 + b * z1 + c * z2
    current = zbuffer[top:bottom + 1, left:right + 1]
    visible = (a >= -1e-8) & (b >= -1e-8) & (c >= -1e-8) & (depth > current + 1e-8)
    current[visible] = depth[visible]
    image[top:bottom + 1, left:right + 1][visible] = color


def render_model(path: str | Path, output_path: str | Path, *, azimuth: float = 315,
                 elevation: float = 28, width: int = 1200, height: int = 800) -> dict:
    source = Path(path).resolve(strict=True)
    target = Path(output_path).resolve()
    if source.suffix.lower() != ".3dm" or target.suffix.lower() != ".png":
        raise ValueError("render needs .3dm input and .png output")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite: {target}")
    if isinstance(width, bool) or isinstance(height, bool) or not isinstance(width, int) or not isinstance(height, int) or not (320 <= width <= 4096 and 240 <= height <= 4096):
        raise ValueError("render dimensions out of range")
    model = r3d.File3dm.Read(str(source))
    if model is None:
        raise ValueError("not a readable 3DM file")
    azimuth, elevation = _finite([azimuth, elevation], "camera angles")
    if not -90 <= elevation <= 90:
        raise ValueError("elevation must be within -90..90 degrees")
    az, el = math.radians(azimuth), math.radians(elevation)
    right = (-math.sin(az), math.cos(az), 0.0)
    up = (-math.sin(el) * math.cos(az), -math.sin(el) * math.sin(az), math.cos(el))
    toward_camera = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    light = (0.3, -0.4, 0.87)
    faces = []
    all_points = []
    for obj in model.Objects:
        mesh = obj.Geometry
        if not isinstance(mesh, r3d.Mesh):
            continue
        rgb_text = obj.Attributes.GetUserString("color_rgb")
        try:
            rgb = tuple(int(x) for x in rgb_text.split(",")) if rgb_text else tuple(int(x) for x in obj.Attributes.ObjectColor[:3])
            if len(rgb) != 3 or any(x < 0 or x > 255 for x in rgb):
                raise ValueError
        except ValueError:
            rgb = tuple(int(x) for x in obj.Attributes.ObjectColor[:3])
        vertices = [(float(v.X), float(v.Y), float(v.Z)) for v in mesh.Vertices]
        if any(not math.isfinite(coordinate) for vertex in vertices for coordinate in vertex):
            raise ValueError("3DM contains non-finite mesh vertices")
        all_points.extend(vertices)
        for face in mesh.Faces:
            indices = list(face)
            if len(indices) == 4 and indices[2] == indices[3]:
                indices.pop()
            polygon = [vertices[i] for i in indices]
            if len(polygon) < 3:
                continue
            normal = _cross(_sub(polygon[1], polygon[0]), _sub(polygon[2], polygon[0]))
            magnitude = math.sqrt(_dot(normal, normal))
            shade = 0.75 if magnitude == 0 else 0.60 + 0.38 * abs(_dot(normal, light)) / magnitude
            color = tuple(min(255, round(channel * shade)) for channel in rgb)
            faces.append((polygon, color))
    if not all_points:
        raise ValueError("3DM has no mesh vertices to render")
    projected = [(_dot(v, right), _dot(v, up)) for v in all_points]
    min_x, max_x = min(v[0] for v in projected), max(v[0] for v in projected)
    min_y, max_y = min(v[1] for v in projected), max(v[1] for v in projected)
    scale = min((width * 0.82) / max(max_x - min_x, 1e-9),
                (height * 0.82) / max(max_y - min_y, 1e-9))
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    image = np.full((height, width, 3), (244, 246, 248), dtype=np.uint8)
    zbuffer = np.full((height, width), -np.inf, dtype=np.float64)
    for polygon, color in faces:
        vertices = [(((_dot(v, right) - center_x) * scale) + width / 2,
                     height / 2 - ((_dot(v, up) - center_y) * scale),
                     _dot(v, toward_camera)) for v in polygon]
        for i in range(1, len(vertices) - 1):
            _draw_triangle(image, zbuffer, (vertices[0], vertices[i], vertices[i + 1]), color)
    target.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(target)
    return {"path": str(target), "source": str(source), "faces": len(faces),
            "camera": {"azimuth": azimuth, "elevation": elevation},
            "kind": "orthographic mesh inspection view"}
