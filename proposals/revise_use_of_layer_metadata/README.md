# Revise Use of Layer Metadata in USD

Copyright &copy; 2023, Pixar Animation Studios,  version 1.0

## Contents
  - [Introduction](#introduction)
  - [Layer Metadata](#layer-metadata)
  - [Three Categories of Layer Metadata, by Use](#three-categories-of-layer-metadata-by-use)
    - [Advisory Layer Metadata](#advisory-layer-metadata)
    - [Composition Metadata](composition-metadata)
    - [Stage Metadata](stage-metadata)

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

    # `defaultPrim` names a root-level prim on this STAGE for the composition engine to
    # target when no target is provided in a reference or payload arc to this layer.
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
is generally not meaningfully consumed by the USD core. It can be _sually_ be reasonably 
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
Stage layer metadata coopts the root layer (with the potential for a single override in the
root (only) session layer) to make a statement about all of the data contained in the scene
or stage.  This encoding for "stage data" at first seemed attractive because it eliminates
the need to pick one of potentially many root prims on which to encode information that
can reasonably be thought of as applying to the entire stage, and it is the choice Pixar 
made many years ago in Presto to encode the frame/time range of animated scenes.

When we designed USD's [assetInfo feature,](https://openusd.org/dev/api/class_usd_model_a_p_i.html#Usd_Model_AssetInfo)
even though the current equivalent feature in Presto was layer-metadata based, our experience 
informed us that a prim-based encoding would be superior, because we strongly desired:
1. AssetInfo to persist at namespace asset-boundaries even when a stage is flattened
2. A simple way to access AssetInfo for referenced assets in a composed stage, i.e. not
   needing to manually inspect all of the layers in a prim's primIndex, as one **must** do
   to retrieve stage metadata from a referenced layer.

However, we did not apply this analysis to many other uses of stage metadata we selected for
USD's design.
