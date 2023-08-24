# Namespace Editing

Copyright &copy; 2023, Pixar Animation Studios,  version 1.0


Project Description
===================




| **Brief Description and/or Goal** | Add APIs to facilitate namespace editing in USD (e.g., renames, reparenting, etc.) |
| **Team(s)/Developer(s)** | 
  |
| **Designer(s)** | *-* |
| **Project Epic** | 
Pixar JIRAissuekey,summary,issuetype,created,updated,duedate,assignee,reporter,priority,status,resolutionkey,summary,type,created,updated,due,assignee,reporter,priority,status,resolution5e843848-c397-323d-a8ef-e692b4e85ddaUSD-5295 |
| **Proposal Task** | 
Pixar JIRAissuekey,summary,issuetype,created,updated,duedate,assignee,reporter,priority,status,resolutionkey,summary,type,created,updated,due,assignee,reporter,priority,status,resolution5e843848-c397-323d-a8ef-e692b4e85ddaUSD-8204 |


Background
==========


Robust and performant namespace editing on a UsdStage is one of a few remaining marquee features missing from USD's core featureset.  It is a prerequisite for our plans to replace Csd with USD, which is why it is not a "USDI" project; but at the same time, it is also a top request from software vendors Adobe and Autodesk.  A few of the issues that seem worth considering in research and design, here:


* We *probably* need to support at least the same featureset as Csd

Proposal
========

To start, it is useful to define exactly what we mean by namespace editing. In the context of this proposal, a namespace edit is an operation that removes or changes the namespace path of a **composed object** of a **composed object** on a stage. On a UsdStage, these composed objects consist of prims and properties with a property being either an attribute or a relationship. The types of operations that are considered namespace edits are deleting, renaming, and reparenting a composed prim or property.

In Sdf we already have API for performing all these namespace operations on individual specs in a single layer. And on UsdStage and UsdPrim we also have existing functions for creating and removing prims and properties. However, this existing API is not sufficient for fully namespace editing composed objects on a UsdStage for the following reasons:

1. All of this existing API affects a single spec and layer (for UsdStage this is determined by the current edit target). Since UsdStage prims and properties can be composed from multiple specs and layers, a single namespace edit on a composed object may require edits to multiple specs and layers.
2. Some namespace operations can’t be performed correctly just by adding and removing specs on the layers that define them. In particular, deleting, renaming, or reparenting a prim or property that is introduced across a composition arc (like a reference) can’t necessarily be performed via edits to the source layer without unintended side effects to other namespace objects using an arc to the same asset. Additionally, you may not have the permission or ability to directly edit the asset that is being referenced. Alternative scene description would need to be authored to perform these edits to stage namespace.
3. It’s also frequently desirable to have paths to namespace objects – such as composition arcs, relationship targets, and attribute connections – not “break” when the targeted object is moved or renamed. This “fix up” of target paths is not something the existing API does (and nor should it automatically due to the cost), but we want our API to be able to perform this “fix up” when needed.

Thus, we propose to add a new full API specifically for performing namespace edits on composed UsdStage objects.

Namespace Editing API
---------------------

To distinguish between composed namespace editing and the single layer edit target operations that already exist on UsdPrim and UsdStage, we’re going to introduce a new class called UsdNamespaceEditor that will provide all the API for performing edits on the composed namespace of a UsdStage. A UsdNamespaceEditor object can be constructed to perform namespace edits on objects of a UsdStage.

The UsdNamespaceEditor class will provide the following editing operations that work on object paths:


* Delete[Prim/Property]AtPath(stage, path)
+ Authors/deletes **all scene description in the layer stack of the current edit target necessary** to remove the prim or property at path from the composed stage.

* Move[Prim/Property]AtPath(stage, currentPath, newPath)
+ Authors/deletes all scene description in the layer stack of the current edit target necessary to make the composed prim or property at the currentPath instead exist at newPath.

Additionally, the class will provide operations that take UsdPrim or UsdProperty objects for additional convenience. For each of the following XXXPrim functions that take a UsdPrim, there will be an equivalent XXXPropertry function that takes a UsdProperty

* DeletePrim(usdPrim)
+ Authors/deletes all scene description in the layer stack of the current edit target necessary to remove the usdPrim from its composed stage.

* RenamePrim(usdPrim, newName)
+ Authors all scene description in the layer stack of the current edit target necessary to change the name of the composed usdPrim to newName. The prim will retain its original parent prim.

* ReparentPrim(usdPrim, newPrimParent)
+ Authors all scene description in the layer stack of the current edit target necessary to move the composed usdPrim from its original path to instead be a child of the composed prim, newPrimParent.

* ReparentPrim(usdPrim, newPrimParent, newName)
+ Overload of ReparentPrim that also renames the composed prim to newName when moving it be a child of newParentPrim.

For each of the above functions on both paths and UsdObjects, we will provide a corresponding Can[Operation] function (e.g. CanDeletePrimAtPath, CanMovePrim, CanRenameProperty) that returns whether the operation can be successfully performed with the current edit settings (see Authoring Settings below).

#### Batch Editing

Similar to how we have SdfBatchNamespaceEdit to describe a series of one or more Sdf namespace edits that we can then possibly apply more efficiently than we would be able to if applied one at a time, we will provide a USD namespace editing equivalent structure, such as UsdBatchNamespaceEdit. This batch edit structure will allow all of the same edit operations provided by UsdNamespaceEditor to be added in sequence as edits to the batch. The UsdNamespaceEditor class will have the functions ApplyEdits(batchNamespaceEdit) and CanApplyEdits(batchNamespaceEdit) that will perform (and determine if can be performed) the effect of the sequence of edits in the batch. Like with SdfBatchNamespaceEdit, the edits will be processed before they are applied to determine the most efficient way to perform the series of edits.

Another option for batch editing would be to implement a BatchEditingBlock RAII structure that, when opened, would cause all edits performed via UsdNamespaceEditor to be queued up until the block is closed/deleted at which point the edits would be processed and performed. This has the advantage that we wouldn’t need an entire structure that parallels the same API as UsdNamespaceEditor just for batch editing. There's a potential downside in that we would have to process the effects of the queued edits to answer any of the “can perform edit” queries made during an open batch, but this may end up not being a big enough issue to avoid going this route. Another potential issue would result if the user wanted to change the authoring settings or edit target in the middle of an open batch. We could work around this by disallowing the changing of authoring settings or edit targets when a batch is open or by just using the state of the settings when the batch is closed.

In the end the RAII structure will likely be preferred, but which of these methods we use for batch editing can be decided during implementation.

Editing Across Composition Arcs - Relocates and Deactivation
------------------------------------------------------------

As mentioned above, when namespace hierarchy is introduced by a composition arc, we can’t necessarily perform namespace operations like rename, reparent, or delete on these objects via standard spec edits alone in the targeted layer stack. For these operations, our namespace editing operations will need to provide alternative ways to encode the edit in scene description.

This is best demonstrated with an example:  
Say we have a UsdStage where the root layer defines two prims A and B that both reference the same asset

*root.usda*
```
def “A” (
 references = @model.usda@</Model>
) {
}

def “B” (
 references = @model.usda@</Model>
) {
}
```
*model.usda*
```
def Scope “Model” 
{
 def Sphere “Child” 
 {
 }
}
```

Via the reference the prim /A on the stage will have a child prim /A/Child and prim /B will have the child /B/Child. Now say we want to delete /A/Child. We can’t perform this delete in the root layer (root.usda) as the spec for “Child” is defined in the referenced model.usda. We could technically delete Child across the reference in model.usda by deleting the spec for /Model/Child. But this has two big issues: 1) it’s common to have references to assets that we cannot edit so it may not be possible to perform the deletion of the spec (or specs) in the referenced asset itself, and 2) deleting /Model/Child in the asset would delete it for ALL prims that reference /Model which may not be the desired outcome of the operation (e.g. /B/Child would be deleted as well and that is not what we want in this example).

For this case, we will provide the option (through Authoring Settings) to perform this delete operation as a “soft delete” or in other words a deactivation of the prim in the root layer stack. So in this case DeletePrim would produce the following which effectively removes /A/Child from the composed scene while leaving the model asset and /B/Child alone:

*root.usda*
```
def “A” (
 references = @model.usda@</Model>
) {
 over “Child” (
 active = false
 ) {
 }
}
``` 

Now say instead of deleting /A/Child, we want to rename it to be /A/Ball on our stage. Here we run into the exact issues as mentioned in the delete case where we can’t perform the rename in the root layer stack directly but also cannot reasonably edit the reference asset either. One possible alternative for performing this type of rename operation locally would be to deactivate /A/Child locally and add a new child /A/Ball that references /Model/Child which would give us the following:

*root.usda*
```
def “A” (
 references = @model.usda@</Model>
) {
 over “Child” (
 active = false
 ) {
 }

 def “Ball” (
 references = @model.usda@</Model/Child>
 ) {
 }
}
```

This is parallel to what we want to do in the delete case, but is more complicated since we have to add a new prim that is equivalent to the original child prim but with the new name. This can become unwieldy as more direct composition arcs are added and also makes it hard to maintain the synchronization between /A and /A/Ball if edits are made to /A’s reference.

The solution we use for these kinds of edits in Presto is relocates. Relocates are another composition arc that maps a prim path in namespace to a new path location. The above example performed with relocates (as implemented in Presto) would be as such:

*root.usda*
```
def “A” (
 references = @model.usda@</Model>
 relocates = { 
 <Child>: <Ball> 
 }
) {
}
```

This has the advantage of being more robust in the presence of multiple composition arcs and more resilient to edits of these arcs. It’s also more clear as far as intention. And additionally relocates are already supported in Pcp (but not for USD mode caches). However, supporting relocates has a non-trivial cost even when no relocates are present anywhere in the composed stage and we do not want to pay the cost for this feature when it is not used. The good news is that a lot of work has already been done internally to reduce/remove the cost of supporting relocates when no relocates are present. As part of this feature, we plan to revive the existing work that has been completed for supporting relocates and finish landing relocates support in USD.

It’s worth noting that the existing relocates only work for moving prims in namespace; they cannot be used to individually move properties in namespace. Given that there are already additional considerations/limitations to property namespace editing (like deleting or moving properties that built-in from a prim’s schema type can be undesirable), we will not be tackling “relocating” properties.

Editing Across Composition Arc - Edit Targets
---------------------------------------------

As mentioned in the description of the UsdNamespaceEditor functions, all edits via this API will be performed in the **layer stack of the current edit target** which means that the operation may author to any of the layers in the edit target’s layer stack that are necessary to move or delete the object in namespace. Typically the current edit target will be referring to the stage’s root layer stack so most namespace editing will author solely to the root layer stack of the stage. But we also allow the creation of edit targets that map across composition arcs. If a stage’s current edit target does map to another layer and path across a composition arc, then namespace edits performed through UsdNamespaceEditor will be **mapped to the edit target’s layer stack and mapped path**. In other words, the namespace edits that will be performed will be edits to the object at the mapped path in the edit target’s layer stack that will produce the desired namespace edit in the composed stage.  

For instance, if we take the same example in the above section, it's possible to create a UsdEditTarget that targets the model.usda layer using the node that represents the reference to model.usda's "Model" prim in the prim index for /A. This edit target would have a map function that maps /A to /Model like the node does for the reference. Now, if we were to use the UsdNamespaceEditor API to rename /A/Child to /A/Ball on the root.usda stage but using the edit target we just created, this namespace edit would be mapped across the edit target. I.e. the paths processed by the rename operation would be mapped so that the rename will be from /Model/Child to /Model/Ball and the edits would be performed in model.usda. Or to put this yet another way, editing across this edit target would be equivalent to opening model.usda as its own UsdStage and performing the same namespace edit using the paths mapped from /A to /Model.

A few things to note here:
1. Editing across the reference using an edit target can cause additional side effect namespace changes. In the example, by performing the rename of /A/Child to /A/Ball across the model reference, thereby renaming /Model/Child to /Model/Ball in model.usda, **will cause /B/Child to be renamed to /B/Ball in the root stage**as well. This is a different outcome from when we performed the edit in the root layer stack.
2. Namespace edits across arcs may require propagating “fixup edits” to stronger layer stacks (which is explained in the next section) in order to maintain composed opinions on the edited object.
3. It’s also worth noting that as the UsdEditTarget currently only holds a layer and mapping function, we will either need to be able to determine a targeted layer stack from this information or add layer stack identification back into UsdEditTarget to be used during namespace editing.

Fixup of Namespace Targets
--------------------------

As mentioned earlier, one major consideration when handling namespace editing in USD is that we have ways in which scene description can refer to or target namespace paths of other objects. Any scene description that targets another path may become invalid if a namespace edit were to change or remove the path of the targeted object. Thus, we will provide the ability to automatically author the necessary edits to fix up paths to namespace objects that have been moved or deleted through the UsdNamespaceEditor API.

The types of paths in scene description that we will need to be able to fix up are:
* Relationship targets
* Attribute connections
* Path expressions for pattern based collections
* Composition arcs (references, payloads, inherits, specializes)
* Overs in higher composition strength layer stacks
* Layer metadata for default prim (which can be consumed by references and payloads)
* Possibly internal path reliant structures (like a stage's current edit target which may have a path map function)

The paths that need to be fixed up after an edit will commonly come from the layers that comprise the UsdStage that is being edited itself. But it's also possible that the edits are being performed on layers that are part of the composition of other open USD stages (for instance via references or sublayers) and we would want those stages to be fixed up as well in response the namespace edits. Because of this we will provide the ability to **explicitly designate the list of open stages on which to perform namespace target fixups** in the UsdNamespaceEditor API. Any stages specified in this list will be check for any paths that need to be fixed up and will have those edits authored to the appropriate layers as well. 

The fixup behaviors we implement in USD will be modeled off of what fixups we already do in Csd. These behaviors are best explained via examples. Here we’ll define three layers root.usda, b\_ref.usda, and c\_ref.usda. root.usda defines a prim “A” which references a prim “B” in b\_ref.usda which in turn references a prim “C” in c\_ref.usda. In each layer we define connections, relationships, overs, and references to a prim that we’ll rename.

*root.usda*
```
def Scope "A" (
 references = @./b\_ref.usda@</B>
) {
 def Scope "A\_Child" {
 custom double a\_attr
 }

 custom double a\_attr\_connections
 prepend double a\_attr\_connections.connect = [
 </A/A\_Child.a\_attr>,
 </A/B\_Child.b\_attr>,
 </A/C\_Child\_ToRename.c\_attr> ]

 custom rel a\_rel\_targets
 prepend rel a\_rel\_targets = [
 </A/C\_Child\_ToRename>,
 </A/B\_Child>,
 </A/A\_Child> ]

 def Scope "A\_Child\_References" (
 references = [
 </A/C\_Child\_ToRename>,
 </A/B\_Child>,
 </A/A\_Child> ]
 ) {}

 over "B\_Child" {}

 over "C\_Child\_ToRename" {}
}
```
*b\_ref.usda*
```
def Scope "B" (
 references = @./c\_ref.usda@</C>
) {
 def Scope "B\_Child" {
 custom double b\_attr
 }

 custom double b\_attr\_connections
 prepend double b\_attr\_connections.connect = [
 </B/B\_Child.b\_attr>,
 </B/C\_Child\_ToRename.c\_attr> ]

 custom rel b\_rel\_targets
 prepend rel b\_rel\_targets = [
 </B/C\_Child\_ToRename>,
 </B/B\_Child> ]

 def Scope "B\_Child\_References" (
 references = [
 </B/C\_Child\_ToRename>,
 </B/B\_Child> ]
 ) {}

 over "C\_Child\_ToRename" {}
}
```
*c\_ref.usda*
```
(
 defaultPrim = “C”
)

def Scope "C" {
 def Scope "C\_Child\_ToRename" {
 custom double c\_attr = 1
 }

 custom double c\_attr\_connections
 prepend double c\_attr\_connections.connect = [
 </C/C\_Child\_ToRename.c\_attr> ]

 custom rel c\_rel\_targets
 prepend rel c\_rel\_targets = [
 </C/C\_Child\_ToRename> ]

 def Scope "C\_Child\_References" (
 references = </C/C\_Child\_ToRename>
 ) {}
}
```

For all the following examples, assume we have a UsdStage open for each of the above layers where that layer is the root. We'll call these StageA (root.usda), StageB (b\_ref.usda), and StageC (c\_ref.usda).

#### Example 1:

Say we want to rename the prim “/C” to “/XXXX” on StageC. When we call RenamePrimAtPath(StageC, “/C”, “/XXXX”), we will be able to fix up all the paths in c\_ref.usda that refer to /C.

*c\_ref.usda*
```
(
 defaultPrim = “XXXX”
)

def Scope "XXXX" {
 def Scope "C\_Child\_ToRename" {
 custom double c\_attr = 1
 }
 
 custom double c\_attr\_connections
 prepend double c\_attr\_connections.connect = [
 </XXXX/C\_Child\_ToRename.c\_attr> ]

 custom rel c\_rel\_targets
 prepend rel c\_rel\_targets = [
 </XXXX/C\_Child\_ToRename> ]

 def Scope "C\_Child\_References" (
 references = </XXXX/C\_Child\_ToRename>
 ) {}
}
```

But additionally since StageB is open and b\_ref.usda has a prim “B” that references “/C” in c\_ref.usda, we want to also fixup the reference in b\_ref.usda to refer to the renamed path so that the composed prim /B remains the same after the edit.

*b\_ref.usda*
```
def Scope "B" (
 references = @./c\_ref.usda@</XXXX>
) {
…
}
```

This is the only fixup necessary since the new path /XXXX is mapped across the reference in the same way as the path /C was before. It’s worth noting that if the prim B’s reference had instead been written to use the default prim instead of the explicit path to /C (a la `references = @./c\_ref.usda@`) there would be no fixups necessary in b\_ref.usda at all as the defaultPrim metadata in c\_ref.usda was fixed up to use the new prim name "XXXX".  

Another thing to note is that the edit in this example can only be accomplished via a performing the edit on StageC as there’s no way to create a single edit target for StageB or StageA that can map both the old and new paths to /C and /XXXX respectively in the target layer c\_ref.usda.

#### Example 2:

Say instead we want to rename “/C/C\_Child\_ToRename” to “/C/Renamed\_XXXX” on StageC. 

First, it’s worth pointing out that, unlike the previous example, this exact namespace edit can be accomplished using any of StageA, StageB, and StageC as long as the edit target maps to c\_ref.usda with the correct map function. For example, on StageC you can perform the operation RenamePrimAtPath(StageC, “/C/C\_Child\_ToRename”, “/C/Renamed\_XXXX”) with the default edit target for the stage. On StageA, you could instead perform the operation RenamePrimAtPath(StageA, “/A/C\_Child\_ToRename”, “/A/Renamed\_XXXX”) with an edit target that is set to the layer c\_ref.usda with the map function that maps /A -> /C. These will both perform the same edit operations including the same path fixups (as dictated by the authoring settings).

So, say we chose to use RenamePrimAtPath(StageC, “/C/C\_Child\_ToRename”, “/C/Renamed\_XXXX”) on StageC. We will be able to fix up all the paths that refer to “/C/C\_Child\_ToRename” in c\_ref.usda to use the new path.

*c\_ref.usda*
```
def Scope "C" {
 def Scope "Renamed\_XXXX" {
 custom double c\_attr = 1
 }

 custom double c\_attr\_connections
 prepend double c\_attr\_connections.connect = </C/Renamed\_XXXX.c\_attr>

 custom rel c\_rel\_targets
 prepend rel c\_rel\_targets = [
 </C/Renamed\_XXXX> ]

 def Scope "C\_Child\_References" (
 references = </C/Renamed\_XXXX>
 ) {}
}
```

But additionally since StageB is open and b\_ref.usda has a prim “B” that references c\_ref.usda’s “C”, our rename causes the composed /B/C\_Child\_ToRename to instead now be /B/Renamed\_XXXX in any stage or reference arc that uses b\_ref.usda. We typically don’t want any paths in b\_ref.usda that target /B/C\_Child\_ToRename to fall off, so here we’ll also fix up all the paths that refer to /B/C\_Child\_ToRename to use the new mapped path as well.

*b\_ref.usda*
```
def Scope "B" (
 references = @./c\_ref.usda@</C>
) {
 def Scope "B\_Child" {
 custom double b\_attr
 }

 custom double b\_attr\_connections
 prepend double b\_attr\_connections.connect = [
 </B/B\_Child.b\_attr>,
 </B/Renamed\_XXXX.c\_attr> ]

 custom rel b\_rel\_targets
 prepend rel b\_rel\_targets = [
 </B/Renamed\_XXXX>,
 </B/B\_Child> ]

 def Scope "B\_Child\_References" (
 references = [
 </B/Renamed\_XXXX>,
 </B/B\_Child> ]
 ) {}

 over "Renamed\_XXXX" {}
}
```

But we’re not done; since StageA is open and root.usda has a prim “A” that references b\_ref.usda’s “B”, our rename causes the composed /A/C\_Child\_ToRename to instead now be /A/Renamed\_XXXX (because of the direct reference chain /A -> /B -> /C) in any stage or reference arc that uses root.usda. We also don’t want any paths in root.usda that target /A/C\_Child\_ToRename to fall off, so here we’ll also fix up all these paths as well.

*root.usda*
```
def Scope "A" (
 references = @./b\_ref.usda@</B>
) {
 def Scope "A\_Child" {
 custom double a\_attr
 }

 custom double a\_attr\_connections
 prepend double a\_attr\_connections.connect = [
 </A/A\_Child.a\_attr>,
 </A/B\_Child.b\_attr>,
 </A/Renamed\_XXXX.c\_attr> ]

 custom rel a\_rel\_targets
 prepend rel a\_rel\_targets = [
 </A/Renamed\_XXXX>,
 </A/B\_Child>,
 </A/A\_Child> ]

 def Scope "A\_Child\_References" (
 references = [
 </A/Renamed\_XXXX>,
 </A/B\_Child>,
 </A/A\_Child> ]
 ) {}

 over "B\_Child" {}

 over "Renamed\_XXXX" {}
}
```

#### Example 3

Now instead take the previous example and instead of doing the rename of C\_Child\_ToRename on StageC where the prim is introduced, we instead perform a rename of “/B/C\_Child\_ToRename” to “/B/Renamed\_XXXX” directly on StageB with the intention of only renaming it in the referencing prim. Since /B/C\_Child\_ToRename is introduced across the reference to /C on c\_ref.usda we can’t edit the specs directly and will need to introduce a relocates on /B to perform the rename. And since this produces the same effective rename in StageB that was achieved in the previous example, the same fixups will be performed in b\_ref.usda for this edit.  

*b\_ref.usda*
```
def Scope "B" (
 references = @./c\_ref.usda@</C>
 relocates = {
 <C\_Child\_ToRename>: <Renamed\_XXXX>
 }
) {
 def Scope "B\_Child" {
 custom double b\_attr
 }

 custom double b\_attr\_connections
 prepend double b\_attr\_connections.connect = [
 </B/B\_Child.b\_attr>,
 </B/Renamed\_XXXX.c\_attr> ]

 custom rel b\_rel\_targets
 prepend rel b\_rel\_targets = [
 </B/Renamed\_XXXX>,
 </B/B\_Child\_ToRename> ]

 def Scope "B\_Child\_References" (
 references = [
 </B/Renamed\_XXXX>,
 </B/B\_Child> ]
 ) {}

 over "Renamed\_XXXX" {}
}
```

And just like the previous example, our rename causes the composed /A/C\_Child\_ToRename to instead now be /A/Renamed\_XXXX in StageA so we’ll do the exact same fixups to root.usda as in the previous example. But still, to reiterate, we don’t make any changes across the reference to c\_ref.usda.

There are obviously tons of other examples that could demonstrate more complicated composition structures and how we would propagate namespace fixups, but this should give gist of what to expect. There are also some open questions about the limitations of which paths we’ll be able to fix up that are worth calling out directly here. The main one is what we can do about paths that are defined inside of variants that are not currently the active selected variant. It’s reasonable to expect that all paths in all variants should be fixed up when a namespace edit would necessitate it. However, this can be extremely complex and expensive, especially in cases of nested variants. We expect that we will not tackle this as part of this proposal but is something we may have to consider as follow-up work.

Authoring Settings
------------------

Authoring settings will be organized as its own class (a la UsdNamespaceAuthoringSettings) that provides all the options we want to obey during namespace editing. The UsdNamespaceEditor class will own a single authoring settings that then applies to all edits performed with that class instance; these authoring settings will of course be editable. It's possible that in the future we may want to provide a way of configuring a set of “default authoring settings” that will be used as the default settings for new UsdNamespaceEditor instances when they’re created, but we will not tackle that within the scope of this project.

The exact list of options we will provide in the authoring settings is not complete and is intended to expand and evolve as we see what the emerging needs are. But here are the types of settings we expect that we could implement right now:

* Allow authoring active = false for Delete operations that can’t be performed through deleting specs? (This option being off would reject namespace edits that cannot be through deleting specs in the targeted layer stack.)
* Allow authoring of relocates for Move operations that would require it? (This option being off would reject namespace edits that cannot be performed without authoring relocates on the targeted layer stack.)
* Allow deletion of target paths to removed prims during fixup when performing a namespace delete? (This option being off would allow dangling path targets to an object to remain after that object is deleted from namespace)

There are also some potential future options that can be added but we will not implement right now:
* More fine tuned control of what path fixups to do, like attribute connections, relationship targets, composition arcs fixups being individual options.
* Whether to fixup incoming target paths from inactive/masked prims (i.e. prims that aren’t composed on the current stage even though they do have scene description)?

UsdObject Identities
--------------------

We currently have classes in USD that act as handles to composed prims and properties on the UsdStage, namely UsdPrim, UsdProperty, UsdAttribute, and UsdRelationship. These classes are all derived from the base class UsdObject and will remain valid for as long as the underlying Usd\_PrimData that they hold a pointer to is valid. Many namespace operations, such as reparenting, renaming, or deleting a prim, will cause the Usd\_PrimData for the original prim path to become invalid and “marked as dead”, thus invalidating any still existing UsdObjects that referred to that prim. These invalid objects will never become valid again even if an operation like the equivalent of an undo is performed to have a prim at original path come into existence again.

For many namespace editing workflows we expect it will be desirable for UsdObjects to persist across namespace edits. This can be particularly useful for GUI workflows that may want to maintain state across undo/redo operations or just want a handle that continues to refer to a renamed or reparented object. For these situations we want to provide the ability for UsdObjects to maintain and update an identity that can: 1) be transferred across rename or reparent (e.g. an existing UsdPrim(</A>) automatically becomes UsdPrim(</B>) if /A is renamed to /B) and 2) be “revived” if the composed object is deleted and at some point later is created again at the same path (e.g. UsdPrim(</A>) becomes invalid when /A is deleted, but if a prim at /A is added again, UsdPrim(</A>) automatically becomes valid again, referring to the new prim).

The maintaining of object identities doesn’t come for free so we do not want to pay the cost for it in the majority of workflows which do not expect to perform namespace edits or do not care about UsdObject identities even in the presence of edits. Therefore we propose that the existing UsdObjects will not maintain their identities themselves; they will remain unchanged. Instead we will introduce a new UsdObjectHandle (plus the equivalent UsdPrimHandle, UsdPropertyHandle, etc.) that will hold a UsdObject and a persistent shared “identity” for the object. The handle will behave as a pointer to the underlying UsdObject and will update the underlying object when needed to refer to the composed object that is now represented by the handle’s identity. UsdObjectHandles will be able to be explicitly constructed from UsdObjects essentially creating identities “on demand”. If need be, we could additionally provide API on UsdStage for getting UsdObjectHandles (parallel to the ones that just return UsdObjects) but for now we expect the explicit construction of the handles to be sufficient.

So for example, if a UsdStage has two prims </A> and its child </A/Child> and you were to get:```  
  UsdPrim aPrim = stage.GetPrimAtPath(“/A”)
  UsdPrimHandle childHandle = stageGetPrimHandleAtPath(“/A/Child”)
```

Both aPrim and childHandle would start valid. If you use the namespace editing API to rename /A to /B, then aPrim will no longer be valid since UsdPrim doesn’t track identity. But childHandle will now hold the prim object that refers to /B/Child as UsdPrimHandle will have its shared identity updated. The same would be true if we had instead deleted /A and then performed some sort of “undo” that recreated /A and /A/Child again. aPrim would still be invalid even though a prim at /A exists again, but childHandle would become valid again and hold a UsdPrim representing the recreated /A/Child.

Risks, Issues and Caveats
=========================

* This namespace editing is an important component of adding an undo/redo system, but we will not be tackling undo/redo here.
* There has been some debate as to whether copy/duplicate for composed prims and properties should be considered a “namespace editing” operation or if it’s truly its own thing entirely. Therefore, we will not be touching copy/duplicate as part of this namespace editing feature.
* Rename and reparent operations will only be treated as such when performed through the official UsdNamespaceEditor API, i.e. we will not try to figure out if from generic Sdf change notification if some set of layer changes could be a rename or reparent.
* Should we implement a different indication of "soft-delete" to distinguish it from "active = false"? Something that is maybe the equivalent of relocating a path to nothing. I don't know if it will be useful to distinguish between "delete" and "deactivate" which  is why this is mentioned here instead of in the Deactivate section.
* There are some instances of string valued metadata (besides defaultPrim) that are used to represent namespace paths. An example is “renderSettingsPrimPath” which is stage level metadata that is defined as meaningful in usdRender. While a path like this is something that a user could conceivably expect to be fixed up if the prim it references is reparented or renamed, this would open up a whole can of worms with looking for string values that could possibly represent paths. Thus, we will not be attempting to fix up paths that come from string valued data.
