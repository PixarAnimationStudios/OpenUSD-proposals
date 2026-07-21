# Semantic Captions

Copyright &copy; 2024, NVIDIA Corporation, version 1.0

## Goal
Extend the `usdSemantics` domain with a schema for natural language 
semantic descriptions of subgraphs of an OpenUSD stage.

## Background
The proposed semantic labels API provides a mechanism for tagging
subgraphs with labels using different taxonomies.

```
def Mesh "orange" (apiSchemas = ["SemanticsLabelsAPI:tags",
                                 "SemanticsLabelsAPI:state"]) {
    token[] semantics:labels:tags = ["fruit", "food", "citrus"]
    token[] semantics:labels:state = ["peeled"]
}
```

Labels as discrete tokens makes it easy to construct merged 
sets of ancestors (to aid `IsLabeled` queries) or generate
segmentation images. Labels also suggest certain user interfaces and 
query considerations (ie. drag and drop labels onto prims).

## Proposal
Some workflows are looking for natural language descriptions of
subgraphs that can be used to describe a variety of features.

```
def Xform "dancing_robot" (
    apiSchemas = ["SemanticsCaptionsAPI:summary",
                  "SemanticsCaptionsAPI:skills"]
) {
    string semantics:captions:summary = "This is a bipedal robot made up of metal that is painted red. The robot was manufactured in 2024."
    string semantics:captions:skills = "This robot can perform a box step, a grapevine, and the waltz."
}
```

Captions are expected to be longer phrases, sentences, or paragraphs.
A single prim may have multiple named instances of a caption to
suggest its intent. Multiple instances can also allow for multiple language
support.

### Time Varying Captions
Just as labels benefit from being able to describe state changes 
over time, captions may also be time varying.

```
def Xform "learning_robot" (
    apiSchemas = ["SemanticsCaptionsAPI:skills"]
) {
    string semantics:captions:skills.timeSamples = {
        0 : "The robot does not know how to dance",
        100 : "The robot is learning the box step",
        150 : "The robot knows the box step"
    }
}
```

### Ancestral captions
It's expected that captions describe the prim's subgraph. A prim may
look to ancestors for additional context. API will likely be
provided to aid in this.

```cpp
// Find either the instance of the captions API applied directly
// to prim the nearest hierarchical ancestor of the prim.
UsdSemanticsCaptionsAPI
FindNearest(const UsdPrim& prim, const TfToken& instance) const;

// Find all caption instances applied directly to the prim or
// to ancestors of the prim
std::vector<UsdSemanticsCaptionsAPI>
FindHierarchical(const UsdPrim& prim, const TfToken& instance) const;
```

## Alternatives
### Use `documentation` metadata
The documentation metadata would be an alternative. However, it 
does not allow for multiple instances and may conflict with user
documentation. For example-- `doc = "This asset is designed for background usage only"`.

### Use `assetInfo` metadata
Unlike the `documentation` field, an asset info dictionary
could capture multiple strings in the dictionary. However, they
cannot vary over time.

### Use `SemanticsLabelsAPI`
The proposed labeling API could be used to capture captions. 
There are two reasons to have distinct APIs.
* An authoring user interface for adding labels should be 
different than the user interface for adding descriptions. (ie. 
drop down box vs. text box).
* Merging ancestor labels into sets to perform membership
queries has many potential applications (ie. semantically 
partioned image masks). There is no equivalent workflow for
captions.