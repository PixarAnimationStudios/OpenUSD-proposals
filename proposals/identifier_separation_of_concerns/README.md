# Separation of Concerns for Identifiers in USD

Copyright &copy; 2026, NVIDIA Corporation, version 0.1 (DRAFT)

Aaron Luk

## Contents

- [Introduction](#introduction)
- [Motivation](#motivation)
  - [USD identifiers today](#usd-identifiers-today)
  - [The expanding ecosystem](#the-expanding-ecosystem)
- [Problem statement](#problem-statement)
  - [Two distinct roles for identifiers](#two-distinct-roles-for-identifiers)
  - [Why this matters now](#why-this-matters-now)
- [Key questions](#key-questions)
  - [Instance identity vs. source identity](#instance-identity-vs-source-identity)
  - [Single value vs. metadata package](#single-value-vs-metadata-package)
- [Existing mechanisms in USD](#existing-mechanisms-in-usd)
  - [assetInfo](#assetinfo)
  - [displayName](#displayname)
  - [customData and customLayerData](#customdata-and-customlayerdata)
- [Industry use cases](#industry-use-cases)
  - [Architecture, Engineering, Construction, and Operations (AECO)](#architecture-engineering-construction-and-operations-aeco)
  - [Product Lifecycle Management (PLM) and Manufacturing](#product-lifecycle-management-plm-and-manufacturing)
  - [Media and Entertainment (M&E)](#media-and-entertainment-me)
- [Design considerations](#design-considerations)
  - [Principles](#principles)
  - [Open questions for discussion](#open-questions-for-discussion)
- [Relationship to other proposals](#relationship-to-other-proposals)
- [Next steps](#next-steps)
- [Appendix A: Provenance and AI-Assisted Drafting](#appendix-a-provenance-and-ai-assisted-drafting)

## Introduction

As OpenUSD adoption grows across industries, a recurring tension has emerged
between the identifiers that USD uses internally for scene composition and
hierarchy navigation, and the identifiers that external systems use to track
assets, components, and objects. These two kinds of identifiers serve
fundamentally different purposes, yet there is no clear, standardized mechanism
in USD to represent and manage external identifiers alongside USD's namespace
paths.

This proposal articulates the problem, surveys existing mechanisms that
partially address it, and identifies the key questions that the community must
align on before converging on a solution. The goal is to establish a shared
conceptual framework across industries -- AECO, manufacturing, PLM, M&E, and
others -- so that any eventual solution serves the broadest possible set of
stakeholders.

## Motivation

### USD identifiers today

In USD, every prim is addressed by a **namespace path** -- a hierarchical,
textual identifier such as `/World/Building/Floor1/Room101`. These paths are
the backbone of USD's composition engine: references, payloads, inherits,
variants, and overrides all bind to prims by their namespace paths.

USD's namespace paths are:

- **Unique per instance** within a composed stage.
- **Structural** -- they encode the scene hierarchy and are used for traversal,
  queries, and composition arc targeting.
- **Governed by grammar rules** -- identifiers must conform to syntactic
  constraints (currently the XID specification as of OpenUSD 24.03).
- **The primary key** for binding opinions across layers.

USD intentionally avoids GUIDs as primary identifiers. As stated in the
[OpenUSD introduction](https://openusd.org/release/intro.html#no-guids):

> USD uses a textual, hierarchical namespace to identify its data, which means
> it is "namespace paths" by which overrides bind to their defining
> prims/properties. [...] We have decided that for us, the cost of occasional
> "namespace fix-up" operations run over a collection of assets is worth paying
> for the ease of asset construction and aggregation, and readable text asset
> representations that we get from [namespace paths].

This is a deliberate and well-reasoned design choice. The question this
proposal raises is not whether USD should change this design, but rather how
USD should accommodate the *additional* identifiers that external systems need
to carry alongside the namespace path.

### The expanding ecosystem

USD was born in the visual effects and animation industry, where scene
hierarchies tend to originate from digital content creation (DCC) tools with
naming conventions that align well with USD's identifier grammar. As USD
expands into new industries, it increasingly encounters data originating from
systems with their own identification schemes:

- **AECO tools** (Revit, ArchiCAD, IFC) use identifiers like GUIDs, room
  numbers (`1001`), classification codes with slashes and hyphens
  (`BB/500`, `Ss_25_10_30`), and revision-stamped names.
- **PLM systems** (Teamcenter, Windchill, 3DExperience) track parts by
  alphanumeric part numbers (`A-0000-12345`), revision identifiers, and
  multi-attribute metadata packages.
- **Manufacturing and ECAD/MCAD workflows** use component designators with
  leading digits and medial hyphens (`1N4148`, `R-101`).
- **GIS and infrastructure tools** use identifiers tied to geospatial
  coordinate systems or regulatory codes.
- **Game engines and M&E pipelines** use asset management systems with their
  own unique IDs, tags, and versioning metadata.

In all these cases, the external identifier is *not* an alternative name for
the same prim -- it identifies something conceptually different: the **source
asset, component, or entity** in the originating system, which may be
instantiated multiple times in a USD stage, or may carry metadata that has no
equivalent in the USD namespace.

## Problem statement

### Two distinct roles for identifiers

The core observation is that there are two fundamentally different roles an
identifier can play in a USD-based workflow:

| | **USD namespace identifier** | **Source / external identifier** |
|---|---|---|
| **Purpose** | Address a prim in the composed stage | Identify an asset, component, or entity in an external system |
| **Uniqueness** | Unique per prim instance in the stage | May be shared across multiple prim instances (e.g., multiple placements of the same part) |
| **Governed by** | USD prim name grammar (XID rules) | External system conventions (may include characters invalid in USD) |
| **Used for** | Composition, hierarchy traversal, overrides | Asset tracking, classification, BOM generation, regulatory compliance, cross-system linking |
| **Persistence** | Tied to the prim's position in the namespace | Tied to the source entity; should survive namespace edits |
| **Multiplicity** | Exactly one per prim | Potentially many -- one per external system the entity participates in |

Today, there is no standardized place in USD to express the right-hand column.
Users work around this through ad-hoc conventions: encoding external
identifiers in prim names (losing characters to grammar restrictions), storing
them in `customData` (losing discoverability and interoperability), or using
`displayName` (conflating display concerns with identification).

### Why this matters now

Without a clear separation of concerns:

1. **Data loss on ingest.** External identifiers that contain characters
   invalid in USD prim names (leading digits, hyphens, slashes, GUIDs) are
   either mutilated or lost when data enters USD. Round-tripping back to the
   source system becomes unreliable.

2. **Ad-hoc solutions fragment the ecosystem.** Each integrator invents its own
   convention for storing external identifiers, making cross-tool
   interoperability difficult. A Revit-to-USD pipeline and a
   Teamcenter-to-USD pipeline may store their source identifiers in
   incompatible ways.

3. **Conflation of concerns.** When prim names are forced to double as
   external identifiers, the USD namespace becomes polluted with naming
   constraints from external systems, or external systems lose fidelity when
   their identifiers are forced into USD grammar.

4. **Missed opportunities for tooling.** If source identifiers were
   discoverable through a standard mechanism, tools could provide cross-system
   linking, BOM generation, classification lookups, and regulatory compliance
   checks without requiring knowledge of each pipeline's ad-hoc conventions.

5. **The `displayName` migration is already underway.** The
   [UI Hints](../ui-hints/README.md) work has been
   [implemented in OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD/tree/dev/pxr/usd/usdUI),
   migrating `displayName` from a top-level metadata field on `UsdObject` into
   a `uiHints` dictionary and cementing it as a *presentation-only* concern.
   The new access API lives in
   [`UsdUIObjectHints`](https://openusd.org/dev/api/class_usd_u_i_object_hints.html),
   and the existing top-level `displayName` get/set API in `Usd` and `Sdf` is
   on a deprecation path toward eventual removal. Any pipelines currently using
   `displayName` as a workaround to carry source identifiers are now facing
   both **API breakage** (deprecated accessors) and **content migration costs**
   (existing assets authored with the old field location). This is not a future
   risk -- it is an active change. The window to establish a proper,
   purpose-built mechanism for source identifiers is closing as the community
   accumulates more technical debt on `displayName`-as-identifier workarounds
   that will need to be migrated twice: once away from the deprecated field
   location, and again when a standardized source identifier mechanism is
   eventually adopted.

## Key questions

Before proposing a specific solution, the community should align on two
foundational questions.

### Instance identity vs. source identity

A USD prim's namespace path uniquely identifies one *instance* -- a specific
occurrence of something in the scene. But many workflows also need to express
which *source asset or entity* that instance represents.

Consider a building model where the same door type is placed in 30 locations.
Each placement is a distinct prim with a unique namespace path, but they all
share a common source identity: the door type's catalog number, IFC GUID, or
PLM part number.

**Question:** Should the proposed mechanism primarily support source identity
(shared across instances), instance identity in external systems (unique per
placement), or both?

The answer likely varies by domain. In manufacturing, a part number (source
identity) is shared across instances but each physical part may also have a
serial number (instance identity). Both are useful; a flexible mechanism should
accommodate either.

### Single value vs. metadata package

Some external identification schemes are simple strings -- a GUID, a part
number, a classification code. Others are richer: a dictionary of metadata
that together constitutes the identity in the external system, potentially
including identifiers from multiple systems simultaneously.

For example, a single structural column in a building might carry:

| System         | Identifier type | Value               |
|----------------|----------------|---------------------|
| IFC            | GlobalId       | `2O2Fr$t4X7Zf8NOew3FNr2` |
| Revit          | ElementId      | `847562`            |
| Uniclass 2015  | Classification | `Ss_25_10_30`       |
| Revit          | Mark           | `C-14`              |

<!-- 
  - For Uniclass 2015 codes, see: [Uniclass 2015 - Table Ss: Structure](https://www.thenbs.com/our-tools/uniclass/ss_25_10_30) for example codes.
  - The "Project"/"Mark" example was originally included to demonstrate a project-specific identifier. In AECO (Architecture, Engineering, Construction, and Operations) workflows, "Mark" is a commonly used parameter (e.g., in Autodesk Revit) for an instance or tag number. "Project" is not a standardized system like IFC or Revit, so "Revit / Mark" better reflects actual usage, where the "Mark" parameter is an identifier for individual elements.
-->

**Question:** Should the mechanism be a single identifier string, a typed
identifier with a system qualifier, or a dictionary that can hold multiple
identifiers from different systems?

`assetInfo` already exists as a dictionary on USD model prims and may provide a
starting point, but the question is whether it is the right vehicle or whether
a new, more general mechanism is needed.

## Existing mechanisms in USD

Several existing mechanisms partially address the need for external
identifiers. Understanding their strengths and limitations is essential to
deciding whether to extend one or introduce something new.

### assetInfo

`assetInfo` is a composed dictionary available through `UsdModelAPI` on prims
that represent the root of a *model* (as defined by USD's `Kind` hierarchy).
It provides:

- **`identifier`** (`SdfAssetPath`) -- the asset's resolvable path.
- **`name`** (`string`) -- the asset's name, suitable for database queries.
- **`version`** (`string`) -- the asset's resolved version.
- **`payloadAssetDependencies`** (`SdfAssetPath[]`) -- dependencies inside the
  payload.

`assetInfo` is composed element-wise and is nestable, which makes it well-suited
for model-level asset management metadata. However:

- It is designed around USD's own concept of an asset (a referenceable layer or
  package), not around external system identifiers.
- It lives on model roots via `UsdModelAPI`, which limits its applicability to
  prims that participate in the `Kind` hierarchy. Many real-world objects that
  need source identifiers (individual rooms, structural members, electrical
  components) are not model roots.
- Its schema is fixed around a small set of known keys. Extending it to hold
  arbitrary external identifiers from multiple systems would require either
  changes to the schema or reliance on the dictionary's freeform nature,
  which reduces discoverability.

`assetInfo` may be part of the solution, but it was not designed for the
breadth of external identification needs emerging from cross-industry adoption.

### displayName

`displayName` is metadata available on prim specs and property specs. It
provides a human-readable name that can contain any UTF-8 string, including
characters not valid in prim names.

`displayName` is useful for presentation but is semantically a *display*
concern, not an *identification* concern. Using it to carry source identifiers
conflates two purposes: the name shown to a user in a UI may differ from the
identifier used to link back to a source system. A structural column's display
name might be "Column C-14 (Level 3)" while its source identifier is the
IFC GUID `2O2Fr$t4X7Zf8NOew3FNr2`.

The [UI Hints](../ui-hints/README.md) work, now
[implemented in OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD/tree/dev/pxr/usd/usdUI),
has migrated `displayName` into a `uiHints` dictionary alongside other
presentation-only metadata like `hidden` and `displayGroup`. This makes
explicit what was always implicit: `displayName` is a UI concern. The new
access API is
[`UsdUIObjectHints`](https://openusd.org/dev/api/class_usd_u_i_object_hints.html),
and the old top-level accessors are deprecated. Pipelines that have been using
`displayName` as a carrier for source identifiers now face an active migration
-- and the question is whether they migrate to yet another ad-hoc convention,
or to a standardized source identifier mechanism.

### customData and customLayerData

`customData` is a freeform dictionary available on any prim or property.
`customLayerData` is the layer-level equivalent. Both are intended for
pipeline-specific or ad-hoc metadata.

While `customData` can technically store external identifiers, it provides no
standardization: every pipeline must agree on key names, and tools have no way
to discover or interpret source identifiers without prior knowledge of the
convention used. This is precisely the interoperability gap that a standardized
mechanism would close.

## Industry use cases

The following examples illustrate the problem across industries. They are not
exhaustive but are intended to show that the need for separating USD namespace
identifiers from source identifiers is broad and cross-cutting.

### Architecture, Engineering, Construction, and Operations (AECO)

AECO data originates from tools like Autodesk Revit, Graphisoft ArchiCAD,
Bentley MicroStation, and the open IFC standard. Naming conventions in AECO
frequently conflict with USD's prim name grammar:

- **Room numbers** are often purely numeric (e.g., `1001`), which cannot serve
  as a prim name starting character under pre-24.03 rules and still cannot
  serve as identifiers under current XID rules.
- **Classification codes** use slashes and hyphens as semantic delimiters
  (e.g., Uniclass `Ss_25_10_30`, OmniClass `23-13 11 00`).
- **IFC GUIDs** are 22-character base64-encoded strings that uniquely identify
  building elements across the lifecycle of a project.
- **Revision workflows** produce new identifiers with each design iteration;
  the ability to derive revision information from the identifier is a
  requirement, not a convenience.

The AOUSD AECO Interest Group has documented these requirements in detail. A key insight from that work is the distinction between the prim
name (which may be a transcoded or generated valid identifier) and the
**source name** from the originating system, which must be preserved exactly
for round-trip fidelity.

### Product Lifecycle Management (PLM) and Manufacturing

PLM systems are the backbone of manufacturing workflows. They assign stable
identifiers -- part numbers, revision codes, serial numbers -- that must
persist across the lifecycle of a physical product and its digital twin.

- A **part number** like `A-0000-12345-Rev.C` identifies the *design* of a
  component. Multiple instances of that component in an assembly share this
  identifier.
- A **serial number** like `SN-2025-00847` identifies a specific *physical
  instance* of that component.
- A **BOM (Bill of Materials)** is generated by traversing an assembly and
  collecting part numbers -- a workflow that requires source identifiers to be
  discoverable and unambiguous.

If these identifiers are encoded into prim names, characters like hyphens and
periods are lost or transcoded, making BOM generation from the USD stage
unreliable without an additional decoding step.

### Media and Entertainment (M&E)

Even in USD's original domain, asset management systems assign identifiers that
differ from prim namespace paths:

- **Asset management database IDs** track versions, approvals, and
  dependencies at a granularity that may not align with USD's namespace
  hierarchy.
- **Shot and sequence identifiers** follow studio-specific conventions that may
  include characters not valid in prim names.
- **Published asset versions** are tracked by systems (e.g., ShotGrid, ftrack)
  that assign their own unique identifiers alongside the USD asset path.

While `assetInfo` covers some of these cases at the model level, it does not
address identification at finer granularities (individual props, lights,
materials) or across multiple asset management systems.

## Design considerations

This section does not propose a solution but outlines principles and open
questions to guide the community toward one.

### Principles

1. **Separation of concerns.** USD namespace paths and external source
   identifiers serve different purposes. They should be stored and accessed
   through distinct mechanisms, even if they sometimes carry the same value.

2. **Industry agnosticism.** The mechanism should not be specific to any one
   industry's identifier scheme. It should be flexible enough to carry IFC
   GUIDs, PLM part numbers, M&E asset database IDs, and schemes not yet
   envisioned.

3. **Composability.** External identifiers should participate in USD's
   composition model in a well-defined way. It should be clear how source
   identifiers are resolved when a prim is referenced, inherited, or
   specialized.

4. **Discoverability.** Tools should be able to discover that a prim carries
   source identifiers without prior knowledge of a pipeline-specific
   convention. This argues for a schema-based approach rather than ad-hoc
   `customData` usage.

5. **Minimal disruption.** The solution should build on USD's existing
   strengths. It should not require fundamental changes to the composition
   engine or namespace path semantics.

6. **Round-trip fidelity.** Source identifiers should survive a round-trip
   through USD without loss, even if the characters they contain are not valid
   in USD prim names.

### Open questions for discussion

1. **Extend `assetInfo` or introduce a new mechanism?**
   `assetInfo` already provides a composed dictionary for asset metadata. Could
   it be extended with standardized keys for source identifiers from multiple
   systems? Or would overloading `assetInfo` conflate USD asset identity with
   external system identity?

2. **Schema or metadata?**
   Should source identifiers be expressed as an applied API schema (like
   `SemanticsAPI`), as metadata (like `assetInfo`), or as properties? Each has
   different implications for composition, queryability, and performance.

3. **Scope: model roots only, or any prim?**
   `assetInfo` is scoped to model roots. External identifiers are needed on
   prims at all levels of the hierarchy -- individual rooms, structural
   members, electrical components, fasteners. The mechanism must not be
   artificially limited to model roots.

4. **Namespacing of identifiers.**
   If a prim carries identifiers from multiple external systems, how should
   they be organized? A flat dictionary with well-known keys? A
   multiply-instanced schema with system-specific instance names?

5. **Relationship to `displayName`.**
   How does the source identifier relate to the prim's `displayName`? In some
   workflows the display name *is* the source identifier; in others they
   differ. The proposal should clarify this relationship.

6. **Interaction with transcoding.**
   If source identifiers contain characters invalid in USD, they should be
   stored verbatim (not transcoded) in whatever mechanism is chosen. Transcoding
   is relevant when external identifiers need to be *embedded in prim names*,
   which is a separate concern. The source identifier mechanism should
   eliminate the need to encode external identifiers into prim names in most
   workflows.

## Relationship to other proposals

This proposal is conceptually upstream of several related efforts:

- **[Unicode Identifiers in USD](../tf_utf8_identifiers/README.md)**
  (Implemented, 24.03) -- Expanded USD's prim name grammar to support Unicode
  XID characters. This broadens what can be expressed *as a prim name* but
  does not address the separation of concerns between prim names and external
  identifiers.

- **[Extended Unicode Identifiers](https://github.com/NVIDIA-Omniverse/USD-proposals/tree/extended_unicode_identifiers/proposals/extended_unicode_identifiers)**
  -- Explores further extensions to prim name grammar (leading digits, medial
  hyphens). Addresses syntax constraints but not the conceptual distinction
  between USD and external identifiers.

- **[Bi-Directional Transcoding of Invalid Identifiers](../_notPublished/draft/transcoding_invalid_identifiers/README.md)**
  -- Proposes a Bootstring-based algorithm for round-trip encoding of arbitrary
  UTF-8 strings into valid USD identifiers. This is an implementation
  technique that becomes less critical if external identifiers have a dedicated
  storage mechanism outside the prim name.

- **[Revise Use of Layer Metadata](../revise_use_of_layer_metadata/README.md)**
  -- Proposes migrating stage metadata to applied schemas. The analysis of
  `assetInfo`'s prim-based design in that proposal is directly relevant:
  the same reasoning that led to `assetInfo` being prim-based (persistence
  through flattening, composability in referenced assets) applies to source
  identifiers.

- **[UI Hints in USD](../ui-hints/README.md)**
  ([Implemented](https://github.com/PixarAnimationStudios/OpenUSD/tree/dev/pxr/usd/usdUI))
  -- Has migrated `displayName`, `hidden`, and `displayGroup` into a `uiHints`
  dictionary, with deprecation of the existing top-level fields. This cements
  `displayName` as a presentation concern and creates urgency for a dedicated
  source identifier mechanism, since pipelines currently using `displayName`
  as a workaround now face active API and content compatibility costs.

## Next steps

1. **Align on the problem statement.** Circulate this document among TAC
   members and industry stakeholders to confirm that the problem is understood
   consistently and that the framing resonates across industries.

2. **Gather additional use cases.** Solicit concrete examples from PLM,
   manufacturing, M&E, and other domains to ensure the framing is not
   inadvertently biased toward any single industry.

3. **Evaluate `assetInfo` extensibility.** Conduct a focused analysis of
   whether `assetInfo` (or a generalization of it) can serve as the vehicle
   for source identifiers, or whether a new mechanism is warranted.

4. **Draft a solution proposal.** Based on alignment from steps 1-3, draft a
   concrete proposal specifying the mechanism (schema, metadata, or properties),
   its composition semantics, and its API.

---

## Appendix A: Provenance and AI-Assisted Drafting

This proposal was drafted with the assistance of an AI language model (Claude,
Anthropic) operating within Cursor IDE, under the direction of Aaron Luk. All
conceptual framing, editorial decisions, and technical judgment are the
responsibility of the human author. The AI was used as a drafting tool to
accelerate the writing process based on context and direction provided by the
author.

### Context provided to the AI

The following materials were provided as input context for drafting:

1. **Meeting discussion notes** -- Summary of an AOUSD TAC from 2026-02-20 covering
   the core problem statement (separating USD identifiers from external
   identifiers), key questions (instance vs. source, single value vs. package),
   existing USD concepts (`assetInfo`), the desired approach (conceptual
   separation first, implementation details later, cross-industry alignment),
   and timeline.

2. **[Extended Unicode Identifiers proposal](https://github.com/NVIDIA-Omniverse/USD-proposals/tree/extended_unicode_identifiers/proposals/extended_unicode_identifiers)**
   -- Referenced as related but noted as an implementation detail regarding
   prim name syntax expansion.

3. **[Bi-Directional Transcoding of Invalid Identifiers proposal](../_notPublished/draft/transcoding_invalid_identifiers/README.md)**
   -- A draft proposal for Bootstring-based encoding of arbitrary UTF-8
   strings into valid USD identifiers. Referenced as a related implementation
   technique.

4. **AOUSD AECO Interest Group Prim Name Grammar Use Case**
   (DRAFT v0.0, dated 2025-04-05) -- AECO domain requirements including
   leading digits, medial hyphens, slashes, GUIDs, regional characters,
   bi-directional transcoding, and semantically meaningful naming conventions.

5. **Existing proposals in this repository** -- The AI reviewed the structure
   and conventions of published proposals (e.g., `semantic_schema`,
   `tf_utf8_identifiers`, `revise_use_of_layer_metadata`) and the
   `UsdModelAPI` / `assetInfo` documentation to inform the analysis of
   existing mechanisms.

6. **[UI Hints in USD](../ui-hints/README.md)
   ([Implemented](https://github.com/PixarAnimationStudios/OpenUSD/tree/dev/pxr/usd/usdUI))**
   -- The migration of `displayName`, `hidden`, and `displayGroup` into a
   `uiHints` dictionary with deprecation of the existing top-level fields.
   Already implemented in OpenUSD `dev`. Identified as creating urgency due
   to API and content compatibility implications for pipelines using
   `displayName` as a workaround for source identifiers.

### Prompts provided to the AI

The following is a chronological log of all prompts (paraphrased) given to the
AI during the drafting session:

1. *"We're going to draft a new proposal -- don't start yet -- just let me
   provide context."* -- Followed by the meeting discussion summary (core
   problem, key questions, existing concepts, approach, timeline).

2. *"[Extended Unicode Identifiers URL] is relevant but potentially an
   implementation detail."*

3. *"[Transcoding Invalid Identifiers README] is relevant but may be an
   implementation detail."*

4. *"[AECO Prim Name Grammar Use Case PDF] has use cases and requirements for
   at least one domain, AECO."*

5. *"Keep in mind that solving the AECO use cases should be an outcome but not
   necessarily the primary driver -- the key is to win alignment across
   industries around separation of concerns for identifiers."*

6. *"Let's get started in a new folder called
   identifier_separation_of_concerns."*

7. *"Please add an appendix where you cite yourself for provenance -- we will
   also keep a running list of all prompts there and all context that you have
   been provided."*

8. *"Let's add some urgency due to the migration of the displayName metadata
   into the usdUI hints dictionary, which has content and API compatibility
   implications -- see [UI Hints proposal]."*

9. *"Let's refine the previous update, as the usdUI proposal has already been
   implemented -- see [OpenUSD usdUI source]."*

10. *"Keep in mind that this is going to be submitted as a pull request to
    PixarAnimationStudios/OpenUSD-proposals -- please fix any absolute links
    to asluk/OpenUSD-proposals accordingly."* -- Audit found no links to the
    fork; all links already target upstream repos.
