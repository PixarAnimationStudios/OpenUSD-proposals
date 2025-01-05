# Profiles in OpenUSD

Version 0.7 2025 Jan 5
	Authored capabilities and schema applied capabilities
version 0.6 2025 Jan 4
	final capabilities, component capabilities, implementation capabilities
version 0.5 2025 Jan 3
	strawman Capabilities DAG
version 0.4 2024 Dec 31
	reorganize requirements as main part of document
	fold more scratch notes into main body
version 0.3 2024 Dec 19
	rewrite requirements based on brainstorming with spiff
version 0.2 2024 Dec 14
	revise introduction
	start cleaning ISO 19650 section
	fold notes into main body
	organize body to match the requirements index
version 0.1, 2024 Dec 12, collection of scratch notes, Requirements

TO DO:

[ ] ProfileCapabilityAPI, declares the need for a capability at a scope
[ ] ProfileCapabilityDescriptionAPI, provides detailed metadata about a Profile Capability
[ ] Describe side car profile files
[ ] OpenUSD SDK design

## Introduction

USD's flexibility enables custom schemas, proprietary formats, and extensions, but this creates significant interoperability challenges. Schemas are large, yet applications typically implement the subsets that matter to them, resulting in awkward overlap with document capabilities. The USDZ specification enforces strict resource portability by restricting what may be contained in an archive, and thus variants appear as a work around, such as Adobe Scene Description (ASD) and Apple's RealityKit which both uses proprietary schemas and run time components.
An extension system should enable an application to determine and manage:

- A document's compatibility and runtime requirements, 
- Interoperability with specific layers, prims, and scene hierarchies within a document,
- Whether a document may satisfy a given set of functional requirements.

## Profile Requirements

### Domains

Profile functionality applies to three different domains.

- Document
    - Data that applies at a document level.
- Scopes
    - Data that applies at a specific scope within a document.
- Application
    - Data that applies to the application itself.

### Profiles

A Profile is a versioned, directed graph of capabilities. Profiles may be obtained appropriately to its  domain.

- It may be encoded in a USD file on scopes via an applied schema.
- It may accompany a USD file as a separate manifest file, which may itself be a USD file containing a root prim with an encoded profile.
- It may be dynamically constructed by an application.

A profile could potentially guide the build process for OpenUSD, as an alternative mechanism to command line switches or CMake options. That would be out of scope for this project.

### Capabilities

Profiles are constructed from capabilities. A capability is an identifier indexing particular functionality. Capabilities are organized in a directed graph, and the leaves of that graph are Profiles.

- Capabilities must co-derive ancestrally
- Capabilities must independently interoperate via ancestral capabilities
- Capabilities that require sibling interoperability require a co-descendant feature such that interoperable profile capabilities become ancestral

Features are named via a reverse domain scheme, for example, com.pixar.base is the root domain all other features derive from. The specification of the standard OpenUSD features, which reflect the current state of the OpenUSD repository, is part of the initial delivery of Profiles. Vendor features may be constructed on top of the standard features using the mechanisms described above.

The reverse naming enables clear namespacing, which has advantages for clear diagnostic messages. There's no dependence on URLs or other live resources, providing stability and simple queries. There is however the need for a central authority for registration; at first this will be the OpenUSD distribution itself.

A profile Capability represents a grouping of functional abilities. A capability may group all the functionality of USD core physics, or subdivision surfaces, or some other component that brings new functionality. 

Capabilities are organized into a directed acyclic graph (DAG), and terminal nodes in the graph are profiles.

A system may declare that it supports a capability, a document may declare that it requires a certain capability. In general, a domain of interest, whether it is an application, or a document, or some other system may be queried of its capabilities in terms of a profile, or a list of capabilities.

- Given this profile, what capability level do you offer?
- Given this profile, what required capabilities are missing?

A domain may respond with:

- None
  - The scope is explicitly incompatible.
- Not Applicable
  - The scope is neither incompatible nor interoperable at any level. For example, a query against an implementation detail such as the use of OpenGL might be of interest when queried against a system such as Storm, it is of no interest when queried against a format scope.
- View
  - The scope is viewable at a certain level, either generically such as an Image Poster, via a Polygonal representation, via Subdivision Surfaces, so on, and via feature sets such as RealityKit, AdobeSubstance, Renderman, and so on.
- Review
  - The prim is reviewable for validation, approval, and introspection purposes via appropriate mechanisms as may be domain specific.
- Interoperable
  - The prim may be reliably modified.

A capability query follows standard LIVRPS compositional rules, and kind rules. The query is concluded at a leaf scope, or at scope of component kind. The query frontier is expanded at USD payloads, so an asset hierarchy should be designed appropriately to limit a query. For example, if a city has "city blocks" as components, asking the city for its capabilities can be determined quickly without loading every building in the city. As another example, assets offering application specific capabilities, such as a choice between a web proxy, a game asset, and a full technical asset, may use components corresponding to those high level application needs to enable rapid discovery of a proxy without loading everything.

A capability may be marked in its metadata as a component, indicating that a query does not need to introspect a layer further, as a further aid to streamlining queries.

Capabilities may be authored on scopes, and this utilization is expected during document distribution and delivery for streamlining and efficiency. Accordingly there are two kinds of queries possible; a query on explicitly authored capabilities, and an exhaustive introspection to discover capabilities encoded in a document by virtue of having had capabilities required through the application of schema APIs to a scope. Applied schemas therefore may also have a query functionality on them that describes the set of capabilities conferred on the scope by the schema. It would make sense to audit and retrofit existing applied APIs with capabilities.

See Appendix A for a suggested preliminary capability DAG for OpenUSD.

### Versions

Profiles may be versioned. As an example, there might be a Reality Kit 1.0 profile, and a Reality Kit 2.0 profile. Note that asset versions, also known as editions, are not part of the Profiles proposal.

- If a profile references a versioned ancestor, the versioned ancestor is preferred
- If a profile references a non-versioned ancestor, the greatest numbered versioned variant is preferred

It is proposed that versions are indicated via the semver major.minor.patch system. This system is well known, and enables easy determination of version precedence and compatibility, including checks for exact versions, ranges, and so on.

### Validation

Profiles will leverage the UsdValidator system to check that authored profiles are not contradicted by authored prims in a document. This check is performed by performing an explicit check on a document as well as an applied check, and reporting whether the explicit check is equal to the applied check, or perhaps whether the explicit profile is a superset of the applied profile. Other tools include:

- usdchecker
  - Check an asset for validity given a profile.
- usdprofile 
  - traverses a file and rewrites as necessary profile information to satisfy a usdchecker request and annotation non-core requirements.

Applications include such cases as:

- Asset pipelines validating files against a profile to ensure project requirements are meant.
- Asset vendors could use compatibility information to check deliveries before submission.
- Interested parties, such as AOUSD or vendors, to investigate certification and badging services. Certification and badging is out of scope for the Profiles project itself.
- Library browsers could filter documents.

### Late Binding

Late binding refers to the idea of extending OpenUSD functionality on demand at runtime. Late binding could provide key functionality for users of the Profile system; for example, an application could discover that a given asset needs a particular schema to be present for the Review capability. The ability to late load the schema would provide a critical extensibility and interoperability mechanism. 
Late binding allows systems to dynamically configure workflows, validations, and data handling logic based on EIR metadata or rules. If a certain properties (e.g., fire ratings, material quantities) must be exchanged in a specific format, a late-bound system could dynamically incorporate the required validation logic or property schemas without modifying the shared base. Extensions or updates to evolving schemas could be implemented and deployed without requiring changes to existing software infrastructure. 
Although the implementation of late binding is out of scope for the Profiles project, some useful applications are noted here:

- Existing OpenUSD plugin points could be extended with on-demand loading.
- Schemas could be bundled in an usdz archive, or encoded in a usd file.
- glslfx shaders could be bundled, encoded, available via plugins, or the file system.
- Asset resolution could be extended at runtime.

Late binding mechanisms could enable an interested party, such as AOUSD or a vendor to create a centralized registration and delivery point for validated plugin and extensions.

### Appendix A. Taxonomy

Proposed Capability DAG Structure (Strawman for discussion)

Capabilities are tags in reverse domain order. Capabilities reference their direct ancestors, and only ancestors previously declared, thus ensuring that the capability graph is a directed acyclic graph. The DAG is rooted at a node named root which confers no capabilities, but always exists.

Syntax:

```
name {, version} {[ancestor]} {final}


name [ancestor]
name, version [ancestor]
```

DAG:

```
root [] // common ancestor all capabilities
usd [root]
python [root]
usd.geom [usd]
usd.geom.subdiv [usd.geom]
usd.geom.skel [usd.geom]
usd.shadeMaterial [usd]
usd.imaging [usd.geom.subdiv, usd.shadeMaterial]
usd.format [usd]
usd.format.usda [usd.format]
usd.format.usdc [usd.format]
usd.format.usdz [usd.format.usda, usd.format.usdc]
usd.format.abc [usd.format, usd.geom]  // relies on geometry features
usd.format.obj [usd.format, usd.geom]
usd.python [usd, python]
usd.physics [usd.geom]
```

Vendor domains have their own root, the exact name is chosen by the vendor.

```
apple [root] // Apple specific subsystems are present
apple.realityKit [usd.physics, usd.imaging, usd.geom.skel]
apple.format.realityKit [apple.realityKit, usd.format.usdz]
```

Versions are independent, as core functionality is assumed to come from an ancestor, consider MaterialX; the version may be known or unknown:

```
matx [root]
usd.format.matx, [matx, usd.format, usd.geom, usd.shadeMaterial]
usd.format.matx, 1.38 [matx, usd.format, usd.geom, usd.shadeMaterial]
usd.format.matx, 1.39 [matx, usd.format, usd.geom, usd.shadeMaterial]
```

Capabilities may be roll ups of simpler capabilities:

```
usd.format.gltf-read [usd.format, usd.geom, usd.shadeMaterial]
usd.format.gltf-write [usd.format, usd.geom, usd.shadeMaterial]
usd.format.gltf [usd.format.gltf-read, usd.format-gltf.write]
```

Profiles are terminal nodes that may be used to describe a feature level.

```
usd.profile, 25.05 [usd.geom.skel, usd.physics, …]
```

The scheme could apply to Hydra:

```
hd [usd.imaging]
hd.subdiv [hd]
hd.splat [hd]
hd.matx [hd, matx]
hd.hio [hd]
hd.hio.avif-read [hd.hio]
hd.hio.exr-read [hd.hio]
hd.hio.exr-read [hd.hio]
hd.hio.exr [hd.hio.exr-read, hd.hio.exr-write]
hd.hio.png-read [hd.hio]
```

Implementation details are typically marked as final, and are useful to query against a system, rather than a document. If recorded in a document, they indicate that the detail is required for interpretation of the document.

```
khronos.opengl [root]
intel.tbb [root]
```

In these examples, the capabilities are assigned to a vendor, however, they refer to root as an ancestor, because there are no characteristics beyond ownership interred by being in a vendor domain.

### Appendix B. ISO 19650

Some inspiration for Profiles came from ISO 19650, so a brief overview is provided here for context.

The IFC (Industry Foundation Classes) schema demonstrate modularity via a graph of dependent extensions that introduce new capabilities. This structure is intended to enable domain interoperability via the composition of distinct features. ISO 19650 is a series of standards that define a framework for collaborative management of information in the realm of buildings and infrastructure throughout the lifecycle of assets and is widely recognized wherever standards based information exchange is mandated or beneficial.

The standard is divided into several parts, each addressing different aspects of information management. Work is ongoing to introduce further chapters around health and safety and project management.

- ISO 19650-1: Concepts and principles.
  - Introduces the framework and provides high-level guidance on its implementation.
- ISO 19650-2: Delivery phase of assets.
  - Focuses on managing information during the design and construction phases.
- ISO 19650-3: Operational phase of assets.
  - Extends the framework to asset operation and maintenance.
- ISO 19650-4: Organization and digitalization of building information
  - Specific schemas related to construction
- ISO 19650-5: Security-minded approach.
  - Provides guidelines for securing sensitive information.

Key Principles of ISO 19650:

- Standardized and modularized views enable formal conformance levels and collaboration.
  - Preview.  An asset may be viewed to a certain degree of fidelity
  - Coordination and Review. An asset may be viewed and introspected to the degree required to share details, gain consensus, and support sign off processes.
  - Design Conformance: Full parametric fidelity and editing of an asset, enabling cross application interoperability.
  - Exchange Information Requirements (EIR)
  - Specify what information is needed, by whom, and at what project stage.
  - Late-binding approaches to implementation can greatly aid in supporting these requirements flexibly.
- Asset Information Requirements (AIR): 
  - Define information needs for managing the asset during its operation.
- Common Data Environments (CDE)
  - Establish workflows for information management: producing, sharing, and approving information.
- Roles and Responsibilities:
  - Assign information management responsibilities to specific roles like the Lead Appointed Party and Task Teams.
- Formal Hierarchy of Schemata:
  - The hierarchy includes general principles, specific extensions (like Exchange Information Requirements), and derived structures (project-specific workflows).
- Schema Interoperability:
  - Prioritizes interoperable workflows. Document and manage project lifecycle via interoperation of design, construction, and operational applications.
- Dynamic Binding of Extensions:
  - Dynamic EIRs enable tailoring information to project needs without altering the base standard.
- Lifecycle Thinking:
  - Information is managed across all asset lifecycle stages, from design to operation to decommissioning.
- Validation Framework:
  - Information management processes ensure compliance with requirements at various stages.
- Extensibility without Duplication:
  - Extensions reuse core principles without duplicating base definitions, maintaining efficiency and scalability.

### Appendix C: Links

- Original propsal: https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/75
- Internal JIRA USD-10252
- ISO 19650 overview https://www.cdbb.cam.ac.uk/system/files/documents/InformationManagementaccordingtoBSENISO19650GuidancePart1Concepts.pdf
- RDN https://en.wikipedia.org/wiki/Reverse_domain_name_notation
