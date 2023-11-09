# Multiple Animation in USDSkel

This proposal outlines a way to add the ability for a Usd Skeleton to have multiple animation sources associated with it. 

A follow up proposal will describe a possible way to add multiple animations to regular prims. I've chosen to split them out so as to focus discussion.

This would be useful for runtimes like game engines or crowd simulation software where the ability to have access to multiple animations at once are useful so that the runtime can activate and blend between them as needed based on application specific context.

It would also help bring better parity to the takes system in FBX, which has facilities for specifying multiple animations per object.

Additionally, there is a desire to have no default animation as well, to speed up time to first load, since animation processing can be elided if the user isn’t using animations till a later time. e.g in Unreal, you may place a static actor for layout purposes, but only apply animation during runtime


## Why not Variants? 

Variants have a runtime cost associated with switching, and only expose a single variant at a time on the composed stage.
Meanwhile, runtimes like game engines require access to the full range of options available and also switch often, such that recomposition is too heavy a cost to pay.

## UsdSkel Schema Change Proposal

USD Skeletons are unique in that they store animation externally to the prim itself. They are also the most likely candidate in a real time pipeline to have multiple animations, and game studios often will treat even basic transforms as a single joint skinned object.

While the skeleton proposal wouldn’t allow generalization over non-skeletal animation such as transforming objects, it would at least cover the most common use cases requested in a way that should be fairly easy to provide quickly.
This would also allow easier sharing of animations between multiple characters that share a skeleton.

A future proposal would describe how we may add multiple animations to generic prims, and how that could play well with this Skeleton proposal.

### Proposal 1

In this version, we allow `skel:animationSource` to be a list, much like `blendShapeTargets` is. Since rels are allowed to be lists, this doesn’t change the schema.

The API’s for the schema would need to be modified, with an overload for a Vec, and modify the getter/setter to take the first item in the list as the default active animation.

Since this is not a schema change, the API wouldn’t need to be versioned and existing files would continue to work as is.
However files authored with this API may not be compatible with DCCs that do not assume a list.

With this proposal, you’d need a secondary attribute to control whether animations get applied by default. This would default to True to maintain current behaviour, but could be flipped to signal the intent that animations shouldn’t be applied by default

```
bool skel:applyAnimation (
    customData = {
        string apiName = “applyAnimation”
    }
    doc = “”“Controls whether animations are meant to be applied by default or not. If set to False, the static pose should be used”“”
)
```

### Proposal 2

In this second proposal, we'd add a new property. A new `skel:animationLibrary` type would need to be added to `SkelBindingAPI` like below. It would be a list of sources while leaving the current animationSource as the active selection 

```
rel skel:animationLibrary (
    customData = {
        string apiName = "animationLibrary"
    }
    doc = """An ordered list of skeletal animations that can be used for this skeleton.  
    """
)
```

In the interest of backwards compatibility, I propose that this live alongside the existing `skel:animationSource`. The singular one would be used as the default in places like usdview or runtimes that don’t support multiple clips.

If the singular `animationSource` is not specified, then no animation should be applied by default, falling back to the rest pose. This would maintain the current behaviour, and give the option to elide application of animations when undesired.

This should avoid the need to version the schema, and the Setter/Getter functions could handle this abstraction for developers.


### Proposal 3

In the third Proposal, we simply define conventions based on [the general proposal](general.md).

Each of the general proposals can simply vary the existing `skel:animationSource`. 

See the other file for concerns about bounding and storage.


## Naming

One other nicety would be naming of the animations.
It is unclear what the best way to do this would be.


### Names as Attributes on SkelBindingAPI

The names could be a matched index array on the `SkelBindingAPI` that correspond to each rel.
This would allow for the names to not require a stage traversal, and allow each prim to have unique names if necessary.
It would also allow using names elsewhere in the SkelBindingAPI if needed.

On the downside, this would duplicate the names


### Names on the SkelAnimation

Since the SkelAnimation is independent already, the name could simply be derived from the Prim name or displayName of the SkelAnimation.

Alternatively SkelAnimation could have a new TfToken/String attribute for name.
This way every use of the SkelAnimation gets the same name, and no data duplication occurs.

However fetching the names would require a stage traversal.


## Extents

Currently there is no way to specify how the `SkelAnimation` would affect the bounding box of an animated character. This causes issues where clipping may occur based on the authored extents of the static mesh.

Many authoring systems either skip authoring extents for Skeletal animations, or author it based on the single animation source. This varies by runtime, where game engines may ignore the authored extents, while crowd simulation software may make use of it when not using dynamic animation.

As I do not work in an environment where extents for skeletons are key for their use, this section is a strawman argument but I believe it’s important to bring up since others may have such a need.

If we were to add multiple animation sources, it might also be beneficial to allow multiple bounding boxes to be associated with the Skeleton.

This could not exist on the SkelAnimation since the Animation may be shared by multiple characters, each with different extents. Take for example, crowd characters that share the skeleton and animations but have different costume attachments.

As such it could be valuable to introduce a new schema type like so that could be calculated ahead of time for each bound animationSource:

```
class SkelExtents “SkelAnimationExtents” (
    inherits = </Typed>
    doc = “”“Describes the extents of a given skeleton character when used with a given animation.”
    customData = {
        string className = “AnimationExtents”
    }
)
```


The SkelBindingAPI could then have another rel attribute like so

```
rel skel:animationExtents (
    customData = {
        string apiName = “animationExtents”
    }
    doc = “”“An ordered list of extents that maps to the order of the animationSources”“”
)
```

The ordering of the extents would map to the ordering of the animationSources.


## Support for multiple animations on generic prims

I think there's also a lot to be gained by having multiple animation support for generic prims, especially Xform based prims.
However in the interest of keeping this proposal scoped smaller, I'll put up a separate proposal for that.

I expect a general purpose solution to be a much larger undertaking, and I think we'd have maximal, immediate ROI by adding support for skeletal use cases. 

Once that's up, I'll update this proposal with a link and more details on how they could work in concert.