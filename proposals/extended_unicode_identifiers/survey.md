# Survey of Object, Prim, and Node Names
Copyright &copy; 2024, NVIDIA Corporation

## Overview
This document looks at four scene formats and what restrictions
are placed on object names.

This document considers node, object, group, and prim to be
roughly equivalent. This survey does not dive into property
and blind data naming. While some of the mappings to prim
names are taken from file format plugins, this doesn't mean that
file format plugins are the only way to associate
scene representations.

## Summary
### Specification
✅ = allowed ❌ = not allowed
| Format                             | glTF | OBJ | IFC | JT  |
|------------------------------------|------|-----|-----|-----|
| Any String                         | ✅   | ❌ | ✅  | ✅ |
| Leading Digits                     | ✅   | ✅ | ✅  | ✅ |
| Only Digits                        | ✅   | ✅ | ✅  | ✅ |
| Medial Hyphens                     | ✅   | ❌ | ✅  | ✅ |

### Observed in Sample Data
glTF and IFC have example asset repositories. We didn't survey 
OBJ sample data and only looked at a handful of examples from
JT release blogs and marketing.

✅ = observed ❌ = not allowed ❓ = not observed
| Format                             | glTF       | OBJ | IFC | JT    |
|------------------------------------|------------|-----|-----|-------|
| Whitespace                         | ✅        | ❌  | ✅ | ✅    |
| Leading Digits                     | ✅        | ❓   | ✅ |  ✅   |
| Only Digits                        | ❓         | ❓  | ✅ | ❓    |
| Medial Hyphens `-`                 | ✅        | ❌  | ✅ | ✅   |
| Periods `.`                        | ✅        | ❌  | ✅ | ❓   |
| Parenthesis `(`, `)`               | ✅        | ❌  | ✅ | ✅   |
| Other Symbols                      | `+`, `%`  | ❌  | ❓ | `/`, `;` |

## Analysis
The extended identifier proposal aims to reduce transformations 
required of node names to represent scenes in OpenUSD. This analysis
is broken down into what's currently proposed (leading digits and medial hyphens), what's common but not proposed, and other observed
symbols.
### Leading Digits, Only Digits, and Medial Hyphens (Proposed)
Three of the four surveyed allowed arbitrary strings as node identifiers. These
formats commonly leveraged leading digits and medial hyphens in sample
data. Leading digits were more common in IFC and
JT than in glTF.

The only format (OBJ) that did not allow arbitrary strings still 
allowed leading digit and digit only identifiers.

Leading digits and hyphens were used in identifying part numbers.
Digit only identifiers were observed as well in sample IFC data, 
where they may refer to numbered rooms or objects.

Allowing leading digits and medial hyphens would
reduce the number of scenes and nodes in the surveyed assets
that would require a form of transcoding or conversion to have
an associated OpenUSD representation.

Constraining identifiers so that digit only names aren't allowed
would still allow part numbers to be robustly supported but digit
only names are common enough that we don't recommend adding this
constraint.

#### Medial, Continue, or "Nonleading and Nontrailing" Hyphens?
The Unicode identifier specification specifies that medial characters
can't be neighboring. You can't have `a--b` or `a---b` for example.
As proposed, hyphens must be medial. Neighboring hyphens were
observed in the test data, but often with other unsupported characters
and whitespace. Medial is sufficient for many part numbers and
nodes.

Adding `-` to Continue would increase the number of ambiguous cases
with path expressions. Trailing hyphens were not observed in the
sample data.

Some other [naming rules](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#name) are more flexible,
simply constraining against leading and trailing hyphens. It
may be worth considering diverging from the Unicode identifier 
rules.

### Whitespace, Periods, and Parenthesis (Not Proposed)
Whitespace, periods, and parenthesis were observed in many of the surveyed examples as well. Parenthesis were not observed without
whitespace. Periods were commonly used when their usage held semantic
meaning. (ie. A node had an embedded version number or was referencing
a paricular index of refraction.)

It's our expectation that whitespace and periods are 
not viable to support without introducing an escaping or
other encoding mechanism into the path grammar.

### Other Symbols (Not Proposed)
Other symbols or patterns occured, but without common frequency
to warrant recommendation. Notably, just having two symbols `-` and `_` affords
users with more flexibility when generating valid names. (ie.
replace invalid symbols with `-` and replace whitespace with `_`).

## Format Appendix
This section provides reference links that inform the above
analysis.
### GLTF
#### Overview
* https://en.wikipedia.org/wiki/GlTF

#### Object naming
* https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#indices-and-names
* https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#json-encoding

Names may be any Unicode string and are not guaranteed to be unique.

#### Mapping to OpenUSD
* https://github.com/adobe/USD-Fileformat-plugins/blob/4045f510cfae94e06ed7964e0877f3a6d4fdf542/gltf/src/gltfImport.cpp#L842

The Adobe glTF file format plugin tries to use the name of the node.

#### Sample Assets
Medial hyphens were commonly observed in sample data (leading
digits, less so).

Whitespace and periods (`.`) were commonly observed, though mostly in test data where `IOR2.2` (for example) might be used in node names.

Less commonly observed symbols observed were `+`, `(`, `)`, and `%`, generally in concert with white space.

* https://github.com/KhronosGroup/glTF-Sample-Assets/blob/754a32a333b27698b6c36d8bec8ff7ed5f729538/Models/Avocado/glTF/Avocado.gltf
* https://github.com/KhronosGroup/glTF-Sample-Assets/blob/754a32a333b27698b6c36d8bec8ff7ed5f729538/Models/BrainStem/glTF/BrainStem.gltf#L1066
* https://github.com/KhronosGroup/glTF-Sample-Assets/blob/754a32a333b27698b6c36d8bec8ff7ed5f729538/Models/CompareAnisotropy/glTF/CompareAnisotropy.gltf#L386
* https://github.com/KhronosGroup/glTF-Sample-Assets/blob/754a32a333b27698b6c36d8bec8ff7ed5f729538/Models/EnvironmentTest/glTF/EnvironmentTest.gltf#L124
* https://github.com/KhronosGroup/glTF-Sample-Assets/blob/754a32a333b27698b6c36d8bec8ff7ed5f729538/Models/GlassHurricaneCandleHolder/glTF/GlassHurricaneCandleHolder.gltf#L23
* https://github.com/KhronosGroup/glTF-Sample-Assets/blob/754a32a333b27698b6c36d8bec8ff7ed5f729538/Models/ChairDamaskPurplegold/glTF/ChairDamaskPurplegold.gltf#L45

### OBJ
#### Overview
* https://en.wikipedia.org/wiki/Wavefront_.obj_file

#### Object Naming
* https://www.martinreddy.net/gfx/3d/OBJ.spec

Optional but constrained to letters, numbers, and combinations of letters and numbers by specification.

#### Mapping to OpenUSD
* https://github.com/PixarAnimationStudios/OpenUSD/blob/59992d2178afcebd89273759f2bddfe730e59aa8/extras/usd/examples/usdObj/translator.cpp#L67

#### Sample Assets
Sample assets were not explored during this survey.

### IFC
#### Overview
* https://en.wikipedia.org/wiki/Industry_Foundation_Classes

#### Object Naming
* https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/concepts/Object_Attributes/Object_User_Identity/content.html
* https://technical.buildingsmart.org/resources/ifcimplementationguidance/string-encoding/

Name uniqueness is recommended but not guaranteed. While not currently
UTF-8, the docs say that's on the roadmap.

#### Mapping to OpenUSD
This has not been thoroughly vetted, but the name field mentioned is 
likely the best way to map IFC nodes to OpenUSD prims.

IFC also have unique identifiers which could be a candidate for
name as well, but that would still require leading digits.

#### Sample Assets
* https://github.com/buildingSMART/Sample-Test-Files

IFC was the format where digit only names were most commonly observed.
It notes in its documentation that room number is a common use case.

### JT
#### Overview
* https://en.wikipedia.org/wiki/JT_(visualization_format)

#### Sample Assets

JT was not as thoroughly explored as other formats. The referenced 
sample is from a release announcement blog.

* https://blogs.sw.siemens.com/jt-open/jt2go-desktop-has-a-new-release/
* https://blogs.sw.siemens.com/jt-open/updates-to-jt2go-for-windows-desktop-now-available/