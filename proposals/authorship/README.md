# Authorship Schema

[Link to Discussion](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/106)

**Authors:** Dhruv Govil

**Disclaimer:** This proposal should not be taken as an indication of any upcoming
features in any particular product.
It is being provided to garner community feedback and help guide the ecosystem.
I am also going to emphasize that I am not a lawyer.
While I have consulted with our great legal team to see if we have holes in coverage, that doesn't extend to providing any legal advice.

## Summary

Generative AI uses is growing quickly, and regulations around it are arriving around the world.,
These regulations require that AI-generated content be clearly
identifiable as such. 
USD is increasingly the format of choice for 3D content across
games, film, spatial computing, and the web, we need a standardized way to
record who or what made a given prim or asset.

This proposal aims to fix that. We propose a standardized set of authorship metadata
fields that any prim can carry, covering the range of things people actually need:
meeting regulatory requirements around AI-generated content, crediting artists,
tracking studio ownership, and just generally knowing where your content came from.
Generative AI is the immediate motivation, but the same schema works just as well
for human artists, studios, and non-AI algorithmic tools like photogrammetry.

The important thing is that the industry aligns on the same fields in
the same place (the exact storage mechanism is a secondary concern, and we discuss the
options in the [Details](#details) section). One natural fit is a multiple-apply API schema,
which would let a single prim carry records from every step in its creation pipeline,
for example a generative AI model, a photogrammetry tool, and a human artist who cleaned
up the result (or the other way around because I'd like AI to be cleaning up my messy models).

A quick example of what it looks like in practice:

```python
def Mesh "Bunny" (
    prepend apiSchemas = ["AuthorshipAPI:hunyuan3d"]
) {
    uniform string authorship:hunyuan3d:producer = "net.trellis3d.hunyuan3D"
    uniform string authorship:hunyuan3d:version = "2.1"
    uniform string authorship:hunyuan3d:sourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string[] authorship:hunyuan3d:attribution = ["Trellis Hunyuan 3D", "John Doe"]
    uniform string authorship:hunyuan3d:description = "Prompt: A fluffy bunny"
    uniform string authorship:hunyuan3d:creationTime = "2025-02-16T12:03:17+01:00"
    uniform string authorship:hunyuan3d:identifier = "6530a534-ca8f-487c-8968-0fecd8e717a6"
    uniform string authorship:hunyuan3d:license = "CC-BY-SA-4.0"
    uniform string[] authorship:hunyuan3d:contact = ["johndoe@sample.com"]
}
```

**Note:** We have had early conversations with John McCarten, who you will know from
the RMTC group at the [Academy Software Foundation (ASWF)](https://www.aswf.io), and while there
is overlap in the problems both efforts are concerned with, the two approaches are
harmonious rather than competing.

---

## Problem Statement

USD does not currently have a standard way to record authorship or provenance information
on prims. People have worked around this using custom metadata, `assetInfo` dictionaries,
or bespoke schemas, but none of these are standardized across the industry.

This is becoming a more pressing issue for a few reasons:

1. **Generative AI content** is increasingly common in production pipelines,
   and a growing number of regulations around the world require that AI-generated
   content be identifiable as such (see the [Regulatory Landscape](#regulatory-landscape) section).
2. **USD's composition model** means a single prim may have been touched by
   multiple tools from multiple vendors across multiple pipeline steps.
   This makes it hard for a simple file-level tag to accurately describe what happened.
3. **Attribution and licensing** are important even for human-created content.
   Artists, studios, and tool vendors all have perfectly good reasons to want to record
   who made something and under what terms.

Without a shared standard, every application and pipeline ends up inventing its own
solution, which hurts interoperability and makes compliance harder than it needs to be.

This is not just important for the processes that create the content, but also for viewers and renderers that will
then have regulatory requirements to present the information or persist it in their outputs.

---

## Non-Goals

It is worth being upfront about what this proposal is deliberately not trying to do,
so that the scope stays manageable and the discussion stays focused.

**Tamper resistance and cryptographic signing** are explicitly out of scope.
We know this matters, especially for situations where you need to prove
that authorship metadata has not been altered after the fact. However, it is a
significantly harder problem that involves key management, certificate authorities,
file format changes, and a whole ecosystem of tooling. We do not want to hold up
a useful and achievable metadata standard while waiting to solve that.
It deserves its own proposal and its own focused discussion. 

This proposal only records who or what authored a prim. It does not verify it,
sign it, or guarantee that the information has not been tampered with.
We are relying on the honor system here, and we trust the community to provide
trustworthy information. May your render times be longer if you do not.

---

## Why Authorship and not Provenance?

Early versions of this proposal used the name "Provenance" and `ProvenanceAPI`.
We made a deliberate choice to rename it, and it is worth explaining why.

**Provenance** is a term borrowed from the art world and archival practice.
It refers to the full documented chain of ownership and custody of an object over time:
who owned it, where it has been, and how it changed hands. That is a richer concept
than what we are trying to do here, and it sets expectations we cannot meet.
A provenance system implies tracking changes over time, recording transfers of ownership,
and potentially verifying the chain of custody. That is a much harder problem and
overlaps heavily with the tamper-resistance work we have explicitly left out of scope.

**Authorship** is simpler and more direct. It answers the question "who or what made this?"
at the moment it was made. That is what matters for attribution, licensing, and most
regulatory requirements. It is also a term that artists, studios, and tool vendors will
find intuitive, regardless of whether they are working in a legal or archival context.

We still use "provenance" in the glossary as a general concept, because it is a useful
word for describing the broader problem space. But the schema itself is about authorship.

---

## Glossary of Terms

* **Provenance**: The origin and history of an asset or prim, including who or what created it
  and how it was modified over time.
* **Producer**: The specific tool, model, or person most directly responsible for creating
  a given prim or asset. More on how to pick this in the [Details](#details) section.
* **Generative AI (GenAI)**: AI systems that generate novel content such as 3D meshes,
  textures, or animations from a prompt or other input.
* **Photogrammetry**: A technique for creating 3D models from photographs.
  Not generative AI, but also not fully human-authored. A good example of why we
  need a flexible `sourceType` rather than a simple AI/not-AI flag.
* **IPTC**: The International Press Telecommunications Council. They maintain a vocabulary of
  [Digital Source Types](https://cv.iptc.org/newscodes/digitalsourcetype/)
  that we reference in `sourceType`, though other registrars are also acceptable.
* **SPDX**: The Software Package Data Exchange standard, which maintains a list of
  [standardized license identifiers](https://spdx.org/licenses/) we recommend for the `license` field.
* **C2PA**: The Coalition for Content Provenance and Authenticity.
  An industry standard for signing and verifying media provenance,
  primarily targeting 2D formats. See [Relationship to C2PA](#relationship-to-c2pa).
* **UUID4**: A universally unique identifier, version 4. Recommended as a format for the `identifier` field.

---

## Regulatory Landscape

A number of jurisdictions are introducing or have introduced requirements around
identifying AI-generated content. We are not lawyers, and nothing in this proposal
should be taken as legal guidance. It is up to individual asset authors and pipeline
owners to understand and comply with the laws that apply to them.

That said, we want to acknowledge that this space is moving fast and provide a starting
point for people who want to understand the landscape.
[VerifyWise](https://verifywise.ai/global-ai-regulations) maintains a useful running
list of global AI regulations if you want a broader picture.
Here are some of the regulations we are aware of that are most relevant:

| Region          | Regulation                                                                                                                                                                        | Effective Date    |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| European Union  | [EU AI Act, Article 50](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)                                                                                     | August 2, 2026    |
| California, USA | [CA AI Transparency Act (SB 942)](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB942)                                                            | January 1, 2026   |
| China           | [Measures for Identifying Synthetic Content](https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm)                                                                            | September 1, 2025 |
| Japan           | [AI Guidelines for Business](https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20260331_12.pdf)                                                              | March 31, 2026    |
| Australia       | [Being Clear About AI-Generated Content](https://www.industry.gov.au/publications/being-clear-about-ai-generated-content)                                                         | Active            |
| Canada          | [Guide on the Use of Generative AI](https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/guide-use-generative-ai.html) | Active            |
| Singapore       | [Model AI Governance Framework for Generative AI](https://aiverifyfoundation.sg/wp-content/uploads/2024/06/Model-AI-Governance-Framework-for-Generative-AI-19-June-2024.pdf)      | Active            |

I know this proposal is arriving fashionably late to be of
immediate help with some of these deadlines. Regulations, it turns out, do not wait
for the 3D ecosystem to finish its design review. However, most of these regulations are
currently focused on traditional media and do not yet specifically address 3D scene content.
I believe that showing we are working towards this and doing it right will be important.

We believe the fields we have proposed here cover the common requirements across these
regulations reasonably well, but I would welcome feedback from your own legal counsels.
In any case, this proposal does not provide guidance on legal compliance and it is upto all content creators to comply with the laws that affect them.

---

## Relationship to C2PA

[C2PA](https://c2pa.org) (Coalition for Content Provenance and Authenticity) is a
widely adopted standard for provenance in media, backed by Adobe, Google, Microsoft,
and others. It handles things like cryptographic signing, tamper evidence, and
provenance manifests.

This proposal and C2PA are complementary and not in conflict:

* C2PA operates at the **file level**, attaching provenance manifests to media files.
* This proposal operates at the **prim level** within the USD scene graph,
  letting individual prims carry their own authorship records even when they
  come from different sources and are composed together.

We are explicitly **not** tackling cryptographic signing or tamper resistance in this
proposal. That is a much larger and separate discussion, and we do not want to hold up
a useful and achievable standard while waiting to solve a much harder problem.

---

## Authorship Metadata Fields

Before getting into how to store this data, here are the fields we propose.
Of these, only `producer` and `version` are required if the schema is applied at all.
We strongly encourage `sourceType` as well, as it is the most useful field for
compliance and interoperability.

### `producer` (required)

An identifier for the tool or system that wrote the USD data for this prim.
This is always a tool, not a person. If Jane modeled something in Blender,
the producer is `org.blender` because Blender is what generated the USD.
Jane goes in `attribution`.

The key word is *most directly*. If a generative AI model runs inside a DCC tool,
the producer should be the generative AI model, not the DCC tool. The DCC tool may
be recorded separately as its own `AuthorshipAPI` instance (see the
[multi-step pipeline example](#multi-step-ai-pipeline)).

Producer identifiers should use reverse domain notation, the same convention used
by Apple bundle identifiers and Java packages:

```
net.trellis3d.hunyuan3D
org.blender
com.artstation.<username>
```
This helps prevent conflicts between GenAI model names, especially when multiple providers may have the same GenAI models with customizations.
This helps avoid conflicts since domain names are globally unique
and their ownership is publicly verifiable. If you own `trellis3d.net`, nobody else
can legitimately claim `net.trellis3d.*`. Reversing the domain puts the most specific
part last, so you can also namespace within your own tools cleanly
(e.g. `com.mycompany.toolA` vs `com.mycompany.toolB`).
If you do not have a domain, using a well-known identifier like your GitHub username
or organization is a reasonable fallback. 


Note that the instance name in `AuthorshipAPI:hunyuan3d` is just a short namespace
handle to avoid field collisions on the prim. The same model could be hosted by
multiple providers, or two vendors could pick the same short name.
The `producer` field is what tools should actually read to identify the creator.

### `version` (required)

A string identifying the version of the producer that created this prim.

### `sourceType` (strongly encouraged)

A URI or identifier describing the nature of the creative process.
We recommend using the [IPTC Digital Source Type vocabulary](https://cv.iptc.org/newscodes/digitalsourcetype/),
but other standards bodies and registrars are equally acceptable.
If nothing appropriate exists in any registrar, a plain descriptive string is also fine.

Some common IPTC values that may be useful:

* `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia`: content generated by a trained AI model
* `http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicMedia`: content generated by an algorithm (e.g. photogrammetry, procedural)
* `http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital`: created by a human using digital tools

### `attribution` (optional)

A list of human-friendly attribution strings. This might include the name of the tool
or service, the name of an individual artist, or a studio name. This is intended for
display purposes.

### `description` (optional)

A free-form description of how the prim was created. 

For AI-generated content, this might include the prompt used. 

For human-created content, it might describe the technique or reference material used.
This might also be useful for things like museum assets where we can include the history
of how the asset was acquired. It is technically an unbounded string, so the full
dramatic backstory is allowed. We leave editorial restraint as an exercise for the author.

### `creationTime` (optional)

An ISO 8601 timestamp recording when this prim was created, including timezone.
For example: `2025-02-16T12:03:17+01:00`.

### `identifier` (optional)

A unique identifier for a specific version of this asset. We recommend a UUID4 or similar.
This is useful both for generative AI tools (where the same prompt run twice produces
different outputs that need to be distinguishable) and for human-made assets where
you want to track a specific version of a piece of work.
This identifier should not encode information that could identify the author
outside of the system that created the asset. A UUID4 is good. Your email address
is not. Your social security number is certainly not.

### `license` (optional)

A license for use of this asset. We strongly recommend using an
[SPDX identifier](https://spdx.org/licenses/) where possible (e.g. `CC-BY-SA-4.0`,
`MIT`, `LicenseRef-Proprietary`). If your license is not in the SPDX list,
a URL to the license text is also fine or the full license text.

If no license is provided, no specific license should be assumed.

### `contact` (optional)

One or more contact strings for questions about this asset. This is intentionally
freeform. It could be an email address, a support URL, a licensing page, a phone
number, or anything else that helps someone get in touch about the asset.
It is up to the author or tool to decide what is useful here.
Please be sensible about what you put here; nobody needs your home address in a mesh file.

---

## Details

### Storage Mechanism

We propose the fields above be stored as a **multiple-apply API schema** called
`AuthorshipAPI`, with the namespace prefix `authorship`.

We looked at a few options before landing here:

* **Layer metadata**: The most obvious place to put this kind of information,
  but layer metadata does not survive USD composition well. When layers are
  combined or flattened, this information can easily be lost or become ambiguous.
  To designate an entire file as AI-generated without using layer metadata,
  apply `AuthorshipAPI` to the top-level prims in the file (e.g. the default prim
  or all root-level prims). Child prims then inherit authorship by convention as
  described in the [Hierarchy and Inheritance](#hierarchy-and-inheritance) section.

* **`assetInfo` dictionary**: A reasonable alternative, and one we considered carefully.
  This works well for single-author assets but might get awkward when a prim has
  multiple authorship records from different pipeline steps.

* **Multiple-apply API schema**: Our preferred approach. It composes correctly
  with USD's composition model, supports multiple simultaneous authorship records cleanly,
  and makes the authorship data queryable through standard USD APIs.
  Crucially, because each instance has its own namespace (e.g. `authorship:hunyuan3d:`
  and `authorship:blender:`), instances from different layers do not clobber each other
  during composition. Both survive and remain independently readable.

We are open to `assetInfo`-based alternatives if there is strong community preference,
as long as the format is standardized. The important thing is that everyone is reading
and writing the same fields in the same place.

### Choosing a Producer

The `producer` field should name the most proximate creator of the prim.
This is worth spelling out because it can be surprisingly ambiguous in multi-step pipelines.

If a generative AI model runs inside Blender, you would list the AI model as the
producer for its authorship record. Blender might be listed as the producer for a
separate `AuthorshipAPI` instance representing the step where a human used Blender
to review or modify the result. These are distinct steps in the pipeline and deserve
distinct records.

A few practical guidelines:

* A plugin should attribute the underlying algorithm, not the host application,
  unless the host application itself is doing the creative work.
* A studio pipeline step (e.g. a procedural rigging tool) is itself a valid producer
  even if it is not a commercial product.
* A human artist is usually not a `producer`. The tool they used to generate the USD is, unless they literally manually wrote the USD (power to them if they're writing whole assets manually).
  The human goes in `attribution`.

### Hierarchy and Inheritance

USD's composition model naturally raises the question of what it means for a prim
to have authorship information when its children do not.

Our convention is:

**A prim's children implicitly inherit its authorship unless they specify their own.**

This is by convention, not by schema enforcement. A child prim that has been modified
or recreated by a different tool or person can simply apply its own `AuthorshipAPI`
to record that fact. We recognize this inheritance is inherently ambiguous (a parent
prim being AI-generated does not necessarily mean every child is, especially in
complex compositions), but it provides a useful and safe default for tools that want to
make conservative inferences.

### Viewer and Renderer Responsibility

How authorship information is surfaced to end users is entirely up to individual applications,
and we intentionally do not prescribe this. A viewer might choose to show a badge on
AI-generated content, an exporter might write authorship data using the authorship
data, or a compliance tool might flag prims that lack required fields. All of those
are perfectly valid uses of this data.

Similarly, when a USD scene is rendered to an image or video, any content labeling
requirements from the regulations above may need to carry through to the rendered output.
That is outside the scope of this proposal, but the authorship data in the scene graph
can serve as the source of truth for downstream labeling tools.

---

## Examples

### AI-Generated Mesh

A mesh generated by a single generative AI tool.

```python
def Mesh "Bunny" (
    prepend apiSchemas = ["AuthorshipAPI:hunyuan3d"]
) {
    uniform string authorship:hunyuan3d:producer = "net.trellis3d.hunyuan3D"
    uniform string authorship:hunyuan3d:version = "2.1"
    uniform string authorship:hunyuan3d:sourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string[] authorship:hunyuan3d:attribution = ["Trellis Hunyuan 3D", "John Doe"]
    uniform string authorship:hunyuan3d:description = "Prompt: A fluffy bunny"
    uniform string authorship:hunyuan3d:creationTime = "2025-02-16T12:03:17+01:00"
    uniform string authorship:hunyuan3d:identifier = "6530a534-ca8f-487c-8968-0fecd8e717a6"
    uniform string authorship:hunyuan3d:license = "CC-BY-SA-4.0"
    uniform string[] authorship:hunyuan3d:contact = ["johndoe@sample.com"]
}
```

### Multi-Step AI Pipeline

A mesh generated by an AI model and then cleaned up inside a DCC tool.
Each step in the pipeline gets its own `AuthorshipAPI` instance.
Note that `hunyuan3d` is listed as the producer for the AI step even though Blender
was the host application, because the "creative" work for that step was done by the model.

```python
def Mesh "Bunny" (
    prepend apiSchemas = ["AuthorshipAPI:hunyuan3d", "AuthorshipAPI:blender"]
) {
    # The generative AI model that produced the initial mesh
    uniform string authorship:hunyuan3d:producer = "net.trellis3d.hunyuan3D"
    uniform string authorship:hunyuan3d:version = "2.1"
    uniform string authorship:hunyuan3d:sourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string authorship:hunyuan3d:description = "Prompt: A fluffy bunny"

    # A human artist who cleaned up the mesh in Blender afterwards
    uniform string authorship:blender:producer = "org.blender"
    uniform string authorship:blender:version = "4.2"
    uniform string authorship:blender:sourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"
    uniform string[] authorship:blender:attribution = ["Jane Doe"]
    uniform string[] authorship:blender:contact = ["jane@example.com"]
}
```

### Human Artist

A prop modeled by a human artist and released under a Creative Commons license.

```python
def Mesh "TeaCup" (
    prepend apiSchemas = ["AuthorshipAPI:jane"]
) {
    uniform string authorship:jane:producer = "org.blender"
    uniform string authorship:jane:version = "4.2"
    uniform string authorship:jane:sourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"
    uniform string[] authorship:jane:attribution = ["Jane Doe"]
    uniform string authorship:jane:license = "CC-BY-4.0"
    uniform string[] authorship:jane:contact = ["jane@example.com"]
}
```

### Photogrammetry Scan

A prop captured using photogrammetry. Not AI-generated, not hand-modeled,
but the schema handles it naturally via `sourceType`.

```python
def Mesh "ScannedProp" (
    prepend apiSchemas = ["AuthorshipAPI:rcapture"]
) {
    uniform string authorship:rcapture:producer = "com.capturingreality.rcapture"
    uniform string authorship:rcapture:version = "1.4"
    uniform string authorship:rcapture:sourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicMedia"
    uniform string[] authorship:rcapture:attribution = ["Acme Studio"]
    uniform string authorship:rcapture:creationTime = "2025-06-01T09:00:00+00:00"
}
```

---

## Schema Definition

```python
class "AuthorshipAPI" (
    inherits = </APISchemaBase>
    doc = """Records authorship information about how a prim was created.
    Multiple instances may be applied to a single prim, one for each distinct tool or
    person that contributed to its creation."""

    customData = {
        token apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "authorship"
    }
) {
    uniform string producer (
        doc = """An identifier for the system or person most directly responsible for
        creating this prim. Should be the most specific producer in the pipeline.
        For example, if a generative AI model runs inside a DCC tool, this should name
        the AI model. Reverse domain notation is recommended:
        e.g. net.trellis3d.hunyuan3D, org.blender, com.artstation.janedoe."""
    )

    uniform string version (
        doc = """A string identifying the version of the producer."""
    )

    uniform string sourceType (
        doc = """A URI or identifier describing the nature of the creative process.
        We recommend using the IPTC Digital Source Type vocabulary at
        https://cv.iptc.org/newscodes/digitalsourcetype/ , though other registrars
        are acceptable."""
    )

    uniform string[] attribution (
        doc = """An optional human-friendly list of attributions for display purposes.
        May include tool names, service names, and individual contributors."""
    )

    uniform string description (
        doc = """An optional free-form description of how this prim was created.
        For AI-generated content this might include the prompt. For human-created
        content it might describe the technique or reference material."""
    )

    uniform string creationTime (
        doc = """An ISO 8601 timestamp including date, time, and timezone.
        For example: 2025-02-16T12:03:17+01:00"""
    )

    uniform string identifier (
        doc = """A unique identifier for this asset. A UUID4 is recommended.
        Should not encode information that could personally identify the author
        outside of the creating system."""
    )

    uniform string license (
        doc = """An optional license for use of this asset. SPDX identifiers are
        strongly recommended (https://spdx.org/licenses/). A URL is also acceptable
        for non-SPDX licenses. If absent, no specific license should be assumed."""
    )

    uniform string[] contact (
        doc = """Optional contact information for questions about this asset."""
    )
}
```

---

## Risks

The main risk is that this schema gets ignored or inconsistently adopted,
which would undermine its usefulness for compliance and interoperability. The best
mitigation is to keep the schema simple and the barrier to entry low, which we have
tried to do.

There is also a risk that the `producer` naming convention is not followed consistently,
making it hard to identify specific tools in practice. We can only encourage best
practices here, not enforce them.

Beyond those, given that this schema is purely metadata, the risks are fairly limited.
At worst, tools that do not understand it will just ignore it.

---

## Alternates Considered

* **Layer metadata**: Simpler to author, but does not compose well. Information
  gets lost when layers are combined or flattened.

* **`assetInfo` dictionary**: Reasonable for single-author assets, but there is no
  great way to record multiple distinct authorship records cleanly without inventing
  a convention on top of it.

* **A single-apply schema**: Would not support the multi-step pipeline case,
  which is one of the most important motivating use cases for USD specifically.

* **Building on C2PA directly**: C2PA is a powerful standard but is designed around
  file-level manifests and cryptographic signing. It does not map naturally to
  prim-level authorship within a composed scene graph.
  We see these as complementary, not competing.

## Caveats

Any implementation of this proposal that would make its way into OpenUSD should probably carry some kind of disclaimer
that the OpenUSD project does not provide legal guidance, that its up to the creators to be compliant with regulations,
and that the project is not liable for any misuse.

In fact...while, I'm at it, all those disclaimers also apply to this proposal too!

---

## Excluded Topics

* **Cryptographic signing and tamper resistance**: We know this is important,
  especially for regulatory compliance. It is also a much larger and harder problem.
  We have deliberately left it out of this proposal so that it does not block progress
  on the more achievable authorship metadata standard. It deserves its own proposal.

* **Rendering and output labeling**: Whether and how rendered images or videos should
  carry authorship labels derived from the USD scene data is out of scope here.
  We note it as an important downstream problem worth solving.

* **Enforcement or validation**: We do not prescribe how pipelines should validate
  the presence or accuracy of authorship data. That is up to individual tools and studios.

---

## Open Questions

These are things we have not resolved yet and would love community input on. Some of these may be okay to leave ambiguous.

**What happens when an asset is referenced into another scene?**
If a scene references in an asset that carries `AuthorshipAPI` records, the referenced
prims bring their authorship along. But does the act of referencing the asset into a
new scene implicitly apply to the referencing scene as containing AI-generated content?
We think it should be considered being applied in the same way that a child prim inherits
from its parent, but this has implications for how tools surface the information and
warrants broader discussion.

**Where does authorship live when AI generates an empty layer?**
If a generative AI tool creates an empty USD layer (containing no prims of its own)
and then sublayers in human-made content, there is no obvious prim to attach
`AuthorshipAPI` to. Should there be a convention for stamping authorship at the
layer or stage level in this case, even though layer metadata has the composition
limitations described above?

**What if AI creates an empty layer and sublayers human-made content?**
Related to the above: if the structure is an AI-authored root layer that pulls in
human-made sublayers, the human content has clear authorship on its own prims.
But the overall scene structure was created by an AI. How should tools reason about
the authorship of the scene as a whole versus the individual prims within it?

---

## Closing Notes

Having a shared standard for authorship in USD feels genuinely overdue, both for the AI
content compliance use case that is motivating a lot of interest right now, and for the
broader goal of just being able to know where your content came from.

The fact that USD is used across the entire industry, with complex multi-vendor pipelines
and scene composition, makes this both more important and more interesting to solve than
it is for simpler formats. We think the multiple-apply schema approach handles that
complexity well.

We hope this can be a useful starting point for a good discussion, and we genuinely
welcome feedback on the schema, the field names, and the storage approach.
