# Pattern-Based Collections for OpenUSD
The ability to identify collections of objects in scenes is crucial to many digital content workflows. OpenUSD has an existing applied API schema, [`UsdCollectionAPI`](https://openusd.org/dev/api/class_usd_collection_a_p_i.html) to do this, but it is limited to hierarchical include/exclude rules. This is inconvenient or insufficient for some tasks. So DCCs often provide richer ways to identify collections, allowing wildcard/glob style object name matching and predicate testing.  Just a couple of current examples are [Katana's CEL](https://learn.foundry.com/katana/dev-guide/CEL.html) and [Houdini Solaris' Prim Matching Patterns](https://www.sidefx.com/docs/houdini/solaris/pattern.html). Here we propose to add pattern-based collection support to OpenUSD, drawing inspiration from CEL and Solaris.

## Requirements and Guiding Principles
- Membership testing must not require possibly unbounded search. To achieve this, patterns may only consider the object itself (and its properties in case of a `UsdPrim`) and its ancestors.
- The [`UsdCollectionAPI`](https://openusd.org/dev/api/class_usd_collection_a_p_i.html) is an important use-case for this technology. But we expect it to be used in other domains to identify non-`UsdObject`s that are also identified by `SdfPath`s.  For example, in Hydra Scene Indexes, or in user-facing GUI components. To support this we will build an extensible library that may be adapted to different domains, of which `UsdCollectionAPI` is just one.

## Basic Syntax
### Path Matching Patterns
The syntax for `SdfPath` matching is similar to that for `SdfPath` itself, with the following changes:
- Path elements may contain `/Gl*b/[Ss]tyle/patt?rns`
- Double-slash `//` indicates arbitrary levels of hierarchy, e.g. `/World//cup` matches any prim named `cup` descendant to `/World`.

### Predicate Expressions
Each path element in a Path Matching Pattern may optionally include a Predicate Expression that can test object qualities. Predicate Expressions are introduced by braces: `{}`.
- `//Robot*{kind:component}` select all prims whose name starts with `Robot` and have `kind=component`.
- `//Robot*{kind:component}//{isa:Imageable purpose:guide}` select all imageable guides descendant to `Robot` components.

These predicate functions take zero or more arguments, and may be invoked in three different ways:
- `predicate` a bare invocation with no arguments.
- `predicate:arg1,...,argN` invocation with unnamed positional arguments separated by commas with no spaces.
- `predicate(arg1, keyword=value, ...)` invocation with multiple positional and keyword arguments, spaces allowed.

The specific set of available predicate functions (like `isa`, `purpose`, and `kind` above) is domain-specific. That is, each domain that implements a pattern-based collection can register its own set of predicate functions, appropriate for the kinds of objects that the collection identifies.
