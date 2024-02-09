# Visualizing the Unseeable

## Overview
OpenUSD models both fantastical and real world scenes with physically modeled geometry and materials. There's an increasing need to render nondiegetic visualizations that do not participate in physically based rendering and simulation. These may be user defined labels or curves describing a path through a scene. They may be curves representing vector fields (or even captured light paths!). The traditional method of tagging `Gprim`s with `guide` purpose has not been sufficient in part because users are looking to visualize in non-physical ways (like screen space widths). These nondiegetic visualizations require different descriptions than those the current `UsdGeom` domain currently specifies.

### Nondiegetic visualizations and `guide`s
We use "nondiegetic" as a handle for describing objects intended to be a part of any primary visualizations of the scene but aren't physically present. If `Gprims` are diegetic like dialogue on audio track, we're concerned with how to represent the visualization equivalent of the orchestral score. Nondigetic effects cannot be removed without fundamentally changing the viewing experience but hold a different set of constraints and idealized representations than their diegetic cousins.

We view nondiegetic visualizations as orthogonal to the `guide` `purpose` attribute. In our audio track analogy, `guide` serves the role of a DVD commentary, an overlay adding additional context and visual information that aren't a part of the primary viewing experience and may be optionally experienced.

## Background
OpenUSD was developed as path tracing and physically based rendering were maturing in the visual effects production pipeline. As such, scenes are modeled as physical 3-D geometry. `Points` are spheres and `BasisCurves` are tubes (or user-oriented ribbons) that can be ray traced from any direction. They were decidedly not the screen oriented disks and ribbons previously used in rasterizers.

Users are currently seeking a way to visualize data through schemas added to OpenUSD. A user may want describe a "red line" to draw attention to a particular object or a "green curve" to represent available paths towards exits during building design.

### Schema Slicing
One instance of these new schemas is `CurveStyleAPI`, proposed as an API schema for the existing `Curves` schemas. The API schema makes three transformative changes. It transforms the meaning of the `widths` attribute to be a screen space size (`constant` or `uniform` only), changes the appearence of joints and end caps, and resticts the materials allowed to be bound to a restricted set of "styling" materials.

We believe this creates a situation we're calling "schema slicing" (to adapt the term "object slicing" from C++). In that language, object slicing occurs when the properties and behavior of a derived type are "sliced" off when interfacing with an object via a higher level type. Using `CurveStyleAPI` to transform the curves into screen space defined primitives similarly creates the potential for slicing. A user interacting with the prim using the `BasisCurves` schema and not the full prim definition will have effectively "sliced" off the reinterpretation of widths and other modifications to the underlying definition. Utlimately, "slicing" complicates interchange and standardization.

### Disaggregating `hermite` out of `BasisCurves`
As a historical analogue, the `hermite` basis was previously a part of `BasisCurves` but was left unimplemented in Storm and many renderers. We learned the primary usage was to describe paths and not as a renderable representation, ultimately seperating it out into its own schema. This change made `BasisCurves` simpler for renderers to fully support and let `HermiteCurves` stand on its own with a decoupled `points` and `tangents` representation and without the need to formulate support for the different `wrap` modes of `BasisCurves`.

We similarly wonder if all variations of the current set of `Curves` are needed to describe screen space visualizations and when adding support, how renderers and other consumers know which to prioritize to establish compatability. A new axis of variation that transform the existing geometric schemas complicates interchange and compatability of the `UsdGeom` domain. We suggest new schema domain with a new set of schemas may be the best place to drive development of nondiegetic primitives separate from their diegetic `UsdGeom` cousins.

## Proposal
Introduce a class of visualization primitives that are defined in a 3-D scene, but whose imaging definition is allowed to include nondiegetic screen effects and with a relaxed definition of boundability. Let's call them `Vprims` (visualization primitives). Boundability as a schema partioning mechanism is already employed in `UsdLux` which classifies light schemas as either boundable (ie. `RectLight` and `SphereLight`) or non-boundable (`DomeLight`).

Let's use points as a motivating example. Consider an OpenUSD file that contains a mesh reconstruction of data from a point cloud scan. A user might benefit from visualizing the points on top of the mesh to aid in debugging some errors in the reconstruction. The user might choose the `Points` schema to encode positions. And they might be able to hide the source point cloud from rendering contexts using `purpose` tagging and/or variant sets. But they will be unable to make the points all the same size in camera space in a specification compliant renderer. Preview optimizations that might give a user their desired effect like those found in Storm exist primarily for performance reasons and may not persist across renderers, sessions, and future releases.

A visualization focused specification of points could look something like this--

```
def VizPoints "PointCloud" {
    point3d[] points = [...]
    float[] pixels = [...]
    color3f[] primvars:displayColor = [(1, 0, 0)]
}
```

`VizPoints` could be rendered in camera but may also be composited against a depth buffer from a physically based renderer.

### Styling
`Vprims` still support primvars and would be primarily styled using `displayColor` and `displayOpacity`.

We'd like to leave open the possibility of a `viz` material purpose as a holder for describing nondiegetic styles best described through material network, but this proposal doesn't have a concrete definition of this yet.

### API Schema and Grouping Adapters
This proposal frames screen space points (and paths) visualization primitives as fundamentally different from their `Gprim` counterparts, warranting their own first class `Vprim` typed schemas. Does this proposal set the precedent that other `Gprim` types like `Cube` or `Cylinder` require visualization equivalents if they wanted to be adapted into the "visualization" domain? We'd suggest no and offer two solutions that have prior art in OpenUSD.

If a primitive retains its underlying definition, `UsdLux` already provides a solution to the problem of adapting `Gprim`s into another domain. Rather than a `MeshLight`, the `Mesh` `Gprim` is adapted via an API schema. `Gprim`s could be similarly "adapted" into the visualization domain. To avoid "schema slicing" an adaptation must not change the underlying definition or require their own distinct `purpose` or `visibility` tagging. Consideration must be also given to if or how these schemas affect interactive picking. A non-slicing visualization effect might include sillhoutte outlines, glows, or overlays applied to a `Gprim` to style or highlight its importance.

For `Gprim`s that need to be aligned, anchored, or otherwise nondiegtically constrained for visualization, we suggest that a custom `Imageable` be introduced-- (`VizAnchor` or `VizGroup`). Just as `UsdGeomPointInstancer` is allowed to introduce a break in a transformation hierarchy to introduce vectorized instancing, these grouping adapters would be responsible for introducing nondiegetic transformations of the existing `Gprim` domain (including screen relative placement). We'd propose a Macbeth color chart as an example of geometry that users might want nondiegetically constrained to a screen position in an asset's OpenUSD.
```
(
    defaultPrim = "Asset"
)

def Xform "Asset" {
    def Scope "Geometry" {
        def Sphere "sphere" {}
    }
}

def VizScope "Visualization" {
    # Collection of properties that anchor descendants to the lower right
    # corner of screen spaces
    def Plane "MacbethChart" {}
}
```
### Boundability
Because `Vprim`s are allowed to be screen dependent, they may have a relaxed notion of boundability and may complicate extent computation of `Boundable`s like `PointInstancer`s and `SkelRoot`s (and `PointInstancer`s of `SkelRoot`s). It may desirable for users to optionally specify a "reference" or "approximate" extent.

### Purpose
The traditional purpose rules still apply. Visualization primitives may but are not required to be tagged as `guide`s. There may be complicated visualizations that warrant `render` and `proxy` tagging as well.

### Sample Set of Visualization Primitives
A proposed initial set of visualization primitives is listed below. Additional iterations of this document should ensure that the the visualization primitive concept can accomodate existing proposals. Further evaluation should be done to see if existing `Gprim`s might be more appropriate as `Vprim`s (like `HermiteCurves` which is explicitly called out as "not for final rendering").
* `VizPoints`: Points with 3-D positions but screen space widths
* `VizVolumeSamples`: List of 3-D points at which to sample fields in a `UsdVol`. The field type can drive the output style (`vector` renders as arrows, `density` or `color` render as screen space points) or could be otherwise configured.
* `VizPolylines`: Align with existing curve styling proposals
* `VizPaths`: Cubically interpolated curves that align with existing curve styling proposals
* `VizText`: Align with existing text schema proposals

### Note on Schema Slicing
It's worth noting that this proposal does not believe that all applications or usages of API schemas are inherently "slicing". Most API schemas are used to augment, annotate, or adapt prims for usage by other domains, but generally leave the original prim definition untouched. Using API schemas to describe "optional" features of a concrete typed schema (that might otherwise be described with an enabling `bool` flag) would generally not be considered slicing as well.

## Alternative Approaches
### Annotation Specific Schemas
Some suggest that the needs would be better served with discrete purposed annotation primitives (ie. `AnnotationLabel`, `AnnotationPaths`, `AnnotationPoints`). The door should be cleanly shut to using visualzation primitives for imposter billboard cards or generalized non-photorealistic rendering. This choice was not the preferred approach because there is a need for visualization primitives outside of the annotation space, and that annotations specific properties could extend the set of visualization primitives through additional schemas.

### Introduce New Typed Schemas Without the `Vprim` Categorization
Readers may agree that some of these nondiegetic primitives are distinct enough to warrant new schemas, but may reject the premise that screen independence is necessarily a fundemental property of `Gprim`s. The USD Glossary says `Gprim`s are just drawable, transformable, and boundable. The problems of how to bound, transform (and otherwise collide / intersect) screen space objects should be clarified and reconciled within the existing `Gprim` definition, rather than introduce a new type. This is not the preferred approach of this proposal which sees value having a high level classification for diegetic and nondiegetic primitives that clients can use to organize scenes and imaging pipelines around.

### Disaggregate Boundability out of `Gprim`
The proposal suggests that `Vprim`s required a relaxed definition of boundability. One could imagine that just as `visibility` was disaggregated out of `Gprim` into its own schema, boundability could disaggregated as well so that not every `Gprim` requires a traditional `extent`.

We think there might be other core properties (`doublesided`) and behaviors that warrant removal from the "visualization" domain so this isn't our preferred approach.

## Summary
To preserve compatability, supportability, and interchange of existing `UsdGeom` schemas while extending USD's ability to describe nondiegetic visualizations, a new domain should be introduced. The `Vprim` domain would allow visualizations to be described in relation to both screen and other primitives and would avoid introducing schemas that might "slice" the current set of `Gprim`s.

## Questions
* As formulated `Vprims` cannot be `PointBased` which are strictly `Gprims`. Are there any cases where dispatching behavior off of the more general `PointBased` without knowing the concrete type is important?
* When defining screen space sizes, what is the best choice of units? Is it pixels or something else?
* How should scaling be treated for screen space objects?

## Future Work

### Hiding
As currently described, visualization primitives should be strictly hidden via depth. However, one could imagine customizing hiding for these prims. Some visualizations might want to hide based on a particular reference point for the entire string of text. Some visualizations might want to express priority with respect to other objects in the scene. Hiding is another axis where the specification may eventually end up diverging from the `Gprim` space.

### Breaking the Fourth Wall
Some care needs to be taken to establish best practices and rules for visibility of screen-constrained primitives. While we generally would expect nondiegetic primitives to not participate in physically based lighting, consider screen constrained "context spheres" as reference objects. They "break the fourth wall" and capture light and reflections. It should be possible to specify this behavior even when using nondiegetic transformations.

### Styling Schemas
Universal material model description has required a plugin system build around `Sdr` to allow for disparate renderer and site specific materials models to be integrated into OpenUSD. Even the simplest material models in OpenUSD (ie. `UsdPreviewSurface`) requires the notion of a network and connections.

Visualization style, on the other hand, is a more compact problem. Users often want to specify a single color, image, or pattern to style an object. There's potentially some inspiration to be drawn from 2-D tooling where often the same user interface is used to style text, lines, and other shapes.

We think the simplicity afforded by configuring stylization with simple declarative schemas that don't require material networks is worth pursuing in the future, but is beyond the scope of this proposal.
