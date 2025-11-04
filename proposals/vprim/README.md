# Visualizing the Unseeable
Copyright © 2024, NVIDIA Corporation, version 1.1
## Overview
OpenUSD models both fantastical and real world scenes with physically
modeled geometry and materials. There's an increasing need to render
nondiegetic visualizations that do not participate in physically based
rendering and simulation. These may be screen anchored labels or paths
through a scene. They may be vector fields (or even captured light
paths!). The traditional method of tagging `Gprim`s with `guide`
purpose has not been sufficient in part because users are looking to
style these visualizations with nondiegetic effects (screen dependent
positioning and sizing, outlines and overlays, etc.). These
nondiegetic visualizations often require different descriptions than
those the current `UsdGeom` domain currently specifies.

Nondiegetic visualizations fall into three categories.
* Nondiegetic drawables used to describe screen and other
extrinsically constrainted effects (ie. markup curves or labels)
* Nondiegetic transformations that may introduce screen and other
extrinsic contraints on top of existing diegetic geometry
* Applied nondiegetic styling schemas that can be add screen and
extrinsically constrained effects to existing `Gprim`s (ie. like a
sillhoutte outline or overlays).

This proposal focuses mostly on examples of nondiegetic drawables. But
this does not aim to suggest that every diegetic `Gprim` requires a
nondiegetic reflection. Nondiegetic transformations and styles should
be appliable to the existing set of `Gprim`s as well.

### Nondiegetic visualizations and `guide`s
We use "nondiegetic" as a handle for describing objects intended to be
a part of any primary visualizations of the scene but aren't
physically present. If `Gprims` are diegetic like dialogue on audio
track, we're concerned with how to represent the visualization
equivalent of the orchestral score. Nondiegetic effects cannot be
removed without fundamentally changing the viewing experience but hold
a different set of constraints and idealized representations than
their diegetic cousins.

We view nondiegetic visualizations as orthogonal to the `guide`
`purpose` attribute. In our audio track analogy, `guide` serves the
role of a DVD commentary, an overlay adding additional context and
visual information that aren't a part of the primary viewing
experience and may be optionally experienced.

## Proposal
To address the need for standardized and interopable nondiegetic
drawables, transformations, and styling, introduce a new domain
`UsdViz` for nondiegetic visualizations primitives.

This domain would have three primary bases:
* `Vprims`: a set of typed nondiegetic drawables that remove some of
the constriants of `Gprim` (ie. intrinsic boundability)
* `VizAnchor`: a typed nondiegetic transformations that removes some
of the contraints of `Xform` (ie. intrinsic transformability)
* `VizStyleAPI`: a set of applied API schemas to add nondiegetic
effects to existing `Gprim`s.

The idea of `Vprims` and `VizStyleAPI` was partially inspired by work
done in `UsdLux`. Boundability as a schema partioning mechanism was
introduced to classify light schemas as either boundable (ie.
`RectLight` and `SphereLight`) or non-boundable (`DomeLight`). Applied
schema adapters were introduced to make any `Gprim` a light without
having to redefine in `UsdLux`.

### Example: `VizPoints`
Let's use points as a motivating example of a `Vprim`. Consider an
OpenUSD file that contains a mesh reconstruction of data from a point
cloud scan. A user might benefit from visualizing the points on top of
the mesh to aid in debugging some errors in the reconstruction. The
user might choose the `Points` schema to encode positions. And they
might be able to hide the source point cloud from rendering contexts
using `purpose` tagging and/or variant sets. But they will be unable
to make the points all the same size in camera space in a
specification compliant renderer. Preview optimizations that might
give a user their desired effect like those found in Storm exist
primarily for performance reasons and may not persist across
renderers, sessions, and future releases.

A visualization focused specification of points could look something
like this--

```
def VizPoints "PointCloud" {
    point3d[] points = [...]
    float[] pixels = [...]
    color3f[] primvars:displayColor = [(1, 0, 0)]
}
```

`VizPoints` could be rendered in camera but may also be composited
against a depth buffer from a physically based renderer.

`Vprims` would still support primvars and would be primarily styled
using `displayColor` and `displayOpacity`. We'd like to leave open the
possibility of a `viz` material purpose as a holder for describing
nondiegetic styles best described through material network, but this
proposal doesn't have a concrete definition of this yet.

### Example: `VizOverlayAPI`
This proposal frames screen space points (and paths) visualization
primitives as fundamentally different from their `Gprim` counterparts,
warranting their own first class `Vprim` typed schemas. It's important
that other `Gprim` types like `Cube` or `Cylinder` that retain their
underlying definition don't require nondiegetic reflections.

Consider an important primitive that you want to highlight in the
context of visualization.

```
def Sphere "grey_sphere" (apiSchemas=["VizOverlayAPI"])
{
    double radius = 4
    color3f primvars:displayColor (0.3, 0.3, 0.3)
    color3f viz:overlay:color = (0.6, 0.0, 0.0)
    float viz:overlay:opacity = 0.5
    token viz:overlay:visability = "inherited"
}
```
This adds a nondiegetic overlay and outline for visualizations to a
grey sphere. The viewer will see the red transparently overlayed, but
the sphere is still a grey sphere from the perspective of light
transport (reflected and refracted light).

Consideration must be also given to if or how these schemas affect
interactive picking. A non-slicing visualization effect might include
sillhoutte outlines or overlays applied to a `Gprim` to style or
highlight its importance.

### Example: `VizScreenAnchor`
For `Gprim`s that need to be aligned, anchored, or otherwise
nondiegtically constrained for visualization, we suggest that a custom
`Imageable` be introduced. Just as `UsdGeomPointInstancer` is allowed
to introduce a break in a transformation hierarchy to introduce
vectorized instancing, these grouping adapters would be responsible
for introducing nondiegetic transformations of the existing `Gprim`
domain (including screen relative placement). We'd propose a Macbeth
color chart as an example of geometry that users might want
nondiegetically constrained to a screen position in an asset's OpenUSD.
```
(
    defaultPrim = "Asset"
)

def Xform "Asset" {
    def Scope "Geometry" {
        def Sphere "sphere" {}
    }
}

def VizAnchor "Visualization" {
    # Collection of properties that anchor descendants to 
    # the lower right corner of screen
    def Plane "MacbethChart" {}
}
```

A nondiegetic transformation could be used to orient an object to
 camera or provide a floating region for a label around an object.

### Sample Set of Visualization Primitives
A proposed initial set of visualization primitives is listed below.
Additional iterations of this document should ensure that the the
visualization primitive concept can accomodate existing proposals.
Further evaluation should be done to see if existing `Gprim`s might be
more appropriate as `Vprim`s (like `HermiteCurves` which is explicitly
called out as "not for final rendering").
* `VizPoints`: Points with 3-D positions but screen space widths
* `VizVolumeSamples`: List of 3-D points at which to sample fields in
a `UsdVol` volume. The field type can drive the output style (`vector`
renders as arrows, `density` or `color` render as screen space points)
or could be otherwise configured.
* `VizPolylines`: Align with existing curve styling proposals
* `VizPaths`: Cubically interpolated curves that align with existing
curve styling proposals
* `VizLabel`: Align with existing text schema proposals
* `VizOverlayAPI`: Add a nondiegetic color overlay on top of an
existing `Gprim`
* `VizSilhoutteAPI`: Add a nondiegetic edge on top of an existing
`Gprim`
* `VizScreenAnchor`: Nondiegetic screen anchoring transformation

### Schema Slicing
One important consideration when introducing schemas in this domain is
to whether or not they are new drawables (`Vprim`s) or styles on top
of existing drawables (`Gprim` + `VizStyleAPI`).

An iteration of the `LineStyle` [proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/LineStyle)
suggests the existing `Curves` schemas can be adapted into screen
space via API schema. The API schema makes three transformative
changes. It transforms the meaning of the `widths` attribute to be a
screen space size (`constant` or `uniform` only), changes the
appearence of joints and end caps, and resticts the materials allowed
to be bound to a restricted set of "styling" materials.

The current code for bounding `UsdGeomCurves` takes the maximum value
of the `widths` attribute to pad the extent of its `points`. Consider
a scene with `metersPerUnit = 1.0`. If a prim uses the `CurveStyleAPI`
to redefine a 1 pixel constant width, the
`UsdGeomCurves::ComputeExtent` code is unawair of the redefinition and
interpret the `widths` as object space meters, padding the curve
`extent` by a meter.

We term this ambiguity "schema slicing" (to adapt the term "object
slicing" from C++). In that language, object slicing occurs when the
properties and behavior of a derived type are "sliced" off when
interfacing with an object via a higher level type. Using an API
schema to transform the curves into screen space defined primitives
similarly slices off the space redefinition for contexts like extent
computation. Utlimately, "slicing" complicates interchange and
standardization.

This proposal does not believe that all applications or usages of API
schemas are inherently "slicing". Most API schemas are used to
augment, annotate, or adapt prims for usage by other domains, but
generally leave the original prim's meaning untouched.

#### Disaggregating `hermite` out of `BasisCurves`
As a historical analogue, the `hermite` basis was previously a part of
`BasisCurves` but was left unimplemented in Storm and many renderers.
We learned the primary usage was to describe paths and not as a
renderable representation, ultimately seperating it out into its own
schema. This change made `BasisCurves` simpler for renderers to fully
support and let `HermiteCurves` stand on its own with a decoupled
`points` and `tangents` representation and without the need to
formulate support for the different `wrap` modes of `BasisCurves`.
Disaggregating schemas based on usage and client needs can lead to
better support and interopability for all.

## Alternative Approaches
### Annotation Specific Schemas
Some suggest that the needs would be better served with discrete
purposed annotation primitives (ie. `AnnotationLabel`,
`AnnotationPaths`, `AnnotationPoints`). The door should be cleanly
shut to using visualzation primitives for imposter billboard cards or
generalized non-photorealistic rendering. This choice was not the
preferred approach because there is a need for visualization
primitives outside of the annotation space, and that annotations
specific properties could extend the set of visualization primitives
through additional schemas.

### Introduce New Typed Schemas Without the `Vprim` Categorization
Readers may agree that some of these nondiegetic primitives are
distinct enough to warrant new schemas, but may reject the premise
that screen independence is necessarily a fundemental property of
`Gprim`s. The USD Glossary says `Gprim`s are just drawable,
transformable, and boundable. The problems of how to bound, transform
(and otherwise collide / intersect) screen space objects should be
clarified and reconciled within the existing `Gprim` definition,
rather than introduce a new type. This is not the preferred approach
of this proposal which sees value having the high level classification
for diegetic and nondiegetic primitives that clients can use to
organize scene processing and imaging pipelines around.

### Disaggregate Boundability out of `Gprim`
The proposal suggests that `Vprim`s required a relaxed definition of
boundability. One could imagine that just boundability could
disaggregated as well so that not every `Gprim` requires a traditional
`extent`.

This would be a large change requiring schema upgrades for almost all
current `Gprim` usage. We also think there might be other core
properties (`doublesided`) and behaviors that warrant removal from the
"visualization" domain so this isn't our preferred approach.

## Summary
To preserve compatability, supportability, and interchange of existing
`UsdGeom` schemas while extending USD's ability to describe
nondiegetic visualizations, a new domain of applied and typed schemas
should be introduced. This domain would allow visualizations to be
described in relation to both screen and other primitive.

## Questions
* As formulated `Vprims` cannot be `PointBased` which are strictly
`Gprims`. Are there any cases where dispatching behavior off of the
more general `PointBased` without knowing the concrete type is
important?
* When defining screen space sizes, what is the best choice of units?
Is it pixels or something else?
* How should scaling be treated for screen space objects?

## Future Work

### Hiding
As currently described, visualization primitives should be strictly
hidden via depth. However, one could imagine customizing hiding for
these prims. Some visualizations might want to hide based on a
particular reference point for the entire string of text. Some
visualizations might want to express priority with respect to other
objects in the scene. Hiding is another axis where the specification
may eventually end up diverging from the `Gprim` space.

### Breaking the Fourth Wall
Some care needs to be taken to establish best practices and rules for
visibility of screen-constrained primitives. While we generally would
expect nondiegetic primitives to not participate in physically based
lighting, consider screen constrained "context spheres" as reference
objects. They "break the fourth wall" and capture light and
reflections. It should be possible to opt into this behavior when
using nondiegetic transformations.