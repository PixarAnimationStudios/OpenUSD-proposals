# Revise Use of Layer Metadata in USD

Copyright &copy; 2023, Pixar Animation Studios,  version 1.0

## Contents
  - [Introduction](#introduction)
  - [Layer Metadata](#layer-metadata)
  - [Three Categories of Layer Metadata, by Use](#three-categories-of-layer-metadata-by-use)

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
If we classify layer metadata by its intended use, we find three categories, one of which has proven problematic.

### Advisory Layer Metadata
Advisory layer metadata provides hints and ancillary data to clients and editors, but is generally not meaningfully consumed by the USD core. It can be _sually_ be reasonably interpreted as a statement about the stage _or_ about the root layer and, importantly, it does not critically matter which interpretation is applied.  We do not consider advisory layer metadata to be problematic; some examples of advisory layer metadata:
* `documentation`/`comment` - any layer can have a "top-level" comment string that describes the layer's contents.
* `customLayerData` - provides more structured advisory data for a layer than the comment field does.
* `framesPerSecond` - meant to be a hint to playback consumers as to the optimal rate at which to temporally sample a scene
