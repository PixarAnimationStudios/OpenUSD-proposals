# Accessibility Schema

[Link to Discussion](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/69)

## Summary

As USD enters more widespread use, with a range of interactive experiences for spatial computing and the web, it becomes necessary to make sure we do not exclude anyone. It is important for 3D content to be as accessible as other media types for people with a range of needs that may require virtual assistive services.

To facilitate this, we propose the addition of accessibility metadata, using industry standard nomenclature.

```python
def Mesh "Cube" (
    prepend apiSchemas = ["AccessibilityAPI"]
) {
    string accessibility:label = "A sentient lamp with an adjustable body and cone head"
    string accessibility:alternate = "The lamp has round base with two sections above it that may be adjusted. It has a conical head with a lightbulb inside. It likes to chase inflatable balls"
    token accessibility:important = "standard"
}
```

## References and Notes

**Disclaimer :** This proposal should not be taken as an indication of any upcoming feature in our products. It is being provided to garner community feedback and help guide the ecosystem.

**Authors**: J Lobo Ferreira da Silva , Dhruv Govil

### Glossary of Terms

* **Accessibility affordances** : Refers to features that may provide information for assistive services like audio description tools to provide assistance to users who may have limited sight or mobility.
* **Audio Description** : Several tools and platforms provide the ability to describe what is on screen to the user.
    These are usually based on metadata on user interface items, such as image alt text or button descriptions.
* **ARIA (Accessible Rich Internet Application) Roles** : A set of roles and attributes to make the web more accessible. 

### Related Reading

Here are some related materials to read on about the use of accessibility in various systems.
None of these are required reading, but may help provide context.

* [Apple Accessibility](https://www.apple.com/ca/accessibility/)
  * [Catch up on accessibility in SwiftUI](https://developer.apple.com/wwdc24/10073)
  * [Improving the Accessibility of RealityKit Apps](https://developer.apple.com/documentation/realitykit/improving-the-accessibility-of-realitykit-apps)
* [Microsoft Accessibility](https://www.microsoft.com/en-us/accessibility)
* [Web Accessibility Guidelines](https://www.w3.org/TR/WCAG21/)
* [ARIA Roles](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
* [Unity 3D Accessibility](https://docs.unity3d.com/2023.2/Documentation/ScriptReference/UnityEngine.AccessibilityModule.html)

## Details 

### API Schema

We propose a new Applied API schema that will allow any Prim to provide descriptions for Audio Description tools. 

We include the following attribute groupings, with the `accessibility` namespace prefix.

* `label`: The primary description string that is presented to the user. 
* `alternate` : An alternate description string that may provide more detail than the primary label.
* `importance` : Sets the importance of this group so tools may prioritize what to surface to a user. Options are `high`, `standard`, `low` with a default of `standard`.

All three attributes are based on existing standard names in accessibility frameworks, and in consultation with multiple accessibility experts.

Given the example in the summary, repeated here

```python
def Mesh "Cube" (
    prepend apiSchemas = ["AccessibilityAPI"]
) {
    string accessibility:label = "A sentient lamp with an adjustable body and cone head"
    string accessibility:alternate = "The lamp has round base with two sections above it that may be adjusted. It has a conical head with a lightbulb inside. It likes to chase inflatable balls"
    token accessibility:important = "standard"
}
```

Only the label is required, and so the shortest form of this may be as simple as

```python
def Mesh "Cube" (
    prepend apiSchemas = ["AccessibilityAPI"]
) {
    string accessibility:label = "A sentient lamp with an adjustable body and cone head"
}
```

### Attribute Purposes

It can be useful to have multiple types of descriptions, represented as purposes.
For example, a primary description may choose to describe a general appearance, but a secondary one may choose to describe a specific detail.

For example, a user may want to have a short summary of the object, but then ask details about its size.

We propose that these be represented as purposes on the attribute.

```Python
def Mesh "Cube" (
    prepend apiSchemas = ["AccessibilityAPI"]
)
{
    string accessibility:label = "A Cube"
    string accessibility:alternate:default = "This cube is a wonderful looking cube"
    token accessibility:importance:default = "standard"
    
    string accessibility:alternate:size = "As big as a house"
    token accessibility:importance:size = "low"
}
```

This allows for multiple levels of description, and also allows for aspects of the description to be changed by variants.

For example a user may ask what color an object is, and different material variants may provide their own `color` purpose here.

While we do not limit the names of these purposes, a few suggestions may be:

* `default`: The generic, anonymous purpose. No purpose needs to be specified here.
* `size` : Describe the size of the object in ways a human without inherent unit visualizations might understand.
    For example, a user with limited visibility may not know how large a `metre` is, but may understand sizes in relationship to a common object.
* `color` : The color of the object, which can describe more details such as textural properties.

### Language Support

We also allow expect accessibility to, optionally, be provided in multiple languages. For example, in Canada it is often required to provide equal affordances to English and French users.

We suggest using the [Multiple Language Proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/blob/main/proposals/language/README.md) to allow specification of the language.

In keeping with the language proposal, the language purpose would appear after all other purpose tokens.

For example,

```Python
def Mesh "Cube" (
    prepend apiSchemas = ["AccessibilityAPI"]
)
{
    string accessibility:label = "A Cube"
    string accessibility:alternate = "This cube is a wonderful looking cube"
    token accessibility:importance = "Standard"
    
    string accessibility:label:lang:fr = "Un cube"
    string accessibility:alternate:lang:fr = "Ce cube est un cube magnifique"
    string accessibility:alternate:lang:fr_ca = "Ce cube est un cube magnifique canadien"
}
```

#### Options for Language Tokens

In the language proposal, I offer two options for language purposes.

1. A prefix-less version : `<attribute_name>:<language_token>`
2. A prefixed version : `<attribute_name>:lang:<language_token>`

It would likely be preferable to choose the second version here.

However, if we did want to choose the first one, we propose options for the default accessibility attribute to distinguish between the language purpose and an accessibility purpose token.

1. Implicit Default Purpose:
   - If no accessibility purpose is given, and no language purpose is given, it is implicitly the `default` purpose. 
   - If the `default` purpose is explicitly authored, it is preferred over the anonymous version.
   - If a language purpose is provided, the `default` accessibility purpose must also be explicitly authored.
2. Explicit Default Purpose:
   - The default purpose must always be provided as part of the attribute name regardless of the language being specified.

My preference is that we require the language purpose always have the `:lang:` prefix to make it clear in all cases.


### Prim Restrictions

Initially we believed it might be valuable to restrict accessibility attributes to just `model` kinds, but we've since come to realize that users may like it over any object in the hierarchy. 

This would allow users with accessibility needs to perhaps inspect assets within a scene if needed, but also learn about non-gprim types such as Materials or Lights.

#### Default Prim Recommendation

Often, USD files are presented to users as a single object even if they consist of many assets. 

We strongly recommend that the scene description be hosted on the default prim in the scene. 

Utilities that want to go further with exposing the USD hierarchy may still choose to expose accessibility on the rest of the prims, but by having the default prim host the primary scene description, we believe many applications can more easily report the information in the majority of contexts.

This would be analogous to alt-text for an image which describes an entire image, rather than elements within it, though some tools do support more granular descriptions.


### Temporal Changes

In most accessibility systems, the information is static.
However, in recent times, several attempts have been made at temporal accessibility in mediums such as games or our very own proposals to HLS video streaming for photosensitivity.

As such, we think it is valuable to optionally allow the accessibility attributes to have time samples that may vary over time. For example an animation of Luxo, Jr. However, this must never be the primary source of accessibility information for reasons laid out below.

```Python
def Xform "LogoIntro" (
    prepend apiSchemas = ["AccessibilityAPI"]
)
{
    string accessibility:alternate.timeSamples = {
        54: "The lamp jumps on the ball",
        56: "The lamp rolls back and forth on the ball",
        60: "The ball deflates and the lamp sinks down",
        66: "The lamp moves itself off the squashed ball",
        70: "The lamp tries to revive the ball",
        80: "The lamp looks down, sad and leaves"
        88: "The lamp returns with a larger ball"
    }
}
```

As with the prim restrictions above, we do not suggest that this be commonly used but leave the option for people to do so. 

As most accessibility systems are based around static content, and too much changing information may inundate a user, we strongly recommend that a static default value be provided for accessibility information even when time samples are provided.

Assistive tools should not be expected to support temporally changing data, though they may choose to at their discretion.

### Prim Relationships

For the initial implementation, we do not allow for rel connections as part of the schema. This is a common request so that strings may format in other prims descriptions, or show semantic relationships between objects. We feel this is too large a problem to keep in scope for the first version.

However, we recognize that a prims hierarchical and binding relationships may be useful to describe to a user.

As such we suggest that it may be useful to provide utilities to gather accessibility data across the following axes:

1. Prim ancestors : A prim hierarchy may be getting more specific descriptions as it descends the tree. Being able to collect the information across its parents would allow a utility to combine the descriptions downwards.
2. Prim children : Similarly, it might be valuable to go in the reverse order when asking about information on a prim where the children provide the details to be combined.
3. Common bindings like Material and Skeleton to fetch information on what the object may look like or what the animation might be doing

We do not suggest or require the traversal to be in the initial implementation, but recognize that it may be a good middle ground between having explicit semantic relationships specific to Accessibility.

My personal suggestion is to defer these API systems till a later point.

### Other Non-Goals

Accessibility is a far-reaching system, and as such we have some explicit non-goals.

* We do not prescribe the way the accessibility data should be presented by accessibility tools. There is a wide range of utilities that may be suited for different needs.
* We do not limit the default number of purpose keys, and only provide a default set as suggestions.


## Alternate Uses

Accessibility information is often very useful for other aspects of a scene. We often find that even users without accessibility needs may benefit from accessibility affordances in systems.

* This may be useful to natural language searches across a scene
* Machine Learning and AI systems may use the accessibility information to gain understanding of the scene. 


## Risks

Given the scope of this proposal is simply metadata, we do not believe there are significant risks. At worst, systems will just ignore them

## Alternates Considered

We've considered several alternatives but discarded them for the following reasons:

* Metadata: Metadata like assetInfo etc may have been useful here but we feel there's too many axes of information here to represent in metadata. 
* SemanticsLabelsAPI is also a valid accessibility information source, but the target goals are too different. Labels are geared towards data management systems versus human interaction.

## Closing Notes

We believe accessibility is a very important facility to provide, and can help open USD up to a wider audience who may otherwise be unable to experience or use the same things many of us take for granted.

To the best of my knowledge, there is no existing accessibility standards for 3D content that is authored independent of a target engine. If there is, I would love to see it though. If there isn't , I think this can let us lead by example.


Again, I'd leave a disclaimer that this proposal is not an indication of any future work on our part. However, I believe that by having this in the USD ecosystem, it's something that we can take on together.