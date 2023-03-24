# PickAPI
Copyright &copy; 2023, NVIDIA Corporation, version 1.0

## Overview
This document defines picking as mouse / controller driven interaction with one or more prims through interactive rendering of the scene. Picking encompasses both point-and-click and sweep interactions. Picking is often accelerated through the use of the rendering toolkit, such as a pick buffer or a bounding volume hierarchy.

In most contexts, picked objects are converted into the application's selection state.

This document proposes a specification for customized prim picking behavior to benefit the interchange of a variety of scenes and assets in USD.

## Motivation
### Interactive Scenes
A designer of an interactive scene might want to limit picking inside of a room to a set of specific scopes. While objects may not be pickable, the designer may still choose to have them occlude picking of other objects (ie. Walls shouldn't be pickable, but picking shouldn't resolve objects behind walls).

### Performance
Asset builders may want to improve selection speed for consumers by removing expensive to render prims from pick buffers. Downstream consumers understand and expect that these objects will both not be pickable and not occlude picking (ie. Rendered fur on a character may be invisible to picking, allowing the underlying surface to be picked).

### Retargeting
Asset builders may be aware of important scopes made up of multiple gprims, say a group of prims representing a door. They understand that downstream users picking the door knob are generally trying to rotate the entire door and would benefit from retargeting the pick to the rotatable root prim.

## Proposal
To describe high level, customized primitive pick behavior, provide a `PickAPI` schema in `UsdUI`. This schema describes two key functions [visibility](#visibility) and [retargeting](#retargeting).

This proposal distinguishes between pick specialization and [application selection modes](#relationship-to-application-selection-modes). Selection modes are user interface options that apply to the entire scene and cannot be practically encoded on every prim in the scene.

The `PickAPI` should only be applied to `Imageable` prims (ie. `UsdGeom` and `UsdVol` but not `UsdShade`).

### Visibility
```
uniform token pick:visibility = "inherited" (allowedTokens = ["inherited", "invisible"])
```
`pick:visibility` controls whether or not the object should be considered visible with respect to any picking operation. Objects `invisible` to picking should be excluded from any picking calculations (and acceleration structures like BVHs or pick buffers). Prims should only be included in the pick buffer if they are imaged, taking into account `visibility`, `purpose`, and any other viewport render settings.

Because picking is often accelerated through the rendering toolkit, it's important to describe picking on its terms.

If the `PickAPI` is applied to multiple sites in a hierarchy, `pick:visibility` has pruning semantics similar to the `visibility` attribute. If a prim is invisible to picking, so are its descendants.

To make an object _unpickable_ but still participate in calculations as a matte occluder, users must use [retargeting](#retargeting-for-pick-occluders).

`pick:visibility` may not be animated.

In this current proposal, sending geometry to a pick buffer that is not actively imaged is currently out of scope. One hypothetical use case would be interactive picking of volumetrics. A user might provide a mesh to be used as the pick target for a dense volumetric cloud. This proposal doesn't provide a path for including non-imageable geometry in picking because the semantics become somewhat confusing and complicates implementations leveraging rendering pipelines.

### Retargeting

```
uniform token pick:retargeting = "none" (allowedTokens = ["none", "replace"])
rel pick:targets
```
These attributes control whether or not to forward picking to alternative targets. The default behavior (`none`) is to not forward picking. However, if `replace` is selected, all descendant prim selections will be replaced with `pick:targets`.

If the `PickAPI` is applied to multiple sites in a hierarchy, the retargeting behavior will be defined by the nearest applied ancestor. This is notably different than the pruning semantics of `pick:visibility`. As specified, retargeting could be set to `none` in a descendant, overriding any ancestral retargeting opinions.

Targets will usually include one or more prims, but may include one or more properties. If a relationship is targeted, standard relationship forwarding should be applied. If an attribute is targeted, that attribute should be selected if meaningful, otherwise the attribute's parent prim. There is no way to use the `PickAPI` to retarget selection to a relationship.

#### Retargeting for Pick Occluders
If targets is empty, no prims will be selected, and the hierarchy will act as a matte occluder. Utilities (say `UsdUIPickAPI(prim).OccludeOnly()`) can be used to explicitly set `pick:visibility` to `inherited`, `pick:retargeting` to `replace`, and `pick:targets` to an empty list.

#### Retargeting Descendants
If targets is set to `<.>`, the `PickAPI` will naturally retarget to the prim on which the schema was applied. Utilities (say `UsdUIPickAPI(prim).TargetSelf()`) can be used to explicitly set `pick:visibility` to `inherited`, `pick:retargeting` to `replace`, and `pick:target` to `<.>`.


### Relationship to Application Selection Modes
The proposed schema aimed at customizing viewport picking but and not for implementing workflow-based selection modes.

For example, a user may enter various application selection modes:
* Filter picking by schema (ie. make lights not pickable)
* Select the bound materials of the picked hierarchy
* Select the points of the picked object
* Select ancestral component model

Implementing all these features as variants with different `PickAPI` settings would result in an explosion of variants. Interest in cross-platform standardization of selection modes should be handled by utilities and specifications external to this schema.

 Selection modes should in general operate on top of the `PickAPI`. Since pick visibility is pruning and respects all other visibility settings, the order of application doesn't strictly matter. Selection modes that engage in retargeting behavior should clearly document their relationship to the `PickAPI`. This proposal recommends that schema pick retargeting should be applied, followed by application selection mode. (ie. select bound materials of `/picked/prim.pick:targets` not `/picked/prim`). If there are practical reasons where the schema defined pick mode need to be ignored (ie. explicit point sculpting of meshes), the interface or documentation should aim to communicate that the `PickAPI` will intentionally be ignored.

Applications that do not support the `PickAPI` and its features should try to issue warnings when they observe it being applied.

Implementers should consider the implications of this API being applied to a wide variety of prims in a hierarchy, assembly or component models, point instancers, gprims, and geom subsets.

The `PickAPI` strictly customizes behavior from viewport picking. It should not be used to customize selection behavior in scene graph tree views and other widgets. However, widgets and interfaces may choose to reference the `PickAPI` in filtering and display of pickable scopes.

## Applied Examples
### Fur (Visibility)
Consider the case where fur curves are affecting picking of the underlying mesh.
```
def Xform "Cat" {
    def Mesh "Body" { ... }
    def BasisCurves "Fur" (
        append apiSchemas = "PickAPI"
    ) {
        uniform token pick:visibility = "invisible"
    }
}
```

### Forest of Trees (Retargeting)
It may be hard to generalize point instancer picking behavior, especially
when considering departmental usage variation and nesting of point instancers.
To ensure that the 'Leaves' point instancer is always picked, this example uses
retargeting.
```
def Xform "VeryLargeForest" {
    def PointInstancer "OakTrees" {
        rel prototypes = <./OakTree_1>
        def Xform "OakTree_1" {
            def Mesh "Trunk" { ... }
            def PointInstancer "Leaves" (
                append apiSchemas = "PickAPI"
            ) {
                token pick:visibility = "inherited"
                token pick:retargeting = "replace"
                rel pick:targets = <.>

                rel prototypes = <./Leaf_1>
                def "Leaf_1" { ... }
            }
        }
    }
}
```

### Room (Retargeting, Inheritance, and Invisibility)
This example demonstrates custom picking behavior for several scopes.
- Use retargeting to suppress picking of prims
- Overriding retargeting when nesting `PickAPI` application
- Using guide geometry as a target for unpickable prims

```
# The room specifies that by default, prims are visible to picking (if imaged)
# but that they should retarget to an empty list. By default, objects in the
# room act as pick occluders.
def Xform "Room" (
    append apiSchemas = "PickAPI"
) {
    uniform token pick:visibility = "inherited"
    uniform token pick:retargeting = "replace"
    rel pick:targets = []

    def Xform "Walls" {
        def Mesh "NorthWall" { ... }
        def Mesh "SouthWall" { ... }
        def Mesh "EastWall" { ... }
        def Mesh "WestWall" { ... }
    }

    # The door overrides the retargeting behavior so that it and all its
    # descendants are pickable and retarget to the rotatable 'DoorGroup'
    def Xform "DoorGroup" (
        append apiSchemas = "PickAPI"
    ) {
        uniform token[] xformOpOrder = ["xformOp:rotateZ"]
        double xformOp:rotateZ = 0.0

        uniform token pick:visibility = "inherited"
        uniform token pick:retargeting = "replace"
        rel pick:targets = <.>

        def Mesh "Door" { ... }
        def Mesh "DoorKnob" { ... }
        def Mesh "DoorKnocker" { ... }
    }

    # The window makes its glass not pickable by default but provides a
    # tiny sphere collocated with Glass to be used as a pick target by
    # users when guides are enabled.
    def Xform "Window" {
        def Mesh "Frame" { ... }
        def Mesh "Glass" (
            append apiSchemas = "PickAPI"
        ) {
            uniform token pick:visibility = "invisible"
        }
        def Sphere "GlassPickTarget" (
            append apiSchemas = "PickAPI"
        ) {
            uniform token purpose = "guide"
            uniform token pick:visibility = "inherited"
            uniform token pick:retargeting = "replace"
            rel pick:targets = <../Glass>
        }
    }
}
```

## Questions
* This proposal does not address support for `UsdGeomSubset`. Visibility and purpose are currently not supported by subsets, so it may be hard to support the visibility attribute. However, one can imagine a desire for using face sets to describe pick retargeting.
* Should pick visibility and and pick retargeting be two separate APIs? One could imagine tools providing facility for controlling pick visibility but not supporting retargeting. One could also imagine prims like `UsdGeomSubset` not supporting pick visibility but supporting pick retageting. One challenge with this formulation is identifying whether the visibility or retargeting schemas are responsible for describing pick occluders without creating ambiguity.
* Is `UsdUI` the right place for viewport behavior schemas?
* Can the PickAPI subsume or clarify the responsibilities of the proxyPrim relationship? Does it conflict at all with that relationship?
* Are the rules for hierarchies with multiple applied PickAPIs consistent and expressive?
* This proposal considered an `append` retargeting mode to accumulate ancestral targets but didn't find a practical example. Relationship forwarding could be used to express this more explicitly in the current formulation. Are there other "retargeting" modes that would be useful?
* This schema views picking through the lens of authoring static scenes and not on picking as a potential event trigger (say, playback of an animation when a scope is picked). Does this schema complicate event triggers? Does it complement it? Or would this schema simply not be used in those contexts?