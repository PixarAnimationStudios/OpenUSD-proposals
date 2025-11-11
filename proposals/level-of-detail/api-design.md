# LOD Schema API Design

## C++ API

### Core Classes

#### UsdLodGroup

```cpp
class UsdLodGroup : public UsdGeomXformable
{
public:
    // Constructor
    explicit UsdLodGroup(const UsdPrim& prim);
    
    // Create a new LodGroup prim
    static UsdLodGroup Define(const UsdStagePtr& stage, const SdfPath& path);
    
    // Get/Set the LOD metric
    UsdAttribute GetLodMetricAttr() const;
    TfToken GetLodMetric() const;
    bool SetLodMetric(const TfToken& metric);
    
    // Get/Set the LOD ranges
    UsdAttribute GetLodRangesAttr() const;
    VtArray<float> GetLodRanges() const;
    bool SetLodRanges(const VtArray<float>& ranges);
    
    // Get/Set the LOD targets relationship
    UsdRelationship GetLodTargetsRel() const;
    SdfPathVector GetLodTargets() const;
    bool SetLodTargets(const SdfPathVector& targets);
    
    // Get/Set fade transition properties
    UsdAttribute GetFadeTransitionsAttr() const;
    bool GetFadeTransitions() const;
    bool SetFadeTransitions(bool enable);
    
    UsdAttribute GetFadeTransitionWidthAttr() const;
    float GetFadeTransitionWidth() const;
    bool SetFadeTransitionWidth(float width);
    
    // Utility methods
    size_t GetLodCount() const;
    UsdPrim GetLodPrim(size_t index) const;
    
    // Schema registry
    static TfToken GetSchemaAttributeNames();
};
```

#### UsdLodLevel

```cpp
class UsdLodLevel : public UsdGeomXformable
{
public:
    // Constructor
    explicit UsdLodLevel(const UsdPrim& prim);
    
    // Create a new LodLevel prim
    static UsdLodLevel Define(const UsdStagePtr& stage, const SdfPath& path);
    
    // Get/Set the LOD index
    UsdAttribute GetLodIndexAttr() const;
    int GetLodIndex() const;
    bool SetLodIndex(int index);
    
    // Get/Set the complexity
    UsdAttribute GetComplexityAttr() const;
    float GetComplexity() const;
    bool SetComplexity(float complexity);
    
    // Schema registry
    static TfToken GetSchemaAttributeNames();
};
```

### Hydra Integration

```cpp
class HdLodSchema : public HdSchema
{
public:
    // LOD selection parameters
    struct LodSelectionParams {
        TfToken metric;
        std::vector<float> ranges;
        bool fadeTransitions;
        float fadeTransitionWidth;
    };
    
    // Get LOD selection parameters from scene delegate
    static LodSelectionParams GetLodSelectionParams(
        const HdSceneDelegate* delegate,
        const SdfPath& id);
        
    // Compute the appropriate LOD level based on parameters and view
    static size_t ComputeLodLevel(
        const LodSelectionParams& params,
        const GfVec3f& cameraPosition,
        const GfMatrix4d& viewProjectionMatrix,
        const GfVec2i& viewportSize);
        
    // Compute blend factors for cross-fading between LOD levels
    static std::pair<size_t, size_t> ComputeLodBlendLevels(
        const LodSelectionParams& params,
        const GfVec3f& cameraPosition,
        const GfMatrix4d& viewProjectionMatrix,
        const GfVec2i& viewportSize,
        float* blendFactor);
};
```

## Python API

```python
class LodGroup(Xformable):
    """A group that contains multiple representations of the same object
    at different levels of detail."""
    
    @classmethod
    def Define(cls, stage, path):
        """Create a new LodGroup prim."""
        return cls(stage.DefinePrim(path, 'LodGroup'))
    
    def GetLodMetric(self):
        """Get the LOD metric."""
        return self.GetAttribute('lodMetric').Get()
    
    def SetLodMetric(self, metric):
        """Set the LOD metric."""
        return self.GetAttribute('lodMetric').Set(metric)
    
    def GetLodRanges(self):
        """Get the LOD ranges."""
        return self.GetAttribute('lodRanges').Get()
    
    def SetLodRanges(self, ranges):
        """Set the LOD ranges."""
        return self.GetAttribute('lodRanges').Set(ranges)
    
    def GetLodTargets(self):
        """Get the LOD targets."""
        return self.GetRelationship('lodTargets').GetTargets()
    
    def SetLodTargets(self, targets):
        """Set the LOD targets."""
        return self.GetRelationship('lodTargets').SetTargets(targets)
    
    def GetFadeTransitions(self):
        """Get whether fade transitions are enabled."""
        return self.GetAttribute('fadeTransitions').Get()
    
    def SetFadeTransitions(self, enable):
        """Set whether fade transitions are enabled."""
        return self.GetAttribute('fadeTransitions').Set(enable)
    
    def GetFadeTransitionWidth(self):
        """Get the fade transition width."""
        return self.GetAttribute('fadeTransitionWidth').Get()
    
    def SetFadeTransitionWidth(self, width):
        """Set the fade transition width."""
        return self.GetAttribute('fadeTransitionWidth').Set(width)


class LodLevel(Xformable):
    """Represents a single level of detail for an object."""
    
    @classmethod
    def Define(cls, stage, path):
        """Create a new LodLevel prim."""
        return cls(stage.DefinePrim(path, 'LodLevel'))
    
    def GetLodIndex(self):
        """Get the LOD index."""
        return self.GetAttribute('lodIndex').Get()
    
    def SetLodIndex(self, index):
        """Set the LOD index."""
        return self.GetAttribute('lodIndex').Set(index)
    
    def GetComplexity(self):
        """Get the complexity."""
        return self.GetAttribute('complexity').Get()
    
    def SetComplexity(self, complexity):
        """Set the complexity."""
        return self.GetAttribute('complexity').Set(complexity)
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

# Create an LOD group
lod_group = LodGroup.Define(stage, "/Model/LodGroup")
lod_group.SetLodMetric("distance")
lod_group.SetLodRanges([10.0, 50.0, 200.0])
lod_group.SetFadeTransitions(True)
lod_group.SetFadeTransitionWidth(5.0)

# Create LOD levels
high_detail = LodLevel.Define(stage, "/Model/LodGroup/HighDetail")
high_detail.SetLodIndex(0)
high_detail.SetComplexity(1.0)

medium_detail = LodLevel.Define(stage, "/Model/LodGroup/MediumDetail")
medium_detail.SetLodIndex(1)
medium_detail.SetComplexity(0.5)

low_detail = LodLevel.Define(stage, "/Model/LodGroup/LowDetail")
low_detail.SetLodIndex(2)
low_detail.SetComplexity(0.2)

# Set LOD targets
targets = [
    "/Model/LodGroup/HighDetail",
    "/Model/LodGroup/MediumDetail",
    "/Model/LodGroup/LowDetail"
]
lod_group.SetLodTargets(targets)
