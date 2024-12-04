# Variant Set Metadata

Copyright &copy; 2024, NVIDIA Corporation, version 1.0

Tyler Hubbard   
Joshua Miller   
Matthew Kuruc   

## Contents

- [Introduction](#introduction)
- [Metadata in OpenUSD](#metadata-in-openusd)
    - [Metadata Fields](#core-metadata-fields)
    - [Custom Metadata Fields](#custom-metadata-fields)
    - [Metadata Value Resolution](#metadata-value-resolution)
- [Example](#example)
- [Variant Display Name](#variant-display-names)
- [Variant Ordering](#variant-ordering)
- [Crate File Format Support](#crate-file-format-support)
- [UsdVariantSet is not a UsdObject](#UsdVariantSet-is-not-a-usdobject)
- [Stage Flattening](#stage-flattening)

## Introduction

Variant sets would benefit from a means of storing and retrieving additional information about them
and their variant children. Users of editors have a need to create and view context
and informative descriptors about variant sets. A common use case for this feature is
showing a user friendly display name instead of just an identifier. For example,
being able to show UTF-8 transcoded display names in editors,
providing a much better user experience across languages.

There is currently no support for this functionality on variant sets,
so we propose adding the ability to author metadata on `UsdVariantSet` to support similar 
functionality available to `UsdPrim`, `UsdAttribute` and `UsdRelationship`. 
This metadata is intended to be used in editors to display information such as a 
nicely formatted name for the variant set or whether the variant set should be hidden in certain views.
`UsdVariantSet` metadata will not affect the composition behavior for a `UsdPrim`, 
`UsdAttribute` or `UsdRelationship` on a `UsdStage`. 

## Metadata in OpenUSD

Metadata is a core feature of OpenUSD that is available to `SdfLayer`, `UsdStage`, `UsdPrim` 
and both subclasses of `UsdProperty`. `UsdPrim` and `UsdProperty` both derive from `UsdObject` 
which provides API for authoring and accessing metadata. 
Common examples of metadata available for these types are documentation, display name, 
display group, and hidden to name a few. This metadata is extremely helpful for editors, 
such as UsdView, so users can get a better understanding, or visualization, of the stage.
For instance, display name is a very common form of metadata on a `UsdPrim` to create a nice,
human-readable name that will be presented in an editor.

A `UsdVariantSet`, which does not derive from a `UsdObject`, has no such API to create metadata.
If an author would like to produce a `UsdVariantSet` that should be hidden from editors,
there isn't a uniform way to do so. Yes, the author could prefix the name of the `UsdVariantSet` 
with something like "test" or "__", but every editor would need to respect this prefix.
A better way to support such a feature on `UsdVariantSet` would be to expose a hidden metadata field.
This would be consistent with the `UsdObject` API and lends itself to other metadata fields
that would be applicable for a `UsdVariantSet` like display name.

## Metadata Fields

The following are metadata fields that will be commonly used on a `UsdVariantSet` 
and will have an explicit API. The fields proposed here will provide the normal accessors 
and mutators that will be available on a `UsdVariantSet`:

- `comment` - User notes about a variant set
- `documentation` - Information that can describe the role of the `UsdVariantSet` and its intended uses
- `displayGroup` - Name to assist with grouping similar `UsdVariantSet`s in editors.
- `displayName` - Name for the `UsdVariantSet` that can be used in editors
- `hidden` - Boolean field that can inform an editor if the `UsdVariantSet` should be hidden. 
    This field will have a fallback value of `false`
- `variantDisplayNames` - Mapping of variant name to a variant's display name that can be used in editors. 
    See [Variant Display Names](#variant-display-names) for more implementation details.
- `variantOrder` - User defined ordering of variants, similar to primOrder and propertyOrder. 
    See [Variant Ordering](#variant-ordering) for more implementation details.
- `customData` - User defined dictionary of additional metadata

## Custom Metadata Fields

Similar to other types that allow authoring of metadata fields, `UsdVariantSet` will also 
allow custom metadata fields that are defined in plugins. These custom fields can be used to 
author metadata on a `UsdVariantSet` that might be site-specific but should always be applied 
to the `UsdVariantSet` type.

## Metadata Value Resolution

As described below, a [UsdVariantSet should not be a UsdObject](#usdvariantset-is-not-a-usdobject). 
But the metadata value resolution process of a `UsdVariantSet` should behave 
similar to that of `UsdObject`. For most types the resolution process will be 
"strongest opinion wins" but other, more complicated types like VtDictionary will be 
correctly resolved. This will slightly complicate the implementation since 
`UsdVariantSet` will need to provide this value resolution step, 
but should provide expected results for authored metadata.

## Example

An example showing metadata on variant sets can be found [here](example.usda)

```
#usda 1.0
(
    defaultPrim = "MilkCartonA"
)

def Xform "MilkCartonA" (
    kind = "prop"
    variants = {
        string modelingVariant = "Carton_Opened"
        string shadingComplexity = "full"
        string shadingTest = "milkBrandA"
    }
    prepend variantSets = ["modelingVariant", "shadingComplexity", "shadingTest"]
)
{
    variantSet "modelingVariant" (
        doc = "Modeling variations for the asset"
    ) = {
        "ALL_VARIANTS" {
            float3[] extentsHint = [(-6.27056, -6.53532, 0), (6.14027, 6.10374, 29.8274)]

        }
        "Carton_Opened" {
           float3[] extentsHint = [(-6.27056, -6.53532, 0), (6.14027, 6.10374, 29.8274)]

        }
        "Carton_Sealed" {
           float3[] extentsHint = [(-6.27056, -6.44992, 0), (6.14027, 6.10374, 29.2792)]

        }
    }
    variantSet "shadingComplexity" = {
        reorder variants = ["none", "display", "modeling", "full"]
        "display" {

        }
        "full" {

        }
        "modeling" {

        }
        "none" {

        }
    }

    variantSet "shadingTest" (
        """Added UPC# for the display names"""
        displayName = "Shading Test Variations"
        doc = "Shading variations that are currently being explored for product placement"
        variantDisplayNames = { "milkBrandA" : "Milk Brand A (UPC#: 123-ABC)", "milkBrandB" : "Milk Brand B (UPC#: 456-DEF)" }
        hidden = True
    ) = {
        "milkBrandA" {

        }
        "milkBrandB" {

        }
    }
}
```

## Variant Display Names

Adding display names to variants is another metadata field that this proposal would like to support.
This field will need to be handled differently than other displayName metadata fields 
found on types like `UsdPrim` and `UsdProperty`. Specifically, a mapping of variant name
to display name will be required as display name can not be added to a variant.
First, there is no `UsdVariant` type to add display name API to. Secondly, and most importantly,
all fields within a variant are applied directly to a `UsdPrim` when selected.
If a displayName metadata field was added to a variant, that field would be applied to the
`UsdPrim`'s displayName and not the variant's. It's for this reason that a mapping of 
variant name to display name will be added to a `UsdVariantSet`.
As described in [Metadata Value Resolution](#metadata-value-resolution), 
the mapping of variant name to display name will need to be correctly resolved and merged.

## Variant Ordering

One of the metadata fields presented in this proposal is the 
addition of [variantOrder](#metadata-fields). The goal of this field is simple;
to specify an explicit order for how an editor should display variants in a `UsdVariantSet`.
When considering the implementation of this metadata field for the `SdfTextFileFormat`
it seems consistent with other `SdfSpec`s to use a `reorder variants` statement.
This can be seen in the [proposed example](example.usda) but worth 
calling out specifically as it brings up two questions:

1. Is a `reorder variants` statement the correct approach for implementing `variantOrder` 
    metadata field?
2. If so, should the addition of a new `reorder` statement in the `SdfTextFileFormat` 
    require a version bump as it requires changes to the parser?

## Crate File Format Support

The general consensus is that the USD Crate File Format should "just work" when 
metadata support is added to `UsdVariantSet`. The proposal does not mention 
any implementation details regarding the USD Crate File Format as the expectation 
is that no changes should be necessary. Unfortunately, it is not easy to test out 
if this assumption is correct due to Crate being a binary file format.
This will require further experimentation once the changes proposed here move 
to the implementation step.

## UsdVariantSet is not a UsdObject

`UsdObject` is the base class for `UsdPrim` and `UsdProperty` that provides the 
common API for accessing metadata. Investigating metadata support for `UsdVariantSet` 
immediately raised the question of: *“Should UsdVariantSet be a UsdObject?”*. 
The answer is no, a `UsdVariantSet` should not be a UsdObject. The reason is more 
philosophical than technical as a `UsdObject` is the common base shared amongst types 
in OpenUSD’s scenegraph. The idea is that a `UsdObject` is a tangible entity 
on OpenUSD's scenegraph. These objects can be accessed directly from API such as 
UsdStage::GetObjectAtPath(), relationships can be established between multiple 
`UsdObject`s, they can be included in collections, they will not be discarded during 
the flattening process, and all `UsdObject`s share a common set of metadata. 
This last point is the main reason for asking *"Should UsdVariantSet be a UsdObject?"*; 
specifically to prevent code duplication. But when thinking about these other points, 
it becomes clear that deriving `UsdVariantSet` from a `UsdObject` would require 
quite a few exemptions in OpenUSD.

From a technical perspective though, deriving `UsdVariantSet` from a `UsdObject` seems logical. 
It already provides a lot of the metadata API that is presented in this proposal. 
But `UsdVariantSet` would also inherit API for metadata such as AssetInfo which 
is not something that applies to a `UsdVariantSet`. It would also create ambiguity 
with `UsdCollectionAPI` and `UsdRelationship` as those expect `SdfPath`s 
to `UsdObject`s like `UsdPrim`, `UsdAttribute` or `UsdRelationship`. 
What benefit would a collection containing a `UsdVariantSet` provide? 
Or what does a relationship from a `UsdAttribute` to a `UsdVariantSet` mean? 
The convenience of avoiding code duplication does not warrant changing `UsdVariantSet` 
to be a `UsdObject`. There is also precedent in OpenUSD for API that provides 
metadata support without deriving from `UsdObject`, `UsdStage` is one such example.

But answering this question leads to discussion on how to best implement metadata support 
for `UsdVariantSet`. Since `UsdVariantSet` should not be a `UsdObject` a potential 
implementation for metadata support could lead to unnecessary code duplication. 
A better approach might be to refactor common metadata API found in `UsdObject` to 
private internal utilities that can be used for types that do not derive from 
`UsdObject`. Types such as `UsdStage` and `UsdVariantSet` could use these utilities 
to implement their own API for metadata, avoiding code duplication and 
not deriving from `UsdObject`.

## Stage Flattening

The stage flattening process will remove all `UsdVariantSet`s when the stage is collapsed 
into a single merged layer. With all `UsdVariantSet`s being removed, there is no reason 
to maintain authored metadata as an editor will not have any `UsdVariantSet`s to display. 
As such, metadata authored for a `UsdVariantSet` will not be preserved when flattened. 
This could be viewed as another argument for [UsdVariantSet should not be a UsdObject](#usdvariantset-is-not-a-usdobject) 
since they are discarded during the flattening process.