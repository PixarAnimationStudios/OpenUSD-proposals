# SkelInstancedAnimationSourcesAPI Schema Proposal

# Abstract

We propose SkelInstancedAnimationSourcesAPI, a new single-application API schema for PointInstancer designed to supply instance-varying attributes and a relationship to drive animation binding and time offsets for SkelRoot prototypes. This schema enables a compact definition where a single PointInstancer can efficiently manage thousands (or orders of magnitude more) of skeletal instances, each with unique animation states.

Currently, the only supported method for achieving pose variation is by overriding skel:animationSource in the skeletal binding on a native instance. However, this implicit instance aggregation becomes highly inefficient when processing a large volume of unique poses. Our proposed schema allows for the explicit expression of that override on the point instancer when deferred skinning is active, reducing translation to Hydra to nearly a no-op. Additionally, it provides a unified data source interface for both native and point instances within Hydra.

# Background

Hydra 2.0 introduces support for `UsdGeomPointInstancer` with `UsdSkel` prototypes—a workflow that was fundamentally impossible in Hydra 1.0. Previously, using a UsdSkelRoot as a prototype caused conflicts between the PointInstancer and SkelImaging adapters, leading to validation errors and render failures. Consequently, the Crowds department relies on native instancing for large-scale assets. To achieve variation, artists were forced to duplicate `SkelAnimation` prims with reference or layer offsets—a workaround that significantly bloated prim counts. PointInstancer, however, offers more compact semantics than native instancing, resulting in smaller file size, faster load times and improved editability.

This is phase 2 of the larger deferred skinning project. Which utilizes modern GPU to solve one of the main challenges of instancing animated assets by decoupling posing from the prototypes. The feature was introduced to native instancing first in phase 1 (because historically we’ve only been able to utilize native instancing) and now we’d like to extend the same interface to point instancing to align with the unified hydra instancing paradigm.

# Proposal

We propose creating a new single-application API schema `SkelInstancedAnimationSourcesAPI` (see the [Risks/Concerns](#risksconcernstodos-risksconcernstodos) section for rationales behind the design choice) for PointInstancer to supply instance-varying attributes and a relationship to drive animation binding and time offsets. This enables a compact definition where a single PointInstancer manages thousands (or orders of magnitude more) of skeletal instances, each with unique animation states, as demonstrated below:

```usda
def Scope "World"
{
    def PointInstancer "HumanFemaleCrowd" (
        append apiSchemas = ["SkelInstancedAnimationSourcesAPI"]
    )
    {
        # Bind unique animation sources per instance
        rel skel:animationSources = [
            </World/Anim/Walk_1>,
            </World/Anim/Walk_2>,
            </World/Anim/KA>
        ]

        # Per-instance index into skel:animationSources relationship
        # Similar to how protoIndices index into prototypes.
        int[] skel:animationSourceIndices = [0, 1, 2]

        # Apply per-instance time offsets
        duration[] skel:animationOffsets = [0, 5, 0]

        # Standard PointInstancer attributes
        point3f[] positions = [
            (0, 0, 0),
            (50, 0, 0),
            (100, 0, 0)
        ]
        int[] protoIndices = [0, 0, 0]

        rel prototypes = [
            </World/HumanFemaleCrowd/Prototypes/HumanFemale>
        ]

        over "Prototypes"
        {
            def "HumanFemale" (
                prepend references = @./HumanFemale.usda@
            )
            {
            }
        }
    }
}
```

Note that skel:animationOffsets has a new `duration` SdfValueType.  
Such values need to be mapped during value resolution to pick up time-scaling due to authored SdfLayerOffsets and timecodesPerSecond scaling, but encoding them as timecode valued is incorrect because skel:animationOffsets must be insensitive to any offsets (i.e. the translation component) specified in SdfLayerOffsets, i.e. they must only be affected by the scaling component. More details in the commit here: [fee8b47 \- Add GfDuration, a scalable time-difference value type](https://github.com/PixarAnimationStudios/OpenUSD/commit/fee8b47357830922a124a5671f78d3473b7eb5b6)

The hydra `instancedAnimationSources` schema will replace the original instance primvars used for native instances, acting as the unified interface for instance overrides across both point and native instancing.

While mixing and matching prototype prim types is permitted for architectural flexibility, it is generally discouraged for performance reasons. Because not all prototypes are defined as `SkelRoots`, these overrides will only affect applicable instances. Overrides applied to non-`SkelRoot` instances will have no impact; however, for the sake of technical clarity and to explicitly indicate that an instance is not a `SkelRoot`, authors are encouraged to use a value of \-1 for `skel:animationSourceIndices` and 0 for `skel:animationOffsets`.

The primary rendering challenge for instancing is the massive amount of unique geometry generated by agents with distinct animations. Managing the unique instance states of `protoIndices`, `skel:animationSourceIndices`, and `skel:animationOffsets` is considerably more straightforward than native instancing, providing a more effective path toward higher instance rates.

# Properties

| Property | Type | Description | Required |
| :---- | :---- | :---- | :---- |
| `skel:animationSources` | `relationship` | Relationship targets SkelAnimation prims. | Yes |
| `skel:animationSourceIndices` | `int[]` | Per-instance index into skel:animationSources relationship. Similar to how protoIndices index into prototypes. | Yes |
| `skel:animationOffsets` | `duration[]` | Per-instance time offset on the target animationSource. This is the equivalent of setting a layer offset on a referenced SkelAnimation prim, but interpreted by the schema rather than core value resolution. | No |

# Engineering Work

Add a new SkelInstancedAnimationSourcesAPI schema to UsdSkel and the corresponding hydra instancedAnimationSources schema, animationSources API adapter in usdSkelImaging to supply instance-varying attribute and relationship to drive animation binding and time offsets. We output the composed result as per-instance time offsets. They eventually flow through dataSourceResolvedSkeletonPrim to offset skinningTransforms and blendShapeWeights (by utilizing shutterOffset mechanism in hydra API).

We need to add new logic in xformResolver to compute per-instance animation override corresponding to its prototype from the new skelAnimationSources API in order to support multiple prototypes for point instancers which we didn't need to do because in the native instance case there's always only one prototype.

For native instances, in niPrototypePropagatingSceneIndex, after we aggregated the skelAnimationSource instance primvar, we relocate it to the new skelAnimationSourcesAPI schema so native and point instances are now agnostic to downstream scene indices. This also prevents undesired authoring of the instance primvar directly to have an effect in the point instancer case.

When skinning is deferred, everything flows through as vectors of instance overrides, including the new hydra SkelInstancedAnimationSources schema but for compatibility with current USD semantics, which is to support the non-deferred code path is a little trickier. In which case if two instances share the same prototype but their schema override attributes are different we will need to permute the prototypes and group instances that share the exact same signature. We can follow the same pattern as niInstancesAggregation by adding a new instancerDataSourceNames() method to sceneIndexPlugin. 

# Initial Results

We have a working prototype and test scenes of 100, 1k and 10k agents. The PointInstancer file size is significantly reduced compared to its native instance equivalent, measuring nearly 75% smaller. In a large-scale 20k stadium scene, this results in a substantial footprint reduction from 1.6GB down to 500MB.

**\[TODO\]** provide some load time and TTFJ stats

# Additional Notes

### Animation Source Encapsulation 

The `skel:animationSources` relationship architecturally mirrors the `prototypes` relationship; therefore, it currently imposes no explicit topological restrictions on target locations. However, the schema documentation will explicitly specify that `SkelAnimation` prims should adhere to the established best practice for prototypes. Specifically, they should be encapsulated entirely within the instancer hierarchy and organized under a pure `over` scope to ensure they are skipped by default traversals. Furthermore, should future schema revisions tighten encapsulation requirements for `PointInstancers` due to hydra implementation complexity, the `skel:animationSources` relationship will adopt and enforce those identical constraints.

### Per-instance Time Scale

It is possible to support the addition of a per-instance time scale if we provide an anchor timecode attribute like skel:animationAnchor=0. Alternatively we can extend SkelAnimation with two timecode attributes animationStart/End and require that to be set for a SkelAnimation to be used with the instancer. However, after a few iterations of prototyping and testing, we decided not to support this feature due to the complexity required for users to bookkeep those extra attributes and the error-prone nature of the design. Moreover, in our production experience we mostly create the amount of variation needed through offsets and if necessary we can achieve the same time scale variation through duplicating SkelAnimation prims with a reference scale.

### Looping

It is also possible to support infinite looping utilizing the same technique in hydra by offsetting the length of SkelAnimation at the looping point. We decided not to pursue the feature because we can not represent infinite timeSamples in USD. If we were to UsdStage::Flatten() a scene with infinitely looping timeSamples, we'd be altering the animation in order to make it finite at some arbitrary point in time. While the USD team continues to develop a first-class looping implementation for Value Clips, our current solution is leveraging jump discontinuities to achieve a finite number of loops for SkelAnimation.

### Skeleton Decoupling

Finally, inspired by WDAS’ recent work of [`UsdSkelPointInstancer`](https://dl.acm.org/doi/full/10.1145/3799818.3812104), we want to note that if decoupling skeletons proves compelling for reusability in a production environment, we are entirely open to expanding the API schema with a new skeleton relationship to support it in the future.

# Risks/Concerns/Todos {#risks/concerns/todos}

### API v.s. Derived Schema

While WDAS utilized a derived schema for their [`UsdSkelPointInstancer`](https://dl.acm.org/doi/full/10.1145/3799818.3812104)—a specialized approach largely restricted to massive crowd scenes—we opted for an API schema to prioritize flexibility and generalization. This design adheres to contemporary USD philosophy by emphasizing type composition over inheritance, establishing a reusable pattern for future instance-overrides across various prim types. Furthermore, this approach preserves the ability to mix and match different prototype prim types; although this is not a recommended practice for performance optimization, maintaining such architectural versatility remains a key advantage.

### UsdSkelBakeSkinning

UsdSkelBakeSkinning should warn if asked to bake animation for a SkelRoot that is driven by this schema on an ancestor PI. We will address this in the next iteration **\[TODO\]**.

### Extents computation

This new feature raises concerns regarding the calculation of tight bounds—since it essentially makes the extent for each instance unique. Also, the per-instance extent for skelRoot prototypes will be computed without the overrides applied and thus incorrect (could be a series of entirely different poses). We propose the following for next iteration **\[TODO\]**: 

1. Add a per-instancer-API-schema override registry to UsdGeomPointInstancer and register an override extent provider keyed on an applied API schema type. Multiple providers may be registered; all are called and results are unioned.  
2. Modify UsdGeomPointInstancer::\_ComputeExtentFromTransforms() logic per prototype to apply all registered per-instance override providers first and union their results; if none apply, fallback to existing bboxCache code path.  
3. In usdSkel/root.cpp, register a provider keyed on UsdSkelInstancedAnimationSourcesAPI, we will have enough information to compute the extent union of a particular prototype with all its instance overrides.

However an architectural conflict arises when deferred skinning is active. Because this mode bypasses skinning computations entirely by deferring them to the vertex shader, attempting to calculate precise bounds would counteract the primary efficiency gains of utilizing deferred skinning.

Following a 6/18 discussion with spiff regarding authored v.s. computed extents:  
Pixar's current methodology involves precomputing and authoring extents on the SkelRoot during the asset build process. Rather than per-frame calculation, we decouple root motion from skelAnim; this allows for a single approximate bounds computation at the rest pose, with subsequent frames relying on the root transform. This workflow is executed via an export task, which invokes the SkelRoot [\_ComputeExtent()](https://github.com/PixarAnimationStudios/OpenUSD/blob/2d39590aac6dde875507d2a334ff6e5b9dc05fe1/pxr/usd/usdSkel/root.cpp#L142) function.  
In contrast, external clients typically do not decouple root motion from skelAnim, instead relying on *\_ComputeExtent()* to yield results that include applied root motion. We are awaiting a repro case to investigate reports that this function may currently be failing to provide accurate results in these scenarios.  
The following enhancements are discussed to refine extent accuracy:

* A "dial" attribute on the `SkelRoot` would allow users to select from varying levels of extent fidelity.  
* **Low Fidelity (Current):** This remains the most computationally efficient method.  
* **Medium Fidelity (Approximation):** Implements a configurable set of bones, such as pairing the root bone for motion with specific leaf bones.  
* **High Fidelity (Exact):** Compute precise extents similar to `UsdSkelBakeSkinning`.

In multi-skeleton scenario: compute extent for each and then union the results to enclose all.

### Pipeline Code Risk

The risk that existing pipeline code—specifically processes handling PointInstancers outside of Imaging—might be unaware that this schema fundamentally alters posing and evaluation behavior is considered minimal. Because using SkelRoot prototypes was historically unsupported, no legacy pipeline code exists to handle skeletal posing in this context. However, we must safeguard future pipeline development. To prevent issues when traversing or evaluating Skel data, we will add explicit documentation highlighting the risks and expected behaviors of processing SkelRoot prototypes alongside this new API schema **\[TODO\]**.  
