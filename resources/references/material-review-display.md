# Material and render verification

Use for uncertain material identity, surface fidelity, mapping, display problems
or final rendering. SKILL.md defines scope and quality. Choose relevant checks;
there is no mandatory classification report for every material.

## Geometry and material

Inspect geometry with neutral/solid/clay display when materials obscure it. For
a material comparison, hold a verified comparable camera and geometry fixed so
display changes do not hide geometric changes. Clay views diagnose geometry;
the final deliverable includes an actual material render from the final model.

In Rhino, query installed display mode names/IDs; an available material-capable
mode can help inspect mapping. Use exact returned identifiers. In Blender use its
actual solid/material/render modes. Neither a display-mode label nor a successful
render command proves that textures or geometry rendered correctly.

## Surface and source

- Uniform material is appropriate for a genuinely uniform surface, an inferred
  unseen surface, or explicitly simplified distant context. It is insufficient
  when a recognizable or promised surface pattern is missing.
- Bitmap and procedural materials are both valid. Inspect actual brick joints,
  grain, stone patterns or other defining surface detail, not material names alone.
  Use geometry for architectural relief that affects silhouette, openings or space.
- Record essential texture/material provenance: reference-derived, procedural or
  library source, plus approximate substitution where relevant. Do not present
  invented provenance or a generic texture as the photographed original.
- Deliver the user's specified resolution and format. Otherwise choose resolution
  sufficient for the surface size and intended views; there is no universal pixel
  requirement. Native procedural materials need not be baked without a reason.

## What to inspect

Check appropriate object assignment and boundaries; material identity; colour,
roughness, metallic response, transmission/refraction and opacity as applicable;
real-world pattern scale; mapping direction/stretch/seams/repetition; and shared
material consistency across instances. Validate observable appearance under
useful lighting rather than treating stored shader numbers as proof.

Where a pattern has a known dimension, use it to check mapping. A parameterized
surface can stretch a texture differently on each face even when the material's
scale is correct: inspect object mapping as well. When scale is inferred, state
the assumption instead of claiming a measurement.

## Diagnose before changing

Distinguish geometry, material assignment, missing pattern, unsuitable identity,
wrong scale, UV/object mapping, resource path, lighting and display mode. Correct
the cause and inspect the result. If geometry is wrong, fix its controls; editing
roughness or camera angle cannot repair an opening or recess.

Before delivery, inspect the saved-file material/resources and the actual output
primary and supplementary images for missing maps, broken transparency, blank output, unwanted clipping and
resolution. Save both cameras/views and necessary render settings with the
model. A rendered image alone does not establish native-file editability.
