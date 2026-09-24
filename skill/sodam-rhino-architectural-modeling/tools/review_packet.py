#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path):
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser()
    selection = ap.add_mutually_exclusive_group()
    selection.add_argument("--purpose", choices=["form", "dimensions", "assembly", "editability", "materials", "scene", "delivery"], help="Question to review; defaults to delivery")
    selection.add_argument("--gate", type=int, choices=[1, 2], help="Legacy alias: 1 = form, 2 = delivery; does not require staged reviews")
    selection.add_argument("--level", choices=["L1", "L2", "L3"], help="Legacy review labels only: L1 maps to gate 1; L2/L3 to gate 2")
    ap.add_argument("--primary-reference", help="Reference image when applicable")
    ap.add_argument("--brief", help="User description or constraints; useful without a photograph")
    ap.add_argument("--model-capture", help="Actual model image for the assigned question")
    ap.add_argument("--comparison-dir")
    ap.add_argument("--dimensions-json")
    ap.add_argument("--hypothesis-json")
    ap.add_argument("--uncertainty-json")
    ap.add_argument("--form-check-json")
    ap.add_argument("--coverage-json")
    ap.add_argument("--object-list-json")
    ap.add_argument("--depth-contract-json")
    ap.add_argument("--checkpoint", default="")
    ap.add_argument("--out", default="review_packet.json")
    args = ap.parse_args()
    gate = args.gate if args.gate is not None else (1 if args.level == "L1" else 2 if args.level else None)
    purpose = args.purpose or ("form" if gate == 1 else "delivery")

    packet = {
        "review_purpose": purpose,
        "review_gate": gate,
        "review_level": args.level,
        "primary_reference": args.primary_reference,
        "user_brief": args.brief,
        "model_capture": args.model_capture,
        "comparison_dir": args.comparison_dir,
        "dimensions": load_json(args.dimensions_json),
        "architecture_hypothesis": load_json(args.hypothesis_json),
        "uncertainties": load_json(args.uncertainty_json),
        "form_check": load_json(args.form_check_json),
        "coverage": load_json(args.coverage_json),
        "objects": load_json(args.object_list_json),
        "depth_contract": load_json(args.depth_contract_json),
        "checkpoint": args.checkpoint,
        "review_instruction": "Use REVIEWER.md for the assigned question. Inspect actual evidence, not modeler justification. This optional packet neither imposes review stages nor proves completion. Obtain missing relevant evidence; report limitations. Delivery includes the native model, actual main-view render and saved camera/view."
    }
    Path(args.out).write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    print(Path(args.out).resolve())

if __name__ == "__main__":
    main()
