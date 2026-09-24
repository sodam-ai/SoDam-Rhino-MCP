"""Command line access to the same engine used by the MCP server."""

from __future__ import annotations

import argparse
import json

from .blend_import import import_blend
from .blender_render import render_blender_views
from .evidence import (
    build_verified_model,
    draft_evidence_spec,
    prepare_reference_case,
    validate_reference_case,
)
from .model import build_model, inspect_model
from .render import render_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and inspect 3DM models without Rhino")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("spec")
    build.add_argument("output")
    verified = commands.add_parser("build-verified")
    verified.add_argument("spec")
    verified.add_argument("packet")
    verified.add_argument("output")
    reference = commands.add_parser("prepare-reference")
    reference.add_argument("output")
    reference.add_argument("images", nargs="+")
    reference.add_argument("--known", action="append", default=[], metavar="NAME=VALUE")
    reference.add_argument("--units", default="meters")
    draft = commands.add_parser("draft-evidence")
    draft.add_argument("spec")
    draft.add_argument("packet")
    draft.add_argument("output")
    audit = commands.add_parser("audit-evidence")
    audit.add_argument("spec")
    audit.add_argument("packet")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("model")
    render = commands.add_parser("render")
    render.add_argument("model")
    render.add_argument("output")
    render.add_argument("--azimuth", type=float, default=315)
    render.add_argument("--elevation", type=float, default=28)
    blender = commands.add_parser("render-blender")
    blender.add_argument("model")
    blender.add_argument("output_dir")
    blender.add_argument("--blender-exe")
    blender.add_argument("--front-azimuth", type=float, default=315)
    blender.add_argument("--front-elevation", type=float, default=28)
    blender.add_argument("--rear-azimuth", type=float, default=135)
    blender.add_argument("--rear-elevation", type=float, default=28)
    imported = commands.add_parser("import-blend")
    imported.add_argument("blend")
    imported.add_argument("output")
    imported.add_argument("--blender-exe")
    imported.add_argument("--meters-per-unit", type=float)
    args = parser.parse_args()
    if args.command == "build":
        result = build_model(args.spec, args.output)
    elif args.command == "build-verified":
        result = build_verified_model(args.spec, args.packet, args.output)
    elif args.command == "prepare-reference":
        known = {}
        for item in args.known:
            name, separator, value = item.partition("=")
            if not separator:
                parser.error("--known must use NAME=VALUE")
            known[name] = float(value)
        result = prepare_reference_case(args.images, known, args.output, args.units)
    elif args.command == "draft-evidence":
        result = draft_evidence_spec(args.spec, args.packet, args.output)
    elif args.command == "audit-evidence":
        result = validate_reference_case(args.spec, args.packet)
    elif args.command == "inspect":
        result = inspect_model(args.model)
    elif args.command == "render":
        result = render_model(args.model, args.output, azimuth=args.azimuth, elevation=args.elevation)
    elif args.command == "import-blend":
        result = import_blend(args.blend, args.output, args.blender_exe, args.meters_per_unit)
    else:
        result = render_blender_views(
            args.model, args.output_dir, args.blender_exe,
            front_azimuth=args.front_azimuth, front_elevation=args.front_elevation,
            rear_azimuth=args.rear_azimuth, rear_elevation=args.rear_elevation,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
