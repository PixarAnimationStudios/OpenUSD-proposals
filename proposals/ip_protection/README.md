# Separation of Concerns for IP Protection in USD

Copyright &copy; 2026, NVIDIA Corporation, PTC Inc., Vertiv Holdings Co., version 0.1 (DRAFT)

Stephen Prideaux-Ghee (PTC), Steve Blackwell (Vertiv), Aaron Luk (NVIDIA)

## Contents

- [Introduction](#introduction)
- [Motivation](#motivation)
  - [The data sharing gap](#the-data-sharing-gap)
  - [Why USD amplifies the problem](#why-usd-amplifies-the-problem)
- [Problem statement](#problem-statement)
  - [Two personas, one tension](#two-personas-one-tension)
  - [Four distinct concerns](#four-distinct-concerns)
  - [Why this matters now](#why-this-matters-now)
- [Industry use cases](#industry-use-cases)
  - [Manufacturing and product engineering](#manufacturing-and-product-engineering)
  - [Data center infrastructure](#data-center-infrastructure)
  - [Aerospace and defense](#aerospace-and-defense)
  - [Media and entertainment](#media-and-entertainment)
  - [Digital asset libraries and content marketplaces](#digital-asset-libraries-and-content-marketplaces)
- [Concern 1: Protection against dissemination](#concern-1-protection-against-dissemination)
  - [Protection through omission](#protection-through-omission)
  - [Tiered representations](#tiered-representations)
  - [Metadata filtering](#metadata-filtering)
  - [Relationship to asset structure and composition](#relationship-to-asset-structure-and-composition)
- [Concern 2: Ephemeral data and runtime protection](#concern-2-ephemeral-data-and-runtime-protection)
  - [The flatten problem](#the-flatten-problem)
  - [Secure asset resolution](#secure-asset-resolution)
  - [Language-level protection concepts (illustrative, not proposed)](#language-level-protection-concepts-illustrative-not-proposed)
  - [Streaming as an alternative](#streaming-as-an-alternative)
- [Concern 3: Copyright and attribution](#concern-3-copyright-and-attribution)
- [Concern 4: Provenance and compositional integrity](#concern-4-provenance-and-compositional-integrity)
  - [The recombination problem](#the-recombination-problem)
  - [Living provenance](#living-provenance)
- [Existing mechanisms in USD](#existing-mechanisms-in-usd)
  - [Asset resolvers](#asset-resolvers)
  - [Composition arcs and layering](#composition-arcs-and-layering)
  - [customData and customLayerData](#customdata-and-customlayerdata)
- [Separation of concerns](#separation-of-concerns)
  - [What USD can address](#what-usd-can-address)
  - [What requires external systems](#what-requires-external-systems)
  - [What requires guidance and best practices](#what-requires-guidance-and-best-practices)
- [Relationship to other proposals](#relationship-to-other-proposals)
- [Design considerations](#design-considerations)
  - [Principles](#principles)
  - [Open questions for discussion](#open-questions-for-discussion)
- [Next steps](#next-steps)
- [Appendix A: AI-Assisted Drafting](#appendix-a-ai-assisted-drafting)

## Introduction

OpenUSD is increasingly used outside its original visual effects context --
in manufacturing, infrastructure, industrial digital twins, and
multi-vendor production pipelines. This brings a question that
industries from visual effects to heavy manufacturing have wrestled
with for decades:
how do you share a digital representation of a product without giving away
the parts you need to keep secret?

Both M&E and PLM have extensive experience here, from baked caches and
vendor-restricted sequences to access control lists and simplified
representations to DRM and watermarking. USD adds a new
dimension to the problem: its composition model lets multiple parties
reference, layer, and recombine data from different sources, which is
exactly what makes it powerful for collaborative workflows -- and exactly
what makes IP protection harder.

In practice, "IP protection" turns out to be an umbrella covering at least
four distinct concerns:

1. **Protection against dissemination** -- preventing sensitive information
   (proprietary geometry, operational parameters, cost data, supplier
   information) from reaching unauthorized recipients.
2. **Ephemeral data and runtime protection** -- allowing authorized users to
   view data at runtime without the ability to persistently save or
   redistribute it.
3. **Copyright and attribution** -- ensuring that content creators receive
   credit and that ownership claims travel with the data.
4. **Provenance and compositional integrity** -- tracking the origin and
   validity of composed assets, particularly when USD's composition model
   enables recombination of components into configurations never sanctioned
   by the original supplier.

These concerns have different threat models and different likely solutions.
When they get lumped together, discussions stall because participants are
effectively trying to solve different problems at the same time.

**What this proposal delivers.** A clear problem statement and separation
of concerns, plus practical guidance on structuring USD assets so that
external systems -- asset resolvers, access control, managed content
pipelines -- can protect them effectively. No changes to core USD are
assumed. Where future USD enhancements might help (copyright metadata,
flatten-protection semantics), those are identified and scoped for
follow-up proposals.

IP protection cannot be solved by any single party. It requires
coordination across data formats, content management systems, access
control infrastructure, and industry-specific policies.

## Motivation

### The data sharing gap

Today, the workflow for getting product data into a digital twin is mostly
manual. A vendor designs in CAD, manages in PLM, and when a customer needs
a digital representation for simulation, someone exports files, curates
them, and hands them off.

```
┌─────────────────────────────────┐                  ┌──────────────┐
│        Vendor / Manufacturer    │                  │   Customer   │
│  ┌──────────┐    ┌──────────┐  │   manual work    │              │
│  │  Design   │───▶│   CAD    │──┼─────────────────▶│   Simulate   │
│  └──────────┘    └──────────┘  │                  │  (Digital    │
│           ISV                   │                  │    Twin)     │
└─────────────────────────────────┘                  └──────────────┘
```

That manual handoff is slow, but it does give the vendor control over
exactly what leaves their environment. The appeal of USD is replacing
this with live, composable references that stay current -- but that
requires an answer to: *how does the vendor keep control over what the
customer can see, save, and redistribute?*

### Why USD amplifies the problem

Several properties of USD's composition model are directly relevant:

- **Referencing and payloads** allow consumers to compose assets from
  multiple vendors into a single scene. This is powerful for building
  complex environments (e.g., a data center with thousands of pieces of
  equipment from dozens of vendors, or a feature film with assets from
  multiple VFX studios), but it means that once a reference is resolved,
  the geometry and metadata become part of the consumer's composed stage.

- **Flattening** (`UsdStage::Flatten`) collapses the entire composition
  graph into a single layer, stripping away the reference structure that
  connected back to the original source. Any asset resolver-based
  protection is bypassed once the data is flattened and saved to disk.

- **Open traversal** through Hydra and the USD API means that any
  application with access to the composed stage can read any prim, any
  property, any value. There is no built-in concept of per-prim or
  per-property access control within a stage.

- **Composability enables recombination.** Components from different
  assemblies can be rearranged under new structures, creating product
  configurations that the original supplier never validated or sanctioned
  -- with no mechanism to indicate that the provenance chain has been
  broken.

None of this makes IP protection impossible, but it does narrow the
solution space. Decades of DRM experience in other domains suggest that
relying on the data format itself to enforce access control is fragile --
once data is accessible to a renderer, it is hard to keep it from being
captured or redistributed.

A more useful question is: *how should assets be structured and delivered
so that external systems can enforce the right protections?*

## Problem statement

### Two personas, one tension

IP protection for shared digital assets comes down to a tension between
two parties:

- **The data owner** (vendor, manufacturer, content creator) wants to
  share a digital representation of their product, but needs to control
  what information is accessible and to whom.
- **The data consumer** (customer, integrator, simulation engineer) needs
  a usable asset for their workflow -- layout, simulation, visualization,
  procurement -- and the richer the asset, the more useful it is.

The data owner's incentives to share:
- A good digital asset helps sell the physical product.
- Better integration reduces support costs.
- Richer data makes the vendor's equipment easier to specify and deploy.

The data owner's reasons to withhold:
- Competitive advantage -- internal construction, control strategies,
  supplier relationships.
- Regulatory restrictions -- ITAR, classification levels, export controls.
- Liability -- unauthorized configurations that appear to work but are
  not supported.

Consumers, meanwhile, need enough data to build useful simulations. If
the data is too locked down or too hard to get, people fall back to
manual workflows.

This tension is inherent to the domain. This proposal does not try to
resolve it, but provides a framework for understanding where different
approaches apply.

### Four distinct concerns

In the discussions that led to this proposal, "IP protection" was
consistently used as a single label for at least four separate things:

| Concern | Threat model | Primary mitigation | USD role |
|---|---|---|---|
| **Dissemination** | Unauthorized access to sensitive geometry, metadata, or operational parameters | Omission, filtering, tiered representations managed by external systems | Guidance on asset structure; no core changes needed |
| **Ephemeral data** | Authorized viewer saves or redistributes data beyond their access level | Controlled resolution, streaming, flatten prevention | Raises format-level questions (see [Open questions](#open-questions-for-discussion)); fundamentally hard to enforce |
| **Copyright** | Content used without attribution; ownership claims lost through processing | Metadata that travels with the data | Relates to how metadata travels through composition (see [Open questions](#open-questions-for-discussion)) |
| **Provenance** | Recombined components presented as supplier-sanctioned configurations | Origin tracking that invalidates on unauthorized recomposition | Relationship to source identifiers; approaches from other domains (digital signatures, watermarking) may inform solutions |

Separating these matters because what works for one may be useless for
another. Omission handles dissemination well but does nothing for
copyright. Watermarking helps with provenance but not dissemination.
Streaming helps with ephemeral data but needs infrastructure that is
not always available.

### Why this matters now

Why now:

1. **Cross-industry adoption is accelerating.** Manufacturing,
   infrastructure, and energy companies are evaluating USD for digital
   twins and simulation -- joining M&E studios that already manage
   multi-vendor IP boundaries on every production. Many of these
   organizations have strict IP protection requirements that must be
   addressed before they will commit to USD-based workflows.

2. **The composition model invites collaboration.** USD's strength in
   composing data from multiple sources is precisely what makes IP
   protection necessary. The more powerful the collaboration, the more
   critical the protection.

3. **Expectations exceed reality.** People sometimes assume USD
   will "magically" handle IP protection. Setting clear expectations
   about what USD can and cannot do -- and what data owners need to do
   themselves -- is important for building trust.

4. **The source identifiers proposal provides a foundation.** The
   [Separation of Concerns for Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)
   proposal establishes a framework for carrying external system
   identifiers on USD prims. Provenance, copyright, and access control
   all depend on the ability to identify the source and lineage of
   content -- making standardized source identifiers a useful
   foundation for IP protection workflows.

## Industry use cases

The examples below come from direct conversations with practitioners.
They span USD's original M&E domain through to newer industrial
adopters.

### Manufacturing and product engineering

Equipment manufacturers deal with several layers of protection when
sharing digital representations of their products:

- **Proprietary geometry.** The internal construction of a machine --
  gearing, motor drives, bearing assemblies, joint mechanisms -- is
  competitive intellectual property. A robot arm manufacturer may want
  customers to see the outer shell and understand the arm's range of
  motion, but the detailed construction of the arm segments, inner
  joints, and drive mechanisms should be simplified or omitted.

- **Operational parameters.** Static performance data (ratings,
  dimensions, power consumption) may be published openly. Dynamic
  performance data -- control system set points, thermal response curves,
  efficiency maps -- is highly proprietary. With modern AI, dynamic
  operational data can be used to reverse-engineer control strategies,
  making its exposure a direct competitive risk.

- **Proprietary metadata.** Engineering data accumulated through the
  design cycle -- cost information, supplier identities, designer
  contact information, manufacturing process parameters -- is valuable
  upstream but should never flow downstream to external consumers.

- **Configurable products.** Products assembled from configurable
  components (e.g., modular cooling units composed from sub-assemblies
  C+D or E+F) present a unique challenge: the components are shared
  individually, but only certain combinations are valid. A customer or
  third party using USD's composition capabilities could create an
  invalid combination (C+F) that appears functional in simulation but
  cannot be manufactured, leading to frustration for both customer and
  supplier.

PLM systems (PTC Windchill, Siemens Teamcenter, Dassault 3DEXPERIENCE)
handle much of this through access-controlled data management:
- Different users accessing the same part get different representations
  based on their authorization level.
- The challenge: when data "escapes" the PLM environment -- exported as
  USD files -- the access control context is lost.

### Data center infrastructure

Data centers show what happens when collaboration and protection collide
at scale:

- **Scale of composition.** A single data center model may include
  thousands of pieces of equipment from dozens of vendors -- cooling units,
  power distribution, compute racks, networking gear. Building a useful
  model requires a common repository or set of vendor-provided references.

- **Tiered protection needs.** An equipment vendor like Vertiv provides
  mechanical models as correct exterior boxes with pipe and electrical
  connections that terminate at the enclosure boundary -- nothing inside
  the box. Operational data has its own tiering axis, independent of
  geometry: static performance data published on the vendor's website
  is shared freely; dynamic performance data required for detailed
  system simulation is shared only with customers under agreement;
  internal control system parameters are never shared. These tiers do
  not map one-to-one onto geometry tiers -- a customer may receive
  simplified geometry but detailed operational parameters, or vice
  versa, depending on their role.

- **Competing vendors in shared environments.** A data center operator's
  digital twin may include equipment from competing vendors. Each vendor
  wants to protect their IP while still enabling the operator to build an
  accurate simulation.

- **Repository tension.** The most practical delivery mechanism is an
  industry repository where operators can pull vendor models. But a
  shared repository is fundamentally at odds with per-vendor IP
  protection requirements. Resolving this tension requires that the
  repository support variable access levels -- which in turn requires
  that the USD assets be structured to support variable-resolution
  delivery.

### Aerospace and defense

Regulatory frameworks add hard constraints that override business
judgment:

- **ITAR (International Traffic in Arms Regulations)** restricts access
  to certain technical data to U.S. persons only. This is not a
  discretionary business decision but a legal requirement with severe
  penalties for non-compliance. The only reliable approach is complete
  omission of restricted content at the source -- any scheme that relies
  on the consuming system to enforce access is insufficient.

- **Classification levels.** Beyond ITAR, defense programs operate under
  multi-level security classifications where the very existence of
  certain components may be classified. A bounding box labeled
  "restricted" still reveals that something exists in that location;
  true protection requires that restricted content not appear in the
  delivered asset at all.

### Media and entertainment

USD's home territory has its own IP protection needs, particularly
when multiple vendors collaborate on the same production:

- **Multi-vendor VFX pipelines.** A feature film may involve several
  VFX studios working on different sequences, sharing assets through
  a common USD scene graph. Each studio's work is proprietary --
  character rigs, simulation setups, proprietary shader networks --
  and must not leak to the other vendors on the same show.
- **Pre-release confidentiality.** Character designs, story elements,
  and unreleased footage are highly sensitive. Assets shared between
  studios for integration work must be restricted to authorized
  personnel, and studios are contractually liable for leaks.
- **Animation studio collaboration.** When animation and lighting are
  split across studios, the lighting team needs geometry and layout
  but should not have access to the animation rig internals. Today
  this is managed by exporting baked caches -- a form of protection
  through omission -- but tighter USD-native integration would
  benefit from more granular access control.

### Digital asset libraries and content marketplaces

Content creators and asset library providers have a different set of
worries:

- **Return on investment.** Creating high-quality digital assets is
  expensive. Providers need assurance that their investment is protected
  when assets are placed into shared libraries or marketplaces.

- **Attribution continuity.** When assets are referenced, composed,
  modified, and redistributed through USD's composition model, copyright
  and attribution metadata must survive the processing chain. A
  copyright notice in a layer header is only useful if downstream tools
  preserve it.

- **Licensing enforcement.** Different licensing terms may apply to
  different uses of the same asset (evaluation vs. production,
  single-user vs. enterprise). USD has no built-in mechanism for
  expressing or enforcing licensing terms, and this is likely outside
  the scope of what a data format should do -- but the format can
  facilitate external enforcement by providing standard places for
  licensing metadata.

## Concern 1: Protection against dissemination

This is the concern people think of first, and it is also the one with
the most proven solutions.

### Protection through omission

Don't ship what you don't want leaked. This is the approach that
practitioners with the most experience consistently come back to:

> *"If you don't want it to go out, don't include it in the first place.
> Anything else -- complex DRM schemes -- honestly, we tried them all and
> they will add infinite amounts of pain."*

The data owner curates the export to include only what the recipient
should see. It is binary -- the information is there or it is not -- but
it works. If something was never in the file, it cannot leak out of it.

For regulatory cases like ITAR, omission is not just advisable -- it is
the only approach that satisfies the legal requirement. Restricted
content must not be present in any form accessible to unauthorized
persons.

This requirement extends beyond regulatory contexts. Factory planners
have expressed the need to hide not just the *content* behind a
reference, but the *existence* of the reference itself. A bounding box
labeled "restricted" or a payload that fails to resolve still reveals
that something is there -- and even that can be informative to a
competitor or an unauthorized party. True omission means the
restricted content does not appear in the delivered asset's structure
at all: no placeholder prim, no dangling reference, no redacted field.

### Tiered representations

A less binary approach: provide multiple representations of the same
asset, each curated for a different audience:

- **Full access.** The complete engineering representation with all
  internal geometry, operational parameters, and metadata. Available only
  to authorized internal users or partners under NDA.

- **Customer simulation.** Accurate exterior geometry with operational
  parameters sufficient for system-level simulation. Internal
  construction simplified or omitted. Proprietary metadata stripped.

- **Public / layout.** A bounding box or simplified shell that claims the
  correct physical space, with basic connection points, rigid body
  properties, colliders, and measurements. May include a minimal set of
  metadata for basic simulation (e.g., weight, power rating, thermal
  output). May be provided to anyone.

The principle behind tiered representations is that **even the lowest
tier must serve a workflow.** A bounding box with no usable properties
is not a useful asset -- it is a placeholder that forces the consumer
back to manual workflows. If the lowest tier carries correct
dimensions, collision geometry, and enough metadata for basic layout
and simulation, it justifies the vendor's investment in creating and
maintaining tiered representations, and it gives the consumer a reason
to use the system rather than work around it.

These are not the same as Levels of Detail (LODs). LODs manage runtime
display fidelity and performance. Tiered representations manage
*information access* -- the simplified versions are intentionally less
informative, not just less detailed.

How these tiers get delivered depends on the environment:
- **Managed (PLM):** Tiers are generated from the same source data and
  delivered dynamically based on the requesting user's authorization
  level. The PLM system handles access control; the USD asset resolver
  is the integration point.
- **Unmanaged:** Tiers must be curated and distributed as separate
  assets by the data owner.

Tiered delivery has a real operational cost. The data owner must
create and maintain multiple representations, and -- particularly in
unmanaged environments -- track which customers received which tier.
As one equipment vendor put it: *"It's a problem for them in terms of
having to reach out to everybody and get the data, and frankly a
problem for us because we have to keep up with who we gave what to."*
Managed systems (PLM, DAM with resolver integration) can absorb much
of this cost by generating tiers dynamically, but organizations
without that infrastructure face a manual burden that factors into
whether tiered delivery is practical at all.

### Metadata filtering

Geometry gets the most attention, but metadata on prims and properties
can be just as sensitive:

- Cost and pricing data
- Supplier and vendor contact information
- Designer names and email addresses
- Manufacturing process parameters
- Internal revision and change order history

When data is exported from a managed system (PLM), the export process can
apply the same access-control rules that govern the source data. The hard
part is making sure filtering is systematic -- that every property and
custom data entry is evaluated against the access policy, not just the
ones someone remembered to check.

Two options for sensitive fields:
- **Redact:** Replace values with placeholders
  (e.g., `designedBy = "********"`). Useful when you want users to know
  a field exists but they lack access.
- **Omit entirely:** Safer, because even the presence of a redacted
  field can reveal information -- e.g., that a particular analysis was
  performed, or that a particular supplier relationship exists.

Property-level protection surfaces as two similar but distinct
requirements:

- **Producer-side: export control.** The data owner wants to tag
  individual properties so that export processes know not to include
  them in outbound assets. This is a filtering concern -- ensuring
  that the right properties are systematically stripped at the point
  of export, rather than relying on someone remembering to remove
  them manually.

- **Consumer-side: access-controlled visibility.** Even after delivery,
  a consumer working with an asset should not be able to see certain
  properties based on their access level. The data may be present in
  the delivered layers, but the consumer's tooling -- mediated by an
  asset resolver or a managed environment -- restricts what is visible.

These requirements call for different approaches. Export control is
a form of protection through omission -- the sensitive properties are
never in the exported file at all, so structuring them into layers
that are excluded from export (or stripping them during export) is
the natural solution. Consumer-side visibility is an access control
problem -- the properties may be present in the delivered data, but
structured into separate layers that the consumer's tooling
(mediated by an asset resolver or managed environment) can
independently restrict.

### Relationship to asset structure and composition

How well omission works depends on how the USD asset is organized. If
public and privileged information live in separate layers, payloads, or
sub-assemblies, access control is straightforward. If they are
interleaved in a single monolithic file, protecting one without the
other is painful.

**Practical guidance for asset structuring:**

- **Separate internal and external representations** into distinct
  sub-assemblies or payloads. Internal (privileged) geometry and external
  (public) geometry should be independently referenceable, so that access
  control systems can serve one without the other.

- **Layer proprietary metadata separately.** Metadata that should not
  leave the source environment should be authored in layers that are not
  included in the exported asset, rather than being stripped after the
  fact.

- **Use composition arcs as privilege boundaries.** Any composition
  arc that targets an external layer -- references, payloads,
  sublayers -- can serve as an access-control boundary. An asset
  resolver that requires authentication before resolving the target
  can enforce per-user access control at the composition level.
  Payloads are especially convenient because they are deferred by
  default, but references and sublayers work the same way from the
  resolver's perspective.

- **Design for the lowest common denominator.** The base representation
  of any shared asset should be the most restricted version -- the one
  safe for the widest audience. Additional detail should be layered on
  top through composition arcs that can be independently access-controlled.

## Concern 2: Ephemeral data and runtime protection

A harder problem: let a user *see* data at runtime but prevent them from
*saving or redistributing* it. A familiar analogy: a password-protected
website controls who can access a page, but once it renders in a browser,
nothing stops the viewer from taking a screenshot or saving the HTML.
The same fundamental tension applies to USD -- once data is resolved and
visible on a composed stage, it is capturable.

### The flatten problem

USD's composition model gives you some implicit protection here. When a
scene references external assets through composition arcs, a normal "save"
preserves the references, not the resolved data. The next person who opens
the file has to re-resolve those references, and if they don't have the
right credentials, they only get what they're authorized to see.

The protection breaks when the stage is **flattened**. `UsdStage::Flatten`
collapses the composition graph into a single layer, resolving all
references, payloads, and overrides into their final composed values. The
resulting layer contains all the data that was visible to the user who
performed the flatten, without any reference back to the original sources.
A user with full access who flattens and saves can redistribute the
complete data to anyone.

### Secure asset resolution

Asset resolvers are the main integration point for external access
control. A custom resolver can:

- **Require authentication** before resolving any asset path, ensuring
  that only authorized users receive the data.
- **Return different representations** based on the requesting user's
  authorization level (delivering a simplified shell to one user and full
  geometry to another, from the same reference).
- **Log access** for audit and compliance purposes.
- **Enforce session-scoped access** where resolved data is valid only for
  the current session and cannot be cached or persisted.

Resolvers work because they sit at the boundary where external data
enters the USD stage. But they cannot prevent a user from saving the
resolved data -- once it is in the composed stage, any code with stage
access can read it.

### Language-level protection concepts (illustrative, not proposed)

> **Note:** This section documents a *requirement* expressed by
> practitioners, not a proposal for changes to USD's grammar or
> composition engine. The sketches below are included to make the
> requirement concrete and to explain why it is difficult to address
> at the format level. They are not recommendations.

In our working sessions, the question came up: could USD's grammar
express protection intent on composition arcs? For example, imagine a
`final`-like keyword on a payload telling tools not to flatten it:

```
# Hypothetical syntax -- NOT a proposal
prepend final payload = @windchill:OR:wt.part:1234567@
```

Borrowed from programming language semantics (`final` in C++/Java
prevents overriding), the idea would be to prevent "overriding" a
reference with its resolved content.

The requirement behind this idea is real: data owners want to share
live references that stay connected to the source system, and they
want assurance that those references cannot be resolved and saved
out from under them. But implementing this at the format level is
hard:

- **Renderers need geometry, not policy.** The renderer must have
  vertices, normals, and textures to draw. But a performant
  renderer should not carry IP privilege or access-control metadata
  it does not need -- and if it does not carry that context, it
  cannot enforce it.

- **Driver interception.** Even if USD prevented flattening,
  graphics data passing through the GPU driver is interceptable.
  If the pixels must be displayed, the data is capturable.

- **Hydra's open traversal model.** Any Hydra render delegate can
  read the full scene graph, and anyone can write a delegate.
  Format-level protection cannot work without also controlling
  the render pipeline.

Whether any of this belongs in USD is an open question (see
[Open questions for discussion](#open-questions-for-discussion)).
One lighter-weight possibility: an advisory annotation that signals
producer intent without changing composition semantics:
- Conforming tools would respect the annotation and refuse to
  flatten the marked arc.
- Non-conforming tools could ignore it -- but they would be
  operating outside the producer's stated policy.
- Even advisory protection is a useful signal, analogous to `const`
  in C: it does not prevent all misuse, but it communicates
  expectations.

This is documented here to capture the requirement, not to advocate
for a specific solution.

### Streaming as an alternative

Another approach: never deliver geometry to the client at all.

- **How it works:** The server renders the scene and transmits only
  pixels. The client sees the image but never has access to the
  underlying geometry or metadata.
- **Limitations:** Screen capture and 3D reconstruction from images
  remain possible. Not USD-specific.
- **Trade-offs:** Requires server-side rendering infrastructure, adds
  latency, and limits interactivity compared to local rendering.
- **Adoption:** Some organizations with strict IP protection
  requirements have adopted this approach despite the trade-offs.

The reasoning behind streaming adoption is instructive. Even
delivering tessellated mesh data (as opposed to source CAD geometry)
is considered risky by some vendors: mesh vertices lie on the
original surfaces, so surface geometry can be reconstructed from
the mesh with reasonable fidelity. One PLM vendor described arriving
at streaming specifically because every other delivery mechanism --
including simplified meshes -- left enough information for a
determined party to reverse-engineer the original shapes. Pixel
streaming was the only approach that kept geometry entirely
server-side.

A related technique explored in prior industry research is
**view-dependent geometric obfuscation**: mathematically composing
geometry so that it renders correctly from a specific camera
viewpoint, but is meaningless from any other angle -- conceptually
similar to Gaussian splatting. In practice this proved too difficult
to implement at production scale, which reinforced the industry
trend toward simpler approaches: omission for what can be withheld,
streaming for what must be shown but not delivered.

## Concern 3: Copyright and attribution

Copyright is more straightforward than the previous concerns, but it
matters for getting people to participate in shared asset ecosystems.
If you invest in building a high-quality digital asset and put it in a
library, you want to know your name stays on it.

To illustrate the requirement, one approach that has come up in
discussion is a standardized copyright field in the USD layer header:

> **Note:** The syntax below is illustrative -- it shows what the
> requirement *looks like*, not what USD should implement. The
> specifics of any metadata schema would be the subject of a
> separate proposal.

```usda
# Illustrative syntax -- NOT a proposal
#usda 1.0
(
    upAxis = "Y"
    defaultPrim = "World"
    metersPerUnit = 1.0
    copyright = "© ACME Corp. 2026"
)
```

If copyright metadata were an array, it could accommodate
composition:

```usda
    # Illustrative
    copyright = ["© ACME Corp. 2026", "© WidgetWorks Inc. 2026"]
```

Key considerations regardless of the specific mechanism:

- **Persistence through flattening.** Copyright metadata needs to
  survive `Flatten` operations. Whether this requires explicit
  handling in the flatten implementation, an applied schema, or
  external tooling is an open question.

- **`customLayerData` is not sufficient.** Copyright can be stored
  in `customLayerData` today, but `customLayerData` does not
  survive `Flatten` -- it is per-layer metadata that is discarded
  when layers are composed into one (see
  [Revise Use of Layer Metadata](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/revise_use_of_layer_metadata)).
  If copyright must persist through flattening, it needs a
  different mechanism.

- **Not enforcement.** A copyright field does not *enforce*
  copyright -- it merely asserts it. Enforcement is a legal and
  business matter, not a data format problem. But clear assertion
  is a prerequisite for enforcement.

- **Display watermarking as prior art.** Some PLM vendors already
  ship watermarking in their file formats: copyright and watermark
  data are embedded in the file, and conforming viewers are expected
  to display a visible mark (a company logo, for example) on screen.
  This does not prevent copying, but it makes the provenance visible
  to anyone viewing the asset and creates a social and contractual
  deterrent. Whether USD should support a similar convention -- and
  whether Hydra render delegates should be expected to honor it --
  is a question worth raising.

Whether and how USD should address this is an open question (see
[Open questions for discussion](#open-questions-for-discussion)).

## Concern 4: Provenance and compositional integrity

Provenance -- tracking where content came from -- gets complicated in
USD because composition lets you pull things apart and recombine them.

A note on terminology: the
[Separation of Concerns for Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)
proposal identifies **authorship traceability** as a related use
case -- tracking *who* created or modified content, at the person
or tool level. Provenance as used here is a different concern:
tracking whether a *composed assembly* still matches what the
supplier validated. Authorship asks "who touched this?";
compositional provenance asks "is this still a valid product
configuration?" Both build on source identifiers, but they track
different things for different audiences.

### The recombination problem

Consider a vendor who provides two configured products as USD assets:
product C+D and product E+F, where C, D, E, and F are components that
have been validated to work together in those specific combinations.

USD's composition model allows a consumer to:

1. Reference both product C+D and product E+F.
2. Extract component C from the first and component F from the second.
3. Compose them into a new structure C+F.
4. Save this as a new asset that looks like a valid product.

The resulting C+F assembly may render correctly and even pass simulation
tests, but:
- It is not a product the vendor manufactures or supports.
- The customer approaches the vendor expecting to buy C+F -- and
  discovers it does not exist.
- The vendor gets a frustrated customer for a product they never offered.

This scenario has been raised as a specific concern by manufacturers who
see USD's composition capabilities as both an opportunity and a risk.

### Living provenance

Ordinary provenance records where data came from. The recombination
problem needs something stronger: **provenance that breaks when the
composition is changed**.

If product C+D carries a provenance marker indicating it is a validated
configuration from vendor X:
- Extracting C and composing it with F from a different assembly should
  *break* that provenance.
- The new assembly C+F should not inherit the validated status of its
  source components.

This is "living" or "dynamic" provenance -- not a static stamp, but a
property that is sensitive to compositional changes.

Some approaches from other domains:

- **Digital watermarking.** A watermark encodes provenance information
  within the geometric data itself. Breaking the intended composition
  (e.g., extracting a component from its validated context) would
  invalidate the watermark. Watermarking for 3D data is a well-researched
  field but has historically been difficult to implement at scale,
  particularly when the data can be further modified after watermarking.

- **Digital signatures.** A cryptographic signature over the composed
  assembly validates that the configuration matches what the supplier
  signed. Any modification -- adding, removing, or rearranging
  components -- invalidates the signature. This is conceptually clean
  but requires infrastructure for key management and signature
  verification.

- **Compositional checksums.** A lighter-weight approach where the
  supplier includes a checksum computed over the specific combination of
  components. Tools can verify the checksum to determine whether the
  assembly matches the supplier's validated configuration, without the
  full infrastructure of cryptographic signatures.

Provenance ties into the source identifiers work:
- If components carry standardized source identifiers
  ([Separation of Concerns for Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)),
  provenance tracking can build on them to record which components were
  combined and whether the combination has been validated.
- Copyright and provenance may benefit from overlapping mechanisms --
  e.g., digital signatures that attest to both origin and integrity.

## Existing mechanisms in USD

### Asset resolvers

USD's
[`ArResolver`](https://openusd.org/dev/api/class_ar_resolver.html)
provides a plugin interface for resolving asset paths to concrete data.
Custom resolvers can implement authentication, access control, and
content-dependent resolution -- making this the main extension point
for IP protection in USD today.

The OpenUSD repository includes a
[resolver example](https://github.com/PixarAnimationStudios/OpenUSD/tree/dev/extras/usd/examples/usdResolverExample)
that demonstrates the plugin interface. Each stakeholder implements
their own resolver to integrate with their specific access control
infrastructure.

Pluggable authentication is a well-established pattern: OAuth 2.0,
web server auth modules (Apache `mod_authn_*`, Nginx
`auth_request`), PAM, and Java JAAS all define a plugin interface
that each deployment wires to its own infrastructure. Those systems
go further than `ArResolver` by also standardizing authorization
rules (token formats, module types, principal semantics).
`ArResolver` intentionally stops at the extension point -- it
defines *where* to plug in but says nothing about *how*
authorization should work, leaving that to the external systems
where it belongs.

### Composition arcs and layering

USD's composition arcs (references, payloads, inherits, variants,
specializes) provide natural boundaries for access control:
- **Payloads** are particularly useful because they are deferred -- a
  tool can open a stage without loading payloads, then selectively load
  only those the user is authorized to access.
- **Layer separation** supports protection through omission: proprietary
  metadata can be authored in layers that are never distributed, while
  shared layers contain only what is appropriate for the recipient.

### customData and customLayerData

`customData` (on prims and properties) and `customLayerData` (on layers)
can carry arbitrary key-value metadata. Copyright, provenance, and
protection policy could be stored here today, but:
- Every pipeline must agree on key names independently.
- Tools have no way to discover or interpret the metadata without prior
  knowledge of the convention used.
- `customLayerData` does not survive `Flatten` -- it is per-layer
  metadata that is discarded when layers are composed into one
  (see [Revise Use of Layer Metadata](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/revise_use_of_layer_metadata)).
  Any metadata that must persist through flattening (e.g.,
  copyright) cannot rely on `customLayerData` alone.

## Separation of concerns

Part of the value of this proposal is being explicit about what belongs
where: what can be addressed in USD, what needs external systems, and
what is really about guidance and best practices.

### What USD can address

- **Copyright and attribution metadata.** Copyright metadata is one
  area where a standardized field *might* reduce fragmentation
  across toolchains. The specifics -- schema design, composition
  semantics, whether this belongs in core USD or in an applied
  schema convention -- would be the subject of a separate, focused
  proposal informed by community discussion.

- **Statement-of-intent annotations on composition arcs.** An
  advisory annotation signaling producer intent regarding
  flattening has been discussed as an illustration of the
  requirement (see [Language-level protection concepts](#language-level-protection-concepts-illustrative-not-proposed)).
  Whether this belongs in USD, in external tooling conventions, or
  nowhere at all is an open question.

- **Source identifier infrastructure.** The
  [Separation of Concerns for Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)
  proposal provides the foundation for provenance tracking by
  standardizing how source identifiers are carried on prims.

### What requires external systems

- **Access control.** Per-user, per-role, or per-organization access
  control is the responsibility of asset management systems (PLM, DAM),
  delivery infrastructure, and custom asset resolvers. USD is a data
  format, not an access control system.

- **Content filtering and tiered delivery.** Generating different
  representations for different audiences is a content management
  function. PLM systems already do this; the guidance in this proposal
  helps USD asset authors structure their data to support it.

- **Streaming and ephemeral rendering.** Pixel-streaming solutions that
  prevent client-side data access are infrastructure concerns, not data
  format concerns.

- **DRM and encryption.** Full DRM schemes require runtime enforcement
  infrastructure that is outside the scope of a data format
  specification.

### What requires guidance and best practices

- **Asset structuring for protectability.** How to organize layers,
  payloads, and sub-assemblies so that external access control systems
  can serve appropriate content to each user.

- **Metadata hygiene.** Practices for ensuring that proprietary metadata
  does not inadvertently leak into exported assets.

- **Tiered representation creation.** Guidelines for creating simplified
  representations that are useful for downstream workflows while omitting
  sensitive detail.

- **Expectation setting.** Clear communication that USD is not a security
  boundary and that robust IP protection requires external systems,
  informed by decades of industry experience.

## Relationship to other proposals

- **[Separation of Concerns for Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)**
  -- Source identifiers are a prerequisite for provenance and copyright
  tracking. IP protection builds on the ability to identify the origin
  and lineage of components.

- **[Revise Use of Layer Metadata](../revise_use_of_layer_metadata/README.md)**
  -- Proposes migrating stage metadata to applied schemas. Copyright and
  licensing metadata would follow the conventions established by this
  proposal.

- **[UI Hints in USD](../ui-hints/README.md)** -- The migration of
  `displayName` to a presentation-only concern parallels the
  distinction here between what metadata is for display vs. what is for
  identification and protection.

## Design considerations

### Principles

1. **Separation of concerns.** Each of the four IP protection concerns
   has different characteristics and likely solutions. They should be
   addressed independently, even where the mechanisms overlap.

2. **No single mechanism is sufficient.** Layer multiple protections
   so no single failure is catastrophic. Effective IP protection
   combines asset structuring, access control, metadata hygiene,
   and appropriate delivery mechanisms.

3. **Protection by default.** The base representation of any shared asset
   should be the most restricted version. Additional detail should be
   layered on through composition arcs that can be independently
   access-controlled.

4. **USD as facilitator, not enforcer.** USD can provide metadata
   standards, structural conventions, and extension points (particularly
   asset resolvers) that facilitate IP protection. Attempting to enforce
   protection entirely at the data format level risks repeating the
   challenges that DRM schemes have encountered in other domains.

5. **Vendor extensibility.** Different organizations and industries have
   different IP protection policies. The mechanisms should allow vendors
   to implement their own protection strategies through asset resolvers
   and metadata conventions, without requiring changes to core USD for
   each new policy.

6. **Industry agnosticism.** The framework should apply equally to
   M&E, manufacturing, AECO, data center infrastructure, and domains
   not yet envisioned. Domain-specific policies are implemented through
   the extension points, not hard-coded into the framework.

7. **Pragmatism over perfection.** Perfect IP protection for digital
   data is an unsolved problem. Practical guidance that addresses the
   majority of real-world concerns is more valuable than a theoretically
   complete solution that is too complex to implement.

### Open questions for discussion

1. **Scope of standardization.**
   - Which of the four concerns belong in core USD (metadata schemas,
     grammar extensions)?
   - Which should be left to external conventions and best-practice
     guides?
   - Where is the line between "USD should standardize this" and "USD
     should provide extension points for this"?

2. **Interaction with asset resolvers.**
   - What conventions or APIs would make tiered delivery easier to
     implement?
   - Should resolvers have a standard way to advertise what protection
     levels they support?
   - How should a resolver communicate the requesting user's
     authorization level to the content management system?

3. **Copyright metadata schema.**
   - What fields? A simple `copyright` string, an array for composition,
     or structured fields (license type, attribution, usage restrictions)?
   - How should copyright metadata compose when layers are referenced or
     flattened?

4. **Provenance representation.**
   - Static metadata (origin, timestamp, signature)?
   - A relationship to source identifiers?
   - A compositional checksum that invalidates on recomposition?
   - What is the minimum viable provenance that would address the
     recombination problem?

5. **Flatten-protection semantics.**
   - Is there value in a `final` or `protected` annotation on
     composition arcs?
   - Purely advisory, or enforced by conforming tools?
   - `final` is not currently a keyword in USD. Would introducing it
     create ambiguity or conflict with future USD features?

6. **Relationship to streaming and cloud delivery.**
   - As USD scenes are increasingly served from cloud infrastructure,
     how does this framework interact with cloud rendering and streaming?
   - Should the proposal address these scenarios explicitly, or treat
     them as infrastructure concerns outside USD's scope?

## Next steps

1. **Submit as pull request.** Post this proposal to the OpenUSD-proposals
   repository for community discussion and feedback.

2. **Align on the problem statement and separation of concerns.** Confirm
   among stakeholders that the four-concern framing resonates and that the
   separation of what USD can vs. should address is agreed upon.

3. **Develop asset structuring guidelines.** Create practical guidance --
   with examples -- for structuring USD assets to support tiered delivery
   and protection through omission. This is the most immediately
   actionable outcome.

4. **Draft focused follow-up proposals if warranted.** If community
   discussion identifies concerns that would benefit from USD
   enhancements, draft targeted proposals with concrete schemas and
   semantics.

5. **Prototype asset resolver patterns.** Develop reference
   implementations demonstrating access-controlled resolution with tiered
   delivery, building on the existing
   [resolver example](https://github.com/PixarAnimationStudios/OpenUSD/tree/dev/extras/usd/examples/usdResolverExample)
   in the OpenUSD repository.

Contributors are welcome on any of these steps. IP protection is a
cross-organization problem -- no single vendor can define the solution,
and the guidance will be better for having more perspectives in the room.

---

## Appendix A: AI-Assisted Drafting

This proposal was drafted with AI assistance (Claude, Anthropic, via
Claude Code) under the direction of Aaron Luk. The conceptual framing,
use cases, and technical judgment come from the human authors and the
working sessions that preceded the drafting. The AI accelerated the
writing; it did not participate in the discussions whose outputs it
received as input.

### Context provided to the AI

The following materials were provided as input context for drafting:

1. **Internal requirements tracking** -- "Configurable IP Protection"
   user story and comment history documenting the evolution of
   requirements, including contributions from Alex Fuchs (NVIDIA),
   Max Bickley (NVIDIA), Aaron Luk (NVIDIA), and Daniel Lindsey
   (NVIDIA).

2. **Working document from Stephen Prideaux-Ghee (PTC)** -- "IP
   Protection" document outlining four pillars: protection against
   dissemination, ephemeral data, copyright, and provenance. Includes
   detailed use cases, approaches, and examples drawn from 30+ years of
   CAD/PLM industry experience.

3. **IP Protection Proposal working session transcript** (2026-04-08) --
   Full transcript of working session with Stephen Prideaux-Ghee (PTC),
   Steve Blackwell (Vertiv), Aaron Luk (NVIDIA), Alex Fuchs (NVIDIA),
   and Daniel Lindsey (NVIDIA). Covered all four IP protection concerns
   with real-world examples from data center infrastructure,
   manufacturing, M&E, and aerospace.

4. **Workflow diagram from Alex Fuchs (NVIDIA)** -- "As of today - a
   complete detached workflow" diagram illustrating the current
   disconnected pipeline from Design → CAD (within ISV/Vendor) to
   Simulate (Customer/Consumer digital twin), highlighting the manual
   work gap that USD-based workflows aim to bridge.

5. **[Separation of Concerns for Identifiers](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)**
   -- The identifiers proposal, used as both a methodological template
   (problem-first, separation of concerns, industry-agnostic framing)
   and a technical foundation (source identifiers as prerequisite for
   provenance and copyright tracking).

### Review and refinement

This is the initial draft. Review and refinement is expected through
community discussion on the pull request.
