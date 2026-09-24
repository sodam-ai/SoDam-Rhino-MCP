"""Trace geometric numbers to image evidence, given dimensions, or explicit assumptions."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image

from .model import UNIT_SYSTEMS, build_model, validate_spec


def _new_file(path: str | Path, extension: str) -> Path:
    target = Path(path).resolve()
    if target.suffix.lower() != extension:
        raise ValueError(f"output must be {extension}")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite: {target}")
    return target


def _write_json_new(target: Path, value: dict) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2)
    target.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with target.open("x", encoding="utf-8") as stream:
            created = True
            stream.write(content)
    except OSError:
        if created:
            target.unlink(missing_ok=True)
        raise


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_reference_case(images: list[str | Path], known_dimensions: dict[str, float],
                           output_path: str | Path, units: str = "meters") -> dict:
    target = _new_file(output_path, ".json")
    if units not in UNIT_SYSTEMS:
        raise ValueError("unsupported reference units")
    if not isinstance(images, list) or not images:
        raise ValueError("at least one reference image is required")
    if not isinstance(known_dimensions, dict):
        raise TypeError("known_dimensions must be an object")
    known = {}
    for name, value in known_dimensions.items():
        if not isinstance(name, str) or not name.strip() or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("known dimensions need names and positive finite values")
        known[name] = float(value)
    records = []
    used = set()
    for item in images:
        path = Path(item).resolve(strict=True)
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ValueError("reference image must be PNG, JPEG or WebP")
        if path.parent != target.parent:
            raise ValueError("reference images and packet must share a folder")
        if path.name in used:
            raise ValueError("duplicate reference image")
        used.add(path.name)
        with Image.open(path) as source:
            source.verify()
        with Image.open(path) as source:
            size = list(source.size)
        records.append({"file": path.name, "sha256": _sha256(path), "pixels": size})
    packet = {"schema": "sodam-reference-v1", "units": units, "images": records,
              "known_dimensions": known, "note": "Image measurements require human review; pixels alone do not establish world dimensions."}
    _write_json_new(target, packet)
    return {"path": str(target), "images": len(records), "units": units, "known_dimensions": known}


def _geometry_fields(item: dict) -> list[str]:
    names = [f"origin.{i}" for i in range(3)] + [f"size.{i}" for i in range(3)]
    if item["kind"] == "gable_roof":
        names.append("ridge_height")
    if item["kind"] == "wall_opening":
        names += [f"opening.start_bottom.{i}" for i in range(2)]
        names += [f"opening.size.{i}" for i in range(2)]
    return names


def draft_evidence_spec(spec_path: str | Path, packet_path: str | Path,
                        output_path: str | Path, units: str = "meters") -> dict:
    target = _new_file(output_path, ".json")
    packet = _load_packet(packet_path)
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    validate_spec(spec)
    for item in spec["components"]:
        item["field_evidence"] = {
            key: {"status": "inferred", "reason": "Not established by the supplied reference images; review before use."}
            for key in _geometry_fields(item)
        }
    spec["reference_packet"] = Path(packet_path).name
    _write_json_new(target, spec)
    return {"path": str(target), "components": len(spec["components"]),
            "fields_to_review": sum(len(_geometry_fields(i)) for i in spec["components"]),
            "images": len(packet["images"])}


def _load_packet(packet_path: str | Path) -> dict:
    path = Path(packet_path).resolve(strict=True)
    packet = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise TypeError("invalid reference packet")
    if packet.get("units") not in UNIT_SYSTEMS or not isinstance(packet.get("known_dimensions"), dict):
        raise ValueError("invalid reference packet units or known dimensions")
    for name, value in packet["known_dimensions"].items():
        if not isinstance(name, str) or not name.strip() or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("known dimensions need names and positive finite values")
    if packet.get("schema") != "sodam-reference-v1" or not isinstance(packet.get("images"), list) or not packet["images"]:
        raise ValueError("invalid reference packet")
    for image in packet["images"]:
        if not isinstance(image, dict) or not isinstance(image.get("file"), str) or Path(image["file"]).name != image["file"]:
            raise ValueError("invalid reference image path")
        actual = (path.parent / image["file"]).resolve(strict=True)
        if actual.parent != path.parent or _sha256(actual) != image.get("sha256"):
            raise ValueError(f"reference image changed: {image['file']}")
    return packet


def validate_reference_case(spec_path: str | Path, packet_path: str | Path) -> dict:
    packet = _load_packet(packet_path)
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    validate_spec(spec)
    if spec["units"] != packet.get("units"):
        raise ValueError("reference and model units differ")
    if spec.get("reference_packet") != Path(packet_path).name:
        raise ValueError("spec does not identify this reference packet")
    images = {record["file"] for record in packet["images"]}
    known = set(packet.get("known_dimensions", {}))
    totals = {"given": 0, "measured": 0, "inferred": 0}
    review_required = []
    for item in spec["components"]:
        entries = item.get("field_evidence")
        required = set(_geometry_fields(item))
        if not isinstance(entries, dict) or set(entries) != required:
            raise ValueError(f"{item['name']}: every geometric number needs exactly one evidence record")
        for field, record in entries.items():
            if not isinstance(record, dict) or record.get("status") not in totals:
                raise ValueError(f"{item['name']}.{field}: invalid evidence status")
            status = record["status"]
            if status == "inferred":
                if not isinstance(record.get("reason"), str) or not record["reason"].strip():
                    raise ValueError(f"{item['name']}.{field}: inference needs a reason")
            elif status == "given":
                if record.get("source") not in known:
                    raise ValueError(f"{item['name']}.{field}: given value needs a known dimension source")
                value = item
                for segment in field.split("."):
                    value = value[int(segment)] if segment.isdigit() else value[segment]
                if not math.isclose(float(value), float(packet["known_dimensions"][record["source"]]), abs_tol=1e-6):
                    raise ValueError(f"{item['name']}.{field}: given value does not match source")
            elif record.get("source") not in images:
                raise ValueError(f"{item['name']}.{field}: measured value needs a reference image source")
            if status != "given":
                review_required.append({
                    "field": f"{item['name']}.{field}",
                    "reason": "image measurement needs independent calibration" if status == "measured"
                              else "inferred geometry needs human confirmation",
                })
            totals[status] += 1
    return {"valid": True, "components": len(spec["components"]), "fields": totals,
            "images": len(images), "accuracy_verified": False,
            "review_required": review_required,
            "note": "Provenance checked; geometric accuracy and image interpretation are not automatically verified."}


def build_verified_model(spec_path: str | Path, packet_path: str | Path,
                         output_path: str | Path, units: str = "meters") -> dict:
    audit = validate_reference_case(spec_path, packet_path)
    result = build_model(spec_path, output_path)
    result["evidence_audit"] = audit
    return result
