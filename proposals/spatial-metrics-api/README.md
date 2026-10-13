# Spatial Metrics in USD

## Contents
- [Background](#background)
- [Potential Approaches](#potential-approaches)
- [Proposal](#proposal)
  - [Scope](#scope)
  - [UsdSpatialMetricsAPI](#usdspatialmetricsapi)
  - [UsdGeomSpatialMetricsXformCompensationAPI](#usdgeomspatialmetricsxformcompensationapi)
  - [Compensation Ordering](#compensation-ordering)
  - [Examples](#examples)
  - [Validators](#validators)
  - [Deprecation Cycle and Backward Compatibility](#deprecation-cycle-and-backward-compatibility)
- [Questions](#questions)
- [Future Considerations](#future-considerations)

## Background

USD's stage metadata (`metersPerUnit`, `upAxis`) doesn't compose well when
assets with different metrics are referenced into a single stage. Currently USD
doesn't provide any guidelines or compensation helpers for DCCs importing assets
with varied spatial metrics to conform and different pipelines and DCCs adopt
different mechanisms, for example, Houdini ignores any spatial metric an asset
advertises in its layer metadata when referencing it in, whereas NVIDIA's
Omniverse pipeline has a
["Metrics Assembler"](https://docs.omniverse.nvidia.com/extensions/latest/ext_metrics_assembler.html)
which provides means of bringing referenced asset in stage's metrics on the fly.

Also, since the information lives in the asset's layer metadata, referenced
assets lose this information during stage flattening.

The
[Proposal to Evolve Stage Metadata to Applied Schemas](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/revise_use_of_layer_metadata#proposal-to-evolve-stage-metadata-to-applied-schemas)
from Spiff discusses moving these layer metadata to prim attributes via a core
`UsdSpatialMetricsAPI` and provide helper utilities for clients to compensate
for the difference in the assets' and stage's metrics as per their needs, while
still retaining the asset's original metrics when flattening, etc.

## Potential Approaches

Below are some approaches considered for reconciling an asset's spatial metrics
with the referencing stage's.

### 1. Detect and Correct all affected data when referencing an asset

Continue to use layer metadata but correct all referenced assets if needed in
the stronger layer. This is very similar to what Omniverse's Metrics Assembler
does, that is when a DCC / Client detects that a "correctable" asset has been
referenced in, it loads and traverses the asset, finds **all the data** that
needs correcting (scales, axis swizzles, etc) as needed and writes the
corrections as overrides in a stronger layer.

This has at least the following 2 problems:

1. The highlighted **"all the data"**! USD does not have a semantic role for
   spatial data so determining what data to robustly and generically correct is
   a problem. Even if such roles are defined, all schemas will have to be
   updated and new schemas will have to make sure to include it explicitly; it
   may be difficult or impossible to track completely.
2. Since the "corrections" are overrides, it's a snapshot of the current state
   of the referenced asset. It suffers from the problem of becoming **stale**,
   when the underlying asset changes without any means of quickly detecting the
   stale state, which could be costly to determine.

### 2. Perform a JIT correction during value resolution

If we knew what data needs spatial corrections (semantic tagging of data from
above), we could have used this information during value resolution along with
the metrics computed and cached by UsdStage during population. Hence
Just-In-Time computation to transform the appropriate data during value
resolution. But this also faces some big hurdles:

1. Like above, we will need all data semantically tagged with appropriate
   information.
2. Expensive, and violates the zero-copy optimizations during value resolution.
3. Heavily obfuscates the authored data.

### 3. Explicit intent of specifying spatial metrics via applied APISchema (Proposed)

We take a more conservative approach, drawing on Spiff's proposal referenced
above, specifically, moving spatial metrics layer metadata onto prims via an
applied API schema. We propose to introduce a new `UsdSpatialMetricsAPI` on the
prim, which provides for its subtree's spatial information (`upAxis` and
`metersPerUnit`). This allows easy detection of differences in spatial metrics
for a referencing asset and DCC / Clients can then explicitly apply a
compensating `UsdGeomSpatialMetricsXformCompensationAPI` which also provides
appropriate compensations.

- Doesn't obfuscate any authored data
- Composes non-destructively over the referenced asset (compensation ops are
  added to `xformOpOrder` via `AddXformOp`, creating a new, complete 
  specification for the `xformOpOrder`).
  - Additionally asset changes can be easily detectable.
- And sidesteps the "semantic roles for spatial metrics" problem entirely,
  because compensation is a single transform on the referenced subtree rather
  than a per-attribute data rewrite.
- This results in explicit xformOps authored on the prim, which might go
  out-of-sync, which we plan to handle via validators.

The proposal below describes `UsdSpatialMetricsAPI` and
`UsdGeomSpatialMetricsXformCompensationAPI`, however we also provide an alternative
to `UsdGeomSpatialMetricsXformCompensationAPI` for discussion purposes.

#### Alternative compensation mechanism: compute-on-the-fly in core transform

Instead of having explicit `xformOps` authored on the prim via
`UsdGeomSpatialMetricsXformCompensationAPI`, we can have the core transform
computation apply the necessary computations on the fly.
`UsdGeomXformCache::_GetCtm` composes a prim's transform as
`ctm(prim) = localXform(prim) * ctm(parent)`; this could be extended so that
when a prim has `UsdSpatialMetricsAPI` applied and its metrics differ from its
parent's effective metrics, the compensating transform is injected into that
composition directly. The prim's computed transform would then reflect the
reconciliation.

However, there are some trade-offs:

1. **It becomes part of the normative Geom Spec**: A prim's transform would be
   defined to depend on its `UsdSpatialMetricsAPI` relative to its ancestors,
   changing the meaning of `ComputeLocalToWorldTransform` for all clients.
2. **DCCs might have to re-implement it natively for imported USD assets:** DCCs
   such as Maya translate a prim's authored transform data into their own native
   transform systems on import and they do not evaluate through USD's transform
   computation. A compensation that exists only as a value computed inside core
   USD transform computations and never as authored scene description, will
   therefore not be reflected in the DCC's native transforms unless that DCC
   re-implements similar logic.
3. **No opt-out of compensation utility:** As noted in the introduction, DCCs or
   pipelines differ in how they handle referenced metrics (at least at present).
   Houdini ignores an asset's advertised metrics, while NVIDIA uses their
   Metrics Assembler when importing assets. Baking compensation into USD core
   transformation computation means removing this flexibility. With this every
   client routing through USD core's transform would get compensation applied
   unconditionally. The `UsdGeomSpatialMetricsXformCompensationAPI` on the other
   hand, keeps compensation an explicit, opt-in decision, so that a pipeline
   chooses whether to author it, whether to honor it and whether to run the
   validators that check it.
4. **Transform-only**. A computed compensating transform can only reconcile
   transformable data. Metric-aware attributes in other domains -- e.g. a
   `PhysicsScene`'s `physics:gravityMagnitude` -- cannot be fixed by a transform
   at all, so a compute-on-the-fly mechanism leaves them unreconciled.

Given these trade-offs we plan to proceed with the authored
`UsdGeomSpatialMetricsXformCompensationAPI`.

## Proposal

### Scope

- **`UsdSpatialMetricsAPI`**

  A single-apply API schema defined in core *usd* schema domain, in order to
  maintain the stage level access of these spatial metrics. These will impart
  builtin spatial metrics specific properties to the prim, `upAxis`,
  `metersPerUnit` to begin with.
  - Utility functions to query effective spatial metrics for a given prim
    (ancestor inheritance, etc).

- **`UsdGeomSpatialMetricsXformCompensationAPI`**

  A companion single-apply API schema defined in *usdGeom* schema domain.
  `CanOnlyApply` to `UsdSpatialMetricsAPI`.
  - This declares builtin compensation xformOps (suffixed with
    `metricsCompensation`)
  - Provides compensation methods, which make use of these builtin xformOps.

- **Backward compatibility with current spatial metrics layer metadata.** Given
  the nature of this update, we expect this to have a long tail.
  - `UsdSpatialMetricsAPI`'s utility functions will fallback to layer metadata.
  - Environment variable controlled phased removal of these layer metadata
    - Phase 1: Introduce environment variable with new mechanics in place
    - Phase 2: Allowed, but warn on usage
    - Phase 3: Disallowed, but environment variable retained so clients can
      explicitly (selectively?) continue to use layer metadata
    - Phase 4: Environment variable removed.

### UsdSpatialMetricsAPI

`UsdSpatialMetricsAPI` will be introduced in core usd schema domain (under
*pxr/usd/usd*) and will provide the following properties:

| Name | Type | Default | Notes |
|------|------|---------|-------|
| `spatial:metersPerUnit` | `double` | `0.01` | Meters per encoded unit. Default = centimeters to match current metersPerUnits metrics defined in usdGeom |
| `spatial:upAxis` | `token` | `'Y'` | Allowed: `'Y'`, `'Z'`. Matches current usdGeom allowed values. |

#### Inheritance Behavior

`UsdSpatialMetricsAPI` is authoritative for the prim it's applied on and its
descendants until a descendant prim has the API applied.

#### UsdSpatialMetricsAPI on subroot references

`UsdSpatialMetricsAPI` may be applied at any prim, not only root prims.
Sub-root references -- e.g. referencing a subcomponent model into a larger
assembly -- are explicitly supported and not restricted. The inheritance behavior
above, together with the spatial-metrics consistency validator (see 
[Validators](#validators)),
reconciles metrics at any depth in the hierarchy, so there is no requirement
that the API live only on root prims.

#### Authoring

It is recommended for DCC / clients to author `UsdSpatialMetricsAPI` on prims
likely to be referenced, for example all root prims, and in particular the
`defaultPrim` specified in the root layer. Validators will be added as part of
this work for clients to validate their assets against.

For backward-compatibility purposes, we plan to provide an authoring API that,
when clients use it, authors the `UsdSpatialMetricsAPI` attribute and -- while
the backward-compatibility environment variable is in effect -- additionally
authors the corresponding layer metadata. This keeps assets readable by both new
and legacy consumers during the transition, without each client having to
dual-author.

```cpp
// Authoring helpers on UsdSpatialMetricsAPI. These apply the API
// Schema and author the schema attributes and, while the
// backward-compat environment variable is in effect, additionally
// author the corresponding layer metadata.
static bool UsdSpatialMetricsAPI::ApplyAndAuthorMetersPerUnit(
    const UsdPrim& prim, double metersPerUnit);

static bool UsdSpatialMetricsAPI::ApplyAndAuthorUpAxis(
    const UsdPrim& prim, const TfToken& upAxis);

static bool UsdSpatialMetricsAPI::ApplyAndAuthorSpatialMetrics(
    const UsdPrim& prim, double metersPerUnit, const TfToken& upAxis);
```

#### Utility Methods

```cpp
static TfToken UsdSpatialMetricsAPI::ComputeEffectiveUpAxis(
    const UsdPrim& prim);

static double UsdSpatialMetricsAPI::ComputeEffectiveMetersPerUnit(
    const UsdPrim& prim);
```

As mentioned in the Inheritance Behavior section above, these APIs will
appropriately provide the effective `upAxis` or `metersPerUnit` for a given prim
by doing the following:

1. Check if the prim itself has `UsdSpatialMetricsAPI` applied, and if so use
   the attribute values from itself.
2. If not, walk up the prim hierarchy, until a prim with
   `UsdSpatialMetricsAPI` applied is found and use its attribute values.
3. If no ancestor is found which has `UsdSpatialMetricsAPI` applied, then
   fallback to the layer metadata (backward compat); and if that is also
   absent, to the documented schema fallback (`Y` / `0.01`). Refer to the 
   backward compatibility section below for more details.

`ComputeEffective*` always returns a value: if no ancestor has the API applied
and there is no authored layer metadata (backward compat), it returns the
documented schema fallback (`upAxis = "Y"`, `metersPerUnit = 0.01`). It never
fails to produce a metric. The absence of authored metrics on the
defaultPrim/root is instead surfaced by validation.

### UsdGeomSpatialMetricsXformCompensationAPI

`UsdGeomSpatialMetricsXformCompensationAPI` is a single applied API schema, which
**can only apply** to prims which have `UsdSpatialMetricsAPI` applied. This API
which is defined in the `usdGeom` schema domain, provides the following
**builtin xformOp**, to provide appropriate compensation transformations to be
applied on a referenced asset to conform to the current stage's spatial metrics.

The API provides the following properties / xformOps:

| Name | Type | Default |
|------|------|---------|
| `metricsCompensation:desired` | `bool` | `true` |
| `xformOp:scale:metricsCompensation` | `float3` | `(1,1,1)` |
| `xformOp:rotateX:metricsCompensation` | `float` | `0` |

Since `spatial:upAxis` is restricted to `'Y'` and `'Z'`, the compensating
rotation is always about the `X` axis; only its sign differs.

`metricsCompensation:desired` records the author's intent. Setting it to `false`
states that the referenced asset should retain its own spatial metrics and
deliberately not be reconciled to the referencing context, distinguishing an
intentional decision from an unreconciled mistake. This intent cannot be inferred
from the compensation `xformOps` themselves: their absence is indistinguishable
from an author simply having forgotten to compensate, so an explicit opinion is
needed to tell a deliberate decision apart from an unreconciled mistake. Nor can
it be inferred from the presence of the `xformOps`: because the compensation
`xformOps` are declared builtin properties with identity fallbacks, they exist
on the prim as soon as the API is applied, even if the client never calls the
compensation utilities. A prim carrying identity-valued compensation `xformOps`
is therefore ambiguous -- it may mean the client applied the API and did not
author values, or that no compensation is intended.
`metricsCompensation:desired` makes that distinction explicit.

Compensation for spatial transformation is "explicit", which the DCC Application
will have to apply to transform the referenced asset if needed in the
referencing stage's spatial metrics.

Compensation `xformOps` are authored on the current edit target. USD Core does
not create or manage a separate compensation layer. Clients can however provide
a compensation specific layer, like "MetricsAssembler Layer" NVIDIA's Metrics
Assembler provides, which implements an automatic compensation example via a
drag-and-drop listener or other asset importing hooks, and a background change
listener, to update the compensation. Note that this can now use the utility
methods provided by `UsdGeomSpatialMetricsXformCompensationAPI` to add these new
`xformOps`.

Compensation ops are added to `xformOpOrder` via `AddXformOp`, which places
them at the end of the order (most local -- applied first to geometry). See
[Compensation Ordering](#compensation-ordering) for details on how `AddXformOp`
handles the interaction between compensation ops and non-compensation ops.

Note on `!resetXformStack!`: The compensation utilities do not attempt to work
around `!resetXformStack!`. A reset could appear not only on the compensated
prim itself but also on a descendant, making special handling impractical.
`!resetXformStack!` is an intentional authoring decision: if a prim resets its
transform stack, it is deliberately opting out of inherited parent transforms,
including any compensation on an ancestor.

#### Compensation Ordering

Compensation ops are authored at the **end** of `xformOpOrder` (most local),
so they are applied first to the descendant geometry, converting it from the 
asset's metric space into the referencing prim's metric space. We want any
referencing-side ops appended to the prim to operate in the post-compensation
space.

For example, given an asset authored in centimeters / Z-up referenced into a
meters / Y-up assembly:

```
xformOpOrder = ["xformOp:translate",
                "xformOp:rotateX:metricsCompensation",
                "xformOp:scale:metricsCompensation"]
```

A point `P` transforms as:
`P' = translate * rotateX:metricsCompensation * scale:metricsCompensation * P`

1. `scale:metricsCompensation` scales from centimeters to meters
2. `rotateX:metricsCompensation` rotates the descendant geometry from Z-up to Y-up
3. `translate` (referencing-side op) applies in the post-compensation space, 
i.e. in meters.

**`AddXformOp` compensation-aware insertion.** To maintain this ordering, 
`AddXformOp` is taught the following logic when `metricsCompensation` named ops 
are present in `xformOpOrder`:

- Adding a **`metricsCompensation`** named op: push to the end (stays most
  local).
- Adding a **non-`metricsCompensation`** op when `metricsCompensation` named
  ops exist in the order: insert before the first `metricsCompensation` op, so
  it operates in the post-compensation (assembly) space.
- Adding a **non-`metricsCompensation`** op when no `metricsCompensation` ops
  exist: normal push to the end.

**This ensures that an assembly asset author who calls `AddXformOp` to position
or orient a referenced asset gets an op that operates in the assembly's units
and orientation, not the asset's.**

**Re-compensation.** When a previously-compensated prim is referenced into a
stage with different metrics, the compensation ops are already in the composed
`xformOpOrder` (from the reference). The utility method detects this and updates 
the existing ops' values via `Set()` -- recomputing from the prim's declared 
source metric to the new target -- rather than calling `AddXformOp` again. On 
the referencing layer, `Set()` creates a stronger opinion that shadows the
referenced layer's old compensation value. If the reference is later removed,
the old compensation value is still intact underneath.

The compensation always goes from the prim's declared source metric to the
next-closest ancestral SpatialMetrics frame in one step.

#### Utility Methods

```cpp
// instanced methods
bool UsdGeomSpatialMetricsXformCompensationAPI::CompensateMetersPerUnit(
    double targetMetersPerUnit);

bool UsdGeomSpatialMetricsXformCompensationAPI::CompensateUpAxis(
    TfToken targetUpAxis);

bool UsdGeomSpatialMetricsXformCompensationAPI::CompensateSpatialMetrics(
    double targetMetersPerUnit, TfToken targetUpAxis);

// helper static methods which also apply the UsdGeomSpatialMetricsXformCompensationAPI
static bool UsdGeomSpatialMetricsXformCompensationAPI::ApplyAndCompensate(
    const UsdPrim prim, double targetMetersPerUnit, TfToken targetUpAxis)
```

As mentioned above clients need to explicitly apply
`UsdGeomSpatialMetricsXformCompensationAPI` and then they can use the instanced
`CompensateMetersPerUnit` or `CompensateUpAxis` methods appropriately on the
prim they need the compensation `xformOps` applied to.

We also plan to provide a static helper API `ApplyAndCompensate`, which applies
the `UsdGeomSpatialMetricsXformCompensationAPI` on the specified prim and then
calling the compensate methods.

These methods manage `xformOpOrder` via the modified `metricsCompensation` aware 
`AddXformOp`, placing the compensation ops at the most-local position so that 
any subsequent client-authored transforms take the compensation into account. 
The compensation op attributes always exist on a prim with the API applied (they
are builtins with identity fallbacks), but may not be in `xformOpOrder`. The 
utility method checks the composed `xformOpOrder` first: if the ops are already 
present, it updates their values via `Set()`; otherwise it calls `AddXformOp`. 
This check is required because `AddXformOp` raises a coding error on duplicate 
entries. See [Compensation Ordering](#compensation-ordering) for details.

#### Compensation Workflow

1. Query the prim's effective metric via
   `UsdSpatialMetricsAPI::ComputeEffective*` API
2. Compare against the `target*` argument
3. If they differ, then set the compensation `xformOp` value and add it to
   `xformOpOrder` appropriately.
4. If they match, do nothing. Additionally if the
   `UsdGeomSpatialMetricsXformCompensationAPI` is applied, then unapply it. (DCC
   Applications can use this appropriately to remove stale compensations).

#### Pseudocode for CompensateMetersPerUnit

```
CompensateMetersPerUnit(prim, targetMetersPerUnit)
    primMPU = UsdSpatialMetricsAPI::ComputeEffectiveMetersPerUnit(prim)
    if (primMPU == targetMetersPerUnit):
        # nothing to do for compensation
        # remove the API if it is applied.
        # (note that only the static convenience method will remove the API,
        #  instanced method will not)
        return true

    scaleFactor = primMPU / targetMetersPerUnit
    # set xformOp:scale:metricsCompensation using scaleFactor
    # append to xformOpOrder via AddXformOp (or Set() if already in order)
    return true
```

A similar approach will be used for `CompensateUpAxis`.

#### Why not autoApply to UsdSpatialMetricsAPI?

Compensation `xformOps` might not be required in all scenarios, and if
`UsdGeomSpatialMetricsXformCompensationAPI` is auto applied to
`UsdSpatialMetricsAPI`, it's noisy and confusing to see the extra
`xformOp:scale:metricsCompensation` and
`xformOp:rotateX:metricsCompensation` with their respective default values on
all prims on which `UsdSpatialMetricsAPI` is applied. Additionally an explicit
application of `UsdGeomSpatialMetricsXformCompensationAPI` means it's a meaningful
breadcrumb, to signal that compensation is happening (or expected) on the prim.

#### XformCommonAPI compatibility (not)

`UsdGeomXformCommonAPI` recognizes only a fixed set of ops (to cater to some
DCCs specifically) in a specified order:
`["xformOp:translate", "xformOp:translate:pivot", "xformOp:rotateXYZ", "xformOp:scale", "!invert!xformOp:translate:pivot"]`.
The suffixes introduced by `UsdGeomSpatialMetricsXformCompensationAPI` fall outside
this list and hence do not conform to `UsdGeomXformCommonAPI`.

Note that this is not special to compensation `xformOps` -- it applies to any
client authored ops outside `UsdGeomXformCommonAPI`, readers either consume via
`xformOpOrder` directly or flatten it on import.

#### Compensation for non-transformable attributes

Compensation is not limited to transforms. Other schema domains may have
metric-aware attributes that need reconciling and cannot be expressed as an
`xformOp` -- for example a `PhysicsScene`'s `physics:gravityMagnitude`
(`9.8 m/s^2`) must change if the asset is referenced into a stage with a
different `metersPerUnit`. Because `UsdGeomSpatialMetricsXformCompensationAPI` marks
the prim as metric-compensated, clients of other domains can key their own
compensation behavior off it. The `xformOps` are usdGeom's realization of
compensation; the API schema is what makes the concept addressable by other
domains.

**Physics Scene Asset being imported (physicsScene.usda):**
```usda
#usda 1.0

def PhysicsScene "Scene" (
    prepend apiSchemas = ["SpatialMetricsAPI"]
) {
    double spatial:metersPerUnit = 1
    float physics:gravityMagnitude = 9.8
}
```

**ReferencingLayer.usda with CompensationAPI on imported Physics Scene asset:**
```usda
#usda 1.0

def Xform "World" (
    prepend apiSchemas = ["SpatialMetricsAPI"]
) {
    double spatial:metersPerUnit = 0.1

    def PhysicsScene "SceneRef" (
        references = @physicsScene.usd@</Scene>
        prepend apiSchemas = ["SpatialMetricsXformCompensationAPI"]
    ) {
    }
}
```

`physics:gravityMagnitude` is not transformable; no `xformOp` can fix it.
Because `UsdGeomSpatialMetricsXformCompensationAPI` is applied to
`/World/SceneRef`, physics clients / `usdPhysicsParser` can key off that marker
to attach their own compensation behavior - scaling `gravityMagnitude`
appropriately for the differing `metersPerUnit`. The `xformOps` are `usdGeom's`
realization of compensation; the API schema is what makes the concept
addressable by other domains.

### Examples

**Asset with `Z` spatial:upAxis:**
```usda
#usda 1.0

def Xform "Asset" (
    prepend apiSchemas = ["SpatialMetricsAPI"]
) {
    token spatial:upAxis = "Z"
    double3 xformOp:translate = (0, 0, 5)
    uniform token[] xformOpOrder = ["xformOp:translate"]

    def Mesh "Body" {
        # geometry authored with Z-up
        point3f[] points = [(0, 0, 0), (100, 0, 0), (100, 100, 0), ...]
    }
}
```

**Refer this asset in a stage with `Y` spatial:upAxis:**
```usda
#usda 1.0

def Xform "World" (
    prepend apiSchemas = ["SpatialMetricsAPI"]
) {
    token spatial:upAxis = "Y"
    def Xform "AssetRef" (
        references = @asset.usd@</Asset>
    ) {
        # Composed asset is Z-up; stage is Y-up -- upAxis mismatch
        # (metersPerUnit matches at default 0.01)
    }
}
```

**Client / DCC detects the mismatch, applies the
`UsdGeomSpatialMetricsXformCompensationAPI` or uses the static utility method on
the referenced prim, and compensates:**
```usda
def Xform "AssetRef" (
    prepend apiSchemas = ["SpatialMetricsXformCompensationAPI"]
    references = @asset.usd@</Asset>
) {
    # compensation ops added via AddXformOp (most local, applied first to geometry)
    uniform token[] xformOpOrder = [
        "xformOp:translate",
        "xformOp:rotateX:metricsCompensation",
        "xformOp:scale:metricsCompensation"
    ]
    float3 xformOp:scale:metricsCompensation = (1, 1, 1)
    float xformOp:rotateX:metricsCompensation = -90
}
```

### Validators

1. **`rootPrims` must have `UsdSpatialMetricsAPI` applied:** Stage level
   validator to make sure `UsdSpatialMetricsAPI` is applied to the `rootPrims`
   for the stage. Should be added to `coreValidators`.

2. Sub-root references should have `UsdSpatialMetricsAPI` directly applied. A
   prim with authored references (`prim.HasAuthoredReferences()`) that does not
   have `UsdSpatialMetricsAPI` directly applied (only inherited from the
   referencing context) may have lost its source metric across the reference
   arc. This validator warns so the asset author can apply the API on the
   intended-to-be-referenced prim. A fixer is provided, which will open the
   referenced layer on a stage masked to the referenced prim (which will compose
   all of the prim's ancestors). It then inspects the referenced layer to
   recover the source prim's effective `SpatialMetricsAPI` values, applies the
   `UsdSpatialMetricsAPI` on the referenced prim with the original values, and
   applies appropriate compensation. Very likely this validator will not be
   included in the default set of usdGeom or usdCore validators.

3. **Spatial metrics on a referenced prim must match the stage's prim:**
   Example: A `Lamp` prim (Y-up) references a `@bulb.usda@</Bulb>` (Z-up) at
   `/Lamp/Bulb`. After referencing, compensation is not applied on `Bulb` and
   hence causing `/Lamp/Bulb` to have different metrics to its ancestor's
   `upAxis` (or stage's `upAxis`). This validator should error and point out
   that compensation must be applied for the referenced asset to match the
   stage's metrics. This should be added to `usdGeomValidators`.

   This validator should not error when `metricsCompensation:desired` is
   `false`, as the mismatch is then the author's stated intent.

4. **Compensation must reconcile the metric difference:** a prim has
   `UsdGeomSpatialMetricsXformCompensationAPI` applied and
   `metricsCompensation:desired` is `true`, but the authored compensation does
   not reconcile the prim's spatial metrics with its effective ancestor metrics.
   This validator should error.

5. In cases where an API is applied, a `usd.geom.spatialMetrics` capability
   could be validated because an asset could signal that spatial compensation is
   required for correct interpretation of the asset (assuming it's decided to
   add a capability for this).

6. When `metricsCompensation:desired` is `false`, the compensation `xformOps`
   and `xformOpOrder` must not be explicitly authored, irrespective of their
   values. This validator should error.

7. **Compensation ops must be adjacent in `xformOpOrder`:**
   `xformOp:rotateX:metricsCompensation` and 
   `xformOp:scale:metricsCompensation` must appear adjacent in
   `xformOpOrder` with no other ops between them (rotateX first, then scale).
   The compensation utility always authors them in this order so that together
   they form a single atomic metric conversion at the most-local position in
   the op stack (see [Compensation Ordering](#compensation-ordering)). An op
   between them would break the conversion. This validator should error.

### Deprecation Cycle and Backward Compatibility

Phased rollout guarded by an environment variable:

- **Phase 1:** Introduce an environment variable with new mechanics in place.
- **Phase 2:** Layer metadata fallback allowed, but warn on usage.
- **Phase 3:** Layer metadata fallback disallowed, but environment variable
  retained.
- **Phase 4:** Environment variable removed.

The following functions in `pxr/usd/usdGeom/metrics.h` are superseded by
`UsdSpatialMetricsAPI` query utilities and should be deprecated:

- `UsdGeomGetStageMetersPerUnit()`
- `UsdGeomSetStageMetersPerUnit()`
- `UsdGeomStageHasAuthoredMetersPerUnit()`
- `UsdGeomGetStageUpAxis()`
- `UsdGeomSetStageUpAxis()`
- `UsdGeomGetFallbackUpAxis()`

The following are constants which are used in metrics conversion and can be /
should be retained:

- `UsdGeomLinearUnits`
- `UsdGeomLinearUnitsAre()`

#### Plugin-configurable upAxis fallback - not carried forward

Today `upAxis` supports a site-wide fallback default that studios can configure
via a `UsdGeomMetrics.upAxis` entry in their pipeline's `plugInfo.json` (Refer
`UsdGeomGetFallbackUpAxis()`). 

We do not plan to provide an equivalent for the new schema-based approach.
`UsdSpatialMetricsAPI` uses fixed schema fallbacks
(`upAxis = "Y"`, `metersPerUnit = 0.01`), and the plugin configurable fallback
is retained only for the legacy layer-metadata path during the backward
compatibility window.

It's important to note that plugin configurability for this is undesirable for
portable assets. An asset can appear correct inside the studio because of the
plugin provided fallbacks, but when published for external consumption, the
internal plugin provided fallback will not apply causing the asset to break for
external clients.

## Questions

### ForwardDirection / Handedness

A `forwardDirection` hint, or an equivalent handedness token, could be added as a
third spatial metrics. We are **not** proposing it, for the following reasons:

- Unlike `upAxis` and `metersPerUnit`, a `handedness` / `forwardDirection`
  cannot be reconciled with a simple compensating `xformOp`. `upAxis` is
  compensated by a **rotation** and `metersPerUnit` by a **uniform scale**, both
  determinant positive transforms expressible as a single `xformOp`. A
  handedness difference, on the other hand is a "reflection", i.e. negative
  determinant, and reconciling it correctly requires a full change of basis
  (`B = P*A*P^-1`) applied to **all of the asset's data** -- points, normals,
  etc and not just a transform op on the prim. (Refer to Jeremy Cowles' well 
  written article on the topic:
  https://medium.com/data-science/change-of-basis-3909ef4bed43)
- It also relies on a right axis being `+X` assumption to derive the third
  axis, which even though many graphics systems we know of agree upon, but might
  not be universally safe. Additionally a `handedness` / `forwardDirection` hint
  could **disagree** with the authored `upAxis` which adds to more confusion
  (even though we can have validators for this).

## Future Considerations

### UsdPhysicsMetricsAPI

Consider adding a `UsdPhysicsMetricsAPI` for `kilogramsPerUnit`, mirroring
`UsdSpatialMetricsAPI`, together with a companion
`UsdPhysicsMetricsCompensationAPI` (analogous to
`UsdGeomSpatialMetricsXformCompensationAPI`) that provides the compensation
utilities.

**Some Details.** Though unlike spatial metrics, mass-metric compensation cannot
be expressed as a single `xformOp` -- it requires scaling individual attribute
values (`physics:mass`, `physics:density`, etc.), some of which depend on both
`metersPerUnit` and `kilogramsPerUnit`. Authored attribute-value scaling
(Approach 1) is actually more tractable for physics than it was for spatial. The
mass-dependent attributes are a closed, schema-defined set (`physics:mass`,
`density`, `diagonalInertia`, `joint: breakForce / breakTorque`,
`drive: stiffness / damping / maxForce`), so there is no open-ended "find all
the scalar data" / semantic-role discovery problem we faced for spatial -- a
utility can enumerate exactly what to scale.

The harder question is keeping compensation self-describing, the way the named
compensation `xformOp` is for spatial. If physics compensation scales
`physics:mass` in place, the compensation dissolves into the authored value --
the breadcrumb is lost, and (unlike spatial) it cannot be recovered from
`kilogramsPerUnit` alone. The direction that mirrors the spatial design is a
named multiplier attribute declared by a companion
`UsdPhysicsMetricsCompensationAPI` (`CanOnlyApply` to
`UsdPhysicsMetricsAPI`) -- e.g. `physics:metrics:compensation:mass` -- that mass
computations consume, leaving authored values untouched. This works cleanly for
the computed mass quantities: `physics:mass` / `density` / `diagonalInertia`
already flow through `UsdPhysicsRigidBodyAPI::ComputeMassProperties()` and
`UsdPhysicsMassProperties`, which already exposes an `operator*(scale)` -- the
named `physics:metrics:compensation:mass` is exactly the scale it would apply,
yielding an effective mass.

The independent dimensional quantities (`breakForce`, `breakTorque`, drive
`stiffness` / `damping` / `maxForce`) have no core computation to route a
multiplier through -- they are consumed directly by a physics simulator and
remain the open case.

This is a natural follow-up to the spatial metrics work, but the design space
differs and warrants its own discussion.

### OpenExec Compensation Computations - considered, not pursued

We discussed with the OpenExec folks whether compensation could instead be
provided as an exec computation that applies the compensating transformation
automatically. The conclusion was that authored scene description is preferable:
an exec-computed transform addresses only the transform, and cannot handle
metric-aware attributes that are not transformable (see the
`physics:gravityMagnitude` example above). Keeping the compensation in scene
description also keeps it inspectable, validatable, and consumable by clients
that do not run exec.

### Geospatial considerations

Geospatial coordinate systems typically involve a multi-tier coordinate frame,
for example, a geodesic index and barycentric coordinates in the geodesic frame
which ultimately need to be resolved to a local cartesian frame. Probably these
can also be addressed in a similar manner in the appropriate Geospatial domain
of schemas.
