# Conditional UI Visibility

## Background
This proposal builds on top of the [UI Hints](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/85) proposal.  It expands on the concept of "conditional visibility", the proposed `shownIf` metadata field, and the associated boolean expression language.

For a complex prim with many attributes, subsets of these attributes might not be applicable at any given time. For example, a prim representing a light may have an attribute controlling whether shadows are enabled, as well as a set of shadow-specific attributes. When shadows are not enabled, these additional attributes are not applicable and contribute to a cluttered UI. Conditional visibility improves the situation by allowing attributes and display groups to be hidden from the UI based on small pieces of logic stored as metadata. This logic decides whether an attribute/group should be hidden based on the values of other attributes on the owning prim. It will often want to be provided as part of a schema definition, but can also be authored by users.

A notable example of conditional visibility comes from Katana, where the conditions are expressed in "args" files ([docs](https://learn.foundry.com/katana/dev-guide/ArgsFiles/index.html), [UI docs](https://learn.foundry.com/katana/Content/ug/groups_macros_super_tools/conditional_behavior.html)). In Katana, visibility conditions are essentially expression trees that produce a boolean value based on the values of other attributes on the prim.

## Proposal
We propose a new metadata field named `shownIf` that allows an attribute or display group to be hidden from the UI based on the result of an embedded logic condition. These logic conditions can perform comparison operations on attributes of the owning prim and are represented using a compact and concise expression language. A new class (`SdfBooleanExpression`) is provided to aid in parsing, evaluating, and otherwise manipulating these expressions.

### Intepretation of the `shownIf` field
The `shownIf` field is a member of the `uiHints` dictionary; it holds a UTF-8 encoded string representing a logic condition and is parsed according to the boolean expression syntax described below. Its value is interpreted as follows:

|Value of `shownIf` field|Interpretation|
|-|-|
|Not present|Visible|
|Empty string|Visible|
|Malformed expression|Visible|
|Expression evaluating to `true`|Visible|
|Expression evaluating to `false`|Hidden|

### Relation to the `hidden` field
The existing `hidden` field serves a similar purpose, indicating whether an attribute should be visible in the editor UI, though it can only hold an unconditional `true` or `false` value. DCCs supporting the `shownIf` field should hide an attribute if *either* field indicates that it should be hidden. In other words, an attribute is hidden if either:
- The `hidden` field holds the value `true`, or
- The `shownIf` field holds an expression that evaluates to `false`

If neither condition is met, the attribute should be visible.

### Boolean Expression Language
The syntax for boolean expression is intended to be concise and recognizable to those familiar with C/C++. An expression can be a boolean constant, a comparison between variables and values, or a boolean operations containing one or more sub-expressions.

#### Constants
The simplest allowed expressions are the boolean constants:
- `true`
- `false`

#### Comparison Operations
A comparison operation takes two operands and one of the supported operators (`==`, `!=`, `>`, `>=`, `<`, `<=`). The operands may be either variables or constant values. A variable is expressed as a [USD property name](https://openusd.org/release/glossary.html#usdglossary-property); the permitted syntax for variables is identical to that of properties as supported by [`SdfPath`](https://openusd.org/dev/api/class_sdf_path.html#details). A constant value can be a number, a string, or a boolean value.

- `numOps != 3`
- `mode == 'default'`
- `width > 10.0`

##### String Literals
Strings may be either single (') or double (") quoted. Escape-sequences are supported following the conventions of [`TfEscapeString`](https://openusd.org/dev/api/group__group__tf___string.html#gab6646faf6bcb393bab4d0e7deffa63c2). Only single-line strings are permitted (no unescaped newline characters).
- `"double-quoted string"`
- `'single-quoted string'`
- `"string with\nescaped newline"`

#### Boolean Operations
A boolean operation takes two subexpressions and one of the supported boolean operators (`&&`, `||`)
- `numOps != 3 && mode == 'default'`
- `width > 10.0 || height > 10.0`

#### Parenthesized expressions `(...)`
Parenthesis may be used to group subexpressions.
- `numOps != 3 && (width > 10.0 || height > 10.0)`

#### Complement Operator
The complement operator performs the boolean NOT operation, inverting the result of a subexpression.
- `!(width > 10.0 || height > 10.0)`

### Example
In the following example, a prim representing a light has an attribute that controls whether shadows are enabled (`enableShadows`). Twoadditional shadow-related attributes, `shadowColor` and `shadowMaxDistance`, are only displayed in the UI if the `enableShadows` attribute has a value of `1`.
```usda
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

Alternatively, the shadow-related properties could be grouped into a namespace:
```usda
def Scope "MyLight"
{
    custom int shadow:enable = 0

    # Only show these if shadow:enable is turned on
    custom color3d shadow:color = (0, 0, 0) (
        uiHints = {
            string shownIf = "shadow:enable == 1"
        }
    )
    custom double shadow:maxDistance = -1.0 (
        uiHints = {
            string shownIf = "shadow:enable == 1"
        }
    )
}
```

## Details

### `SdfBooleanExpression`
This class encapsulates a boolean expression and provides API for parsing, evaluating, assembling, and traversing expressions.

#### Parsing
An expression can be constructed from a string, which will be parsed according to the boolean expression grammar. If the constructor is unable to parse the expression, the resulting object will be 'empty' and the underlying error message can be accessed via the `GetParseError` method. The string-equivalent of an expression can be accessed via the `GetText` method and is suitable for passing to the `SdfBooleanExpression` constructor to reconstitute an expression.

When constructing an expression from a string, a callback must be provided to aid in the type-resolution of any variables encountered while parsing the expression. The callback will receive the name of the variable and should return the appropriate `SdfValueTypeName`.

```cpp
class SdfBooleanExpression {
public:
    using TypeCallback = TfFunctionRef<SdfValueTypeName (TfToken const&)>;

    SdfBooleanExpression(std::string const& text,
                         TypeCallback const& typeCallback);

    bool IsEmpty() const;

    std::string GetText() const;

    std::string const& GetParseError() const;

    // ...
};
```

#### Evaluation
An expression can be evaluated to produce a boolean value. During evaluation, the provided callback will be invoked to determine the current value for any variables referenced in the expression. The list of variables referenced within an expression is available via `GetVariableNames`. Clients may wish to observe those variables to determine when the expression should be reevaluated.

```cpp
class SdfBooleanExpression {
public:
    // ...

    using ValueCallback = TfFunctionRef<VtValue (TfToken const&)>;

    bool Evaluate(ValueCallback const& valueCallback) const;

    std::set<TfToken> GetVariableNames() const;

    // ...
};
```

#### Assembling Expressions
A new expression can be constructed progammatically without resorting to string-manipulation. Static methods are provided for constructing all of the supported expression types.

```cpp
class SdfBooleanExpression {
public:
    // ...

    enum class BooleanOp {
        And,
        Or,
    };

    enum class ComparisonOp {
        EqualTo,
        NotEqualTo,
        LessThan,
        LessThanOrEqualTo,
        GreaterThan,
        GreaterThanOrEqualTo,
    };

    static SdfBooleanExpression
    MakeComparisonOp(Operand const& lhs,
                     Operand const& rhs,
                     ComparisonOp op);

    static SdfBooleanExpression
    MakeBooleanOp(SdfBooleanExpression const& lhs,
                  SdfBooleanExpression const& rhs,
                  BooleanOp op);

    static SdfBooleanExpression
    MakeComplement(SdfBooleanExpression const& expression);

    static SdfBooleanExpression const& True();

    static SdfBooleanExpression const& False();

    // ...
};
```

#### Traversing Expressions
The traversal API mirrors the assembly API. The `Visit` method allows one to inspect an expression, where one of the provided callbacks will be invoked depending on the type of the underlying expression.

```cpp
class SdfBooleanExpression {
public:
    // ...

    using ComparisonVisitor = TfFunctionRef<void(Operand const&,
                                                 Operand const&,
                                                 ComparisonOp)>;

    using BooleanVisitor = TfFunctionRef<void(SdfBooleanExpression const&,
                                              SdfBooleanExpression const&,
                                              BooleanOp)>;

    using ComplementVisitor = TfFunctionRef<void(SdfBooleanExpression const&)>;

    using ConstantVisitor = TfFunctionRef<void(bool)>;

    void Visit(ComparisonVisitor comparison,
               BooleanVisitor boolean,
               ComplementVisitor complement,
               ConstantVisitor constant) const;

    // ...
};
```

### Sdr Compatibility with Katana-style Conditional Visibility

The format for conditional visibility introduced by Katana has also seen unofficial adoption in other formats such as Open Shading Language.

#### `SdrShaderNode`
To take advantage of existing conditional visibility metadata, `SdrShaderNode` will be updated to detect and convert this metadata to the format proposed here. Specifically, metadata fields of the form `conditionalVisOp`/`conditionalVisPath`/`conditionalVisValue`/etc will be combined into a `shownIf` field, though only if there is not an explicit `shownIf` field already. After converting to a `shownIf` expression, the existing conditional visibility metadata will be preserved to avoid breaking compatibility with other clients.

#### `SdrShaderProperty`
`SdrShaderProperty` will be updated to provide an accessor for `shownIf` expressions, either authored directly in shaders or converted as described above.
```cpp
class SdrShaderProperty {
public:
    // ...
    SDR_API
    std::string GetShownIf() const;
    // ...
};
```
