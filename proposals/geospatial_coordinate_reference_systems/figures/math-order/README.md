# Placement-order figure provenance

The [proposal's informative placement-order illustration](../../README.md#placement-order-illustration)
is the sole walkthrough. This directory stores its six individual panels.

## Source and credit

“( FREE ) La tour Eiffel” by
[SDC PERFORMANCE](https://sketchfab.com/Lambo_SC04),
[original model](https://sketchfab.com/3d-models/free-la-tour-eiffel-8553f94d06e24cb4b0fde1080f281674),
licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The geometry was reoriented, rendered and adjusted for explanation.

## Reproduction record

[figure-provenance.json](figure-provenance.json) records the geometry hash,
source and output WKT, illustrative input values, ordered panel names,
ordinary transform stack, display origin, camera/overlay conventions and
figure-arithmetic checks.

To reproduce the panels, use that record with the credited geometry conformed
to metres and Z-up, retain one camera and ground grid, and render the six
listed states with the recorded previous-state outlines and direction/height
guides. The record does not prescribe a rendering tool or evaluator.

The checks concern figure arithmetic and presentation, not surveyed Paris
ground truth or proposal conformance. Height, attitude and adjustments are
illustrative; the attitude encoding remains under review.
