# Multiple Animation for General Prims

It would ideally be great to support multiple animations generically across any USD prim type.

My concern is that possible changes could be a signficant amount of time and work. That said, I recognize the strong benefits of having a singular solution that systems can build around.

## Proposals

There are several forms that this could take. I'll do my best to summarize previous discussions in various forms.

### Non-exclusive variants

A new runtime variant form could be added that allows for each prim to specify variants that the runtime could apply to the prim hierarchy.

They would ideally have limitations on what changes they can provide, such as preventing changes to references to prevent needing to re-evaluate composition for each possibility.

For the purpose of this proposal, I'll call this `multiSets` and `multi`.

It would have the same syntax as variants with

```
def Xform “Foo” (
    prepend multiSets = “animation”
) {
    multiSet “animation” {
        “none” {...}
        “idle” {...}
        “walk” {...}
    }
}
```

While this would be a significant change to USD, it has a few advantages:

- It could also solve the case for other non-exclusive variant situations like levels of details for game runtimes.
- It could include an entire hierarchy within it, so animation clips can be defined in one place.

### Namespaced variants

Another form that we could take is adding namespaces to individual fields. 

For example, the following defines a default, idle and run animation.

```
double3 xformOp:translate.timesamples = {...}
double3 xformOp:translate:idle.timesamples = {...}
double3 xformOp:translate:run.timesamples = {...}
```

This has the advantage of needing a very small change to USD.

However it has a couple disadvantages:

- It is hard to discern that the namespace is intended for animation and not another use.
- It would be hard to gather up a clip across they entirety of a hierarchy. 

### Value Clips

Value clips and value clip sets are a great choice because they already implement the concept of multiple animations per a USD hierarchy.


However I think the following changes would need to happen to USD to allow for this to truly  meet the goal for realtime use cases or any case where the animation is being extracted into another runtime.

1. Value Clips require multiple layer files to function in their current state, or at least that appears to be the only documented setup. Ideally we'd allow pulling in prim hierarchies from within a single layer to allow for simplified pipelines where needed, since many users of USD might not have a studio pipeline and convention.

2. If we enable putting the value clip hierarchy within a single file, we need a way to tell renderers to ignore that hierarchy. That might be as simple as putting them under a Scope convention like "Animations", and then giving them a non-imageable type , or no type at all. Value Clips might therefore need to explicitly allow for type mismatches (which they might but documentation isn't clear.)

3. USD doesn't seem to have any API to pull out just the properties and their values that vary. Ideally we should have some kind of API that returns a read only view into what each individual clip would resolve into.

## Preference

Based on the above, and further discussion with folks, I think modifying value clips would be the best general solution for the following reasons:

1. It doesn't require any new mental model changes for USD itself. Which is always nice when introducing people to all the ways something can work in USD.

2. The changes needed should hopefully be minimal if people agree that they're wanted.

3. The intent of a value clip is fairly clear so there's no ambiguity.


## Skeletons

The changes needed for a general purpose solution are quite a bit more regardless of the solution than those for a UsdSkel only solution.

I think it would be necessary to evaluate the work needed for the proposals above to decide if it makes sense to do

1. A separate solution for skeletons and general prims
2. A general solution only

While a general purpose solution would of course be nice for simplifying things down, it does offer two problems:

1. Possibly a longer turnaround time
2. Very hard to bound what can be animated, whereas SkelAnimation is very tidily bounded.


----

Anyway hopefully this document is a good recap of the discussions thus far.