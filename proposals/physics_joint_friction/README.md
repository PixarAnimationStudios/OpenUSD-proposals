# Joint friction in UsdPhysics

## Summary

This proposal adds `PhysicsJointFrictionAPI`, a multiple-apply API schema
for the passive friction inside a joint degree of freedom.
It has a static effort that holds a stationary joint in place,
a dynamic (Coulomb) effort that resists a moving joint,
and an optional viscous coefficient.
It is applied to a `PhysicsJoint` per degree of freedom
(`angular`, `linear`, `transX` ... `rotZ`),
the same way as `PhysicsDriveAPI` and `PhysicsLimitAPI`.

## Problem statement

UsdPhysics can describe what moves a joint (`PhysicsDriveAPI`),
how far a joint can move (`PhysicsLimitAPI`),
and the friction between bodies in contact (`PhysicsMaterialAPI`).
It has no way to describe friction inside the joint itself,
such as the bearing friction of an unpowered wheel,
a hinge that stays where it was left,
a backdrivable gearbox in a robot joint,
or a carriage on a rail.

The formats robots and machines are usually converted from all have it.
URDF has `<dynamics friction="...">`,
SDFormat has `<axis><dynamics><friction>`,
and MJCF has `frictionloss`.
Simulators that read USD have it too, each in its own schema:

- PhysX has `physxJoint:jointFriction`, documented as dimensionless,
  and per-axis `physxJointAxis:<axis>:staticFrictionEffort`,
  `dynamicFrictionEffort` and `viscousFrictionCoefficient`.
- MuJoCo's `mjcPhysics` schema has `mjc:frictionloss`.
- Newton's `NewtonJointAPI` has `newton:friction`,
  which Newton's URDF importer fills from URDF `friction`.

Since UsdPhysics has no attribute for it,
converters write the same value into several vendor namespaces at once.
Isaac Sim's URDF importer maps the URDF `friction` attribute
to both `PhysxJointAPI.jointFriction` and `mjc:frictionloss`,
and its MJCF importer maps `mjc:frictionloss` to `PhysxJointAPI.jointFriction`.
The values do not mean the same thing either.
URDF friction is an effort in N or N·m,
while `physxJoint:jointFriction` is a dimensionless coefficient.
A simulator that only reads UsdPhysics gets none of it.

The closest portable workaround is a `PhysicsDriveAPI` with zero stiffness,
zero target velocity and some damping.
Its resistance is proportional to velocity,
so it produces no force at rest and a body on a slope still creeps downhill.
It also uses up the drive on that degree of freedom,
so a joint with both a motor and friction can only describe one of them.

## Use cases

A disc harrow or a trailer has unpowered wheels on revolute joints.
Parked on a slight slope it should stay put until a tractor pulls it,
and pulling it should cost the tractor some effort.
Today this needs either a drive used as a brake, which creeps,
or a simulator-specific attribute.

Robot gearboxes and harmonic drives have a lot of joint friction,
and sim-to-real work identifies and authors it as a matter of course.
URDF, SDFormat and MJCF robot descriptions already carry it,
and it gets lost or split across vendor schemas on the way into USD.

Doors, lids, drawers, levers and monitor arms
should stay where they are left.

## Proposed schema

```
class "PhysicsJointFrictionAPI"
(
    customData = {
        string className = "JointFrictionAPI"
        token apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "jointFriction"
    }
    doc = """The PhysicsJointFrictionAPI, when applied to a joint primitive,
    resists motion along one degree of freedom of the joint with passive
    friction. It is a multipleApply schema, applied per degree of freedom with
    the same instance names as PhysicsDriveAPI: "transX", "transY", "transZ",
    "rotX", "rotY", "rotZ", "linear" for a prismatic joint or "angular" for a
    revolute joint.

    While the degree of freedom is at rest, friction opposes the net effort
    on it with a magnitude of up to staticEffort, so the degree of freedom
    stays at rest until that effort is exceeded. While it moves, friction is
    -sign(velocity) * (dynamicEffort + viscousCoefficient * abs(velocity))."""

    inherits = </APISchemaBase>
)
{
    float physics:staticEffort = 0.0 (
        customData = {
            string apiName = "staticEffort"
        }
        displayName = "Static Effort"
        doc = """Largest friction force or torque that holds the degree of
        freedom at rest. Units:
        if linear: mass*DIST_UNITS/second/second
        if angular: mass*DIST_UNITS*DIST_UNITS/second/second.
        Must be non-negative."""
    )

    float physics:dynamicEffort = 0.0 (
        customData = {
            string apiName = "dynamicEffort"
        }
        displayName = "Dynamic Effort"
        doc = """Coulomb friction force or torque that resists the degree of
        freedom while it moves. Units as staticEffort. Must be non-negative
        and should not exceed staticEffort."""
    )

    float physics:viscousCoefficient = 0.0 (
        customData = {
            string apiName = "viscousCoefficient"
        }
        displayName = "Viscous Coefficient"
        doc = """Friction added per unit of velocity while the degree of
        freedom moves. Units:
        if linear: mass/second
        if angular: mass*DIST_UNITS*DIST_UNITS/second/degrees.
        Must be non-negative."""
    )
}
```

All attributes default to zero,
so the schema has no effect until something is authored
and existing content behaves as before.
Units follow the stage's `metersPerUnit` and `kilogramsPerUnit`
and the degree-based angular units the rest of UsdPhysics uses.
They are the same units as `PhysicsDriveAPI`'s `maxForce` and `damping`.

### Example: towed implement

The wheel of a disc harrow holds the harrow on a slope
until about 150 N·m acts on the axle,
and once rolling it costs a constant 110 N·m.

```
#usda 1.0
(
    metersPerUnit = 1
    kilogramsPerUnit = 1
)

def Xform "Harrow"
{
    def PhysicsRevoluteJoint "LeftWheelAxle" (
        prepend apiSchemas = ["PhysicsJointFrictionAPI:angular"]
    )
    {
        rel physics:body0 = </Harrow/Frame>
        rel physics:body1 = </Harrow/LeftWheel>
        uniform token physics:axis = "Y"
        float jointFriction:angular:physics:staticEffort = 150
        float jointFriction:angular:physics:dynamicEffort = 110
    }
}
```

### Example: driven robot joint with gearbox friction

A drive and friction on the same degree of freedom.
A damping-only drive cannot describe this joint.

```
def PhysicsRevoluteJoint "Elbow" (
    prepend apiSchemas = ["PhysicsDriveAPI:angular", "PhysicsJointFrictionAPI:angular"]
)
{
    rel physics:body0 = </Arm/UpperArm>
    rel physics:body1 = </Arm/Forearm>
    uniform token physics:axis = "Z"
    float drive:angular:physics:stiffness = 400
    float drive:angular:physics:damping = 40
    float drive:angular:physics:maxForce = 87
    float jointFriction:angular:physics:staticEffort = 2.5
    float jointFriction:angular:physics:dynamicEffort = 1.8
    float jointFriction:angular:physics:viscousCoefficient = 0.002
}
```

### Mapping from existing formats and simulators

| Source | Attribute | Maps to |
|---|---|---|
| URDF | `<dynamics friction>` (N or N·m) | `staticEffort` and `dynamicEffort` |
| URDF | `<dynamics damping>` | `viscousCoefficient` (converted to per degree) |
| SDFormat | `<axis><dynamics><friction>` | `staticEffort` and `dynamicEffort` |
| SDFormat | `<axis><dynamics><damping>` | `viscousCoefficient` |
| MJCF | `frictionloss` (upper bound on friction effort) | `staticEffort` and `dynamicEffort` |
| MJCF | `damping` | `viscousCoefficient` |
| PhysX (`PhysxJointAxisAPI`) | `staticFrictionEffort`, `dynamicFrictionEffort`, `viscousFrictionCoefficient` | one to one |
| PhysX (`PhysxJointAPI`) | `jointFriction` (dimensionless) | no direct mapping, see alternate solutions |
| Newton (`NewtonJointAPI`) | `newton:friction` (Newton imports URDF `friction` into the same value) | `staticEffort` and `dynamicEffort` |

The friction model above is the one PhysX documents for `PhysxJointAxisAPI`.
MuJoCo's `frictionloss` and the URDF and SDFormat `friction`
correspond to a `staticEffort` equal to `dynamicEffort`.

### Parsing utilities

The physics parsing utilities added in USD 25.05 describe drives and limits
per joint with `UsdPhysicsJointDrive` and `UsdPhysicsJointLimit`.
A matching `UsdPhysicsJointFriction`
holding `staticEffort`, `dynamicEffort` and `viscousCoefficient`
would sit next to them,
as a `friction` member on the revolute and prismatic joint descriptors
and as a per-axis list on `UsdPhysicsD6JointDesc` beside `jointDrives`.

### Validation

- All three attributes must be finite and non-negative.
- A `dynamicEffort` greater than `staticEffort` is reported as a warning,
  and simulators then use `dynamicEffort` for both.
- The instance name must address a degree of freedom the joint has,
  with the same rules as `PhysicsDriveAPI`
  (`angular` on a revolute joint, `linear` on a prismatic joint).

## Risks

Holding a joint exactly at rest (stiction) is harder for some solvers
than resisting motion.
PhysX applies joint friction only to articulation joints,
and maximal-coordinate solvers may approximate it.
The schema describes the intended behaviour, as UsdPhysics does elsewhere.
A simulator without support ignores it,
the same as it ignores vendor attributes today.

`viscousCoefficient` is passive damping of the joint,
and `PhysicsDriveAPI` damping is a gain of the drive,
but reviewers may still see the two as overlapping.
If the working group would rather keep this proposal to dry friction,
`viscousCoefficient` can be removed and nothing else changes.

Converters that write vendor attributes today can write both during a transition,
and vendor schemas can keep their attributes as overrides.

## Alternate solutions

A `PhysicsDriveAPI` with damping only cannot hold a body at rest,
because its resistance is proportional to velocity,
and it takes the place of a real drive on the same degree of freedom.

A single `physics:jointFriction` attribute on `PhysicsJoint` would be simpler.
It could not address the individual degrees of freedom of a D6 joint,
and it could not separate static from dynamic friction.

A dimensionless coefficient, as in `physxJoint:jointFriction`,
only becomes an effort once a simulator multiplies it by a force of its own choosing,
so the same value can behave differently from one simulator to the next.
URDF, SDFormat and MJCF all give an effort,
so converters can carry an effort over without loss.

Leaving joint friction to vendor schemas keeps the current situation,
where one physical quantity sits in several namespaces with different meanings.

## Out of scope

- Rolling and torsional friction at contacts,
  such as Newton's `newton:rollingFriction` on materials.
  That resistance acts where two bodies touch and belongs with `PhysicsMaterialAPI`.
- Spherical and distance joints.
  Friction for these needs per-axis instances on a cone or a distance instance,
  and can follow in a later proposal.
- Joint friction that grows with the force the joint carries.
- Joint armature (reflected rotor inertia, MJCF `armature`, `newton:armature`),
  another common passive joint property that needs its own proposal.

## Reference links

- [UsdPhysics PhysicsDriveAPI](https://openusd.org/release/api/class_usd_physics_drive_a_p_i.html)
  and [PhysicsLimitAPI](https://openusd.org/release/api/class_usd_physics_limit_a_p_i.html)
- [URDF joint specification](https://wiki.ros.org/urdf/XML/joint)
- [SDFormat JointAxis](https://gazebosim.org/api/sdformat/15/classsdf_1_1SDF__VERSION__NAMESPACE_1_1JointAxis.html)
- [MuJoCo XML reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
  and [friction loss in MuJoCo's computation chapter](https://mujoco.readthedocs.io/en/stable/computation/index.html)
- [MuJoCo mjcPhysics USD schema](https://mujoco.readthedocs.io/en/stable/OpenUSD/mjcPhysics.html)
- [PhysX joint schema (Omniverse Physics)](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/108.1/dev_guide/joints/physx_joint_schema.html)
- [Isaac Sim URDF importer](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
  and [MJCF importer](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/importer_exporter/ext_isaacsim_asset_importer_mjcf.html)
- [Newton joint attributes (SimReady)](https://nvidia.github.io/simready-foundation/latest/capabilities/physics_bodies/physics_driven_joints/requirements/newton-joint-attributes.html)
