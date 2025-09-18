# Multiple Language Support

[Discussion](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/55)

## Summary

We propose additions to USD to allow specifying the human language locale used so that content may be
localized to provide language and locale context for rendered text, speech synthesis, assistive technologies, or other
applications.

We propose use of [BCP-47](https://www.w3.org/International/core/langtags/rfc3066bis.html) specifiers according
to the [Unicode CLDR](https://cldr.unicode.org) specification, using underscores as the delimiter.

We propose specifying the language as a binding to a language catalog, and a new metadata key to signify
localizations are available.

```
def Xform "Sherrif" (
    prepend apiSchemas = ["LocalizationAPI"]
    displayName = "Sherrif"
    localized = true
) { 
    string localization:sourceLanguage = "en_US"
    rel localization:catalog = </Foo/Translations>
    string name = "There's a snake in my boot" (
        localized = true
    )
    
    def LocalizationCatalog "Translations" () {
        string sourceLanguage = "en_US"
        
        def LocalizedString "Sherrif" () {
            string identifier = "Sherrif"
            string text:fr_CA = "shérif"
            string text:hi = "शेरिफ"
        }
        
        def LocalizedString "SnakeInMyBoot" () {
            string identifier = "There's a snake in my boot"
            string text:fr_CA = "Il y a un serpent dans ma botte"
            string text:hi = "मेरे जूते में एक सांप है"
        }
    }
}
```

## Problem Statement

Today, most 3D formats assume a single unspecified language across the represented content.

However, USD is expanding into more domains than traditional 3D scene formats where the ability to localize content
opens the doors for more consumers of content.

Areas such as the following would benefit from being able to provide localized content:

1. Interactive content (games, spatial computing)
2. Education content
3. E-Commerce

A lack of langauge guidance and features in 3D formats, not just USD, makes this a much more difficult proposition.
However, we believe a few very simple changes could really open up USD content to many more people.

We would like to localize the following items as they are presented to users in user interfaces:

1. String attributes
2. Prim display names when presented in a consuming (not editing) UI like QuickLook.
3. Variant Sets and Variant identifiers

Additionally, in the future, it may be useful to localize other data types but we defer those to a later time.

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

## Existing Language Localization Formats

* [Apple:Discover String Catalogs](https://developer.apple.com/videos/play/wwdc2023/10155)
* [XLIFF](https://en.wikipedia.org/wiki/XLIFF)

## Details

### Localization Relationships

We propose the addition of a `LocalizationAPI` that would allow for various Localization style metadata.
For the purposes of this proposal, we will only focus on language but this may include other types of localization info
in the future.

This API would have two properties:

1. `string localization:sourceLanguage` that denotes the default language of this prim. Refer to the language resolution
   section for more on how this is resolved if not present.
2. `rel localization:catalog` which points to a `LocalizationCatalog` prim. The binding does inherit down a prim
   hierarchy.

Additionally, we propose adding a `localized` metadata that can apply to any UsdObject type to denote that it is
localized.

When applied to a property, it denotes that attribute is localized. While initially, we plan to only support strings,
this would also allow for localizing other attributes that are stringly typed such as asset paths e.g for localized
textures.

When applied to a Prim, it denotes that the prims displayName , as well as any Variant Sets or Variants are
localized as well. The Localized metadata does not inherit down the prim hierarchy.

### Language Catalogs

A new prim type acts as a container for multiple localizations.

A Language Catalog is inspired by the Xcode String Catalog and includes a top level sourceLanguage, and includes
multiple localizations.

In this case the container includes a single attribute `string sourceLanguage` that defines what the default
language is for any `LocalizedString` prims.

The use of a container like this allows for a runtime to quickly build up its mapping ahead of time as needed.

The Language Catalog also maps to both Xcode String Catalogs and the standard XLIFF translation format structures.
This allows for pipeline tools to quickly translate between them, and allows for future file format plugins if that
was a direction one wanted to go in.

By providing a shareable container, we also allow for multiple uses of the same string to share a single translation.

### Localized String

A new prim type encodes strings that have been localized.
By default, it must contain at least a single attribute: `string identifier`.

This identifier is what a runtime would use to match a localized attribute value or path identifier against.
The name of the prim itself is irrelevant.

It may include any number of translations in the form `string text:<locale>` which provide translations for that
locale.

For example if a runtime encounters the string "There's a snake in my boot", it can see if any `LocalizedString` prims
define the same identifier and lookup appropriate translations for it.

```
def LocalizedString "SnakeInMyBoot" () {
    string identifier = "There's a snake in my boot"
    string text:fr_CA = "Il y a un serpent dans ma botte"
    string text:hi = "मेरे जूते में एक सांप है"
}
```

Similarly, a prims  display name can be looked up against this localized string and translated for a user.

USD itself would not substitute the values for the runtime, and there should not be any overhead for systems that do
not provide localizations to the user.

## Language Semantics

### Language Resolution

In the event that a source language is not specified on a prim, we prescribe the following fallback behaviour.

1. If your prim is missing a source language, check the parent hierarchy for an inherited value.
2. If no language is specified, and if your runtime can infer a language, it is free to do so but does not have to.
3. If you cannot or choose not to infer a language, assume the user's current locale.

This matches the behaviour of common assistive technologies like screen readers.

### Language Encoding

To maximize compatibility with other systems, we recommend using `BCP-47` derived locales. For use as a `purpose`,
this would require the use of `_` as a delimiter , as opposed to the standard `-`.

e.g. Instead of `en-CA`, we use `en_CA`

This brings it closer to the derived `Unicode Common Locale Data Repository (CLDR)` standard. This is commonly used
by many operating systems, programming languages and corporations. If you are on a POSIX system, this also has
significant overlap with the POSIX locale standards ([ISO/IEC 15897](https://www.iso.org/standard/50707.html)).

An example list of languages is provided in the relevant links section above.


### Language Selection Recommendations

When the requested or desired language is not represented in the set of languages within the file, there are some
recommendations
on how a runtime can pick a fallback option.

Following the recommendations of CLDR and BCP-47, we suggest:

1. If a language is available within the set of languages, pick that attribute. e.g. `en_US` matches `text:en_US`
2. If a language isn't available, check for a more specific version of that language.
   e.g. `de_DE` matches `text:de_DE_u_co_phonebk`
3. If a more specific language isn't available, then pick a less specific purpose.
   e.g. `en_US` matches `text:en`
4. If a less specific version isn't available, take the version without any language specified.
   e.g. `en_US` matches `text`

## Common Discussion Items

### Why not Variants?

Variants are also a possible solution, however we believe that this becomes difficult for systems to work with as
variants are effectively unbounded.

We also find in some of our use cases, that we'd want variants for the core data itself, and doing language
variants per each of these variants would quickly become exponential in variant count and complexity.

Localization catalogs like this also allow for localizations to be shared across multiple instances of a string
being used. Additionally, the catalog allows for the translations to be authored independent of the primary content
while separating the two concerns.

### API Suggestions

We recommend that USD itself does not provide any translation lookup APIs.
However, we can provide convenience methods on the LocalizedString prim type to look up all available languages on it.

A runtime can then quickly find all LocalizedString items under a LocalizationCatalog, and then query LocalizedString
for any strings that have been translated. 

### Localizing Other Types

Strings presented to a user seem like the best place to start.

However in the future, creators may want to also support localizing other data types.
We think that is currently out of scope for this proposal, however, we recognize that it is a possible desire and
therefore have included the Type in the name of LocalizedString. 

Future localization types could be `Localized<Type>`, such as `LocalizedAsset` etc...

We do not recommend tackling those at this time as there are several factors involved with other types.
However, I think it should be able to scale this pattern up for localizing assets and relationships if truly needed.

### Risks

I do not see significant risk with this proposal. There is a potential for significantly more attributes,
but the number of attributes this would apply to is fairly limited.


## Excluded Topics

This API specifically does not approach other locale based data like currencies, units and Timezones.
At this time, we are not sure if those other locale based metadata have a strong use case within USD.

However, we suggest naming it something like `UsdLocaleAPI` or `UsdLocalizationAPI` such that it allows for future additions to those
types of metadata.



