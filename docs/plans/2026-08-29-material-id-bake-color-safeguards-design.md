# Material ID Bake Color Safeguards

## Problem

Material ID bakes can produce colors that differ from the temporary ID colors assigned before baking. With anti-aliasing disabled, the likely source is not downsampling. The current Material ID setup paints selected faces through Blender's vertex paint operator, while Element ID writes loop colors directly through `bmesh`.

## Design

For the first fix pass, make Material ID use the same deterministic color-writing strategy as Element ID. `setup_vertex_color_id_material()` should write the resolved ID color directly to every loop of every face using the original material slot index. This keeps TexTools' existing persistent material-to-color mapping, avoids brush/operator color handling, and removes the need for a View3D override in this path.

This pass will not change global bake padding or post-process pixels. If color bleeding remains after exact loop assignment, the next focused safeguard should be an ID-specific bake margin or nearest-ID post-bake quantization step.

## Verification

Test in Blender with a simple multi-material mesh using `Material ID` and AA set to `None`. Confirm that the baked colors match the generated ID colors and that material boundaries do not show unexpected mixed colors.
