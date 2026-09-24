"""Persist a validated modeling specification received through MCP."""

from __future__ import annotations

import json
from pathlib import Path

from .model import validate_spec


def write_spec(spec_json: str, output_path: str | Path) -> dict:
    if not isinstance(spec_json, str):
        raise TypeError("spec_json must be a JSON string")
    if len(spec_json) > 2_000_000:
        raise ValueError("spec_json is too large")
    target = Path(output_path).resolve()
    if target.suffix.lower() != ".json":
        raise ValueError("spec output must be .json")
    spec = json.loads(spec_json)
    validate_spec(spec)
    content = json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
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
    return {"path": str(target), "units": spec["units"], "components": len(spec["components"])}
