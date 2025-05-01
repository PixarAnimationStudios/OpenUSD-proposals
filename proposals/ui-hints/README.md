# Widget Types in USD

Work is underway at Pixar to expand and formalize support for UI hints in USD. One key piece of this will be to add an explicit “widget type” metadata field to specify the editor widget that UIs should use for an attribute. This field will be string-valued and freeform, but we’d also like to describe, and provide key tokens for, a set of basic widget types as a starting point for DCCs to use and extend.

## Widget Options

Alongside `WidgetType`, we’re planning to provide a `WidgetOptions` field on UsdAttribute. This would be a dictionary-valued field for configuring an attribute’s widget with values that don’t make sense to include as “top-level” attribute metadata in their own right. It also provides a spot for DCCs to add their own custom options without having to modify the core schema.

## Basic Types and Options Proposal

Following is a working proposal for a set of basic widget types and options. These are mainly adapted from Katana’s “args” file format (docs [here](https://learn.foundry.com/katana/dev-guide/ArgsFiles/index.html)) for describing node interfaces. It leans toward generality and minimalism since it’s only a starting point.

|Widget Type|Widget Description|Options|Option Type|Option Description|
| --- | --- | --- | --- | --- |
|checkBox|A simple checkbox widget||||
|number|A numeric field, handling both floating point and integer attributes|forceInt|bool|For float fields, whether to require integer input|
|||digits|int|For float fields, the number of digits to display after the decimal point|
|||strictLimits|bool|Whether to strictly enforce the attribute’s value range (to be held in the soon-to-be-added MinimumValue and MaximumValue metadata fields)|
|||sensitivity|double|Modification sensitivity for e.g., value scrub operations, if the number field itself is directly scrubbable|
|||slider|bool|Whether to show a slider widget next to the number field|
|||sliderMin|double|Minimum slider value|
|||sliderMax|double|Maximum slider value|
|||sliderCenter|double|Origin value of the slider|
|||sliderSensitivity|double|Slider sensitivity|
|||sliderExponent|int|Non-linear scaling factor for the slider|
|text|A string input field|multiLine|bool|Whether the text field should be single- or multi-line|
|popup|Combo box presenting predefined value options. Contents populated by the AllowedTokens and ValueLabels fields (see discussion section below).|editable|bool|Whether the combo box should allow free-form input in addition to the predefined choices|
|color|Color picker widget||||
|assetInput|Text field with a button to launch a filesystem browser|fileTypes|string[]|List of file extensions to filter for|
|||assetKind|string|General asset type (e.g., “texture”)|
|||multiSelect|bool|Whether to allow multiple assets to be selected|
|||acceptDir|bool|Whether directories are selectable as assets|
|||dirsOnly|bool|Whether only directories are selectable|
|scenegraphPath|Picker widget for a location in the scenegraph||||

## Array Support

For array-valued attributes, DCCs can present a series of one of the basic widgets listed above, or provide custom array widget types to handle special cases. To support array-editing widgets, the following widget options are proposed in addition to those above.

|Widget Option|Type|Description|
| --- | --- | --- |
|arraySize|int|A fixed or expected size of the array|
|arrayIsDynamic|bool|Whether the array should be allowed to grow and shrink dynamically|
|arrayTupleSize|int|Column count|

## What’s Not Included in the “Basics”

Some of the common widget types present in the args format are intentionally left off this list, including "boolean" (an alternate for “checkBox” that shows a Yes/No combo box), "mapper" (a combo box populated with labeled values), and float and color ramp widgets.

These omissions are generally motivated by parsimony and complexity. For example, the effect of the "boolean" and "mapper" widget types can be achieved by setting WidgetType="popup" and providing an appropriate set of value labels (see the next section for more discussion on the `ValueLabels` field).

The ramp widgets in Katana are driven by a 4-attribute encoding specifying the knots and interpolation. But ramps at other studios and DCCs have widely varying feature sets, knot types, and parameterizations, making standardization difficult.

## Populating Popup Widgets

USD already has the `AllowedTokens` field, which provides an allowable set of values that string attributes can take on. In UIs these string values are typically used to populate a dropdown or combo box widget for users to select from. We’d also like to add a dictionary-valued `ValueLabels` field to provide additional flexibility for populating these kinds of UIs.

`ValueLabels` gives us a way to associate human-meaningful display labels with arbitrary underlying values. For example:

```
def Scope "Scope"
{
    custom int level = 0 (
        valueLabels = {
            int "all the way" = 11
            int high = 2
            int low = 0
            int medium = 1
        }

        valueLabelsOrder = ["low", "medium", "high", "all the way"]
    )
}
```
The popup UI for the `level` attribute would display "low", "medium", "high", and “all the way” options, and author the corresponding numeric values when the user makes a selection. Since dictionary entries have a fixed order (`TfDictionaryLessThan` by key), we'd also add the list-valued `ValueLabelsOrder` field to specify display order.
