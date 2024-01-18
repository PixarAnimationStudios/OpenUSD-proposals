# OpenUSD-proposals

Welcome to OpenUSD-proposals, a forum for sharing and collaborating on proposals for the advancement of USD.

Before getting started, please familiarize yourself with the contents of the [Supplemental Terms](https://openusd.org/release/contributing_supplemental.html) page.

If you are interested in browsing existing proposals, please proceed right to [the current list of proposals, with status information](https://github.com/orgs/PixarAnimationStudios/projects/1/views/1).

## What is a proposal?

- a new schema, such as "Level of Detail for Games"
- an outline for a technical action, such as "Removing the usage of boost preprocessor macros"
- a new development, such as "Evaluation of Hermite Patches"
- a discussion of scope tightening, such as "Standardizing Alembic without HDF5"

For inspiration, here are several proposals that have previously been worked through: https://openusd.org/release/wp.html

## Relationship to other forums

Initial discussion and coordination of effort may occur in face-to-face meetings, the [AOUSD forum](https://forum.aousd.org/), the Academy Software Foundation's wg-usd Slack channels, and other venues. 

When a proposal has taken enough shape that it warrants detailed feedback and iteration, this repository exists as a place to work together on artifacts such as white papers, sample schema definitions, and so on.

## Process for a new Proposal

### Create a Pull Request for the proposal

1. Fork this repo.
2. Create a directory within `proposals/` for the proposal and its materials, and a README.md.
    1. The README.md document may contain the proposal, or at a minimum, it should announce the contents of the proposal and how to understand the materials within the proposal. 
    2. The README.md should also contain notes the author considers important for anyone looking at the proposal, which could include notes that a proposal has been superseded by another, that the proposal resulted in a change to another project, and so on.
3. Submit a PR and fill out the provided sections in the pull request body.
    1. The PR may include links to supporting materials that could not be included with the proposal files, such as white papers. Add links to the "Supporting Materials" section of the PR body.
    2. Please mention and link any issues and PRs in [OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD) or [OpenUSD-proposals](https://github.com/PixarAnimationStudios/OpenUSD-proposals) that are related to the new proposal. A label will be created to link relevant discussions together. 

### Discuss the proposal

A typical workflow for the proposal PR will have some initial discussion on the PR itself. Once some level of consensus has been reached on the proposal details, the PR may be landed. Iteration of the proposal may proceed via subsequent PRs, discussions in the corresponding issue, or using other tools available in github's interface.

New issues and PRs related to the proposal should be linked to the initial proposal by [autolinking](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls#issues-and-pull-requests) the original proposal PR (eg, #1234).

At any point, proposal text may be used in other contexts. For example, a proposal may be referenced when writing new schemas or code for USD. Referencing a proposal in this way does not guarantee that the proposal will advance beyond a discussion stage.

When a proposal has been approved as a starting point for implementation, that should be noted here with an updated proposal status (see section below). Subsequent development should occur in the appropriate forums. For example, if a proposal has been developed into code and concrete schemas, that might become a pull request against the main OpenUSD repo. Such a development should be noted in the proposal's README.md file and linked to the pull request in the main OpenUSD repo.

### Proposal Status

There are five proposal statuses:

- **To do** - This item hasn't been started
- **Draft** - Proposal is work-in-progress, but open for feedback and reviews
- **Published** - Proposal is approved to use as a starting point for implementation
- **Implemented** - Proposal has been implemented
- **Hold** - Proposal is not being worked on

You can monitor your proposal status using the [OpenUSD Proposals Status page](https://github.com/orgs/PixarAnimationStudios/projects/1/views/2)

New PRs are automatically given the **To do** status. This indicates the proposal is still in an early draft that is not yet ready for discussion/comments.

When the proposal is changed to the **Draft** status, this indicates the proposal is ready to be reviewed and discussed; however it is still work-in-progress and may continue to be updated.

Once a proposal is complete and fully reviewed, it will be merged and can be moved to **Published** status. This indicates the proposal can be used as a starting point for implementation. Any changes to the proposal at this point would need to be filed as a new PR.

Once implementation work has been completed, the proposal will be moved to **Implemented** status, with indication of which version of USD the proposal was implemented in. 

## Code of Conduct

The success of the forum is predicated on involvement and communication, so consider this an appeal to everyone's creativity and thoughtful consideration.

Civility, inclusiveness, friendship, and constructive collaboration shall be the hallmarks of this forum.

Thank you for your participation!
