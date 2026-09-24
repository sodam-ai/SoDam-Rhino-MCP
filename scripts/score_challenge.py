"""Score the harder single-view fixture from saved 3DM mesh vertices.

The reconstruction JSON is deliberately not read: changing it after a build must
not change the score of the delivered model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import rhino3dm as r3d

from scripts.score_benchmark import gable_rise_from_saved_mesh, mesh_bounds


def measure_saved_model(path: Path) -> dict[str, float]:
    archive = r3d.File3dm.Read(str(path))
    if archive is None:
        raise ValueError("unreadable 3DM")
    if archive.Settings.ModelUnitSystem != r3d.UnitSystem.Meters:
        raise ValueError("challenge scorer requires a 3DM in meters")
    objects = list(archive.Objects)
    names = [item.Attributes.Name for item in objects]
    if len(names) != len(set(names)):
        raise ValueError("3DM has duplicate object names")
    if any(not isinstance(item.Geometry, r3d.Mesh) for item in objects):
        raise ValueError("challenge scorer requires mesh objects")
    boxes = mesh_bounds(path)
    required = {"main_volume", "main_roof", "front_wing", "front_door"}
    missing = required - boxes.keys()
    if missing:
        raise ValueError(f"3DM missing objects: {sorted(missing)}")
    main_min, main_max = boxes["main_volume"]
    wing_min, wing_max = boxes["front_wing"]
    door_min, door_max = boxes["front_door"]
    return {
        "main_width": main_max[0] - main_min[0],
        "main_depth": main_max[1] - main_min[1],
        "main_wall_height": main_max[2] - main_min[2],
        "roof_rise": gable_rise_from_saved_mesh(path, "main_roof"),
        "wing_x": wing_min[0] - main_min[0],
        "wing_width": wing_max[0] - wing_min[0],
        "wing_projection": main_min[1] - wing_min[1],
        "wing_height": wing_max[2] - wing_min[2],
        "door_left": door_min[0] - main_min[0],
        "door_width": door_max[0] - door_min[0],
    }


def score(truth: dict, model: Path) -> dict:
    if truth.get("units") != "meters":
        raise ValueError("challenge truth must use meters")
    actual = measure_saved_model(model)
    expected = {
        "main_width": (truth["width"], "given"),
        "main_depth": (truth["depth"], "inferred"),
        "main_wall_height": (truth["wall_height"], "inferred"),
        "roof_rise": (truth["roof_height"], "inferred"),
        "wing_x": (truth["wing"]["x"], "inferred"),
        "wing_width": (truth["wing"]["width"], "inferred"),
        "wing_projection": (truth["wing"]["projection"], "inferred"),
        "wing_height": (truth["wing"]["height"], "inferred"),
        "door_left": (truth["door_left"], "inferred"),
        "door_width": (truth["door_width"], "inferred"),
    }
    rows = {
        name: {
            "saved_3dm_measurement_m": round(actual[name], 4),
            "truth_m": float(reference),
            "absolute_error_m": round(abs(actual[name] - float(reference)), 4),
            "evidence": evidence,
        }
        for name, (reference, evidence) in expected.items()
    }
    errors = [row["absolute_error_m"] for row in rows.values()
              if row["evidence"] == "inferred"]
    return {
        "mode": truth.get("reference_mode"),
        "measurement_source": "saved_3dm_mesh_vertices",
        "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "known_width_error_m": rows["main_width"]["absolute_error_m"],
        "inferred_mean_absolute_error_m": round(sum(errors) / len(errors), 4),
        "inferred_max_absolute_error_m": max(errors),
        "comparison": rows,
        "limitation": "One synthetic perspective; no real-photo or independent 3DM-reader proof.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    args = parser.parse_args()
    folder = args.case_dir.resolve(strict=True)
    target = folder / "score_challenge_geometry.json"
    if target.exists():
        raise FileExistsError(target)
    truth = json.loads((folder / "reference_truth.json").read_text(encoding="utf-8"))
    result = score(truth, folder / "reconstructed.3dm")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "measurement_source": result["measurement_source"],
        "known_width_error_m": result["known_width_error_m"],
        "inferred_mean_absolute_error_m": result["inferred_mean_absolute_error_m"],
        "inferred_max_absolute_error_m": result["inferred_max_absolute_error_m"],
    }))


if __name__ == "__main__":
    main()
