"""Create a new component spec revision without changing its source file."""

from __future__ import annotations

import json
from pathlib import Path

from .model import validate_spec


def revise_spec(source_path: str | Path, component_name: str,
                replacement_json: str, output_path: str | Path) -> dict:
    source = Path(source_path).resolve(strict=True)
    target = Path(output_path).resolve()
    if source.suffix.lower() != ".json" or target.suffix.lower() != ".json":
        raise ValueError("revision input and output must be .json")
    if source == target or target.exists():
        raise FileExistsError(f"refusing to overwrite: {target}")
    if not isinstance(component_name, str) or not component_name.strip():
        raise ValueError("component_name must be a nonempty string")
    if not isinstance(replacement_json, str) or len(replacement_json) > 2_000_000:
        raise ValueError("replacement_json must be a JSON string under 2,000,001 characters")
    spec = json.loads(source.read_text(encoding="utf-8"))
    validate_spec(spec)
    if "reference_packet" in spec or any("field_evidence" in part for part in spec["components"]):
        raise ValueError("evidence-tagged specs require a new evidence review; use a new full spec")
    replacement = json.loads(replacement_json)
    if not isinstance(replacement, dict) or replacement.get("name") != component_name:
        raise ValueError("replacement must be an object with the same component name")
    if "field_evidence" in replacement:
        raise ValueError("replacement cannot carry unreviewed field_evidence")
    matches = [index for index, part in enumerate(spec["components"])
               if part["name"] == component_name]
    if len(matches) != 1:
        raise ValueError(f"component not found: {component_name}")
    spec["components"][matches[0]] = replacement
    validate_spec(spec)
    content = json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(content)
    return {"path": str(target), "revised_component": component_name,
            "components": len(spec["components"]), "units": spec["units"]}
