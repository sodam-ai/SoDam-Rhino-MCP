---
name: sodam-rhino-architectural-modeling
description: Create and revise editable architectural 3DM models from photos, briefs, and dimensions without Rhino, using the SoDam offline MCP.
---

# License-independent architectural reverse modeling

Use the `sodam-rhino-offline` MCP server. Call `get_architectural_workspace` first to locate its file workspace and supported geometry. The server does not run Rhino. For setup and scope, see [workflow](references/workflow.md).

Collect photos, descriptions, known dimensions, the modeling scope, and output requirements. Distinguish given facts, observations, and assumptions. A single photo cannot establish absolute size or hidden geometry. Ask only for missing facts that materially affect the result.

For non-photo JSON revisions, call `revise_architectural_spec` with the existing spec filename, exact component name, complete replacement component JSON, and a new output filename; then build a new `.3dm`. If the spec contains a photo evidence packet, write a new full spec and repeat evidence review instead.

For ambiguous form or camera matching, read [form verification](references/upstream/form-verification.md). For dimensions and source conflicts, read [checks](references/upstream/checks.md). For assembly or materials, read [construction logic](references/upstream/architectural-construction-logic.md) or [material review](references/upstream/material-review-display.md). These upstream references guide judgment only; their Rhino-specific execution paths are not available here. Optional image helpers are in `tools/`, with the upstream MIT notice in `UPSTREAM_LICENSE.txt`.

Write and validate the component JSON with `write_architectural_spec` in the configured workspace (or preserve an existing user-authored JSON), then use `prepare_architectural_reference`, `draft_architectural_evidence`, `audit_architectural_evidence`, and `build_verified_architectural_model` when photos are provided. For briefs without photos, use `build_architectural_model` and disclose that image accuracy was not checked.

For forms beyond the four JSON component kinds, build or edit a trusted source `.blend` in Blender, then call `import_blender_scene` and keep the `.blend` alongside the mesh-based `.3dm`. Confirm scene units and any explicit scale. Read back the saved `.3dm` with `inspect_architectural_model`. Check `blender_executable_configured` in `get_architectural_workspace`. If true, use `render_blender_model` for two different rendered views and a saved `.blend`; inspect all three files. When a reference view is provided, set front_azimuth/front_elevation to approximate its direction and choose a distinct rear_azimuth/rear_elevation; these are camera angles, not automatic image registration. If Blender rendering fails, report the failure instead of presenting inspection PNGs as full renders. If Blender is not configured, call `render_architectural_view` twice for inspection only and disclose that material renders and saved cameras remain unavailable. Inspect actual outputs. Do not claim Rhino viewport control, Rhino NURBS/Boolean parity, photogrammetric accuracy, or photo-matched rendering.

Deliver the source JSON, saved model, primary and complementary views, and brief notes identifying known facts, assumptions, and unverified features. Do not overwrite existing work. See [quality checklist](references/quality.md) before saying the deliverable is complete.
