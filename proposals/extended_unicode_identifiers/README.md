# Extended unicode identifiers

Copyright &copy; 2024, NVIDIA Corporation, version 1.0

Miguel Hernandez  
Matthew Kuruc

# Contents

- [Introduction](#introduction)
- [Alternative Approaches](#alternative-approaches)
- [Requirements](#requirements)
- [Proposed solution](#proposed-solution)
- [Considerations on SdfPathExpression](#considerations-on-sdfpathexpression)
    - [Medial hyphen](#medial-hyphen)
    - [Leading digits](#leading-digits)
    - [Other considerations](#other-considerations)
- [Out of scope](#out-of-scope)
- [Examples](#examples)

# Introduction

In v24.03, OpenUSD introduced UTF-8 identifiers lifting many of the requirements
in different industries around the world respect to identifiers, i.e. the use of
different languages in Prim identifiers.
UTF-8 identifiers adhere to [Unicode XID](https://unicode.org/reports/tr31/) and
as such, some identifiers are still invalid, in particular identifiers with
leading digits and medial hyphens (i.e. `-`).
This type of identifiers are consistently used in different areas like
manufacturing and it is important to have a direct one-to-one mapping between
the virtual representation and the real world.

Examples of identifiers with these contraints include (but not limited to):

- International Standard Audiovisual Number (ISAN),
  example: `0000-0000-2CEA-0000-1-0000-0000-Y`.
- Building Information Modelling (ISO 19650),
  example: `PROJ-ORG-PH-LV-TYP-RL-CL-NUM-SUIT-REV`.
- International Standard Book Numbers (ISBN), example: `0-545-01022-5`.
- Universal unique identifiers (UUID),
  example: `192615d1-5749-4407-aa88-2c1d52470a86`.
- Proper name with medial hyphens, example: `Carmel-by-the-sea`.
- Language tags (RFC 5646), example: `en-US`.
- Hash values as SHA-128 or MD5, example: `7815696ecbf1c96e6894b779456d330e`.

For brevity in this proposal we refer to identifiers with leading digits and/or
medial hyphens as extended identifiers.

# Alternative approaches

The
proposal [Bi-Directional Transcoding of Invalid Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/37)
addresses this and other potential cases.
However it requires an implicit encoding and decoding of the strings with its
corresponding overhead. While transcoding is still relevant,
by addressing the issue of leading digits and medial hyphens we expect to
downscale the number of cases where transcoding needs to be applied.

# Requirements

| Category                          | Identifiers                 | Description                                                 |
|-----------------------------------|-----------------------------|-------------------------------------------------------------|
| Leading digits and medial hyphens | Prim, Variant sets, Variant | The identifiers addressed by this proposal.                 |
| Medial hyphens                    | Properties                  | Properties are excluded from using leading digits.          |
| Unchanged                         | Metadata fields             | Other identifiers such as metadata fields remain unchanged. |

For this proposal we look to support extended identifiers to Prim, Variant sets
and Variant identifiers, as their grammars should be the same. Metadata fields
should remain untouched by this proposal.
Multi-apply schema instance names could also allow leading digits and medial
hyphens and still conform to the property grammar.

# Proposed changes

Currently, the grammar for Prim and Variants is similar to:

```regexp
Utf8IdentifierStart = XIDStart | Underscore
Utf8IdentifierContinue = XIDContinue
Utf8Identifier = Utf8IdentifierStart Utf8IdentifierContinue*

PrimName = Utf8Identifier
VariantSetName = Utf8IdentifierStart (Utf8IdentifierContinue | MedialHyphen) *
```

We proposed to change it to described in XID
[UAX #31: Unicode Identifiers and Syntax](https://unicode.org/reports/tr31/#R1-2):

```regexp
Utf8IdentifierStart = XIDStart | Underscore | Digits
Utf8IdentifierContinue = XIDContinue
Utf8IdentifierMedial = MedialHyphen XIDContinue+
Utf8Identifier = Utf8IdentifierStart Utf8IdentifierContinue* Utf8IdentifierMedial*

PrimName = Utf8Identifier
VariantSetName = Utf8Identifier
```

Example of valid prim names include: `12345`, `123-456`, `abc-def` but
exclude `-123-456`, `123-456-`.

A respective change is expected for Properties, without the leading digits:

```regexp
Utf8PropertyNameStart = XIDStart | Underscore
Utf8PropertyNameContinue = XIDContinue
Utf8PropertyNameMedial = (MedialHyphen | MedialColon) XIDContinue+

PropertyName = Utf8PropertyNameStart Utf8PropertyNameContinue* Utf8PropertyNameMedial*
```

Example of valid property names include: `abc:123-456:def` but
exclude `abc:-123456:def`, `abc:123-456-:def`.

# Considerations on SdfPathExpression

As of v24.03, with the introduction of PEGTL grammar the changes on identifiers
do not represent a big challenge.
However there are implications to this proposal. The main one being the changes
regarding `SdfPathExpression`.
We list the restrictions below.

## Medial hyphen

Medial hyphen is already used in `SdfPathExpression` in two major forms:

- As regular expression pattern, for example `foo[0-9]`
- As a disjoint operator of paths, example `//a/b - //a/b/c`.

While the first use may not introduce problems (medial hyphen is guarded by
square brackets, i.e. `[]`), the main problem with medial hyphen in identifiers
is the ambiguity
introduced with the disjoint operator in `SdfPathExpression` (i.e. `-`).

The ambiguity is mostly resolved when dealing with absolute paths (i.e. prefixed
by `/`) and relative paths prefixed by `.` or `..`, however unclear when those
prefixes are missing.

| SdfPathExpression | Ambiguity                |
|-------------------|--------------------------|
| `a-b`             | `a-b` vs `a - b`         |
| `//a/b-c`         | `//a/b-c` vs `//a/b - c` |

This ambiguity could disappear if spaces were mandatory between expressions.
This proposal does not expect to change the current behaivor, and thus the
following ways address the problem
could be:

- By means of optionally escaping medial hyphen
- By means of optionally escaping the path pattern

It is clear that this ambiguity only applies to identifiers with medial hyphen,
thus the optionality. Solution would look like:

| Case                                       | A single path pattern | Disjoint of two path patterns |
|--------------------------------------------|-----------------------|-------------------------------|
| Escaping character (example with` \ `)     | `//a/b\-c`            | `//a/b-c`                     |
| Escaping path pattern (example with `< >`) | `<//a/b-c>`           | `<//a/b>-<c>`                 |

Although escaping with backslash is widespread, it has the problem that
backslash itself needs to be escaped, so in reality the character would look
more verbose i.e. `//a/b\\-c`.
As a result, this proposal opts for escaping the path pattern completely.

The choice of character for escaping the path pattern could be a single quote (
i.e. `'path'`) or less than/greater than (i.e. `<path>` similar to paths and
relationship targets).  
Other options as curly brackets, i.e. `{}` would collide with variants. Square
brackets, i.e. `[]` would collide with regular expressions used
in `SdfPathExpression`.

## Leading digits

Leading digits do not impose ambiguity as medial hyphen
does. `SdfPredicateExpresion` does make use of numbers, however their case is
very well delimited to arguments in functions (i.e. `SdfPredicateLibrary`) and
is strongly typed in C++.

However, the syntax may look surprising in some cases, we list some examples.

| Example  | Description                                                                             |
|----------|-----------------------------------------------------------------------------------------|
| foo - 0  | This relative expression includes path component `foo` and excludes path component `0`. |
| foo{1=2} | Variant set and variant names allow digits                                              |

This proposal opts to embrace this cases.

## Other considerations

- At the moment of writing this proposal `SdfPathExpression` does not support
  UTF-8, which constraints its usage,
  see [PrimPathWildCard](https://github.com/PixarAnimationStudios/OpenUSD/blob/release/pxr/usd/sdf/pathExpression.cpp#L752).
- [VariantName](https://github.com/PixarAnimationStudios/OpenUSD/blob/release/pxr/usd/sdf/pathParser.h#L130)
  syntax is very permisive currently. We propose this should be symetrical to
  Variant sets and Prim names.
- [PrimPathWildCard](https://github.com/PixarAnimationStudios/OpenUSD/blob/release/pxr/usd/sdf/pathExpression.cpp#L755)
  regular expression grammar is very permissive.

# Out of scope

Between the initial UTF-8 Identifiers proposal and this Extended Unicode
Identifiers proposal, readers may wonder if there will be subsequent proposals (
say Another Extension to Unicode Identifiers or Even More Extensions to Unicode
Identifiers) in the coming months. We thought through the set of symbols and
whether this proposal should include any other symbols and do not recommend
additional extensions in the near future. Few symbols had compelling use cases
for symbols other than medial hyphens. Those that did (like `/`) would introduce
too much ambiguity with other grammars core to OpenUSD. If there are use cases for
any of these symbols that warrant overriding our reasons for passing them over,
we encourage readers to call them out for further discussion.

The two given most serious consideration were `%` and `$`. `$` is considered an
optional `XID_Start` character like `_` in the Unicode Identifier specification.
However, its prevalence throughout OpenUSD for token substitution informed our
rejection of it.

Adding `%` to support percent encoding of symbols is something that we discussed
in depth. We determined that there is an expectation of idempotence and
comparison around percent encoding that we didn't think was practical to thread
through the OpenUSD core. Additionally, many tools wouldn't consider `%` to be a
valid identifier, so it likely creates more content compatibility issues than it
solves.

# Examples

An example of usage in an SDF file format for Prim Identifiers.

```usd
#sdf 1.4.32
(
    defaultPrim = "I-01234-56789"
)
def Xform "I-01234-56789"
{
    def Xform "fa392685-392b-476a-b796-13319f573a5d"
    {
    }
    def Xform "2b293787-5362-4f21-8c58-aeef8b4db667"
    {
    }
}
```

An example of usage in an USDA file format for Variants.

```usd
#usda 1.0
(
    defaultPrim = "hello"
)
def Xform "hello" (
    variants = {
        string shadingVariant = "0x008000"
    }
    prepend variantSets = "shadingVariant"
)
{
    def Sphere "world"
    {
        color3f[] primvars:displayColor
        double radius = 2
    }

    variantSet "shadingVariant" = {
        "0x0000FF" {
            over "world"
            {
                color3f[] primvars:displayColor = [(0, 0, 1)]
            }
        }

        "0x008000" {
            over "world"
            {
                color3f[] primvars:displayColor = [(0, 1, 0)]
            }
        }

        "0xFF0000" {
            over "world"
            {
                color3f[] primvars:displayColor = [(1, 0, 0)]
            }
        }
    }
}
```

An example of usage with an expression containing relative paths.

```cpp
  SdfPathExpression e("<hi-there> ../hi");
  SdfPathExpression abs = e.MakeAbsolute(SdfPath("/hello/world"));

  auto eval = MatchEval { abs };

  TF_AXIOM(eval.Match(SdfPath("/hello/world/hi-there")));
  TF_AXIOM(eval.Match(SdfPath("/hello/hi")));
```