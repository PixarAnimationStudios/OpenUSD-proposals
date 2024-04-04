# Semantic data in USD

Copyright &copy; 2022-2024, NVIDIA Corporation, version 1.0


Dennis Lynch  
Eric Cameracci


## Overview

USD is quickly becoming the standard for describing 3D objects to be used for synthetic data generation, but it currently does not have a standard for describing and storing object semantics.  

Semantic data is vitally important to synthetic data generation and AI-driven systems. These labels provide meaningful information about data, making it easier for machines and algorithms to understand and process the content. Semantic labels are essential in supervised machine learning tasks, where a model is trained on labeled data to make predictions on new, unseen data. Having accurate semantic labels on 3D objects at the pixel-level gives rendered synthetic data an advantage over traditional human-labeled real-world captured data.

Semantically labelled data also enables new ways to search-for and find assets based on semantic attributes, without needing to know about asset paths, names, or directory structures.  Semantic data can also provide additional information about an asset's "state", makeup, or other meaningful information.

While it is possible to add custom schema and metadata to USD prims, it would be beneficial for the community using semantic data to agree upon a basic standard for the handling of semantic data within the official USD specification to promote interoperability and discoverability as more applications and content are created for the purpose of generating synthetic data or AI tools utilizing semantic information.

## Schema proposal

The schema can be found [here](schema.usda)

```
#usda 1.0
(
    subLayers = [
        @usd/schema.usda@
    ]
)

over "GLOBAL" (
    customData = {
        string libraryName = "usdSemantics"
        string libraryPath = "./"
    }
) {
}

class "SemanticsAPI" (
    inherits = </APISchemaBase>

    customData = {
        token apiSchemaType = "multipleApply"
        token propertyNamespacePrefix  = "semantics"
    }
)
{
    token[] labels (
        doc = "List of semantic labels"
    )
}
```

## Key Considerations

With semantic labels, we want to move away from naming conventions or parsing prim paths/names to extract information.  
An object could be `/kitchen/accessories/cups/wine_glass_D` or 
`/props/glasses/french/long_stemmed_wine_glass_83` but both would have the same or similar _semantic_ labels.

* Needs to store an arbitrary number of labels, as "meaning" grows among users
  * Especially true for labels to be applied in the user's native language
* Needs to be multiple-apply, as semantic meaning greatly depends on context. Examples:
  * What _is_ an object? A wine glass. `class:wine_glass`
  * What is it _made of_? Glass. `material:glass`
  * What is it _for_? Drinking. `purpose:drinking`
  * Where can it be located? Cabinets, tables, hands, etc. `location:[interior, kitchen, held, table]`
  * Is the object, or its style, region specific?  `locale:[Europe, France]`
* Needs to be relatively lightweight for performance.
* A single asset may require multiple taxonomies for multiple training paradigms
* Semantic labels must be interpretable on `render products` like images for computer vision pipelines that may not have access to the OpenUSD API.
* Needs to be able to vary over time to encode information like "state":
  *   A door is always a door, but it could be `open` or `closed`
  *   Electronics could be `on`/`off`

A Multiple-Apply API Schema works well for defining semantics about a prim, and allows us to query the data through `HasAPI` instead of having to parse through informal ways of storing information on a prim such as `metadata` or `userProperties` and will diferentiate assets that do and do not have semantic labels.


- `assetInfo` - More suited to information about the digital asset, not its semantic meaning(s)

- `userProperties` - Too informal, do not want to be a dumping-ground for lots of data

- `Metadata` - Too informal, do not want to be a dumping-ground for lots of data.  Cannot vary over time.  It could be possible that the semantic "meaning" of something could change over time.
  
  _Example_: At first an object is a wine glass for drinking, but after dropping it from a physics simulation it is now shards of glass - not for drinking.

- `Kind` - Must be pre-defined. Cannot vary over time. Better suited for filtering or interacting with objects on the Stage, not for rendering or label data.

### Why a list?

What an object "is" becomes very tricky with the nature of human language. Is the object an `automobile`, a `vehicle`, or the more informal `car`?  
This is especially true when considering multiple languages: `car`, `Auto`, `voiture`, `bil`, `coche`, etc.

Objects can also have more detailed semantics depending on their context.

Examples:
 -  `['vehicle', 'emergency vehicle', 'ambulance']`
 -  `['chair', 'office furniture', 'executive chair']`

By having a list, semantics on a prim can be additive, increasing the understanding of what the object is for more people and use cases, allowing filtering for the terms that are applicable to the user.


### Encoding semantic "type"

Within the machine learning community, 'class' is a very common moniker for defining a category for semantic labels, but there could be more "types" of semantic labels. An object's `class` could be `vehicle`, its `sub-class` `ambulance`, and it's material semantics `metal` or `steel` for certain parts, etc.

For this we took inspiration from existing USD Schemas such as `CoordSysAPI` and light linking that encode meaning in the instance name of the schema object.

Preferring:

```
token[] semantics:class:labels = ["animal", "bird", "penguin"]
```

instead of multiple instances on the same prim just to contain all of the information for all possible `class` labels

```
token semantics:Semantics_aDa0:semanticType = "class"
token semantics:Semantics_aDa0:semanticLabel = "animal"

token semantics:Semantics_d282:semanticType = "class"
token semantics:Semantics_d282:semanticLabel = "bird"

token semantics:Semantics_c0nr:semanticType = "class"
token semantics:Semantics_c0nr:semanticLabel = "penguin"
```

Or requiring string parsing operations

```
string[] semantics:instance_name:labels = ["class:animal", "class:bird", "class:penguin"]
```

The proposed method has better performance as the number of labels of the same type increase on a prim to dozens, hundreds, or thousands of labels.

### Multiple Taxonomies

The combination of a MultipleApply schema and using prim instance names as "special" identifiers allows semantic information to be stored in USD from multiple sources of taxonomy, while still retaining additional existing taxonomy.

Example of a "police car" prim semantics from different taxonomy sources:
```
omniverse-simready: ['emergency_vehicle']

# COCO has no special taxonomy for police vehicles so "car" might be most appropriate
ms-coco-stuff: ['car'] 

kitti: ['vehicle-other']

ImageNet_classID: ['734']

ImageNet_className: ['police van', 'police wagon', 'paddy wagon', 'patrol wagon', 'wagon', 'black Maria']
```
Here, a user would "query" for semantic prim data of only the specific taxonomy that is relevant to their needs. (ex: `ImageNet_classID`)

Users can also later add additional semantics for new or missing taxonomies to the prim data.

### Semantic Aggregation

"Aggregating" semantic data is essential to workflows.  A prim could have the semantic label of `door`, but that is missing wider context.  Is the prim a door inside of a room, on the exterior of a building, part of a vehicle?

A method should be provided to "aggregate" parent semantics in a consistent way that allows users to understand the semantic heirarchy.

Example prim setup:
```
└── xform - car
    ├── wheel
    ├── door
    │   ├── window(glass)
    │   └── handle
    └── seat
```
Querying the semantic hierarchy should should return a uniquified list(Set) of labels, where ordering is determined by ancestral distance from the prim being queried, and the first time a label is encountered in the ancestors-walk determines its position in the list.

example results:
```
Aggregation query on handle: ['handle', 'door', 'car']
Aggregation query on seat: ['seat', 'car']
```

### Proposed Methods

The `primvarsAPI` has provided some inspiration for possible methods that would be used for semantics:

```
GetSemanticLabels() - Returns list of `labels` on prim
GetSemanticInheritedLabels() - returns an aggregated ordered set of `labels` from the prim and its parent prims
```

### Tokens vs Strings

Consideration was taken for the datatype being tokens or strings.  Considering that semantic labels should be more read-intensive rarely (if ever) written/updated, tokens are thought to be the better representation.

Some performance testing was done, and in some cases StringArray performed better than TokenArray in Python, the difference was negligible and could be attributed to the overhead of converting tokens to native Python strings.

Tokens might also facilitate future expansion use of `allowedTokens` for contraining semantic labels, but that will not be a part of this proposal at this time.

## Out-of-Scope

The purpose of schema is defining _how_ to define and store semantic data on prim data within a USD file.

What this is _not_ doing is defining specifics on semantics, taxonomy, or ontologies.  

There are already multiple large public datasets with their own label taxonomies for classification ([MS COCO](https://cocodataset.org/#stuff-eval), [ImageNet](https://deeplearning.cms.waikato.ac.nz/user-guide/class-maps/IMAGENET/), [KITTI](https://www.cvlibs.net/datasets/kitti/), [SUN RGB-D](https://rgbd.cs.princeton.edu/), [NYU](https://cs.nyu.edu/~silberman/datasets/nyu_depth_v2.html), etc).  

Trying to define a specific agreed-upon taxonomy for classification across the industry is beyond the scope of this proposal. So this is not trying to dictate `car` vs `vehicle` vs `automobile` for a specific label.

Dicussions about semantics often devolve into debating over specific labels and consensus can take a long time.
