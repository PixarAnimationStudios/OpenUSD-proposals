# Self Assembling Model Hierarchy
Copyright © 2023, NVIDIA Corporation, version 1.3

## Goal
Simplify correct model hierarchy maintenance and construction through removal of the need for explicit `kind=group` tagging without incurring _any_ additional reads of `kind` metadata.

## Background
USD presents "model hierarchy" as a mechanism for efficient traversal of a stage's "important" prims. This importance generally corresponds to the stage's referenced assets, but is pipeline independent, persistent under flattening of arcs, and allows for "casual" use of composition operators without implying "importance" (ie. using internal references to reuse scene description).

Model hierarchy is expressed through a prim's `kind` metadata. It's worth noting that `kind` is an extensible concept, but that won't be addressed in this document as to participate in model hierarchy, they must derive from one of the standard `kind`s. `kind` is distinct from and orthogonal to a prim's schema type.

There are several first class `kind` types.

* `component`: This `kind` represents the leaf in model hierarchy traversals. What defines a `component` can be context dependent. In the context of a city, each building may be a `component`. In the context of a room, pieces of furniture may be `component`s. As they represent leaves in the model hierarchy, they _cannot_ be nested. Individual `Gprim`s are rarely tagged as `component` models.
* `assembly`: Assemblies aggregate `component` models. In a city of buildings, the city would be an `assembly`. Assemblies may be nested. For example, a city `assembly` may contain multiple district `assembly` models.
* `subcomponent`: These prims do not participate in model hierarchy traversals, but indicate important descendant prims of `component` models. `subcomponent` prims may be arbitrarily nested. In a city of `component` buildings, the doors on each building may be "important" to picking and other user interface browsers. `component` models that need to reference other `component` models often will override the `kind` to `subcomponent` to avoid violating model hierarchy rules.

The fourth first class kind is that of `group` which must be explicitly specified on prims that are not `assembly` models but may contain `assembly` or `component` models. `group` acts to bridge model hierarchies on non-"important" scopes that may contain important descendants. For completeness, it's important to note that `assembly` models are necessarily `group`s because they may contain models (`component` or other `assembly` models).

Let's look at an example of model hierarchy correctly used.
```
def Scope "TriStateArea" (kind = "group") {
    def Xform "NewYorkCity" (kind = "assembly") {
        def Scope "Water" (kind = "group") {}
        def Scope "Bridges" (kind = "group") {
            def Xform "BrooklynBridge" (kind = "component") {}
        }
        def Scope "Tunnels" (kind = "group") {
            def Xform "LincolnTunnel" (kind = "component") {}
        }
        def Scope "Boroughs" (kind = "group") {
            def Scope "Manhattan" (kind = "assembly") {
                def Scope "FifthAvenue" (kind = "group") {
                    def Xform "DepartmentStore" (kind = "component") {
                        def Scope "GroundFloor" {
                            def Scope "Housewears" (kind = "subcomponent") {
                                def Xform "Aisle_1" {
                                    def Mesh "TopShelf" {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```
> **Note** "GroundFloor" and "Aisle_1" do not have `kind` authored. It would be incorrect to set `kind=group` or `kind=assembly`
here. As a descendant of `component`, it may only be unset, or a `subcomponent`.

> **Note** There's no relationship between the type of a prim being a `Scope` or an `Xform` and its authored `kind`.

We've described `assembly` and `component` models as being "important" prims generally corresponding to referenced assets. While not provided or mandated by USD, it is likely that pipeline and tooling supports setup and maintenance of `assembly` and `component` models.

Prims with `kind=group` rarely correspond to assets. Their relevance to the model hierarchy is implicit from the fact that they _may_ contain important prims. `group` tagging exists solely so that model hierarchy traversal knows to keep descending in pursuit of more models.

## Problem
There aren't currently consequences to violating model hierarchy so it happens a lot. Model hierarchy doesn't affect rendering so tools and users may not be properly maintaining it. Even pipelines that attempt to honor model hierarchy may choose to repair model hierarchy only at specific validation points.

Invalid model hierarchy can lead to inconsistent results when using the `UsdModelAPI`. Consider the following scene description
```
def "root" (kind="group") {
    def "invalid_component_ancestor" {
        def "component" (kind="component") {}
    }

    def "invalid_group_ancestor" (kind="component") {
        def "group" (kind="group") {}
    }
}
```

Here is an example of how invalid model hierarchy behaves in the current state of the world.
```
>>> Usd.ModelAPI(stage.GetPrimAtPath("/root/invalid_component_ancestor/component")).GetKind()
'component'
>>> Usd.ModelAPI(stage.GetPrimAtPath("/root/invalid_component_ancestor/component")).IsModel()
False
>>> Usd.ModelAPI(stage.GetPrimAtPath("/root/invalid_component_ancestor/component")).IsKind("component")
False
>>> Usd.ModelAPI(stage.GetPrimAtPath("/root/invalid_group_ancestor/group")).GetKind()
'group'
>>> Usd.ModelAPI(stage.GetPrimAtPath("/root/invalid_group_ancestor/group")).IsGroup()
False
>>> Usd.ModelAPI(stage.GetPrimAtPath("/root/invalid_group_ancestor/group")).IsKind("group")
False
```
The validating form of `IsKind` rejects invalid `group` and `component`  specifications while `GetKind` just returns the authored metadata. Local inspection of the prim's metadata will not reveal the cause of this discrepency. 

What makes this especially worth addressing now is the new pattern based collection [proposal](https://github.com/PixarAnimationStudios/USD-proposals/pull/4) aims to leverage model hierarchy in its predicates. Model hierarchy will now affect (and potentially accelerate) collection membership computation. **Tagging a prim as an `assembly` or a `component` and failing to maintain proper `group` tagging could change the results of material bindings or light linking.**

Proper maintenance of model hierarchy involves performing hygene up and down the hierarchy. For users to rely on model hierarchy in their predicates, model hierarchy maintenance can't be deferred to a validation script or ignored.

Let's view an invalid version of model hierarchy on the above example.
```
def Scope "TriStateArea" (kind = "group") {
    def Xform "NewYorkCity" (kind = "assembly") {
        def Scope "Water" (kind = "group") {}
        def Scope "Bridges" {
            def Xform "BrooklynBridge" (kind = "component") {}
        }
        def Scope "Tunnels" {
            def Xform "LincolnTunnel" (kind = "component") {}
        }
        def Scope "Boroughs" (kind = "group") {
            def Scope "Manhattan" (kind = "assembly") {
                def Scope "FifthAvenue" (kind = "group") {
                    def Xform "DepartmentStore" (kind = "component") {
                        def Scope "GroundFloor" {
                            def Scope "Housewears" (kind = "subcomponent") {
                                def Xform "Aisle_1" {
                                    def Mesh "TopShelf" {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```
Some scopes (`Bridges`, `Tunnels`) are missing their group tagging. A model hierarchy centric traversal of the stage will miss the `LincolnTunnel` and `BrooklynBridge`.

The automatic fix is obvious-- Find all `component` models and tag any untagged parents with `kind=group`. It seems like USD could just figure this out on its own eliding the need for `kind=group`. However, model hierarchy is cached during composition and not multi-pass. Making prim flag computation multi-pass is too complex a solution to this problem and would incur the cost of potentially reading `kind` metadata on the entire hierarchy.

## Proposal
The USD Glossary provides this guidance on model hierarchy maintenance.

> When assets are published/packaged with model kinds already established, the model hierarchy becomes mostly “self assembling”.

As the above examples demonstrate, a self assembling model hierarchy unfortunately has been complicated by the need for the "glue" `group` kind.

There is prior art for composition "fixing" errant model hierarchy. Consider just the department store. It's not uncommon to see users (incorrectly) apply the `group` kind to all `Xform` and `Scope` prims in a hierarchy.
```
def Xform "DepartmentStore" (kind = "component") {
    def Scope "GroundFloor" (kind = "group") {
        def Scope "Housewears" (kind = "subcomponent") {
        }
    }
}
```

The authored `group` kind is ignored with respect to model hierarchy because its parent isn't a `group` or `assembly`. With minimal trade-offs, this proposal argues that just as incorrect usage can be discarded by composition, _correct `group` usage can be propagated by composition_.

More simply-- **untagged children of groups and assemblies are automatically groups**.

When applied recursively, this simple change would correct most incorrect model hierarchy usage and vastly simplify maintenance. Model hierarchy would be "self assembling".

Let's revise the example, removing sites where explicit authoring of `kind=group` would no longer be necessary.
```
def Scope "TriStateArea" (kind = "group") {
    def Xform "NewYorkCity" (kind = "assembly") {
        def Scope "Water" {}
        def Scope "Bridges" {
            def Xform "BrooklynBridge" (kind = "component") {}
        }
        def Scope "Tunnels" {
            def Xform "LincolnTunnel" (kind = "component") {}
        }
        def Scope "Boroughs" {
            def Scope "Manhattan" (kind = "assembly") {
                def Scope "FifthAvenue" {
                    def Xform "DepartmentStore" (kind = "component") {
                        def Scope "GroundFloor" {
                            def Scope "Housewears" (kind = "subcomponent") {
                                def Xform "Aisle_1" {
                                    def Mesh "TopShelf" {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```
In this example, because `NewYorkCity` is an `assembly` (and therefore a `group`), its descendant `Water`, `Tunnels`, `Bridges`, and `Boroughs` scopes are automatically `group` prims. Propagation would end at the `BrooklynBridge`, `LincolnTunnel`, and `DepartmentStore` `component` models.

### Performance When Model Hierarchy is Unused
It's worth noting that the pseudo-root is automatically a `group`. Propagation will need to be suppressed in that case with an additional check to see if the parent is the
pseudo root. A prim's status as the pseudo root is already cached as a prim flag.

For a stage which does not specify model hierarchy, no additional reads of `kind` will be required.
```
# `kind` is unset on `/root` so it is not a `group`.
# `kind` has to be read on `/root` but /not/ on any descendant
# There are no additional reads of `kind`
def "root" {
    def "child" {
        def "descendant" {}
    }
}
```
The only additional required cost is the read of the pseudo root prim flag for all root prims to suppress propagation.

### Performance When a Model Hierarchy is Complete and Explicitly Specified
We define a "complete" model hierarchy where every leaf prim is either a descendant of a `component` (or is a `group`, `assembly`, or `component`).

If a model hierarchy is complete and explicitly no additional reads of `kind` will be required.

```
# `kind` has to be read only on the prims
# where it is explicitly specified but none of
# the descendants of the `component` models.
def "root" (kind = "group") {
    def "assembly" (kind = "assembly") {
        def "group" (kind = "group") {
            def "component_1" (kind = "component") {
                def "gprim_1" {}
                def "gprim_2" {}
            }
            def "component_2" (kind = "component") {
                def "gprim_1" {}
                def "gprim_2" {}
            }
        }
    }
}
```
No pseudo root checks are required because the model hierarchy is complete and explicitly specified.

### Performance When a Model Hierarchy is Complete and Implicitly Specified
If every leaf prim is a descendant of a `component` model and `group` is /not/ explicitly set, no additional reads of `kind` will be required.

```
# `kind` has to be read on the prims where it is explicitly
# specified plus the `/root/assembly/group` prim.
# It is not read on the descendants of the `component` models.
def "root" (kind = "group") {
    def "assembly" (kind = "assembly") {
        def "group" {
            def "component_1" (kind = "component") {
                def "gprim_1" {}
                def "gprim_2" {}
            }
            def "component_2" (kind = "component") {
                def "gprim_1" {}
                def "gprim_2" {}
            }
        }
    }
}
```
Any prim that is a child of a `group` (or `assembly`) prim not explicitly specified will pay the cost of the pseudo root prim flag check. In this case, that's only `/root/assembly/group`.

### Performantly Handling an Incomplete Hierarchy
The fundamental challenge of this proposal is determining how to performantly handle an incomplete hierarchy.

```
# An incomplete model hierarchy-- The "East River Conundrum"
def Xform "NewYorkCity" (kind = "assembly") {
    def Scope "Water" (kind = "group") {
        def Mesh "EastRiver" {}
        def Material "EastRiverMaterial" { ... }
    }
}
```

The "EastRiver" is geometry just inlined as a mesh into the "NewYorkCity" assembly with a material. This "incomplete" hierarchy is not incorrect.  It just means that there are leaf prims that are not `component` descendants.

It's worth noting that in the current implementation without propagation, `kind` will be checked on the `EastRiver` and `EastRiverMaterial` scopes. **If we can signal that propagation should end on these scopes, then we can provide a path for self assembling model hierarchies without additional `kind` reads.**

#### Variant #1: Introduce a new `auto` kind which enables propagation
`auto` becomes `kind`'s new fallback value. The "EastRiver" and other members of the incomplete hierarchy could be explicitly tagged with `kind=""` to preserve current behavior. Propagation for `group` or `assembly` kinds is `group`.

#### Variant #2: Use authored state to control propagation
Only propagate when `kind` is unauthored. This is effectively the same as `auto` in that "EastRiver" can be tagged with `kind=""` to suppress propagation.

In user interfaces, it may be hard to disambiguate between unauthored (and propagating) and authored (not propagating) `kind` state. There would also not be way to author a value to re-enable propagation, but this may be fine.

#### Variant #3: Use `subcomponent` (or some other kind) to prune traversal
Despite its name, there are no rules that `subcomponent` prims are descendants of `component` prims. One could use that or some other kind to meaningful stop traversal. `kind=none` has been another suggestion. Even if variant #1 or #2 were adopted, this would still be a valid way to prune traversal, it just wouldn't be the only (or preferred) way.

### Instancing
Propagation when `instanceable=True` is complicated, as a prim may have multiple parents with different model hierarchy validity. There are actually [bugs](https://github.com/PixarAnimationStudios/USD/issues/2406) with this today.

The USD development team proposes that prim flags are considered in concert with composition arcs when constructing prototypes to deal with this ambiguity.

Until that fix is available, the best that can be done in both the current state of the world and with self propagating hierarchies is to encourage users to be intentional about model hierarchy when authoring `instanceable` to avoid violating the hierarchy's continuity.

### Additional API

To further simplify usage of model hierarchy for developers, this proposal also advocates introducing `IsAssemblyModel` and `IsComponentModel` methods on `UsdModelAPI`, along with associated cached prim flags and traversal predicates.

To better clarify what it means to be a "model group", this proposal recommends deprecating `IsGroup` in favor of `MayContainComponentModel`.

This proposal also recommends `IsModel` should be deprecated in favor of `MayContainOrIsComponentModel` and should be equivalent to (`MayContainComponentModel() || IsComponentModel()`).

Prim flag predicates should be be added to match these APIs. 

The USD core API could also provide ranges to iterate explicitly over `assembly` or `component`  prims, skipping over the intermediate prims. This might be easier to provide in C++20 (with the forthcoming ranges specification) and could be deferred until that point.

An early version of this proposal considered whether some of these APIs should extend to the `subcomponent` kind, but given they aren't a part of model hierarchy and cannot be cached in the same way, that's been deferred.

### Forward / Backwards Compatability
Assets that don't use model hierarchy or that are both "complete" and "explicit" do not require any updates to be forward or backwards compatable.

To make assets backwards compatible, implicit groups need to be made explicit. To make assets forward compatible, incompete model hierarchies need to author explicit `kind=""`. Both of these could be handled via a script.

We can also enabling/disabling propagation through a feature flag to give sites time to test any unexpected impact on their assets.

## Summary
Model hierarchy can become "self assembling" without intermediate `group` tags AND without additional `kind` reads.

* In scenes where model hierarchy is unused, an additional prim flags query on the root prims will be required to suppress propagation from the pseudo root prim.
* In scenes where the model hierarchy is complete and explicit, there will be no additional queries of either prim flags or `kind`.
* In scenes where the model hierarchy is complete but implicit through propagation, there will be an additional prim flags check on every prim that requires propagation.
* In scenes where the model hierarchy is incomplete, a traversal pruning, non-`component` `kind` will need to be explicitly authored. As long as they are authored at the highest possible level, there will be no additional `kind` queries.

If rendering behavior is going to increasingly depend on model hierarchy being correctly specified through path expressions, it's important to simplify correct assembly and maintenance of model hierarchy for users and tools.

## Questions
* This proposal hand waives prevelance of invalid model hierarchies as "a lot". Are the cases of invalid model hierarchy ultimately anecodatal and tooling for assembling it strong enough that it doesn't warrant any changes?
* This proposal takes care to enumerate when `kind` queries will be necessary but does not distinguish between when the query returns an authored or fallback value. Is that worthy of consideration?