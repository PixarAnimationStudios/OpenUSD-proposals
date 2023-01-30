# USD-proposals

Welcome to USD-proposals, a forum for sharing and collaborating on proposals for the advancement of USD.

Before getting started, please familiarize yourself with the contents of the [Supplemental Terms](https://graphics.pixar.com/usd/release/contributing_supplemental.html) page.

## What is a proposal?

- a new schema, such as "Level of Detail for Games"
- an outline for a technical action, such as "Removing the usage of boost preprocessor macros"
- a new development, such as "Evaluation of Hermite Patches"
- a discussion of scope tightening, such as "Standardizing Alembic without HDF5"

For inspiration, here are several proposals that have previously been worked through: https://graphics.pixar.com/usd/release/wp.html

## Relationship to other forums

Initial discussion and coordination of effort may occur in face to face meetings, the usd-interest Google Group, the Academy Software Foundation's wg-usd Slack channels, and other venues. 

When a proposal has taken enough shape that it warrants detailed feedback and iteration, this repository exists as a place to work together on artifacts such as white papers, sample schema definitions, and so on.

## Process for a new Proposal

### Create a Pull Request for the proposal

Fork this repo, create a directory within `proposals/` for the proposal and its materials, and a README.md, then submit a PR. Use the Pull Request Template, and fill in the requested details. The README.md document may contain the proposal, or at a minimum, it should announce the contents of the proposal and how to understand the materials within the proposal. The README.md should also contain notes the author considers important for anyone looking at the proposal, which could include notes that a proposal has been superceded by another, that the proposal resulted in a change to another project, and so on.

The PR may contain other materials to support the proposal, such as white papers, diagrams, sample USD files, and pseudocode. 

### Discuss the proposal

A typical workflow for the proposal PR will be have some initial discussion on the PR itself, and at some point, the PR may be landed here. Iteration of the proposal may proceed via subsequent PRs discussions in the corresponding issue, or using other tools available in github's interface.

At any point, proposal text may be used in other contexts, for example, a proposal may be referenced when writing new schemas or code for USD, although there is no guarantee that any particular proposal will advance beyond a discussion stage.

When a proposal advances beyond being a proposal, that should be noted here, and subsequent development should occur in the appropriate forums. For example, if a proposal has been developed into code and concrete schemas, that might become a pull against the main USD repo. Such a development should be noted in the proposal's README.md file here, with a link to the new pull request.

## Code of Conduct

The success of the forum is predicated on involvement and communication, so consider this an appeal to everyone's creativity and thoughtful consideration.

Civility, inclusiveness, friendship, and constructive collaboration shall be the hallmarks of this forum.

Thank you for your participation!
