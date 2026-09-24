# Architectural Construction Logic

Reusable architectural knowledge. Apply relationships according to the actual
building type, user intent and scope in SKILL.md. Read the relevant systems;
the numbered sections organize knowledge, not a mandatory construction sequence.
There is no required written answer for every component or independent review
for every operation.

## 1. Core Principle: Model Architectural Systems, Not Stacked Surfaces

Mode A must reconstruct architecture as a three-dimensional assembly of real
architectural systems.

The model must not merely reproduce the appearance of the reference image by
stacking or attaching surfaces.

For a system whose role or connections are unclear, reason through:

1. what the element is;
2. what space or assembly it belongs to;
3. what it connects to;
4. what is in front of it and behind it;
5. whether it has thickness;
6. whether it creates an opening, enclosure, support, screen, railing, finish,
   or other architectural function.

Correct consequential spatial contradictions even when the assembly looks similar.

Represent applicable floor structure and circulation at the agreed scope. Use the
questions only where a relationship is unclear; no written answers are required.

## 2. Architectural relationships

Understand relevant adjacent systems and represent their spatial relationships.
Use a short note or a model inspection where needed; no per-system form is required.

Understand and model correctly where applicable:

- wall ↔ floor/slab;
- wall ↔ ceiling/roof;
- wall ↔ window;
- wall ↔ door;
- slab ↔ column;
- beam ↔ column;
- balcony ↔ slab;
- railing/parapet ↔ balcony/slab edge;
- curtain wall ↔ slab edge;
- façade screen ↔ structural/enclosure wall;
- ceiling ↔ structural slab;
- stair ↔ floor/landing;
- roof ↔ wall/parapet;
- cladding ↔ backing wall/subframe.

Check the relationships that affect the building being modeled; this list is a
knowledge reference, not an inspection form.

## 3. Window / Wall Relationship

A window is **not a surface pasted onto a wall**.

For a normal wall-based window condition, the model must represent, at the
required level of detail:

1. a real wall or enclosure element with thickness;
2. a real opening in that wall;
3. the window/frame positioned within the opening;
4. a believable setback or alignment relative to the wall faces;
5. sill, head, and jamb relationships consistent with the reference and
   architectural logic.

Forbidden:

- placing glass directly on the exterior face of an opaque wall without an
  opening;
- allowing glass to visually overlap solid wall geometry as a substitute for a
  window;
- using a single floating plane to represent a real window system when depth is
  visible;
- leaving the wall continuous behind a visible window opening unless the
  reference clearly shows a surface-applied glass assembly.

Correct missing openings or misplaced glazing at the controlling assembly.

## 4. Curtain Wall / Glazing Relationship

Distinguish curtain wall and large glazing systems from ordinary wall windows.

Where the reference indicates a curtain-wall system, identify:

- glazing plane;
- mullion/transom rhythm;
- slab-edge relationship;
- opaque spandrel zone if present;
- frame depth;
- corner condition;
- connection or setback relative to structural frame.

Do not model a curtain wall as a gray or transparent sheet attached arbitrarily
to the front of another façade.

## 5. Balcony / Loggia / Parapet Relationship

A balcony, recessed loggia, or external corridor is a spatial assembly, not
several unrelated planes.

Where applicable, identify:

1. front structural/façade frame;
2. balcony or corridor slab;
3. side boundaries;
4. parapet / railing / screen;
5. rear wall or glazing plane;
6. actual depth between front and rear elements.

Parapets, brick screens, and railings must terminate logically at side walls,
columns, or frame boundaries unless the reference clearly shows a gap.

Do not leave arbitrary gaps at both ends merely because the element was modeled
as a shorter rectangular surface.

## 6. Typical Floor Consistency

Where typical floors repeat, use shared controls or a repeated system to keep
their intended relationships consistent while preserving evidenced variations.

The typical-floor system should define, as applicable:

- floor-to-floor height;
- slab thickness;
- structural bay/module;
- column/vertical-frame positions;
- balcony/loggia depth;
- parapet/railing height;
- rear façade setback;
- opening positions;
- major façade module.

Where repetition is supported by the sources, investigate unexplained changes in
levels, alignments, depth or modules. Preserve actual variations rather than
forcing every floor into the same template.

## 7. Repetition: Build the Type First, Then Instance

Choose a shared generator, instance, modifier or another editable representation
that suits the repeated system. Check representative geometry and connections
before expensive multiplication; preserve real variations and exceptions.
A repeated error should be corrected at its controlling source.

## 8. Depth Must Be Explicit

When interpreting spatial relationships, distinguish:

- coplanar;
- recessed;
- projected;
- overlapping in view only;
- physically connected;
- physically separated.

Where visible depth materially defines the architecture, use real 3D offsets.

Do not approximate a recessed façade by placing darker material on the same
plane. Do not approximate a projecting element by changing color only.

## 9. Junction Check

Inspect representative junctions before propagating a system and on the
resulting assembly. The purpose is correct connections, not a named audit step.

Inspect representative conditions:

- wall-window jamb/head/sill;
- wall-door opening;
- slab-balcony edge;
- parapet/slab edge;
- column/slab;
- curtain wall/slab edge;
- roof/parapet;
- façade screen/primary enclosure;
- stair/landing.

The purpose is not construction-document detailing. The purpose is to confirm
that the architectural assembly is spatially and logically valid.

A model can be visually similar and still fail if the junction logic is
fundamentally wrong.

## 10. Assessment and correction

Distinguish fidelity to the sources from construction plausibility. Check the
actual role, location, count, section, level and connections of relevant elements;
for circulation, verify endpoints and spatial continuity. Use direct inspection
or a targeted independent review as appropriate.

Describe consequential discrepancies in plain language with enough evidence to
locate and correct them. No error codes, severity tables or pass/fail fields are
required. Correct repeated errors at their shared control before propagating them.
Choose priorities by their effect on the building and dependent work, not by a
fixed sequence of systems.

## 13. No Visual Cheat Rule

The following must never be used as substitutes for correct architectural
geometry:

- color difference;
- material difference;
- shadow;
- transparency;
- floating plane;
- surface overlap;
- camera angle;
- entourage.

If the reference shows a real recess, opening, slab, railing, wall, or window
relationship, model it as real geometry to the detail required by SKILL.md and the user's scope.

## 14. Objective Adaptability

These rules remain building-type neutral.

Do not hard-code assumptions such as:

- every façade is curtain wall;
- every repeated bay has the same width;
- every balcony is recessed;
- every building uses a frame structure;
- every window is centered in a wall;
- every floor is a typical floor.

Instead:

1. identify evidence;
2. determine the applicable architectural system;
3. apply the correct system logic;
4. preserve uncertainty where evidence is insufficient.

Behave like an architect applying transferable construction knowledge, not like
a benchmark-specific script.
