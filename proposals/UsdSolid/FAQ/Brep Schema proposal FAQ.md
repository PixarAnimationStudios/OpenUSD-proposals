
# **Brep Schema proposal FAQ**

**Why not represent Breps as black box models? What advantages come with incorporating the schema directly into USD?**

Having the Brep data available within USD will enable enhanced functionality, including measurement, interference checking and simulation with exact geometry. Current functionality relies on mesh-based solids, which introduce approximation errors. 

This design allows the annotation of Brep topology and geometry with cross-domain data, such as physical and material properties. This metadata could be assigned per BrepArray, and by using GeomSubsets, per Brep, or per topology object.

Having Brep data in USD fits with its ability to aggregate data from various sources to create homogeneous scenes.  This will allow users to control, e.g., the visual data quality rather than relying on the choices made by the user who exported the data to USD.

Further, the AOUSD geometry working group could explore the possibility of using sparse overrides for variants. One could calculate an appropriate delta that represents a sequence of changes to a source Brep. This work is not actively considered in this proposal, but presented here as an avenue for future work. 


**Why should the core Brep prim allow an array of Breps? Does this not conflate assembly structures, scenegraph hierarchies, etc. into a single prim?**

A BrepArray is not intended to be an assembly or scenegraph hierarchy representation. It is meant to be a list of Brep parts. The design intent is to be as flexible as possible, leaning into USD’s universal nature. 

For many users, limiting the BrepArray list length to one to author Breps with a 1-to-1 relationship between prims and Breps will be the natural way to represent their data. The BrepArray 1-to-1 model structure can leverage USD’s referencing and relationships. 

For some, the efficiencies of reducing prim count will motivate them to find a way to group like Breps into a single BrepArray. A set of rigidly connected bodies with uniform material properties would be a good candidate. 


**Can the BrepArray be separated into smaller prims?**

No, a BrepArray only represents whole Breps; it does not represent the individual topology objects that make up a Brep with individual prims. An alternative one-prim-per-Brep-topology-object design would be useful if there was a strong use case for CAD design in USD. Without that use case we cannot justify such a proliferation of prims. The aim of the proposal is to support the use of designs created in CAD modelers. 



**Why not use STEP?**

STEP has a couple of drawbacks that this design overcomes. First, the BrepArray can represent non-manifold models (AKA general bodies or irregular space partitions), which STEP cannot do. Second, STEP data cannot be flexibly annotated, so it has no mechanism for adding domain specific metadata.



