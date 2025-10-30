# Level of Detail (LOD) API for USD

## Summary

This proposal defines an API schema for managing Level of Detail (LOD) in USD compositions. LOD systems allow engines and applications to efficiently switch between asset representations based on configurable criteria such as distance, screen size, performance heuristics, or explicit authoring. This API standardizes LOD representation, enabling runtime composition, hierarchical evaluation, and multi-domain decoupling while maintaining deterministic behavior.

## Glossary

- **LOD (Level of Detail)**: A representation of an object at a specific resolution or fidelity.
- **LOD Switching**: Process of changing between LODs according to specified rules.
- **Transition Rules**: Functions and thresholds that determine when LODs switch.
- **Applied API Schema**: A USD schema applied to prims to extend functionality.
- **LOD Domain**: A set of LOD levels and heuristics applied to a prim hierarchy.
- **Active Level**: The currently selected LOD level in a domain.
- **Parent-Child Relation**: A child LOD’s activation is conditioned on its parent’s activation.
- **Heterogeneous Hierarchical LOD Network**: Multiple independent LOD domains coexisting on a prim hierarchy.

## Problem Statement

USD lacks a standardized runtime LOD representation. Current workarounds (variants, payloads, custom schemas) do not provide:

- Standardized interchange of LOD data.
- Multiple LOD domains simultaneously composed (e.g., cross-fading geometry while switching physics LOD).
- Runtime evaluation and deterministic selection.

## Existing Implementations & Reference Documents

- Game engines implement LOD systems
    - many common features to these systems such as distance from the camera switching
    - many unique features specific to singular engine capabilities
- Previous proposals have explored node-based approaches (see originalProposal.md)
- USD's Collections API provides a pattern for targeting sets of prims that we can leverage

## Proposal Details

### Proposal Overview

- Multi-domain support: Geometry, physics, material, or other LOD domains can coexist.
- Hierarchical LOD: Parent-child propagation ensures partial hierarchies behave predictably.
- Deterministic evaluation: Activation is frame-deterministic.
- Renderer-agnostic: API defines the data; selection logic is engine-dependent.

### API Schemas

- `LodConfigurationAPI` (multi-apply): Top-level LOD configuration for a prim, supports multiple domains.
- `LodLevelAPI` (multi-apply): Defines individual LOD levels and associated members.
- `LodHeuristicAPI` (single-apply): Defines domain-specific runtime selection logic.

---

## **Formal Definition: Hierarchical Heterogeneous LOD**

## **Definitions**

1. **LOD Domain** $D$
   A set of LOD rules and heuristics applied to a prim hierarchy. For example, distance-driven geometric LOD constitutes a domain $D_1$, while entity-presence-driven physics LOD constitutes a domain $D_2$.

2. **LOD Level** $L \in D$
    A collection of prims within a domain that share the same LOD criteria.

3. **Active Levels**
   A level $L \in D$ is *active* at time $t$ if its domain heuristic selects it for rendering or simulation.

4. **Parent-Child Relation**
   Given two levels $L_p$ and $L_c$ in a hierarchy, $L_c \prec L_p$ if activation of $L_c$ is conditioned on the activation of $L_p$.

5. **Heterogeneous Hierarchical LOD Network.**
   A set of domains ${D_1, D_2, \dots, D_n}$, each with independent hierarchies and heuristics. Levels are parent-child conditioned withint their domain;  domains are mutually independent unless explicitly coupled.

---

## **Axioms**

* **P1: Hierarchical Resolution**
  Activation is evaluated top-down within a domain. A child level may only be active if its parent is active.

* **P2: Domain Independence**
  Activation in domain $D_i$ does not affect any $D_j$ for $i \neq j$, except through explicit cross-domain heuristics.

* **P3: Domain-Specific Conditioning**
  Heuristics or triggers affect only their own domain.

* **P4 Parent Activation Propagation**
  An LOD level $L_c$ in domain $D_i$ is considered *eligible* for activation only if its parent $L_p$ is active; activation propagates predictably within each domain, ensuring consistent runtime behavior:
  
  $$
  L_c \text{ active} \implies L_p \text{ active}, \quad L_c, L_p \in D_i
  $$

## **Implications for API Design.**

* Multi-domain support is safe: geometry, physics, and material LODs can coexist without interference.
* Parent-child propagation ensures that partial hierarchies do not activate unexpectedly.
* Decoupled heuristics allow runtime selection per domain while maintaining deterministic results.

## **Summary.**

* `LodAPI` as a multi-apply schema to handle multiple domains per prim.
* `LodLevelAPI` to define ordered levels with hierarchical relationships.
* `LodHeuristicAPI` to provide domain-specific, runtime-deterministic selection logic.

Together, they ensure that hierarchical LOD evaluation is predictable, efficient, and extensible across multiple asset types and runtime systems.


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
        string libraryName      = "UsdLod"
        string libraryPath      = "pxr/usd/UsdLod"
        #string libraryPrefix    = "UsdLod"
        #string tokensPrefix     = "UsdLod"
    }
)
{
}

class "ConfigurationAPI"
(
    inherits = </APISchemaBase>
    doc = """API for configuring Level of Detail (LOD) facilities on a prim.
    
    This API schema provides the a way to define multiple LOD levels for a prim
    and rules for transition between them during rendering. It is expected to be 
    applied to a prim that serves as the root for LOD management, within a 
    hierarchy of LOD managed prims.
    
    This schema leverages collections to define sets of geometry for different
    detail levels, and provides properties to control LOD selection via 
    specified heuristics.
    
    The schema is multipleApply in order that multiple systems may independently
    specify level of detail criteria to a single prim; for example, a single prim
    may have geometry level of detail specification within it as well as physics
    level of detail.
    """

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "Configuration"
    }
)
{
    uniform token levelType = "none" (
        doc = """Names the system that consumes this LOD application.
        
        By convention, certain systems should reflect the singular form
        of the common term of art for the system, including,
        "geometry", "material", "lighting", "collision", "volume", and "physics"."""
    )
    
    rel lodLevels (
        doc = """Relationship to the LOD levels defined for this prim.
        
        This relationship targets prims with the LodLevelAPI applied.
        The order of the targets should match a high to low priority order.
        Empty or unresolvable references are ignored, additionally references
        to prims with no LodLevelAPI applied schema are ignored."""
    )
    
    rel heuristic (
        doc = """Relationship to the heuristic used for LOD selection.
        
        This relationship targets a prim with the LodHeuristicAPI applied.
        If no heuristic is specified, no automatic LOD switching will occur."""
    )
}

class "LevelAPI"
(
    inherits = </APISchemaBase>
    doc = """Defines a single LOD level for a prim, owning a collection of member prims.
    
    Each LOD level contains a collection of prims that participate in this level. 
    The ordering of LOD levels is determined by LodAPI:lodLevels[]."""
    
    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "Level"
    }
)
{
    rel members (
        doc = """Targets a prim with a collection defining the members of this LOD level.
        
        Typically the collection:content:includes attribute on the target defines
        the geometry, room, or other prims participating in this LOD level.
        Empty collections are ignored."""
    )
}


class "GeometryConfigurationAPI"
(
    inherits = </APISchemaBase>
    doc = """API that configures a single LOD level within an LOD group.
    
    This multi-apply API schema allows defining multiple LOD levels for a prim."""

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "geometryConfiguration"
    }
)
{    
    point3f center = (0.0, 0.0, 0.0) (
        doc = """The center point of this LOD level, used for distance calculations.
        
        This value may be used by distance-based heuristics to calculate the
        distance from the camera or other reference point."""
    )
    
    bool isCollisionGeometry = false (
        doc = "Indicate whether the geometry is meant as collision geometry"
    )
    
    rel boundingVolume (
        doc = """Optional relationship to a prim that defines the bounding volume
        for this LOD level, used for distance or screen-size calculations. The
        bounding volume may be one of the geometry primitives, a mesh, or other
        primitive whose extent may be computed in a well defined manner."""
    )
    
    token computeDistanceTo = "center" (
        allowedTokens = ["center", "boundingVolume", "boundingBox"]
        doc = """Method used to compute distance from a reference point to this LOD.
        
        - center: Use the lodLevel:center property
        - boundingVolume: Use the lodLevel:boundingVolume prim
        - boundingBox: Use the computed bounding box of the collection content"""
    )
}


class "HeuristicAPI"
(
    inherits = </APISchemaBase>
    doc = """API that defines the heuristic for LOD selection.
    
    This API schema defines how LOD levels should be selected during
    rendering or interaction. It supports various transition modes and
    can be extended for specific heuristic types.
    
    The LodHeuristic structure is meant to be advisory, signalling authoring
    intent, but not an absolute interchange contract. Different engines and
    rendering systems may have different needs, and absolute translation
    between them is unreasonable and mostly ill-posed. Nonetheless it is
    valuable to have consistent places to store consistent data, and that
    is the purpose of this API. It is advisory to interoperability but
    nonetheless facilitates the storage of data within a single system. 
    
    The name of the prim the heuristic applied to should indicate the system 
    domain.   
    """

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "Heuristic"
    }
)
{
    uniform int manualLodIndex = -1 (
        doc = """When type is 'manual', this specifies the LOD index to use.
        
        This property can be time-sampled to animate LOD transitions.
        A value of -1 means use automatic selection."""
    )

    uniform token transition = "discrete" (
        allowedTokens = ["discrete", "crossFade", "morphGeometry", "dithered"]
        doc = """Advisory field: How to transition between LOD levels.
        
        - discrete: Switch immediately between levels
        - crossFade: Blend between levels using opacity
        - morphGeometry: Interpolate geometry between levels
        - dithered: Use screen-space dithering pattern

        Other choices are possible, these are common and should be used if
        applicable in preference to non-standard names for the same concepts.
        """
    )
    
    rel localCoordinateSystem (
        doc = """The reference origin that may be used by heuristic calculations.
        
        Typically targets a camera or other reference object.
        If unspecified, the world origin is assumed."""
    )
}

class "DistanceHeuristicAPI"
(
    inherits = </APISchemaBase>
    prepend apiSchemas = ["HeuristicAPI"]

    doc = """API that defines the Distance based LOD selection heuristic.
    
    This API schema defines how LOD levels should be selected during
    rendering or interaction on the basis of distance from the camera.
    
    The distance thresholds are grouped via minimum and maximum threshold.
    By separating these two, threshold hysteresis may be adjusted; in other
    words, the problem of flickering between two LODs is avoided by creating
    a bistable threshold to allow for slight frame-to-frame variance.
    
    The name of the prim the heuristic applied to should indicate the system 
    domain.   
    """

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "distanceHeuristic"
    }
)
{
    uniform float[] distanceMinThresholds = [] (
        doc = """This defines the distance thresholds
        for LOD transitions in ascending order. The min treshold is consulted
        to transition from a higher LOD to a lower one.
        
        For example, [10.0, 50.0, 100.0] means:
        - Use LOD 0 when distance < 10.0
        - Use LOD 1 when 10.0 <= distance < 50.0
        - Use LOD 2 when 50.0 <= distance < 100.0
        - Use LOD 3 when distance >= 100.0

        This field is advisory and not strongly interoperable.
        """
    )
    uniform float[] distanceMaxThresholds = [] (
        doc = """This defines the distance thresholds
        for LOD transitions in ascending order. The max treshold is consulted
        to transition from a lower LOD to a higher one.
        
        See distanceMinThresholds for complementary information.

        This field is advisory and not strongly interoperable.
        """
    )
}


class "ScreenSizeHeuristicAPI"
(
    inherits = </APISchemaBase>
    prepend apiSchemas = ["HeuristicAPI"]

    doc = """API that defines the Screen Size based LOD selection heuristic.
    
    This API schema defines how LOD levels should be selected during
    rendering or interaction on the basis of the visible extent of an object
    from the perspective of the rendering camera.
    
    The distance thresholds are grouped via minimum and maximum threshold.
    By separating these two, threshold hysteresis may be adjusted; in other
    words, the problem of flickering between two LODs is avoided by creating
    a bistable threshold to allow for slight frame-to-frame variance.
    
    The name of the prim the heuristic applied to should indicate the system 
    domain.   
    """

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "distanceLodHeuristic"
    }
    
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
        for LOD transitions in descending order and is consulted when transitioning
        from a higher LOD to a lower one.
        
        For example, [1000.0, 400.0, 100.0] means:
        - Use LOD 0 when screen size >= 1000.0
        - Use LOD 1 when 400.0 <= screen size < 1000.0
        - Use LOD 2 when 100.0 <= screen size < 400.0
        - Use LOD 3 when screen size < 100.0

        This field is advisory and not strongly interoperable.
        """
    )
    
        uniform float[] screenSizeMaxThresholds = [] (
        doc = """This defines the screen size thresholds
        for LOD transitions in descending order and is consulted when transitioning
        from a lower LOD to a higher one.
        
        For example, [1000.0, 400.0, 100.0] means:
        - Use LOD 0 when screen size >= 1000.0
        - Use LOD 1 when 400.0 <= screen size < 1000.0
        - Use LOD 2 when 100.0 <= screen size < 400.0
        - Use LOD 3 when screen size < 100.0

        This field is advisory and not strongly interoperable.
        """
    )
}   

class "PhysicsEntityHeuristicAPI"
(
    inherits = </APISchemaBase>
    prepend apiSchemas = ["HeuristicAPI"]

    doc = """Custom heuristic for physics LOD selection.
    
    This class is meant to be illustrative to show a general pattern. 
    Heuristics will be highly specific to particular system domains, 
    and application developers may create their own heuristic apis to 
    signal heuristics.

    Selects LOD based on whether an active entity is present in the prim or collection.
    For example, a room can switch to full physics LOD only when a player or other
    dynamic entity is inside."""
    
    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "physicsEntityHeuristic"
    }
)
{
    rel activeEntities (
        doc = """Targets prims representing entities that trigger this LOD when present.
        
        For example, a player character, NPCs, or other dynamic objects."""
    )
    
    uniform token selectionMode = "any" (
        allowedTokens = ["any", "all"]
        doc = """Defines how multiple entities influence LOD selection:
        - any: if any entity is present, switch to this LOD
        - all: only switch if all listed entities are present"""
    )
}

class "FramerateHeuristicAPI"
(
    inherits = </APISchemaBase>
    prepend apiSchemas = ["HeuristicAPI"]

    doc = """Extension of HeuristicAPI for framerate-based LOD selection.
    
    This is another example to show how specific heuristics may be defined
    for particular systems. Application developers may create their own
    heuristic apis to signal heuristics specific to their needs.

    This API provides additional properties for controlling LOD based on
    renderer performance."""

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "framerateHeuristic"
    }
)
{
    uniform float targetFramerate = 60.0 (
        doc = """Target framerate to maintain in frames per second."""
    )
    
    uniform float hysteresis = 0.2 (
        doc = """How much the framerate can fluctuate before triggering an LOD change.
        
        Expressed as a fraction of targetFramerate. For example, with a target of
        60fps and hysteresis of 0.2, LOD changes will occur when framerate falls
        below 48fps or rises above 72fps."""
    )
    
    uniform int maxLodIncrease = 1 (
        doc = """Maximum number of LOD levels to increase (reduce detail) in a
        single update."""
    )
}

```

### Usage Examples

#### Example 1: Hierarchical LOD Demo: City → Buildings → Rooms

This example demonstrates two LOD domains:

- **Geometry**: standard camera distance heuristic, smooth cross-fade.
- **Physics**: entity-based heuristic, LOD depends on which rooms have players/NPCs.

Each uses its own LodConfigurationAPI:<domain> instance applied to the same prim.
Levels are defined as separate prims with LodLevelAPI:<name> applied, and each references a collection.

```python
#usda 1.0
(
    defaultPrim = "City"
)

def Xform "City" (
    prepend apiSchemas = ["LodConfigurationAPI:geometry", "LodConfigurationAPI:physics"]
)
{
    #-----------------------------------------
    # GEOMETRY DOMAIN
    #-----------------------------------------
    uniform token lodConfiguration:geometry:levelType = "geometry"
    rel lodConfiguration:geometry:lodLevels = [
        </City/GeometryLOD0>,
        </City/GeometryLOD1>
    ]
    rel lodConfiguration:geometry:heuristic = </City/GeometryDistanceHeuristic>

    def Scope "GeometryLOD0" (
        prepend apiSchemas = ["LodLevelAPI:high"]
    )
    {
        rel lodLevel:high:members = </City/HighDetailCollection>
    }

    def Scope "GeometryLOD1" (
        prepend apiSchemas = ["LodLevelAPI:low"]
    )
    {
        rel lodLevel:low:members = </City/LowDetailCollection>
    }

    def Scope "GeometryDistanceHeuristic" (
        prepend apiSchemas = ["DistanceLodHeuristicAPI:geometry"]
    )
    {
        uniform float[] distanceLodHeuristic:geometry:distanceMinThresholds = [50.0, 200.0]
        uniform float[] distanceLodHeuristic:geometry:distanceMaxThresholds = [60.0, 220.0]
        uniform token lodHeuristic:geometry:transition = "crossFade"
        rel lodHeuristic:geometry:localCoordinateSystem = </Camera>
    }

    #-----------------------------------------
    # PHYSICS DOMAIN
    #-----------------------------------------
    uniform token lodConfiguration:physics:levelType = "physics"
    rel lodConfiguration:physics:lodLevels = [
        </City/PhysicsLOD0>,
        </City/PhysicsLOD1>
    ]
    rel lodConfiguration:physics:heuristic = </City/PhysicsEntityHeuristic>

    def Scope "PhysicsLOD0" (
        prepend apiSchemas = ["LodLevelAPI:full"]
    )
    {
        rel lodLevel:full:members = </City/Buildings>
    }

    def Scope "PhysicsLOD1" (
        prepend apiSchemas = ["LodLevelAPI:simple"]
    )
    {
        rel lodLevel:simple:members = </City/Buildings>
    }

    def Scope "PhysicsEntityHeuristic" (
        prepend apiSchemas = ["PhysicsEntityLodHeuristicAPI"]
    )
    {
        rel physicsEntityLodHeuristic:activeEntities = [
            </Player>,
            </NPCs>
        ]
        uniform token physicsEntityLodHeuristic:selectionMode = "any"
    }
}

#-----------------------------------------
# Geometry collections
#-----------------------------------------
def Scope "HighDetailCollection" (
    prepend apiSchemas = ["CollectionAPI"]
)
{
    rel collection:includes = [
        </City/Buildings/BuildingA/Rooms/Room1>,
        </City/Buildings/BuildingA/Rooms/Room2>,
        </City/Buildings/BuildingB>
    ]
}

def Scope "LowDetailCollection" (
    prepend apiSchemas = ["CollectionAPI"]
)
{
    rel collection:includes = [
        </City/Buildings/BuildingA>,
        </City/Buildings/BuildingB>
    ]
}

#-----------------------------------------
# City hierarchy
#-----------------------------------------
def Xform "Buildings" {
    def Xform "BuildingA" {
        def Xform "Rooms" {
            def Xform "Room1" {}
            def Xform "Room2" {}
        }
    }
    def Xform "BuildingB" {}
}
```

#### Example 2: Three LOD domains: geometry, physics, material.

This demonstrates how three independent LOD domains coexist peacefully on the same prim.
Each domain uses its own multi-applied LodConfigurationAPI:<domain> with different heuristics.

```python
#usda 1.0
(
    defaultPrim = "Vehicle"
)

def Xform "Vehicle" (
    prepend apiSchemas = [
        "LodConfigurationAPI:geometry",
        "LodConfigurationAPI:material",
        "LodConfigurationAPI:physics"
    ]
)
{
    #-----------------------------------------
    # GEOMETRY DOMAIN
    #-----------------------------------------
    uniform token lodConfiguration:geometry:levelType = "geometry"
    rel lodConfiguration:geometry:lodLevels = [
        </Vehicle/GeoLOD0>,
        </Vehicle/GeoLOD1>,
        </Vehicle/GeoLOD2>
    ]
    rel lodConfiguration:geometry:heuristic = </Vehicle/DistanceHeuristic>

    def Scope "GeoLOD0" (prepend apiSchemas = ["LodLevelAPI:high"])
    {
        rel lodLevel:high:members = </Vehicle/HighMeshCollection>
    }

    def Scope "GeoLOD1" (prepend apiSchemas = ["LodLevelAPI:medium"])
    {
        rel lodLevel:medium:members = </Vehicle/MediumMeshCollection>
    }

    def Scope "GeoLOD2" (prepend apiSchemas = ["LodLevelAPI:low"])
    {
        rel lodLevel:low:members = </Vehicle/LowMeshCollection>
    }

    def Scope "DistanceHeuristic" (
        prepend apiSchemas = ["DistanceLodHeuristicAPI:geometry"]
    )
    {
        uniform float[] distanceLodHeuristic:geometry:distanceMinThresholds = [10.0, 30.0, 80.0]
        uniform float[] distanceLodHeuristic:geometry:distanceMaxThresholds = [12.0, 35.0, 90.0]
        uniform token lodHeuristic:geometry:transition = "crossFade"
        rel lodHeuristic:geometry:localCoordinateSystem = </RenderCamera>
    }

    #-----------------------------------------
    # MATERIAL DOMAIN
    #-----------------------------------------
    uniform token lodConfiguration:material:levelType = "material"
    rel lodConfiguration:material:lodLevels = [
        </Vehicle/MatLOD0>,
        </Vehicle/MatLOD1>
    ]
    rel lodConfiguration:material:heuristic = </Vehicle/ScreenSizeHeuristic>

    def Scope "MatLOD0" (prepend apiSchemas = ["LodLevelAPI:high"])
    {
        rel lodLevel:high:members = </Vehicle/HighResMaterials>
    }

    def Scope "MatLOD1" (prepend apiSchemas = ["LodLevelAPI:low"])
    {
        rel lodLevel:low:members = </Vehicle/LowResMaterials>
    }

    def Scope "ScreenSizeHeuristic" (
        prepend apiSchemas = ["ScreenSizeLodHeuristicAPI:material"]
    )
    {
        uniform float[] screenSizeLodHeuristic:material:screenSizeMinThresholds = [1200.0, 400.0]
        uniform float[] screenSizeLodHeuristic:material:screenSizeMaxThresholds = [1300.0, 500.0]
        uniform token lodHeuristic:material:transition = "dithered"
        uniform token screenSizeLodHeuristic:material:screenSizeMetric = "projectedArea"
        rel lodHeuristic:material:localCoordinateSystem = </RenderCamera>
    }

    #-----------------------------------------
    # PHYSICS DOMAIN
    #-----------------------------------------
    uniform token lodConfiguration:physics:levelType = "physics"
    rel lodConfiguration:physics:lodLevels = [
        </Vehicle/PhysLOD0>,
        </Vehicle/PhysLOD1>
    ]
    rel lodConfiguration:physics:heuristic = </Vehicle/PhysicsEntityHeuristic>

    def Scope "PhysLOD0" (prepend apiSchemas = ["LodLevelAPI:full"])
    {
        rel lodLevel:full:members = </Vehicle/CollisionMeshDetailed>
    }

    def Scope "PhysLOD1" (prepend apiSchemas = ["LodLevelAPI:simple"])
    {
        rel lodLevel:simple:members = </Vehicle/CollisionMeshSimplified>
    }

    def Scope "PhysicsEntityHeuristic" (
        prepend apiSchemas = ["PhysicsEntityLodHeuristicAPI"]
    )
    {
        rel physicsEntityLodHeuristic:activeEntities = [</Driver>, </NPC>]
        uniform token physicsEntityLodHeuristic:selectionMode = "any"
    }
}

#-----------------------------------------
# Collections for geometry/material membership
#-----------------------------------------
def Scope "HighMeshCollection" (prepend apiSchemas = ["CollectionAPI"])
{
    rel collection:includes = [</Vehicle/Body/HighDetailMesh>]
}

def Scope "MediumMeshCollection" (prepend apiSchemas = ["CollectionAPI"])
{
    rel collection:includes = [</Vehicle/Body/MediumDetailMesh>]
}

def Scope "LowMeshCollection" (prepend apiSchemas = ["CollectionAPI"])
{
    rel collection:includes = [</Vehicle/Body/LowDetailMesh>]
}

def Scope "HighResMaterials" (prepend apiSchemas = ["CollectionAPI"])
{
    rel collection:includes = [</Vehicle/Materials/HighRes>]
}

def Scope "LowResMaterials" (prepend apiSchemas = ["CollectionAPI"])
{
    rel collection:includes = [</Vehicle/Materials/LowRes>]
}
```



### Implementation Considerations

These considerations are advisory to application developers. LOD selection is not performed by USD itself. If Storm implements LOD heuristics they will be specific to Storm.

1. **Performance**: LOD switching should be frame-deterministic and not require access to previous frame states.

2. **Integration with Game Engines**: The API is designed to be used as a data interchange format, with the execution logic handled by the renderer or engine.

3. **Edge Cases:** Empty parent LODs are evaluated normally; children render nothing if their collection is empty.

4. **Instance Handling**: For point instancing, each instance can use its own LOD switching based on its position relative to its reference point.

## Alternative Solutions Considered

1. **Concrete LOD Node Types**: The original proposal used concrete node types rather than API schemas. This approach predates API schemas which provide better extensibility and composability.

2. **Variant-Based LODs**: Using USD variants for LOD switching was considered but rejected because it lacks standardized metadata for automatic LOD selection.

3. **Payload-Based LODs**: Using payloads for LODs is another option but focuses more on load-time optimization rather than runtime LOD switching.

## Excluded Topics

1. **Automatic LOD Generation**: This proposal does not address the generation of LOD levels from high-resolution models, which is considered a separate tool specific concern.

2. **Specialized Material Features**: Specialized material LOD features like on demandyes mip-map generation are considered tool or runtime specific concerns.

3. **Pipeline Integration**: Specific workflows for authoring and managing LODs in content creation tools are outside the scope of this proposal.