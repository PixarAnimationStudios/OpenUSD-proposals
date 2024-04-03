[Status:Draft]()
# Use of OpenTimelineIO for arbitrary time-series data

- Copyright: Signly Ltd & Michael Davey Consulting Ltd, version 0.1
- License: [Apache 2.0](/proposals/usdotio/LICENSE.md)

## Use Case
- **In order to** quickly interpret and gain insights into the results and find the specific scene(s), object(s), time(s), ... I am interested in,
- **As a** creative,
- **I want to** run task-oriented analysis tools on my OpenUSD project and see the results represented on a timeline as time-series data
- **Whereas currently** I would need to either,
    - Where possible, build a custom extension with its own timeline widget, or
    - Where possible, customise the standard DCC or NLE sequencer timeline widget to fetch the results from the analysis tool, or
    - Use an external analyser application with its own timeline widget

## Example DCC/NLE Workflow

1. A creative working in a DCC or NLE has loaded up a project with at least one timeline defined.
    - They select the timeline then pick an analysis tool to run on the timeline.
2. The analysis tool produces its output (arbitrary time-series data) in OpenTimelineIO format.
    - The track *kind* is set to a tool-specific name (labeled with a tool-specific schema).
    - The OTIO data in inserted into OpenUSD (OpenUSD OTIO schema)
3. The DCCs or NLEs standard sequencer timeline UI component can render the time-series data on the timeline without requiring the analyser tool to be present and without needing to know about the semantic meaning of what it is displaying.
    - If the appropriate analysis tool is present, additional functionality (such as context-sensitive menu options) may be enabled in the Sequencer 
    - The sequencer or extension manager may be able to automatically find and install / enable the extensions indicated by the track kind if the tool is not present or not enabled by default.

<div style="text-align: center;">

![Alt](/proposals/usdotio/Analysis%20menu.png)

</div>

In a DCC or NLE, analysis tools lend themselves to implementation using a plugin architecture, as this empowers creative professionals to pick the best tools for their specific workflow from a rich ecosystem.
- In Omniverse terminology for instance, an analysis tool would be an Omniverse extension.
- The tool may very well call a microservices API such as an Omniverse microservice or an NVIDIA Inference Microservice (NIM).


![Alt](/proposals/usdotio/Workflow.png)


## OpenUSD serialisation
This proposal creates an OpenUSD serialisation of the OpenTimelineIO schema, to complement the existing JSON serialisation.  The intention is that transliteration between OpenUSD and JSON serialisations of the OpenTimelineIO schema is lossless.

To achieve this serialisation in OpenUSD using OpenUSD's atomic types, we create a new OpenUSD codeless schema to hold the OpenTimelineIO data.

### OpenUSD OTIO serialization (proposed)
OpenTimelineIO serialization in OpenUSD looks like this (proposed):
- [generatedSchema.usda](https://docs.google.com/document/d/1pjWVgwJjt6N6V868geHNKBnqlZ_ACZCsEfZIaQRe-18/edit#heading=h.nx4ytxndufde)

### Example
An example OpenUSD file using the above schema:
- [testenv/testUsdOtioAdd1/baseline/out.usda](https://docs.google.com/document/d/1pjWVgwJjt6N6V868geHNKBnqlZ_ACZCsEfZIaQRe-18/edit#heading=h.h75d7jxyqeoh)

## Example timelines
### Object Analysis
Here is a mock-up of a timeline after an 'Object Analysis' tool has been run on the video elements of the timeline. The time-series data represents in which frames particular objects are present.
- This could potentially enable search functionality that would be able to respond to queries such as, "Show me all the scenes containing a woman wearing a wedding dress"

![Alt](/proposals/usdotio/Object%20Analysis.png)

### Speaker and Scene Analysis
Here is a mock-up of a timeline after both a 'Speaker Analysis' tool and a 'Scene Change Analysis' tool have been run on the the timeline. The time-series data represents in which frames particular characters are speaking, and where each scene change occurs.

![Alt](/proposals/usdotio/Speaker%20and%20Scene%20Analysis.png)

## Command line (proposed)
1. Embed the OpenTimelineIO metadata from otio.json into a OpenUSD file:
    - `usdotio add otio.json usdfile.usd`
2. Save the OpenTimelineIO metadata written by #1 to a JSON file:
    - `usdotio save -o otio.json usdfile.usd`
3. Find the Omniverse sequencer information, remove, convert to
OpenTimelineIO format and add back in again as OTIO metadata
    - `usdotio update -v2 usdfile.usd`

## Strawman implementation (PR #2995)
We've produced a proposed implementation the usdotio 'add' and 'save' commands (and an initial implementation of an OpenUSD codeless schema for OTIO), to spark discussion.

*"Adds a python script to add OpenTimelineIo data to and from a .usd file. The .otio information is stored in a tree fashion for easy inspecting it with usdview or similar.
You can have multiple .otio timelines, so that, for example, a TV set model carries its own .otio timeline differently from the main .otio at the root."*

- [**Created usdotio python script to add or extract .otio data from USD** *#2995*](https://github.com/PixarAnimationStudios/OpenUSD/pull/2995)

## Follow-on work
If this work is favourably recieved by the various stakeholder communities, we plan to create a new version of Omniverse's Sequencer extension that can read from and write to the OpenTimelineIO metadata section of OpenUSD described above in close collaboration with the Omniverse community, to further demonstrate the utility of this proposal.

## FAQs
An ongoing discussion within the OTIO community is how best to handle both dense time-sampled data and sparse time-sampled data. This proposal is silent on the subject: the same challenges (and potential solutions) that apply to OTIO data represented in JSON, also apply to that same OTIO data when represented in OpenUSD format. See [*Dense vs Sparse Time-Sampled Data*](https://docs.google.com/document/d/1pjWVgwJjt6N6V868geHNKBnqlZ_ACZCsEfZIaQRe-18/edit#heading=h.4yoitppk0adj) for further discussion on this subject.

## Supporting documentation
- [PDF presentation](/proposals/usdotio/OpenTimelineIO%20&%20OpenUSD.pdf)
- [OTIO + OpenUSD discussion / PoC document on ASWF.:OTIO](https://docs.google.com/document/d/1pjWVgwJjt6N6V868geHNKBnqlZ_ACZCsEfZIaQRe-18)
