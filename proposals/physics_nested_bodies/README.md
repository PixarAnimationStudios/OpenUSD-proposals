# Physics Nested Bodies

## Summary

This proposal amends the UsdPhysics Schema documentation & validation code to allow PhysicsRigidBodyAPI prims to have ancestor & descendant PhysicsRigidBodyAPI prims, even without the use of a resetXformStack XformOp.

## Background

[UsdPhysics](https://openusd.org/release/api/usd_physics_page_front.html) is designed around rigid body simulators, which take as input a list of rigid bodies and a list of constraints. In particular, most design decisions are based on multi-body simulation, in which bodies are modeled as single, independent entities in world space, which by default move and respond to forces and torques independently. Constraints are used to reduce the degrees of freedom between two bodies.

Another approach to physics simulation is a reduced coordinate system for articulated bodies, which is often used to model complex systems with multiple interconnected rigid bodies, such as robots, characters, or real-world mechanisms. Articulated bodies are systems composed of a kinematic tree of rigid bodies connected by joints, hinges, or other constraints. The motion of each body is described relative to its parent body or a reference frame, rather than using absolute coordinates. This helps to eliminate redundant degrees of freedom and reduces the dimensionality of the system.

Both approaches have common concepts (i.e. rigid bodies and joints/constraints) and should ideally be modeled in USD using the same schemas: [PhysicsRigidBodyAPI](https://openusd.org/release/api/class_usd_physics_rigid_body_a_p_i.html) and [PhysicsJoint](https://openusd.org/release/api/class_usd_physics_joint.html).

UsdPhysics also already provides the [PhysicsArticulationRootAPI](https://openusd.org/release/api/class_usd_physics_articulation_root_a_p_i.html) to mark the root of a subtree for a reduced coordinate [articulation](https://openusd.org/release/api/usd_physics_page_front.html#usdPhysics_articulations).

## Problem Statement

The current UsdPhysics Schema documentation specifically forbids nesting rigid bodies in a section on [Interaction with the USD hierarchy](https://openusd.org/release/api/usd_physics_page_front.html#usdPhysics_interaction_with_usd). There is an exception made for prims with a [resetXformStack op](https://openusd.org/release/api/class_usd_geom_xformable.html#a6d16bc5455344e131683d91e14ab62db), which is effectively saying that all rigid bodies must be in world space.

Additionally, in USD 25.05, UsdValidation rules for UsdPhysics have been added which enforce this nesting restriction & additionally enforce that articulations cannot be kinematic.

These restrictions are at odds with the reduced coordinate approach, where bodies are described relative to a parent body or a reference frame.

It makes mapping reduced coordinate datasets to USD cumbersome for developers and confusing for content creators and consumers.

The PhysicsArticulationRootAPI concept in itself implies a nested hierarchy of prims, yet such nesting is forbidden in USD hierarchy, and only exists via a computed tree of bodies and joints. It is logical to use this API to markup all articulation roots, however UsdValidation currently disallows its use on kinematic bodies, which effectively disallows kinematic articulations.

## Proposed Change

### Documentation

Amend the UsdPhysics Schema documentation to allow nested rigid bodies, even without the use of resetXformStack.

Make clear the intent of PhysicsArticulationRootAPI with respect to reduced coordinate simulators, why nested bodies are allowed, and add a functional example of an articulated system in the [Examples](https://openusd.org/release/api/usd_physics_page_front.html#usdPhysics_examples) section at the bottom of the document.

Update the "aggregate properties" paragraph to describe the logic change in [Mass Computation](#mass-computation).

Add a description of fully or partially kinematic articulations within the Articulation subsection & update the Kinematic Bodies subsection to refer to it.

### Mass Computation

Update the logic in `UsdPhysicsRigidBodyAPI::ComputeMassProperties` to prune traversal when a descendant PhysicsRigidBodyAPI is encountered (i.e. child bodies do not contribute to the mass or volume of the parent body).

### Validation

Update the [NestedRigidBody](https://github.com/PixarAnimationStudios/OpenUSD/blob/dev/pxr/usdValidation/usdPhysicsValidators/validatorTokens.h#L28) validation error to allow nesting within articulations.

Update the [ArticulationOnKinematicBody](https://github.com/PixarAnimationStudios/OpenUSD/blob/dev/pxr/usdValidation/usdPhysicsValidators/validatorTokens.h#L31) validation error to allow kinematic bodies which start at the root of an articulation and continue down hierarchy, until the first non-kinematic body is encountered. Once a non-kinematic body is found, the remainder of the articulation must also be non-kinematic. In other words, fully or partially animated articulations are allowed, provided they are not interleaved with simulated bodies.

### Parsing Utils

The physics parsing utilities added in USD 25.05 do already allow nested bodies to be parsed successfully.

However, in the case of the PhysicsArticulationRootAPI being applied as an ancestor of the root PhysicsRigidBodyAPI, the parser currently attempts to find the center of the graph to use as the root. It will need to be changed to explicitly select the top-most body within the articulation hierarchy as the root.

Additionally, parsed nested bodies will have values computed in world space rather than parent-body space, which may be unexpected for the reduced coordinate simulation consumer. This caveat should be clearly documented so consumers know to compute relative coordinates if they are required.

## Example

### MuJoCo Scene Description

Below is a partial example of a reduced coordinate scene description in XML-based MJCF format, used by the OSS [MuJoCo simulator](https://github.com/google-deepmind/mujoco), which shows the rigid bodies & joints of a single finger on a robotic hand.

The details of MJCF format are not relevant here, what is important to note is that the dataset has a clear hierarchy of bodies & joints. They have meaningful names within a relative hierarchy, which loose meaning if the hierarchy was flattened to a list. They are positioned and oriented relative to their parents, which requires recomputation & possible precision loss when flattening to world space.

```
<worldbody>
    <body name="palm" pos="0 0 0.1" quat="0 1 0 0">
        <body name="index_finger_base" pos="-0.007 0.023 -0.0187" quat="0.500003 0.5 0.5 -0.499997">
            <joint name="metacarpophalangeal"/>
            <body name="proximal" pos="-0.0122 0.0381 0.0145" quat="0.500003 -0.5 -0.499997 0.5">
                <joint name="rotational"/>
                <body name="middle" pos="0.015 0.0143 -0.013" quat="0.500003 0.5 -0.5 0.499997">
                    <joint name="proximal_interphalangeal"/>
                    <body name="distal" pos="0 -0.0361 0.0002">
                        <joint name="distal_interphalangeal"/>
                    </body>
                </body>
            </body>
        </body>
    </body>
</worldbody>
```

### Current UsdPhysics Equivalent

In order to obey the current UsdPhysics requirements, the hierarchy above needs to be flattened into a list of bodies and a list of joints.

This flattening results in a loss of legibility for the content author & consumers. The kinematic tree of the articulation is difficult to infer from this hierarchy.

It also introduces possibility of name collisions that could otherwise be avoided, and possible precision loss converting parent-space xformOps (not shown) into world space.

```
def Xform "World"
{
    def PhysicsScene "PhysicsScene"
    {
    }
    def Scope "PhysicsBodies"
    {
        def Xform "palm" (prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsArticulationRootAPI"])
        {
        }
        def Xform "index_finger_base" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
        {
        }
        def Xform "proximal" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
        {
        }
        def Xform "middle" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
        {
        }
        def Xform "distal" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
        {
        }
    }
    def Scope "PhysicsJoints"
    {
        def PhysicsJoint "metacarpophalangeal"
        {
            rel physics:body0 = </World/PhysicsBodies/palm>
            rel physics:body1 = </World/PhysicsBodies/index_finger_base>
        }
        def PhysicsJoint "rotational"
        {
            rel physics:body0 = </World/PhysicsBodies/index_finger_base>
            rel physics:body1 = </World/PhysicsBodies/proximal>
        }
        def PhysicsJoint "proximal_interphalangeal"
        {
            rel physics:body0 = </World/PhysicsBodies/proximal>
            rel physics:body1 = </World/PhysicsBodies/middle>
        }
        def PhysicsJoint "distal_interphalangeal"
        {
            rel physics:body0 = </World/PhysicsBodies/middle>
            rel physics:body1 = </World/PhysicsBodies/distal>
        }
    }
}
```

### Proposed UsdPhysics Equivalent

With the proposed change, the USD hierarchy more closely resembles the original hierarchy, retaining legibility for the content author & consumers, and providing a clear description of the kinematic tree via the USD hierarchy.

Additionally, joint relationships can be more easily expressed using relative paths, and Xform positions and orientations (not shown) can remain in parent-space.

```
def Xform "World"
{
    def PhysicsScene "PhysicsScene"
    {
    }
    def Xform "palm" (prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsArticulationRootAPI"])
    {
        def Xform "index_finger_base" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
        {
            def PhysicsJoint "metacarpophalangeal"
            {
                rel physics:body0 = <../../palm>
                rel physics:body1 = <../index_finger_base>
            }
            def Xform "proximal" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
            {
                def PhysicsJoint "rotational"
                {
                    rel physics:body0 = <../../index_finger_base>
                    rel physics:body1 = <../proximal>
                }
                def Xform "middle" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
                {
                    def PhysicsJoint "proximal_interphalangeal"
                    {
                        rel physics:body0 = <../../proximal>
                        rel physics:body1 = <../middle>
                    }
                    def Xform "distal" (prepend apiSchemas = ["PhysicsRigidBodyAPI"])
                    {
                        def PhysicsJoint "distal_interphalangeal"
                        {
                            rel physics:body0 = <../../middle>
                            rel physics:body1 = <../distal>
                        }
                    }
                }
            }
        }
    }
}
```
