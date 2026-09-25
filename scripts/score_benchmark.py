"""Compare saved 3DM geometry with a separately authored Blender reference."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import rhino3dm as r3d


def mesh_bounds(path: Path) -> dict[str, tuple[list[float], list[float]]]:
    archive = r3d.File3dm.Read(str(path))
    if archive is None:
        raise ValueError("unreadable 3DM")
    if archive.Settings.ModelUnitSystem != r3d.UnitSystem.Meters:
        raise ValueError("benchmark scorer requires a 3DM in meters")
    found = {}
    for obj in archive.Objects:
        if not isinstance(obj.Geometry, r3d.Mesh):
            raise TypeError("benchmark scorer requires mesh objects")
        name = obj.Attributes.Name
        if not name or name in found:
            raise ValueError(f"missing or duplicate mesh name: {name}")
        vertices = [(float(v.X), float(v.Y), float(v.Z)) for v in obj.Geometry.Vertices]
        if not vertices or any(not math.isfinite(value) for vertex in vertices for value in vertex):
            raise ValueError(f"mesh needs finite vertices: {name}")
        found[name] = (
            [min(v[i] for v in vertices) for i in range(3)],
            [max(v[i] for v in vertices) for i in range(3)],
        )
    return found


def gable_rise_from_saved_mesh(path: Path, object_name: str) -> float:
    """Measure ridge rise above the top eave, excluding vertical roof thickness."""
    archive = r3d.File3dm.Read(str(path))
    if archive is None:
        raise ValueError("unreadable 3DM")
    matches = [obj.Geometry for obj in archive.Objects
               if obj.Attributes.Name == object_name and isinstance(obj.Geometry, r3d.Mesh)]
    if len(matches) != 1:
        raise ValueError(f"expected one roof mesh named {object_name}")
    vertices = [(float(v.Y), float(v.Z)) for v in matches[0].Vertices]
    if not vertices or any(not math.isfinite(value) for vertex in vertices for value in vertex):
        raise ValueError("roof mesh needs finite vertices")
    eave_y = min(y for y, _ in vertices)
    top_eave = max(z for y, z in vertices if y == eave_y)
    rise = max(z for _, z in vertices) - top_eave
    if rise <= 0:
        raise ValueError("roof ridge must rise above its eave")
    return rise


def measure_saved_model(path: Path) -> dict[str, float]:
    boxes = mesh_bounds(path)
    names = {
        "slab", "front_wall:left", "front_wall:right", "rear_wall:left",
        "roof", "front_door", "rear_glazing"
    }
    missing = names - boxes.keys()
    if missing:
        raise ValueError(f"3DM missing objects: {sorted(missing)}")
    slab_min, slab_max = boxes["slab"]
    front_left_min, front_left_max = boxes["front_wall:left"]
    roof_min, _ = boxes["roof"]
    door_min, door_max = boxes["front_door"]
    window_min, window_max = boxes["rear_glazing"]
    return {
        "width": slab_max[0] - slab_min[0],
        "depth": slab_max[1] - slab_min[1],
        "slab_thickness": slab_max[2] - slab_min[2],
        "wall_height": front_left_max[2] - slab_max[2],
        "wall_thickness": front_left_max[1] - front_left_min[1],
        "roof_height": gable_rise_from_saved_mesh(path, "roof"),
        "overhang": slab_min[0] - roof_min[0],
        "door_left": door_min[0] - slab_min[0],
        "door_width": door_max[0] - door_min[0],
        "door_height": door_max[2] - door_min[2],
        "window_left": window_min[0] - slab_min[0],
        "window_width": window_max[0] - window_min[0],
        "window_bottom": window_min[2] - slab_max[2],
        "window_height": window_max[2] - window_min[2],
    }


def score(truth: dict, model: Path) -> dict:
    actual = measure_saved_model(model)
    visible = set(actual) - {"wall_thickness"}
    results = {}
    for name, measured_value in actual.items():
        expected = float(truth[name])
        error = round(abs(measured_value - expected), 4)
        is_visible = name in visible
        tolerance = 0.01 if name == "width" else 0.2
        results[name] = {
            "reference": expected,
            "saved_3dm_measurement": round(measured_value, 4),
            "absolute_error_m": error,
            "evidence": "given_or_visible" if is_visible else "inferred_hidden",
            "within_gate": error <= tolerance if is_visible else None,
        }
    scored = [item for item in results.values() if item["within_gate"] is not None]
    return {
        "reference_authoring": "Independent Blender script; same evaluating agent",
        "saved_3dm_mesh_objects": len(mesh_bounds(model)),
        "observed_parameters": len(scored),
        "observed_parameters_passing": sum(item["within_gate"] for item in scored),
        "all_observed_within_gate": all(item["within_gate"] for item in scored),
        "parameters": results,
        "limitation": "One synthetic orthographic case; no real-photo, Rhino UI, or third-party reader validation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    args = parser.parse_args()
    root = args.case_dir.resolve(strict=True)
    target = root / "score_geometry.json"
    if target.exists():
        raise FileExistsError(target)
    truth = json.loads((root / "reference_truth.json").read_text(encoding="utf-8"))
    result = score(truth, root / "reconstructed.3dm")
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"observed_parameters_passing":result["observed_parameters_passing"],
                      "observed_parameters":result["observed_parameters"],
                      "saved_3dm_mesh_objects":result["saved_3dm_mesh_objects"]}))


if __name__ == "__main__":
    main()
