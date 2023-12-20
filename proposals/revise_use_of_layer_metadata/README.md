# Revise Use of Layer Metadata in USD

Copyright &copy; 2023, Pixar Animation Studios,  version 1.0

## Contents
  - [Introduction](#introduction)
  - [Layer Metadata](#layer-metadata)

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
    # 'customLayerData'

    # `defaultPrim` names a root-level prim on this STAGE for the composition engine to
    # target when no target is provided in a reference or payload arc to this layer.
    defaultPrim = "MyModel"

    # 'metersPerUnit' provides information for clients about how the linear units of
    # geometry on this STAGE should be scaled
    metersPerUnit = .01

    # 'stageVariables' is a core dictionary datum that provides named values
    # associated with a STAGE
    stageVariables = {
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
