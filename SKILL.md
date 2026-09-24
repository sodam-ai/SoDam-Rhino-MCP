---
name: sodam-rhino-offline-modeling
description: Create and check architectural 3DM files from photos, dimensions, and descriptions without running Rhino. Use for license-independent 3DM work; not for live Rhino viewport control.
---

# SoDam architectural reverse modeling

Use the local JSON-to-3DM CLI or MCP tools. Do not start Rhino or assume a Rhino license. The JSON is the editable control source; the 3DM stores named mesh components, layers, and control values. Read README.md for setup and usage rights.

1. Collect the photos, known dimensions, modeling scope and desired output. A single image does not establish absolute dimensions or hidden geometry. Keep every source file unchanged.
2. Call prepare_architectural_reference with the photos and independently known dimensions. Analyze massing, openings, levels and roof. Write a component JSON based on examples/small_house.json. If no photo is supplied, work from the given description and state that image comparison is unavailable.
3. Call draft_architectural_evidence to create a field_evidence record for every geometric number. Mark a field given only when its numeric value equals the matching known dimension. Mark measured only when it was actually measured from the named image; otherwise keep inferred and explain the assumption. The draft defaults all numbers to inferred.
4. Call audit_architectural_evidence and inspect its review_required list. Resolve or explicitly disclose every inferred dimension and uncalibrated image measurement. build_verified_architectural_model verifies provenance completeness only; accuracy_verified remains false. Read the saved file with inspect_architectural_model; check units, bounds, names and layers. If a reference photo is unavailable, use build_architectural_model as the explicitly unverified path. Use a new output name for each iteration.
5. Read `blender_executable_configured` from get_architectural_workspace. If true, use render_blender_model for two material renders and a saved .blend; verify the files. If false, use render_architectural_view for two inspection images only and disclose the missing final render capability. Inspect the actual PNGs and compare them with the reference photo. A plausible render does not prove dimensions, materials, hidden geometry, camera match or Rhino-native editing.
6. Deliver the spec, 3DM, PNGs, reference packet when present, assumptions and unresolved differences. Report the actual verification level and the limitations of supported mesh shapes. Do not treat an unrendered file or guessed field as fully validated.

The upstream checklist in resources/upstream_mode_a_SKILL.md is historical guidance only. Its Rhino/MCP execution instructions do not define this project's workflow. See README.md for the upstream MIT notice, new-code license status, external reference rights, warranty and liability limits.
