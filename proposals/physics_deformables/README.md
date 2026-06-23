# Deformable Body Physics in USD

**Status:** Draft — under active discussion in the [Alliance for OpenUSD (AOUSD)](https://aousd.org) Physics Working Group. Details are expected to evolve as the proposal is reviewed.

## Proposal document

> [!NOTE]
> **Full proposal:** [wp_deformable_physics.md](./wp_deformable_physics.md)
> — includes `.usda` examples and illustrative figures.

## Summary

After OpenUSD was extended with the ability to express rigid body physics in 2021, this proposal extends `UsdPhysics` with a basic, interoperable set of abstractions for **deformable body dynamics**, covering the elastic deformation of volumes, surfaces (e.g. cloth, shells), and curves (e.g. hair, rods).

The design goals follow those of the existing rigid body schema:

- A minimal, **backwards-compatible** addition that preserves the ability to load existing assets, including those that mix rigid and deformable content.
- **Interoperability** with the existing rigid body abstractions, so volume, surface, and curve deformables can be represented and believably simulated.
- Real-world engineering quantities for material properties, with USD's unit independence preserved.
- Material properties attached to materials rather than to simulated objects, and a preference for adding APIs to existing classes over introducing new prims.

## What the proposal covers

- Rigid body refactor that factors shared attributes into a `UsdPhysicsBodyAPI` pseudo-base, retaining backwards compatibility.
- Deformable materials for volumes, surfaces, and curves (Young's modulus, Poisson's ratio, thickness, and stretch/shear/bend/twist stiffness).
- Deformable bodies, simulation geometry, and rest shape (tetrahedral, triangular, and curve representations).
- Collision and graphics geometries, and point-based bind poses that support geometry embeddings.
- Material assignment and mass distribution.
- Kinematic deformables, attachments, and element collision filtering.

## New schema types

The proposal introduces the following `UsdPhysics` types:

| Type | Description |
| --- | --- |
| [`UsdPhysicsBodyAPI`](./wp_deformable_physics.md#rigid-body-refactor) | Pseudo-base body API factored out of the rigid body schema and shared with deformables. |
| [`UsdPhysicsDeformableBodyAPI`](./wp_deformable_physics.md#deformable-bodies) | Marks a prim and its subtree as a deformable body. |
| [`UsdPhysicsVolumeDeformableMaterialAPI`](./wp_deformable_physics.md#deformable-materials) | Material properties for volume deformables (Young's modulus, Poisson's ratio). |
| [`UsdPhysicsSurfaceDeformableMaterialAPI`](./wp_deformable_physics.md#deformable-materials) | Material properties for surface deformables (thickness, stretch/shear/bend stiffness). |
| [`UsdPhysicsCurvesDeformableMaterialAPI`](./wp_deformable_physics.md#deformable-materials) | Material properties for curve deformables (thickness, stretch/shear/bend/twist stiffness). |
| [`UsdPhysicsVolumeDeformableSimAPI`](./wp_deformable_physics.md#simulation-geometry-and-rest-shape) | Applied to a `UsdGeomTetMesh` to define a volume deformable's rest shape. |
| [`UsdPhysicsSurfaceDeformableSimAPI`](./wp_deformable_physics.md#simulation-geometry-and-rest-shape) | Applied to a triangular `UsdGeomMesh` to define a surface deformable's rest shape. |
| [`UsdPhysicsCurvesDeformableSimAPI`](./wp_deformable_physics.md#simulation-geometry-and-rest-shape) | Applied to a linear `UsdGeomBasisCurves` to define a curve deformable's rest shape. |
| [`UsdPhysicsDeformablePoseAPI`](./wp_deformable_physics.md#geometry-embeddings) | Multiple-apply API that authors the bind poses used to support geometry embedding. |
| [`UsdPhysicsAttachment`](./wp_deformable_physics.md#attachments) | Typed prim that attaches deformables to each other, to rigid bodies, or to a static frame. |
| [`UsdPhysicsElementCollisionFilter`](./wp_deformable_physics.md#element-collision-filtering) | Typed prim providing fine-grained, per-element collision filtering for deformable colliders. |

It also reuses or modifies existing types:

| Type | Change |
| --- | --- |
| [`UsdPhysicsRigidBodyAPI`](./wp_deformable_physics.md#rigid-body-refactor) | Refactored to share attributes via `UsdPhysicsBodyAPI`; adds `bodyEnabled`, retaining `rigidBodyEnabled` for backwards compatibility. |
| [`UsdPhysicsMaterialAPI`](./wp_deformable_physics.md#physics-material) | Reused for deformables, with `restitution` documented as ignored. |

## Notes

- This is a **work in progress**; the proposal is being developed and discussed in the AOUSD Physics Working Group, and the schema is subject to change.
- The proposal builds on, and is intended to interoperate with, the existing `UsdPhysics` rigid body schema. Prose refers to schema types by their C++ class names (e.g. `UsdPhysicsRigidBodyAPI`), while `.usda` examples use the registered token names (e.g. `PhysicsRigidBodyAPI`).
