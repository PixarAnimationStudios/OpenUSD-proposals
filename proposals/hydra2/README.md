![Status:Implemented, 21.11](https://img.shields.io/badge/Implemented,%2021.11-blue)
# Modular Scene Delegation and Manipulation in Hydra
Copyright &copy; Pixar Animation Studios, 2021, version 1.0

## Proposal

We propose a new mechanism that represents the scene to the renderer backend as 
a full scene hierarchy, each node of which is capable of indirecting its 
requests to the delegated source scene. Our proposed system is also flexible 
and allows custom data to be transported easily.

We introduce two new concepts: data sources and scene indices. From a high level 
a data source provides the data indirection, and a scene index provides the 
ability to manipulate scene data. We also discuss how schemas can be used to 
give more meaning to data sources, how dependencies can be used across data 
sources, and how to locate data sources.

The full proposal may be viewed here: [Proposal PDF](ModularSceneDelegationAndManipulationInHydra.pdf)
