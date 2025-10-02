# Bi-Directional Transcoding of Invalid Identifiers

Copyright &copy; 2023-2024, NVIDIA Corporation, version 1.0

Miguel Hernandez  
Aaron Luk  
Matthew Kuruc  

# Contents
  - [Introduction](#introduction)
  - [Requirements](#requirements)
  - [Proposed solution](#proposed-solution)
  - [Proposed API](#proposed-api)
  - [Proposed algorithm](#proposed-algorithm)
    - [Encoding procedure](#encoding-procedure)
    - [Decoding procedure](#decoding-procedure)
    - [Differences to Punycode](#differences-to-punycode)
  - [Examples](#examples)

# Introduction

Users of OpenUSD in non-English speaking regions and users in a variety of domains (mechanical, manufacturing, electrical,
automotive, etc.) desire the ability to name OpenUSD primitives with identifiers that are not allowable by the specification.  

Previously, OpenUSD specification only allowed for prim names and other identifiers to be:
- Non-empty strings.
- Start with an alpha character `[A-Za-z]` or underscore.
- Only be composed of characters in the set of `[A-Za-z0-9_]`.

This is fixed in OpenUSD 24.03, however the following are still not allowed:
- Characters that are part of the lexical structure such as whitespace or newline.
- Only numeric identifiers or identifiers starting with a numeric character.
- Set of characters that are disallowed in identifiers with syntactic use, such as arithmetic operators.
- SdfPath separators as forward slash (`/`), curly brackets (`{}`), square brackets (`[]`), etc. 

`TfMakeValidIdentifier`, was used in OpenUSD to convert any identifier into a valid identifier. However, it creates a 
non-bidirectional relationship, for example, something like `カーテンウォール` would be transformed into `________________`. 
It is easy to see many strings colliding.

The objective of this proposal is to provide an alternative to `TfMakeValidIdentifier` that can take any identifier 
(potentially with invalid characters) and transform it into a OpenUSD valid identifier. The process must be reversible, 
unique, and easily identifiable. 

We address the problems presented above with transcoding. Transcoding is the translation from one domain 
(illegal characters) to another domain (legal characters), this translation allows a lightweight shim between 
applications and OpenUSD data to preserve identifiers.

# Requirements

A real bijective function would let us convert any UTF-8 token into a valid identifier and vice versa. In general, 
such function should have the following features:
- **Completeness**: Every UTF-8 string can be represented by an encoded string.
- **Uniqueness**: There is at most one encoded string that represents an original UTF-8 string.
- **Reversibility**: Any UTF-8 string mapped to an encoded string can be recovered from that string.
- **Efficient encoding**: The ratio of encoded  string length to UTF-8 string length is small.
- **Simplicity**: The encoding and decoding algorithms are reasonably simple to implement.

# Proposed solution

Defined in [RFC-3492](https://datatracker.ietf.org/doc/html/rfc3492), we find PunyCode. PunyCode is a specialization
of Bootstring algorithms. Bootstring would perform better than base encodings and url encodings. 

However, a basic Punycode implementation have an initial limitations for OpenUSD.
- Punycode (and Bootstring in general), involves an initial basic code segregation. In the definition of Punycode, 
basic codes are all ASCII characters whose value is less than or equal to the parameter `initial_n`. For example, 
`--> $1.00 <--` will be converted to `--> $1.00 <--` in Punycode (i.e., no change), however this identifier is 
invalid. An implementation of Punycode (or another Bootstring algorithm) would require a specific `IsBasicCode` function to 
account for this, also adapting different steps in the algorithm to account for the situation where `initial_n` is 
non existent (i.e. 0).
- Another less impactful problem with Punycode (but not with Bootstring), is the way the extended code characters 
are encoded/decoded. To encode, Punycode uses base 36 encoding by default. This is due to the fact that upper case and
lower case are considered the same. We could lift this limitation and use less memory when encoding. 
- Finally, just as other encodings, special care must be taken to address leading digits. In the case of Punycode, 
we can treat any leading digits as extended codes and add them after the delimiter.

These concerns can be addressed with a custom implementation of Bootstring. This strategy has the following advantages:
- **Efficiency**, 100% for basic code characters, at worst 72% for extended code characters. This is because variable 
length encoding is way more efficient than simple bit shifting encoding (i.e. base 62).
- **Readability**, a valid identifier will be encoded without any change, i.e. `hello` will be encoded to `hello`; 
non-valid identifiers consisting mostly of valid characters will be partially encoded, i.e. `hello world` will be 
encoded to `tn__helloworld_lA`, i.e. only the space is encoded; and only non-valid identifiers consisting mostly 
of invalid characters will be non-readable, i.e. `->$.<-` will be encoded to `tn__a0I26g1D`. 
This is improved over other encoding methods, i.e. base62, where every case is obfuscated.
- **Querying**, for basic code characters, querying is the same as before.

Disadvantages:
- **Querying**, unfortunately encoding the search term and doing character comparison will not work as this is not a 
byte-aligned encoding.This will require all paths to be decoded as they are traversed.
- **Prefix**, to give a hint of transcoding we add a prefix `tn__`, in similar fashion to `xn--` in Punycode. 
For short identifiers this may represent a big overhead, and it could potentially collide with identifiers starting 
with `tn__` for reasons other than a hint for decoding.

# Proposed API

As the Bootstring implementation is reversible, we can add now a function to reverse the transcoding (i.e. decode). 
For a proposed API we expect to have three functions: 

* `std::optional<std::string> SdfBoostringEncodeAsciiIdentifier(const std::string&)`
  * Transform any valid UTF-8 string into a valid OpenUSD identifier using the character set `[A-Za-z0-9_]`. 
  Mostly used for  backwards compatibility (OpenUSD less than 24.03). Invalid UTF-8 strings (i.e. strings with 
  invalid UTF-8 code points) will return no value, we rely on `TfUtf8CodePoint` for the implementation.

* `std::optional<std::string> SdfBoostringEncodeIdentifier(const std::string&)`
  + Transform any valid UTF-8 string into a valid OpenUSD XID identifier. Mostly used for OpenUSD 24.03 and higher. 
  Invalid UTF-8 strings (i.e. strings with invalid UTF-8 code points) will return no value, we rely on 
  `TfUtf8CodePoint` for the implementation.

* `std::optional<std::string> SdfBootstringDecodeIdentifier(const std::string&)`
  * Transform the results of either `SdfBoostringEncodeAsciiIdentifier` or `SdfBoostringEncodeIdentifier` into the 
  original valid UTF-8 string. Decoding invalid encoded identifiers will return no value.

# Proposed algorithm

The algorithm is a generalization of Punycode, known as bootstring. There are references to how the algorithm 
work in the [RFC-3492](https://datatracker.ietf.org/doc/html/rfc3492), the following document summarize it and 
may offer a more friendly explanation of the concepts.

## Encoding procedure

### Separation of basic codes

In general, in the Bootstring algorithm we need to differentiate between basic codes and extended codes:
- **Basic codes** are known a priori and are the valid codes supported in our application domain. 
- **Extended codes** are every other code which is not in the basic code set.

For example, in OpenUSD versions prior to 24.03, the basic codes would be compromised of the characters `[A-Za-z0-9_]` 
whereas from 24.03, the basic codes will make up to the Unicode XID specification.

The first step in encoding is separating the basic codes from the extended codes. The basic codes will be copied 
directly to the string, since they already belong to the domain of valid characters and will not cause any problem.
If no extended code exists, then the algorithm finishes here.

| Identifier        | Group    | Value         |
|-------------------|----------|---------------|
| `012-345-678/9.0` | Basic    | `01234567890` |
|                   | Extended | `--/.`        |

### Encoding of extended codes

If there are extended codes, we start by appending a delimiter character. A delimiter character is a character
which belongs to the set of basic codes and help to differentiate between basic and extended codes. 
The original specification uses dash (`-`), however in our implementation we will use underscore (`_`).

| Prefix | Basic codes   | Delimiter | Suffix              |
|--------|---------------|-----------|---------------------|
| `tn__` | `01234567890` | `_`       | `ENCODING_OF(--/.)` |


We then use the following:

#### Delta encoding

Delta encoding is the process of encoding differences of values, instead of encoding directly the values. In transcoding
this is useful as it exploits the fact that `UTF-8` characters of the same language appear close to each other.
For example for japanese, Hiragana syllabary appears from `0x3040` to `0x309f` while Katakana appears from `0x30a0` to `0x30ff`.
This helps to reduce the number of encoded bytes.

| Characters sorted | Value to encode                            |
|-------------------|--------------------------------------------|
| `-`               | 45                                         |
| `-`               | 0 (UTF-8 value 45, same as previous)       |
| `.`               | 1 (UTF-8 value 46, one more than previous) |
| `/`               | 1 (UTF-8 value 47, one more than previous) |


One difference in this implementation is that delta encoding starts at character `0`. In Punycode, 
all ASCII characters are valid, as such delta encoding start with value `128`. However, this is not true in OpenUSD 
where we still have invalid ASCII codes.

#### Variable length integer encoding

Variable length integer encoding allow us to concatenate integers without having to mark the limits between each of them. 
`UTF-8` itself is an example of a variable length encoding. We know the last digit (and the beginning of a new one) when
we hit a threshold.

| 0             | 1             | 2                                                     | 3             | 4   |
|---------------|---------------|-------------------------------------------------------|---------------|-----|
| D<sub>0</sub> | D<sub>1</sub> | D<sub>2</sub>                                         | D<sub>0</sub> | ... |
| T<sub>0</sub> | T<sub>1</sub> | T<sub>2</sub>                                         | T<sub>0</sub> | ... |
|               |               | D<sub>2</sub> < T<sub>2</sub>, <br/>new number starts |               |     |


#### Mixed radix representation

Above encodings let us represent single numbers, however we intend to store both the extended code and its position. 
Although we could store a sequence of two integers, that would expand our encoding representation. Another way is to represent
the extended code and position as a single number using mixed radix. 

|               | 0 | ... | i                             | ... | N -1 |
|---------------|---|-----|-------------------------------|-----|------|
|               |   |     |                               |     |      |
| V<sub>j</sub> |   |     | value = V<sub>j</sub> * N + i |     |      |
|               |   |     |                               |     |      |

Thus, the extended code (V<sub>j</sub>) and the position (i) can be extracted as (_floor(value / N)_) and (_value % N_) 
respectively.

## Decoding procedure

`TfMakeValidIdentifier` had no reverse function, it was not possible. Since our function is bijective we can create 
a decoding mechanism for the proposed solution.

The decoding procedure follows the reverse process:
- Remove prefix.
- Copy the basic codes.
- For the extended codes (i.e. encoding section):
  - Let `value` be the variable length integer read.
  - Increase code value `code` by `value / N` (due to delta encoding).
  - Let position `pos` be `value % N`.
  - Insert code value `code` at position `pos`.
  - Increase N.

It is important to notice that whereas the proposed encoding could generate different values depending on what 
character set is considered (i.e. ASCII vs UTF-8 XID), decoding is agnostic to the character set and will always result
into the original string.

## Differences to Punycode

A summary of the differences against Punycode are:
- The separating character changes from `-` to `_`. Since `-` is invalid character in OpenUSD.
- Delta encoding starts from `0` instead of `128`. This is to account the fact not all ASCII's are allowed in OpenUSD.
- The base representation changes from `36` in Punycode to `62` in this implementation (to represent more information
in less characters).
- Threshold is constant in this implementation. There is no loss of performance or memory representation, since our 
`base` is also increased, and simplifies implementation.

# Examples

The above example:

| Original        | Transcoding           |
|-----------------|-----------------------|
| 012-345-678/9.0 | tn__01234567890_lG7QQ |

```cpp
static_assert(
    SdfBoostringEncodeIdentifier("012-345-678/9.0") == "tn__01234567890_lG7QQ"
);
static_assert(
    SdfBootstringDecodeIdentifier("tn__01234567890_lG7QQ") == "012-345-678/9.0"
);
```

Encoding valid identifiers produces no changes.

| Original      | Transcoding   |
|---------------|---------------|
| id12345_abcde | id12345_abcde |

```cpp
static_assert(
    SdfBoostringEncodeIdentifier("id12345_abcde") == "id12345_abcde"
);
static_assert(
    SdfBootstringDecodeIdentifier("id12345_abcde") == "id12345_abcde"
);
```

An encoded identifier is already a valid identifier, and it will result in itself.

| Original              | Transcoding           |
|-----------------------|-----------------------|
| tn__01234567890_lG7QQ | tn__01234567890_lG7QQ |

```cpp
static_assert(
    SdfBoostringEncodeIdentifier("tn__01234567890_lG7QQ") == "tn__01234567890_lG7QQ"
);
```

Existing valid identifiers with `tn__` prefix will produce no changes.

| Original           | Transcoding        |
|--------------------|--------------------|
| tn__mycoolstring   | tn__mycoolstring   |
| tn__my_cool_string | tn__my_cool_string |

```cpp
static_assert(
    SdfBoostringEncodeIdentifier("tn__mycoolstring") == "tn__mycoolstring"
);
static_assert(
    SdfBoostringEncodeIdentifier("tn__my_cool_string") == "tn__my_cool_string"
);
```

Remove invalid characters. The extended characters is `-` and `/`.

| Original    | Transcoding       |
|-------------|-------------------|
| 123-456/555 | tn__123456555_oDT |

```cpp
static_assert(
    SdfBoostringEncodeIdentifier("123-456/555") == "tn__123456555_oDT"
);
static_assert(
    SdfBootstringDecodeIdentifier("tn__123456555_oDT") == "123-456/555"
);
```

Convert UTF-8 characters to valid ASCII (i.e. `TfMakeValidIdentifier`). This can be useful to share identifiers
between new versions of OpenUSD and legacy versions. The extended character set is `ü`, `,` and ` `(space).

| Original         | Transcoding               |
|------------------|---------------------------|
| München, Germany | tn__MnchenGermany_pDV5hi2 |


```cpp
static_assert(
    SdfBoostringEncodeAsciiIdentifier("München, Germany") == "tn__MnchenGermany_pDV5hi2"
);
static_assert(
    SdfBootstringDecodeIdentifier("tn__MnchenGermany_pDV5hi2") == "München, Germany"
);
```

Convert UTF-8 characters to valid XID. The extended character set is, `,` and ` `(space). Notice how the decoding 
function is the same as above (i.e. `SdfBootstringDecodeIdentifier`).

| Original         | Transcoding             |
|------------------|-------------------------|
| München, Germany | tn__MünchenGermany_rEi5 |


```cpp
static_assert(
    SdfBoostringEncodeIdentifier("München, Germany") == "tn__MünchenGermany_rEi5"
);
static_assert(
    SdfBootstringDecodeIdentifier("tn__MünchenGermany_rEi5") == "München, Germany"
);
```

Encoding invalid UTF-8 strings will generate no value.

```cpp
static_assert(
    SdfBootstringDecodeIdentifier(generateInvalidUTF8()) == std::optional<std::string>{}
);
```

Decoding invalid identifiers will generate no value.

```cpp
static_assert(
    SdfBootstringDecodeIdentifier("tn__///abc") == std::optional<std::string>{}
);
static_assert(
    SdfBootstringDecodeIdentifier("tn__my_cool_string") == std::optional<std::string>{}
);
```
