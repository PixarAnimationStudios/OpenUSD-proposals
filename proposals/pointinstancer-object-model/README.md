*Note: This document was formerly at [https://github.com/PixarAnimationStudios/OpenUSD/wiki/PointInstancer-Object-Model](https://github.com/PixarAnimationStudios/OpenUSD/wiki/PointInstancer-Object-Model)
and has been moved here for archival reasons.*

# PointInstancer Object Model
Several years prior to developing general [scene-level instancing](https://openusd.org/release/glossary.html#usdglossary-instancing) in USD, at Pixar we were using a specialized point/array/table instancer consisting of a schema, optimized drawing support in Hydra, and plugin support in Katana (read only), Houdini, Presto, and Maya (export only). Today, even though scene-level instancing is broadly deployed in our pipeline, there are still scalability use cases for a vectorized instancer over having many prim-instances: when the number of instances grows to the tens or hundreds of thousands or more (largest instancer to-date in production had around nine million instances) *and* the need to interact with individual instances is small, an instancer will load faster and consume less memory than individual prim-instances.

Our Houdini plugins rely on pointInstancers as they map closely to Houdini's instancing model; therefore to enable open-sourcing of those plugins, we are reformulating our internal pointInstancer - mostly simplifying, plus applying some lessons learned from earlier versions - for inclusion in [UsdGeom](http://openusd.org/release/api/usd_geom_page_front.html).

This document attempts to define the motivation and expected behaviors for the PointInstancer schema, then provide the details of the schema itself, and finally discuss the kinds of integration we expect to provide in DCC plugins.

# PointInstancer Behaviors

The proposed PointInstancer schema is very similar to [Houdini's point instancing scheme](https://www.sidefx.com/docs/houdini19.0/copy/instanceattrs), with a few simplifications in terms of specifying the per-instance transforms, and a few extra features designed to meet the needs of migrating this kind of data down a CG pipeline.  The PointInstancer schema must meet the needs of our sets/environments department, and the needs of our FX department.

## Sets Department Needs
The sets department relies on PointInstancers for dressing large numbers of simple and complex geometries, typically in the tens to hundreds of thousands of instances of one to tens of "prototypes".  Some examples:
* The leaves in the canopy of a deciduous tree
* Rocks or other debris scattered on a landscape
* Fields and crops of vegetation/shrubs
* Forests

The requirements deriving from these needs, beyond the most basic, that the encoding (and decoding of it) must scale, are:
* **Prototypes must be animatable** - which means that if the sources for the prototypes on the UsdStage have timeSampled animation, it will be honored. This allows us to apply "keep alive" or simulated, wind-driven motion to trees and other vegetation scattered in PointInstancers.
* **PointInstancer prototypes can themselves contain PointInstancers** - or stated more broadly, there is no restriction on what geometry a prototype can contain, or limit to its complexity.  In the forest example, we are PointInstancing trees, each of which may have one or more PointInstancers as part of its own geometry.  For added scalability, typically each prototype itself will be a [native, scene-level instance](https://openusd.org/release/glossary.html#usdglossary-instancing). This took several iterations to get working properly in Hydra and Katana, but now does, with the internal version of this proposed schema.
* **Must be able to sparsely 'promote' instances** - typically an environment will be laid out and referenced into sequences prior to knowing where action will take place.  Often, some number of PointInstancer-dressed models must interact with characters, which is difficult.  Therefore, we must facilitate "promoting" an instance into full, hero geometry that can be collided against, deformed, etc.  To facilitate this, the schema must minimally provide a means of sparsely pruning out certain, identified instances without needing to re-author all of the vectorized transformation-related attributes and primvars.
* **Must be able to prune instances over time for complexity reduction** - Since most "final frame" rendering is performed a single frame at a time and we want to focus available memory and compute on important scene elements, we find it useful to (roughly) prune a scene to the rendering camera's frustum.  In any sequence in which either the camera or PointInstanced elements are moving, the elements visible to the camera may change over the course of the sequence.  Since we would like the ability to precompute and cache the results of this culling operation, we must be able to make instances invisible over (potentially) only certain time intervals. 

## FX Department Needs
The FX/simulation departments often have higher scalability requirements than sets, ranging into the millions of instances.  Although the prototypes tend to be simpler in FX, each instance is typically animated (whereas instance transforms for sets are generally static), and instances may be ephemeral.  Some examples:
* Rigid body simulation of Cheetos scattering onto the floor
* Animated particulate matter in a fish tank
* Foreground grains of sand on a beach, for (very) close-up shots

The only new requirements this adds beyond those already established for sets' needs is:
* **Instances must be optionally identifiable by an integer ID, not just their position in the transform arrays** - this allows instances to retain their identity as other instances are birthed and die over time, and therefore provides a stable means of pruning instances.
* **Per-instance velocity and angular velocity** - because when the instance-set topology is not stable from frame to frame, we cannot use linear interpolation between samples to effect motion-blur.

# Schema

 **class UsdGeomPointInstancer Properties**

| Name | Type | Required | Description                         |
| ---- | ---- | -------- | ------------------------------------ |
| prototypes | [relationship](https://openusd.org/release/glossary.html#usdglossary-relationship) | Yes | Ordered targets for prototype roots; can be located anywhere in the scenegraph that is convenient, although we promote organizing prototypes as children of the PointInstancer.  Since relationships are uniform, cannot be animated. |
| protoIndices | int[] | Yes | Per instance index into 'prototypes' relationship that identifies what geometry should be drawn for this instance.  Topology attribute - can be animated, but at a potential performance impact for streaming. |
| positions | point3f[] | Yes | Per instance position.  The PointInstancer prim's [LocalToWorld transformation](https://openusd.org/release/api/class_usd_geom_imageable.html#a8e3fb09253ba63d63921f665d63cd270) is applied to these positions. |
| orientations | quath[] | No | If authored, per-instance orientation of each instance about the prototype's origin (as defined by application of the prototype's own transformation).  Expressed as a half-precision quaternion, since, although we stipulate the quaternion shall be normalized prior to consumption, we expect most clients to be authoring unit or near-unit length quaternions, for which half-precision is more than adequate. |
| scales | float3[] | No | If authored, per-instance non-uniform scale to be applied to each instance, before any rotation is applied. |
| velocities | vector3f[] | No | If authored, per-instance velocity vector to be used for motion-blurring position.  Velocities should be considered mandatory for motion-blur if **protoIndices** is animated. |
| angularVelocities | vector3f[] | No | If authored, per-instance angular velocity vector to be used for motion-blurring orientation.  Velocities should be considered mandatory for motion-blur if **protoIndices** is animated. |
| ids | int64[] | No | If authored, specifies a numeric identifier for each instance, which will be consulted for all pruning-related behaviors. If unauthored, all pruning behaviors refer simply to instances by their element index. |
| inactiveIds | listOp(int64) | No | If authored, this *metadatum* on the prim provides a [list editable](https://openusd.org/release/glossary.html#usdglossary-listediting) set of ids to prune, *over all time*, similarly to how [activation](https://openusd.org/release/glossary.html#usdglossary-active-inactive) works for prims in USD. We use this metadatum to prune instances that have been "promoted" to addressable (in the scenegraph) hero geometry. |
| invisibleIds | int64[] | No | If authored, represents a time-varying list of ids to prune.  Because invisibleIds is meant to be animated, it must be an attribute (rather than a metadatum), and therefore cannot be list-edited in stronger layers.  That means that in order to change a single sample i a stringer layer, one must re-encode the entire dataset in the layer. |
| primVars:anyName | anyType[] | No | The [UsdGeomPrimvars API's](https://openusd.org/release/api/class_usd_geom_primvars_a_p_i.html) can be used to author primvars on a PointInstancer, with the understanding that each "element" (as determined by the primvar's elementSize) is applied as a constant primvar to the instance. |

# Function and API

## Why the Level of Indirection For Prototypes?
Why not just encode the prototype of each instance as an array of strings and dispense with the linearized relationship targets?  Two reasons:

1. Strings are a fragile way to encode namespace locations, because there is no way for USD to know what strings should get special treatment to remap their values appropriately as files get referenced and namespaces get concatenated and/or renamed.
1. Relationships are list-editable, which means we can make very sparse changes non-destructively.  For example we can, in a stronger layer, swap out one prototype for another without needing to reauthor all of the *prototIndices* attribute values.

## Transformation Applied to an Instance 
For instance *i* evaluated at time *t*:

1. Apply (most locally) the authored transformation for *prototypes[protoIndices[i]]*
2. If *scales* is authored, next apply the scaling matrix from *scales[i]*
3. If *orientations* is authored: **if *angularVelocities* is authored**, first multiply *orientations[i]* by the unit quaternion derived by scaling *angularVelocities[i]* by the time differential from the left-bracketing timeSample for *orientation* to the requested evaluation time *t*, storing the result in *R*, **else** assign *R* directly from *orientations[i]*.  Apply the rotation matrix derived from *R*.
4. Apply the translation derived from *positions[i]*. If *velocities* is authored, apply the translation deriving from *velocities[i]* scaled by the time differential from the left-bracketing timeSample for *positions* to the requested evaluation time *t*.
5. Least locally, apply the transformation authored on the PointInstancer prim itself (or the [LocalToWorldTransform](https://openusd.org/release/api/class_usd_geom_imageable.html#a8e3fb09253ba63d63921f665d63cd270) of the PointInstancer to put the instance directly into world space)

## Helper API's
The schema class will include a number of helper computations:
* **Computing the 4x4 transform for each instance at a given time,** which will resolve and apply pruning, consult and apply velocity and angularVelocity if present, and utilize multiple cores for the computation when available.
* **Resolve pruning to a bitfield for a given time,** for clients that need more granular access to per-instance data (e.g. primvars), a helper will factor both *inactiveIds* and *invisibleIds* to return a bitfield whose length is the same as *protoIndices* at the given time, indicating whether each element should be considered present.  Additionally, there will be a templated function for condensing/collapsing any given VtArray in-place by such a bitfield. 
* **Bounds Computation,** Since UsdGeomPointInstancer derives from UsdGeomBoundable, it is expected that each PointInstancer prim will have an authored [extent attribute](https://openusd.org/release/api/class_usd_geom_boundable.html#abecc87b5433fec139295a78b439b0531).  To facilitate this, the schema class will provide an extent computation that instances each prototype's extent onto each instance and unions them, in the PointInstancer's local space.

# Pipeline Support for PointInstancer

## Hydra/UsdImaging
UsdImaging via Hydra supports the PointInstancer encoding, including:

* imaging nested (recursive) PointInstancers correctly
* Allow for picking and highlighting of individual instances (when PointInstancers are nested, only the instances of the top-level PointInstancer can be individually picked)  
**Limitations as of 6/1/2017**
* Does not yet honor velocities or angularVelocities in computing interpolated positions
* Does not yet properly handle inactiveIds/invisibleIds

## Houdini
The (imminent) open USD Houdini plugins will import PointInstancers to a packed prim form, and will export the same packed prim form to UsdGeomPointInstancer prims.  It can also export native Houdini instancing idioms to PointInstancer.

## Katana
PxrUsdIn translates PointInstancers into a new op/location-type *instanceArray* that preserves the spirit of vectorized instancing, which the Renderman backend (*Rfk* - renderman for katana) knows how to translate into Renderman native instancing.

## Maya
Initially, no support in Maya. We welcome contributions/ideas in this area.  Internally, we have a custom Node that roughly mirrors the data layout of a PointInstancer, which we use in our custom set-construction plugins.  If interest is strong, we will consider cleaning up and opening the custom node to allow at least import, editing, and re-export from Maya.  There are other Maya authoring tools that can produce data that could export as PointInstancers, for sure.
