# **Solid Models in USD Proposal**


# **1. Purpose and scope**

The industrial metaverse is here and with it comes requirements for digital content that are not met by the current USD standard.  
Surface models and meshes are not sufficient to describe the solid models common to CAD/CAM/CAE, so we propose the adoption of a solid model boundary representation (Brep) schema to USD.  
The proposed schema is an implementation of the Radial Edge Data Model, as first published by Kevin Weiler in 1986.  
In the last 35+ years, this model has proven itself to be flexible and robust, supporting myriad industries via commercial geometry kernels.  
Kevin Weiler’s thesis is available here:    [https://www.scorec.rpi.edu/REPORTS/1986-1.pdf](https://www.scorec.rpi.edu/REPORTS/1986-1.pdf)

With this proposal, we aim to add a Brep model to USD. In support of this model we propose to also add many new curve, surface, and volume geometry types. 
The set of shapes was derived from the Product Representation Compact (PRC) format, a well known ISO standard used in, e.g, 3d models in PDFs.

Section 2.1 contains a catalog of curve and surface primitives that we propose _UsdSolid_ supports to match the capabilities of PRC.  
The current document does not yet include detailed designs of all geometry types, but we intend to add them soon. 

# **2. Overall design concerns**

Solid models rigorously partition space into regions by connecting sets of surfaces into region boundaries.  
Regions are the set of points that can be connected by curves of any shape that don't cross boundaries.  
The boundaries between regions must be watertight to prevent the points of each region from being connectable to one another.  
Manifold solid objects partition space into one solid and one or more void regions, classifying every point in space as either inside or outside the solid.
A solid is manifold if for all points on the boundary there exists a neighborhood that is homeomorphic to a two-dimensional disk.
A Brep that isn't manifold is called "non-manifold."
Non-manifold objects can partition space from one to any number of regions, where every point in space classifies to one of the model's regions. 

In the world of geometric modeling, where mathematical approximations of shape are rife, gaps between adjacent surfaces are common. 
In the Radial Edge Data Model, the connections of adjacent surfaces are explicit objects that can fill the gaps and create the necessary partition of space.

Several Brep models were considered as options to serve as the base of the _UsdSolid_ schema. 
The radial edge data model was chosen because in addition to standard manifold modeling, it offers a robust representation of non-manifold modeling.
In fact, Weiler's model was the first complete non-manifold Brep to explicitly represent topological adjacencies (Lee, 1999).
The topology models in PRC, STEP, Parasolid, et al map into the proposed radial edge data model. 
Concepts from both PRC and STEP are used in this proposal, including all of the Brep geometry types in PRC and the volumes concept from STEP. 
As in PRC and STEP, this design supports wire frame models.

The proposed model is composed of 3 parts: shapes, topology objects, and special connectivity objects called "uses."
Because limiting _UsdPrim_ count is a good practice in general and a must in large scale scenes, the _UsdSolid_ design utilizes a _UsdSolidBrepAPI_ multiple-apply schema that can be applied to a _UsdSolidBrepArray_ IsA schema. 
Each instance of the _UsdSolidBrepAPI_ contains all the shape, topology, and connectivity data of a single Brep, plus metadata such as material bindings and a local transform.

## **2.1 Shape**

In practice, Breps are a large class of shape functions built on parametric mappings. 
Today, this includes NURBs curves and surfaces, analytics, and is extendable to helices, offsets and more. 
USD currently supports the standard NURBS curves, _UsdGeomNurbsCurves_, and NURBS surfaces, _UsdGeomNurbsPatch_. 
Further, USD has analytic surfaces _UsdGeomCone, UsdGeomCylinder, UsdGeomPlane, UsdGeomSphere_.

The existing USD surface primitives have some issues relative to their use with Breps. 
First, the NURBS curves and surfaces do not support double precision control vertices.
This is necessary for USD to be accepted as a reference CAD format, so the proposed schema includes double precision geometry. 
Second, the _UsdGeomCylinder_ surface includes its end caps. 
Also the _UsdGeomCone_ surface often includes an end cap in practice, but does not address caps in the documentation.
For full flexibility, solid models require that the analytics do not include end caps.
Third, the parameterization of the sphere, cone, cylinder, plane and volume are currently unspecified.
In order to trim them properly for solid modeling the analytics will need parameterizations and double precision.
Last, the CAD community uses a larger set of analytic surfaces that currently present in USD.

In this proposal each geometry type is defined by a set of attributes that reside within the _UsdSolidBrepAPI_ schema.
The geometry is packed within like types, as in the _UsdGeomNurbsCurves_ class.
Where necessary, the geometry will have double precision attributes, e.g., NURBS curves have double precision control vertices, weights, and knots.
Analytic geometry data will include both the analytic definition and the parameterization, e.g., a sphere will have a radius and also a frame of reference that defines the parameterized surface origin, orientation, beginning, and end.
We recommend using the PRC parameterizations for analytic geometries.
Trimming curves are also a part of the _UsdSolidBrepAPI_ schema, packed as the 3D curves are.

For a complete set of geometry, we recommend meeting the PRC standard, certified by the International Organization for Standardization (ISO 14739-1:2014). 
To achieve this will require an extensive list of attributes for the _UsdSolidBrepAPI_.
To match the PRC specification it will be necessary to add the following curves and surfaces. 
We also suggest adding _Volume_, _CurveInVolume_, and _SurfInVolume_ types for anticipated future uses.
New geometry will be added to the _UsdSolidBrepAPI_ schema.


<table>
  <tr>
   <td><strong>Curves</strong>
   </td>
   <td><strong>Surfaces</strong>
   </td>
   <td><strong>Volumes</strong>
   </td>
  </tr>
  <tr>
   <td>Blend02Boundary
   </td>
   <td>Blend01
   </td>
   <td>Volume
   </td>
  </tr>
  <tr>
   <td>Circle
   </td>
   <td>Blend02
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Composite
   </td>
   <td>Blend03
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>OnSurf
   </td>
   <td>Cylindrical
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Ellipse
   </td>
   <td>Offset
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Equation
   </td>
   <td>Ruled
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Helix01
   </td>
   <td>Revolution
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Hyperbola
   </td>
   <td>Extrusion
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Intersection
   </td>
   <td>FromCurves
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Line
   </td>
   <td>Torus
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Offset
   </td>
   <td>Transform
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Parabola
   </td>
   <td>SurfInVolume
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>PolyLine
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Transform
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>ProjectedCurve
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>CurveInVolume
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
</table>



## **2.2 Topology and "use"**


When a closed set of curves lay on a surface, it can be used to trim the surface to that set of boundary curves and this results in a trimmed surface. 
If two surfaces share the same segment of a boundary, this is called an edge and the two surfaces are neighbors. 
If one has a way to keep track of which surfaces share an edge, then they have added a topology to our modeling system.


A trimmed surface, together with the information about its neighbors is referred to as a face. 
A face must have an outer boundary and it may have many inner boundaries or “holes.” 
A shell is a collection of connected faces.


If a shell is closed then you have a solid. 
A solid has an outer closed shell and possibly many inner shells that define cavities in the solid. 
A “region” encloses space from a closed outer shell or between two closed shells (one inside the other) and has volume. 
The outer region is the infinite region, so a closed box is represented by two regions – the outer infinite region, and the region within the box. 
If there is a box within the box ( a ‘thick’ box) then there are 3 regions. 
The inner box may ‘float in space’ without being attached to the outer box; it may not be physically possible, but it is topologically acceptable.


In a closed solid each boundary edge is shared by two neighboring faces (or connected to one face twice, called a seam edge), so this is referred to as a boundary representation or “Brep”. 
The first implementations of a Brep model were manifold, that is they allowed for only two faces to share an edge, hence the name “twin-edge boundary representation” or Brep. 
If more than two faces can share an Edge, the topology is non-manifold.


It turns out that the manifold restriction that an edge may have only two neighbors is very limiting. 
Any time you intersect two surfaces, if you look in the neighborhood of a point on the intersection curve, there appear to be four neighboring surfaces at that point. 
That’s what is meant by being “non-manifold”. 
A manifold edge is restricted to having two neighboring surfaces and a non-manifold edge may have more than two surfaces that share that edge.


Each boundary of a face consists of a closed loop of edges. 
In the topology structure each loop has a list of edges, and the same edge may be used by two or more faces and that’s what “EdgeUse” refers to. 
The term edgeuse has real importance since there could be many uses of an edge.


If one constructs a box (it defines a region) and then adds another box right next to it, then they have another region. 
Since they share the same face, you can see why “FaceUses” are necessary. 
The face is used on one region, and the face is also used in the other region.


## **2.3 Brep**

The key idea of Brep modeling is that simple trimmed-shapes connect together through their boundaries to form complex geometry models just as a set of small glass pieces welded together along their edges form a stain glass window.


Shapes are points, curves, and surfaces each of which is a simply connected point set within a 3D space. 
Shapes can be infinite (planes, cylinders, lines and such) or finite (Bspline curves and surfaces) but have no sense of boundaries. 
For every shape there is a simple topology object that adds trimming to the shape so that it can be connected into a Brep model. 
The simple topology objects are vertices, edges, faces, and regions. 
Important combinations of simple topology objects forming key boundaries within a geometry model are also represented explicitly; a loop is any closed sequence of connected edges used to bound a face and a shell is any set of faces connected edge-to-edge to bound a region.


A topology object is “used” each time it connects to the geometry model to form a boundary. 
In general, all of the simple topology objects participate in a hierarchy of boundaries: regions are bounded by faces (gathered into connected shells), faces are bounded by edges (gathered into connected loops), and edges are bounded by vertices.


Boundaries are used to establish neighbor relations. 
Topology objects don’t connect directly to their neighbors; rather neighbor relationships are created when two topology objects both use a common boundary.


A geometry model represented as a hierarchy of boundary connections is referred to as a boundary representation or “Brep” model.


Each use of a topology object (that can be used more than one time in one model) is represented by a specialized use object. 
Each use of a face to bound a region is represented by a Faceuse. 
Each use of a loop to bound a face is represented by a Loopuse. 
Each use of an edge to bound a face is represented by an Edgeuse, and each use of a vertex to bound an edge is represented by a Vertexuse. 
There are no Shelluse objects because shells are used just once per model to bound one region and the shell object can act as its own Shelluse object.


A connection between an object and a boundary is represented as a connection between their use objects.


The following diagram shows the Brep object model.

![alt_text](images/image0.png "Brep Object Model")



## **2.4 USD Implementation**

To make the USD implementation as lightweight as possible, yet fully featured, we propose using a single concrete IsA schema as an array of Breps and single apply APIs to add geometry to the array.
The _UsdSolidBrepArray_ is a flattened format that describes all the necessary connectivity to build the Brep directed graph, with topology and "use" objects; and standardizes the application of select metadata.
Each geometry type, e.g. _NURBS_ curves or surfaces, are singly apply API schemas. 
Since each type of geometry is optional (a given Brep may have only _NURBS_ and no analytics), this will minimize the number of default valued attributes.

In solid modeling a Brep is not a monolithic object; each object within the Brep has its own instance and may have unique properties.
For example, material properties may be assigned to Faces, ID tags for any or all objects, etc.
A minimal set of metadata for the components within a Brep are included in the schema.

Any Brep model must be modified to optimize its performance in OpenUSD.
The set of modifications neccessary are
1. Flattened representation
    1. The schema must represent all topology with arrays of indices
    1. Entities smaller than a Brep (Face, Edge, etc.) don't exist as `Prims`
1. Geometries are applied schemas
1. Design that allows compacted Breps (multiple Breps in one `Prim`)

This set of modifications could be applied to other Brep models.
The Radial Edge Data Model was chosen because of it's neutral position in the CAD industry and its natural representation of general bodies as well as the usual manifold bodies, wire frames, etc.

### **2.4.1 _UsdSolidBrepArray_**

The _UsdSolidBrepArray_ derives from _UsdGeomGprim_ with attributes to define the Brep topology, "uses", and count of each per Brep.
_UsdSolidBrepArray_ derives from _UsdGeomGprim_ so that it can have the properties _Extent_ and _Visibility_, and have _XformOps_ applied.
It follows the rules of all geometric primitives, such as no nested _Gprims_.

The flat format of Brep connectivity is a concise representation of the Brep that creates only a small perturbation of the USD format, a single schema to represent an entire Brep model.
With this model, creating one or more Breps in USD requires one _BrepArray_ to define the connectivity and metadata, with curves and surfaces applied.
In some usecases we expect that a collections of Breps will have one Brep per _BrepArray_.

### **2.4.2 Instancing of Brep Models**

In this proposal, whole _UsdSolidBrepArray_ can be referenced to create multiple instances of a set of Breps.

### **2.4.3 Brep Geometry in USD**

There are 4 types of geometry stored along with the _UsdSolidBrepArray_.
The simplest is the vertex location, which is stored as a point3d.
An edge needs a curve and a face needs a surface to have shape, so curves and surfaces are applied APIs, where owning Edges and Faces indicate which geometry gives them shape.
UVTrimCurves are the fourth geometry object, also an applied API. 
They are the projection of the edge curves onto the face surfaces.

### **2.4.4 Geometry type extensions**

Not yet included at this stage of the proposal is the _USD_ implementation of the new geometry types.
The definitions of the PRC geometry types listed above can be found in the[ PRC specification.](https://docs.techsoft3d.com/exchange/latest/SC2N570-PRC-WD.pdf)
Having reviewed the definitions, we see no issues with the potential implementation.
Care will be taken to ensure proper architecture.
Each geometry type definition will be another applied API.
The attributes will be compact definitions of the parameterized shape, allowing multiple geometries of one type to be defined within the finite set of attributes.

### **2.4.5 Modeling Breps on a UsdStage**

Efficient modeling or editing a Brep directly on a UsdStage is not a feature of the current schema, but there are clear steps to take to support this.
Creating schemas for the 11 topology and use objects in the Brep model will allow the entire directed graph structure of the Brep to be represented in USD, which will be well-suited for live editing.

### **2.4.6 Trimming Curves** 

Optional trim curves can be included similarly to curve and surface geometry.
The edgeuse defines the connection between a given edge and face; the edgeuse stores an index for the associated trimming curve applied API.
Trim curves are optional in this Brep model because the edge curve defines the model truth, but trim curves are useful for, e.g., speeding up tessellation algorithms.  


## **2.5 Flexible design possiblities**

The _UsdSolidBrepArray_ enables many possible design paradigms. 
We enumarate some of the choices here.

### **2.5.1 One Brep per BrepArray**

The first design we present draws an equivalency between a Brep and a _UsdPrim_.
Standard _USD_ hierarchies can be built to represent a CAD model.

This design is well suited to building a _USD_ representation of a CAD model similar to how it would be structured in the native design software.
A _USD_ model in this style of a large assembly containing a vast number of constraints would be challenging to simulate.
A single model can have multiple assembly representations depending on the designers use case.
An animator creating marketing material will rig a model differently than an engineer writing manufacturing documentation.
When constraints are applied throughout this model, the hierarchy is not as useful.

### **2.5.2 One Assembly per BrepArray**

Next, one might consider a design where each _UsdSolidBrepArray_ contains a set of Breps forming a rigidly connected CAD assembly.
Consider a car model represented in this way, where an entire door is packed into one _UsdSolidBrepArray_. 
Adding constraints to the door hinge enables simulation or modeling of the door opening and closing.

This simplified model reduces the number of constraints that need to be simulated.

### **2.5.3 One Model per BrepArray**

Last, a user could pack an entire model into a single _UsdSolidBrepArray_ _UsdPrim_.  
This design is well suited to content delivery due to it's highly packed nature.
The single _UsdPrim_ design minizes the cost of stage traversal. 

## **2.6 Other implementations considered**

Several designs were implemented prior to the one presented.
We discuss them below.

### **2.6.1 One _UsdPrim_ per geometry object**

The first design attempted created individual prims for each brep and its curves an surfaces.
This design followed the _UsdGeom_ schema design where _UsdGeomNurbsPatch_ exists for individual surfaces.
It was also thought that being able to interact with individual curves and surfaces may be useful.

Practice found that this was an untenable design.
A surface model of a car was used to test the design.
Surfaces with geometric proximity and like materials were stitched into Breps, then imported to _USD_.
A typical model would have 500 Breps, each with 100 geometry _UsdPrim_.
Representing each model with 50,000 _UsdPrim_ is not practical, so a new design that packed geometry into the Brep was created.

### **2.6.2 One _UsdPrim_ per Brep**

The second design eliminated the surface and curve prims. 
Instead, all of the geometry information was moved into the _Usd_ Brep schema, packing geometry based on type.
This design improved performance and shrunk file size by 1/3. 

The proposed design is capable of everything the one-_UsdPrim_-per-Brep design is, but adds the capability of packing multiple Breps into a single _UsdPrim_.

### **2.6.3 Breps as an Applied API**

In this design the _BrepArray_ was a strongly typed container derived from _Gprim_.
Each Brep was added to the _BrepArray_ through an application of a multiple apply API.
This design had an advantage over the proposed design in instancing of individual Breps.
Utilizing _Connections_, a single Brep in this _BrepArray_ could be referenced in another _BrepArray_.

What this design lacked was coherence with USD's style.  
Using _Connections_ to instance a Brep could be considered an abuse.
Effective instancing required unique _XformOps_ for each Brep applied to the _BrepArray_, forcing a new means to apply _XformOps_ to subsets of a _UsdPrim_.
Further, _GeomSubset_ wasn't an option for applying material properties to Breps or Faces, so a new material binding scheme was required.


This schema was shelved because it deviated too far from _USD_ norms.


## **2.7 Assemblies**

Most non-trivial CAD models will be assemblies of parts.
However, CAD assemblies are outside the scope of this proposal as we aim to define only the base geometric and topologic representation of a Brep.


Significant care will be necessary when defining how CAD assemblies will be represeted in OpenUSD.
First, the concept of _kind_ already exists so the name _assembly_ will be overloaded.
The existing _kind_ is used for picking; applying that label to CAD assemblies would cause confusion and conflicts in the scene.
Second, it is not clear whether CAD assemblies will require a new schema or be a best-practices guide utilizing existing instancing tools.
Last, the CAD assembly structure should work with constraints imposed by external modeling tools, further enabling world simulation.


## **2.8 Tolerance**

A valid Brep will have a single tolerance number that it conforms to.  
Any two topologically connected geometric entities will have a maximum gap size less than the given tolerance. 
This includes trim curves, which must be within tolerance to both the surface and projected curve.  
Degenerate geometry is not allowed, where degeneracy is measured against tolerance.  
All unconnected topologic entities must have a minimum  gap greater than tolerance. 
The specific rules are enumerated in section 2.9.1.


## **2.9 Valididation**


Without a validation engine, there is no schema.
We record in this proposal rules that we expect authored Breps to conform to.
Given the complex nature of geometric modeling, not all of the constraints are verifiable within OpenUSD.

For the proposed model, it is straight-forward to create a topology verification tool.
One can walk the topology graph of the Brep to confirm that, e.g., every edge has a start and end vertex.
Some geometric data is verifiable as well, such as confirming that a NURBS curve has a coherent order, knot vector, weights and control vertices.

But some geometric requirements will be outside the scope of OpenUSD.
Without a complete geometric engine, testing for, e.g., self-intersecting curves is not possible.
As adoption of this schema grows, we hope to find that 3rd party geometry modeling libraries are interested in taking on the challenge of validating Usd Breps.


### **2.9.1 Rules and requirements**

Here we record the rules and requirements of a valid Usd Brep model.
These rules will be included in the schema prior to publishing.

1. Brep
    1. All self-intersections are marked with appropriate topology, including:
        1. Any face-face intersections have an edge and/or vertex
        1. Any edge-edge intersections have a vertex
1. Regions
    1. All regions are separated by closed shells
1. Shells   
    1. A shell may contain either
        1. A vertex
        1. WireEdges and vertices
        1. or Facesuses and (optional) wireEdges and vertices
1. Faceuses
    1. The "same" orientated faceuse is on the positive-normal side of the associated surface
1. Faces
    1. The face range must be a subset of the surface range 
    1. No sliver faces (a face is a sliver if it is contained in a pipe with radius = tolerance)
    1. No faces with area less than tolerance^2
    1. A face has a single outer loop (seam edges are required)
    1. The first loop listed is the outer loop.
1. Loops
    1. A loop may contain either
        1. A vertex (degenerate inner loop on a face)
        1. or one or more edgeuses
1. Edges
    1. The edge range must be a subset of the curve range
    1. No edges contained in a sphere of radius = tolerance 
    1. The orientation of the edge is the same as its curve
    1. The curve runs from the start vertex to the end vertex (possibly through either vertex)
1. Surfaces
    1. No sliver surfaces (a surface is a sliver if it is contained in a pipe with radius = tolerance)
    1. No surface with area less than tolerance^2
1. Curves
    1. No edges contained in a sphere of radius = tolerance 
    1. Curve orientation is with the parameterization
1. Trim Curves 
    1. An edge or wireedge type edgeuse must be represented with NURBS 
    1. The control points need not be constrained to lie on the surface, but the curve must
1. Range
    1. For any range _[a, b]_ it must be that _b > a_
    1. The range on periodic geometry must have length <= period



# **3 Schema**
**schema.usda**
<details>
  <summary>  Click to expand </summary>

```
#usda 1.0
(
    subLayers = [
        @usd/schema.usda@,
        @usdGeom/schema.usda@
    ]
)

over "GLOBAL" (
    customData = {
        string libraryName   = "usdSolid"
        string libraryPath   = "./"
        string libraryPrefix = "UsdSolid"
        string tokensPrefix  = "UsdSolid"
        bool skipCodeGeneration = true
    }
) {
}

class BrepArray "BrepArray" (
    inherits = </Gprim>
    doc = """ Solid boundary representation models (Breps) rigorously partition space into regions by connecting sets of surfaces into region boundaries.  Regions are the set of points that can be connected by curves of any shape that don't cross boundaries.  The boundaries between regions must be watertight to prevent the points of each region from being connectable to one another.  Manifold solid objects partition space into one solid region and one or more void regions. Non-manifold objects can partition space from one to any number of regions, where every point in space classifies to one of the model's regions.  In the world of geometric modeling, where mathematical approximations of shape are rife, gaps between adjacent surfaces are common. In this model, the connections of adjacent surfaces are explicit objects that can fill the gaps and create the necessary partition of space.

    This model is comprised of 3 parts: shapes, topology objects, and special connectivity objects called "uses." For a thorough description of this model, see the Solid Models USD Proposal.
    
    Rules and restrictions on topology and geometry are listed in the proposal. They will be migrated to this schema when the AOUSD Geometry WG is aligned on a design.
    
    For compact storage of the radial edge data model redundant elements are removed from the flattened representation.  There are no attributes for Vertexuses and Loopuses.  The lists of Edgeuses represents pairs, so the arrays size() are half the number of Edgeuses in the Brep model.

    Objects related to a single Brep must be consecutive in the BrepArray.  For example, the Edges of Brep i are the brep:edgeCount[i] consecutive Edges starting at SUM(brep:edgeCount[n]), for n in [0,i).
) {
    uniform int[]      brep:id                   ( doc = """ User applied ID. size() = Number of Breps. """ )
    uniform int[]      brep:regionCount          ( doc = """ Number of Regions in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:shellCount           ( doc = """ Number of Shells in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:faceuseCount         ( doc = """ Number of Faceuses in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:faceCount            ( doc = """ Number of Faces in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:loopCount            ( doc = """ Number of Loops in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:edgeuseCount         ( doc = """ Number of Edgeuses in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:edgeCount            ( doc = """ Number of Edges in this Brep. size() = Number of Breps """ )
    uniform int[]      brep:vertexCount          ( doc = """ Number of Vertices in this Brep. size() = Number of Breps """ )

       
    uniform int[]      region:id                 ( doc = """ User applied ID. size() = number of regions. """ )
    uniform int[]      region:shellCount         ( doc = """ Number of shells in this region - shells after the first shell are inner shells in the region. size() = number of regions. SUM(region:shellCount) = number of Shells""")
    uniform token[]    region:type               ( allowedTokens = ["solid", "void"]
                                                   doc = """ Indicates if this region is a solid or a void. size() = number of regions.""")
    
    uniform int[]      shell:id                  ( doc = """ User applied ID. size() = number of shells. """ )
    uniform token[]    shell:type                ( allowedTokens = ["faceuse", "wireEdge", "vertex"]
                                                   doc = """ A vertex type shell contains one and only one vertex. A wireEdge type shell contains Edges and Vertices. A faceuse type shell contains Faces, Edges and Vertices. size() = number of shells.""")
    uniform int2[]     shell:childCount          ( doc = """ Provides the start index and number of topology items associated with this Shell. The type of the associated topology is indicated by the `shell:type` attribute. """ )
    
    uniform int[]      faceuse:face              ( doc = """ Index of owning Face. size() = number of faceuses = 2 x number of faces""" )
    uniform token[]    faceuse:orientation       ( allowedTokens = ["same", "opposite"] 
                                                   doc = """ Orientation of the faceuse relative to the face->surface. The "same" oriented faceuse will be on the positive-normal side, and the "opposite" orientated faceuse will be on the negative-normal side of the surface.  size() = number of faceuses. """)
    
    uniform int[]      face:id                   ( doc = """ User applied ID. size() = number of faces. """ )  
    uniform int2[]     face:loopCount            ( doc = """ Provides the start index and number of loops associated with this Face. """)
    uniform token[]    face:surfaceType          ( allowedTokens = ["BrepSurfaceNurbsAPI"] )
    uniform int[]      face:surfaceIndex         ( doc = """ Provides the index of the surface associated with this Face. The type of the associated geometry is indicated by the `face:surfaceType` attribute. """ )
    uniform token[]    face:trim                 ( allowedTokens = ["none", "uvCurves", "rectangular"]
                                                   doc = """ none = No UV trim curves specified. uvCurves = UV trim curves are specified for this Edgeuses connected to this face.
                                                             rectangular = Special case of 'uvCurves', UV domain is composed of isoparameter curves. size() = number of faces.""")
    uniform double2[]  face:uRange               ( doc = """ U domain of the face on its surface. size() = number of faces. """)
    uniform double2[]  face:vRange               ( doc = """ V domain of the face on its surface. size() = number of faces. """)
    
    uniform int[]      loop:id                   ( doc = """ User applied ID. size() = number of Loops. """ )
    uniform token[]    loop:type                 ( allowedTokens = ["edgeuse", "vertex"] 
                                                   doc = """ A vertex type loop exists on one and only one vertex.  An edgeuse type loop is comprised of one or more edgeuses. size() = number of loops. """)
    uniform int2[]     loop:childTopology        ( doc = """ Provides the start index and number of topology items associated with this Loop. The type of the associated topology is indicated by the `loop:type` attribute. """ )

    uniform token[]    edgeuse:type              ( allowedTokens = ["edge", "vertex", "wireEdge", "vertexAtPole"]
                                                   doc = """ An edge type edgeuse connects an edge to a loopuse. A wireEdge type edgeuse connects an edge to a shell. Vertex and vertexAtPole type edgeuses connect a vertex to a loop. size() = 1/2 number of Edgeuses. """)
    uniform int[]      edgeuse:edgeOrVertexIndex ( doc = """ Index of the owning edge or vertex. Edge index when edgeuse:type == edge or wireEdge, Vertex index when edgeuse:type == vertex or vertexAtPole. size() = 1/2 number of Edgeuses.  """)
    uniform int[]      edgeuse:loopOrShellIndex  ( doc = """ Index of the owning loop or shell. Shell index when edgeuse:type == wireEdge, Loop index otherwise. size() = 1/2 number of Edgeuses.""")
    uniform token[]    edgeuse:orientation       ( allowedTokens = ["same", "opposite"] 
                                                   doc = """ The edge has the same direction as its curve. The "same" oriented edgeuse also runs in the same direction as the edge->curve.  size() = 1/2 number of Edgeuses.""")
    uniform int[]      edgeuse:nextEdgeuse       ( doc = """ Index of next edgeuse when edgeuse:type == edge. O otherwise.  size() = 1/2 number of Edgeuses. """)
    uniform int[]      edgeuse:mateNextEdgeuse   ( doc = """ Index of mate's next edgeuse when edgeuse:type == edge. O otherwise.  size() = 1/2 number of Edgeuses. """)
    uniform int[]      edgeuse:uvCurveIndex      ( doc = """ Provides the index of the curve associated with this edgeuse. The curve is a UV Nurbs curve. """)

    uniform int[]      edge:id                   ( doc = """ User applied ID. size() = number of Edges. """ )
    uniform token[]    edge:curveType            ( allowedTokens = ["BrepCurveNurbsAPI"] )
    uniform int[]      edge:curveIndex           ( doc = """ Provides the index of the curve associated with this edge. The type of the associated geometry is indicated by the `edge:curveType` attribute. """ )
    uniform double2[]  edge:range                ( doc = """ Interval of the edge. size() = number of Edges.""")
    uniform int2[]     edge:vertexIndices        ( doc = """ Indices of the Edge's start and end vertices. size() = number of Edges. """)
    uniform int[]      edge:primaryEdgeuse       ( doc = """ Index of Edge's primary edgeuse. size() = number of Edges.
                                                   Positive Value = pBrepData->m_vEdgeuses[lIndex].m_pEdgeuse1
                                                   Negative Value = pBrepData->m_vEdgeuses[(-lIndex)-1].m_pEdgeuse2 """)

    uniform int[]      vertex:id                 ( doc = """ User applied ID. size() = number of Vertices. """ )
    uniform token[]    vertex:type               ( allowedTokens = ["BrepVertexPointAPI"] )
    uniform int[]      vertex:index              ( doc = """ Provides the index of the position associated with this vertex. The type of the associated geometry is indicated by the `vertex:type` attribute. """ )
}

class "BrepVertexPointAPI" (
    inherits = </APISchemaBase>
    doc = """ Packed Point Vertex description for use as a Brep geometry source """
)
{
    uniform point3d[] brep:vertex:point:position (
        doc = """ Vertex position. size() = number of Vertices. """
        customData = {
            string apiName = "position"
        }
    )
}

class "BrepCurveNurbsAPI" (
    inherits = </APISchemaBase>
    doc = """ Packed Nurbs Curve description for use as a Brep geometry source

    This class varies from the UsdGeomNurbsCurves primarily in having double precision control vertices. 
    
    This schema is analagous to NURBS Curves in packages like Maya and Houdini, often used for interchange of rigging
    and modeling curves. We require 'numSegments + 2 * degree + 1' knots (2 more than maya does). This is to be more
    consistent with RenderMan's NURBS patch specification.  
    
    
    """
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["UsdSolidBrepArray"]
    }
)
{
    uniform point3d[] brep:curve:nurbs:controlVertices (
        doc = """Control vertices of the NurbsCurve.
        size() = SUM(vertexCount)."""
        customData = {
            string apiName = "controlVertices"
        }
    ) 
    
    uniform int[] brep:curve:nurbs:vertexCount (
        doc = """Number of control vertices per curve.
        size() = number of NURBS curves."""
        customData = {
            string apiName = "vertexCount"
        }
    )
    
    uniform int[] brep:curve:nurbs:order (
        doc = """Order of the curve. 
        Order must be positive and is equal to the degree of the polynomial basis to be evaluated, plus 1.
        Its value for the 'i'th curve must be less than or equal to vertexCount[i].
        size() = number of NURBS curves."""
        customData = {
            string apiName = "order"
        }
    )
    
    uniform double[] brep:curve:nurbs:knots (
        doc = """Knot vector providing curve parameterization.
        The length of the slice of the array for the ith curve must be ( vertexCount[i] + order[i] ), and its entries
        must take on non-decreasing values. Knots are listed in multiplicity, e.g. [0, 0, 1, 1]."""
        customData = {
            string apiName = "knots"
        }
    )
    
    uniform double[] brep:curve:nurbs:weights (
        doc = """Provides "w" component for each control point, thus must be the same length as the
        controlVertices attribute. All weights must be positive, w>0. \\note Some DCC's pre-weight the \\em points, but in this schema, \\em points are not pre-weighted."""
        customData = {
            string apiName = "weights"
        }
    )

}

class "BrepCurveUvAPI" (
    inherits = </APISchemaBase>
    doc = """ Packed UV Curve description for use as a Brep geometry source """
)
{
    uniform double2[] brep:curve:uv:controlVertices (
        doc = """2D Control points (u, v) that comprise the curves.
        size() = SUM(vertexCount)."""
        customData = {
            string apiName = "controlVertices"
        }
    )
    
    uniform int[] brep:curve:uv:vertexCount (
        doc = """Number of control vertices for each of the curves.
        size() = number of curves."""
        customData = {
            string apiName = "vertexCount"
        }
    )
    
    uniform int[] brep:curve:uv:order (
        doc = """Order of the curves.
        Order must be positive and is equal to the degree of the polynomial basis to be evaluated, plus 1.
        Its value for the 'i'th curve must be less than or equal to vertexCount[i].
        size() = number of curves."""
        customData = {
            string apiName = "order"
        }
    )
    
    uniform double[] brep:curve:uv:knots (
        doc = """Knot vector providing curve parameterization.
        The length of the slice of the array for the ith curve must be ( vertexCount[i] + order[i] ), and its entries
        must take on non-decreasing values. Knots are listed in multiplicity, e.g. [0, 0, 1, 1]."""
        customData = {
            string apiName = "knots"
        }
    )

    uniform double[] brep:curve:uv:weights (
        doc = """Provides "w" components for each control point, thus must be the same length as the
        controlVertices attribute. All weights must be positive, w>0. \\note Some DCC's pre-weight the \\em points, but in this schema, \\em points are not pre-weighted."""
        size() = controlVertices.size()"""
        customData = {
            string apiName = "weights"
        }
    )
}

class "BrepSurfaceNurbsAPI" (
    inherits = </APISchemaBase>
    doc = """ Packed Nurbs Surface description for use as a Brep geometry source

    These attributes vary from the UsdGeomNurbsPatch primarily in having double precision control vertices. 

    The encoding mostly follows that of RiNuPatch and RiTrimCurve:
    https://renderman.pixar.com/resources/current/RenderMan/geometricPrimitives.html#rinupatch , with some minor
    renaming and coalescing for clarity.

    The layout of control vertices in the \\em points attribute is row-major with U considered rows, and V columns.

    The authored points, orders, knots, weights, and ranges are all that is required to render the nurbs patch.
    """
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["UsdSolidBrepArray"]
    }
)
{
    uniform point3d[] brep:surface:nurbs:controlVertices (
        doc = """Control vertices of the NurbsSurface.
        The layout is row-major with U considered rows, and V columns.
        size() = SUM_i(uVertexCount[i] * vVertexCount[i])."""
        customData = {
            string apiName = "controlVertices"
        }
    )

    uniform int[] brep:surface:nurbs:uVertexCount (
        doc = """Number of control vertices per surface in U dir.
        size() = number of NURBS surfaces."""
        customData = {
            string apiName = "uVertexCount"
        }
    )

    uniform int[] brep:surface:nurbs:vVertexCount (
        doc = """Number of control vertices per surface in V dir.
        size() = number of NURBS surfaces."""
        customData = {
            string apiName = "vVertexCount"
        }
    )
    
    uniform int[] brep:surface:nurbs:uOrder (
        doc = """Order in the U direction.
        Order must be positive and is equal to the degree of the polynomial basis to be evaluated, plus 1.
        size() = number of NURBS surfaces."""
        customData = {
            string apiName = "uOrder"
        }
    )
    
    uniform int[] brep:surface:nurbs:vOrder (
        doc = """Order in the V direction.
        Order must be positive and is equal to the degree of the polynomial basis to be evaluated, plus 1.
        size() = number of NURBS surfaces."""
        customData = {
            string apiName = "vOrder"
        }
    )
    
    uniform double[] brep:surface:nurbs:uKnots (
        doc = """Knot vector for U direction providing parameterization.
        The length of the slice of the array for the ith surface must be ( uVertexCount[i] + uOrder[i] ), and its entries
        must take on non-decreasing values.  Knots are listed in multiplicity, e.g. [0, 0, 1, 1].
        size() = SUM(uVertexCount) + SUM(uOrder)."""
        customData = {
            string apiName = "uKnots"
        }
    )

    uniform double[] brep:surface:nurbs:vKnots (
        doc = """Knot vector for V direction providing parameterization.
        The length of the slice of the array for the ith surface must be ( vVertexCount[i] + vOrder[i] ), and its entries
        must take on non-decreasing values.  Knots are listed in multiplicity, e.g. [0, 0, 1, 1].
        size() = SUM(vVertexCount) + SUM(vOrder)."""
        customData = {
            string apiName = "vKnots"
        }
    )

    uniform double[] brep:surface:nurbs:weights (
        doc = """Provides "w" components for each control point, thus must be the same length as the
        controlVertices attribute. All weights must be positive, w>0. \\note Some DCC's pre-weight the \\em points, but in this schema, \\em points are not pre-weighted."""        
        customData = {
            string apiName = "weights"
        }
    )

}
```
</details>


# **4. Examples**

To exhibit this model we present 4 examples: a unit cube; a unit cube with IDs assigned to each topology object; a non-manifold brep consisting of 2 cubes sharing a face; and nested cubes, creating a void space in a manifold brep.


## **4.1. Cube**

A simple cube, as shown in the following wireframe model.
Each of the 36 topology object has a unique, integer ID tag. There are: 8 vertices, 12 edges, 6 loops, 6 faces, 2 shells, and 2 regions.

![Cube](images/cube.png "Cube")

**CubeIds.usda**
<details>
  <summary> Click to expand </summary>

```
#usda 1.0

def Xform "World"
{
    def BrepArray "CubeIds" (
        prepend apiSchemas = ["BrepCurveUvAPI", "BrepCurveNurbsAPI", "BrepSurfaceNurbsAPI"]
    )
    {
        uniform point3d[] brep:curve:nurbs:controlVertices = [(1, 0, 1), (1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 1, 0), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 0), (1, 1, 0)]
        uniform double[] brep:curve:nurbs:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:nurbs:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:nurbs:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform double2[] brep:curve:uv:controlVertices = [(0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1)]
        uniform double[] brep:curve:uv:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:uv:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:uv:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:uv:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform int[] brep:edgeCount = [12]
        uniform int[] brep:edgeuseCount = [24]
        uniform int[] brep:faceCount = [6]
        uniform int[] brep:faceuseCount = [12]
        uniform int[] brep:id = [0]
        uniform int[] brep:loopCount = [6]
        uniform int[] brep:regionCount = [2]
        uniform int[] brep:shellCount = [2]
        uniform point3d[] brep:surface:nurbs:controlVertices = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 0, 1), (1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (1, 1, 0), (1, 1, 1)]
        uniform double[] brep:surface:nurbs:uKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:uOrder = [2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:uVertexCount = [2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:vKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:vOrder = [2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:vVertexCount = [2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform point3d[] brep:vertex:point:position = [(1, 1, 1), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0)]
        uniform int[] brep:vertexCount = [8]
        uniform int[] edge:curveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        uniform token[] edge:curveType = ["BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI"]
        uniform int[] edge:id = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        uniform int[] edge:primaryEdgeuse = [6, 7, -12, -10, 13, 14, 16, 17, 18, 19, -21, -24]
        uniform double2[] edge:range = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int2[] edge:vertexIndices = [(4, 0), (5, 0), (2, 6), (1, 5), (3, 7), (7, 0), (2, 1), (2, 3), (3, 4), (1, 4), (6, 5), (6, 7)]
        uniform int[] edgeuse:edgeOrVertexIndex = [2, 11, 4, 7, 3, 9, 0, 1, 6, 3, 10, 2, 8, 4, 5, 0, 6, 7, 8, 9, 10, 1, 5, 11]
        uniform int[] edgeuse:loopOrShellIndex = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5]
        uniform int[] edgeuse:mateNextEdgeuse = [-12, -24, 2, 3, -10, 5, -16, -22, 8, 9, -21, 11, 12, -3, -23, 15, -9, -4, -13, -6, 20, 21, 22, 23]
        uniform int[] edgeuse:nextEdgeuse = [-1, -2, 13, 17, -5, 19, -7, -8, 16, 4, -11, 0, 18, -14, -15, 6, -17, -18, -19, -20, 10, 7, 14, 1]
        uniform token[] edgeuse:orientation = ["same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite"]
        uniform token[] edgeuse:type = ["edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge"]
        uniform int[] edgeuse:uvCurveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        uniform float3[] extent = []
        uniform int2[] face:childLoops = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1)]
        uniform int[] face:id = [4, 5, 6, 7, 8, 9]
        uniform int[] face:surfaceIndex = [0, 1, 2, 3, 4, 5]
        uniform token[] face:surfaceType = ["BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI"]
        uniform token[] face:trim = ["uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves"]
        uniform double2[] face:uRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform double2[] face:vRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int[] faceuse:face = [5, 4, 2, 0, 3, 1, 5, 1, 4, 0, 3, 2]
        uniform token[] faceuse:orientation = ["same", "same", "same", "same", "same", "same", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite"]
        uniform int2[] loop:childTopology = [(0, 4), (4, 4), (8, 4), (12, 4), (16, 4), (20, 4)]
        uniform int[] loop:id = [10, 11, 12, 13, 14, 15]
        uniform token[] loop:type = ["edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse"]
        uniform int[] region:id = [0, 1]
        uniform int[] region:numberOfShells = [1, 1]
        uniform token[] region:type = ["void", "solid"]
        uniform int2[] shell:childTopology = [(0, 6), (6, 6)]
        uniform int[] shell:id = [2, 3]
        uniform token[] shell:type = ["faceuse", "faceuse"]
        uniform int[] vertex:id = [28, 29, 30, 31, 32, 33, 34, 35]
        uniform int[] vertex:index = [0, 1, 2, 3, 4, 5, 6, 7]
        uniform token[] vertex:type = ["BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI"]
    }
}
```
</details>
 

## **4.2. Non-manifold cubes**

In this example, we show how each partition of space is explicitly represented with a Region. Two cubes sharing a face have 3 regions: the infinite region outside the Brep, and 1 region inside each cube.  The model contains 11 faces, as one is shared between the cubes.

In the wireframe model image below, the non-manifold edges are shown in blue. An edge is non-manifold when it does not connect to exactly 2 faces (or 1 face twice for closed surfaces).


![NonManifold Cubes](images/cube2.png "Non-manifold cubes")


**nonManifoldCubes.usda**

<details>
  <summary> Click to expand </summary>

```
#usda 1.0

def Xform "World"
{
    def BrepArray "nonManifoldCubes" (
        prepend apiSchemas = ["BrepCurveUvAPI", "BrepCurveNurbsAPI", "BrepSurfaceNurbsAPI"]
    )
    {
        uniform point3d[] brep:curve:nurbs:controlVertices = [(1, 0, 1), (1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 1, 0), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 1), (2, 0, 1), (2, 0, 1), (2, 1, 1), (1, 1, 1), (2, 1, 1), (2, 1, 0), (2, 1, 1), (1, 1, 0), (2, 1, 0), (2, 0, 0), (2, 1, 0), (1, 0, 0), (2, 0, 0), (2, 0, 0), (2, 0, 1)]
        uniform double[] brep:curve:nurbs:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:nurbs:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:nurbs:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform double2[] brep:curve:uv:controlVertices = [(0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 1), (1, 1)]
        uniform double[] brep:curve:uv:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:uv:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:uv:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:uv:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform int[] brep:edgeCount = [20]
        uniform int[] brep:edgeuseCount = [44]
        uniform int[] brep:faceCount = [11]
        uniform int[] brep:faceuseCount = [22]
        uniform int[] brep:id = [0]
        uniform int[] brep:loopCount = [11]
        uniform int[] brep:regionCount = [3]
        uniform int[] brep:shellCount = [3]
        uniform point3d[] brep:surface:nurbs:controlVertices = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 0, 1), (1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (1, 1, 0), (1, 1, 1), (1, 0, 1), (2, 0, 1), (1, 1, 1), (2, 1, 1), (1, 1, 0), (1, 1, 1), (2, 1, 0), (2, 1, 1), (1, 0, 0), (1, 1, 0), (2, 0, 0), (2, 1, 0), (2, 0, 0), (2, 1, 0), (2, 0, 1), (2, 1, 1), (1, 0, 0), (2, 0, 0), (1, 0, 1), (2, 0, 1)]
        uniform double[] brep:surface:nurbs:uKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:uOrder = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:uVertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:vKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:vOrder = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:vVertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform point3d[] brep:vertex:point:position = [(1, 1, 1), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (2, 0, 1), (2, 1, 1), (2, 1, 0), (2, 0, 0)]
        uniform int[] brep:vertexCount = [12]
        uniform int[] edge:curveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        uniform token[] edge:curveType = ["BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI"]
        uniform int[] edge:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] edge:primaryEdgeuse = [6, 7, -12, -10, 13, 14, 16, 17, 18, 19, -21, -24, 25, 26, -28, -31, -32, -35, -36, -37]
        uniform double2[] edge:range = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int2[] edge:vertexIndices = [(4, 0), (5, 0), (2, 6), (1, 5), (3, 7), (7, 0), (2, 1), (2, 3), (3, 4), (1, 4), (6, 5), (6, 7), (4, 8), (8, 9), (0, 9), (10, 9), (7, 10), (11, 10), (3, 11), (11, 8)]
        uniform int[] edgeuse:edgeOrVertexIndex = [2, 11, 4, 7, 3, 9, 0, 1, 6, 3, 10, 2, 8, 4, 5, 0, 6, 7, 8, 9, 10, 1, 5, 11, 0, 12, 13, 14, 5, 14, 15, 16, 4, 16, 17, 18, 19, 17, 15, 13, 8, 18, 19, 12]
        uniform int[] edgeuse:loopOrShellIndex = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10]
        uniform int[] edgeuse:mateNextEdgeuse = [-12, -24, 2, 3, -10, 5, -16, -22, 8, 9, -21, 11, 12, -3, -23, 15, -9, -4, -13, -6, 20, 21, 22, 23, 24, -44, -40, 27, 14, -28, 30, 31, 13, -32, 34, 35, 36, -35, -31, 39, 40, -36, -37, 43]
        uniform int[] edgeuse:nextEdgeuse = [-1, -2, 32, 17, -5, 19, -7, -8, 16, 4, -11, 0, -41, -14, -15, -25, -17, -18, -19, -20, 10, 7, 28, 1, 6, -26, -27, 29, -29, -30, 38, 33, -33, -34, 37, 41, 42, -38, -39, 26, 18, -42, -43, 25]
        uniform token[] edgeuse:orientation = ["same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite"]
        uniform token[] edgeuse:type = ["edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge"]
        uniform int[] edgeuse:uvCurveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 24, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        uniform float3[] extent = []
        uniform int2[] face:childLoops = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1)]
        uniform int[] face:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] face:surfaceIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        uniform token[] face:surfaceType = ["BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI"]
        uniform token[] face:trim = ["uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves"]
        uniform double2[] face:uRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform double2[] face:vRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int[] faceuse:face = [5, 4, 2, 0, 1, 6, 7, 8, 9, 10, 5, 1, 4, 0, 3, 2, 10, 8, 7, 6, 9, 3]
        uniform token[] faceuse:orientation = ["same", "same", "same", "same", "same", "same", "same", "same", "same", "same", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "same"]
        uniform int2[] loop:childTopology = [(0, 4), (4, 4), (8, 4), (12, 4), (16, 4), (20, 4), (24, 4), (28, 4), (32, 4), (36, 4), (40, 4)]
        uniform int[] loop:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform token[] loop:type = ["edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse"]
        uniform int[] region:id = [0, 0, 0]
        uniform int[] region:numberOfShells = [1, 1, 1]
        uniform token[] region:type = ["void", "solid", "solid"]
        uniform int2[] shell:childTopology = [(0, 10), (10, 6), (16, 6)]
        uniform int[] shell:id = [0, 0, 0]
        uniform token[] shell:type = ["faceuse", "faceuse", "faceuse"]
        uniform int[] vertex:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] vertex:index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        uniform token[] vertex:type = ["BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI"]
    }
}
```

</details>
 

## **4.3. Cube With Internal Void**

This example shows a manifold Brep with an internal void. The infinite region is partitioned from the solid region by the cube shell.  The solid region is partitioned from the internal void region by a shell consisting of a single spherical face.

![Cube With Internal Void](images/cubevoid.png "Cube With Internal Void")


**cubeWithVoid.usda**
<details>
  <summary> Click to expand </summary>

```
#usda 1.0

def Xform "World"
{
    def BrepArray "cubeWithVoid" (
        prepend apiSchemas = ["BrepCurveUvAPI", "BrepCurveNurbsAPI", "BrepSurfaceNurbsAPI"]
    )
    {
        uniform point3d[] brep:curve:nurbs:controlVertices = [(1, 0, 1), (1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 1, 0), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 0), (1, 1, 0), (0.49999999999999994, 0.5, 0.3), (0.7, 0.5, 0.29999999999999993), (0.7, 0.5, 0.49999999999999994), (0.7, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7)]
        uniform double[] brep:curve:nurbs:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0.5, 0.5, 1, 1, 1]
        uniform int[] brep:curve:nurbs:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3]
        uniform int[] brep:curve:nurbs:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5]
        uniform double[] brep:curve:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.7071067811865476, 1, 0.7071067811865476, 1]
        uniform double2[] brep:curve:uv:controlVertices = [(0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (1, 0), (1, 1)]
        uniform double[] brep:curve:uv:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:uv:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:uv:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:uv:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform int[] brep:edgeCount = [13]
        uniform int[] brep:edgeuseCount = [26]
        uniform int[] brep:faceCount = [7]
        uniform int[] brep:faceuseCount = [14]
        uniform int[] brep:id = [0]
        uniform int[] brep:loopCount = [7]
        uniform int[] brep:regionCount = [3]
        uniform int[] brep:shellCount = [4]
        uniform point3d[] brep:surface:nurbs:controlVertices = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 0, 1), (1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (1, 1, 0), (1, 1, 1), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.49999999999999994, 0.5, 0.3), (0.7, 0.5, 0.29999999999999993), (0.7, 0.7, 0.29999999999999993), (0.5, 0.7, 0.29999999999999993), (0.30000000000000004, 0.7, 0.29999999999999993), (0.30000000000000004, 0.5, 0.29999999999999993), (0.30000000000000004, 0.30000000000000004, 0.29999999999999993), (0.49999999999999994, 0.30000000000000004, 0.29999999999999993), (0.7, 0.3, 0.29999999999999993), (0.7, 0.5, 0.29999999999999993), (0.7, 0.5, 0.49999999999999994), (0.7, 0.7, 0.49999999999999994), (0.5, 0.7, 0.49999999999999994), (0.30000000000000004, 0.7, 0.49999999999999994), (0.30000000000000004, 0.5, 0.49999999999999994), (0.30000000000000004, 0.30000000000000004, 0.49999999999999994), (0.49999999999999994, 0.30000000000000004, 0.49999999999999994), (0.7, 0.3, 0.49999999999999994), (0.7, 0.5, 0.49999999999999994), (0.7, 0.5, 0.7), (0.7, 0.7, 0.7), (0.5, 0.7, 0.7), (0.30000000000000004, 0.7, 0.7), (0.30000000000000004, 0.5, 0.7), (0.30000000000000004, 0.30000000000000004, 0.7), (0.49999999999999994, 0.30000000000000004, 0.7), (0.7, 0.3, 0.7), (0.7, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7), (0.5000000000000001, 0.5, 0.7)]
        uniform double[] brep:surface:nurbs:uKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0.25, 0.25, 0.5, 0.5, 0.75, 0.75, 1, 1, 1]
        uniform int[] brep:surface:nurbs:uOrder = [2, 2, 2, 2, 2, 2, 3]
        uniform int[] brep:surface:nurbs:uVertexCount = [2, 2, 2, 2, 2, 2, 9]
        uniform double[] brep:surface:nurbs:vKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0.5, 0.5, 1, 1, 1]
        uniform int[] brep:surface:nurbs:vOrder = [2, 2, 2, 2, 2, 2, 3]
        uniform int[] brep:surface:nurbs:vVertexCount = [2, 2, 2, 2, 2, 2, 5]
        uniform double[] brep:surface:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 0.5000000000000001, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1, 0.7071067811865476, 1]
        uniform point3d[] brep:vertex:point:position = [(1, 1, 1), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (0.5000000000000001, 0.5, 0.7), (0.49999999999999994, 0.5, 0.3)]
        uniform int[] brep:vertexCount = [10]
        uniform int[] edge:curveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        uniform token[] edge:curveType = ["BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI"]
        uniform int[] edge:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] edge:primaryEdgeuse = [6, 7, -12, -10, 13, 14, 16, 17, 18, 19, -21, -24, -25]
        uniform double2[] edge:range = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int2[] edge:vertexIndices = [(4, 0), (5, 0), (2, 6), (1, 5), (3, 7), (7, 0), (2, 1), (2, 3), (3, 4), (1, 4), (6, 5), (6, 7), (9, 8)]
        uniform int[] edgeuse:edgeOrVertexIndex = [2, 11, 4, 7, 3, 9, 0, 1, 6, 3, 10, 2, 8, 4, 5, 0, 6, 7, 8, 9, 10, 1, 5, 11, 12, 12]
        uniform int[] edgeuse:loopOrShellIndex = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6]
        uniform int[] edgeuse:mateNextEdgeuse = [-12, -24, 2, 3, -10, 5, -16, -22, 8, 9, -21, 11, 12, -3, -23, 15, -9, -4, -13, -6, 20, 21, 22, 23, 24, -25]
        uniform int[] edgeuse:nextEdgeuse = [-1, -2, 13, 17, -5, 19, -7, -8, 16, 4, -11, 0, 18, -14, -15, 6, -17, -18, -19, -20, 10, 7, 14, 1, 25, -26]
        uniform token[] edgeuse:orientation = ["same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same"]
        uniform token[] edgeuse:type = ["edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge"]
        uniform int[] edgeuse:uvCurveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        uniform float3[] extent = []
        uniform int2[] face:childLoops = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)]
        uniform int[] face:id = [0, 0, 0, 0, 0, 0, 0]
        uniform int[] face:surfaceIndex = [0, 1, 2, 3, 4, 5, 6]
        uniform token[] face:surfaceType = ["BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI"]
        uniform token[] face:trim = ["uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves"]
        uniform double2[] face:uRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform double2[] face:vRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int[] faceuse:face = [5, 4, 2, 0, 3, 1, 5, 1, 4, 0, 3, 2, 6, 6]
        uniform token[] faceuse:orientation = ["same", "same", "same", "same", "same", "same", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "same", "opposite"]
        uniform int2[] loop:childTopology = [(0, 4), (4, 4), (8, 4), (12, 4), (16, 4), (20, 4), (24, 2)]
        uniform int[] loop:id = [0, 0, 0, 0, 0, 0, 0]
        uniform token[] loop:type = ["edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse"]
        uniform int[] region:id = [0, 0, 0]
        uniform int[] region:numberOfShells = [1, 2, 1]
        uniform token[] region:type = ["void", "solid", "void"]
        uniform int2[] shell:childTopology = [(0, 6), (6, 6), (12, 1), (13, 1)]
        uniform int[] shell:id = [0, 0, 0, 0]
        uniform token[] shell:type = ["faceuse", "faceuse", "faceuse", "faceuse"]
        uniform int[] vertex:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] vertex:index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        uniform token[] vertex:type = ["BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI"]
    }
}
```

</details>

## **4.4 BrepArray with multiple Breps, individual colors**

This example shows a 2 Breps with distinct materials in a single BrepArray.
The BrepArray assigns unique materials to the Breps with the GeomSubset property.

![BrepArray](images/BrepArray.png "BrepArray with multiple Breps")


**cubeBrepArray.usda**

<details>
  <summary> Click to expand </summary>

```
#usda 1.0

def Xform "World"
{
    def BrepArray "brepArray" (
        prepend apiSchemas = ["BrepCurveUvAPI", "BrepCurveNurbsAPI", "BrepSurfaceNurbsAPI"]
    )
    {
        uniform point3d[] brep:curve:nurbs:controlVertices = [(1, 0, 1), (1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 1, 0), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 0), (1, 1, 0), (3, 0, 1), (3, 1, 1), (2, 1, 1), (3, 1, 1), (2, 0, 0), (2, 1, 0), (2, 0, 1), (2, 1, 1), (3, 0, 0), (3, 1, 0), (3, 1, 0), (3, 1, 1), (2, 0, 0), (2, 0, 1), (2, 0, 0), (3, 0, 0), (3, 0, 0), (3, 0, 1), (2, 0, 1), (3, 0, 1), (2, 1, 0), (2, 1, 1), (2, 1, 0), (3, 1, 0)]
        uniform double[] brep:curve:nurbs:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:nurbs:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:nurbs:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform double2[] brep:curve:uv:controlVertices = [(0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1)]
        uniform double[] brep:curve:uv:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:uv:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:uv:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:uv:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform int[] brep:edgeCount = [12, 12]
        uniform int[] brep:edgeuseCount = [24, 24]
        uniform int[] brep:faceCount = [6, 6]
        uniform int[] brep:faceuseCount = [12, 12]
        uniform int[] brep:id = [0, 0]
        uniform int[] brep:loopCount = [6, 6]
        uniform int[] brep:regionCount = [2, 2]
        uniform int[] brep:shellCount = [2, 2]
        uniform point3d[] brep:surface:nurbs:controlVertices = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 0, 1), (1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (1, 1, 0), (1, 1, 1), (2, 0, 0), (2, 1, 0), (3, 0, 0), (3, 1, 0), (2, 0, 1), (3, 0, 1), (2, 1, 1), (3, 1, 1), (2, 0, 0), (2, 0, 1), (2, 1, 0), (2, 1, 1), (3, 0, 0), (3, 1, 0), (3, 0, 1), (3, 1, 1), (2, 0, 0), (3, 0, 0), (2, 0, 1), (3, 0, 1), (2, 1, 0), (2, 1, 1), (3, 1, 0), (3, 1, 1)]
        uniform double[] brep:surface:nurbs:uKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:uOrder = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:uVertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:vKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:vOrder = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:vVertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform point3d[] brep:vertex:point:position = [(1, 1, 1), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (3, 1, 1), (2, 0, 1), (2, 0, 0), (3, 0, 0), (3, 0, 1), (2, 1, 1), (2, 1, 0), (3, 1, 0)]
        uniform int[] brep:vertexCount = [8, 8]
        uniform int[] edge:curveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        uniform token[] edge:curveType = ["BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI"]
        uniform int[] edge:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] edge:primaryEdgeuse = [6, 7, -12, -10, 13, 14, 16, 17, 18, 19, -21, -24, 30, 31, 12, 14, 37, 38, 40, 41, 42, 43, 3, 0]
        uniform double2[] edge:range = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int2[] edge:vertexIndices = [(4, 0), (5, 0), (2, 6), (1, 5), (3, 7), (7, 0), (2, 1), (2, 3), (3, 4), (1, 4), (6, 5), (6, 7), (12, 8), (13, 8), (10, 14), (9, 13), (11, 15), (15, 8), (10, 9), (10, 11), (11, 12), (9, 12), (14, 13), (14, 15)]
        uniform int[] edgeuse:edgeOrVertexIndex = [2, 11, 4, 7, 3, 9, 0, 1, 6, 3, 10, 2, 8, 4, 5, 0, 6, 7, 8, 9, 10, 1, 5, 11, 14, 23, 16, 19, 15, 21, 12, 13, 18, 15, 22, 14, 20, 16, 17, 12, 18, 19, 20, 21, 22, 13, 17, 23]
        uniform int[] edgeuse:loopOrShellIndex = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11]
        uniform int[] edgeuse:mateNextEdgeuse = [-12, -24, 2, 3, -10, 5, -16, -22, 8, 9, -21, 11, 12, -3, -23, 15, -9, -4, -13, -6, 20, 21, 22, 23, 12, 0, 26, 27, 14, 29, 8, 2, 32, 33, 3, 35, 36, 21, 1, 39, 15, 20, 11, 18, 44, 45, 46, 47]
        uniform int[] edgeuse:nextEdgeuse = [-1, -2, 13, 17, -5, 19, -7, -8, 16, 4, -11, 0, 18, -14, -15, 6, -17, -18, -19, -20, 10, 7, 14, 1, 23, 22, 37, 41, 19, 43, 17, 16, 40, 28, 13, 24, 42, 10, 9, 30, 7, 6, 5, 4, 34, 31, 38, 25]
        uniform token[] edgeuse:orientation = ["same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite"]
        uniform token[] edgeuse:type = ["edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge"]
        uniform int[] edgeuse:uvCurveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
        uniform float3[] extent = []
        uniform int2[] face:childLoops = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1), (11, 1)]
        uniform int[] face:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] face:surfaceIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        uniform token[] face:surfaceType = ["BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI"]
        uniform token[] face:trim = ["uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves"]
        uniform double2[] face:uRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform double2[] face:vRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int[] faceuse:face = [5, 4, 2, 0, 3, 1, 5, 1, 4, 0, 3, 2, 11, 10, 8, 6, 9, 7, 11, 7, 10, 6, 9, 8]
        uniform token[] faceuse:orientation = ["same", "same", "same", "same", "same", "same", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite", "same", "same", "same", "same", "same", "same", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite"]
        uniform int2[] loop:childTopology = [(0, 4), (4, 4), (8, 4), (12, 4), (16, 4), (20, 4), (24, 4), (28, 4), (32, 4), (36, 4), (40, 4), (44, 4)]
        uniform int[] loop:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform token[] loop:type = ["edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse"]
        uniform int[] region:id = [0, 0, 0, 0]
        uniform int[] region:numberOfShells = [1, 1, 1, 1]
        uniform token[] region:type = ["void", "solid", "void", "solid"]
        uniform int2[] shell:childTopology = [(0, 6), (6, 6), (12, 6), (18, 6)]
        uniform int[] shell:id = [0, 0, 0, 0]
        uniform token[] shell:type = ["faceuse", "faceuse", "faceuse", "faceuse"]
        uniform int[] vertex:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] vertex:index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        uniform token[] vertex:type = ["BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI"]

        def GeomSubset "subset_0" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token elementType = "brep"
            uniform int[] indices = [0]
            rel material:binding = </World/Looks/Black>
        }

        def GeomSubset "subset_1" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token elementType = "brep"
            uniform int[] indices = [1]
            rel material:binding = </World/Looks/Green>

        }
    }

    def "Looks"
    {
        def Material "Black"
        {
            token outputs:surface.connect = </World/Looks/Black/PBRShader.outputs:surface>

            def Shader "PBRShader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0, 0, 0)
                token outputs:surface
            }
        }

        def Material "Green"
        {
            token outputs:surface.connect = </World/Looks/Green/PBRShader.outputs:surface>

            def Shader "PBRShader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.463, 0.725, 0)
                token outputs:surface
            }
        }
    }

    def Mesh "Mesh_black" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {
        uniform vector3f[] extent = [(0, 0, 0), (1, 1, 1)]
        uniform int[] faceVertexCounts = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        uniform int[] faceVertexIndices = [0, 2, 3, 2, 0, 1, 0, 5, 4, 5, 0, 3, 4, 7, 6, 7, 4, 5, 3, 7, 5, 7, 3, 2, 1, 7, 2, 7, 1, 6, 0, 6, 1, 6, 0, 4]
        rel material:binding = </World/Looks/Black>
        uniform vector3f[] points = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        uniform normal3f[] primvars:normals = [(0, 0, -1), (0, -1, 0), (-1, 0, 0), (0, 0, -1), (0, 1, 0), (-1, 0, 0), (0, 0, -1), (1, 0, 0), (0, 1, 0), (0, 0, -1), (0, -1, 0), (1, 0, 0), (0, -1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (1, 0, 0), (0, 0, 1), (0, 1, 0), (-1, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)] (
            interpolation = "faceVarying"
        )
        uniform int[] primvars:normals:indices = [0, 6, 9, 6, 0, 3, 1, 15, 12, 15, 1, 10, 13, 21, 18, 21, 13, 16, 11, 22, 17, 22, 11, 7, 4, 23, 8, 23, 4, 19, 2, 20, 5, 20, 2, 14]
        uniform token subdivisionScheme = "none"
    }

    def Mesh "Mesh_green" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {
        uniform vector3f[] extent = [(2, 0, 0), (3, 1, 1)]
        uniform int[] faceVertexCounts = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        uniform int[] faceVertexIndices = [0, 2, 3, 2, 0, 1, 0, 5, 4, 5, 0, 3, 4, 7, 6, 7, 4, 5, 3, 7, 5, 7, 3, 2, 1, 7, 2, 7, 1, 6, 0, 6, 1, 6, 0, 4]
        rel material:binding = </World/Looks/Green>
        uniform vector3f[] points = [(2, 0, 0), (2, 1, 0), (3, 1, 0), (3, 0, 0), (2, 0, 1), (3, 0, 1), (2, 1, 1), (3, 1, 1)]
        uniform normal3f[] primvars:normals = [(0, 0, -1), (0, -1, 0), (-1, 0, 0), (0, 0, -1), (0, 1, 0), (-1, 0, 0), (0, 0, -1), (1, 0, 0), (0, 1, 0), (0, 0, -1), (0, -1, 0), (1, 0, 0), (0, -1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (1, 0, 0), (0, 0, 1), (0, 1, 0), (-1, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)] (
            interpolation = "faceVarying"
        )
        uniform int[] primvars:normals:indices = [0, 6, 9, 6, 0, 3, 1, 15, 12, 15, 1, 10, 13, 21, 18, 21, 13, 16, 11, 22, 17, 22, 11, 7, 4, 23, 8, 23, 4, 19, 2, 20, 5, 20, 2, 14]
        uniform token subdivisionScheme = "none"
    }
}
```
</details>

## **4.5 Brep with materials applied to faces**

In this example material properties are applied to each face of the Brep.
When tessellated and authored as a _UsdGeomMesh_, _UsdGeomSubset_ is used to assign appropriate material bindings.

![Brep Face Materials](images/FaceMaterials.png "Brep with materials per face")


**CubeFaceMaterials.usda**

<details>
  <summary> Click to expand </summary>

```
#usda 1.0

def Xform "World"
{
    def BrepArray "CubeMats" (
        prepend apiSchemas = ["BrepCurveUvAPI", "BrepCurveNurbsAPI", "BrepSurfaceNurbsAPI"]
    )
    {
        uniform point3d[] brep:curve:nurbs:controlVertices = [(1, 0, 1), (1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 1, 0), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 0), (1, 1, 0)]
        uniform double[] brep:curve:nurbs:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:nurbs:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:nurbs:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform double2[] brep:curve:uv:controlVertices = [(0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (0, 1), (0, 0), (1, 0), (1, 0), (1, 1), (0, 1), (1, 1), (0, 0), (1, -2.220446049250313e-16), (1, -2.220446049250313e-16), (0.9999999999999998, 0.9999999999999998), (-2.220446049250313e-16, 1), (0.9999999999999998, 0.9999999999999998), (0, 0), (-2.220446049250313e-16, 1)]
        uniform double[] brep:curve:uv:knots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:curve:uv:order = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform int[] brep:curve:uv:vertexCount = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        uniform double[] brep:curve:uv:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform int[] brep:edgeCount = [12]
        uniform int[] brep:edgeuseCount = [24]
        uniform int[] brep:faceCount = [6]
        uniform int[] brep:faceuseCount = [12]
        uniform int[] brep:id = [0]
        uniform int[] brep:loopCount = [6]
        uniform int[] brep:regionCount = [2]
        uniform int[] brep:shellCount = [2]
        uniform point3d[] brep:surface:nurbs:controlVertices = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 1, 0), (1, 0, 1), (1, 1, 1), (0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 0), (0, 1, 1), (1, 1, 0), (1, 1, 1)]
        uniform double[] brep:surface:nurbs:uKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:uOrder = [2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:uVertexCount = [2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:vKnots = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]
        uniform int[] brep:surface:nurbs:vOrder = [2, 2, 2, 2, 2, 2]
        uniform int[] brep:surface:nurbs:vVertexCount = [2, 2, 2, 2, 2, 2]
        uniform double[] brep:surface:nurbs:weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        uniform point3d[] brep:vertex:point:position = [(1, 1, 1), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0)]
        uniform int[] brep:vertexCount = [8]
        uniform int[] edge:curveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        uniform token[] edge:curveType = ["BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI", "BrepCurveNurbsAPI"]
        uniform int[] edge:id = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] edge:primaryEdgeuse = [6, 7, -12, -10, 13, 14, 16, 17, 18, 19, -21, -24]
        uniform double2[] edge:range = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int2[] edge:vertexIndices = [(4, 0), (5, 0), (2, 6), (1, 5), (3, 7), (7, 0), (2, 1), (2, 3), (3, 4), (1, 4), (6, 5), (6, 7)]
        uniform int[] edgeuse:edgeOrVertexIndex = [2, 11, 4, 7, 3, 9, 0, 1, 6, 3, 10, 2, 8, 4, 5, 0, 6, 7, 8, 9, 10, 1, 5, 11]
        uniform int[] edgeuse:loopOrShellIndex = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5]
        uniform int[] edgeuse:mateNextEdgeuse = [-12, -24, 2, 3, -10, 5, -16, -22, 8, 9, -21, 11, 12, -3, -23, 15, -9, -4, -13, -6, 20, 21, 22, 23]
        uniform int[] edgeuse:nextEdgeuse = [-1, -2, 13, 17, -5, 19, -7, -8, 16, 4, -11, 0, 18, -14, -15, 6, -17, -18, -19, -20, 10, 7, 14, 1]
        uniform token[] edgeuse:orientation = ["same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite", "opposite", "same", "same", "opposite", "opposite", "same", "same", "opposite", "same", "same", "opposite", "opposite"]
        uniform token[] edgeuse:type = ["edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge", "edge"]
        uniform int[] edgeuse:uvCurveIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        uniform float3[] extent = []
        uniform int2[] face:childLoops = [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1)]
        uniform int[] face:id = [0, 0, 0, 0, 0, 0]
        uniform int[] face:surfaceIndex = [0, 1, 2, 3, 4, 5]
        uniform token[] face:surfaceType = ["BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI", "BrepSurfaceNurbsAPI"]
        uniform token[] face:trim = ["uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves", "uvCurves"]
        uniform double2[] face:uRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform double2[] face:vRange = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        uniform int[] faceuse:face = [5, 4, 2, 0, 3, 1, 5, 1, 4, 0, 3, 2]
        uniform token[] faceuse:orientation = ["same", "same", "same", "same", "same", "same", "opposite", "opposite", "opposite", "opposite", "opposite", "opposite"]
        uniform int2[] loop:childTopology = [(0, 4), (4, 4), (8, 4), (12, 4), (16, 4), (20, 4)]
        uniform int[] loop:id = [0, 0, 0, 0, 0, 0]
        uniform token[] loop:type = ["edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse", "edgeuse"]
        uniform int[] region:id = [0, 0]
        uniform int[] region:numberOfShells = [1, 1]
        uniform token[] region:type = ["void", "solid"]
        uniform int2[] shell:childTopology = [(0, 6), (6, 6)]
        uniform int[] shell:id = [0, 0]
        uniform token[] shell:type = ["faceuse", "faceuse"]
        uniform int[] vertex:id = [0, 0, 0, 0, 0, 0, 0, 0]
        uniform int[] vertex:index = [0, 1, 2, 3, 4, 5, 6, 7]
        uniform token[] vertex:type = ["BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI", "BrepVertexPointAPI"]

        def GeomSubset "subset_0" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token elementType = "face"
            uniform int[] indices = [0, 1, 2]
            rel material:binding = </World/Looks/Black>
        }

        def GeomSubset "subset_1" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token elementType = "face"
            uniform int[] indices = [3, 4, 5]
            rel material:binding = </World/Looks/Green>
        }
    }

    def "Looks"
    {
        def Material "Black"
        {
            token outputs:surface.connect = </World/Looks/Black/PBRShader.outputs:surface>

            def Shader "PBRShader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0, 0, 0)
                token outputs:surface
            }
        }

        def Material "Green"
        {
            token outputs:surface.connect = </World/Looks/Green/PBRShader.outputs:surface>

            def Shader "PBRShader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.463, 0.725, 0)
                token outputs:surface
            }
        }
    }

    def Mesh "Mesh"
    {
        uniform vector3f[] extent = [(0, 0, 0), (1, 1, 1)]
        uniform int[] faceVertexCounts = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        uniform int[] faceVertexIndices = [0, 2, 3, 2, 0, 1, 0, 5, 4, 5, 0, 3, 4, 7, 6, 7, 4, 5, 3, 7, 5, 7, 3, 2, 1, 7, 2, 7, 1, 6, 0, 6, 1, 6, 0, 4]
        uniform vector3f[] points = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        uniform normal3f[] primvars:normals = [(0, 0, -1), (0, -1, 0), (-1, 0, 0), (0, 0, -1), (0, 1, 0), (-1, 0, 0), (0, 0, -1), (1, 0, 0), (0, 1, 0), (0, 0, -1), (0, -1, 0), (1, 0, 0), (0, -1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (1, 0, 0), (0, 0, 1), (0, 1, 0), (-1, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)] (
            interpolation = "faceVarying"
        )
        uniform int[] primvars:normals:indices = [0, 6, 9, 6, 0, 3, 1, 15, 12, 15, 1, 10, 13, 21, 18, 21, 13, 16, 11, 22, 17, 22, 11, 7, 4, 23, 8, 23, 4, 19, 2, 20, 5, 20, 2, 14]
        uniform token subdivisionScheme = "none"

        def GeomSubset "subset_0" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token elementType = "face"
            uniform int[] indices = [0, 1, 4, 5, 10, 11]
            rel material:binding = </World/Looks/Black>
        }

        def GeomSubset "subset_1" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token elementType = "face"
            uniform int[] indices = [2, 3, 6, 7, 8, 9]
            rel material:binding = </World/Looks/Green>
        }
    }
}

```
</details>

# **5. References**

Lee, K., 1999. Principles of CAD/CAM/CAE Systems. Addison-Wesley Longman Publishing
Co., Inc., 582 pp.