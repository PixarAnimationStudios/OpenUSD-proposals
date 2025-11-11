# Level of Detail (LOD) API for USD

## Summary

This proposal defines an API schema for managing Level of Detail (LOD) in USD compositions. LOD systems allow engines and applications to efficiently switch between asset representations based on configurable criteria such as distance, screen size, performance heuristics, or explicit authoring. This API standardizes LOD representation, enabling runtime composition, hierarchical evaluation, and multi-domain decoupling while maintaining deterministic behavior.

## Problem Statement

USD lacks a standardized runtime LOD representation. Current workarounds (variants, payloads, custom schemas) do not provide:

- Standardized interchange of LOD data.
- Multiple LOD domains simultaneously composed (e.g., cross-fading geometry while switching physics LOD).
- Runtime evaluation and deterministic selection.

## Hierarchical LODGroups

### Overview

A **Level of Detail Group (LODGroup)** is a node in a scene hierarchy that selects among subordinate representations based on a heuristic — typically screen size, distance from the camera, or rendering cost.

In **conventional** designs, an LODGroup’s child nodes represent mutually exclusive states of the same object: only one is active at a time. The hierarchy may itself be nested — an LODGroup can contain other LODGroups. However, evaluation proceeds strictly top-down: in a hierarchy *A → B → C*, C’s heuristic is only evaluated if both A and B are active. Thus, even if C’s metric contradicts A’s (e.g., differing distance thresholds), C’s evaluation remains subordinate to A’s active range.

---

### FBX LODGroup

FBX defines **`FbxLODGroup`** nodes as part of its scene graph model, representing a container that switches among child nodes according to view-dependent heuristics. Each child entry is an **`FbxNode`** (typically a mesh or model variant) associated with a **threshold value**, which defines the distance or screen-space ratio at which the switch to that child occurs.

The key parameters are:

* **`Threshold`** — an array of floating-point values stored in the **`Distance`** property of the `FbxLODGroup`. Each value defines the transition boundary between consecutive LOD levels. For example, a model may have thresholds `[10.0, 30.0, 60.0]`, meaning:

  * LOD 0 is used when the camera is within 10 units,
  * LOD 1 between 10–30 units,
  * LOD 2 between 30–60 units, and
  * LOD 3 (the last child) beyond 60 units.

* **`DisplayLevel`** — an enumerated property (values: `Show`, `Hide`, `UseLOD`, etc.) controlling how the LODGroup behaves in viewers or exporters. When set to `UseLOD`, the switching behavior is active; otherwise, all children may remain visible for debugging or authoring purposes.

Heuristic evaluation is distance-based by default, measured along the camera’s view vector in scene units. However, FBX does not define how distances are computed; this is left to host applications (e.g., Maya or 3ds Max may interpret it differently, typically using camera-to-object center distance).

Each LODGroup may contain up to 32 children, and nested groups are supported. Evaluation proceeds hierarchically, as in other scene representations: subordinate LODGroups are only considered active if their parent LODGroup is active.

FBX allows multiple heuristics (distance, pixel coverage, custom user properties) through metadata or custom properties, but these are generally interpreted as distance-based in most DCCs.
[TODO: Cite Autodesk FBX SDK docs for `FbxLODGroup`].

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

The **`MSFT_lod`** extension — originally introduced by Microsoft — defines a formal mechanism for grouping multiple mesh primitives as successive levels of detail of a single object. The structure is simple and explicit:

* A node may contain an **`extensions.MSFT_lod`** object listing an array of node indices in order of decreasing detail (e.g., `[high, medium, low]`).
* The runtime determines which node to render based on a heuristic such as camera distance or projected screen size; however, **the extension itself does not prescribe** the selection metric or transition behavior.
* The base node remains visible when no LOD is active, ensuring backward compatibility with standard glTF viewers.

Because `MSFT_lod` is intentionally agnostic about the heuristic, it is *not strictly conventional*: it provides a hierarchical LOD structure, but leaves evaluation entirely to the consuming engine. Implementations such as **Babylon.js**, **Three.js**, and **CesiumJS** typically treat it as **distance-based** or **screen-coverage-based**, approximating the conventional model.

The extension is documented at:
[https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Vendor/MSFT_lod](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Vendor/MSFT_lod)

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

- Multi-domain support: Geometry, physics, material, or other LOD domains can coexist; the mechanism for LOD activation is generic.
- Hierarchical LOD: Parent-child propagation ensures partial hierarchies behave predictably.
- Deterministic evaluation: Activation is in recursive decent order.
- Renderer-agnostic: API defines the data; selection logic is engine-dependent.

### API Schemas

- `LodGroupAPI` (single-apply): Top-level LOD group configuration for a prim.
- `LodItemAPI` (single-apply): Defines a single selectable group Item that scopes associated members.
- `LodHeuristicAPI` (multi-apply): Defines domain-specific runtime selection logic on an Item.

---

## **Formal Definition: Hierarchical Heterogeneous LOD**

## **Definitions**

1. **LOD Domain**
    A set of LOD rules and heuristics applied to a prim hierarchy. For example, distance-driven geometric LOD constitutes a geometric domain, while an entity-presence-driven physics LOD constitutes a physics domain.
    
2. **LOD Heuristic**
    A rule that governs the activity of an **Item**.

3. **LOD item**
    A prim with a relationship to a **Group**; the **Item** may have more than one domain specific LOD **Heuristic**.

4. **Active Item**
    An **Item** is *active* at time $t$ if its domain **Heuristic** selects it for rendering or simulation.

5. **Parent-Child Relation**
    Given two **Items** $L_{parent}$ and $L_{child}$ in a hierarchy, $L_{child} \prec L_{parent}$ if activation of $L_{child}$ is conditioned on the activation of $L_{parent}$.

6. **Heterogeneous Hierarchical LOD Network**
    A set of domains ${D_1, D_2, \dots, D_n}$, within the same namespace hierarchy. **Items** are parent-child conditioned within their domain. Domains are mutually independent, in other words, although a single hierarchy exists, the activation of **Items** for a domain is uniquely conditioned.
   
7. **Rendering**
    Within this proposal, *rendering* means post-scenegraph evaluation in a domain specific engine called a **Renderer** that does not write changes back to the scenegraph through its evaluation. Renderer examples include a computer graphics image renderer such as RenderMan, an audio playback system, a real-time physics engine, and so on.

---

## **Axioms**

* **Axiom 1: Hierarchical Resolution**
  Activation is evaluated top-down within a domain. A child **Item** may only be active in its domain if its parent **Item** is also active.

* **Axiom 2: Domain Independence**
  Activation in domain $D_i$ does not affect any **Item** $D_j$ for $i \neq j$.

* **Axiom 3: Domain-Specific Conditioning**
  **Heuristics** or triggers affect only their own domain.

* **Axiom 4 Parent Activation Propagation**
  An LOD **Item** $L_c$ in domain $D_i$ is considered *eligible* for activation only if its parent $L_p$ is active; activation propagates predictably within each domain, yielding consistent runtime behavior:
  
  $$
  L_c \text{ active} \implies L_p \text{ active}, \quad L_c, L_p \in D_i
  $$

## **Implications for SchemaAPI Design.**

* Multi-domain support is safe: geometry, physics, and material LODs can coexist without interference.
* Parent-child propagation ensures that partial hierarchies do not activate unexpectedly.
* Decoupled heuristics allow runtime selection per domain while maintaining deterministic results.
* Conventional LOD as described by systems such as FBX and Collada are fully supported.
* Round tripping to schemes such as Collada where resolution is underspecified mean that determinism is imposed on import and cannot be preserved upon re-export.
* Acceleration mechanisms such as Unreal Engine's HLOD mesh clustering are supported explicitly.

---

### Schema Definitions

#### LodAPI

```python
#usda 1.0
(
    "This file describes the USD Lod API schema."
    subLayers = [
        @usd/schema.usda@
    ]
)

over "GLOBAL" (
    customData = {
        string libraryName      = "usdLod"
        string libraryPath      = "pxr/usd/usdLod"
    }
)
{
}

class "LodGroupAPI"
(
    customData = {
        string className = "GroupAPI"
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "Group"
    }
    inherits = </APISchemaBase>
    doc = """API for configuring Level of Detail (Lod) facilities on a prim.
    
    This API schema defines multiple Lod items that can be selected within the
    group, and rules for transition between them during rendering. The API is 
    applied to a prim that serves as a local root for Lod management, within a 
    hierarchy of Lod managed prims.
    
    This schema has a lodItems relationship that lists the Lod items defined
    for this prim. Each Lod item is represented by a prim with the LodItemAPI
    applied. 
    
    The schema is singleApply in order that multiple systems may independently
    specify level of detail criteria to a single prim; for example, a single prim
    may have geometry level of detail specification within it as well as physics
    level of detail.

    A Lod heuristic is specified via the LodHeuristicAPI applied to the same prim.
    
    A LodGroup may refer only to Items within its scope. This is the mechanism that
    implements hierarchy.
    """
)
{
    rel lodItems (
        doc = """Relationship to the Lod items defined for this prim.
        
        This relationship targets prims with the LodItemAPI schema applied.
        The order of the targets should match a high to low priority order.
        Empty or unresolvable references are ignored, additionally references
        to prims with no LodLevelAPI applied schema are ignored. The related prim
        must be within the Group scope.
        """
    )
}

class "LodItemAPI"
(
    customData = {
        string className = "ItemAPI"
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "Item"
    }
    inherits = </APISchemaBase>
    doc = """Declares that a primspec participates as a singular Lod item.
    
    The ordering of Lod items is determined by LodAPI:lodItems[].

    For legacy renderers that do not understand the LodGroupAPI, the
    purpose of a prim should be set to "lod" to indicate its role as a Lod Item.
    Legacy renderers won't render the prim if it is designated with "lod" purpose,
    so setting one of the items to "default" purpose is recommended to ensure at least
    one item is visible to legacy renderers. Additionally, the prim with a default
    purpose may serve in general as the initially selected Lod item before any
    heuristic evaluation is performed.
    """
)
{
}

class "LodGeometryConfigurationAPI"
(
    customData = {
        string className = "GeometryConfigurationAPI"
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "geometryConfiguration"
    }
    inherits = </APISchemaBase>
    doc = """API that configures a geometrical heuristic on an Item.
    
    This schema is applied to a prim that represents a single Lod item
    within a domain that relies on geometrical information.

    This information differs from the geometry authored within the prim; if 
    provided, it describes geometrical information that informs an Lod selection 
    heuristic in preference to an item's actual geometry.
    
    If authored, the boundingVolume relationship should govern the heuristic,
    otherwise, the center holds.
    """
    }
)
{    
    point3f center = (0.0, 0.0, 0.0) (
        doc = """The center point of this Lod Item, used for distance calculations.
        
        This value may be used by distance-based heuristics to calculate the
        distance from the camera or other reference point."""
    )
    
    rel boundingVolume (
        doc = """Optional relationship to a prim that defines the bounding volume
        for this Lod Item, used for distance or screen-size calculations. The
        bounding volume may be one of the geometry primitives, a mesh, or other
        primitive whose extent may be computed in a well defined manner."""
    )
}

class "LodHeuristicAPI"
(
    customData = {
        string className = "HeuristicAPI"
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "Heuristic"
    }
    inherits = </APISchemaBase>
    doc = """API that defines the heuristic for Item selection.
    
    This API schema defines the condition to activate an Lod Item during
    rendering. The schema supports various transition modes and can be extended 
    for specific heuristic types.
    
    The Heuristic API is meant to be advisory, signalling authoring
    intent, but not an absolute interchange contract. Different engines and
    rendering systems may have different needs, and absolute translation
    between them may be ill-posed. The Heuristic API provides consistent places
    to store consistent data, and supports interoperability to the maximum
    reasonable extent.
    
    The name of the Item the heuristic applied should indicate the system 
    domain. By convention, "graphics", "physics", "audio", and other common
    terms of art are preferred for domain names. Specific systems may name
    themselves, a "HotPotato" game engine may name an Item "HotPotatoGraphics"
    for example, and as such will not be noticed by domain engines expecting
    "graphics".
    """
)
{
    int manualLodIndex = -1 (
        doc = """When type is 'manual', this specifies the Lod index to use.
        
        This property can be time-sampled to animate Lod transitions.
        A value of -1 means use automatic selection."""
    )

    uniform token transition = "discrete" (
        allowedTokens = ["discrete", "crossFade", "morphGeometry", "dithered"]
        doc = """Advisory field: How to transition between Lod levels.
        
        - discrete: Switch immediately between levels
        - crossFade: Blend between levels using opacity
        - morphGeometry: Interpolate geometry between levels
        - dithered: Use screen-space dithering pattern

        Other choices are possible, these are common and should be used if
        applicable in preference to non-standard names for the same concepts.
        As this field is advisory, engines should accomodate the value as
        appropriate to the engine.
        """
    )
}

```

There is an open question. The **Heuristic** is multiple apply, however domain specific **Heuristics** are "subclasses", is the correct choice that they are *singleApply* or *multipleApply*?

```python
class "LodDistanceHeuristicAPI"
(
    customData = {
        string className = "DistanceHeuristicAPI"
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "distanceHeuristic"
    }
    inherits = </APISchemaBase>
    prepend apiSchemas = ["LodHeuristicAPI"]

    doc = """API that defines the Distance based Lod selection heuristic.
    
    This API schema defines how Lod levels should be selected during
    rendering or interaction on the basis of distance from the camera.
    
    The distance thresholds are grouped via minimum and maximum threshold.
    By separating these two, threshold hysteresis may be adjusted; in other
    words, the problem of flickering between two Lods is avoided by creating
    a bistable threshold to allow for slight frame-to-frame variance.
    
    The name of the prim the heuristic applied to should indicate the system 
    domain.   
    """
)
{
    uniform float[] distanceMinThresholds = [] (
        doc = """This defines the distance thresholds
        for Lod transitions in ascending order. The min treshold is consulted
        to transition from a higher Lod to a lower one.
        
        For example, [10.0, 50.0, 100.0] means:
        - Use Lod 0 when distance < 10.0
        - Use Lod 1 when 10.0 <= distance < 50.0
        - Use Lod 2 when 50.0 <= distance < 100.0
        - Use Lod 3 when distance >= 100.0

        This field is advisory and not strongly interoperable.
        """
    )
    uniform float[] distanceMaxThresholds = [] (
        doc = """This defines the distance thresholds
        for Lod transitions in ascending order. The max treshold is consulted
        to transition from a lower Lod to a higher one.
        
        See distanceMinThresholds for complementary information.

        This field is advisory and not strongly interoperable.
        """
    )
}

class "LodScreenSizeHeuristicAPI"
(
    customData = {
        string className = "ScreenSizeHeuristicAPI"
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "distanceLodHeuristic"
    }
    inherits = </APISchemaBase>
    prepend apiSchemas = ["LodHeuristicAPI"]

    doc = """API that defines the Screen Size based Lod selection heuristic.
    
    This API schema defines how Lod levels should be selected during
    rendering or interaction on the basis of the visible extent of an object
    from the perspective of the rendering camera.
    
    The distance thresholds are grouped via minimum and maximum threshold.
    By separating these two, threshold hysteresis may be adjusted; in other
    words, the problem of flickering between two Lods is avoided by creating
    a bistable threshold to allow for slight frame-to-frame variance.
    
    The name of the prim the heuristic applied to should indicate the system 
    domain.   
    """
)
{
    uniform token screenSizeMetric = "projectedArea" (
        allowedTokens = ["projectedArea", "boundingSphereSize", "custom"]
        doc = """When type is 'screenSize', this defines how screen size is calculated.
        
        - projectedArea: Use projected area in pixels
        - boundingSphereSize: Use projected bounding sphere diameter
        - custom: Use application-defined metric

        This field is advisory and not strongly interoperable.
        """
    )
    
    uniform float[] screenSizeMinThresholds = [] (
        doc = """This defines the screen size thresholds
        for Lod transitions in descending order and is consulted when transitioning
        from a higher Lod to a lower one.
        
        For example, [1000.0, 400.0, 100.0] means:
        - Use Lod 0 when screen size >= 1000.0
        - Use Lod 1 when 400.0 <= screen size < 1000.0
        - Use Lod 2 when 100.0 <= screen size < 400.0
        - Use Lod 3 when screen size < 100.0

        This field is advisory and not strongly interoperable.
        """
    )
    
    uniform float[] screenSizeMaxThresholds = [] (
        doc = """This defines the screen size thresholds
        for Lod transitions in descending order and is consulted when transitioning
        from a lower Lod to a higher one.
        
        For example, [1000.0, 400.0, 100.0] means:
        - Use Lod 0 when screen size >= 1000.0
        - Use Lod 1 when 400.0 <= screen size < 1000.0
        - Use Lod 2 when 100.0 <= screen size < 400.0
        - Use Lod 3 when screen size < 100.0

        This field is advisory and not strongly interoperable.
        """
    )
}
```

The following **Heuristics** are examples, not part of the specification. They are meant to illustrate specializations implementors may adopt for their engines.

```python
class "LodPhysicsEntityHeuristicAPI"
(
    customData = {
        string className = "PhysicsEntityHeuristicAPI"
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "physicsEntityHeuristic"
    }
    inherits = </APISchemaBase>
    prepend apiSchemas = ["LodHeuristicAPI"]

    doc = """Custom heuristic for physics Lod selection.
    
    This class is meant to be illustrative to show a general pattern. 
    Heuristics will be highly specific to particular system domains, 
    and application developers may create their own heuristic apis to 
    signal heuristics.

    Selects Lod based on whether an active entity is present in the prim or collection.
    For example, a room can switch to full physics Lod only when a player or other
    dynamic entity is inside.
    """
)
{
    rel activeEntities (
        doc = """Targets prims representing entities that trigger this Lod when present.
        
        For example, a player character, NPCs, or other dynamic objects."""
    )
    
    uniform token selectionMode = "any" (
        allowedTokens = ["any", "all"]
        doc = """Defines how multiple entities influence Lod selection:
        - any: if any entity is present, switch to this Lod
        - all: only switch if all listed entities are present"""
    )
}

class "LodFramerateHeuristicAPI"
(
    customData = {
        string className = "FramerateHeuristicAPI"
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "framerateHeuristic"
    }
    inherits = </APISchemaBase>
    prepend apiSchemas = ["LodHeuristicAPI"]

    doc = """Extension of HeuristicAPI for framerate-based Lod selection.
    
    This is another example to show how specific heuristics may be defined
    for particular systems. Application developers may create their own
    heuristic apis to signal heuristics specific to their needs.

    This API provides additional properties for controlling Lod based on
    renderer performance.
    """
)
{
    uniform float targetFramerate = 60.0 (
        doc = """Target framerate to maintain in frames per second."""
    )
    
    uniform float hysteresis = 0.2 (
        doc = """How much the framerate can fluctuate before triggering an Lod change.
        
        Expressed as a fraction of targetFramerate. For example, with a target of
        60fps and hysteresis of 0.2, Lod changes will occur when framerate falls
        below 48fps or rises above 72fps."""
    )
    
    uniform int maxLodIncrease = 1 (
        doc = """Maximum number of Lod levels to increase (reduce detail) in a
        single update."""
    )
}
```

### Usage Examples

#### Example 1: Hierarchical LOD Demo; City → Buildings → Rooms

[TODO]

#### Example 2: Vehicle Multi-domain Demo; geometry, physics, material.

[TODO]

### Implementation Considerations

These considerations are advisory to application developers. LOD selection is not performed by USD itself. If Storm implements LOD heuristics they will be specific to Storm, and similarly for any other domain specific engine.

1. **Performance**: LOD switching should be frame-deterministic and not require access to previous frame states.

2. **Integration with Game Engines**: The API is designed to be used as a data interchange format, with the execution logic handled by the renderer or engine.

3. **Edge Cases:** Empty parent LODs are evaluated normally; children render nothing if their collection is empty.

4. **Instance Handling**: For point instancing, each instance can use its own LOD switching based on its position relative to its reference point.

## Alternative Solutions Considered

1. **Concrete LOD Node Types**: The original proposal used concrete node types rather than API schemas. This approach predates API schemas which provide better extensibility and composability.

2. **Variant-Based LODs**: Using USD variants for LOD switching was considered but rejected because it lacks standardized metadata for automatic LOD selection.

3. **Payload-Based LODs**: Using payloads for LODs is another option but focuses more on load-time optimization rather than runtime LOD switching.

## Excluded Topics

1. **Automatic LOD Generation**: This proposal does not address the generation of LOD **Item** content from high-resolution models, which is considered a separate tool specific concern.

2. **Specialized Material Features**: Specialized material LOD features like on demand mip-map generation are considered tool or runtime specific concerns.

3. **Pipeline Integration**: Specific workflows for authoring and managing LODs in content creation tools are outside the scope of this proposal.

4. **General Graph LOD Relations**: Arbitrary evaluative networks not hierarchically scoped to the **Group**.