# Profiles

This document proposes the addition of `profiles` as metadata to USD documents.
Profiles are short, structured descriptions of potentially non-standard features
used within the stage such that a runtime or human can know of their existence ahead of time.

Profiles are not meant to change runtime parsing behaviour, and are essentially just
informational hints.

A proposed example would be:

```
(
    profile = {
        string name = "org.openusd.core"
        string version = "1.2.3"
        dictionary compatibility = {
            string com.apple.realitykit = "4.3.2"
        }
        dictionary required = {
            dictionary fileFormats = {
                string org.aom.vvm = "1.0.0"
            }
        }
        dictionary optional = {
            dictionary schemas = {
                string com.apple.realitykit.components = "1.0.0"
            }
        }
    }
)
```

## Problem Statement

USD documents can be pretty wide in terms of the features supported such as custom schemas, textures, audio or geometry
formats. Some of these are important to be
represented, while others are not meant to be portable.

This makes it difficult for an application runtime to know what it should let a user
know about, when it can't represent something. It also means that the application
needs to analyze every element before telling the user something may be amiss.

Conversely, USDZ packages focus on portability and are much stricter about the resource types
they may include (though it omits the same rigidity for schemas).
However, this strictness can also prevent the use of new features until they've
been standardized. While this is great for inter-ecosystem sharing, it can be an
issue for use within more limited scopes.

Profiles aim to solve this by providing metadata so that USD documents and packages
may express what non-standard features they use. This would allow runtimes to flag
concerns to a user faster for unsupported features, and allow USDZ documents to use
features prior to standardization.

## Glossary

N/A

## Details

We propose the addition of a dictionary metadata that stores a structured mapping
of profile identifiers to their corresponding versions.

### Profile Identifiers

We suggest that profiles identify themselves with
a [Reverse Domain Name Notation](https://en.wikipedia.org/wiki/Reverse_domain_name_notation)**.

This is a very standard registration type across multiple systems, and has the
advantage of allowing namespacing, while reducing the risk of name squatting.

E.g `com.apple.text.preliminary` would allow pointing to the use of a preliminary
text schema, that is attributed to Apple. This would allow disambiguation with
something like `com.autodesk.text.preliminary` if Autodesk would want to release
a preliminary version of their schema too.

While there should be other forms of delineation within the schema, and potentially its name, this allows the
application runtime to alert the user before traversing
the scene and running heuristics.

It also allows the application to direct the user to the relevant developers site
where they can ask for more information.

Lastly, it also prevents name collisions.
For example, in the future, [aswf.com](https://www.aswf.com) may want to make schemas for window
film parameters. This would then conflict with [aswf.io](https://www.aswf.io)'s schemas.
Treating the domain identifier as ownership has proven to be quite resilient.

#### Why not a URL?

It may be preferable to some to use a URL like `https://www.openusd.org/profiles/core/v1.2.3`.

However, this has been problematic in past systems where URL's bitrot, and require
that everyone align on one website structure, or that runtimes have many parsers.

A standardized reverse domain name notation is therefore considered a good middleg round.
Users may still have to search for the specific feature, but they'll
at least know who to ask.

### Profile Versioning

We propose that versions of profiles use [semantic versioning](https://semver.org)
compatible strings. We recognize that many projects, including OpenUSD, do not use
semver. However, there is benefit in using a string that can be parsed by
semver parsers even if the semantic meanings of the tokens aren't the same.

For example, one application may support a specific version of an extension but not older or newer versions of it.

### Profile Augmentation

Our proposal for profiles includes the concept of a base profile and augmentations
beyond that.

The base profile should be a well known base level understanding of what features are
standardized under it.

For example, `org.openusd.core = 0.25.8` to represent a core profile of USD that
aligns with OpenUSD 25.8.

Features beyond this base profile may be specified as well in a similar way,
augmenting it. Therefore, profiles are always additive.

`com.apple.realitykit.components = 1.2.3` could augment the base profile, as one
example.

### Dictionary Overview

We propose the dictionary have the following top level keys:

- **name** : The identifier of the base profile
- **version** : The version of the base profile

Beyond that, there are sub-dictionaries of augmentations. Each of these two are
further subdivided into categories as described in the next section:

- **required** : A set of profile augmentations that are
  required to present this USD stage. For example, if using geometry compressed
  file format plugins, the stage would not represent in a usable form without
  their availability.

- **optional** : A set of profile augmentations that are
  not required to portably represent this stage. For example, Reality Kit or other
  runtimes may include many runtime specific schemas for behaviour etc... which
  are not expected to be used by a DCC.

Finally, it may also be beneficial to share what versions of runtimes the document
has been intended for or tested with. This is a mapping of identifiers to
their versions.

- **compatibility** : A map of which versions of a DCC or runtime the document has
  been tested for or is intended to be used with. e.g `com.sidefx.houdini = "12.4""`.
  These should not be used to prevent loading of the file in mismatched versions, but
  provide a standardized way to warn a user if compatibility might be an issue.

### Augmentation Dictionary Categories

Both the required and optional augmentation dictionaries are further subdivided
into categories.

Categories help organize the augmentations into their respective domains.
This further allows a runtime to decide what to present to a user.

For example,a runtime that is not rendering need not bother with augmentations
that are meant for visualization.

Additionally, this allows for better, standardized reporting structures to users
in whatever manner the runtime or app chooses. e.g Maya and Blender would inherently
have different UIs, but wouldn't have to necessarily provide their own categorization.

We propose the following categories:

- **imaging** : features that a renderer would need to support this document.
  For example, Gaussian Splat rendering `com.adobe.splats`.
- **fileFormats** : data plugins that are needed to be read by USD to recreate a hierarchy. e.g `org.aswf.materialx`
- **assetFormats** : Asset formats for textures or audio that may be required.
  e.g `org.aswf.vdb`
- **schemas** : Schemas that may be required for correct parsing of this scene.
  e.g `com.apple.realitykit.components`
- **features** : A list of USD features that may not be supported by a given runtime.
  e.g a USD file may use relocates, but an older runtime won’t understand them even
  if it can parse them. e.g `org.openusd.relocates`
- **general** : Extensions that don’t fit in a predetermined category

## Profiles vs Extensions

Other formats like glTF have extension facilities as described
in [glTF 2.0 Extension Registry](https://github.com/KhronosGroup/glTF/blob/main/extensions/README.md).

Unlike extensions, profiles (as described here) do not add new functionality.
Instead, profiles are a complement to OpenUSD's existing extension system by allowing
up front declaration of which extensions are in use.

Profiles are intended to have no runtime side effects beyond their declaration.

## Runtime Analysis

A concern about profiles is that they are just hints, and are taken at face value.

The real truth is of course always in the actual data stored, whether thats the schemas or asset formats used.

However, this requires runtimes to analyze everything in the scene, and have an
understanding what they may not support ahead of time.
This is difficult in several scenarios, especially when combined with composition
to analyze ahead of time. Additionally, this can help reduce the need to parse
multiple file formats ahead of time to know if they're supported.

As such, profiles are simply hints that should be truthful from the content creation
pipeline to the consuming application/runtime. They are not meant to be taken
as absolute truth.

## Metadata Location

One question is where is best to store the metadata. Especially when it comes to the
use of multiple layers composing a stage.
Does the root layer need to describe the sum of all profile information of the rest
of the stage?

Therefore, it may be preferable to store the metadata on the individual top level prims.

This would allow the metadata to compose together, at the expense of a little more
complexity in where to look for the metadata.

## Suggested Core Profile

We propose the addition of an OpenUSD base profile that corresponds to the USD version.

This would be a well recognized base profile to use for systems in the form of
`org.openusd.core` where the version would be `0.24.5` etc...

Future base profiles could be managed by well known bodies in the industry like the
AOUSD. For example if there was a more limited set of USD for the web without
features like volumetrics, it could be `org.aousd.web` with a requisite version.

## Suggested Augmentation Profiles

The following profiles are examples of hypothetical augmentation profiles.

- **org.aom.vvm** : Use of
  the [Volumetric Visual Media](https://aomedia.org/press%20releases/call-for-proposals-on-static-polygonal-mesh-coding-technology/)
  compression
- **org.aom.avif** : Use of the AVIF media encoder, since USD files may need to be
  used in older runtime versions that do not include the AV1 decoder.
- **com.apple.realitykit.components** : Components that describe RealityKit specific runtime behaviour.
- **org.aswf.materialx** : Requires usdMtlx be built for a specific version of MaterialX to load the data
- **org.aswf.openvdb** : Requires VDB to be available to load volumetric data

## Validation

The addition of profiles could open up the opportunity for more granular validation.
e.g a file that doesn't claim to use RealityKit components could surface a warning
if those components are encountered.

Specific additions to validation are considered out of scope for this proposal, but
the idea as an abstract is one that could be useful.

There are a few ways that profiles can help with validation of USD files:

1. An application may present warnings on load when it load a USD file that uses an unsupported extension. This would be
   similar to when Maya loads a ma file using unknown plugins , or when Keynote loads a file that makes use of unknown
   fonts.
2. Asset deliveries could have very quick validation to make sure that the assets aren’t using undesirable extensions,
   prior to parsing the files themselves. The list of e compatibility information could be provided to asset vendors to
   check against in a normative way.
3. An asset library could choose to only show USD files that have extension versions compatible with the current
   application
4. Command line tools (like the macOS fork of usdchecker) could validate whether a given set of extensions would work on
   the current versions of RealityKit etc...

## Alternate Solutions

When proposing this addition, no other alternate approaches were suggested
beforehand by contributors and evaluators.


