# Application execution

Use Rhino MCP by default; Blender applies only when explicitly chosen by the
user. A connection failure does not authorize switching applications.
Discover the installed tools and live
document before choosing an execution path; do not promise an unavailable
connector. SKILL.md defines the detailed-model outcomes and user scope. This
file supplies execution guidance, not a separate review procedure.

## Shared behavior

- Prefer the application's working connector or scripting interface. Verify
  available commands and signatures; do not translate one application's API into
  guessed calls for another. Use the relevant computer-use skill if UI operation
  is actually needed.
- Inspect the existing document and units, preserve user work, and save a
  recoverable checkpoint before substantial changes to an existing model.
- Choose native, editable geometry that suits the shape: control surfaces,
  meshes, solids, curves, modifiers and instances are means, not quality tiers.
  Test a representative assembly before multiplying expensive geometry.
- Verify scale, transforms, material assignment and resource paths in the saved
  artifact. A successful export call alone does not establish a usable file.
- If performance becomes a bottleneck, preserve component editability while
  using instances, sensible display detail or batching. Do not replace the model
  with an opaque merged mesh merely to obtain a quick capture.

## Rhino

Read relevant sections of `TOOLING.md` before the corresponding operation.
Its documented traps concern Rhino, especially capture scale, material mapping,
view frusta and saved views. Use semantic layers and object attributes, blocks
for suitable repetitions, and appropriate curves/surfaces/solids/meshes. Apply
solid and naked-edge checks according to what the object is intended to be.

## Blender

Use the actual available Blender tool or scripting interface, consulting its
installed API information when needed. This skill does not claim a bundled or
tested Blender connector. Use named objects and collections, reusable instances
where appropriate, and accessible modifiers or control objects for useful
parameters. Keep units and object transforms consistent with supplied dimensions.

Inspect mesh normals, material slots, texture mapping and intersections where
they affect the intended assembly. An intentionally open surface is not a failed
solid. Use a neutral solid/clay view to inspect geometry and a suitable material
view to inspect surfaces; do not copy Rhino display-mode names or capture macros.
Save the native `.blend`, retain or pack required resources, and restore a usable
saved design/reference view. Save the primary and supplementary cameras and render
settings needed to reproduce both delivered images, and inspect the actual renders
from the saved final geometry.
