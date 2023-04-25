# Self Assembling Model Hierarchy
Copyright © 2023, NVIDIA Corporation, version 1.0

## Goal
Simplify correct model hierarchy construction through removal of the need for explicit `kind=group` tagging.

## Background
USD presents "model hierarchy" as a mechanism for efficient traversal of a stage's "important" prims. This importance generally corresponds to the stage's referenced assets, but is pipeline independent, persistent under flattening of arcs, and allows for "casual" use of composition operators without implying "importance" (ie. using internal references to reuse scene description).

Model hierarchy is expressed through a prim's `kind` metadata. It's worth noting that `kind` is an extensible concept, but that won't be addressed in this document as to participate in model hierarchy, they must derive from one of the official `kind`s. `kind` is distinct from and orthogonal to a prim's schema type.

* `component`: This `kind` represents the leaf in model hierarchy traversals. What defines a `component` can be context dependent. In the context of a city, each building may be a `component`. In the context of a room, pieces of furniture may be `component`s. As they represent leaves in the model hierarchy, they _cannot_ be nested.
* `assembly`: Assemblies aggregate `component` models. In a city of buildings, the city would be an `assembly`. Assemblies may be nested. For example, a city `assembly` may contain multiple district `assembly` prims.
* `subcomponent`: These prims do not participate in model hierarchy traversals, but indicate important descendant prims of `component` models. `subcomponent` prims may be arbitrarily nested. In a city of `component` buildings, the doors on each building may be "important" to picking and other user interface browsers. `component` models that need to reference other `component` models often will override the `kind` to `subcomponent` to avoid violating model hierarchy rules.

The fourth first class kind is that of `group` which must be explicitly specified on prims that are not `assembly` prims but may contain `assembly`  or `component` prims. `group` acts to bridge model hierarchies on non-"important" scopes that may contain important descendants. For completeness, it's important to note that `assembly` prims are necessarily `group`s because they may contain models (`component` or other `assembly` prims).

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

We've described `assembly` prims as being "important" prims generally corresponding to referenced assets. While not provided or mandated by USD, it is likely that pipeline and tooling is supporting versioning and setup of `assembly` and `component` models.

For prims with `kind=group`, importance in model hierarchy is implicit from the fact that they _may_ contain important prims. `group` tagging exists solely so that traversal knows to keep going.

## Problem
There aren't currently consequences to violating model hierarchy so it happens a lot. Model hierarchy doesn't affect rendering so tools and users may not be properly maintaining it. Even pipelines that attempt to honor model hierarchy may choose to repair model hierarchy only at specific validation points.

What makes this worth addressing now is the new pattern based collection [proposal](https://github.com/PixarAnimationStudios/USD-proposals/pull/4) aims to leverage model hierarchy in its predicates. Model hierarchy will now affect (and potentially accelerate) collection membership computation. **Tagging a prim as an `assembly` or a `component` could change the results of material bindings or light linking.**

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

The automatic fix is obvious-- Find all `component` models and tag any untagged parents with `kind=group`. It seems like USD could just figure this out on its own eliding the need for `kind=group`. However, model hierarchy is cached during composition and not multi-pass. Making prim flag computation multi-pass is too complex a solution to this problem.

## Proposal
The USD Glossary has this aspirational take on model hierarchy maintenance.

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

The authored `group` kind is ignored with respect to model hierarchy because its parent isn't a `group` or `assembly`. With minimal few trade-offs, this proposal argues that just as incorrect usage can be discarded, _correct `group` usage can be propagated_.

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

(For completeness, it's worth noting that the pseudo-root is automatically a `group`. Propagation will need to be suppressed in that case.)

This proposal has minimal trade-offs, not no trade-offs. Consider this example.

```
# The "East River Conundrum"
def Xform "NewYorkCity" (kind = "assembly") {
    def Scope "Water" (kind = "group") {
        def Mesh "EastRiver" {}
    }
}
```

The "EastRiver" is geometry just inlined as a mesh into the "NewYorkCity" assembly. It is not violating model hierarchy rules but has a non-`component` `Mesh` as a descendant of a `group`. The trade-offs come from how this case should be handled.

#### Variant #1: `component` prims are still the only leaves
We can say that it's okay that the "EastRiver" is now considered a `group`. All we've said is that it "might" contain models. The vast majority of prims in the scene graph will still be skipped during model hierarchy searches.

The biggest drawback is when you considered material networks introduced at the assembly level, there could be a large number of prims to traverse. It may not make sense to nudge these materials into `component` models to prune traversal.

#### Variant #2: Introduce a new `auto` kind which enables propagation
`auto` becomes `kind`'s new fallback value. The "EastRiver" could be explicitly tagged with `kind=""` to preserve the current behavior. Propagation for `group` or `assembly` kinds is `group`. All other kinds propagate `""`.

#### Variant #3: Use authored state to control propagation
Only propagate when `kind` is unauthored. This is effectively the same as `auto` in that "EastRiver" can be tagged with `kind=""` to suppress propagation.

In user interfaces, it may be hard to disambiguate between unauthored (and propagating) and authored (propagating) `kind` state. There would also not be way to author a value to re-enable propagation, but this may be fine.
#### Recommendation
This proposal advocates #2 or #3 as being the best choice as they minimize impact to current usage. The only thing that would have to change is `kind=""` would have to be explicitly authored to explicitly stop propagation. The biggest risk to either of these usages is that code sites may be doing explicit `GetMetadata("kind")` calls and comparisons instead of using the `UsdModelAPI`. For clarity, some of these variations may benefit from the concept to author a more explicit model hierarchy block-- say `kind="none"`, but no proposal strictly requires introducing this.

### Instancing
Propagation when `instanceable=True` is complicated, as a prim may have multiple parents with different model hierarchy validity. There are actually [bugs](https://github.com/PixarAnimationStudios/USD/issues/2406) with this today.

The USD development team proposes that prim flags are considered in concert with composition arcs when constructing prototypes to deal with this ambiguity.

Until that fix is available, the best that can be done in both the current state of the world and with self propagating hierarchies is to encourage users to be intentional about model hierarchy when authoring `instanceable` to avoid violating the hierarchy's continuity.

### Additional API

To further simplify usage of model hierarchy for developers, this proposal also advocates introducing `IsAssembly`, `IsComponent`, and `IsSubcomponent` methods on `UsdModelAPI`, along with associated cached prim flags and traversal predicates.

This proposal also recommends `IsModel` should be deprecated in favor of `IsModelHierarchy` and should be equivalent to (`IsGroup() || IsComponent()`).

The `UsdPrimIsModel` predicate should be deprecated in favor of `UsdPrimIsModelHierarchy` and should be equivalent to `UsdPrimIsGroup || UsdPrimIsComponent`.

The USD core API could also provide ranges to iterate explicitly over `assembly`, `component` or `subcomponent` prims, skipping over the intermediate prims. This might be easier to provide in C++20 (with the forthcoming ranges specification) and could be deferred until that point.

## Summary
This proposal aims to fufill the promise of self assembling model hierarchy as indicated in the USD documentation. If rendering behavior is going to depend on model hierarchy being correctly specified through path expressions, it's important to simplify correct assembly and maintenance of model hierarchy for users and tools.

As the "East River Conundrum" demonstrates, there isn't a trade-off free solution to this problem, but importantly, the trade-offs can be largely mitigated for currently correctly specified model hierarchies and API usage.

## Questions
* This proposal rules out multi-pass population of prim data. Was that a correct assumption?
* This proposal hand waives prevelance of invalid model hierarchies as "a lot". Are the cases of invalid model hierarchy ultimately anecodatal and tooling for assembling it strong enough that it doesn't warrant any changes?
* Should incorrect model hierarchy (`component`, `assembly`, and `group` models under `component` models) be communicated as warnings rather than just suppressed?