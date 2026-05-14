# LOD Schema API Design

## C++ API

### Core Classes

#### UsdLodRootAPI

```cpp
    class UsdLodRootAPI : public UsdAPISchemaBase
    {
    public:
        // Constructor
        explicit UsdLodRootAPI(const UsdPrim& prim);

        // Apply the schema to a prim
        static UsdLodRootAPI Apply(const UsdPrim& prim);

        // Get the default LOD index attribute
        UsdAttribute GetLodDefaultIndexAttr() const;

        // Get the relationship that targets LOD heuristics
        UsdRelationship GetLodHueristicsRel() const;

        // Utility methods
        // The LOD items are simply children of this root prim
        UsdPrimSiblingRange GetLODItems() const;

        ...
    };
```

#### UsdLodOverrideAPI

```cpp
    class UsdLodOverrideAPI : public UsdAPISchemaBase
    {
    public:
        // Constructor
        explicit UsdLodOverrideAPI(const UsdPrim& prim);

        // Apply the schema to a prim
        static UsdLodOverrideAPI Apply(const UsdPrim& prim);

        // Get the override mode attribute. Legal token values are "inherited",
        // "noOverride", "indexedLOD", "noLOD", and "allLOD".
        UsdAttribute GetLodOverrideModeAttr() const;

        // Get the override index attribute. Used only when the override mode
        // is "indexedLOD".
        UsdAttribute GetLodOverrideIndexAttr() const;
    };
```

#### UsdLodDistanceHeuristic
```cpp
    // Base class for all heuristics
    class UsdLodHeuristic : public UsdTyped
    {
    public:
        // Constructor
        explicit UsdLodHeuristic(const UsdPrim& prim);

        // Virtual destructor for RTTI and polymorphism
        virtual ~UsdLodHeuristic();

        // Get the lod:domain attribute. The domain indicates how this
        // heuristic is intended to be used.
        UsdAttribute GetLodDomainAttr();
    }
```

#### UsdLodDistanceHeuristic
```cpp
    // Heuristic based on distance from a viewpoint
    class UsdLodDistanceHeuristic : public UsdLodHeuristic
    {
    public:
        // Constructor
        explicit UsdLodDistanceHeuristic(const UsdPrim& prim);

        // Virtual destructor for RTTI and polymorphism
        virtual ~UsdLodDistanceHeuristic();

        // Get the point3f center attribute
        UsdAttribute GetCenterAttr() const;

        // Get the boundingVolume relationship that targets a UsdGeomBoundable
        // prim
        UsdRelationship GetBoundingVolumeRel() const;

        // Get the float[] thresholds attribute
        UsdAttribute GetThresholdsAttr() const;

        // Get the optional float[] blendThresholds attribute
        UsdAttribute GetBlendThresholdsAttr() const;

        // Additional methods
        // Compute the distance for a viewpoint and transform.
        double ComputeDistance(const GfVec3f& viewpoint,
                               const GfMatrix4d& transform,
                               UsdTimeCode time = UsdTimeCode::Default()) const;

        // Compute the LOD index from the distance. A floating point return
        // value allows for blending between LOD items (at the renderer's
        // discretion).
        float ComputeLOD(double distance);

        // Compute the LOD index for a viewpoint and transform.
        float ComputeLOD(const GfVec3f& viewpoint,
                         const GfMatrix4d& transform,
                         UsdTimeCode time = UsdTimeCode::Default()) const;
    };
```

#### UsdLodScreenSizeHeuristic
```cpp
    // Heuristic based on the screen-size of a extent.
    class UsdLodScreenSizeHeuristic : public UsdLodHeuristic
    {
    public:
        // Constructor
        explicit UsdLodScreenSizeHeuristic(const UsdPrim& prim);

        // Virtual destructor for RTTI and polymorphism
        virtual ~UsdLodScreenSizeHeuristic();

        // Get the projection method attribute. Legal values are
        // "projectedSphere" and "projectedExtent".
        UsdAttribute GetProjectionMethodAttr() const;

        // Get the float3[] extent attribute
        UsdAttribute GetExtentAttr() const;

        // Get the boundingVolume relationship that targets a UsdGeomBoundable
        // prim
        UsdRelationship GetBoundingVolumeRel() const;

        // Get the float[] thresholds attribute
        UsdAttribute GetThresholdsAttr() const;

        // Get the optional float[] blendThresholds attribute
        UsdAttribute GetBlendThresholdsAttr() const;

        // Additional methods
        // Compute the screen-size for a frustum and transform. The screen-size
        // is returned as a fraction of the frustum's view plane. 1.0 == 100%.
        double ComputeScreenSize(const GfFrustum& frustum,
                                 const GfMatrix4d& transform,
                                 UsdTimeCode time = UsdTimeCode::Default()) const;

        // Compute the LOD index from the screenSize. A floating point return
        // value allows for blending between LOD items (at the renderer's
        // discretion).
        float ComputeLOD(double screenSize);

        // Compute the LOD index for a frustum and transform.
        float ComputeLOD(const GfFrustum& frustum,
                         const GfMatrix4d& transform,
                         UsdTimeCode time = UsdTimeCode::Default()) const;
    };
```

## Usage Example

```cpp
    // C++ example
    UsdStageRefPtr stage = UsdStage::CreateNew("lod_example.usda");

    // Create an LOD group
    UsdLodGroup lodGroup = UsdLodGroup::Define(stage, SdfPath("/Model/LodGroup"));
    lodGroup.SetLodMetric(TfToken("distance"));
    lodGroup.SetLodRanges(VtArray<float>{10.0f, 50.0f, 200.0f});
    lodGroup.SetFadeTransitions(true);
    lodGroup.SetFadeTransitionWidth(5.0f);

    // Create LOD levels
    UsdLodLevel highDetail = UsdLodLevel::Define(stage, SdfPath("/Model/LodGroup/HighDetail"));
    highDetail.SetLodIndex(0);
    highDetail.SetComplexity(1.0f);

    UsdLodLevel mediumDetail = UsdLodLevel::Define(stage, SdfPath("/Model/LodGroup/MediumDetail"));
    mediumDetail.SetLodIndex(1);
    mediumDetail.SetComplexity(0.5f);

    UsdLodLevel lowDetail = UsdLodLevel::Define(stage, SdfPath("/Model/LodGroup/LowDetail"));
    lowDetail.SetLodIndex(2);
    lowDetail.SetComplexity(0.2f);

    // Set LOD targets
    SdfPathVector targets = {
    SdfPath("/Model/LodGroup/HighDetail"),
    SdfPath("/Model/LodGroup/MediumDetail"),
    SdfPath("/Model/LodGroup/LowDetail")
    };
    lodGroup.SetLodTargets(targets);
```

```python
    # Python example
    stage = Usd.Stage.CreateNew("lod_example.usda")

    # Create a thing with geometry
    geom = UsdGeom.Scope.Define(stage, "/Thing/Geom")

    # Apply the rootAPI to the geometry
    rootAPI = UsdLod.RootAPI.Apply(geom.GetPrim())

    # Set the default LOD item
    rootAPI.GetLodDefaultIndexAttr().Set(0)

    # Create LOD items
    lodItems = [
        UsdGeom.Scope.Define(stage, "/Thing/Geom/High"),
        UsdGeom.Scope.Define(stage, "/Thing/Geom/Medium"),
        UsdGeom.Scope.Define(stage, "/Thing/Geom/Low")
    ]

    # Create a distance heuristic
    distHeur = UsdLod.DistanceHeuristic.Define(
        stage, "/Thing/Heuristics/Distance")

    distHeur.GetThresholdsAttr().Set([10, 35])

    # Make the heuristic available for this root
    rootAPI.GetLodHueristicsRel().AddTarget(
        distanceHeuristic.GetPrim().GetPath())

    # Query the heuristic
    lodIndex = distanceHeur.ComputeLOD(Gf.Vec3d(0.0, 0.0, -20),
                                       Gf.Matrix4d(1.0))
```
