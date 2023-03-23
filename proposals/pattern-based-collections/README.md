# Pattern-Based Collections for OpenUSD
The ability to identify collections of objects in scenes is crucial to many digital content workflows. OpenUSD has an existing applied API schema, [`UsdCollectionAPI`](https://openusd.org/dev/api/class_usd_collection_a_p_i.html) to do this, but currently operates in terms of hierarchical include/exclude rules. This is inconvenient or insufficient for some tasks. So DCCs often provide richer ways to identify collections, allowing wildcard object name matching and predicate testing. Just a couple of current examples are [Katana's CEL](https://learn.foundry.com/katana/dev-guide/CEL.html) and [Houdini Solaris' Prim Matching Patterns](https://www.sidefx.com/docs/houdini/solaris/pattern.html). Here we propose to add extensible pattern-based collection support to OpenUSD, for use in `UsdCollectionAPI` and other domains, drawing inspiration from CEL and Solaris.

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

These predicate functions take zero or more arguments, including arguments with default values, and may be invoked in three different ways:
- `predicate` a bare invocation with no arguments.
- `predicate:arg1,...,argN` invocation with unnamed positional arguments separated by commas with no spaces.
- `predicate(arg1, keyword=value, ...)` invocation with multiple positional and keyword arguments, spaces allowed.

Boolean operators `not`, `and`, `or` can combine predicate functions, and `(` `)` can group and establish evaluation order. In addition, whitespace between two predicate functions implies the `and` operator.

The specific set of available predicate functions (like `isa`, `purpose`, and `kind` above) is domain-specific. That is, each domain that implements a pattern-based collection can register its own set of predicate functions appropriate to the objects the collection identifies. The specific set of predicate functions we propose for `UsdCollectionAPI` (and thus to be authored in scene description) are listed below.

As a convenience, a predicate expression alone (without a Path Matching Pattern), like `{isa:Imageable}` is shorthand for `//*{isa::Imageable}`.  That is, all prim paths match.  Similarly, a Path Matching Pattern element that is empty except for a predicate expression, like `/World//{isa:Camera}` is shorthand for `/World//*{isa:Camera}`.  That is, all prim names at that location match.

#### Built-in Prim Predicate Functions for UsdCollectionAPI
- `abstract(bool=true)` match prims that are or are not abstract (`UsdPrim::IsAbstract`)
- `defined(bool=true)` match prims that are or are not defined (`UsdPrim::IsDefined`)
- `model(bool=true)` match prims that are or are not considered models (`UsdPrim::IsModel`)
- `group(bool=true)` match prims that are or are not considered groups (`UsdPrim::IsGroup`)
- `kind(kind1, ... kindN, strict=false)` match prims of any of given kinds. If `strict=true` matching subkinds is not allowed, only exact matches pass.
- `purpose(purpose1, ... purposeN)` match prims with any of the given purposes.
- `specifier(specifier1, ... specifierN)` match prims with any of the given specifiers.
- `isa(typeName1, ... typeNameN, strict=false)` match prims that are any typed schema typeName1..N or subtypes.  Disallow subtypes if `strict=true`.
- `hasAPI(typeName1, ... typeNameN, instanceName='')` match prims that have any of the applied API schemas 1..N.  Limit matches by `instanceName` if supplied.
- `variant(setName1 = selGlob1 .. selGlobN, ... setNameN = ...)` match prims that have matching selections for variant setNames 1..N.

#### Matching Prims by Testing Properties, and Matching Properties
We can expand the above syntax to support matching prims by testing their properties, and to match properties themselves, if desired.  However, we may not support this in the first implementation.
- `//Robot*//.*color` select all properties whose names end in "color" on prims whose names start with "Robot".
- `//Robot*//{isa:Sphere .radius{value:default:closeTo:0}}` select all the `Sphere` prims beneath "Robot" prims whose `radius` attributes' `default` values are close to 0.
- `//Robot*//{isa:Sphere}.radius{value:default:closeTo:0}` select all the `radius` attributes on `Sphere` prims beneath "Robot" prims whose `default` values are close to 0.

### Pattern-Based Collection Expressions
A single Path Matching Pattern (with optional Predicate Expressions) is a Collection Expression, but several may also be combined using set-algebra operators.
- Whitespace or the `+` operator forms the set union of two Collections.
- `&` forms the set intersection of two Collections.
- `-` forms the set difference, the left hand Collection minus the right hand.
- `~` complements a Collection.
- `(` `)` may be used to group and enforce evaluation order.

#### Collection References
In addition, collection references (starting with `%`) may be combined with Path Matching Patterns as above.
- `%_` refers to to the next "weaker" collection expression in scene description.  This way `UsdCollectionAPI` expression opinions can make incremental modifications to existing collections if desired.
  - For example, `%_ /Added/Prim` would union `/Added/Prim` with whatever the weaker-composed collection would match. `%_ - /main_cam` would match everything the weaker collection would match, except `/main_cam`.
- In the `UsdCollectionAPI` schema domain, `%/path/to:collectionName` refers to a specific collection on another prim.  For example, `%/House/Lights:KeyLights` refers to the collection `/House/Lights.collections:KeyLights`, and `%:collectionName` refers to a sibling collection on this prim.
  - Note that wildcards/patterns are not allowed in the names of collection references.

### Future Possibilities
As mentioned earlier, initially we may not support querying attribute values.  One concern is that we do not want collections (at least UsdCollectionAPI collections) to be time-varying.  We may consider supporting testing some kinds of attribute values at specific, nonvarying times.

## Software Structure
### New Sdf Attribute Value Type: `SdfPathExpression`
- Contains the expression string as its fundamental data.
- Provides API to:
  - Compose over weaker `SdfPathExpressions`
  - Support path translation across composition arcs: `SdfPathExpression::ReplacePrefix` (as employed by `PcpMapFunction`).
    - In USD value resolution, we will path-translate any "non-speculative" prefixes (i.e. pattern-free elements) of Path Matching Patterns in the same way that relationship and connection target paths are translated today.
    - For example, in `/CharacterGroup/Character//*_sbdv` we would path-translate the `/CharacterGroup/Character` prefix across composition arcs.
    - Collection reference paths will be path-translated similarly.
  - Parse, validate, and introspect.
    - Provide syntax error feedback with source locations.
  - Build expressions by set operations

We will add a built-in attribute, `expression` to `UsdCollectionAPI` of this type.

Note that `SdfPathExpression` can only syntactically validate the predicate expressions that appear within `{` `}`.  The language itself (e.g. the valid predicate function names and their signatures) must be provided externally, and can vary from domain to domain.  For example, in UsdCollectionAPI, the set of functions are those proposed above.  However, predicates in a Hydra Scene Index domain, or in a DCC GUI component may augment or modify these.

### Evaluation Engine: `SdfPathExpressionEvaluator`
An `SdfPathExpression` object is in general incapable of evaluation.  Generally the paths it matches against are only a property of the actual objects of interest.  For example, an expression that wants to test a UsdPrim's "kind" needs the `UsdPrim`, not only its path.  For this it needs to be told what its domain objects are, and how to obtain the SdfPath from a given domain object.  For example, a common case will have `UsdObject` as the domain and `UsdObject::GetPath()` as the means to obtain `SdfPaths`. It also needs to be given the names, signatures, and implementations of all the predicate expression functions.
- Contains an `SdfPathExpression`
- Contains knowledge of a functional domain (such as `UsdObject`, `SdfSpecHandle`, or `UI_Element`) and how to obtain `SdfPath`s from domain objects.
  - Also contains knowledge of how to obtain child objects (e.g. prim & property children) to facilitate searching for matches.
- Contains the set of named predicate expression functions, their function signatures & implementations.
- Contains functions that can answer whether or not a given predicate is "closed" over an interval in the domain.  For example, an `isModel` predicate is always false for descendants of `UsdPrim`s that are `component`s.  This will serve as the basis for important performance optimizations.
- Provides API to:
  - Validate and report errors. `SdfPathExpression` can validate _syntax_, but it cannot say whether the name of a predicate expression function is valid, for example, or if it has been passed the required number of arguments, etc.
  - Test individual domain elements for matches
  - Search a domain interval for matches
    - Batch-compute all matches
    - Generate matches incrementally

### USD Support
- Add custom USD value resolution support for `SdfPathExpression`-valued attributes. Primarily this means consuming opinions, applying the relevant path translations, and composing stronger over weaker until we have a complete expression.  That is, one that does not contain a reference to the next weaker expression: `%_`
- Add custom API to `UsdCollectionAPI` for expressions to create `SdfPathExpressionEvaluator` objects for matching on the `UsdStage`
