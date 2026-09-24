# Form verification

Scope: use relevant methods when a defining feature, control geometry or
finished envelope is uncertain. Choose a useful comparison, not a complete form
for every feature. For oral-only modeling compare against dimensions and intent.
These methods do not prescribe review stages; dimension, assembly, editability,
material and scene outcomes remain separately required under SKILL.md.

## Define what could falsify the reading

Identify the features that determine this building's form from the supplied
references before evaluating the candidate. Include the visible extent and
principal proportions, plus every prominent contour, opening or volume
relationship whose misreading would propagate through the model. Depending on
the building, these may include a roof ridge and eaves, setbacks, courtyard
boundaries, stepped masses, a dominant bay rhythm or a continuous curved surface.
Do not impose curved-tower features on an unrelated building.

For a disputed or complex feature, identify the reference evidence, relevant
model geometry and consequential discrepancy or uncertainty. Keep only what
supports the judgment and correction; no per-feature record template is required.

Choose the acceptance basis from source resolution/distortion, the scale and
salience of the feature, and the intended detailed reconstruction and available evidence. Set it before
judging the candidate; do not relax it afterwards to obtain PASS. Agreed scope does not excuse misplacing an included defining feature that
the references clearly resolve. There is no universal pixel or percentage
threshold suitable for every reference. Record quantitative bounds where the
source supports measurement, and use explicit topology/visibility predicates
where a scalar distance would miss the error.

## Compare geometry at global and feature scales

Use a neutral display and a comparable model view (R5 in `strict-review.md`). Judge the whole
building and the selected features separately. Measurements remain tied to the
original aspect ratio and scale; a magnified crop cannot silently rescale the
candidate relative to the reference.

| Feature | Minimum useful comparison |
|---|---|
| Overall extent and proportion | Whole/part identification; height and widths/depths supported by the views; silhouette through the principal changes in shape. One bounding box is insufficient. |
| Continuous or stepped contours | Sample along the contour, including extrema, shoulders, changes in slope, setbacks and terminations. Compare position and curvature/step sequence, not just endpoints. |
| Principal openings and recesses | Compare both boundaries, center/axis, width changes, endpoints and their relation to surrounding solids. Check recess/enclosure depth from oblique evidence where available. A dark or transparent patch does not establish a void. |
| Volume arrangement and major rhythm | Relative placement, heights, setbacks, connections, count and spacing; whether a repetition rule also explains its visible exceptions. |

Select samples across each feature, not only where the candidate already fits.
Report local discrepancies alongside a global statistic; maximum or persistent
local error must not disappear into an average, silhouette IoU or a whole-image
difference dominated by background. Check the visible contour directly even
when numeric measurements pass. A traced line must identify the actual
architectural boundary under `checks.md` §3, not reflection or shadow alone.

Keep annotations as analysis evidence; do not warp a render to match a photo or
present image manipulation as a corrected model. Final visual evidence comes
from the actual geometry.

## Separate projection, evidence and geometry

Camera comparability allows comparison; it is not a geometric acceptance
criterion. The legacy registration tool's ±5% scale-drift threshold diagnoses
framing/processing, not acceptable shape error. Hold a comparable camera fixed while
assessing a geometry change. If projection is suspect, test it separately using
perspective cues, level relationships and other available evidence. Record what
changed and repeat the comparison. A camera fitted only to the exterior outline
may still contradict openings or spatial relationships.

Use each additional reference that materially constrains a defining feature.
For another photograph, establish its corresponding model view and compare the
region it actually shows; for a plan or section, register the relevant geometric
slice and distinguish cut elements from projections. Merely looking at an
auxiliary photo or quoting a drawing's dimensions does not verify the model in
that view. One source cannot automatically overrule another; resolve conflicts
under `checks.md` §1.7 and the input-conflict guidance in SKILL.md.

When only one photograph exists, perform the supported visual checks and an
oblique model check for spatial plausibility. Label unobservable depth and
absolute-scale limits under R1/R3. Do not invent a second-view confirmation or
demand an unavailable photograph unless the unresolved decision requires it.

## Decide and correct

**Accept the form only when defining features have been checked and no
consequential visible mismatch remains.**
A prominent, clearly resolved discrepancy blocks even if dimensions close and
all objects are valid. An uninspected defining feature remains unverified; missing a preferred
record format is not the same as lacking actual evidence. Permitted uncertainty on unobservable
geometry must state its limit and must not conceal a visible contradiction.

If the error lies in identity, topology or the generator, return to the reading.
If it is a supported numeric adjustment, correct the control parameter and check
affected features and dependencies. If its cause is unresolved, investigate or
ask under the existing stopping conditions; do not call it a material or camera
issue without evidence.

Verify representative components before multiplication. Recheck form when
added panels, frames or other changes can affect it, including the finished
envelope before delivery. Independently inspect assembly, editability,
materials, scene and the saved model/primary and supplementary renders. A good silhouette is necessary where observable;
it is never sufficient for delivery.
