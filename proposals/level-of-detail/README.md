# Level of Detail (LOD) API for USD

## Summary

This proposal defines an API schema for managing Level of Detail (LOD) in USD stages. The LOD API enables creators and renderers to efficiently switch between different detail levels of assets based on configurable criteria like distance, screen size, or explicit selection. This approach allows optimizing rendering performance while maintaining visual quality where needed.

## Problem Statement

USD currently lacks a standardized way to represent and manage multiple levels of detail for assets. Game engines, real-time renderers, and interactive applications need efficient LOD mechanisms to maintain performance while presenting high-quality visuals. The current workarounds using variants, payloads, or custom schemas are insufficient because:

1. They don't provide a standardized interchange format for LODs between different tools and engines
2. They often require runtime resolution at load time, which is inefficient for real-time applications
3. They lack built-in mechanisms for specifying transition rules between detail levels
4. They don't support automatic LOD selection based on common metrics like distance or screen size

## Glossary

- **Level of Detail (LOD)**: A technique for improving rendering efficiency by using different versions of an asset with varying complexity based on factors like distance from camera or importance
- **LOD Switching**: The process of changing between different detail levels based on specified criteria
- **Heuristic**: The rule or function that determines when LODs should transition
- **Applied API Schema**: A USD schema that can be applied to existing prims to extend their functionality

## Existing Implementations & Reference Documents

- Several game engines implement proprietary LOD systems (Unreal Engine, Unity, etc.)
- Previous proposals have explored concrete node-based approaches (see originalProposal.md)
- USD's Collections API provides a pattern for targeting sets of prims that we can leverage

## Proposal Details

### Design Principles

1. Use modern applied API schemas instead of concrete nodes
2. Support both manual and automatic LOD selection
3. Enable smooth transitions between LOD levels when desired
4. Allow both mesh geometry and material complexity reduction
5. Support integration with existing USD features like collections
6. Provide a frame-deterministic execution model
7. Be renderer and engine-agnostic

### API Schema Hierarchy

We propose three new API schemas:

1. `LodAPI`: A single-apply API schema that manages LOD configuration for a prim
2. `LodLevelAPI`: A multi-apply API schema that defines individual LOD levels
3. `LodHeuristicAPI`: A single-apply API schema that defines switching logic

### Schema Definitions

#### LodAPI

```python
class LodAPI "LodAPI"
(
    inherits = </APISchemaBase>
    doc = """API for managing Level of Detail (LOD) on a prim.
    
    This API schema provides a way to define multiple LOD levels for a prim
    and specify how to transition between them during rendering. It is
    expected to be applied to a prim that serves as the root for LOD management.
    
    This schema leverages collections to define sets of geometry for different
    detail levels, and provides properties to control LOD selection via 
    specified heuristics."""

    customData = {
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "lod"
    }
)
{
    uniform token version = "1.0" (
        doc = """Schema version for future extensions and compatibility"""
    )
    
    uniform token definitionOrder = "highestFirst" (
        allowedTokens = ["highestFirst", "lowestFirst"]
        doc = """Defines the order of LOD levels in the lodLevels relationship.
        
        - highestFirst: lod:lodLevels[0] has the highest definition (default)
        - lowestFirst: lod:lodLevels[0] has the lowest definition"""
    )
    
    uniform token levelType = "geometry" (
        allowedTokens = ["geometry", "material", "combined", "procedural"]
        doc = """Specifies what type of data is managed by this LOD setup.
        
        - geometry: LOD affects mesh complexity
        - material: LOD affects material/shader complexity
        - combined: LOD affects both geometry and materials
        - procedural: LOD affects procedurally generated data"""
    )
    
    rel lodLevels (
        doc = """Relationship to the LOD levels defined for this prim.
        
        This relationship targets prims with the LodLevelAPI applied.
        The order of the targets should match the definitionOrder."""
    )
    
    rel heuristic (
        doc = """Relationship to the heuristic used for LOD selection.
        
        This relationship targets a prim with the LodHeuristicAPI applied.
        If no heuristic is specified, no automatic LOD switching will occur."""
    )
}
```

#### LodLevelAPI

```python
class LodLevelAPI "LodLevelAPI"
(
    inherits = </APISchemaBase>
    doc = """API that defines a single LOD level within an LOD group.
    
    This multi-apply API schema allows defining multiple LOD levels for a prim.
    Each level provides a collection of geometry and properties specific to that
    detail level. The collection can include or exclude specific prims to fine-tune
    which parts of the model belong to a particular LOD level."""

    customData = {
        string apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "lodLevel"
        string extraIncludes = """
#include "pxr/usd/usd/collectionAPI.h" """
    }
)
{
    prepend apiSchemas = ["CollectionAPI:content"]
    
    uniform token index (
        doc = """The index of this LOD level. Lower indices typically represent
        higher detail levels, but this depends on the LodAPI's definitionOrder."""
    )
    
    point3f center = (0.0, 0.0, 0.0) (
        doc = """The center point of this LOD level, used for distance calculations.
        
        This value is used by distance-based heuristics to calculate the
        distance from the camera or other reference point."""
    )
    
    rel boundingVolume (
        doc = """Optional relationship to a prim that defines the bounding volume
        for this LOD level, used for distance or screen-size calculations."""
    )
    
    token computeDistanceTo = "center" (
        allowedTokens = ["center", "boundingVolume", "boundingBox"]
        doc = """Method used to compute distance from a reference point to this LOD.
        
        - center: Use the lodLevel:center property
        - boundingVolume: Use the lodLevel:boundingVolume prim
        - boundingBox: Use the computed bounding box of the collection content"""
    )
    
    rel collisionProxy (
        doc = """Optional relationship to a prim that provides simplified collision
        geometry for this LOD level, typically used in physics simulations."""
    )
}
```

#### LodHeuristicAPI

```python
class LodHeuristicAPI "LodHeuristicAPI"
(
    inherits = </APISchemaBase>
    doc = """API that defines the heuristic for LOD selection.
    
    This API schema defines how LOD levels should be selected during
    rendering or interaction. It supports various transition modes and
    can be extended for specific heuristic types."""

    customData = {
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "lodHeuristic"
    }
)
{
    uniform token type = "distance" (
        allowedTokens = ["manual", "distance", "screenSize", "framerate", "memory", "custom"]
        doc = """The type of heuristic to use for LOD selection.
        
        - manual: Explicitly set by the application
        - distance: Based on distance from camera or reference point
        - screenSize: Based on projected screen size
        - framerate: Based on target framerate (performance)
        - memory: Based on memory constraints
        - custom: Custom application-defined heuristic"""
    )
    
    uniform token transition = "discrete" (
        allowedTokens = ["discrete", "crossFade", "morphGeometry", "dithered"]
        doc = """How to transition between LOD levels.
        
        - discrete: Switch immediately between levels
        - crossFade: Blend between levels using opacity
        - morphGeometry: Interpolate geometry between levels
        - dithered: Use screen-space dithering pattern"""
    )
    
    uniform float transitionRange = 0.0 (
        doc = """Width of the transition region, in the units relevant to the
        heuristic type. For distance-based heuristics, this is in distance units.
        
        A value of 0 means immediate switching with no transition region."""
    )
    
    uniform int manualLodIndex = -1 (
        doc = """When type is 'manual', this specifies the LOD index to use.
        
        This property can be time-sampled to animate LOD transitions.
        A value of -1 means use automatic selection."""
    )
    
    uniform float[] distanceThresholds = [] (
        doc = """When type is 'distance', this defines the distance thresholds
        for LOD transitions in ascending order.
        
        For example, [10.0, 50.0, 100.0] means:
        - Use LOD 0 when distance < 10.0
        - Use LOD 1 when 10.0 <= distance < 50.0
        - Use LOD 2 when 50.0 <= distance < 100.0
        - Use LOD 3 when distance >= 100.0"""
    )
    
    rel referencePoint (
        doc = """The reference point for distance calculations.
        
        Typically targets a camera or other reference object.
        If unspecified, the active camera is used."""
    )
    
    uniform token screenSizeMetric = "projectedArea" (
        allowedTokens = ["projectedArea", "boundingSphereSize", "custom"]
        doc = """When type is 'screenSize', this defines how screen size is calculated.
        
        - projectedArea: Use projected area in pixels
        - boundingSphereSize: Use projected bounding sphere diameter
        - custom: Use application-defined metric"""
    )
    
    uniform float[] screenSizeThresholds = [] (
        doc = """When type is 'screenSize', this defines the screen size thresholds
        for LOD transitions in descending order.
        
        For example, [1000.0, 400.0, 100.0] means:
        - Use LOD 0 when screen size >= 1000.0
        - Use LOD 1 when 400.0 <= screen size < 1000.0
        - Use LOD 2 when 100.0 <= screen size < 400.0
        - Use LOD 3 when screen size < 100.0"""
    )
}
```

### Heuristic Extensions

The base `LodHeuristicAPI` can be extended with more specialized heuristics as needed. For example:

```python
class FramerateLodHeuristicAPI "FramerateLodHeuristicAPI"
(
    inherits = </APISchemaBase>
    doc = """Extension of LodHeuristicAPI for framerate-based LOD selection.
    
    This API provides additional properties for controlling LOD based on
    renderer performance."""

    customData = {
        string apiSchemaType = "singleApply"
        token propertyNamespacePrefix = "framerateLodHeuristic"
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

#### Example 1: Basic LOD Setup

```usda
#usda 1.0
(
    defaultPrim = "Truck"
    metersPerUnit = 0.01
    upAxis = "Y"
)

def Xform "Truck" (
    prepend apiSchemas = ["LodAPI"]
)
{
    # Configure LOD API
    uniform token lod:definitionOrder = "highestFirst"
    uniform token lod:levelType = "geometry"
    rel lod:lodLevels = [
        </Truck/LOD0>,
        </Truck/LOD1>,
        </Truck/LOD2>
    ]
    rel lod:heuristic = </Truck/DistanceHeuristic>
    
    # LOD levels
    def Xform "LOD0" (
        prepend apiSchemas = ["LodLevelAPI:high"]
    )
    {
        uniform token lodLevel:high:index = "0"
        rel collection:content:includes = [
            </Truck/HighDetail>
        ]
    }
    
    def Xform "LOD1" (
        prepend apiSchemas = ["LodLevelAPI:medium"]
    )
    {
        uniform token lodLevel:medium:index = "1"
        rel collection:content:includes = [
            </Truck/MediumDetail>
        ]
    }
    
    def Xform "LOD2" (
        prepend apiSchemas = ["LodLevelAPI:low"]
    )
    {
        uniform token lodLevel:low:index = "2"
        rel collection:content:includes = [
            </Truck/LowDetail>
        ]
    }
    
    # Heuristic configuration
    def Scope "DistanceHeuristic" (
        prepend apiSchemas = ["LodHeuristicAPI"]
    )
    {
        uniform token lodHeuristic:type = "distance"
        uniform token lodHeuristic:transition = "crossFade"
        uniform float lodHeuristic:transitionRange = 5.0
        uniform float[] lodHeuristic:distanceThresholds = [20.0, 50.0, 100.0]
    }
    
    # Geometry for different LOD levels
    def Xform "HighDetail" {
        # High-resolution truck model with 100,000 polygons
    }
    
    def Xform "MediumDetail" {
        # Medium-resolution truck model with 25,000 polygons
    }
    
    def Xform "LowDetail" {
        # Low-resolution truck model with 5,000 polygons
    }
}
```

#### Example 2: Material LOD with Screen Size Heuristic

```usda
#usda 1.0
(
    defaultPrim = "Building"
)

def Xform "Building" (
    prepend apiSchemas = ["LodAPI"]
)
{
    uniform token lod:levelType = "material"
    rel lod:lodLevels = [
        </Building/MaterialLOD0>,
        </Building/MaterialLOD1>,
        </Building/MaterialLOD2>
    ]
    rel lod:heuristic = </Building/ScreenSizeHeuristic>
    
    # LOD levels for materials
    def Scope "MaterialLOD0" (
        prepend apiSchemas = ["LodLevelAPI:highQuality"]
    )
    {
        uniform token lodLevel:highQuality:index = "0"
        rel collection:content:includes = [
            </Building/Materials/HighQuality>
        ]
    }
    
    def Scope "MaterialLOD1" (
        prepend apiSchemas = ["LodLevelAPI:mediumQuality"]
    )
    {
        uniform token lodLevel:mediumQuality:index = "1"
        rel collection:content:includes = [
            </Building/Materials/MediumQuality>
        ]
    }
    
    def Scope "MaterialLOD2" (
        prepend apiSchemas = ["LodLevelAPI:lowQuality"]
    )
    {
        uniform token lodLevel:lowQuality:index = "2"
        rel collection:content:includes = [
            </Building/Materials/LowQuality>
        ]
    }
    
    # Screen size heuristic
    def Scope "ScreenSizeHeuristic" (
        prepend apiSchemas = ["LodHeuristicAPI"]
    )
    {
        uniform token lodHeuristic:type = "screenSize"
        uniform token lodHeuristic:screenSizeMetric = "projectedArea"
        uniform float[] lodHeuristic:screenSizeThresholds = [10000.0, 2500.0, 500.0]
    }
    
    # Material variations for different LODs
    def Scope "Materials" {
        def Scope "HighQuality" {
            # High-quality PBR materials with multiple textures
        }
        
        def Scope "MediumQuality" {
            # Medium-quality materials with fewer textures
        }
        
        def Scope "LowQuality" {
            # Low-quality materials with minimal textures
        }
    }
}
```

### Implementation Considerations

1. **Performance**: LOD switching should be frame-deterministic and not require access to previous frame states.

2. **Integration with Game Engines**: The API is designed to be used as a data interchange format, with the execution logic handled by the renderer or engine.

3. **Compatibility**: This approach maintains USD's core principles and can be extended further as needed.

4. **Instance Handling**: For point instancing, each instance can use its own LOD switching based on its position relative to the reference point.

## Risks

1. **Performance Overhead**: Implementation must be careful to avoid excessive overhead during LOD selection, especially for scenes with many LOD-enabled assets.

2. **Compatibility**: Existing tools that use custom LOD solutions may need adapters to work with this standard.

3. **Complexity**: The API needs to balance flexibility with usability to ensure adoption.

## Alternative Solutions Considered

1. **Concrete LOD Node Types**: The original proposal used concrete node types rather than API schemas. This approach predates API schemas which provide better extensibility and composability.

2. **Variant-Based LODs**: Using USD variants for LOD switching was considered but rejected because it lacks standardized metadata for automatic LOD selection.

3. **Payload-Based LODs**: Using payloads for LODs is another option but focuses more on load-time optimization rather than runtime LOD switching.

## Excluded Topics

1. **Automatic LOD Generation**: This proposal does not address the generation of LOD levels from high-resolution models, which is considered a separate tool-specific concern.

2. **Advanced Material Features**: Specialized material LOD features like mip-map generation are left for future proposals.

3. **Animation LOD**: Simplification of animation systems (skinning, blend shapes, etc.) is not fully addressed but could be added in future extensions.

4. **Pipeline Integration**: Specific workflows for authoring and managing LODs in content creation tools are outside the scope of this proposal.