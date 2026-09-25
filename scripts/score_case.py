"""Score independently recorded dimensions against a frozen saved 3DM.

This checks selected mesh measurements, not photographic or Rhino edit fidelity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
import warnings
from pathlib import Path

from PIL import Image

from scripts.score_benchmark import mesh_bounds

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_AXES = {"x": 0, "y": 1, "z": 2}
_EDGES = {"min": 0, "max": 1}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a finite number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _case_file(folder: Path, name: object, suffixes: set[str]) -> Path:
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise TypeError("case files must use simple filenames")
    candidate = folder / name
    if candidate.is_symlink() or candidate.suffix.lower() not in suffixes:
        raise ValueError(f"invalid case file: {name}")
    resolved = candidate.resolve(strict=True)
    if resolved.parent != folder or not resolved.is_file():
        raise ValueError(f"case file escapes folder: {name}")
    return resolved


def _checked_hash(path: Path, expected: object) -> str:
    if not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
        raise ValueError(f"invalid SHA-256 for {path.name}")
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    actual = hasher.hexdigest()
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return actual


def _measurement(row: dict, boxes: dict, names: set[str]) -> dict:
    name = row.get("name")
    if not isinstance(name, str) or not name.strip() or name in names:
        raise ValueError("measurement names must be unique and nonempty")
    names.add(name)
    obj = row.get("object")
    if not isinstance(obj, str) or obj not in boxes:
        raise ValueError(f"unknown model object: {obj}")
    axis = row.get("axis")
    if not isinstance(axis, str) or axis not in _AXES:
        raise ValueError(f"invalid axis for {name}")
    quantity = row.get("quantity")
    if quantity not in ("extent", "min", "max"):
        raise ValueError(f"invalid quantity for {name}")
    axis_index = _AXES[axis]
    low, high = boxes[obj]
    measured = high[axis_index] - low[axis_index] if quantity == "extent" else (
        low[axis_index] if quantity == "min" else high[axis_index]
    )
    relative_to = row.get("relative_to")
    if relative_to is not None:
        if quantity == "extent" or not isinstance(relative_to, str) or relative_to not in boxes:
            raise ValueError(f"invalid relative object for {name}")
        relative_edge = row.get("relative_edge")
        if relative_edge not in _EDGES:
            raise ValueError(f"invalid relative edge for {name}")
        measured -= boxes[relative_to][_EDGES[relative_edge]][axis_index]
    elif "relative_edge" in row:
        raise ValueError(f"relative edge needs a relative object for {name}")
    truth = _finite_number(row.get("truth_m"), f"{name}.truth_m")
    tolerance = _finite_number(row.get("tolerance_m"), f"{name}.tolerance_m")
    if tolerance < 0 or (quantity == "extent" and truth <= 0):
        raise ValueError(f"invalid truth or tolerance for {name}")
    visibility = row.get("visibility")
    if visibility not in ("given", "visible", "hidden"):
        raise ValueError(f"invalid visibility for {name}")
    truth_source = row.get("truth_source")
    if not isinstance(truth_source, str) or not truth_source.strip():
        raise ValueError(f"independent truth source required for {name}")
    error = abs(measured - truth)
    return {
        "name": name, "object": obj, "axis": axis, "quantity": quantity,
        "relative_to": relative_to, "relative_edge": row.get("relative_edge"),
        "visibility": visibility,
        "truth_source": truth_source, "truth_m": truth,
        "saved_3dm_m": round(measured, 6), "absolute_error_m": round(error, 6),
        "tolerance_m": tolerance, "within_tolerance": error <= tolerance + 1e-9,
    }


def score_case(manifest_path: Path) -> dict:
    manifest_path = manifest_path.resolve(strict=True)
    folder = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("case manifest schema_version must be 1")
    if manifest.get("case_type") not in ("real", "synthetic"):
        raise ValueError("case_type must be real or synthetic")
    model_info = manifest.get("model")
    if not isinstance(model_info, dict):
        raise TypeError("model file and SHA-256 are required")
    model = _case_file(folder, model_info.get("file"), {".3dm"})
    model_hash = _checked_hash(model, model_info.get("sha256"))
    references = manifest.get("references")
    if not isinstance(references, list) or not references:
        raise ValueError("at least one reference image is required")
    seen_files: set[str] = set()
    for item in references:
        if not isinstance(item, dict):
            raise TypeError("reference entry must be an object")
        photo = _case_file(folder, item.get("file"), {".png", ".jpg", ".jpeg"})
        if photo.name in seen_files:
            raise ValueError("duplicate reference image")
        seen_files.add(photo.name)
        _checked_hash(photo, item.get("sha256"))
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(photo, formats=("PNG", "JPEG")) as image:
                    image.verify()
                with Image.open(photo, formats=("PNG", "JPEG")) as image:
                    image.load()
        except (OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            raise ValueError(f"unreadable reference image: {photo.name}") from exc
    measurements = manifest.get("measurements")
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("at least one independently checked measurement is required")
    boxes = mesh_bounds(model)
    names: set[str] = set()
    rows = []
    for item in measurements:
        if not isinstance(item, dict):
            raise TypeError("measurement entry must be an object")
        rows.append(_measurement(item, boxes, names))
    return {
        "case_type_declared": manifest["case_type"],
        "measurement_source": "saved_3dm_mesh_vertices_via_rhino3dm",
        "model_sha256": model_hash,
        "reference_images_checked": len(references),
        "measurements_checked": len(rows),
        "measurements_within_tolerance": sum(row["within_tolerance"] for row in rows),
        "all_measured_dimensions_within_tolerance": all(row["within_tolerance"] for row in rows),
        "comparison": rows,
        "photo_shape_match_verified": False,
        "independent_3dm_reader_verified": False,
        "limitation": "Truth source and case type are user declarations; only listed dimensions are checked.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path)
    args = parser.parse_args()
    folder = args.case_dir.resolve(strict=True)
    result = score_case(folder / "case_manifest.json")
    target = folder / "case_score.json"
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"refusing to overwrite: {target}")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=folder,
                                     prefix=".case_score_", suffix=".tmp", delete=False) as stream:
        staged = Path(stream.name)
        try:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            staged.unlink(missing_ok=True)
            raise
    try:
        os.link(staged, target)
    finally:
        staged.unlink(missing_ok=True)
    print(json.dumps({
        "measurements_checked": result["measurements_checked"],
        "measurements_within_tolerance": result["measurements_within_tolerance"],
        "photo_shape_match_verified": False,
    }))


if __name__ == "__main__":
    main()
