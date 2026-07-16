![Status:Implemented, 26.08](https://img.shields.io/badge/Implemented,%2026.08-blue)
# Level of Detail (LOD) API for USD

## Summary

This proposal defines an API schema for managing Level of Detail (LOD) in USD compositions. LOD systems allow engines and applications to efficiently switch between asset representations based on configurable criteria such as distance, screen size, performance heuristics, or explicit authoring. This API standardizes LOD representation, enabling runtime composition, hierarchical evaluation, and multi-domain decoupling while maintaining deterministic behavior.

## Problem Statement

USD lacks a standardized runtime LOD representation. Current workarounds (variants, payloads, custom schemas) do not provide:

- Standardized interchange of LOD data.
- Multiple LOD domains simultaneously composed (e.g., cross-fading geometry while switching physics LOD).
- Runtime evaluation and deterministic selection.

## Background: Hierarchical LOD Group

### Overview

Level of detail is typically implemented by a **Level of Detail Group (LOD Group),** a node in a scene hierarchy that selects among subordinate representations based on a heuristic \- typically screen size, distance from the camera, or rendering cost.

In **conventional** designs, an LOD Group’s child nodes represent mutually exclusive states of the same object: only one is active at a time. The hierarchy may itself be nested \- an LOD Group can contain other LOD Groups. However, evaluation proceeds strictly top-down: in a hierarchy *A → B → C*, C’s heuristic is only evaluated if both A and B are active. Thus, even if C’s metric contradicts A’s (e.g., differing distance thresholds), C’s evaluation remains subordinate to A’s active range.

---

### FBX LODGroup

FBX defines **`FbxLODGroup`** nodes as part of its scene graph model, representing a container that switches among child nodes according to view-dependent heuristics. Each child entry is an **`FbxNode`** (typically a mesh or model variant) associated with a **threshold value**, which defines the distance or screen-space ratio at which the switch to that child occurs.

The key parameters are:

* **`Threshold`** \- an array of floating-point values stored in the **`Distance`** property of the `FbxLODGroup`. Each value defines the transition boundary between consecutive LOD levels. For example, a model may have thresholds `[10.0, 30.0, 60.0]`, meaning:

  * LOD 0 is used when the camera is within 10 units,
  * LOD 1 between 10–30 units,
  * LOD 2 between 30–60 units, and
  * LOD 3 (the last child) beyond 60 units.


* **`DisplayLevel`** \- an enumerated property (values: `Show`, `Hide`, `UseLOD`, etc.) controlling how the LODGroup behaves in viewers or exporters. When set to `UseLOD`, the switching behavior is active; otherwise, all children may remain visible for debugging or authoring purposes.

Heuristic evaluation is distance-based by default, measured along the camera’s view vector in scene units. However, FBX does not define how distances are computed; this is left to host applications (e.g., Maya or 3ds Max may interpret it differently, typically using camera-to-object center distance).

Each LODGroup may contain up to 32 children, and nested groups are supported. Evaluation proceeds hierarchically, as in other scene representations: subordinate LODGroups are only considered active if their parent LODGroup is active.

FBX allows multiple heuristics (distance, pixel coverage, custom user properties) through metadata or custom properties, but these are generally interpreted as distance-based in most DCCs. `FbxLODGroup` documentation can be found [here](https://help.autodesk.com/view/FBX/2015/ENU/?guid=__cpp_ref_class_fbx_l_o_d_group_html).

---

### Maya LODGroup

Maya implements **LODGroups** as DAG nodes compatible with the FBX schema. When exporting to FBX, Maya maps its internal **lodGroup** node and associated **lodThreshold** attributes directly.

Heuristics in Maya are typically distance-based, measured in scene units from the active camera. Maya also provides a simple visual preview in the viewport that switches between levels dynamically based on distance.

---

### Unreal Hierarchical LOD (HLOD)

Unreal’s **Hierarchical LOD (HLOD)** system extends the conventional model by performing *prebaking* of hierarchical simplifications. Rather than switching dynamically among scene nodes at runtime, HLOD resolves the hierarchy at *build time* into merged representations that allow the renderer to stop scene traversal at the HLOD node during rendering.

In other words, all child LODs are collapsed into aggregate “proxy meshes” per cluster, and these clusters become the switchable units at runtime.

Heuristics in Unreal’s HLOD system include distance thresholds, screen size, or user-defined parameters. The system integrates with streaming and occlusion management for large-world optimization.

---

### Apple RealityKit

RealityKit currently provides **no explicit LOD mechanism**. All geometry variants must be managed manually by the developer, typically through entity replacement or material switching.

Heuristic LOD can be simulated via custom logic that monitors camera distance or screen-space size, but there is no native node or schema equivalent to `LODGroup`.

---

### Unity and Godot

Neither **Unity** nor **Godot** provides *hierarchical* LOD systems out of the box.

* **Unity**: Includes a basic **LODGroup** component supporting distance-based switching among meshes for a single object, but not nested or hierarchical LOD evaluation. Community packages (e.g., *SimpleLOD*, *HLOD*) provide hierarchical or batched alternatives for large scenes.
* **Godot**: No built-in LOD system as of Godot 4.x; LOD switching can be scripted, and several community add-ons (e.g., *Godot-HLOD*) emulate Unreal-like behavior.

---

### glTF

There is **no canonical LOD solution** in the glTF 2.0 core specification. However, related extensions such as **`EXT_mesh_gpu_instancing`** and **`EXT_meshopt_compression`** are sometimes used in combination to support engine-specific LOD management through instancing heuristics or mesh simplification pipelines.

The **`MSFT_lod`** extension \- originally introduced by Microsoft \- defines a formal mechanism for grouping multiple mesh primitives as successive levels of detail of a single object. The structure is simple and explicit:

* A node may contain an **`extensions.MSFT_lod`** object listing an array of node indices in order of decreasing detail (e.g., `[high, medium, low]`).
* The runtime determines which node to render based on a heuristic such as camera distance or projected screen size; however, **the extension itself does not prescribe** the selection metric or transition behavior.
* The base node remains visible when no LOD is active, ensuring backward compatibility with standard glTF viewers.

Because `MSFT_lod` is intentionally agnostic about the heuristic, it is *not strictly conventional*: it provides a hierarchical LOD structure, but leaves evaluation entirely to the consuming engine. Implementations such as **Babylon.js**, **Three.js**, and **CesiumJS** typically treat it as **distance-based** or **screen-coverage-based**, approximating the conventional model.

The extension is documented at: [https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Vendor/MSFT\_lod](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Vendor/MSFT_lod)

---

### Web3D / X3D

X3D (successor to VRML) defines a **`LOD`** node that implements conventional distance-based switching between child nodes. The heuristic is purely distance-based and does not support hierarchical interaction between nested LOD nodes beyond normal scene traversal order.

---

### Collada

Collada defines LOD structures under the `<extra>` and `<technique>` elements rather than through a first-class `<LOD>` node. Some DCCs and engines encode LOD data as metadata or through the `<instance_geometry>` element sequence.

Although the schema allows for LOD metadata, interpretation is application-specific, and there is **no standard heuristic or evaluation order** defined.

---

## Proposal Details

### Proposal Overview

- Multi-domain support: Imaging, physics, audio, or other LOD domains can coexist; the mechanism for LOD activation is generic.
- Hierarchical LOD: Parent-child propagation ensures partial hierarchies behave predictably.
- Deterministic evaluation: Activation is in recursive descent order.
- Renderer-agnostic: API defines the data; selection logic is engine-dependent.

### API Schemas

- `LODRootAPI` (single-apply): Marks a prim as an **LOD Root**. Its immediate namespace children are the **LOD Items**, ordered from high to low detail by their order in the composed USD scene. Holds a `lod:heuristics` relationship to one or more **Heuristic** prims and a `lod:default:index` to indicate which **Item** is the default.
- `LODHeuristic` (abstract typed prim): Base class for all LOD heuristics. Carries a `lodDomain` token identifying the domain. Not instantiated directly; use a concrete subclass.
- `LODDistanceHeuristic` (concrete typed prim, subclass of `LODHeuristic`): Selects LOD items based on distance from the viewpoint to the LOD root.
- `LODScreenSizeHeuristic` (concrete typed prim, subclass of `LODHeuristic`): Selects LOD items based on the projected screen-space size of the LOD root.
- `LODOverrideAPI` (single-apply): Defines an inherited LOD override on the prim and that affects that prim and its descendents. The override can specify that the renderer should display no **LOD Items**, all **LOD Items**, or a specific LOD index.

---

## **Formal Definition: Hierarchical Heterogeneous LOD**

## **Definitions**

1. **Rendering** and **Renderer:** Within this proposal, **Rendering** means scenegraph evaluation by a specific engine called a **Renderer** that may present or process a modified version of the scene but does not write changes back to the scenegraph through its evaluation. Renderer examples include computer graphics image renderers such as Storm or RenderMan, audio playback systems, physics engines, game engine exporters, etc. Level of Detail selections are driven entirely by the Renderers and the **LOD Heuristics** that they understand.

2. **LOD Domain:** A hint to the renderer about the intended use of a particular heuristic. A domain is identified by an `lodDomain` token on each **Heuristic** prim. For example, an image renderer may process heuristics with the “imaging” domain but may ignore “audio” or “physics”. An audio renderer may also use heuristics of the same type but ignore them unless they are in the "audio" domain.

3. **LOD Heuristic:** An abstract typed prim (`LODHeuristic`) whose concrete subclasses (e.g., `LODDistanceHeuristic`) define rules that govern the selection of an active **Item**. Not all renderers will understand or be able to use all heuristics. Heuristics that are not understood or that do not yield a suitable answer should be ignored.

4. **LOD Root:** A prim with `LODRootAPI` applied. Its immediate namespace children are the **LOD Items**. It holds an `lod:heuristics` relationship to one or more **Heuristic** prims and an `lod:default:index` attribute to indicate which **Item** is to be rendered if the heuristics do not provide an answer or are not known to the **Renderer**.

5. **LOD Item:** A namespace child prim of an **LOD Root**. Items are ordered from high to low detail by their order in the composed USD stage. Only namespace children that are active, defined, loaded, and not abstract are **LOD Items** (i.e., only the children returned by `prim.GetChildren()`).

6. **LOD Override:** An API schema with `lod:override:mode` and `lod:override:index` attributes that may inform the renderer to skip heuristics for the namespace descendents of the prim with the schema applied. The override may specify a particular LOD item, no LOD items, or all LOD items instead.

7. **Active Item:** An **Item** is *active* at time $t$ in a **Renderer** if the Renderer has used a specific **Heuristic** to select it or used the `lod:default:index` when there are no appropriate heuristics.

---

## **Implications for SchemaAPI Design.**

* Multi-renderer support is safe: imaging, audio, and physics LODs can coexist without interference.
* Parent-child propagation ensures that partial hierarchies do not activate unexpectedly.
* Decoupled heuristics allow runtime selection per renderer while maintaining deterministic results.
* Conventional LOD as described by systems such as FBX and Collada are fully supported.
* Round tripping to schemes such as Collada where resolution is underspecified means that determinism is imposed on import and cannot be preserved upon re-export.
* Acceleration mechanisms such as Unreal Engine's HLOD mesh clustering are supported explicitly.

---

### Schema Definitions

#### LOD API

```python
#usda 1.0
(
    "This files describes the USD Level of Detail (LOD) schemas."
    subLayers = [
        @usd/schema.usda@
    ]
)

over "GLOBAL" (
    customData = {
        string libraryName       = "usdLod"
        string libraryPath       = "pxr/usd/usdLod"
    }
)
{
}

class "LODRootAPI"
(
    customData = {
        string className = "RootAPI"
        string apiSchemaType = "singleApply"
    }
    inherits = </APISchemaBase>
    doc = """API for configuring Level of Detail (LOD) facilities on a prim.

    This API schema marks a prim as the root of an LOD selection hierarchy. The
    immediate namespace children of this prim are the LOD items that can be
    selected during rendering. The order of LOD item child prims in the USD stage
    determines the LOD index, from 0 to the number_of_children - 1.

    Selection of an appropriate LOD items is entirely up to the renderer that is
    processing the scene. Upon encountering an LOD root, the renderer should
    check for an LOD override (see \ref UsdLodOverrideAPI), then check for an
    appropriate heuristic using the heuristic's type and \c lod:domain value
    to select one, falling back to the \c lod:default:index value if all else
    fails. Each heuristic type will likely have a specific, unique API to query
    that heuristic for its LOD recommendation. It is then up to the renderer
    to display the selected LOD item child and not display LOD item children
    that are not selected.

    LOD heuristics are specified by heuristic prims targeted by the
    lod:heuristics relationship. The targeted heuristics are intended to be
    queried and used by the renderer.

    LOD items are generally mutually exclusive selections, though renderers may
    blend between multiple children or even display all of them when given an
    appropriate override.

    The schema is singleApply, but multiple systems may independently specify
    level of detail criteria via heuristics specified by the lod:heuristics
    relationship. For example, a single prim may have both "imaging" and
    "physics" domain heuristics; the choice of the domains to consider and the
    heuristic(s) to use is up to the renderer.

    A child or descendent of an LODRootAPI prim may itself have LODRootAPI
    applied to create nested hierarchical LOD structures.
    """
)
{
    int lod:default:index = 0 (
        doc = """The LOD item child to use if none of the heuristics are
        understood by the renderer or if none return a usable LOD.

        Consider an "audio" renderer that does not understand "imaging" domain
        heuristics. When it encounters a prim with LODRootAPI applied and only
        "imaging" domain heuristics, it should select and process the child
        indicated by lod:default:index and ignore the other children.
        """
    )
    rel lod:heuristics (
        doc = """Relationship targeting all the heuristic prims that could be
        used for this particular LOD root. The choice of which heuristic(s) will
        be used is up to the renderer.
        """
    )
}

class "LODOverrideAPI"
(
    customData = {
        string className = "OverrideAPI"
        string apiSchemaType = "singleApply"
        string extraIncludes = """
#include <optional>
"""
    }
    inherits = </APISchemaBase>
    doc = """API for overriding Level of Detail (LOD) choices.

    This API schema defines an LOD override for namespace descendents. When the
    renderer encounters a prim with LODRootAPI applied, it should first check to
    see if there is an override for the LOD domain of interest before consulting
    heuristics or the root's lod:default:index.
    """
)
{
    token lod:override:mode = "inherited" (
        allowedTokens = ["inherited", "noOverride", "indexedLOD", "noLOD", "allLOD"]
        doc = """How to apply override to LOD decisions. Valid values are:

        - __inherited__: The default. This prim does not provide any override
          information, it inherits any value set above it.
        - __noOverride__: There is explicitly no override. Use the heuristics.
        - __indexedLOD__: The lod:override:index property provides the value.
        - __noLOD__: All LOD items should be hidden.
        - __allLOD__: All LOD items should be displayed.
        """
    )
    float lod:override:index = 0 (
        doc = """The index value to use when lod:override:mode is "indexedLOD".

        If the value is outside the range of available LOD items, the renderer
        should clamp the value into range to select an appropriate LOD. If the
        value is fractional, the renderer may choose to blend or interpolate
        between multiple LOD items. Alternatively, the renderer may simply round
        the value to the nearest integer.
        """
    )
}

class "LODHeuristic"
(
    customData = {
        string className = "Heuristic"
        dictionary schemaTokens = {
            dictionary imaging = {
                string doc = """Name of the LOD domain for heuristics for
                generic imaging based renderers."""
            }
            dictionary audio = {
                string doc = """Name of the LOD domain for heuristics for
                generic audio based renderers."""
            }
            dictionary physics = {
                string doc = """Name of the LOD domain for heuristics for
                generic physics based renderers."""
            }
        }
    }
    inherits = </Typed>
    doc = """Base class for LOD Heuristics.

    Due to the varying nature of the inputs, and potentially outputs, of
    each heuristic, the method of using the heuristic and the type of
    value that it returns may be different for each type of heuristic.
    It is the responsibility of the renderer to select a heuristic (or
    heuristics) that it knows how to use, to invoke it, and to apply
    the result."""
)
{
    # The renderer will choose heuristics to evaluate based on both the domain
    # token AND the concrete heuristic prim type. Each heuristic will have its
    # own specific method for computing an LOD Index. For example, the
    # UsdLodDistanceHeuristic defines a ComputeLOD method that takes a
    # viewpoint and an object-to-worldspace transform, and returns a float. The
    # UsdLodScreenSizeHeuristic has a ComputeLOD method that takes a GfFrustum
    # instead of a viewpoint. Renderers cannot invoke methods that they do not
    # understand.
    token lod:domain (
        doc = """The "domain" of this heuristic. Predefined generic domains
        include "imaging", "physics", and "audio". Other generic domain names
        may be added in the future. If you are creating your own unique
        heuristics, it is recommended that you prefix them with your company
        or product name."""
    )
}

# The LODDistanceHeuristic and the LODScreenSizeHeuristic are proof-of-concept
# implementations. It's likely that any specific renderer may require an equally
# specific heuristic, but these are intended to be working examples that
# demonstrate the concepts while being usable enough for most simple uses.
class LODDistanceHeuristic "LODDistanceHeuristic"
(
    customData = {
        string className = "DistanceHeuristic"
        string extraIncludes = """
#include "pxr/usd/usdLod/distanceHeuristicQuery.h"
#include "pxr/usd/usdGeom/boundable.h"
"""
    }

    inherits = </LODHeuristic>
    doc = """This LOD heuristic selects LOD children on the basis of distance
    from the view point to the LOD root.

    The LOD child selected is determined by the comparing the computed
    distance with the values in thresholds and blendThresholds. Providing
    values in blendThresholds can allow the renderer to blend between
    different LOD children which can be useful to avoid flickering
    between two LODs. Alternatively, hysteresis can be employed to avoid
    changing the LOD when the distance changes by a small amount.

    The center and boundingVolume properties describe geometric information for
    the Root prim that informs the distance calculation. If boundingVolume is
    authored and has a valid extent, the distance to the nearest point on the
    extent box is used; otherwise the distance to the center is used. Both
    center and boundingVolume coordinates are assumed to be in the local
    coordinate system of the LOD root. (Note that this heuristic prim may have
    a completely different coordinate system than that of the root.)
    """
)
{
    point3f center = (0.0, 0.0, 0.0) (
        doc = """The center point of this LOD Root in local coordinates.

        This value is used to calculate the distance from the view point if the
        boundingVolume relationship does not target a Boundable prim.
        """
    )

    rel boundingVolume (
        doc = """Optional relationship to a Boundable prim that defines the
        bounding volume for this LOD Root, the prim's extent will be used for
        distance calculation if it is valid (not empty). The distance will be
        calculated from the viewpoint to the nearest point on the extent box.
        """
    )

    uniform float[] thresholds = [] (
        doc = """This defines the distance thresholds for LOD transitions in
        ascending order.

        For example, [10.0, 50.0, 100.0] means:
        - Use LOD 0 when distance < 10.0
        - Use LOD 1 when 10.0 <= distance < 50.0
        - Use LOD 2 when 50.0 <= distance < 100.0
        - Use LOD 3 when 100.0 <= distance
        """
    )

    uniform float[] blendThresholds = [] (
        doc = """This defines distance thresholds for LOD transitions in
        ascending order. If the blend threshold values are defined, then the
        calculation can return a result between two levels of detail that can be
        used to blend or combine multiple LOD items.

        For example if:
        - thresholds is [10.0, 50.0, 100.0]
        - blendThresholds is [11.0, 55.0, 110.0]

        then:
        - Use LOD 0 when distance < 10.0
        - Blend LOD 0 and LOD 1 when 10.0 <= distance < 11.0
        - Use LOD 1 when 11.0 <= distance < 50.0
        - Blend LOD 1 and LOD 2 when 50 <= distance < 55.0
        - Use LOD 2 when 55.0 <= distance < 100.0
        - Blend LOD 2 and LOD 3 when 100 <= distance < 110.0
        - Use LOD 3 when 110.0 <= distance

        The blend amount should be computed linearly between the corresponding
        thresholds and blendThresholds values. See thresholds for additional
        information. Note that blendThresholds values are clamped internally to
        the current and next thresholds values, ensuring that blending never
        occurs between more than 2 LOD children. Missing blendThresholds
        values result in no blending, just a discontinuous jump from one LOD
        child to the next.
        """
    )
}

class LODScreenSizeHeuristic "LODScreenSizeHeuristic"
(
    customData = {
        string className = "ScreenSizeHeuristic"
        string extraIncludes = """
#include "pxr/usd/usdLod/screenSizeHeuristicQuery.h"
#include "pxr/usd/usdGeom/boundable.h"
"""
    }
    inherits = </LODHeuristic>

    doc = """This LOD heuristic selects LOD children on the basis of the
    fraction of the viewplane would be covered by the extent.

    The LOD child selected is determined by the comparing the computed screen
    size with the values in thresholds and blendThresholds. Providing values in
    blendThresholds can allow the renderer to blend between different LOD
    children which can be useful to avoid flickering between two LODs.
    Alternatively, hysteresis can be employed to avoid changing the LOD when the
    distance changes by just a small amount.

    The extent and boundingVolume properties describe geometric information for
    the Root prim that informs the distance calculation. If boundingVolume is
    authored and has a valid extent, it should govern the heuristic; otherwise,
    the extent holds. Both extent and boundingVolume coordinates are assumed to
    be in the local coordinate system of the LOD root. (Note that this heuristic
    prim may have a completely different coordinate system than the root does.)
    """
)
{
    float3[] extent = [(-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)] (
        doc = """The extent of this LOD Root in local coordinates.

        This value is used to calculate the screen size from the camera if the
        boundingVolume relationship does not target a Boundable prim with a
        valid extent.
        """
    )

    rel boundingVolume (
        doc = """Optional relationship to a Boundable prim that defines the
        bounding volume for this LOD Root, used for size calculation if
        the referenced prim has a valid extent.
        """
    )

    uniform token projectionMethod = "projectedSphere" (
        allowedTokens = ["projectedExtent", "projectedSphere"]
        doc = """Defines how screen size is calculated.

        - projectedExtent: Project the extent to the view plane
        - projectedSphere: Project the extent bounding sphere to the view plane
        """
    )

    uniform float[] thresholds = [] (
        doc = """The screen size thresholds for LOD transitions in descending
        order as a fraction of the viewport size.

        For example, [0.25, 0.10, 0.025] means:
        - Use LOD 0 when the bounds cover more than 25% of the screen
        - Use LOD 1 when the bounds cover 25% or less but more than 10%
        - Use LOD 2 when the bounds cover 10% or less but more than 2.5%
        - Use LOD 3 when the bounds cover 2.5% or less of the screen

        This field is advisory and not strongly interoperable.
        """
    )

    uniform float[] blendThresholds = [] (
        doc = """This defines screen size thresholds for LOD transitions in
        descending order. The blend threshold is consulted for transitions that
        blend or combine multiple LOD items.

        For example if:
        - thresholds is [0.25, 0.10, 0.025]
        - blendThresholds is [0.20, 0.08, 0.020]

        then:
        - Use LOD 0 when size > 25%
        - Blend LOD 0 and LOD 1 when 25% >= size > 20%
        - Use LOD 1 when 20% >= size > 10%
        - Blend LOD 1 and LOD 2 when 10% >= size > 8%
        - Use LOD 2 when 8% >= size > 2.5%
        - Blend LOD 2 and LOD 3 when 2.5 >= size > 2%
        - Use LOD 3 when 2% >= size

        The blend amount should be computed linearly between the corresponding
        thresholds and blendThresholds values. See thresholds for complementary
        information.
        """
    )
}
```

### Heuristics

The schema classes `LODDistanceHeuristic` and `LODScreenSizeHeuristic` are implemented in C++ by the classes `UsdLodDistanceHeuristic` and `UsdLodScreenSizeHeuristic` respectively. They are intended to be simple, generic implementations that function well for a wide range of situations. There are also two "query" classes (`UsdLodDistanceHeuristicQuery` and `UsdLodScreenSizeHeuristicQuery`) that perform LOD calculations independent of the USD scene. The schema classes use the query classes to do the calculations. A renderer can also save a query object and use it to perform LOD calculations without consulting back to the USD scene.

The query classes have methods to compute both the metric by which the LOD index is determined and the LOD index itself. For example, `UsdLodDistanceHeuristicQuery` has both `ComputeDistance` and `ComputeLOD` methods.

#### `ComputeDistance`:

```c++
    double ComputeDistance(const GfVec3d& viewpoint,
                           const GfMatrix4d& transform) const;

    double ComputeDistance(const GfVec3d& viewpoint,
                           const GfMatrix4d& transform,
                           double prevDistance,
                           double hysteresis) const;
```

Calculate a distance given a `viewpoint` and a `transform` with optional hysteresis.

The matrix `transform` should convert from the root's local coordinate space to the viewpoint's coordinate space.  Typically, the viewpoint will be specified in world coordinates and `transform` will convert from the root's object coordinates to world coordinates.

If the overload with `prevDistance` and `hysteresis` is used, then `prevDistance` should contain the most recently calculated distance. If the newly calculated distance differs from `prevDistance` by less than `hysteresis,` then `prevDistance` is returned as the computed distance. This helps prevent flickering between LOD levels when the computed distance is very close to a threshold value.

If `transform` is close to singular or `extent` is empty, then the distance is calculated from `viewpoint` to `center`. Otherwise the distance is calculated from `viewpoint` to the closest point on the surface of `extent`.

#### `ComputeLOD`:

```c++
    float ComputeLOD(double distance) const;

    float ComputeLOD(const GfVec3d& viewpoint,
                     const GfMatrix4d& transform) const;

    float ComputeLOD(const GfVec3d& viewpoint,
                     const GfMatrix4d& transform,
                     double prevDistance,
                     double hysteresis,
                     double* distanceOut) const;
```

Calculate an LOD index given a `distance`. Convenience methods calculate the distance internally and then compute the LOD index from that. The overload that takes hysteresis will return the computed distance in the double pointed to by `distanceOut` so it can be provided in `prevDistance` on the next call.

These methods compare the distance against the values in `thresholds` to determine an LOD index. If `blendThresholds` has values and `distance` is between a `thresholds` value and its corresponding `blendThresholds` value, then the returned LOD Index will be non-integral. If the renderer can blend between 2 LOD item children then is should use the returned index as follows:

```c++
   // compute distance if it was not provided as an argument

   float index = heuristic.CalculateLOD(distance);
   if (blending_between_LOD_levels_is_active) {
       int lowIndex = int(std::floor(index));
       int highIndex = int(std::ceil(index));
       float alpha = index - lowIndex;

       // Display a linear interpolation using:
       //   (1-alpha) * item[lowIndex] + alpha * item[highIndex]
   } else {
       int index = int(std::round(index))

       // Display item[index]
   }
```

If `blendThresholds` is not set then only integer valued results will ever be returned.

`UsdLodDistanceHeuristic` has almost the same methods as the query class but they all take an additional, optional argument `time` that defaults to `UsdTimeCode::Default()` because potentially the values in the scenegraph can change over time.

#### Screen Size Heuristic

`UsdLodScreenSizeHeuristicQuery` has corresponding methods that compute a fractional screen size from a viewing frustum instead of a distance from a viewpoint.

```c
    double ComputeScreenSize(const GfFrustum& frustum,
                             const GfMatrix4d& transform) const;

    double ComputeScreenSize(const GfFrustum& frustum,
                             const GfMatrix4d& transform,
                             double prevSize,
                             double hysteresis) const;

    float ComputeLOD(double size) const;

    float ComputeLOD(const GfFrustum& frustum,
                     const GfMatrix4d& transform) const;

    float ComputeLOD(const GfFrustum& frustum,
                     const GfMatrix4d& transform,
                     double prevSize,
                     double hysteresis,
                     double* sizeOut) const;
```

And like `UsdLodDistanceHeuristic`, `UsdLodScreenSizeHeuristic` has those same methods with an additional, optional `time` argument.

### Computing LOD Indices

When a renderer encounters a prim with the `LODRootAPI` applied, it needs to determine how to select an appropriate LOD item child. In general the renderer will:

1. Check for an LOD override and use it if found.
2. Select an appropriate heuristic from among the targets of `lod:heuristics` and invoke methods on that heuristic to select a LOD item.
3. If no appropriate heuristic returns an answer, select the LOD item child indicated by `lod:default:index`.
4. It is up to the renderer to then ensure that the selected LOD item is displayed/processed and that its siblings are not. For an imaging renderer, this probably means treating the selected child as if it were visible and its siblings are invisible. For an audio renderer it would make them audible and inaudible. Etc.

The `LODOverrideAPI` schema provides a C++ and Python callable method to check for an override.

```c++

    if (prim->HasAPI<UsdLodRootAPI>()) {
        float lod = _GetLODForPrim(prim);
        ...
    }

// Magic values for convenient return from GetLODForPrim. These represent an
// error or an override that wants to show no LOD items or all LOD items.
constexpr float INVALID_LOD = -999.0;
constexpr float NO_LOD = -998.0;
constexpr float ALL_LOD = -997.0;

// hypothetical method for a renderer to get an LOD value. The variables
// currentTime, currentViewpoint, currentViewFrustum, and currentTransform
// are presumed to be members of class Renderer.
float Renderer::_GetLODForPrim(const UsdPrim& prim,
                               const TfToken& targetDomain)
{
    UsdLodRootAPI rootAPI(prim);
    if (!rootAPI) {
        // This is not an LOD root!
        return -1.0;
    }

    // ComputeLODOverride will walk up the hierarchy to search for an
    // override to inherit.
    float overrideIndex = INVALID_LOD;
    TfToken overrideMode =
        UsdLodOverrideAPI(prim).ComputeLODOverride(&overrideIndex);

    if (overrideMode != UsdLodTokens->noOverride) {
        if (overrideMode == UsdLodTokens->indexedLOD) {
            return overrideIndex;
        } else if (overrideMode == UsdLodTokens->noLOD) {
            return NO_LOD;
        } else if (overrideMode == UsdLodTokens->allLOD) {
            return ALL_LOD;
        } else {
            return INVALID_LOD;
        }
    }

    SdfPathVector targetPaths;
    UsdRelationship heuristicsRel = rootAPI.GetLodHeuristicsRel();
    heuristicsRel.GetForwardedTargets(&targetPaths);

    for (const auto& path : targetPaths) {
        const UsdPrim targetPrim = prim.GetStage()->GetPrimAtPath(path);
        UsdLodHeuristic heuristic(targetPrim);
        UsdAttribute lodDomainAttr = heuristic.GetLodDomainAttr();

        TfToken domain;
        if (!lodDomainAttr.Get(&domain, currentTime) ||
            domain != targetDomain)
        {
            // Not an targetDomain heuristic
            continue;
        }

        // check for known heuristic types
        if (auto distHeuristic = UsdLodDistanceHeuristic(heuristic)) {
            return distHeuristic.ComputeLOD(currentViewpoint,
                                            currentTransform,
                                            currentTime);

        } else if (auto sizeHeuristic = UsdLodScreenSizeHeuristic(heuristic)) {
            // members of class Renderer
            return (sizeHeuristic.ComputeLOD(currentViewFrustum,
                                             currentTransform,
                                             currentTime));
        }
    }

    // None of the heuristics were suitable.
    int index = 0;
    rootAPI.GetLodDefaultIndexAttr().Get(&index, currentTime);

    // index is unchanged if Get() failed. Just return 0 in that case.
    return float(index);
}
```

### Other Examples

The following hypothetical **Heuristics** are examples, not part of the specification. They are meant to illustrate possible specializations that implementers may adopt for their engines.

```py
class LODPhysicsEntityHeuristic "LODPhysicsEntityHeuristic"
(
    customData = {
        string className = "PhysicsEntityHeuristic"
    }
    inherits = </LODHeuristic>

    doc = """Custom heuristic for physics LOD selection.

    This class is meant to be illustrative to show a general pattern.
    Heuristics will be highly specific to particular system domains,
    and application developers may create their own heuristic subclasses
    for particular metrics.

    Selects LOD based on whether an active entity is present in the prim
    or collection. For example, a room can switch to full physics LOD only
    when a player or other dynamic entity is inside.
    """
)
{
    rel activeEntities (
        doc = """Targets prims representing entities that trigger this LOD
        when present.

        For example, a player character, NPCs, or other dynamic objects."""
    )

    uniform token selectionMode = "any" (
        allowedTokens = ["any", "all"]
        doc = """Defines how multiple entities influence LOD selection:
        - any: if any entity is present, switch to this LOD
        - all: only switch if all listed entities are present"""
    )
}

class LODFramerateHeuristic "LODFramerateHeuristic"
(
    customData = {
        string className = "FramerateHeuristic"
    }
    inherits = </LODHeuristic>

    doc = """Subclass of LODHeuristic for framerate-based LOD selection.

    This is another example to show how specific heuristics may be defined
    for particular systems. Application developers may create their own
    heuristic subclasses to signal heuristics specific to their needs.

    This heuristic provides additional properties for controlling LOD based
    on renderer performance.
    """
)
{
    uniform float targetFramerate = 60.0 (
        doc = """Target framerate to maintain in frames per second."""
    )

    uniform float hysteresis = 0.2 (
        doc = """How much the framerate can fluctuate before triggering
        an LOD change.

        Expressed as a fraction of targetFramerate. For example, with a
        target of 60fps and hysteresis of 0.2, LOD changes will occur
        when framerate falls below 48fps or rises above 72fps."""
    )

    uniform int maxLodIncrease = 1 (
        doc = """Maximum number of LOD levels to increase (reduce detail)
        in a single update."""
    )
}
```

### Legacy or Naive Renderers

Existing renderers obviously do not yet understand how to process the LOD schemas so it is important to construct scene graphs that can be processed correctly even when the schemas are not understood.

Consider a scenario where there is an LOD root (`.../Root`) with 3 child items (`.../Root/High`, `.../Root/Medium`, and `.../Root/Low`). The root has the `LODRootAPI` schema applied to it so it has a `lod:default:index` property that we’ll set to 0 (the 0th child) and a `lod:heuristics` relationship that targets an `LODDistanceHeuristic`.

In the case of an LOD-aware, interactive renderer like a future version of Storm, all 3 children would be in memory and the renderer would use the distance heuristic to get an LOD index. It is then up to the renderer to operate as if the visibility, transparency, presence or other properties were modified for `.../Root/High`, `.../Root/Medium`, and `.../Root/Low` so as to display the selected child and to skip the others. The renderer should only override properties of the LOD index children themselves, for example changing the visibility from “invisible” to “inherited”. This would not make the child visible if any of its ancestor prims were invisible. All such overrides are internal to the renderer for purposes of rendering the correct LOD Item and do not affect the scene graph itself.

Renderers may also be aware of LOD schemas but may not understand the specific heuristics or the domain that is being used. An audio renderer may not process “imaging” domain heuristics or may not understand a game engine’s frames-per-second heuristic. In this case, the renderer should look at the `lod:default:index` property on the root and process only the child that is referred to by that default. If `lod:default:index = 0` then the renderer should traverse through the 0th child, `.../Root/High`, and disregard the other children.

Legacy renderers are anything that processes the scene graph that has not been updated to process scenes with LOD information in them. Authors should construct scenes in a manner that allows legacy renderers to process something reasonable. For example, if the LOD root has `lod:default:index = 0` set, then the 0th child should have `visibility = “inherited”` and the other children should have `visibility = “invisible”`. An LOD-aware renderer will override those properties on the LOD item children but a naive render will simply process them as they are. LOD items for other domains should have other appropriate properties set (e.g., `volume` for audio prims).

### Usage Examples

#### Example 1: Hierarchical LOD Demo; City → Buildings → Rooms

\[TODO\]

#### Example 2: Vehicle Multi-domain Demo; imaging, physics

\[TODO\]

### Implementation Considerations

These considerations are advisory to application developers. LOD selection is not performed by USD itself. If Storm implements LOD heuristics they will be specific to Storm, and similarly for any other domain specific engine.

1. **Performance**: LOD switching should be frame-deterministic and not require access to previous frame states.
2. **Integration with Game Engines**: The API is designed to be used as a data interchange format, with the execution logic handled by the renderer or engine.
3. **Edge Cases:** Empty parent LODs are evaluated normally; children render nothing if their collection is empty.
4. **Instance Handling**: For point instancing, each instance can use its own LOD switching based on its position relative to its reference point.

## Alternative Solutions Considered

1. **Concrete LOD Node Types**: The original proposal used only concrete node types.  Using an API schema for the **LOD Root** provides better flexibility in the construction of your model hierarchies.
2. **Variant-Based LODs**: Using USD variants for LOD switching was considered but rejected because it lacks standardized metadata for automatic LOD selection.
3. **Payload-Based LODs**: Using payloads for LODs is another option but focuses more on load-time optimization rather than runtime LOD switching.

## Excluded Topics

1. **Automatic LOD Generation**: This proposal does not address the generation of LOD **Item** content from high-resolution models, which is considered a separate tool specific concern.
2. **Specialized Material Features**: Specialized material LOD features like on demand mip-map generation are considered tool or runtime specific concerns.
3. **Pipeline Integration**: Specific workflows for authoring and managing LODs in content creation tools are outside the scope of this proposal.
4. **General Graph LOD Relations**: Arbitrary evaluative networks not hierarchically scoped to the **Root**.
