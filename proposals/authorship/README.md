# Authorship Schema

[Link to Discussion](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/106)

**Authors:** Dhruv Govil

**Disclaimer:** This proposal should not be taken as an indication of any upcoming features in any particular product.
It is being provided to garner community feedback and help guide the ecosystem.

However, I will acknowledge that we have a Generative AI Image to USD Mesh generation algorithm available in Reality Composer Pro 3, and are deeply interested in standardization of this specification
so that we can meet regulatory needs going forward.

I am also going to emphasize that I am not a lawyer.
While I have consulted with our great legal team to see if we have holes in coverage, that doesn't extend to providing any legal advice.

## Summary

We are seeing a growth in Generative AI content, and there is also a corresponding growth of regulations world wide to keep up with it.
These regulations require that AI-generated content be clearly identifiable as such.
I also see this as an opportunity to add functionality that may benefit human authors, and adapt to more than just Generative AI content.

This proposal aims to solve that need with a priority on ease of adoption.
We propose a standardized set of authorship metadata
fields that any prim can carry, covering a range of needs:

- meeting regulatory requirements around AI-generated content
- crediting artists for their contributions to shots and scenes
- tracking studio ownership
- generally knowing where your content came from

It is also designed to be forward looking and flexible, with various fields being optional but specified.
This allows us to adapt to differing regulations and needs, while making sure everyone has a known set of parameters to look for, avoiding divergence.

A quick example of what this proposal could look like in practice if using an Applied API Schema (as one of the options discussed below):

```python
def Mesh "Bunny" (
    prepend apiSchemas = ["AuthorshipAPI:hunyuan3d"]
) {
    uniform string authorship:hunyuan3d:producer = "net.trellis3d.hunyuan3d"
    uniform string authorship:hunyuan3d:version = "2.1"
    uniform string authorship:hunyuan3d:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string[] authorship:hunyuan3d:creator = ["Trellis Hunyuan 3D", "John Doe"]
    uniform string authorship:hunyuan3d:prompt = "A fluffy bunny"
    uniform string authorship:hunyuan3d:created = "2025-02-16T12:03:17+01:00"
    uniform string authorship:hunyuan3d:instanceID = "6530a534-ca8f-487c-8968-0fecd8e717a6"
    uniform string authorship:hunyuan3d:usageTerms = "CC-BY-SA-4.0"
    uniform string[] authorship:hunyuan3d:contact = ["johndoe@sample.com"]
}
```

**Note:** We have had early conversations with John McCarten, who you will know from
the RMTC group at the [Academy Software Foundation (ASWF)](https://www.aswf.io). While there
is overlap in the problems both efforts are concerned with, we believe the two approaches are
harmonious rather than competing.

## Problem Statement

USD does not currently have a standard way to record authorship or provenance information
on prims. People have worked around this using custom metadata, `assetInfo` dictionaries,
or bespoke schemas, but none of these are standardized across the industry.

The [Regulatory Landscape](#regulatory-landscape) is making this a more pressing concern in recent times.

Without a shared standard, every application and pipeline ends up inventing its own
solution, which hurts interoperability and makes compliance harder than it needs to be.

This is not just important for the processes that create the content, but also for viewers and renderers that will
then have regulatory requirements to present the information or persist it in their outputs.

## Goals

As this proposal covers a lot of ground, and has overlap with somewhat similar ideas in other areas, I think it's best to start with some goals:

- **Agree on a shared set of fields.** The single most important goal is that the industry
  reads and writes the same authorship fields in the same place. The exact storage mechanism
  matters less than everyone agreeing on one.
- **Work at the prim level, through composition.** Authorship should live on the prims it
  describes and ride along through composition, so a composed scene can carry records from
  every source that contributed to it. Composition carries this well in the common cases;
  there are a few edges (records on an ancestor of a reference target, and flattening) that
  we spell out in [Composition Issues to Consider](#composition-issues-to-consider).
- **Keep the barrier low, work offline and be privacy sensitive.** Authoring these fields should need no signing infrastructure, no
  network access, and no central registry, so any tool in any pipeline can take part. This enables compatibility with MPAA-style air-gapped pipelines and keeps usage private.
- **Reuse existing vocabularies where it helps.** Where field names and values already exist in
  C2PA, XMP, or IPTC, we align with them rather than reinventing them.
- **Support multiple authors per prim.** A single prim may pass through multiple steps, e.g. a human-authored model modified by a generative AI process. Each of those should be able to record its own
  authorship without clobbering the others. Note that we are not concerned with order of operations in this proposal, but want to design the current proposal so it doesn't prevent that in the future.
- **Cover all kinds of authorship, not just AI.** Human artists, studios, DCC tools, and
  algorithmic tools like photogrammetry all deserve a way to record who or what made something.
  AI disclosure is the loudest motivation right now, but it is not the only one.
- **Help people meet AI-disclosure requirements.** The schema should make it straightforward to
  record the information regulations increasingly ask for, even though compliance itself remains
  the content creator's responsibility.


## Non-Goals

It is also worth being upfront about what this proposal is deliberately not trying to do,
so that the scope stays manageable and the discussion stays focused.

We recognize the value in the problems below, but we believe they are much larger lifts. Instead we focus on making sure that we do not cause friction for future proposals from other parties.

**Tamper resistance and cryptographic signing** are explicitly out of scope.
We know this matters, especially for situations where you need to prove
that authorship metadata has not been altered after the fact. However, it is a
significantly harder problem that involves key management, certificate authorities,
file format changes, and a whole ecosystem of tooling. We do not want to hold up
a useful and achievable metadata standard while waiting to solve that.

This proposal only records who or what authored a prim. It does not verify it,
sign it, or guarantee that the information has not been tampered with.
We are relying on the honor system here, and we trust the community to provide
trustworthy information. May your render times be longer if you do not.

**Scope: creative authorship only.** This proposal covers creative authorship. Other forms of provenance are out of scope, such as sensor-capture
metadata (e.g., LiDAR or camera-rig data), engineering lineage from PLM or CAD systems, and
simulation runs producing synthetic training data.

However, while these are non-goals, we will try (where possible) to make our choices such that they allow for those in the future should others want to champion them.

**Rendering and output labeling.** Whether and how rendered images or videos should carry
authorship labels derived from the USD scene data is out of scope here. We note it as an
important downstream problem worth solving.

**Enforcement or validation.** We do not prescribe how pipelines should validate the
presence or accuracy of authorship data. That is up to individual tools and studios.

**Judging whether content is "substantively" AI-generated.** A question that comes up as a
thought exercise is whether a scene should be considered generative-AI-made forever, even
after all of its AI content is replaced (for example a generative environment used in previs
and then swapped for human-made production assets). This proposal takes no opinion on it;
whether the AI influence was substantive is for each content creator or studio to decide.

**Removal and redaction of authorship.** There are legitimate reasons to strip authorship,
such as honoring a takedown or privacy request, removing a `contact` before redistribution,
or dropping a record a downstream party is not licensed to carry. How to do so is out of
scope for this proposal.

**Legal guidance.** Any implementation that makes its way into OpenUSD should probably carry
some kind of disclaimer that the OpenUSD project does not provide legal guidance, that it is
up to creators to comply with the regulations that affect them, and that the project is not
liable for any misuse. In fact, while I'm at it, all those disclaimers apply to this proposal
too!

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
It is also much harder to guarantee since our data is inherently synthetic.

**Authorship** is simpler and more direct. It answers the question "who or what made this?"
at the moment it was made. That is what matters for attribution, licensing, and most
regulatory requirements. It is also a term that artists, studios, and tool vendors will
find intuitive, regardless of whether they are working in a legal or archival context.

We still use "provenance" in the glossary as a general concept, because it is a useful
word for describing the broader problem space. But the schema itself is about authorship.

## Glossary of Terms

- **Provenance**: The origin and history of an asset or prim, including who or what created it
  and how it was modified over time.
- **Authorship record**: A single applied instance of `AuthorshipAPI` (or its fields if using other formats) stored
  on a prim. A prim may carry several. Records are stored data and stay distinct; they do not
  merge.
- **AI designation**: A *derived* determination that a prim should be treated as AI-generated
  for disclosure purposes. It is computed from the `digitalSourceType` of a prim's accumulated
  records (its own plus its ancestors'), and it propagates downward. It is not itself a stored
  field. Keeping "record" (stored) distinct from "designation" (derived) matters when reasoning
  about inheritance and propagation.
- **Producer**: The specific tool or model most directly responsible for creating
  a given prim or asset. This is normally a tool, not a person; the person goes in `creator`
  (the exception being someone hand-authoring the files directly).
  More on how to pick this in the [Details](#details) section.
- **Generative AI (GenAI)**: AI systems that generate novel content such as 3D meshes,
  textures, or animations from a prompt or other input.
- **Photogrammetry**: A technique for creating 3D models from photographs.
  Not generative AI, but also not fully human-authored. A good example of why we
  need a flexible `digitalSourceType` rather than a simple AI/not-AI flag.
- **IPTC**: The International Press Telecommunications Council. They maintain a vocabulary of
  [Digital Source Types](https://cv.iptc.org/newscodes/digitalsourcetype/)
  that we reference in `digitalSourceType`, though other registrars are also acceptable.
- **SPDX**: The Software Package Data Exchange standard, which maintains a list of
  [standardized license identifiers](https://spdx.org/licenses/) we recommend for the `usageTerms` field.
- **C2PA**: The Coalition for Content Provenance and Authenticity.
  An industry standard for signing and verifying media provenance,
  primarily targeting 2D formats. See [Relationship to Provenance Systems like C2PA](#relationship-to-provenance-systems-like-c2pa).
- **UUID4**: A universally unique identifier, version 4. Recommended as a format for the `instanceID` field.
- **DID**: A [W3C Decentralized Identifier](https://www.w3.org/TR/did-1.1/). A verifiable
  identifier that resolves to identity information without a central registry or certificate
  authority. See [Identifiers](#identifiers).

## Regulatory Landscape

A number of jurisdictions have introduced, or will introduce, requirements around
identifying AI-generated content. 

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
immediate help with some of these deadlines. Unfortunately, the regulations were in flux, and there was not enough clarity to make a good proposal until very recently.

We believe the fields we have proposed here cover the common requirements across these
regulations reasonably well, but I would welcome feedback from your own legal counsels.
In any case, this proposal does not provide guidance on legal compliance and it is up to all content creators to comply with the laws that affect them.

### Adoption before Proposal Approval

We recognize that some products may need to adopt similar metadata earlier than this proposal may be accepted.
In that scenario, we recommend prefixing your schema names with `Preliminary` to avoid confusion once this proposal is accepted.

For example, the mesh from the [Summary](#summary) would instead look like this:

```python
def Mesh "Bunny" (
    prepend apiSchemas = ["PreliminaryAuthorshipAPI:hunyuan3d"]
) {
    uniform string preliminaryAuthorship:hunyuan3d:producer = "net.trellis3d.hunyuan3d"
    uniform string preliminaryAuthorship:hunyuan3d:version = "2.1"
    uniform string preliminaryAuthorship:hunyuan3d:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string[] preliminaryAuthorship:hunyuan3d:creator = ["Trellis Hunyuan 3D", "John Doe"]
    uniform string preliminaryAuthorship:hunyuan3d:prompt = "A fluffy bunny"
    uniform string preliminaryAuthorship:hunyuan3d:created = "2025-02-16T12:03:17+01:00"
    uniform string preliminaryAuthorship:hunyuan3d:instanceID = "6530a534-ca8f-487c-8968-0fecd8e717a6"
    uniform string preliminaryAuthorship:hunyuan3d:usageTerms = "CC-BY-SA-4.0"
    uniform string[] preliminaryAuthorship:hunyuan3d:contact = ["johndoe@sample.com"]
}
```

We believe the API Schema will be the easiest form to detect and clean up in the future to bring in line with whatever form this proposal ultimately takes.
This is what we are recommending our own teams do as well in the interim.

## Relationship to Provenance Systems like C2PA

There are already standards for recording provenance, and we are not trying to replace or recreate them.

The best known is [C2PA](https://c2pa.org) (the Coalition for Content Provenance and
Authenticity), a well known standard that
handles cryptographic signing, tamper evidence, and provenance manifests.
As it is likely the most well known, we will reference it below, but we would like to acknowledge that other provenance systems may also exist and we want to remain inclusive of them.

A goal of this schema is to be considerate so that current adoption of it doesn't preclude future proposals from suggesting adoption of provenance standards.
These can be layered and harmonious, rather than at odds with one another. However, those proposals for adoption would be separate and championed by their respective experts.

We believe that this proposal offers valuable distinctions from existing provenance standards.

- C2PA and similar systems operate at the **file level**, attaching provenance manifests to
  whole media files.
- This proposal operates at the **prim level** inside the USD scene graph, so individual prims
  can carry their own authorship records even when they come from different sources and get
  composed together.

What this schema offers is a set of benefits specific to how USD actually gets used:

- **It rides along through composition.** A composed USD stage routinely stitches together
  prims from many layers. Authorship that lives on the prim rides
  along through composition, which a file-level manifest is not designed to represent. 
- **The barrier to entry is low.** Recording these fields is just authoring metadata. Any tool
  in a pipeline can join in without signing infrastructure, certificate management, or a
  manifest format to implement. Tamper-evident standards ask a good deal more of every tool
  that touches an asset, which is a fair price for what they give you, but a steep one.
- **It works offline and keeps things private.** Reading or writing authorship needs no network
  access, no certificate authority, and no resolution step that could quietly reveal that
  someone opened or checked a given asset. This is one of our goals as it pertains to privacy and compatibility with environments where offline use is mandatory.

There are also package level manifest files, like C2PA's
[ZIP-based embedding](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html#_embedding_manifests_into_zip_based_formats).
These are also valuable, but again, are at the package level and this proposal aims to solve the use case of intermixed scenes that are rapidly under iteration by creatives.

### Field Alignment with Existing Standards

Where possible, we have aligned field names with the C2PA / XMP / IPTC vocabulary
to ease interoperability and avoid reinventing established conventions. The table below
shows the mapping:

| AuthorshipAPI field | Equivalent in other standards                                             | Notes                                                                                                                                                                                                                                                                                                                       |
| ------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `digitalSourceType` | `Iptc4xmpExt:DigitalSourceType`                                           | Direct match. We use the same IPTC vocabulary.                                                                                                                                                                                                                                                                              |
| `creator`           | `dc:creator`                                                              | Direct match. The entity primarily responsible for the resource.                                                                                                                                                                                                                                                            |
| `created`           | `xmp:CreateDate`                                                          | Direct match. An ISO 8601 timestamp.                                                                                                                                                                                                                                                                                        |
| `instanceID`        | `xmpMM:InstanceID`                                                        | Matches XMP's `InstanceID`, the identifier for this particular output. XMP's `DocumentID`, which stays stable across edits, is intentionally not adopted (see [`instanceID`](#instanceid-maybe-required)).                                                                                                                        |
| `usageTerms`        | `xmpRights:UsageTerms`                                                    | Direct match. The license or usage terms.                                                                                                                                                                                                                                                                                   |
| `producer`          | `c2pa:softwareAgent`, `Iptc4xmpExt:AISystemUsed`                          | Close, but not an exact match. C2PA's `softwareAgent` ties a tool to a specific action in a chain, and IPTC's `AISystemUsed` is specific to AI. Our `producer` names the entity most responsible for the prim and is read as a stable creator identity, without assuming that entity is AI. We found it a more natural fit. |
| `version`           | `c2pa:softwareAgent` / `ai-disclosure`, `Iptc4xmpExt:AISystemVersionUsed` | C2PA records tool and model version against an action (`softwareAgent`) or through its newer `ai-disclosure` assertion, and IPTC has `AISystemVersionUsed`. We keep it as a simple field sitting next to `producer`.                                                                                                        |
| `description`       | `Iptc4xmpCore:Description`                                                | Matches IPTC's core description field. C2PA keeps freeform fields like this to a minimum since they can't be verified, which makes sense for a tamper-evident standard. We include it because this schema is about description rather than verification.                                                                    |
| `prompt`            | `Iptc4xmpExt:AIPromptInformation`                                         | Matches IPTC's AI prompt field. C2PA models the same idea as an `inputTo` relationship that links the inputs back to the result. We use a plain `prompt` field, which felt more intuitive and avoids overloading the term against node graph inputs.                                                                        |
| `contact`           | _(no equivalent)_                                                         | No equivalent in these standards. Retained for practical support and licensing inquiries.                                                                                                                                                                                                                                   |

## Identifiers

A couple of these fields are identifiers, so it is worth saying up front how we suggest
filling them in.

For `producer`, we recommend reverse domain notation; this is the same convention as Apple bundle
identifiers or Java packages (for example `net.trellis3d.hunyuan3d` or `org.blender`). Domains
are globally unique and their ownership is publicly checkable, so this keeps producer names
from colliding without anyone needing to run a registry. The [`producer`](#producer-required)
field below goes into more detail.

For `instanceID`, we recommend a UUID4. It is unique enough for any practical purpose and gives
away nothing about the author.

These are recommendations, not hard rules, and they are deliberately low-tech so anyone can use
them without standing up infrastructure first.

### Decentralized Identifiers (DIDs)

[W3C Decentralized Identifiers (DIDs)](https://www.w3.org/TR/did-1.1/) come up as an option for
a stronger, verifiable notion of identity. A DID is an identifier that resolves to identity
information without leaning on a central registry or certificate authority. Because `producer`
and `creator` are just strings, a DID like `did:web:trellis3d.net` is a valid value for either,
and a DID can stand in for `instanceID` too if you want that identifier to be resolvable rather
than an opaque UUID.

That said, our recommendation is to keep things simple unless there is an explicit need for what DID offers.
For most pipelines, I believe that a reverse domain name and a UUID4 will be adequate.

Resolving a DID can mean a network lookup, which may go against the desire to be useable offline, so reach for one only if
you genuinely need verifiable identity and can carry the extra complexity. As with cryptographic
signing, the wider machinery around proving identity is a bigger problem we leave
open for now.

## Authorship Metadata Fields

Before getting into how to store this data, here are the fields we propose.
Of these, only `producer` and `version` are required if the schema is applied at all
(`instanceID` may also be required if a dictionary-based storage form is used, where it
serves as the key; see [`instanceID`](#instanceid-maybe-required)).
We strongly encourage `digitalSourceType` as well, as it is the most useful field for
compliance and interoperability.

### `producer` (required)

An identifier for the tool or system that wrote the USD data for this prim.
This is always a tool, not a person, unless they were hand-authoring the files. If Jane modeled something in Blender,
the producer is `org.blender` because Blender is what generated the USD.
Jane goes in `creator`. However, if Jane authors the file manually in a text editor, or via API, they would use a domain specific to themselves as in the examples below.

The key word is _most directly_. If a generative AI model runs inside a DCC tool,
the producer should be the generative AI model, not the DCC tool. The DCC tool may
be recorded separately as its own `AuthorshipAPI` instance (see the
[multi-step pipeline example](#multi-step-ai-pipeline)).

Producer identifiers should use reverse domain notation, the same convention used
by Apple bundle identifiers and Java packages:

```
net.trellis3d.hunyuan3d
org.blender
com.artstation.<username>
```

This helps prevent conflicts between producer names in general, and GenAI model names in
particular, where multiple providers may host the same model with their own customizations.
Domain names are globally unique
and their ownership is publicly verifiable. If you own `trellis3d.net`, nobody else
can legitimately claim `net.trellis3d.*`. Reversing the domain puts the most specific
part last, so you can also namespace within your own tools cleanly
(e.g. `com.mycompany.toolA` vs `com.mycompany.toolB`).
If you do not have a domain, using a well-known identifier like your GitHub username, portfolio host,
or organization is a reasonable fallback.

Note that the instance name in `AuthorshipAPI:hunyuan3d` is just a short namespace
handle to avoid field collisions on the prim. The same model could be hosted by
multiple providers, or two vendors could pick the same short name.
The `producer` field is what tools should actually read to identify the creator.

### `version` (required)

A string identifying the version of the producer that created this prim.

Together, `producer` and `version` identify the specific tool or model that authored the prim.
For example, `net.trellis3d.hunyuan3d` at version `2.1`. This is important, since multiple versions of the same producer could generate very different results.

Some hosted models don't expose a stable version, or quietly swap the deployed model out from
under you without bumping a version string. In those cases, record whatever the service does
give you (a snapshot label, a build hash, an API version) and lean on `created` (the date of the
run) to pin down which iteration of the model was used. A `version` of `unknown` next to a
populated `created` is better than no record at all.

### `digitalSourceType` (strongly encouraged)

A URI or identifier describing the nature of the creative process.
The field name matches the IPTC `digitalSourceType` vocabulary, which we recommend
using via the [IPTC Digital Source Type vocabulary](https://cv.iptc.org/newscodes/digitalsourcetype/).
Other standards bodies and registrars are equally acceptable.
If nothing appropriate exists in any registrar, a plain descriptive string is also fine.

Some common IPTC values that may be useful:

- `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia`: content generated by a trained AI model
- `http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicMedia`: content generated by an algorithm (e.g. photogrammetry, procedural)
- `http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital`: created by a human using digital tools

**This is the field tools should read, across a prim's whole accumulated record set, to decide whether content is AI-generated.**
The schema is intended for more than Generative AI content, so the
mere presence of an `AuthorshipAPI` record tells you nothing on its own about whether AI was
involved. A boolean would be insufficient as there are no good definitions of what constitutes being made by Generative AI versus simple linear regression algorithms or constraint solvers, and IPTC
therefore allows for subtlety in distinction. 

Tools that want to badge or filter AI-generated content should key off `digitalSourceType`, and they should fail safe: **absent any AI
`digitalSourceType` in a prim's accumulated set, don't assume content is AI-generated.** This keeps a human artist's work from getting mislabeled as AI just because they bothered to
record authorship at all. Where nothing in the set says otherwise, we recommend representing the
prim the same as if the source type was unknown, and leaving it to the inspector of the scene to
identify the information rather than providing incorrect assumptions.

"Absent" in the above statement means absent from the
prim's whole accumulated set, including its ancestors, so recording a human record on your own
prim does *not* clear an AI `digitalSourceType` inherited from an ancestor. 

For example, if a parent prim has an AI designation
but a child is authored without that, the child can still be conservatively
considered AI-designated even if its own content is human (see
[Hierarchy and Inheritance](#hierarchy-and-inheritance)). This is a claim about the derived AI
*designation*, not the stored *records*, which stay distinct so attribution can still show the
prim as human work sitting within an AI-generated context. 

We deem this inference the safest to comply with regulations, while still preserving intent. 


### `instanceID` (maybe required)

A unique identifier for this _specific output_ of the producer, meaning the particular result of
one generation or authoring run. We recommend a UUID4 or similar. A DID works here too if you
want the identifier to be resolvable rather than opaque (see [Identifiers](#identifiers)).
Corresponds to `xmpMM:InstanceID` in the XMP / C2PA vocabulary.

It is worth being precise about how this differs from `version`, since the two were easy to mix
up in early discussion:

- `version` identifies the _producer_. For example, version `2.1` of `net.trellis3d.hunyuan3d`.
- `instanceID` identifies this _run's output_, meaning the specific mesh that came out of that
  producer this time. Run the same model with the same prompt again and you get a new
  `instanceID`.

This is useful for generative AI tools (where the same prompt run twice produces
different outputs that need to be distinguishable) and for human-made assets where
you want to track a specific version of a piece of work.

XMP also defines a `DocumentID` that stays stable across edits, copies, and derived versions of
an asset. We don't adopt that one here. Tracking a single identity _across_ modifications over
time is provenance-over-time, which this proposal scopes out (see [Non-Goals](#non-goals)).
`instanceID` records the output of one authoring step, not a lineage that persists through later
changes.

**Important:** this identifier refers to this particular output from the producer, but does not
guarantee a reproducible recipe. A subsequent run of the same AI model with the same inputs
may not produce the same results, as models may introduce their own internal variance. Do not use `instanceID` to imply that the asset
can be regenerated identically.

This identifier should not encode information that could identify the author
outside of the system that created the asset. A UUID4 is good. Your email address
is not. Your social security number is certainly not.

While this identifier is optional, it may be required if we take the form of asset dictionaries where the identifier is the key.


### `creator` (optional)

A list of human-friendly attribution strings. This might include the name of the tool
or service, the name of an individual artist, or a studio name. This is intended for
display purposes. This corresponds to `dc:creator` in the Dublin Core / C2PA vocabulary.

### `description` (optional)

A free-form description of how the prim was created. For AI-generated content, the
`prompt` field is preferred for recording the generation prompt. This field is better
suited for technique notes, reference material, asset history, or other freeform context.
This might also be useful for things like museum assets where we can include the history
of how the asset was acquired. It is technically an unbounded string. We leave editorial
restraint as an exercise for the author.

### `prompt` (optional)

The prompt or instruction used to generate this prim, if applicable. Specific to
AI-generated content. Separating the prompt from `description` allows tools to extract
and display prompts consistently, and accommodates multi-part or DCC-specific prompt
encodings without conflating them with general descriptive text.

If the model supports iterative prompting (e.g. image generators with multiple rounds
of refinement), the full prompt sequence can be recorded here.

### `created` (optional)

An ISO 8601 timestamp recording when this prim was authored, including timezone.
For example: `2025-02-16T12:03:17+01:00`. Corresponds to `xmp:CreateDate` in the
XMP / C2PA vocabulary.

For overrides or modifications applied in a subsequent tool session, this records the
time of that specific authorship step, not the original creation of the asset.

### `usageTerms` (optional)

The license or usage terms for this asset. Corresponds to `xmpRights:UsageTerms` in the
XMP / C2PA vocabulary. We strongly recommend using an
[SPDX identifier](https://spdx.org/licenses/) where possible (e.g. `CC-BY-SA-4.0`,
`MIT`, `LicenseRef-Proprietary`). If your license is not in the SPDX list,
a URL to the license text is also fine, or the full license text.

If no `usageTerms` is provided, no specific license should be assumed.

### `contact` (optional)

One or more contact strings for questions about this asset. This is intentionally
freeform. It could be an email address, a support URL, a licensing page, a phone
number, or anything else that helps someone get in touch about the asset.
It is up to the author or tool to decide what is useful here.
Please be sensible about what you put here; nobody needs your home address in a mesh file.

## Details

### Storage Mechanism

We propose the fields above be stored as a **multiple-apply API schema** called
`AuthorshipAPI`, with the namespace prefix `authorship`. However, we are open to other storage mechanisms as long as we can provide per prim metadata.

We looked at a few options before landing here:

- **Layer metadata**: Using layer metadata (for example a `customLayerData`
  dictionary) as the primary store has been raised as an alternative approach. 
  While it is a reasonable solution, we do not believe it would meet the legal requirements for per prim clarity unless all content pipelines could isolate assets purely in layers. Our thoughts on this are expanded in the [Composition Issues to Consider](#composition-issues-to-consider) section,
  and the dictionary-based options below. It is simpler to
  author, and some fields are conceptually layer-scoped (when did this layer get written,
  by what tool) rather than prim-scoped. 

  We also believe that Layer metadata is less discoverable without inspecting composition, since it is not immediately visible when viewing the composed stage, while other methods presented here would be.
  This make its potentially more costly to locate, and would be harder for humans to reason about without extra tooling.
  The majority of tooling we have examined work on the composed stage where layer metadata is not immediately discoverable without querying all layers first.

  By that same token, layer metadata is more easily lost when flattening layers which is a fairly common operation in pipelines that we have seen, even if done accidentally.

  Similarly on the export side, a lot of DCCs are specifically developed to be single layer exports.
  Asking them to isolate content by authorship domains into layers is a much heavier lift than having them apply it to the prims within the single layer.
  A lot of applications in our ecosystem specifically deal with flattened, packaged USDZ files where flattening is the default behaviour.

- **`assetInfo` (or another dictionary)**: A dictionary-based store is a reasonable
  alternative, and one we considered carefully. It handles multiple authorship records
  fine, as long as it is *nested* rather than flat: a single flat `authorship` dictionary
  can only hold one record, which throws away the central multi-author use case. Instead,
  we would key the dictionary by a record name, mirroring the instance names an applied schema would
  use, so a prim (or a layer) can carry several records at once:

  ```python
  over "Bunny" (
      authorship = {
          dictionary hunyuan3d = {
              string producer = "net.trellis3d.hunyuan3d"
              string version = "2.1"
              string digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
          }
          dictionary blender = {
              string producer = "org.blender"
              string version = "4.2"
              string digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"
          }
      }
  )
  ```

  A variation keys each record by its `instanceID` instead of a short name, which is more
  collision-proof but does make instanceID's required, and might place restrictions on valid characters:

  ```python
  over "Bunny" (
      authorship = {
          dictionary "6530a534-ca8f-487c-8968-0fecd8e717a6" = {
              string producer = "net.trellis3d.hunyuan3d"
              string version = "2.1"
          }
      }
  )
  ```

  Either form could sit on a prim spec or in layer metadata. **For preliminary adoption we
  still recommend the applied API schema over a dictionary**, because an applied schema is
  discoverable through standard USD APIs (`HasAPI<>()`, `GetAppliedSchemas()`) without a
  tool knowing to look inside a custom dictionary, and is easy to strip cleanly if the final
  standard differs from an early adopter's guess.

- **Multiple-apply API schema**: Our preferred approach. It composes correctly
  with USD's composition model, supports multiple simultaneous authorship records cleanly,
  and makes the authorship data queryable through standard USD APIs.
  Crucially, because each instance has its own namespace (e.g. `authorship:hunyuan3d:`
  and `authorship:blender:`), instances from different layers do not clobber each other
  during composition. Both survive and remain independently readable.

- **A single-apply schema**: Would not support the multi-step pipeline case,
  which is one of the most important motivating use cases for USD specifically.

- **Building on C2PA directly**: C2PA is a powerful standard but is designed around
  file-level manifests and cryptographic signing. It does not map naturally to
  prim-level authorship within a composed scene graph. We see these as complementary, not
  competing: C2PA is worth considering as a packaging mechanism alongside this proposal for
  studios that need signed provenance at the asset level (see
  [Relationship to Provenance Systems like C2PA](#relationship-to-provenance-systems-like-c2pa)).
  The barrier to support and the implications on the core USD toolset would be significantly
  higher than for the prim-level schema proposed here.

We are open to a dictionary-based alternative if there is strong community preference,
as long as the format is standardized. The important thing from our perspective is that everyone is reading
and writing the same fields on prims.

### Where the Schema Should Live

In addition to how the schema is represented, we also need to make a decision on where it is best located within the USD libraries.
Since authorship can be placed on any prim, we need this to be in a library that is not highly domain-specific, i.e., `UsdGeom` is perhaps not a good fit since this could also apply to `UsdShade`, etc.

As such, I suggest one of the following as a place to host it:

- **core `usd`** is where the other domain-agnostic API schemas already live, like `CollectionAPI` and `ModelAPI`, the latter of which also owns asset info, which has some similar thinking. I think this is where our TAC meetings had pushed us towards, but we hadn't made a firm stance. The one downside is that this would then need to be specified in a future Core Spec version, but I think that's a minor lift to make.

- **`usdProfiles`** could also be a fit because authorship is somewhat in good company with Profiles, in that they're both proclamations on the content.

- **`usdUI`** is the other likely fit. It only depends on core `usd`, and I think there are aspects of authorship that are largely UI-driven, so this might be a good place to stash it.

- **`usdMedia`** is perhaps also applicable because it includes `AssetPreviewsAPI`, which you also apply to any prim to record descriptive asset metadata like thumbnails and previews. One potential issue is that it depends on `UsdGeom` for `SpatialAudio`. I'm not sure how we feel about requiring `UsdGeom` to be a dependency for everything.

My personal preference would be `usdProfiles` or `usdUI`, but I wanted to provide a few more options in case people felt otherwise.

### When Records Get Shadowed

However authorship is stored, USD composition can occasionally make a record harder to
discover, or let a stronger opinion shadow a weaker one. 

The failure modes for each storage type are described here. None of these are unique to this proposal,
but I wanted to expand upon them since the question has been brought up a few times. It's also worth it
due to the higher scrutiny required for regulatory compliance in this proposal, but I will note that
my (non-lawyer) read of the regulations is that they are all best effort and these cases are generally fringe.

**Applied API schema.** Applied API schemas are recorded in a prim's `apiSchemas` metadata,
which is a token list that composes with list-op semantics. A strong opinion that authors an
**explicit** `apiSchemas` list can shadow an `AuthorshipAPI` application coming from a weaker
layer like a reference. When that happens the authorship _properties_ still compose onto the
prim and stay readable, but the schema no longer counts as applied, so `HasAPI<>()`,
`GetAppliedSchemas()`, and schema fallbacks won't see it. A tool that hunts for authorship by
walking applied schemas would skate right past such a prim. You have to work to hit this:

- The high-level authoring APIs (`UsdPrim::ApplyAPI()` and friends) always author _additive_
  (prepended) list ops, which compose instead of replacing. Getting an explicit list takes
  deliberate Sdf-level authoring.
- The likeliest way to trip it is overlaying the output of `UsdStage::Flatten()` (which emits
  explicit lists) on top of other layers, which is an odd thing to do in the first place. Note
  that a flattened stage is self-consistent on its own; the explicit list it emits still
  contains the `AuthorshipAPI` token, so `HasAPI<>()` works on the flattened result. The hazard
  is only in *recomposing* that flattened layer against others, where its explicit list can
  shadow their contributions.

**Dictionary metadata.** A dictionary-based store (e.g. a custom `authorship` dictionary)
composes by recursive merge rather than list ops, so distinct record-name keys authored in
different layers generally all survive, which is a point in its favor. Since there is no additive-versus-explicit distinction, a strong
opinion that re-authors the same key (or blocks it) simply wins, overriding the weaker record
for that key with no trace that it was there.

**Layer metadata.** If authorship is stored as layer metadata rather than on a prim, it is
dropped or merged by `UsdStage::Flatten()` entirely (see
[Storage Mechanism](#storage-mechanism)). This is the most severe version of the problem, and
one of the reasons we recommend against it.

### Choosing a Producer

The `producer` field should name the most proximate creator of the prim.

If a generative AI model runs inside Blender, you would list the AI model as the
producer for its authorship record. Blender might be listed as the producer for a
separate `AuthorshipAPI` instance representing the step where a human used Blender
to review or modify the result. These are distinct steps in the pipeline and deserve
distinct records.

A few practical guidelines:

- A plugin should attribute the underlying algorithm, not the host application,
  unless the host application itself is creating the content.
- A studio pipeline step (e.g. a procedural rigging tool) is itself a valid producer
  even if it is not a commercial product.
- A human artist is usually not a `producer`. The tool they used to generate the USD is, unless they literally manually wrote the USD (power to them if they're writing whole assets manually).
  The human usually goes in `creator`.

**Instance name collisions.** If the same DCC is used to author multiple layers that
will be composed together on the same prim (for example, a geometry layer and a shading
layer both produced by Blender), use distinct instance names to avoid one set of
properties shadowing the other during composition, for example `blender_geo` and
`blender_shading`. If the authorship is identical across both layers (same tool, same
version, same contributor), it is also acceptable to reuse the same instance name and
let the properties compose normally as long as it meets regulatory needs.

### Hierarchy and Inheritance

USD's composition model naturally raises the question of what it means for a prim
to have authorship information when its children do not.

Our convention is:

**A prim's children accumulate the authorship of their ancestors. A child may add its
own records, but it does not erase the records above it.**

In an attempt to remove ambiguity, I've tried to include some clarifying statements here:

- **Inheritance here refers to hierarchical propagation, not class inheritance.** While the name conflict is unfortunate,
  this still feels like an intuitive term to use, and one I think we already use successfully in many contexts.
- **Records accumulate as a set, and source types propagate downward.** Walking up
  the hierarchy yields a *set* of records, each keeping its own `digitalSourceType` and
  other fields. For attribution and display, keep them distinct: a hand-modeled child under
  an AI-authored ancestor carries both records (`[ancestor: AI, self: human]`), and a tool
  should surface that mix rather than flattening it into a single label. We treat authorship records as hierarchy markers that "color" the hierarchy below them.
  This means that if a parent is AI-generated, its children inherit this coloring even if they specify otherwise.
  This is not unique to AI-generated source types, as the accumulation is meant to reveal how that point in the hierarchy came to be.
  For example, referencing a human-made model into an AI-populated scene would still color that reference as AI, even if it carries its own authorship metadata, since the way you arrived at that hierarchy layout was AI-populated to begin with.
  However, this would not back-propagate into the source of the reference. 

- **It flows downward, including across references.** Authorship authored on a referenced
  asset (see [Composition Issues to Consider](#composition-issues-to-consider)) lands on the
  referencing prim through normal composition and then flows down to that prim's
  descendants in the consuming scene. The one gap is *upward*: a record authored only on
  an ancestor of a reference target does not travel across the reference (composition
  pulls the target subtree, not the target's ancestors). We address that in the
  references section by recommending you stamp the referenceable boundary. 
  Again, the regulations are best effort, and we cannot account for all methods of use in USD itself. 
  As with several things in USD, some parts are left to the dominion of the creators and pipeline. 
  We just aim to make it as intuitive as possible for the most common cases.

Because inheritance is a display convention rather than authored data, we lightly suggest
that tools give explicit and inherited records a distinct treatment of their choosing (a
different icon, muted styling, a tooltip) so a user can tell what a prim declared for
itself from what it picked up from its context. The right treatment depends on the
application, so we do not prescribe one.

We recommend that OpenUSD provide an API to help with observing this accumulation, but without providing opinions on the data within.
This could be a convenience API added after the proposal itself lands.

### Composition Issues to Consider

Because authorship lives on prims, it travels through composition the same way any other
prim data does. This mostly does the right thing, but there are a couple of composition
edges worth understanding. When a scene references an asset, the referenced prim brings its
authorship records along, they land on the referencing prim, and (per the convention
above) they flow down to that prim's descendants in the consuming scene. 
This should therefore (by default) satisfy many of the regulatory concerns, where referencing in a GenAI-produced asset carries that GenAI record with it.

```python
# rock_asset.usd  --  a published asset with authorship on its defaultPrim
#usda 1.0
(
    defaultPrim = "RockLarge"
)

def Xform "RockLarge" (
    prepend apiSchemas = ["AuthorshipAPI:rockmaker"]
) {
    uniform string authorship:rockmaker:producer = "com.example.rocktool"
    uniform string authorship:rockmaker:version = "3.0"
    uniform string authorship:rockmaker:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"

    def Mesh "Geom" {}
}
```

```python
# scene.usd  --  references the asset; Rock_1 now carries the rockmaker record
#usda 1.0

def "World" (
    prepend apiSchemas = ["AuthorshipAPI:layout"]
) {
    uniform string authorship:layout:producer = "com.example.layouttool"
    uniform string authorship:layout:version = "1.0"
    uniform string authorship:layout:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"

    def "Rock_1" (references = @rock_asset.usd@) {}
}
```

Here `/World/Rock_1` composes in the `rockmaker` authorship from the referenced asset,
and a tool inspecting it sees both the GenAI `rockmaker` record (from the reference) and
the human `layout` record (from `World`, by inheritance). Nothing special is required.

There is one case to be careful of. Composition pulls a reference *target* and its
subtree, not the target's *ancestors*. So if you author authorship only on an ancestor
of the prim you reference (for example on a parent `class`, and then reference one of its
children directly), that ancestor's record will not travel across the reference, and it
will not be recoverable after `UsdStage::Flatten()` either.

We recommend two things to avoid this:

1. **Stamp authorship at every referenceable boundary.** Put the record on the prim that
   is actually meant to be referenced, which in most pipelines is the asset's
   `defaultPrim`, as well as any sub-prim you expect to be referenced on its own. Do not
   rely on an ancestor's record reaching a referenced descendant.
2. **When you need an ancestor's record, walk composition.** If a tool genuinely needs to
   recover a record that lived on an ancestor of a reference target, it can walk the
   prim's `GetPrimStack()` or composition graph to find it. 

In the sample scenes that we've analyzed (our own content and content provided by third parties), these issues are not that common. We recommend avoiding these problematic patterns for convenience sake when it comes to choosing where to put the authorship data, but it is something that USD's design allows for as an escape hatch. 

**Namespace edits and `relocates`.** Another variant of the same issue appears with `relocates` (and namespace editing or
reparenting in general). Consider these examples adapted from Matt:

```python
# terrain.usda
#usda 1.0
(
    defaultPrim = "terrain"
)

def Xform "terrain" (
    prepend apiSchemas = ["AuthorshipAPI:terrain"]
) {
    uniform string authorship:terrain:producer = "com.example.terraintool"
    uniform string authorship:terrain:version = "1.0"

    def Xform "rock" {}   # no authorship of its own; relies on inheriting from `terrain`
}
```

```python
# rockslide.usda
#usda 1.0
(
    relocates = {</terrain/rock> : </rockslide/rock>}
)

def Xform "rockslide" (
    prepend apiSchemas = ["AuthorshipAPI:rockslide"]
) {
    uniform string authorship:rockslide:producer = "com.example.rockslidetool"
    uniform string authorship:rockslide:version = "1.0"
}

def Xform "terrain" (references = @./terrain.usda@) {}
```

The `rock` prim carried no record of its own and relied on inheriting from its namespace
parent `terrain`. The `relocates` moves `rock` out from under `terrain` and under
`rockslide`, so by the inheritance convention it now inherits the `rockslide` record
instead of the `terrain` one. The original attribution is silently swapped for a
different one, and this survives into a flattened result.

While this is also a legitimate case one might run into, I do think this is rare and has the same caveats as referencing above.

It is also worth noting that `relocates` is an advanced, deliberate operation, typically
authored by pipeline engineers who are well positioned to also ensure the prims they move
carry their own authorship. That does not make the limitation go away, but it does keep it
in a corner of the ecosystem that is already handling composition with care.

**Instancing.** Native instances (`instanceable = true`) draw the prims beneath the instance
boundary from a shared prototype, so authorship authored *inside* a prototype is shared across
every instance and cannot vary per instance. Authorship on the instanceable prim itself (the
instance root) is a normal per-prim opinion and behaves as expected; it is only below the
instance boundary that per-instance attribution is not expressible. `UsdGeomPointInstancer` is
more extreme: its instances are not prims at all but encoded in arrays, so authorship can only
live on the `PointInstancer` prim or on its prototype prims, not on an individual point
instance. We think this is acceptable, as instanced content generally shares an origin, so
shared authorship is usually right. We take no opinion on how tools should surface authorship
for instanced content, or whether a per-instance need ever arises.

**Asset-level and layer-scoped authorship.** Some authorship is naturally about a whole asset or a whole layer rather than one deep
prim: "this file was produced by tool X." Rather than store this as layer metadata (see
[Storage Mechanism](#storage-mechanism) for why we steer away from that), we strongly
recommend authoring it on the layer's `defaultPrim`. This follows other recommendations for asset level metadata in USD as USD moves away from layer metadata.

If a layer has no obvious prim to carry the record (for example a generative tool that
emits an otherwise-empty layer), we recommend creating a prim to hold it rather than
falling back to layer metadata.

If a layer only sublayers or references other content and authors no prims of its own
(for example an AI tool whose contribution is *combining* other layers, not generating
geometry), we recommend authoring an `over` on the `defaultPrim` that the composition
produces, and being clear in that record that the contribution was structural
combination rather than content generation. This keeps a "the AI assembled this scene"
record cleanly distinct from a "the AI generated this geometry" record.

### Import, Export and Round-Tripping

In most pipelines a USD layer is the result of an
export from a DCC or other application, while composed stages are what get read back into the DCC. This proposal
standardizes how authorship is *stored in USD*, but how a given tool maps that to and from its
own internal representation is inherently tool-specific and outside the scope of this proposal to define. A few
expectations are still worth stating.

- **On export**, a tool records authorship on the prims it emits. If the tool has its own
  notion of who or what produced content, it maps that onto `AuthorshipAPI` records on the
  corresponding prims, and onto the `defaultPrim` for anything that describes the asset as
  a whole (see [Composition Issues to Consider](#composition-issues-to-consider)).
- **On import**, a tool reads authorship off the prims (and their ancestors, per the
  inheritance convention) and maps it back to whatever native representation it has. A tool
  that has no native concept of authorship should, where practical, preserve the records
  opaquely so they survive a round trip rather than being dropped on the next export.
- **Tools without a hierarchical scene graph** can still take part. Not every application
  models a full prim hierarchy internally, but such a tool can still consolidate the information on import. On export a tool still emits prims, and it
  can attach authorship to those prims or, at minimum, to the `defaultPrim`. 

We've mocked up a few pipelines within several custom and off-the-shelf tools and find this to work well.
Again, my (non-lawyer) read of the regulations is that they are best-effort, and the nature of DCC pipelines is historically somewhat lossy. 
We try and focus on USD itself to maximize the richness of the data expressed.

### Viewer and Renderer Responsibility

How authorship information is surfaced to end users is entirely up to individual applications,
and we intentionally do not prescribe this. A viewer might choose to show a badge on
AI-generated content, or include other visual treatments.

Similarly, when a USD scene is rendered to an image or video, any content labeling
requirements from the regulations above may need to carry through to the rendered output.
That is outside the scope of this proposal, but the authorship data in the scene graph
can serve as the source of truth for downstream labeling tools.

## Examples

### AI-Generated Mesh

A mesh generated by a single generative AI tool.

```python
def Mesh "Bunny" (
    prepend apiSchemas = ["AuthorshipAPI:hunyuan3d"]
) {
    uniform string authorship:hunyuan3d:producer = "net.trellis3d.hunyuan3d"
    uniform string authorship:hunyuan3d:version = "2.1"
    uniform string authorship:hunyuan3d:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string[] authorship:hunyuan3d:creator = ["Trellis Hunyuan 3D", "John Doe"]
    uniform string authorship:hunyuan3d:prompt = "A fluffy bunny"
    uniform string authorship:hunyuan3d:created = "2025-02-16T12:03:17+01:00"
    uniform string authorship:hunyuan3d:instanceID = "6530a534-ca8f-487c-8968-0fecd8e717a6"
    uniform string authorship:hunyuan3d:usageTerms = "CC-BY-SA-4.0"
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
    uniform string authorship:hunyuan3d:producer = "net.trellis3d.hunyuan3d"
    uniform string authorship:hunyuan3d:version = "2.1"
    uniform string authorship:hunyuan3d:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    uniform string authorship:hunyuan3d:prompt = "A fluffy bunny"

    # A human artist who cleaned up the mesh in Blender afterwards
    uniform string authorship:blender:producer = "org.blender"
    uniform string authorship:blender:version = "4.2"
    uniform string authorship:blender:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"
    uniform string[] authorship:blender:creator = ["Jane Doe"]
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
    uniform string authorship:jane:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"
    uniform string[] authorship:jane:creator = ["Jane Doe"]
    uniform string authorship:jane:usageTerms = "CC-BY-4.0"
    uniform string[] authorship:jane:contact = ["jane@example.com"]
}
```

### Photogrammetry Scan

A prop captured using photogrammetry which is therefore neither human generated nor created with Generative AI.

```python
def Mesh "ScannedProp" (
    prepend apiSchemas = ["AuthorshipAPI:rcapture"]
) {
    uniform string authorship:rcapture:producer = "com.capturingreality.rcapture"
    uniform string authorship:rcapture:version = "1.4"
    uniform string authorship:rcapture:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicMedia"
    uniform string[] authorship:rcapture:creator = ["Acme Studio"]
    uniform string authorship:rcapture:created = "2025-06-01T09:00:00+00:00"
}
```

### Mixed Authorship Across a Hierarchy

An AI-authored group with a hand-modeled child, illustrating accumulation and the
downward propagation of the AI designation (see
[Hierarchy and Inheritance](#hierarchy-and-inheritance)).

```python
def Xform "Set" (
    prepend apiSchemas = ["AuthorshipAPI:worldgen"]
) {
    # The whole set was laid out by a generative AI tool.
    uniform string authorship:worldgen:producer = "com.example.worldgen"
    uniform string authorship:worldgen:version = "0.9"
    uniform string authorship:worldgen:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"

    def Mesh "HeroProp" (
        prepend apiSchemas = ["AuthorshipAPI:jane"]
    ) {
        # A human artist modeled this specific prop by hand.
        uniform string authorship:jane:producer = "org.blender"
        uniform string authorship:jane:version = "4.2"
        uniform string authorship:jane:digitalSourceType = "http://cv.iptc.org/newscodes/digitalsourcetype/humanCreatedDigital"
        uniform string[] authorship:jane:creator = ["Jane Doe"]
    }
}
```

Walking authorship for `/Set/HeroProp` yields the accumulated set as something like
`[worldgen: AI (inherited), jane: human (own)]`. A tool displaying attribution should show
both, ideally distinguishing the inherited `worldgen` record from the prim's own `jane`
record. For AI disclosure, `HeroProp` is conservatively considered to carry the AI
designation propagated from `Set`, even though its own content is human-authored: it is
human work sitting within an AI-generated context, not a reason to relabel Jane's mesh as
AI-generated in the attribution sense.

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
        doc = """An identifier for the tool or system most directly responsible for
        creating this prim. This is a tool, not a person; people go in creator.
        Should be the most specific producer in the pipeline.
        For example, if a generative AI model runs inside a DCC tool, this should name
        the AI model. Reverse domain notation is recommended:
        e.g. net.trellis3d.hunyuan3d, org.blender, com.artstation.janedoe."""
    )

    uniform string version (
        doc = """A string identifying the version of the producer."""
    )

    uniform string digitalSourceType (
        doc = """A URI or identifier describing the nature of the creative process.
        We recommend using the IPTC Digital Source Type vocabulary at
        https://cv.iptc.org/newscodes/digitalsourcetype/ , though other registrars
        are acceptable. Corresponds to Iptc4xmpExt:DigitalSourceType in the IPTC vocabulary."""
    )

    uniform string[] creator (
        doc = """An optional human-friendly list of attributions for display purposes.
        May include tool names, service names, and individual contributors.
        Corresponds to dc:creator in the Dublin Core / C2PA vocabulary."""
    )

    uniform string description (
        doc = """An optional free-form description of how this prim was created.
        For AI-generated content, prefer the prompt field for the generation prompt.
        Use this field for technique notes, reference material, or asset history."""
    )

    uniform string prompt (
        doc = """The prompt or instruction used to generate this prim, if applicable.
        Specific to AI-generated content. Separating the prompt from description
        allows tools to extract prompts consistently and accommodates multi-part or
        DCC-specific prompt encodings."""
    )

    uniform string created (
        doc = """An ISO 8601 timestamp including date, time, and timezone.
        For example: 2025-02-16T12:03:17+01:00. Corresponds to xmp:CreateDate in the XMP / C2PA vocabulary.
        Records when this authorship step occurred, not necessarily the original
        creation of the underlying geometry."""
    )

    uniform string instanceID (
        doc = """A unique identifier for this specific output of the producer.
        A UUID4 is recommended. Should not encode information that could personally
        identify the author outside of the creating system.
        Corresponds to xmpMM:InstanceID in the XMP / C2PA vocabulary. Note: this does not imply the asset
        can be reproduced identically from the same inputs."""
    )

    uniform string usageTerms (
        doc = """An optional license or usage terms for this asset. SPDX identifiers are
        strongly recommended (https://spdx.org/licenses/). A URL is also acceptable
        for non-SPDX licenses. If absent, no specific license should be assumed.
        Corresponds to xmpRights:UsageTerms in the XMP / C2PA vocabulary."""
    )

    uniform string[] contact (
        doc = """Optional contact information for questions about this asset."""
    )
}
```

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

## Acknowledgments

This proposal has been meaningfully improved by community feedback, and it will continue to be. 
In particular, thanks to members of the AOUSD TAC like **Matt, Spiff, Nick and Aaron** for their comprehensive questions and consideration of various cases that needed more clarity.
Also thank you for suggestions from **Nick and Leonard** for aligning the fields closer to other existing standards.

## Closing Notes

Having a shared standard for authorship in USD feels genuinely overdue, both for the AI
content compliance use case that is motivating a lot of interest right now, and for the
broader goal of just being able to know where your content came from.

The fact that USD is used across the entire industry, with complex multi-vendor pipelines
and scene composition, makes this both more important and more interesting to solve than
it is for simpler formats. We think the multiple-apply schema approach handles that
complexity well.

This work also connects to a broader structural problem: how attribution, ownership, and
dissemination rights flow when assets are recombined across vendor and pipeline boundaries.
A parallel in-flight proposal on IP protection in USD
([PR #107](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/107)) addresses an
adjacent slice of this. This proposal does not need to wait on that broader discussion, but
downstream tooling benefits from knowing the two are related.

We hope this can be a useful starting point for a good discussion, and we genuinely
welcome feedback on the schema, the field names, and the storage approach.




