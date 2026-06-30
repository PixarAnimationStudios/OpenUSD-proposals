

 # Contributors
 This proposal is an initiative coming from different Ubisoft members working in different studios across the world.
 | Name | Studio | Location | Role |
 |---|:---:|:---:|---|
 | Alessandro Bernardi | Helix | Canada / Montreal | Technical Operations Director |
 | Anthony Mazzier | Helix | Canada / Montreal | Technical Lead |
 | Charles Flèche | Anvil Pipeline | Canada / Montreal | Tool developper (Anvil) |
 | Frieder Erdmann | Snowdrop | Sweden / Malmö | Lead Technical Artist (Snowdrop) |
 | Jason Clark | Redstorm | USA / Cary (NC) | Senior Technical Architect (Anvil) |
 | Kristen Griffin | Reflections | UK / Leamington Spa | Lead Technical Artist |
 | Simon Pardon | Snowdrop | Sweden / Malmö | Technical Artist |
 | Tobias Johansson | Snowdrop | Sweden / Malmö | Lead Progammer (Snowdrop) |


 # Purpose and scope

 The purpose of this proposal is to try to address the way we can store *Levels of Details* (LOD) in a USD File.
 Level of details is a way to reduce memory and or processing power usages in allowing to have different versions of a single feature of an asset. This allows to keep a certain frame rate while keeping still detailed images for game engines.

 The differences between each levels of a LODs affect the quality of the assets, starting, generally, with the highest possible quality, and degrading it along side the depth of levels. The features of an asset that can be addressed in levels of details are:
 - Geometry, reducing the number of polygons, either by modeling low levels of the original geometries or procedurally reducing those with specific technologies.
 - Shading, by using more simple surface models, disabling SSS, using lighters textures, ....
 - Skeleton complexity, reducing the number of weights to compute.
 - ...


 Assets can be any of the standard ones known in the CGI industry at large, ranging from simple props to whole sets for shots animation.

 Solution to address levels of details in a VFX production pipeline tends to be more easily achievable with what USD already provides, like: variants, payloads, and eventually toolings on the DCC side. One the gaming industry, on the other hand, the paradigm cannot be resolved at load time, and so forth, we cannot rely only on the way we store the solution. The paradigm needs to be resolved at render time, implying that the modelisation of LODs in a USD stage needs to make no assumption on when each model will be triggered.

 ## A word on execution

 On the execution side, as evoked in the "On Rigging and Execution in USD" paper, the changing of LODs could sound as of falling in the "Scripted and Triggered Behaviors and Physics" as states changes might be triggered accordingly to animation updates, especially camera movements".

 Nonetheless, it should stay, by design, "frame deterministic", not as would a physical simulation that needs the state of the previous frames, this avoiding falling in the mentioned "hysterisis effect".

 The model should be then "Scene Generators and Filters", and represented as branching instruction graphs, and the existing API, as said in the paper, should be able to address such a model.

 Another point toward execution is that game engines may struggle to go USD native for real time performance issues, this leads to using USD as a data transport facility for this use case, where execution issues are postponed to game engine.


 ## What is not addressed in this draft
 As a first version of the proposal, we didn't put too much focus on every specific features we wanted to store at different levels of details. We focused more on the geometry, but at least surfacing could probably follow the same principles.

 Another topic that is only overseen and that will require more definition is the colision model that has to be used on certain use cases for gaming purposes, mainly with skinned assets.

 Points instancing is also another big part that is strongly tied to LODs and that should be discussed. The proposed model has to find a way to address a per instance of the prototype with different levels of details. There are several ways we can think off, overriding the PointInstancer table, redirecting to prototypes with variants and surely some others, this would be a topic for further discussions.


 # Definitions

 ## LODModel
 An `LODModel` is a term representing an asset that can be spawn in an engine. By extension, what we call a `LODModel` in this proposal is the sum of the different level of details of an asset and the description on how the switching will be done (see heuristic).

 We choose to use concrete nodes rather than API Schemas as this node is completely dedicated to the purpose of LODs as we will see in the proposal.


 ## Level of detail
 A `level of detail` is a description of a single parametrisation of a `LODModel` at a given time. For example, the highest modeling definition of a character will generally with index 0 and called `LOD0`.
 This class can be used to know the partition of prims per level, in order to facilitate tooling on the DCC side.

 ## Heuristic
 `Heuristic` is a description of the criteria needed to choose which level of details to use.
 It could be scene as function f where: *f(parameter1, parameter2, ...) = lod_level*

 In our context, parameters should not be tied to any third parties (ex: Simplygon), but some of them are a good starting point to know the features we need to handle.



 # Proposal


 ## Units
 As some parametrisation might be scene dependant, and so far, based on distances, we will totally rely on the `metersPerUnit` defined in the global metadata.


 ## Tooling Vs Parametrisation
 Rather than having an *on load* representation of the level of details, we have to be able to represent the way we can switch from LODs at different point in time.


 ## LODModel schema
 The LODModel relies on a [IsA schema](https://graphics.pixar.com/usd/release/glossary.html#usdglossary-isaschema).
 If we were only dealing with geometric model, the proposed schema could have derived from [UsdGeomXformable](https://graphics.pixar.com/usd/release/api/class_usd_geom_xformable.html) to have the transformation facilities. But as the LODModel might be used also for shading and others, the base class is [Typed](https://graphics.pixar.com/usd/release/api/class_usd_typed.html) Schema.
 The purpose of this schema is to make a junction between the different level of details and the heuristic that is chosen to select which LOD is active *on screen*.  

 LODModel's attributes are:
 - version: to support updates
 - a relation to the heuristic
 - an array of relations to each level defined as `LODLevel`
 - a type of the LOD, i.e. shapes, materials, ...

 ## Level of definition's schema
 The class that represents one level of details is based on a special IsA schema. This way we can address:
 - complex level of details with many meshes, skinning, materials,...
 - handle [collision models](https://graphics.pixar.com/usd/release/wp_rigid_body_physics.html#collision-shapes) as presented in the rigid body physics.
 - stay opened to further extension on LODs needs (proceduralism, ...).
 - one level might be shared between different LODModels, enabling the possibility (for example) that the same level of detail may be the highest definition in one context (backgrounds), while still being an intermediate level in other contexts.

 It uses a [Collection API](https://graphics.pixar.com/usd/release/glossary.html#collection) to get maximum flexibility on the meshes we want to represent.
 It allows, for example, to select a hierarchy of prims, while still being able to remove some part of it.


 As some heuristic might deal with distance computation, we also need to provide a mean to compute this distance:
 - center: express the point to which distance should be computed.
 - boundingVolume: a relation to prims used to define one bounding volume.
 - computeDistanceTo: choose between the two previous models or the targeted prims computed bounding box.


 ## Heuristic schema
 We decided to go for hierarchical model as some base class can hold generic descriptions. This way, we can specify those attributes for every heuristic:
 - name of the heuristic
 - LOD transition choice, we can choose to have one LOD at a time, switch smoothly between two LODs (depending on further parametrization), or just simply show all, for creation purposes.

 The base model can be enough, on parametrisation stand point, on a creation department where you won't be choosing which model to show, but you need them to be all visible at the same time.
 This is made available by the `lods:transition` parameter:
 - `showAll`: every level are visible at once
 - `fixed`: only one level is applied at one time, it is further defined by a subclass of the heuristic
 - `transition`: this last value allows to have two consecutive models at a time and we should probably handle different ways to express it by percentage, ranges or else. In this proposal we will address this point by ranges.

 By subclassing this class, we can expand and further specialize the heuristic, as a starter here are three propositions:
 - `LODSelectorHeuristic`: a simple chooser where you can select one LOD at a time, the main parameter `lods:LODIndex` allows to choose which level you want to show, and as it can be time sampled, it can be driven by an animation.
 - `LODDistanceHeuristic`: a heuristic based on the distance between a target prim and the LODS
 - `LODCameraHeuristic`: a mock up of camera heuristic selector.


 During internal discussion we stumbled upon having or not a single heuristic for all the LODModels, mimicing what is done with [Physics Scenes](https://graphics.pixar.com/usd/release/wp_rigid_body_physics.html#physics-scenes), and so, not having to link every LODModel to the same instance of the heuristic, allowing it to define it once and for all the stage. This could be a further impprovement that could be applied when the LODModel doesn't define a heuristic relation, and this has to be discussed more broadly.


 ## Class diagram

 ![model](http://www.plantuml.com/plantuml/png/VPJ1RXD138RlynHMBZtGL09k4Q0YAaIbGX5KN107PyQxQpexinfxqrIbxqwiJRQxgTHRrlx7y_iRE-UYMBHle_CHHU3clgFmu1xT_llg-k9h3XGVt2ie527c8Ak6-iAYxAV1cCCLRIZABgZvbj8G3bHnOkMShakW0kzXqN3TaEXdBgABkJfQ1VDWEccm8rdipAIi194gXLoDbjmFwWe99HL044L_kqyBO0gW3RdHAIIYG05GeVH9kING3CxdjkkLuAvXtzXHO84D2wyZEKe1xEO92-imEeFHPKxwjXfiUqfAPKfZdViKkFwLOz_IlCVzdHSiYidJJRPUXmgBQGcVOsJXdBuNRkMOmcZcy0C2YI-y9e6Jlxqev4Gd42rb-a2A7ENKiK8lPCZi0lBsD80T6uyr0QuZsK_5KfEwhd0xuDmLIjfZZFUM3YmUIm1Ee4qM0Yr40avoIp0SgdA15hVSzYrKaRQyviXwFy7QeR_5cc3nvV1Cie279zfZ68ouQE5K3smI7bFLWadOcXb69zzzZ76SdS9rOzXcLTtiYk7M9uZQ44pcHpF87Qjle2gvDRXM2zmkRif4MxNWwUwB1TZuhb48zjreWmeUao7E6og50oKhwcfI48yHd-6PpDrFifVAPRHhG3Zfk7gNAT1sjhQ7-PeSUG5OnLiAi_4R1c0NgM96_VrdYBADwGQZ719lu90gc6gw7FDJBv-mfO8J9sTdP-xH90q7WfQqoK6SiyqFyExVSZbk-L5ih36DZxlWfeenzup4SzcKySkourwSEpXTFVq5mdBvONG5AtYz-ZQHZKDbidbJvvH2tyR_)


 ## Proposed API
 Here is the generic proposition for the LOD schemas.

 ```python
 #usda 1.0
 (
     """ This file describes an example schema for code generation using
         usdGenSchema.
     """
     subLayers = [
         @usd/schema.usda@
     ]
 )

 over "GLOBAL" (
     customData = {
         string libraryName = "LODsSchemas"
         string libraryPath = "."
         string libraryPrefix = "LODsSchemas"
     }
 )
 {
 }

 class LODModel "LODModel"
 (
     customData = {
         string className = "LODModel"
     }
     doc = """Represents a stack of LODs and the heuristic needed at runtime to 
     compute which LOD is visible"""
     inherits = </Typed>
 )
 {
     string lods:version (
         customData = {
             string apiName = "version"
         }

         doc = """Holds model version for further improvements"""
     )

     rel lods:heuristic (
         customData = {
             string apiName = "heuristic"
         }

         doc = """Heuristic to be used at runtime to select the needed LOD, the given
         index correspond to the index in the lods:LodLevels array"""
     )


     rel lods:lodLevels    (
         customData = {
             string apiName = "lodLevels"
         }

         doc = """Array of LODLevel,  ordered according to lods:definitionOrder"""
     )

     token lods:definitionOrder = "highestFirst" (
         allowedTokens = ["highestFirst","lowestFirst"]
         customData = {
             string apiName = "definitionOrder"
         }

         doc = """Defines the order of definitions for lods in lods:lodLevels
         highestFirst => in lods:lodLevels[0] = lod0 has the highest definition
         and in lods:lodLevels[-1] the lowest """
     )

     token lods:levelType = "shapes" (
         allowedTokens = ["shapes","materials","procedural"]
         customData = {
             string apiName = "levelType"
         }

         doc = """What type of data are handled by this model
         can be meshes, materials or a procedural type of data from the engine"""
     )
 }


 class LODLevel "LODLevel"
 (
     customData = {
         string className = "LODLevel"
         string extraIncludes = """
 #include "pxr/usd/usd/collectionAPI.h" """
     }
     inherits = </Typed>
     prepend apiSchemas = ["CollectionAPI:targetPrims"]

     doc = """LODLevel describes 'just one' level of details, it uses a collection api to be
     able to target prims and eventually to discard in those trees some 
     prims for maximum flexibility"""

 )
 {
     point3f lods:center = (0.0, 0.0, 0.0)(
         customData = {
             string apiName = "center"
         }

         doc = """Defines the center of the LOD, used to compute distances"""
     )

     rel lods:boundingVolume (
         customData = {
             string apiName = "boundingVolume"
         }

         doc = """Defines a prim that might be used by heuristic"""
     )

     token lods:computeDistanceTo = "center" (
         allowedTokens = ["center","boundingVolume","boundingBox"]
         customData = {
             string apiName = "computeDistanceTo"
         }

         doc = """Method used to compute the distance from some target to the current LODs, 
         center: will use the lods:center expressed in the schema
         boundingVolume: will use the lods:boundingVolume
         boundingBox: will rely on the compluted bounding boxes of the prims in targetPrims collection
         """
     )

     rel lods:collisionPrims (
         customData = {
             string apiName = "collisionPrim"
         }

         doc = """Defines a prim that is used for collision, will be used by skinned assets"""
     )
 }


 class LODHeuristic "LODHeuristic"
 (
     customData = {
         string className = "LODHeuristic"
         string extraIncludes = """
         #include "pxr/usd/usd/collectionAPI.h" """
     }

     inherits = </Typed>
     doc ="""LODHeuristic class describes the heuristic to switch from one
     lod to the next one, this is a base class that can be overriden
     to get scalability"""
 )
 {
     string lods:name = "default" (
         customData = {
             string apiName = "name"
         }

         doc = """Heuristic's name"""
     )


     token lods:transition = "showAll" (
         allowedTokens = ["showAll","fixed","transition"]
         customData = {
             string apiName = "transition"
         }
         doc = """Transition types
         - showAll: every lods has to be seen (ex: for modeling purposes)
         - fixed: only one lod is shown at a time
         - transition: there is an interval where two adjacent lods could be visible"""
     )
 }


 class LODSelectorHeuristic "LODSelectorHeuristic"
 (
     customData = {
         string className = "LODSelectorHeuristic"
 }
     inherits = </LODHeuristic>
     doc = """LODSelectorHeuristic class enables the possibility to select
     which lod has to be shown"""
 )
 {

     int lods:lodIndex (
         customData = {
             string apiName = "lodIndex"
         }

         doc = """Index of the lod to show, could be time sampled if we want to be able
         to animate levels"""
     )
 }

 class LODDistanceHeuristic "LODDistanceHeuristic"
 (
     customData = {
         string className = "LODDistanceHeuristic"
     }
     inherits = </LODHeuristic>

     doc = """LODDistanceHeuristic class is a specialization of the previous one
     his one handles lods switching based on the distance to some
     prims (camera, transform,...)
     we should probably add some parametrization to express the way to
     compute distance (between transforms, bboxes,...)"""
 )
 {
     # override values from base class
     token lods:transition = "fixed"

     rel lods:target (
         customData = {
             string apiName = "target"
         }

         doc = """Relation to the target prim to compute distance, could be a camera center"""
     )

     float[] lods:intervals = [] (
         customData = {
             string apiName = "intervals"
         }

         doc = """Ordered list of distance to switch lods, if transition is 'fixed'
         ex:
             intervals = [10.0,20.0]
         meaning:
             lod0 is on from 0.0 to intervals[0]
             lod1 is on from intervals[0] to intervals[1]
             """
     )


     float2 [] lods:rangeIntervals = [] (
         customData = {
             string apiName = "rangeIntervals"
         }

         doc = """Ordered list of ranges to switch lods, if transition is 'transition'
         ex:
             intervals = [(0.0,10.0),(8.0.0,20.0),(18.0,30)]
         meaning:
             lod0 is on from intervals[0][0] to intervals[0][1]
             lodi is on from intervals[i][0] to intervals[i][0]
             """
     )
 }


 class LODCameraHeuristic "LODCameraHeuristic"
 (
     customData = {
         string className = "LODCameraHeuristic"
     }
     inherits = </LODDistanceHeuristic>

     doc = """LODCameraHeuristic class is a specialization of the previous one
     this one handles view frustum and the target should be camera prim"""
 )
 {
     # TBD, this just an example, we should give attribute to parametrize the 
     # camera frustum, like overscan,...
 }
 ```

 # Example

 ```python
 #usda 1.0

 (
     defaultPrim = "Root"
     endTimeCode = 100
     metersPerUnit = 0.01
     startTimeCode = 0
     timeCodesPerSecond = 24
     upAxis = "Y"
 )
 # this file is a mockup, it might be totally respectfull to
 # the standard, just is just to show one example

 def Xform "Root"
 {
     def LODModel "lodModel"
     {
         rel lods:heuristic = </Heuristics/byRadius>
         rel lods:lodLevels = [<Levels/level0>,<Levels/level1>]
         token lods:definitionOrder = "highestFirst"
     }


     def Scope "Levels"
     {
         def LODLevel "level0"
         (
             prepend apiSchemas = ["CollectionAPI:targetPrims"]
         )
         {
             rel collection:targetPrims:includes = [</some_meshes...>]

             token lods:levelType = "shapes"
         }

         def LODLevel "level1"
         {
             token lods:levelModel = "auto"
             # parametrization for an auto should be defined
             # in the base class
         }
     }
 }

 def Xform "cameraTrs"
 {
     def Camera "Shot01"
     {
         #...
     }
 }


 def Scope "Heuristics"
 {
     def LODDistanceHeuristic "byRadius"
     {
         string lods:name = "heuristic_byRadius"
         token lods:transition = "fixed"

         rel lods:target = </cameraTrs>
         float[] lods:intervals = [10.0,100.0,inf]
     }
 }
 ```