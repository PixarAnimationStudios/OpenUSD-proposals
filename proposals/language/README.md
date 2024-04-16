# Multiple Language Support

[Discussion](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/55)

## Summary

We propose additions to USD to allow specifying the human language locale used so that content may be
localized to provide language and locale context for rendered text, speech synthesis, assistive technologies, or other applications.

We propose use of [BCP-47](https://www.w3.org/International/core/langtags/rfc3066bis.html) specifiers according
to the [Unicode CLDR](https://cldr.unicode.org) specification, using underscores as the delimiter.

We propose specifying the language as metadata on prims as well as a purpose on attributes.

```
def Foo(
    prepend apiSchemas = ["LocaleAPI"]
    language = "en_US"
) { 
    string text = "There's a snake in my boot"
    string text:fr_CA = "Il y a un serpent dans ma botte"
    string text:hi = "मेरे जूते में एक सांप है"
}
```

## Problem Statement

Today, most 3D formats assume a single unspecified language across the represented content.

A few changes and upcoming changes to USD increase the need to specify language:

1. With Unicode support in USD, it is more attractive to people in a wider range of locales.
2. Upcoming text support feels like a natural area for representing content in different locales
3. USD is now used as part of interactive content (games, spatial computing), where
   localization for user playback and assistive technologies may be useful.

Since there is no language specification, it is unclear for tooling and users how content should be interpreted
when used by language-aware technologies.

## Glossary of Terms

- **[BCP-47](https://www.w3.org/International/core/langtags/rfc3066bis.html)** : An IETF specification
  for language representation that are commonly used by web standards and assistive technologies.
  You may be familiar with these when you visit websites that have sections marked `en-CA` or `fr` in the URL
- **[Unicode CLDR](https://cldr.unicode.org)** : The Unicode expression of the BCP-47 identifiers
- **Language** : The primary language. Can be subdivided further. Lowercase is recommended.
  e.g `en` for English and `fr` for French.
- **Scripts** : An optional subdivision of Language for representation of a language in different written form.
  Title case is recommended. For example, `az-Cyrl` for Azerbaijani in the Cyrillic script
- **Region/Territories** : An optional subdivision of Language for different regions that may share the same core
  language. Uppercase is recommended. For example, `en_CA` for Canadian English

## Relevant Links

* [W3C: Choosing Language Tags](https://www.w3.org/International/questions/qa-choosing-language-tags)
* [Unicode CLDR: Picking the Right Language Identifier](https://cldr.unicode.org/index/cldr-spec/picking-the-right-language-code)
* [W3C: Language Tags and Local Identifiers for the World Wide Web](https://www.w3.org/TR/ltli/)
* [Unicode: Language Tag Equivalences](https://cldr.unicode.org/index/cldr-spec/language-tag-equivalences)
* [Common list of Locales](https://gist.github.com/typpo/b2b828a35e683b9bf8db91b5404f1bd1)
* [Apple: Choosing localization regions and Scripts](https://developer.apple.com/documentation/xcode/choosing-localization-regions-and-scripts)

## Details

### What would use it?

This addition to USD is designed to be generic over several other schema types that might benefit from it.

The primary use case is the
current [Text proposal from Autodesk](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/text)
, where text is a really good pairing for language specification.

Hypothetically, in the future, we could see it also being useful for other use cases like:

- User facing assistive metadata
- Texture
- Geometry

We do not expect these to support languages right away, but we believe this is a good future looking feature that
would allow for the use of USD in specific multi-language pipelines.

For this proposal, we do not require that other schemas explicitly adopt language support. We suggest that this is
something that can be adopted in runtimes over time to support in conjunction with other schemas.

### Language Encoding

To maximize compatibility with other systems, we recommend using `BCP-47` derived locales. For use as a `purpose`,
this would require the use of `_` as a delimiter , as opposed to the standard `-`.

e.g. Instead of `en-CA`, we use `en_CA`

This brings it closer to the derived `Unicode Common Locale Data Repository (CLDR)` standard. This is commonly used
by many operating systems, programming languages and corporations. If you are on a POSIX system, this also has
significant overlap with the POSIX locale standards ([ISO/IEC 15897](https://www.iso.org/standard/50707.html)).

An example list of languages is provided in the relevant links section above.

### Unspecified Language Fallback

In the event that a language is not specified, it is recommended to specify a fallback behaviour.

Our recommendation is:

1. If your attribute or prim is missing a language, check the parent hierarchy for an inherited value
2. If no language is specified, and if your runtime can infer a language, it is free to do so but does not have to.
3. If you cannot or chose not to infer a language, assume the users current locale.

This matches the behaviour of common assistive technologies like screen readers.

### Default Metadata

Most content will prescribe to one primary language, which tends to be the region of the content creator.
To facilitate this, we encourage but do not require content authors to specify a language.

As is the current convention, layer metadata is used for stage level hints. However the
[Revise Use of Layer Metadata proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/45)
suggests moving this to an applied API Schema.

If we assume current conventions of a layer metadata, we recommend the following field.

```
#usda 1.0
(
    language = "en_CA"
)
```

However, per the new proposal this should move to an API schema, and we'd propose the following

```
def Foo(
    prepend apiSchemas = ["LocaleAPI"]
    language = "en_CA"
) { ... }
```

In both scenarios, the language is inherited as the default value for every prim and attribute below it.

### Attribute Purposes

We take inspiration from web and application development conventions, where it is common to provide resources
for multiple languages in a single context.

For this we recommend that languages specification be a purpose on the attribute rather than having a single
attribute language.

Our recommendation is for this to be the last token in the attribute namespaces to work towards the most specific.

```
def foo {
     string text = "Colours are awesome"
     string text:en_us = "Colors are awesome, but the letter U is not"
     string text:fr = "La couleur est géniale"
}
```

One advantage of this system is that you can have your translations in different layer files and referenced it in.

It would be recommended that at least one version of the attribute exclude the language token, so that it can 
fallback to the inherited language and also be used as the fallback if a user asks for a language that has no matching
languages available.

#### Token Delimiter

The proposal currently implicitly uses the last token as the language.
It might however be preferable to be explicit about this by also prefixing `lang_` or `lang:` to the last token.

This could look like one of the below

```
string text:lang_en_us
string text:lang:en_us
```

This perhaps makes things longer, but does make it easier to discern that a token represents a language in a wider
range of use cases. 

#### Why not Variants?

Variants are also a possible solution, however we believe that this becomes difficult for systems to work with as
variants are effectively unbounded.

We also find in some of our use cases, that we'd want variants for the core data itself, and doing language
variants per each of these variants would quickly become exponential in variant count and complexity.

Purposes on attributes feel like the best match to existing paradigms in the web and app development, and easiest for
systems to work with.

### API Suggestions

We do not recommend that OpenUSD itself include all possible language tags. However, it would be beneficial for USD
to provide API to lookup languages specified in the file.

This could look like the following behaviour where it returns a map of Language and attribute.

```
std::map<TfToken, UsdAttribute> UsdLocaleAPI::GetLanguagePurposes(const UsdPrim& prim, TfToken attributeName) {...}
```

Using the example above, a call to `GetLanguagePurposes(foo, "text")` would give

- (`<Fallback or Unknown>`, foo:text)
- (en_US, foo:text:en_US)
- (fr, foo:fr)

In this case, the `<Fallback or Unknown>` represents that it should follow the logic 
in the `Unspecified Language Fallback` section.

I would suggest another function like

```
TfToken UsdLocaleAPI::GetFallbackLanguage(const UsdPrim& prim)
```

That would return either the inherited value or a sentinel `Unknown` value when no language is specified.
Perhaps USD could have some convenience function to do user locale lookup, but I do not think that needs to be a
requirement.

#### Language Selection Recommendations

When the requested or desired language is not represented in the set of languages within the file, there are some recommendations
on how a runtime can pick a fallback option.

Following the recommendations of CLDR and BCP-47, we suggest:

1. If a language is available within the set of languages, pick that attribute. e.g. `en_US` matches `text:en_US`
2. If a language isn't available, check for a more specific version of that language.
   e.g. `de_DE` matches `text:de_DE_u_co_phonebk`
3. If a more specific language isn't available, then pick a less specific purpose.
   e.g. `en_US` matches `text:en`
4. If a less specific version isn't available, take the version without any language specified.
   e.g. `en_US` matches `text`

## Risks

I do not see significant risk with this proposal. There is a potential for significantly more attributes,
but the number of attributes this would apply to is fairly limited.

One potential issue is that you may want to swap out geometry or assigned textures by locale too.
e.g An English texture vs a French texture. This proposal would allow for that, but the risk is
that support may be very renderer dependent.

## Excluded Topics

This API specifically does not approach other locale based data like currencies, units and Timezones.
At this time, we are not sure if those other locale based metadata have a strong use case within USD.

However, we suggest naming it something like `UsdLocaleAPI` such that it allows for future additions to those
types of metadata.



