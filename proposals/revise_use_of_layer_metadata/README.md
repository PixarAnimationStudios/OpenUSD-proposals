# Revise Use of Layer Metadata in USD

Copyright &copy; 2024, Pixar Animation Studios,  version 1.0

## Contents
  - [Introduction](#introduction)
  - [Layer Metadata](#layer-metadata)
  - [Three Categories of Layer Metadata, by Use](#three-categories-of-layer-metadata-by-use)
    - [Advisory Layer Metadata](#advisory-layer-metadata)
    - [Composition Metadata](#composition-metadata)
    - [Stage Metadata](#stage-metadata)
  - [Proposal to Evolve Stage Metadata to Applied Schemas](#proposal-to-evolve-stage-metadata-to-applied-schemas)
  - [Risks](#risks)
    - [Performance of Stage-level Queries](#performance-of-stage-level-queries)
    - [Sub-root References](#sub-root-references)

## Introduction

As OpenUSD's use has grown since its initial release, especially in disciplines 
outside its initial target of animation and VFX, some elements of its design have
been exercized and leveraged beyond Pixar's initial vision for them.  One, in 
particular, has not conceptually scaled well to the complexity of scenes people now
often build.

This proposal re-examines USD's use of *layer metadata*, first explaining the various
ways in which it is currently used in USD, then noting where and why it has been 
problematic.  Finally it will provide new guidelines for when to encode a concept in 
layer metadata, and propose that several core concepts currently expressed as layer
metadata be migrated to **applied schemas**.

## Layer Metadata

Layer metadata is strongly typed by the core Sdf data schema (which can be extended
through plugins in OpenUSD), although the `dictionary` type provides more freeform 
containership in which dictionary fields can declare their element types in the USD 
document.  Following is an example demonstrating what some of the common layer metadata
look like in `usda` syntax.

```
#usda 1.0
(
    # 'customLayerData' is a dictionary provided for ad hoc or pipeline/user-specific
    # data, generally not associated with any schema.  It is the "layer equivalent" of
    # 'customData' on prims and properties
    customLayerData = {
         string ORIGINAL_AUTHORING_DCC = "maya"
         string AUTHOR = "spiff"
         string LAST_MODIFIED_DATE = "12/26/23 08:04:08"
         bool finaled = false
    }

    # `defaultPrim` names a prim on this STAGE for the composition engine to target
    # when no target is provided in a reference or payload arc to this layer.
    defaultPrim = "MyModel"

    # 'metersPerUnit' provides information for clients about how the linear units of
    # geometry on this STAGE should be scaled
    metersPerUnit = .01

    # 'expressionVariables' is a core dictionary datum that provides named values
    # associated with a STAGE
    expressionVariables = {
         string PROD = "s101"
         string SHOT = "01"
         bool IS_SPECIAL_SHOT = "`in(${SHOT}, ['01', '03', '05'])`"
         string CROWDS_SHADING_VARIANT = "baked"
    }
 
    # 'subLayers' is a core datum that provides a stack-listing of other layers to compose
    # when the composition engine consumes this layer.  This one contains examples of
    # variable expressions in sublayer asset paths.
    subLayers = [
        @`if(${IS_SPECIAL_SHOT}, "special_shot_overrides.usd")`@,
        @`"${PROD}_${SHOT}_fx.usd"`@
    ]

    # 'upAxis' is defined by the UsdGeom schema domain via plugin, and declares the cartesian
    # upAxis for the stage's geometry.
    upAxis = 'Z'
)
```

## Three Categories of Layer Metadata, by Use
If we classify layer metadata by its intended use, we find three categories, one of 
which has proven problematic.

### Advisory Layer Metadata
Advisory layer metadata provides hints and ancillary data to clients and editors, but 
is generally not meaningfully consumed by the USD core. It can _usually_ be reasonably 
interpreted as a statement about the stage _or_ about the root layer and, importantly, it 
does not critically matter which interpretation is applied.  We do not consider advisory 
layer metadata to be problematic; some examples of advisory layer metadata:
* `documentation`/`comment` - any layer can have a "top-level" comment string that
  describes the layer's contents.
* `customLayerData` - provides more structurable advisory data for a layer than the 
  comment field does.
* `framesPerSecond` - meant to be a hint to playback consumers as to the optimal rate at 
  which to temporally sample a scene

### Composition Metadata
Composition layer metadata provides per-layer inputs to the composition algorithm that 
composes layers into a Stage. It is consumed when a UsdStage is opened (or when some 
previously uncomposed portion of the scene is later surfaced, via loading, expanding 
a stage's population mask, or any editing of composition arcs, activation, or variant 
selections).  Because composition metadata in "referenced layers" is needed _only_ to
properly compose the layer into the stage, it is not problematic that when a stage is
"flattened", such metadata is lost.  Some examples of composition layer metadata include:
* `subLayers` - ordered specification of other layers that comprise the layerStack rooted at
  a particular layer.
* `expressionVariables` - inputs to variable expressions contained in the scene rooted at
  a particular layer.  Expression variables in all composition arcs and variant selections 
  are naturally "baked in" when fully flattening a stage, though note 
  [there is a desire to preserve expression variables](https://forum.aousd.org/t/stage-variables/1159)
  when flattening a **layerStack**, though this would not affect the use of any expression
  variables in referenced layers' data, thanks to the way the feature's substitutions are
  scoped.
* `defaultPrim` - specifies which prim in the rooted layerStack to use as a target for
  references and payloads when none is specified in the referencing arc.
* `timeCodesPerSecond` - provides the metric for time _in the layer that contains the metadata_,
  and is used by the composition engine to create a mapping of stage-time to layer-time for 
  every use of each layer in the composition.  This allows us to map time coordinates and
  time _values_ (for `timeCode`-valued data) for every bit of time-varying data in the scene.
  When a stage or layerStack is flattened, all time data is transformed into the temporal
  coordinate system of the root layer.

### Stage Metadata
Stage layer metadata co-opts the root layer (with the potential for a single override in the
root (only) session layer) to make a statement about all of the data contained in the scene
or stage.  This encoding for "stage data" at first seemed attractive because it eliminates
the need to pick one of potentially many root prims on which to encode information that
can reasonably be thought of as applying to the entire stage, and it is the choice Pixar 
made many years ago in Presto to encode the frame/time range of animated scenes.  It also has
the very nice properties that:
* This encoding is perfectly suited and unambiguous when considering a stage/asset
  **in isolation**, or in a uniform environment/pipeline (such as Pixar's) where the majority
  of metrics are uniform for all assets.
* When the need arises to query one of the metrics for a scene/asset that is not already
  composed in a stage in the querying application, it is very easy and economical to
  interrogate the scene or asset.

However, when we designed USD's [assetInfo feature,](https://openusd.org/dev/api/class_usd_model_a_p_i.html#Usd_Model_AssetInfo)
even though the current equivalent feature in Presto was layer-metadata based, our experience 
informed us that a prim-based encoding would be superior, because we strongly desired:
1. AssetInfo to persist at namespace asset-boundaries even when a stage is flattened
2. A simple way to access AssetInfo for referenced assets in a composed stage, i.e. not
   needing to manually inspect all of the layers in a prim's PrimStack, as one **must** do
   to retrieve stage metadata from a referenced layer. 

However, we did not apply this analysis to many other uses of stage metadata we selected for
USD's design, because, while we expected `assetInfo` to vary over a composed scene, we did not
expect `upAxis` or `metersPerUnit` to similarly vary, however experience in the broader use of
OpenUSD has proven this false.  Following is an enumeration of stage metadata we believe to be 
problematic, and why (the reason is similar for most).
* `metersPerUnit` - defines the linear metric by which to interpret geometric data in the 
  scene.  When assets with different metrics are referenced into the same scene, we advise
  applying a corrective scale on the referencing prim.  The non-composed nature of 
  stage metadata on referenced assets makes this difficult or impossible to perform and maintain
  in the face of asset changes or flattening.
* `upAxis` - follows `metersPerUnit` logic, as it also implies a corrective transformation.
* `kilogramsPerUnit` from the UsdPhysics schema domain suffers from the same non-composability
  problems.  Unlike `upAxis` and `metersPerUnit`, **there is no corrective that can be applied
  in the referencing scene to compensate for the referenced metric** if it differs from that
  of the referencing scene.  Unless we would require all consumers to check every prim for
  references and examine target layers when performing physics (which is obviously ludicrous),
  we would need to devise _an alternate encoding_ that could represent the metric on the referencing
  prim itself, and teach clients to look for that.
* `startTimeCode` and `endTimeCode` - It is possible, with referencing and animated visibility,
  to construct a scene comprised of other scenes, and when layerOffsets are applied on the
  references, the animation will be adjusted accordingly; however, the animation _range_
  encoded in these two non-composed data will not - nor will they be very accessible.
* `colorConfiguration` and `colorManagementSystem` present an ineresting case.  It would be of very
  dubious usefulness to allow either of these settings to vary over a scene... it would in fact 
  be quite problematic to force a renderer to use two differnt color configuration management
  systems in the same scene.  So they seem to be exceptional in that they are non-composition,
  non-advisory metrics data that is truly limited to global scope.  **However**, currently, the
  only way OpenUSD provides for specifying a default/fallback source colorSpace for a scene is
  _via_ an external `colorConfiguration` document.  We **do** expect for different assets to be
  created in different source colorSpaces, and we are, therefore, in precisely
  the same position as with `kilogramsPerUnit` with respect to source colorSpace.

We could provide utilities that would make it easier to account for metrics in referenced scenes
that _can_ be compensated **at the time of adding a reference to the scene/asset**, which would,
in the case of `upAxis` and `metersPerUnit`, add xformOps on the referencing prim to bring the
referenced coordinate system into the referencing coordinate system.  However, this approach has
a number of limitations:
* There are several ways to add references and payloads in USD, and these activities are not uncommon
  in pipeline scripts.  Ensuring that all such sites call an appropriate UsdUtils utility function
  seems difficult.
* Since new metrics can be a necessary part of new schemas or schema domains, this mechanism would
  need to provide its own plugin registry to allow extensions to ensure _their_ metrics are
  compensated.
* If the referenced asset changes in a way that affects a metric, _post_ adding the reference, our
  compensation will no longer be correct, and detecting this situation automatically is onerous.
* But perhaps most importantly, as we saw above, some metrics cannot be compensated with existing
  encodings, therefore requiring new/alternate/duplicate encodings to be created.

## Proposal to Evolve Stage Metadata to Applied Schemas
In addition to promoting the guidance on what concepts are safe to encode in layer metadata,
we propose, with backwards compatibility for older assets, **to migrate the stage metadata 
enumerated above into appropriate Applied schemas that can be applied to any prim**.  Without
currently-known exception, the information contained in these applied schemas is making a statement
about the subtree of namespace rooted at the prim; in other words, the properties the schemas contain 
are effectively inherited to descendant prims until reaching a prim that itself applies the same 
schema, which then becomes authoritative for its own subtree.  We will post followup proposals with 
specifics for the categories present above, which we believe are:
* **UsdSceneAPI**, containing `startTimeCode` and `endTimeCode` as `timeCode`-valued **attributes**.
  This schema will address [other concerns the community has expressed about organizing
  "top-level scene data"](https://groups.google.com/g/usd-interest/c/HpF60yzj_pI/m/EIjXW_sLBwAJ)
  as well.
* **UsdGeomMetricsAPI**, containing `metersPerUnit` and `upAxis` as attributes
* **UsdPhysicsMetricsAPI** containing `kilogramsPerUnit` as an attribute
* **UsdColorSpaceAPI** or similar schema(s) to allow for both defining new colorSpaces for use in
  the prim-rooted subtree, and specifying already-known source colorSpaces to be considered 
  in-effect for the prim-rooted subtree.

It will be incumbent on authoring applications to apply the appropriate stage-related schemas 
to any prim that is likely to be referenced into other stages, which should include all 
**defined** root prims (and OpenUSD would validate at least this much); see also the 
[Sub-root References](#sub-root-references) section in Risks, below.  

For backwards compatibility with older scenes that use the layer metadata encoding, we might
provide computations on the newly introduced schemas that will fall back to a "stage metadata" 
opinion if neither the queried prim, nor any of its ancestors, have the relevant schema applied.

It would be _possible_ to add heuristics to existing "stage-level" queries such as 
[UsdGeomGetStageUpAxis](https://openusd.org/release/api/group___usd_geom_up_axis__group.html) to 
analyze a stage's root prims to determine "the most representative" prim with an applied schema
to represent "the stage's opinion", but we believe it will be better to deprecate these
methods and encourage the use of the new, schema methods.

## Risks

### Performance of Stage-level Queries
The advantage of this proposal is that it makes it easier and more robust to determine 
relevant "metrics" that _can_ vary over a scene due to composition of disparate assets.  However,
it does sacrifice ease and speed with which the "stage-level" opinion can be determined for
any given scene, **especially** if you do not already have the scene open on a UsdStage.  In that
case, layer metadata is both perfectly robust **and** extremely lightweight to interrogate: 
it is possible to interrogate layer metadata from both `usda` and `usdc` files without accessing
very much of the asset's content.

However, in the proposed API schema encodings, we now _firstly_ need to know which prim we care about,
which we _might_ determine by opening the layer and accessing its `defaultPrim` layer metadata, but 
that is just a guess, albeit a likely one.  But more importantly, even with smart use of
[Stage Masking](https://openusd.org/release/api/class_usd_stage_population_mask.html#details) 
to compose only the one root prim we care about, a stage's root layerStack may consist of dozens to 
hundreds of root subLayers, **all of which must be opened** just to compose the one prim.  If 
those layers are lazy-access `usdc` layers, we do not expect this additional cost to be exorbitant, but
nevertheless may generally be an order(s) of magnitude degredation.

### Sub-root References
Sub-root references pose a similar issue to the "performance risk".  In the current "Stage Metadata"
encoding, sub-root references do not further degrade the referencing stage's ability to determine the
referenced metrics... although that is because it is _already_ difficult for _any_ reference: as 
described above, the referencing stage must find the layer targeted by "the correct" reference, and then
consult that layer's metadata -- whether the reference targets a root prim or not.

In the proposed applied schema encoding, when the referenced scene is "set up correctly for referencing"
it becomes straightforward for the referencing scene to access the metrics because they are composed into
the targeted prim (and is therefore also durable in the face of stage-flattening).  However, we cannot
predict which prims may be targeted in the referenced scene, and is is neither practical nor desirable
to apply the metrics redundantly to every prim in the scene.  If the referenced scene is "well formed
for root-prim referencing", then a client making a sub-root reference in another scene will need to 
**separately** compose the referenced scene in order to search up the targeted prim's 
**composed ancestors** to determine the target prim's metrics, and apply them appropriately on the 
referencing prim.  The client would be able to use [Stage Masking]([url](https://openusd.org/release/api/class_usd_stage.html#ade1d90d759a085022ba76ff910815320)) 
to compose _only_ the targetted prim and its ancestors, but this is still quite a bit more work.

We note, however, that **sub-root references must already be considered an advanced feature** with which
care must be exercized.  For example, all "inherited binding" behaviors such as UsdShade Material binding
and UsdSkel Skel Binding are already brittle in the face of sub-root referencing, for exactly the same
reason as the metrics API's would be.  Primvars authored on ancestors of a targeted geometry prim will
also "fall off" and therefore potentially change the rendered look of a targeted prim.  For these reasons,
we do not consider the additional obfuscation of data with API schemas in these cases to be a significant 
detraction.

