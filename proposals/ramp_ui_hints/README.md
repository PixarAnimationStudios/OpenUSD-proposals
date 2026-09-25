# UI Hints for Ramps

## Background

The [UI Hints](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/85)
proposal introduced a unified and consistent mechanism for describing potentially
complex authoring interfaces in USD.
Ramp widgets were deliberately excluded from that initial proposal.

This proposal picks up that thread.
Ramps are a staple of shading and look-development workflows and are used to
describe value-over-position mappings such as color gradients or opacity falloffs.
Despite their ubiquity, each renderer and DCC currently defines its own ramp property
encoding with no shared schema to tie them together.

A ramp is generally represented by a combination of the following properties:

- An array of knot positions (typically in the range [0, 1])
- An array of knot values (float or color)
- An array of interpolation modes per knot, or a single scalar for a global
  interpolation mode
- An optional knot count (some renderers, such as RenderMan, store the ramp size
  as a separate property, though it can usually be inferred from the position and
  value arrays)

These properties are disparate and currently there is no unified mechanism to
declare that a set of properties should be presented to the user as a ramp 
widget, or to describe the relationships between those properties.

## Proposal

We propose adding a set of new metadata fields to the `uiHints` dictionary that
identify the sibling properties comprising a ramp and instruct UIs to present them
as a single ramp widget.

The metadata is placed on the **values property**, which becomes the canonical
anchor for a ramp.
This placement is both semantically appropriate, the value type of that property
determines whether the ramp is a float ramp or a color ramp, and enables robust
validation, since each unique ramp on a prim is identified by exactly one property.

All other ramp-related properties (positions, interpolations, and optionally size)
should be declared with `hidden = 1` so that no standalone widget is shown for them.
All ramp-related properties must be defined on the same prim.

### Metadata Fields

The following fields are added to the `uiHints` dictionary:

The ramp metadata is grouped under a `ramp` sub-dictionary inside `uiHints`:

| Field Name | Value Type | Description |
|---|---|---|
| `ramp.valuesPropertyName` | `token` | Name of this property (the values property). Used to identify it as the ramp anchor. |
| `ramp.positionsPropertyName` | `token` | Name of the sibling property that holds the knot positions. |
| `ramp.interpolationsPropertyName` | `token` | Name of the sibling property that holds the interpolation modes. |
| `ramp.sizePropertyName` | `token` (optional) | Name of the sibling property that holds the knot count. Omit if the schema does not require it. |

These fields may be set on both USD Attributes and Shader Properties.

### Example

The following example shows a complete ramp encoding.

```usda
#usda 1.0

def Shader "example"
{
    float[] my_ramp_positions = [0.0, 0.1, 0.4, 1.0] (
        uiHints = {
            bool hidden = 1
        }
    )

    color3f[] my_ramp_values = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0, 1.0)] (
        uiHints = {
            string displayName = "Color Ramp"
            dictionary ramp = {
                token valuesPropertyName = "my_ramp_values"
                token positionsPropertyName = "my_ramp_positions"
                token interpolationsPropertyName = "my_ramp_interpolations"
                token sizePropertyName = "my_ramp_size"
            }
        }
    )

    int[] my_ramp_interpolations = [1, 0, 1, 1] (
        uiHints = {
            bool hidden = 1
            dictionary valueLabels = {
                int constant = 0
                int linear = 1
                int bezier = 2
            }
            token[] valueLabelsOrder = ["constant", "linear", "bezier"]
        }
    )

    int my_ramp_size = 4 (
        uiHints = {
            bool hidden = 1
        }
    )
}
```

The same encoding applies to float ramps, only the value type differs:

```usda
float[] my_ramp_values = [0.0, 0.5, 0.8, 1.0] (
    uiHints = {
        string displayName = "Opacity Ramp"
        dictionary ramp = {
            token valuesPropertyName = "my_ramp_values"
            token positionsPropertyName = "my_ramp_positions"
            token interpolationsPropertyName = "my_ramp_interpolations"
        }
    }
)
```

### Property Roles

#### Values property (ramp anchor)
The property whose name is stored in `ramp.valuesPropertyName` holds the metadata
and acts as the single authoritative identifier for the ramp.
It carries any user-facing metadata such as `displayName` or `displayGroup`.
All other ramp properties should be hidden and have no user-facing presentation.

#### Positions property
An array property storing normalized knot positions.
It must be declared `hidden = 1`.

#### Interpolations property
Either an array (one entry per knot, for per-knot interpolation) or a scalar
(for global interpolation).
The topology, array vs scalar, determines which mode is in use, no additional
metadata field is needed.
It must be declared `hidden = 1`.
The `valueLabels` and `valueLabelsOrder` fields on the interpolations property
describe the interpolation modes that the ramp UI should offer and map
human-readable labels to the underlying stored values.

#### Size property (optional)
A scalar integer holding the knot count.
Required only for renderers that need an explicit size property separate from the
position and value arrays.
It must be declared `hidden = 1`.

### Ramp Type

The type of the values property determines the ramp type:

- `color3f[]`, `color4f[]`, or other color array types -> color ramp
- `float[]` or other float array types -> float ramp
- `double[]` or other double array types -> double ramp

### Interpolation

Interpolation modes vary between renderers, so USD does not prescribe a fixed set.
The `valueLabels` metadata on the interpolations property maps string labels to
integer values, and `valueLabelsOrder` controls the display order in the UI.
This mechanism reuses existing `uiHints` fields without requiring new metadata.

The `valueLabels` mechanism is intentionally open-ended to accommodate
renderer-specific extensions.

## Details and Discussion

### Validation

Because the ramp metadata is always placed on the values property, validation is
straightforward: for each property on a prim that contains a `uiHints.ramp` dictionary,
verify that:

1. `ramp.valuesPropertyName` matches the name of the property it is declared on.
2. The property named by `ramp.positionsPropertyName` exists as a sibling.
3. The property named by `ramp.interpolationsPropertyName` exists as a sibling.
4. The property named by `ramp.sizePropertyName` exists as a sibling, if present.
5. All sibling ramp properties are marked `hidden = 1`.
6. No sibling ramp property also carries a `uiHints.ramp` dictionary (each
   ramp has exactly one anchor).

This set of invariants is checkable by a USD validator without evaluating any
scene values.

### Attribute Connections

Connections to ramp properties should be handled using the existing USD connection
system.
Per-knot connections can be fulfilled by additional multi-input-to-array nodes that
convert individual float or color values into a single array suitable for the shader.

### Weights for Tangent-Based Interpolation

Some interpolation modes (such as Bézier or Hermite) require explicit tangent
handles per knot.
However, a review of available renderer documentation did not surface these modes
as commonly supported in shading ramp contexts. The modes found in practice
(constant, linear, Catmull-Rom, monotone cubic) are all self-contained and do
not require additional per-knot weight data.

If future work or community feedback identifies renderers that do support
tangent-based ramp interpolation, a weights property could be introduced as an
additional optional sibling, referenced by a new `ramp.weightsPropertyName` field
analogously to the existing sibling fields.
For now, weight encoding is deferred.

### Existing Scenes

Because the metadata only adds additional context and does not change the
underlying data representation, existing scenes that already encode ramp data
as separate arrays can be upgraded by adding the appropriate `uiHints` metadata
without modifying the data itself.
This allows existing assets to work as-is while gaining ramp widget support in
UIs that understand the new metadata.

### SdrShaderProperty

Shader discovery (`Sdr`) will need to reflect similar encoding.
Specifically, `SdrShaderProperty` should expose the ramp metadata, and the
`usdgenschemafromsdr` conversion utility should translate it through to generated
USD schemas. 

The metatadata itself can be handled in a similar manner as the schema description. The value property would remain the anchor, and provide the metadata description to tie the related properties together.

This could be handled by the existing `GetHints`, where we the TokenMap can still match the documented paths mentioned previously. Similarly it would be expected that `GetWidget` would return `ramp`. The type information similarly being handled by existing `GetTypeAsSdfType()` method.

## Open Questions

1. **Common interpolation token set**: Should USD define a fixed set of
   well-known interpolation token names and their semantics, even if renderers
   are free to extend the list?

2. **Tangent-based interpolation**: Are there renderers or production workflows
   that require Bézier or Hermite interpolation for shading ramps, and if so,
   how are the tangent weights currently encoded?
   This would determine whether a `ramp.weightsPropertyName` field is needed.
