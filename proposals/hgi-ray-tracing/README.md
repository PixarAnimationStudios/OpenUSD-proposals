# HGI Ray Tracing

The code for the proposal described here is available in the following branch:

https://github.com/autodesk-forks/USD/tree/adsk/feature/hgiraytracing-metal

## Background

The Hydra Graphics Interface (HGI) library is the abstraction layer used by the USD Hydra Imaging core package and the HdStorm render delegate to support the advanced functionality provided by modern graphics APIs, such as Vulkan and Metal. By abstracting the low-level GPU interface into a simple, easy-to-use API, HGI allows higher-level rendering code to perform a common set of graphics operations without targeting a specific vendor API. A render delegate that uses HGI can then more easily target new GPU APIs.

The HGI interface is currently based on rasterization only. It does not support any of the recently released extensions to the Vulkan or Metal graphics APIs that enable GPU-accelerated ray tracing.

## Expectations

Hydra render delegates should be able to utilize GPU-accelerated ray tracing, while continuing to benefit from the easy-to-use HGI interface for GPU command submission. In areas of the renderer not directly related to ray tracing (e.g., compositing textures using fullscreen quads), render delegates should be able to use the existing HGI library with no changes, and opt into the new ray tracing extensions only where needed. Where appropriate, ray tracing render delegates may share HGI GPU resources with other delegates, such as HdStorm, to enable efficient mixed operations (e.g., combining ray traced images with raster operations).

## Requirements

Adding ray tracing functionality to HGI requires several new entities in the HGI API:

* **Acceleration Structure**: A representation of the GPU data structure used to efficiently trace rays through a scene.
* **Acceleration Structure Commands**: Similar to existing HGI compute and graphics commands, these commands are submitted to the GPU to build acceleration structures.
* **Ray Tracing Pipeline**: Similar to the existing HGI compute and graphics pipelines, the ray tracing pipeline represents the global state required on the GPU to perform ray tracing.
* **Ray Tracing Commands**: Similar to existing HGI compute and graphics commands, these commands are submitted to the GPU to dispatch ray tracing.

In addition to these new entities, some existing HGI entities will need to be extended to perform ray tracing and related functionality:

* HGI buffer types will be required to represent the various buffers used to build and retain ray tracing acceleration structures.
* HGI shader types will be required to represent the new ray tracing shader stages.

## Out of Scope

While this extension may allow efficient sharing of HGI resources between ray tracing and traditional rasterization render delegates (e.g., HdStorm), the exact mechanism for doing so is beyond the scope of this proposal.

There are no GPU ray tracing extensions for the OpenGL API, which is currently the default HGI backend. For the ray tracing extensions to be useful, the HGI implementation should provide a means to create a ray tracing compatible Vulkan backend in `CreatePlatformDefaultHgi`, or a similar function that returns only a ray tracing compatible backend. The exact mechanism for this is beyond the scope of this proposal.

Also beyond scope is whether, or how, the existing HGI shader generation functionality should be upgraded to support ray tracing shader types. This proposal assumes these shaders will be provided by the render delegate as unprocessed source in the native shader language used by the backend.

## Interface Changes

### Acceleration Structure

The concept of an acceleration structure, a 3D database of scene geometry that can be queried by rays, will be added to HGI via two new classes: `HgiAccelerationStructureGeometry` and `HgiAccelerationStructure`. `HgiAccelerationStructureGeometry` contains the actual geometry that is queried by rays, also known as the bottom-level  acceleration structure (BLAS). `HgiAccelerationStructure` is the whole acceleration structure which can (after being built on the GPU) be queried by rays. This is also known as the top-level acceleration structure (TLAS).

`HgiAccelerationStructureGeometry` can be created via one of two descriptor structures, which define the type of geometry to be created:
* `HgiAccelerationStructureTriangleGeometryDesc` to create a BLAS containing the triangles that make up the geometry to be queried. Positions and indices are contained in the struct as buffers with the `HgiBufferUsageAccelerationStructureBuildInput` usage bit set.
* `HgiAccelerationStructureInstanceGeometryDesc` to create a TLAS containing instances of previously created BLAS objects. Each instance holds a `HgiAccelerationStructureHandle` referencing a BLAS containing the triangles of the instance, along with a transform, visibility mask, and relevant flags.

An `HgiAccelerationStructure` object is created with a vector of `HgiAccelerationStructureGeometry` handles contained in an `HgiAccelerationStructureDesc` struct. The buffer that will contain the acceleration structure is initially empty, and must be built using an `HgiAccelerationStructureCmds` command on the GPU. The command is enqueued and executed on the HGI command queue, as with other HGI command types (e.g., `HgiGraphicsCmds`). `HgiResourceBindings` will also be extended so `HgiAccelerationStructure` resources can be bound alongside buffers, samplers, and other resources.

![Ray tracing acceleration structure](./AccelerationStructure.PNG)

### Ray Tracing

To cast rays that intersect an acceleration structure and produce images, the classes `HgiRayTracingPipeline` and `HgiRayTracingCmds` will be added to HGI. `HgiRayTracingPipeline` contains all the state necessary to render using ray tracing, passed via the `HgiRayTracingPipelineDesc` structure:

* The groups that specify the shaders and resources used for ray tracing a specific instance.
* The resource bindings, a description of the resources (acceleration structures, UBOs, input and output textures, etc.) that will be used for rendering, each with an associated binding index linking resources to a group.
* The shaders used to create rays and shade ray-geometry intersections (hits) and misses.

The pipeline and associated resources themselves must match the layout defined in the pipeline. These are bound, and the actual ray traced rendering occurs, via an `HgiRayTracingCmds` object, enqueued and executed on the HGI command queue as with other HGI command types (e.g., `HgiGraphicsCmds`).

### Buffer Types

New `HgiBufferUsage` buffer types will be added for ray tracing usage modes:

* `HgiBufferUsageAccelerationStructureBuildInput`: Input for an acceleration structure build.
* `HgiBufferUsageAccelerationStructureStorage`: Storage for a built acceleration structure.
* `HgiBufferUsageShaderBindingTable`: Buffer used to store a table binding ray tracing instances to shaders.
* `HgiBufferUsageShaderDeviceAddress`: Flag indicating that the GPU address of the buffer can be retrieved.

### Shader Types

New `HgiShaderStage` shader function types will be added for ray tracing usage modes:

* `HgiShaderStageRayGen`: Ray generation shader that generates the initial (primary) rays for ray tracing.
* `HgiShaderStageAnyHit`: Shader executed for all the intersections along a ray with any geometry.
* `HgiShaderStageClosestHit`: Shader executed for the closest ray-geometry intersection that was not discarded by an any-hit shader.
* `HgiShaderStageMiss`: Shader executed when a ray fails to intersect any geometry.
* `HgiShaderStageIntersection`: Custom intersection shader, for tracing rays against geometry not represented by triangles.
* `HgiShaderStageCallable`: Callable shader that allows arbitrary code execution from another shader.

![Ray tracing shader types](./ShaderStages.PNG)

## Implementation Details

The initial implementation of these ray tracing extensions was based on the `hgiVulkan` backend. We have since added support for the `hgiMetal` backend. The APIs are designed to be compatible with both, and we are open to discussions on how to make them more general and accommodate additional backends.

No OpenGL ray tracing API exists, so the assumption is that these extensions will never work on OpenGL, and will have no effect if called on an OpenGL HGI device. Similarly, they will have no effect on Vulkan or Metal devices that do not support ray tracing, i.e. with GPUs or drivers lacking hardware ray tracing support.

For the ray tracing extensions to work, the Vulkan API version must be 1.2 or higher. The implementation targets this API version and upgrades the Shaderc Vulkan version to 1.2 and the SPIR-V version to 1.5. This upgrade applies only to the new ray tracing shader types; other shader types remain at 1.0 for backward compatibility.

The performance and functionality of existing HGI code will not be affected. Using the ray tracing extensions requires GPUs with hardware ray tracing support, such as NVIDIA RTX series, AMD Radeon RX 6000 (and newer) series, or Apple Silicon GPUs. On devices that do not support ray tracing, the ray tracing interface will not be available; otherwise there are no changes to HGI functionality.

The only change to the existing HGI interface will be a means for a render delegate to select a backend that supports ray tracing in `CreatePlatformDefaultHgi`. The default implementation would continue to return a Vulkan 1.0 or OpenGL backend, as it does now. If the `CreatePlatformDefaultHgi` function is called without any arguments, the result will be an OpenGL HGI instance that does not support ray tracing, exactly as in the current implementation. (Note: this functionality has been implemented in [this branch](https://github.com/autodesk-forks/USD/blob/c7a05671e615d7406bf9bbdc7894f4020ebf0c46/pxr/imaging/hgi/hgi.h#L153) with the `CreateHgiOfChoice` function.)
