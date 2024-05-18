# MaterialX Versioning in OpenUSD

## Contents
- [TL;DR](#tldr)
- [Introduction](#introduction)
- [Problem](#problem)
- [Proposal to Version MaterialX data in OpenUSD](#proposal-to-version-materialx-data-in-openusd)
    - [Overview](#overview) 
- [Risks](#risks)
    - [Risk 1](#risk_1)
- [Out of Scope](#out-of-scope)
- [Questions](#questions)

## TL;DR

We propose adding attributes to UsdShade `Material` primitives to record the MaterialX library version they were authored
with. This will allow for MaterialX to provide an automatic upgrade functionality to the data stored in OpenUSD.

## Introduction

From its inception the MaterialX project has a considered MaterialX documents to be an archival format.  What goes along 
with that is an implied promise that opening a MaterialX file from 10+ years ago should generate a material that will 
render a qualitatively similar image.  This promise is honored by the project in the form of an automatic system that 
mutates data as documents are loaded to be compatible with the current MaterialX library version.

The MaterialX integration within OpenUSD relies upon two libraries, `UsdMtlx` and `HdMtlx`. `UsdMtlx` transcodes the 
MaterialX document in to a `UsdShade` primitives. Inside of Hydra, `HdMtlx` is used to reconstruct the
MaterialX document using the `UsdShade` primitives that have been transported through Hydra (more information 
available [here](https://openusd.org/release/api/_page__material_x__in__hydra__u_s_d.html)). The reconstucted MaterialX 
document is then passed to the MaterialX Shader Generation library to generate shader code in the desired destination
shading languages.

## Problem

For the entire lifetime of MaterialX support within OpenUSD, there has never been a MaterialX library version change. The 
*current* MaterialX library has always been v1.38. The MaterialX project would like to be able to update the MaterialX 
library version without invalidating MaterialX data currently stored in OpenUSD files. Without access to the MaterialX 
library version the upgrade code path inside the MaterialX project cannot function correctly.

Without some sort of remedy, either MaterialX will be constrained to v1.38, or OpenUSD will become an ambiguous container 
for MaterialX data.  

## Proposal to Version MaterialX data in OpenUSD

### Overview

We propose adding an applied API schema `MaterialXVersionAPI` (in the spirit of the 
["Revise use of Layer Metadata in USD"](https://github.com/PixarAnimationStudios/OpenUSD-proposals/blob/main/proposals/revise_use_of_layer_metadata/README.md)) 
that can record the MaterialX library version on the UsdShade `Material` primitive.  Adding the version to the `Material` 
primitive allows for referencing the material directly from a `.mtlx` file. i.e.
```
def "Material" MyMaterial (
    references=@myMaterials.mtlx@</MaterialX/Materials/MyMaterial>
)
{}
```

Any UsdShade `Material` primitives that do not have the applied API would be assumed to be v1.38.

The following is an example of a `Material` primitive with the applied schema applied.
```
def "Material" MyMaterial ( 
    prepend apiSchemas = ["MaterialXVersionAPI"]
)
{
    uniform string materialXVersion = "1.39"
}
```

With the MaterialX library version recorded in the OpenUSD stage, `HdMtlx` would now have access to an appropriate 
version number to use when re-constructing the MaterialX document. This allow the existing MaterialX upgrade functionality
to be used. 

### `UsdMtlx` Implementation changes

The only change required in `UsdMtlx` would be to apply the applied API schema to the `Material` primitive, and set the
MaterialX library version.

### `HdMtlx` Implementation changes.

The `HdMtlx` library will also need to be changed to read the MaterialX library version from the `Material` primitive, 
and author this in to the reconstructed MaterialX document.

If the version is not present it will be assumed to be v1.38. 

**NOTE :** We do not propose any sort of validation regarding the version other than its presence, and then falling back 
to the default. Specifically we do not propose attempting to validate that all opinions that make up a composed `Material` primitive were authored with the same MaterialX version, even though this composition could lead to an invalid MaterialX 
material, for a number of reasosn.
 * The expense of the validation in some circumstances could be too high to consider
 * It is possible that a `Material` primitive may still contain a valid MaterialX material even if composed of differing 
 * MaterialX library versions.
 * Reporting the error during the evaluation of Hydra may be later in a pipeline than desired.
 * Some implementations might not even use the `HdMtlx` library to extract the MaterialX material.

Instead, we propose to leverage another OpenUSD proposal, the [USD Validation Framework](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/usd-validation-framework). Adding a `UsdValidator` to 
inspect all layers that contribute opinions to a UsdShade `Material` primitive, and reporting an error if opinions are 
found that were authored with conflicting MaterialX library versions.

## Out of Scope
To make progress tractable this proposal intentionally does not attempt to automatically account for composition of 
OpenUSD layers that author opinions with differing MaterialX versions, other than reporting this case via a validator.  
This would result in a composed stage that could not be represented currently in any MaterialX document, and thus is 
beyond the scope of what we are trying to solve here. 

This proposal also does not attempt to update in-place any OpenUSD data, or provide functionality to do so. The complex 
nature of scene composition makes this a difficult problem to tackle, and while this problem could probably be tackled 
in the future, we think it prudent to keep the scope of this problem tractable.

## Other solutions considered

Initial conversations around this topic started with discussions of adding layer metadata to the layers containing 
MaterialX information, but in light of the recent proposal to move away from layer metadata the direction of the 
conversation was changed.

We also considered authoring the MaterialX library version on each UsdShade `Shader` primitive, in the hope that it 
would allow more concrete support, or atleast discovery, of mismatched MaterialX library versions created during USD 
composition.  This idea was discarded on the grounds that it would be both noisy in the USD data, and also potentially 
error prone if being authored by hand. A single applied API schema for the entire `Material` primitive seemed like a 
better compromise.
