# Self Assembling Model Hierarchy
Copyright © 2023, NVIDIA Corporation, version 1.3

## Goal
Simplify correct model hierarchy maintenance and construction through removal of the need for explicit `kind=group` tagging without incurring _any_ additional reads of `kind` metadata.

## Background
OpenUSD presents "model hierarchy" as a mechanism for efficient traversal of a stage's "important" prims. This importance generally corresponds to the stage's referenced assets, but is pipeline independent, persistent under flattening of arcs, and allows for "casual" use of composition operators without implying "importance" (ie. using internal references to reuse scene description).

Model hierarchy is expressed through a prim's `kind` metadata. It's worth noting that `kind` is an extensible concept, but that won't be addressed in this document as to participate in model hierarchy, they must derive from one of the standard `kind`s. `kind` is distinct from and orthogonal to a prim's schema type.

There are several first class `kind` types.

* `component`: This `kind` represents the leaf in model hierarchy traversals. What defines a `component` can be context dependent. In the context of a city, each building may be a `component`. In the context of a room, pieces of furniture may be `component`s. As they represent leaves in the model hierarchy, they _cannot_ be nested. Individual `Gprim`s are rarely tagged as `component` models.
* `assembly`: Assemblies aggregate `component` models. In a city of buildings, the city would be an `assembly`. Assemblies may be nested. For example, a city `assembly` may contain multiple district `assembly` models.
* `subcomponent`: These prims do not participate in model hierarchy traversals, but indicate important descendant prims of `component` models. `subcomponent` prims may be arbitrarily nested. In a city of `component` buildings, the doors on each building may be "important" to picking and other user interface browsers. `component` models that need to reference other `component` models often will override the `kind` to `subcomponent` to avoid violating model hierarchy rules.

The fourth first class kind is that of `group` which must be explicitly specified on prims that are not `assembly` models but may contain `assembly` or `component` models. `group` acts to bridge model hierarchies on non-"important" scopes that may contain important descendants. For completeness, it's important to note that `assembly` models are necessarily `group`s because they may contain models (`component` or other `assembly` models).

Let's look at an example of correct model hierarchy usage.
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
The complexity of maintaining model hierarchy complicates its usage. Model hierarchy (until recently) didn't affect rendering so tools and users may not be properly maintaining it. Even pipelines that attempt to honor model hierarchy may choose to repair model hierarchy only at specific validation points.

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

### Maintenance of Model Hierarchy
Proper maintenance of model hierarchy involves performing hygene up and down the hierarchy. Let's view an invalid version of model hierarchy on the above example.
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

### Model Hierarchy Complexity
The complexity of model hierarchy maintenance can lead users to the following workarounds.
* Some users flood the scene graph with `group` tags and make all `Xform` prims `group`s (erroneously including those specified under `component` models).
* Some users build model-discovery features around direct calls to `GetKind()` instead of the cached `IsKind()` to workaround model hierarchy rules, paying for the caching without benefiting and potentially leading to inconsistencies with how `kind` is handled across the ecosystem. Users may believe tooling that relies on the unvalidated `GetKind()` behaves more correctly.
* Finding model hierarchy unreliable or complicated, some users begin to build model-discovery features around composition arc presence. `kind` as a first class feature was designed in part to aid in discovery of important prims _without composition introspection_ and to perserve behavior across flattening of arcs.

### Model Hierarchy Impacting Imaging
Model hierarchy originally could not affect the rendered result and so the consequences of incorrect model hierarchy patterns were minimal. However, the new pattern based collection [proposal](https://github.com/PixarAnimationStudios/USD-proposals/pull/4) aims to leverage model hierarchy in its predicates. Model hierarchy will now affect (and potentially accelerate) collection membership computation. **Tagging a prim as an `assembly` or a `component` and failing to maintain proper `group` tagging could change the results of material bindings or light linking.**

### Model Hierarchy and Namespace Editing
Recent additions to OpenUSD include the namespace editor and relocates. Scene graph restructuring may become more common as a result of these utilities, and with it model hierarchy invalidations.

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

> **Note** This proposal frames `group` as being an "unimportant" bridge kind, but that tooling and pipelines may not have reasoned about `group` in the same way. Please read `group` propagation not as literally propagating the `kind` field onto descendants but just that the prim may contain descendants in the _model hierarchy_.

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
Despite its name, there are no rules that `subcomponent` prims are descendants of `component` prims. One could use that or some other kind to meaningful stop traversal. `kind=none` (or `kind=terminal`) has been another suggestion. Even if variant #1 or #2 were adopted, this would still be a valid way to prune traversal, it just wouldn't be the only (or preferred) way.

### Instancing
Propagation when `instanceable=True` is complicated, as a prim may have multiple parents with different model hierarchy validity. There are actually [bugs](https://github.com/PixarAnimationStudios/OpenUSD/issues/2406) with this today.

The OpenUSD development team proposes that prim flags are considered in concert with composition arcs when constructing prototypes to deal with this ambiguity.

Until that fix is available, the best that can be done in both the current state of the world and with self propagating hierarchies is to encourage users to be intentional about model hierarchy when authoring `instanceable` to avoid violating the hierarchy's continuity.

### Additional API
To better clarify what it means to be a "model group", this proposal recommends deprecating `IsGroup` in favor of `MayContainComponentModel`.

This proposal also recommends `IsModel` should be deprecated in favor of `MayContainOrIsComponentModel` and should be equivalent to (`MayContainComponentModel() || IsComponent()`).

Prim flag predicates should be be added to match these APIs.

The `group` and `model` kinds in the model hierarchy definition would not be affected by these changes, only how they are presented through the API.

An early version of this proposal considered whether some of these APIs should extend to the `subcomponent` kind, but given they aren't a part of model hierarchy and cannot be cached in the same way, that's been removed.

### Forward / Backwards Compatability
Assets that don't use model hierarchy or that are both "complete" and "explicit" do not require any updates to be forward or backwards compatable.

To make assets backwards compatible, implicit groups need to be made explicit. To make assets forward compatible, _intentionally incompete_ model hierarchies need to author explicit `kind=""` (or some other terminating kind).

## Validation in Contrast and in Concert
OpenUSD anticipates including validation as a core service that can be used to detect and repair invalid model hierarchies.

A validation solution follows from an invalid parenting event to occur, generally a `component` or `assembly` being nested below a non-`group`. The user must be prompted to decide whether to change the `kind` of the nested asset (to something like `subcomponent`) or change the `kind` of any non-`group` ancestors.

However, users and tools generally expect to be able to parent `Xform`s underneath other `Xform`s without too much trouble (ie. an extra validation step). They also generally expect that such changes are local and invertible. Reparenting a scope and then undoing it (manually not through an undo queue) will leave spurious `group` tags on any ancestors or an unintentionally "demoted" model to `subcomponent`. Validating on the parenting event can lead to both cruft and blocking user decisions.

Prior to path expressions, delaying validation until `Save`-ing of a stage was perhaps viable. Not necessarily ideal that model hierarchy would be a broken state, but the impact would be limited to a session's interactive features and not imaging. Delaying validation as a post-process could lead to different material binding and light collections. A user saving a stage they are happy with and then validation informing them of errors that change the way the stage renders risks erroding user trust of validation. It also could lead to users avoiding building expressions around model hierarchy features. As model hierarchy is intended to be efficiently cached, relying on adhoc tags or naming conventions could reduce overall performance of path expressions.

Self assembling model hierarchy does not remove the need for validation of model hierarchy. However, it focuses it on the scopes that are changing and reduces the amount cases that can be considered invalid. We enumerate the potential invalid cases below.

### Invalid Case #1: Missing root prim `kind`
As a concession to performance and "pay for what you use", a hierarchy must opt into model hierarchy at the root prim. Validating and repairing a missing root prim kind has the same risks issues and without automatic group propagation. We suggest that users, tools, and pipelines are willing to treat root prims as special and more willing to carefully maintain and validate their correctness than intermediate scopes.
### Invalid Case #2: Nested `component` models
When `component` (or `assembly`) models are nested, the general recommendation is to turn the nested model into a `subcomponent`. Importantly, following this recommendation will not impact path expression matching. Model hierarchy population should have already discarded nested models in both. Converting them to `subcomponent` shores up existing model hierarchy correctness, but does not change the "model"-ness of any ancestors or descendants. (_NOTE-- It's possible that path expressions may match against subcomponents, and so a more conservative validation recommendation may be to convert their kind to the empty string._)
### Performance of incomplete model hierarchies
While self assembling model hierarchy does not introduce any new correctness issues, there is the potential for an unterminated hierarchy to do unnecessary reads of the `kind` field. This performance impact in the context of a stage is likely to be measurable but very small (1-2%). Proficient users and maintainers of model hierarchy should never encounter measurable performance issues.

Validation could be used to "optimize" an inefficient instead of "correct" an invalid hierarchy. Under self assembling model hierarchy, it would become acceptable to introduce optimizing terminal kinds when validating in a post-process. This proposal argues that users are likely to favor validators that optimize content without changing imaging behavior.

Self assembling model hierarchy can partner with validation systems by reducing the number of invalid states a stage can be in and reward users with performance gains instead of potentially leaving them stuck between introducing an imaging change and fixing a model hierarchy error.

## Summary
Model hierarchy can become "self assembling" without intermediate `group` tags AND without additional `kind` reads.

* In scenes where model hierarchy is unused, an additional prim flags query on the root prims will be required to suppress propagation from the pseudo root prim.
* In scenes where the model hierarchy is complete and explicit, there will be no additional queries of either prim flags or `kind`.
* In scenes where the model hierarchy is complete but implicit through propagation, there will be an additional prim flags check on every prim that requires propagation.
* In scenes where the model hierarchy is incomplete, a traversal pruning, non-`component` `kind` will need to be explicitly authored. As long as they are authored at the highest possible level, there will be no additional `kind` queries.

Simplifying correct assembly and maintenance of model hierarchy will promote more consistent handling in toolsets and imaging that increasingly depend on model hierarchy being correctly specified.