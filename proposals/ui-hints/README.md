# UI Hints in USD

## Background

There's been a desire for several years to expand and formalize support for presentation metadata (aka "UI hints") in USD. The goal being to provide an improved language for describing potentially complex authoring interfaces like we find on shaders and lights.

The target set of hints (see below) is mainly adapted out of the world of Katana "args" files ([docs](https://learn.foundry.com/katana/dev-guide/ArgsFiles/index.html)), which provide a rich and battle-tested set of concepts.

## Proposal

We propose adding a new dictionary-valued metadata field, `uiHints`, that will contain most UI-relevant hint values. This field will be added to prims and properties by the UsdUI library, using the plugin metadata mechanism ([docs](https://openusd.org/release/api/sdf_page_front.html#sdf_plugin_metadata)). UsdUI will also contain API to read and write the individual hint entries that the dictionary holds. 

Some of the existing UI-relevant fields (see table below) will migrate into the `uiHints` dictionary, and some will stay where they are now. Those moving are the ones determined to be *only* about presentation, while the rest are *content* that describes the owning object per se. These content fields are relevant to UIs but also have other potential uses or meanings.

We also propose deprecating the `displayGroupOrder` field entirely (see the "Interleaved Ordering of Properties and Display Groups" section below).

### Existing UI-relevant Fields

|Field Name|Owning Core Object|Value Type|Move into dict?|Description|
| --- | --- | --- | --- | --- |
|displayName|UsdObject|string|**Yes**|User-facing name for a prim or property|
|hidden|UsdObject|bool|**Yes**|Whether the object should be hidden from the UI|
|displayGroup|UsdProperty|string|**Yes**|The name of the display group to which the property belongs|
|documentation|UsdObject|string|No|User-facing description of the object's role or purpose|
|allowedTokens|UsdAttribute|token array|No|Expected/valid values a string or token attribute can take on. Used to populate a combo box widget for the attribute.|
|propertyOrder|UsdPrim|token array|No|The (partial) order in which the prim's properties should appear|
|displayGroupOrder|UsdPrim|string array|No|The order in which the prim's display groups should appear|

### New `uiHints` Fields

In addition, the following new hints are proposed for inclusion in the `uiHints` dictionary. See the discussion sections below for more details on what some of these new values mean.

|Field Name|Relevant Core Object|Value Type|Description|
| --- | --- | --- | --- |
|shownIf|UsdProperty|string|Conditional visibility expression for the property|
|valueLabels|UsdAttribute|dictionary|Expected/valid values an attribute can take on, keyed by string labels to be used in a combo box widget|
|valueLabelsOrder|UsdAttribute|token array|The order in which the keys from ValueLabels should be presented in the combo box|
|~widgetType~ (deferred, see section below)|~UsdAttribute~|~string~|~The name of a widget to be used for displaying and editing an attribute~|
|~widgetOptions~ (deferred, see section below)|~UsdAttribute~|~dictionary~|~Configuration options for the named widget~|
|displayGroupsExpanded|UsdPrim|dictionary|Default open/closed state for the prim's display groups|
|displayGroupsShownIf|UsdPrim|dictionary|Conditional visibility expressions for the prim's display groups|

### New Core Fields

#### Limits

We also propose adding a new `limits` top-level metadata field on UsdAttribute for holding minimum and maximum values. It's not part of the `uiHints` dictionary since, while relevant to UIs, it also has important non-UI applications.

`limits` will be dictionary-valued so that the held min and max values can match the value type of the attribute. Actual values will be held in sub-dictionaries corresponding to a particular purpose. Primarily, this means separate "soft" and "hard" limits sub-dictionaries that specify suggested and strict min/max values, but the access API will support reading and writing other sub-dictionaries as well.

So for example we might have the following limits dictionary that specifies a soft range of [1, 100] for a sphere radius, and a hard minimum at 0. 

```
def Sphere "MySphere"
{
    double radius = 10.0 (
        limits = {
            dictionary "soft" = {
                double minimum = 1.0
                double maximum = 100.0
            }
            dictionary "hard" = {
                double minimum = 0.0
            }
        }
    )
}
```

USD will not enforce limits values in its authoring APIs, but will provide a validator to flag instances where an authored value is out of the hard range. Such out-of-bounds values should be considered errors.

#### ArraySizeConstraint

Finally, we also propose adding an `arraySizeConstraint` metadata field of type `int64` to UsdAttribute to describe information commonly specified in shaders relating to expected array size and encoding. The value encoding is as follows:
* `arraySizeConstraint == 0` (the fallback value) indicates the array is dynamic and its size unrestricted
* `arraySizeConstraint > 0` indicates the exact, fixed size of the array
* `arraySizeConstraint < 0` indicates a tuple-length (i.e., column count) of `N = abs(arraySizeConstraint)`; the array's size is unrestricted, but must be a multiple of `N`

This multi-purpose encoding aims to minimize the number of metadata reads needed, and reduce the potential for contradictory values, e.g, specifying a fixed array size that is not a multiple of the tuple size. Multidimensional tuple-length and arrays with a fixed number of tuples are not possible with this encoding, but we think this is unlikely to be an issue in practice.

As with `limits`, USD will not enforce these constraints at the level of authoring, but will provide validation that the authored array size is consistent with `arraySizeConstraint`.

### Access API

Access to UI hints can be provided by "schema-like" API objects that live in the UsdUI library. They are not formally schemas because they must interpret the `uiHints` dictionary on all the core object types, not just UsdPrim. Like schemas however, they will be passed an instance of the relevant object on construction and provide a convenient API that hides details like field keys and extraction from VtValue. `UsdGeomPrimvar` ([docs](https://openusd.org/dev/api/class_usd_geom_primvar.html)) follows a similar pattern.

These API classes will also help ensure that an object's `uiHints` dictionary will only contains hints that are relevant for its type (e.g., `valueLabels` makes no sense on a UsdPrim). Templated accessors for dictionary-valued fields like `limits` and `widgetOptions` should make them easier to work with.

For example, the hints class corresponding to UsdAttribute might look like this:

```cpp
// Hint class inheritance matches corresponding core objects
class UsdUIAttributeHints : public UsdUIPropertyHints
{
public:
    UsdUIAttributeHints(const UsdAttribute& attr);

    VtDictionary GetValueLabels() const;
    void SetValueLabels(const VtDictionary& labels) const;

    TfTokenVector GetValueLabelOrder() const;
    void SetValueLabelOrder(const TfTokenVector& order) const;

    std::string GetWidgetType() const;
    void SetWidgetType(const std::string& widgetType);

    VtDictionary GetWidgetOptions() const;
    void SetWidgetOptions(const VtDictionary& options) const;

    // Templated helper API for sub-dicts
    template <typename T>
    T GetWidgetOption(const TfToken& optionKey) const;

    template <typename T>
    void SetWidgetOption(const TfToken& optionKey, const T& value) const;

    ...
};

// Client code
const UsdAttribute attr = ...;
const UsdUIAttributeHints hints(attr);

if (!hints.GetWidgetType().empty()) {
    ...
}

// Templated API on UsdAttribute for Limits dictionary
if (val >= attr.GetMinimumValue<double>() and val <= attr.GetMaximumValue<double>()) {
    ...
}

// DisplayName API inherited from UsdUIObjectHints   
hints.SetDisplayName(...);
```

## Details and Discussion

### Backwards Compatibility for Relocated Fields

The existing hint fields that are moving into the `uiHints` dictionary (`displayName`, `displayGroup`, and `hidden`) will need to be deprecated at their old locations. The transition plan is to:

* Mark the current get/set API as deprecated in documentation
* Add a deprecation warning to the set API in `Usd` and `Sdf`, controlled by an environment symbol
* Make the new get API in UsdUI fall back to the old fields when no value is present in the `uiHints` dictionary
* Eventually, remove the old get/set API and `SdfSchema` fields

The UsdUI API will provide long-term backwards compatibilty for old assets even after the old fields and APIs are removed.

### Consequences of Dictionary Encoding

Using a dictionary-based encoding gives us a nice encapsulation of hint values at the data level, but has a couple of side effects to note. The composition semantics for dictionary metadata are to merge entries across all layers. So calling, e.g., `SetWidgetOptions(const VtDictionary&)` is an additive operation rather than a complete/exclusive specification -- field entries specified in weaker layers that are not expressly overridden will get composed into the final result. This also means there's no way to "block" an entire subdict like `widgetOptions`, or the `uiHints` dictionary as a whole, by authoring an empty dictionary value.

Using a dictionary also means that USD has no built-in mechanism for providing fallback values for each individual field. Appropriate fallbacks will be returned from the UsdUI API when no authored value is present, but won't be available via, e.g., `SdfSchema::GetFallback()`.

### Conditional Visibility

Conditional visibility (embodied in the `shownIf` fields in the table above) allows properties and display groups to be dynamically hidden or shown in the UI based on the values of other attributes on the owning prim. This is a critical mechanism for complex shading and lighting interfaces that can contain many dozens of controls.

The held value of these conditional fields are logical expressions that reference other properties on the same prim. In Katana's args format (and elsewhere), they are encoded as a dictionary of strings representing the parse tree of the desired expression ([docs](https://learn.foundry.com/katana/dev-guide/ArgsFiles/WidgetsAndHints.html#conditional-visibility-and-locking)).

For USD we'd like to introduce a more straightforward expression encoding along the lines of `SdfPathExpression` ([docs](https://openusd.org/dev/api/class_sdf_path_expression.html)). `shownIf` expressions will be serialized as strings but accessed via a new expression data type, tentatively named `SdfBooleanExpression`.

```
def Scope "MyLight"
{
    custom int enableShadows = 0

    # Only show these if enableShadows is turned on
    custom color3d shadowColor = (0, 0, 0) (
        uiHints = {
            string shownIf = "enableShadows == 1"
        }
    )
    custom double shadowMaxDistance = -1.0 (
        uiHints = {
            string shownIf = "enableShadows == 1"
        }
    )
}
```

API will be provided to construct and evaluate these expressions, and help with invalidation when a referenced value changes. More technical details coming soon on how these expressions and their API will look.

### Value Labels

USD already has the `allowedTokens` field, which provides an allowable set of values that attributes can take on. In UIs these string values are typically used to populate a dropdown or combo box widget for users to select from. `allowedTokens` is only for string- and token-valued attributes, however, and its values are displayed as-is in the UI. The `valueLabels` field gives us a way to associate human-meaningful display labels with arbitrary underlying values. For example:

```
def Scope "Scope"
{
    custom int level = 0 (
        uiHints = {
            dictionary valueLabels = {
                int "all the way" = 11
                int high = 2
                int low = 0
                int medium = 1
            }
            token[] valueLabelsOrder = ["low", "medium", "high", "all the way"]
        }
    )
}
```

The popup UI for the `level` attribute would display "low", "medium", "high", and “all the way” options, and author the corresponding numeric values when the user makes a selection. Since dictionary entries are always sorted lexicographically by key, we also have the list-valued `valueLabelsOrder` field to specify display order.

### Additional Display Group Fields

We want to add hints that convey additional information about display groups (default expansion state and conditional visibility). But display groups are not first-class objects that can carry metadata on their own -- they are implicitly created by virtue of being referenced by properties. Thus we put the additional information we need into the `uiHints` dictionary of the owning UsdPrim. These new hints (`displayGroupsExpanded` and `displayGroupsShownIf`) are themselves dictionaries, keyed by group name and storing boolean values and SdfBooleanExpression strings, respectively.

### Interleaved Ordering of Properties and Display Groups

Organizing and ordering e.g., shader interfaces is extremely important for usability. Interleaving properties and display groups, at both the top level of a prim and within a given display group, is common. USD however has separate `propertyOrder` and `displayGroupOrder` fields, and no official guidance on how to combine them.

Consider for instance:

```
def Scope "Scope" (
    displayGroupOrder = ["Group2", "Group1"]
)
{
    reorder properties = ["prop4", "prop1"]

    custom double prop1 = 0
    custom double prop2 = 0 (
        displayGroup = "Group1"
    )
    custom double prop3 = 0 (
        displayGroup = "Group2"
    )
    custom double prop4 = 0
}
```

Property and group order are separately specified, presumably producing something like this in a UI display:

```
+ Scope
  - prop4
  - prop1
 
  + Group2
    - prop3
  + Group1
    - prop2
```

But there’s no way to produce an interleaved order like this:

```
+ Scope
  - prop4
 
  + Group2
    - prop3
 
  - prop1
 
  + Group1
    - prop2
```

For example, RenderMan's `BarnLightFilter` specifies an interface that looks like this, with the `barnMode` parameter acting as a switch that shows and hides the `Projection` group via conditional visibility.

```
+ Notes (group)
  - note
 
- combineMode
- barnMode
 
+ Projection (group)
  - directional
  - shearX
  - shearY
  - apex
  - useLightDirection
 
+ Barn Shape (group)
  - width
  - height
...
```

We propose deprecating the `displayGroupOrder` field and relying on `propertyOrder` to determine where both properties and groups show up in UIs. `propertyOrder`'s formal semantics remain the same -- a partial ordering of properties belonging to a prim. But it can be used by DCCs to place display groups where they are first referenced by a property when building out UIs. For example, to produce the BarnLightFilter structure above, we just need to specify a depth-first ordering of its parameters: `[note, combineMode, barnMode, directional, shearX, shearY, apex, useLightDirection, width, height, ...]`

### Updates to Sdr

Fields for the new hint values will need to be added to `SdrShaderProperty`. Its existing API and field names can remain as they are (e.g., it deals in the more shader-centric terms "label" and "page" instead of the analogous "display name" and "display group" on the USD side).

The `usdgenschemafromsdr` conversion utility will also require updates to translate the new Sdr hint fields through to its generated USD schema.

### Widget Type and Widget Options

**NOTE: After additional discussion and external feedback, we think it's prudent to defer implementation of the `widgeType` and `widgetOptions` fields. They will remain in the proposal as a reference and starting point for future discussions.**

The `widgetType` field provides a way to specify the editor widget that UIs should use for an attribute. This field is string-valued and freeform, but we’d also like to describe, and provide key tokens for, a set of basic widget types as a starting point for DCCs to use and extend.

Relatedly, `widgetOptions` is a dictionary-valued field for configuring the named widget.

#### Basic Types and Options

This list of "basics" is derived from those supported by the args format, adapted to USD. It leans toward generality and minimalism since it’s only a starting point. It's meant to encourage commonality between DCCs, but is not a contract that _must_ be implemented. DCCs are free to ignore whatever is not useful to them, and also to recognize non-standard widget types and options that may be useful for their specific purposes.

|Widget Type|Widget Description|Options|Option Type|Option Fallback|Option Description|
| --- | --- | --- | --- | --- | --- |
|checkBox|A simple checkbox widget||||
|number|A numeric field, handling both floating point and integer attributes|forceInt|bool|false|For float fields, whether to require integer input|
|||digits|int|-1 (full precision)|For float fields, the number of digits to display after the decimal point|
|||base|int|10|Numeric base to display the number in (decimal, hex, etc)|
|||sensitivity|double|1.0|Modification sensitivity for e.g., value scrub operations, if the number field itself is directly scrubbable|
|||slider|bool|false|Whether to show a slider widget next to the number field|
|||sliderMin|double|0.0|Minimum slider value|
|||sliderMax|double|1.0|Maximum slider value|
|||sliderCenter|double|0.5|Origin value of the slider|
|||sliderSensitivity|double|0.1|Slider sensitivity|
|||sliderExponent|int|1|Non-linear scaling factor for the slider|
|text|A string input field|multiLine|bool|false|Whether the text field should be single- or multi-line|
|popup|Combo box presenting predefined value options. Contents populated by the allowedTokens and valueLabels fields (see discussion section above).|editable|bool|false|Whether the combo box should allow free-form input in addition to the predefined choices|
|color|Color picker widget||||
|assetInput|Text field with a button to launch a filesystem browser|fileTypes|string[]|[]|List of file extensions to filter for|
|||assetKind|string|""|General asset type (e.g., “texture”)|
|||multiSelect|bool|false|Whether to allow multiple assets to be selected|
|||acceptDir|bool|false|Whether directories are selectable as assets|
|||dirsOnly|bool|false|Whether only directories are selectable|
|scenegraphPath|Picker widget for a location in the scenegraph||||

#### What's Not Included in the "Basics"

Some of the common widget types present in the args format are intentionally left off this list, including "boolean" (an alternate for “checkBox” that shows a Yes/No combo box), "mapper" (a combo box populated with labeled values), and float and color ramp widgets.

These omissions are generally motivated by parsimony and complexity. For example, the effect of the "boolean" and "mapper" widget types can be achieved by setting WidgetType="popup" and providing an appropriate set of value labels. In our research, different DCCs and shading systems had little agreement on ramp features and encodings, so we're leaving them out for now. We can revisit down the road if it becomes clear that standardizing ramps would be desirable.
