# UsdShade Material Prim "material" terminal proposal

## TL;DR
Adding a `material` terminal to the Material prim in UsdShade allows for material construction techniques to be changed 
independently of Usd Schema changes. Allowing for UsdShade to describe a broader set of material concepts.

```
def Material "MyMaterial"
{
    token outputs:mtlx:material.connect = </MyMaterial/MyRootNode.outputs:out>

    def Shader "MyRootNode"
    {
        uniform token info:id = "ND_surfacematerial"
        token inputs:surfaceshader.connect = </MyMaterial/std_surf.outputs:out>
        token outputs:out
    }
    def Shader "std_surf"
    {
        uniform token info:id = "ND_standard_surface_surfaceshader"
        <...>
        token outputs:out
    }
}
```

## Introduction
This proposal aims to introduce a new `material` terminal type to the UsdShade Material primitive, to allow material 
authoring systems more freedom to iterate within a stable UsdShade schema.

Currently the the UsdShade Material prim supports a fixed set of terminal connections, `surface`, `displacement` and 
`volume`. These terminals connect to Shader prims encapsulated inside the Material prim. These shader prims are the 
root of the respective shaders graphs. This has so far been sufficient for the current rendering use cases, but we 
would like to broaden the scope of the supported rendering approaches.

MaterialX does not have a node that directly corresponds to the UsdShade `Material` primitive. Instead it provides two
nodes that output a `material` type. A `surfacematerial` node that takes a `surfaceshader` and `displacementshader` as
input, and a `volumematerial` that has a `volumeshader` input. In MaterialX 1.38 the `surfacematerial` node interface
only contained these inputs for surface and displacement, but in MaterialX 1.39 a third, `backsurfaceshader`, was added
to the `surfacematerial` node.

## Problem
Directly supporting this new MaterialX `surfacematerial` input with the current UsdShade Material could suggest that we 
need to update the USD schema to add an additional terminal, incurring the usual complexity and support cost 
of schema changes, but we are also not sure that this will be the last such change. There are a number of other ideas being 
discussed where it may be necessary to extend the material in different ways. Some real time shading models would 
like to include ambient occlusion signal at the material level. There is an in progress proposal for MaterialX to add 
non-visual data to material definitions. This would be very similar in mechanism to the existing <aovoutput> proposal, 
where new elements are added to the `surfacematerial` node. If we want to add that, with the current setup that means 
we need to add ports for all of those to the UsdShadeMaterial. 

There is also strong interest for to be able to describe material layering, in both MaterialX and UsdShade.  That is 
correct physical layering of materials (or "vertical layering" or "slabs" depending on who you ask) and that needs 
to include the entire material definition including non-visual properties. If we were to try to describe this in the 
current UsdShade schema, the layering would need to be defined over the UsdShade Material prim, which is not its 
business (its business is "what material does this renderer apply to this prim, and for what render purpose").

## Goal
To make a compatible change to the existing UsdShade schema that will allow material system authors more flexibility 
to construct materials within UsdShade, without the need to couple that construction directly to the UsdShade schema.

## Proposal
We propose adding a new terminal, `material`, to the UsdShade Material schema. This terminal would be connected to a 
UsdShade Shader prim representing the root node of a material. This shader prim would have its shader definition 
registered in the Shader Definition Registry. This gives us the advantage of not needing to directly define the 
material root nodes interface in the UsdShade schema, but instead being able to dynamically register in the Shader 
Definition Registry.

In Hydra the UsdShade Material terminals are mapped through to the `HdMaterialNetworkMap` or `HdMaterialNetwork2`, so 
we do not propose any changes to Hydra itself. Hydra Render Delegate authors will need to be updates to query the new 
terminal type. This suggests that the render will potentially need to understand how to decompose the new material 
terminal in to the components required for rendering, such as the existing surface shader and displacement shader. It 
is likely that the renderer already has the need for a deep understanding of the material authoring system, and that 
this would be a trivial change, but we should canvas renderer developers to validate this assumption.

## Backwards Compatibility
We suggest that the `material` terminal be respected as matter of first priority, but if no `material` terminal is 
authored, then the existing `surface`, `displacement` and `volume` terminals are used. This allows for all existing 
assets to continue to work as they currently do, and only as new `material` terminals are authored will any potential 
behavior change. Potentially in the future the current terminal convention could be deprecated, once the new `material` 
terminal has become the defacto standard.

## Benefits
By design, this proposal allows material authoring systems such as MaterialX, to iterate the structure of a material 
independent of the UsdShade schema.
It also decouples the material purpose (`full`, `preview`) and the renderer target (`ri`, `mtlx`, `arnold`, etc.) from 
the material terminals, meaning that less terminals will need to be duplicated if multiple purposes or render targets 
are being authored for. We hope this is a small win for simplicity.
With this change, the node that the `material` terminal is connected to is the root node of the entire material. This 
root node itself is a Shader prim, thus it's output could conceptually be connected to other Shader nodes. This 
would allow material authoring systems to explore ideas where entire composite materials, such as rusty painted metal, 
could be authored in a more natural way.
While the MaterialX standard library does not currently contain nodes that operate on a `material` type as an input, 
other production proven material authoring systems exist that facilitate this workflow in a user friendly way. Concretely,
this is exactly how MDL in Omniverse works, having a node that defines the material with the constituent parts being
connected as inputs. Sony Pictures Imageworks also has a node based material "layering" system, MaterialCombine. Where 
the atomic nodes in the graph are materials, and a number of combination operations are supported. It is a production 
proven system, and has been used for all of projects over the past 8 years. 

## Challenges
The introduction of this change will likely infer a change in `UsdMtlx` to adopt this new terminal convention. Any 
change to the structure of the Usd stage created when referencing a `.mtlx` file in directly is challenging to 
navigate. Changes in the structure of the UsdShade data generate when reading a MaterialX document can invalidate 
composition arcs in existing data authored against the old structure.

This new `material` terminal will need authoring support in DCCs and other applications that generate UsdShade Material 
prims. As well as adoption in any software that consumes the UsdShade Material prim, such as renderers interfacing to 
USD via Hydra. It also places a slightly higher burden of understanding on those consumers/rendering engines to 
understand a little more about the associated material authoring sytems, but we think that most of these systems are 
already tightly integrated with their respective material systems.

## Other Solutions
The most obvious alternate solution is to continue to update the UsdShade schema as material authoring systems, such as 
MaterialX, require additional information to be stored at the Material prim level. As already discussed this presents 
challenges with frequently changing schema, and also potentially challenges around finding consensus about what should 
exist in the Material prim interface. Is it possible that different material authoring systems may have conficting 
concepts that need to be represented?
