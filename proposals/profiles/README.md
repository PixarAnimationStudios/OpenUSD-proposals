![Status:Implemented, 26.08](https://img.shields.io/badge/Implemented,%2026.08-blue)
# USD Profiles and Capabilities

**USD Profiles and Capabilities** are the mechanism by with prims within a *USD* composition declare what they need to function properly and what funcitonal contracts they fulfill. Profiles and Capabilities are organized into a single **Directed Acyclic Graph** (DAG) by which means it is possible to reason about the full capabilities of a prim by reasoning about the structure of the graph from the perspective of the prim's declarations.

*USD*'s flexibility via custom schemas, proprietary formats, and extensions makes its use applicable and attractive across industries, but that flexibility also introduces interoperability challenges. While comprehensive schemas exist for a wide variety of domains, and more are always in development, applications typically implement subsets relevant to their needs. Although expedient, this potentially creates inconsistencies and mismatches when working with documents between applications with differing schema support.

These problems are not unique to USD. Systems like glTF and Vulkan place similar burdens on developers: reconciling SDK capabilities, document requirements, and runtime configurations often involves guesswork, experimentation, and platform-specific tweaks. This fragmentation complicates tool development and hinders reliable workflows.

Proprietary format extensions such as Adobe Scene Description (ASD) and Apple’s RealityKit introduce additional compatibility challenges by embedding custom schemas and runtime behaviors. While the USDZ specification mitigates some of these issues by restricting archive contents, the emergence of workarounds—like specialized schemas and format variants—underscores the need for a more robust, principled approach to interoperability.

This proposal introduces a structured extension system, **USD Profiles**: a declarative approach to extensibility and interoperability, intended to address these challenges by enabling applications to:

- Discovery and validation of a document's compatibility and runtime requirements,
- Interoperability assessment of particular scenes or scene elements,
- Determining capability satisfaction for declared functional needs.

## Capabilities

**Capabilities** are fine-grained tokens declaring a singular functionality required by a prim; a prim may declare that it requires many capabilities. Not every feature needs a capability, the need for a capability token arises when it is desired to flag critical functionality to a consumer.

> For example, the creator of a prim reliant on correct color management may wish to communicate that a color management capability is required.

Capabilities use reverse domain notation for hierarchical clarity and diagnostic stability, for example

- `usd.geom.skel` - USD skeletal geometry capability
- `usd.shade.material` - USD material shading capability
- `yoyodyne.dimensional.contabulator` - Vendor-specific extension

The naming scheme communicates logical functional and domain grouping, but does not encode strict ancestry, as nodes may have multiple immediate predecessors and names would quickly become confusing.

Versioning capabilities utilizes the same naming scheme followed by *USD* schemas. Versioning may be used to differentiate a capability that has gained or lost functionality that needs flagging to consuming entities.

## Profiles

**Profiles** are convenient named locations within the full capability DAG; they serve to compactly name groups of aggregated capabilities, such as built in file formats, or a particular OpenUSD release.

## Claims

**Claims** on a prim declare the **capabilities** used by the prim, and **profiles** that are expected to be satisified by the prim. Claims are implemented in *USD* by the `UsdProfilesClaimsAPI` schema and associated utility functions (the associated functions are not described here).

Claims are stored in two tiers of data, a **capability tier**, and a **profile tier**.

### Prim Capability Usage Tier

The **Capability Usage Tier** records which USD USD capabilities a prim actually uses, together with a degradation class for each:

- **hard**: The capability is load-bearing; a consumer that does not support it will produce incorrect results.
- **soft**: it is acceptable that the prim degrades gracefully if the capability is absent (e.g. although the capability may be absent, an application has a fallback representation).
- **enhancement**: a capability improves quality but its absence is allowable.

This tier is intended to be written automatically by the tool that saved the prim, or during a tool-based post-process that traverses a stage aggregating capabilities.

### Profile Compatibility Tier

The **Profile Compatibility Tier** records which named profiles this prim is compatible with, together with an optional per-profile exception set listing capabilities that are present but known to be out of compliance.

A profile compatibility claim without exceptions is an unqualified assertion that a prim satisfies every capability in the profile's transitive closure, in other words, it is not out of compliance with the profile's capabilities.

> As an example, a low-end mobile profile may be able to display a particular material, but the performance is known to be poor. So, while the prim has a `hard` capability declared, the specific embodiment of that prim fails the profile's constraints.

This tier is appropriate for publishable deliverables. It is typically authored by a pipeline conformance step or when performing a platform-compatibility audit.

## Validation

The USD Validation system may be leveraged to check that authored profiles are not contradicted by claims declared on a prim.

## The Profiles Graph

The directed acyclic capability graph (DACG) enforces two key principles:

1. **Ancestral Derivation**: Capabilities inherit from one another, creating a structured hierarchy.
2. **Interoperability Constraints**: Sibling capabilities must share a common descendant to ensure meaningful grouping and capability.

Example Hierarchy:

```text
usd (root)
└── usd.image
    ├── usd.image.jpeg
    ├── usd.image.png
    └── usd.image.avif
```

Capabilities and profiles integrated into the graph have a few requirements that must be observed:

- All USD-extending capabilities must transitively inherit from `usd`
- Vendor capabilities may define independent graphs using their own root nodes
- Plugins may publish multiple capability graphs simultaneously
- Versioned capabilities are new nodes in the capability graph, integrated appropriately to reflect their transitive route to `usd`.

Edges in the DACG may be marked as deprecated, indicating that a path through that edge represents a superseded or obsolete route. A path may be considered:

- **valid** for a given ancestor of a prim if the ancestor is reachable via at least one non-deprecated path.
- **deprecated** if the path is satisfied only via deprecated paths.
- **conflicted** if the edge is reachable by both valid and deprecated paths.

## Utility and Observation

The fundamental utility of the USD Profiles is resolving a fundamental question:

> What claim is a profile declaring, and on whose behalf?

A profile declared on a prim may be read adversarially, or accomodatively:

1. **Adversarial** (restrictive): "I require these capabilities. If your pipeline cannot satisfy them, you may not use me correctly."

    In this case, profiles are a gate: a failure to satisfy the profile is a hard rejection.

2. **Accommodative** (declarative): "I was authored using these capabilities. Here is a precise description of what I depend on. Use that information as you may be useful."

    In this case, profiles are a description: a failure to satisfy the profile is actionable information, with graceful degradation, substitution, warning, or rejection all possible according to some external policy.

Choosing one or the other determines how useful the system will be in practice, and how expensive it is to use.

- A system that is purely adversarial will either be ignored (because the cost of compliance is too high) or will be gamed (because participants will claim the weakest profile they can get away with).
- A system that is purely accommodative may fail to protect assets from being used in genuinely incompatible contexts.

Both framings are valid, apply at different layers of the system, and must be kept distinct.

### Asset-Level Claims

An individual USD asset, whether it be a character, a prop, a material, and so on, makes a claim about the capabilities it was authored with. This is the natural unit of provenance: the artist or DCC tool that produced the asset knows what is required.

Such Asset-level claims are granular and tractable, and authoring tools can emit them automatically. The claims are stable in that an asset doesn't change after it's published.

> The USD Profiles system provides utility to assign the claims; however, it is not responsible for selecting or assigning claims.

### Composition-Level Claims

A USD stage is a composition of many assets. A renderer asking "can I render this stage?" needs a composition-level answer, not O(n) asset-level answers.

Composition-level claims are derived rather than asserted. No single author knows the full composition at authoring time; that's the whole point of USD's compositional model. The composition-level capability profile of a stage is the aggregate of all referenced assets, subject to composition semantics (variants, payloads, inherits, references).

Ideally this aggregate doesn't simply union all asset profiles. Ideally, it is the union of active capabilities that are actually loaded and contributing to the composed result. The consequence though, is that a true accounting of composition level claims depends on which variants are selected, which payloads are loaded, and which overrides are in effect. There is a Schrödinger's Cat paradox in play; a composition-level claim depends on a decision on how deeply to introspect and on the degree of compositional observability when a claim is accounted.

> Since composition may hide any degree of further composition, the observational horizon of a composed scene is in principle unbounded!

### Software / Pipeline Claims

A DCC tool, renderer, or pipeline component may make consumer-side claims about what it supports: "I can handle everything up to `profile.studio.vfx-v2508`."

Consumer claims are analogous to asset claims but point in the opposite direction - rather than saying "I used these capabilities", they say "I can satisfy these capabilities."

> The question of whether a consumer can handle an asset is a matching problem between the asset's capability set and the consumer's capability set.

### The Observational Horizon Problem

#### The Antiques Mall

Consider a composed scene that references thousands of independently-authored assets like Pixar's Toy Story 4 antiques mall; in this scene, each prop is a USD asset, each authored by different artists at different times using different DCC tools.

Each asset in this Ideal USD Antiques Mall may thus carry different profile claims. A renderer opening this stage faces a question: "can I render this?" To answer it, the renderer would need to:

- Load (or at least inspect) every referenced asset.
- Determine which assets are active under the current variant/payload configuration.
- Aggregate the capability requirements of all active assets.
- Determine whether its own capability set satisfies the aggregate.

The first step is potentially intractbile:

> In USD, payloads are explicitly designed to be *deferred*; not loaded until needed. Forcing load of all assets to determine capability requirements defeats the purpose of payloads entirely.

#### The Horizon is Intentionally Bounded

USD's composition model provides a natural answer to this problem: the observational horizon is bounded by what the consumer chooses to load. A renderer that loads only the default payload set sees only the capability requirements of that set. If the renderer later loads additional payloads, it may discover new capability requirements.

This mirrors how USD composition works generally: the full composed result can't be known until the full composition is loaded. Profile claims are subject to the same lazy evaluation semantics as everything else in USD. Accordingly:

> Capability checking is an *incremental* operation. As the consumer loads more of the scene, it discovers more capability requirements and can decide at each step whether to continue.

#### Aggregate Profiles and Stage-Level Metadata

For common cases, such as a renderer opening a well-defined deliverable, it is useful to have a stage-level capability summary that answers "what does this stage need?" without loading everything. This is a cached aggregate of claims, not a ground truth, we need to trust that claims have been accurately made.

A pipeline step (e.g. a conform or packaging tool) can could walk the full composition once, compute the aggregate capability set, and record it. The principal at play is this:

> Profile metadata is advisory. It is a best-effort, well-intentioned, summary subject to the variant/payload configuration at the time it was computed. Consumers that need stronger guarantees must do their own traversal.

#### Adverserial Profile Matching

In the adversarial framing, an asset declares a *minimum required profile*. A consumer that cannot satisfy that profile must refuse to process the asset (or at least warn loudly).

```
asset requires: { usd.geom.mesh, usd.shading.mtlx, usd.geom.splats }
consumer supports: { usd.geom.mesh, usd.shading.mtlx }
result: REJECT - consumer cannot satisfy usd.geom.splats
```

This is appropriate for hard dependencies: if a renderer cannot process Gaussian splats, it cannot correctly render an asset that uses them. Silently dropping the capability would produce a wrong result, not a degraded result.

> The **adversarial framing** imposes the highest burden on consumers: they must explicitly support every capability claimed by every asset they wish to use. It creates strong incentives to lie. Assets might deceptively *under-claim* weaker profiles to maximize compatibility, and applications might deceptively *over-support* capabiliities that exceed the truth.

#### Accommodative Matching

In the accommodative framing, an asset declares *what it used*, and the consumer decides what to do with capabilities it doesn't support.

```
asset used: { usd.geom.mesh, usd.shading.mtlx, usd.geom.splats }
consumer supports: { usd.geom.mesh, usd.shading.mtlx }
result: PARTIAL - usd.geom.splats will be ignored/degraded
       consumer decides: warn, substitute, or continue silently
```

This is appropriate for soft dependencies: a scene that uses splats for particle effects may still be rendered without them, albeit sans particles. End users and applications will need to determine appropriate action on the basis of available information.

#### Resolution

These viewpoints are not in conflict; they are resolved by applying them appropriately to application.

- At the **composition** level, an application of profiles and capabilities may be considered `hard` and adverserial. A mix of `hard` and `soft` classes makes a more nuanced claim.
- At the **consumer** level, a consumer's policy detrmines how to handle mismatches; a strict consumer may treat `soft` mismatches as errors, another may treat them as `warnings`.

## Summary

The profile system provides value at three levels:

1. **Automatic - DCC**

"I used this set of capabilities." The system burden is near-zero, as the declaration is tool-generated, and a tool that makes the declaration provides a trust-worthy capability description for every asset.

2. **Audited - Pipeline**

"I am compatible with profile X under exceptions E." The cost is a one-time audit at publication time. The declaration of compatibility provides guarantees for deliverables within the pipeline.

3. **Published - Vendor**

"My software supports profile set S." The software must be audited on publication, and subsequently should provide discoverable consumer capability for tooling.

### In Conclusion

The profiles and capability system does not require every asset to be manually audited, nor does it require every consumer to satisfy every possible profile. It provides a shared vocabulary and a set of well-defined queries that make compatibility questions answerable, as required by the DCC, Pipeline, Vendor, or User.

Unboundedly large assets such as the Antiques Mall are viable in this system because the per-asset cost is paid at authoring/packaging time. The stage-level aggregate is advisory, and a renderer that can't satisfy some capability in the mall can decide (per its policy) whether to degrade, warn, or reject.

Similarly, adverserial and accomodative interpretations of claims are both valid policies; the system imposes no mandatory interpretation, but it does make the salient aspects of an asset and consuming software expressible and verifiable.

