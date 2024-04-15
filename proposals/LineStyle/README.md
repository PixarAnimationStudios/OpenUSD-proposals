# Introduction
USD already has primitives to render 3D curve-like geometries, such as hair or grass. In practice, we also need curves in sketch or CAD document. The curve has uniform width, and its width will not change when we rotate or zoom the sketch. The curve may also have dash-dot patterns. We will provide a schema which is for patterned lines or polylines. The primitive will have uniform screen-width, and can have dash-dot patterns.

Here is a picture of common dash dot patterns.

![image of curve patterns](linePatterns.jpg)

# Requirements

### Line Width
The line width is a screen-space width. It will not change when we zoom in or zoom out. The line width is uniform across the whole line.

### Line Caps
The line cap is the shape at the start or end of a line or dash. There are different types of line cap. The value can be different for the start and the end. But all the start caps in a line should be the same, and all the end caps should be the same.
The line cap will also impact the shape of the dot in a dash-dot pattern. The start cap is the shape of the left half of the dot, and the end cap is the shape of the right half of the dot.

| cap type |   round   |  square  |  triangle  |
|:--------:|:---------:|:-----------:|:----------:|
|  figure  |![round](roundcap.png)|![square](rectanglecap.png)|![triangles](triangleoutcap.png)|

### Line Joint
The line joint is the shape at the joint of two lines, or at the joint of a polyline. The value is constant for the whole primitive.

![image of line joint](roundJoint.png)

### Dash-dot Pattern
A dash-dot pattern is a composite of dashes and dots and the composition is periodic. 

You can also define other type of patterns.

# The implementation of DashDot line style
Our implementation will introduce a new type of primitive, the DashDotLines. It inherits from Curves. The primitive is a list of line segments or polylines. The width of the line will be uniform, and it will not change when camera changes. There can be no pattern in the line. Or there can be dash-dot pattern.

We also add a new rprim for the DashDotLines. We add a new shader file, the dashDotLines.glslfx, which includes both vertex and fragment shader. We also need two different materials: one is for a line with no pattern, and another is for a line with dash-dot pattern.

In the implementation, we also create special geometry for the primitive. Each line segment is converted to a rectangle which is composed from two triangles. 

### The DashDotLines schema
A new primitive DashDotLines is added, which inherits from Curves. It inherits properties from Curves.
The shape of this primitive on the screen is a uniform-width line or polyline. Its width will not change when camera changes. It has either no pattern or dash-dot pattern.

The DashDotLines primitive must bind to a specific material. If the material contains a texture of the dash-dot pattern, the primitive will have dash-dot pattern. Or else, the primitive will have no pattern. The property of the style, such as the cap shape or the scale of the dash dot pattern, will also be set in the material via the surface input.

These are properties which inherited from Curves:
- curveVertexCounts
- widths. Widths are now interpreted as the widths in screen space.

The DashDotLines has the following new properties:
- screenSpacePattern. A bool uniform. By default it is true, which means the dash-dot pattern will be based on screen unit. If we zoom in, the pattern on the line will change in the world space, so that the dash size and the dash gap size in the screen space will not change. If it is false, the pattern will be based on world unit. If we zoom in, the pattern on the line will not change in world space. The dash size and the dash gap size in the screen space will be larger. 

![image of screenSpacePattern](screenSpacePattern.png)

### Extents of the DashDotLines
Different from the other Curves, the extents of the DashDotLines is only the bound box of the control points. The width of the line will not be considered, because it is screen spaced, that it is implemented via the shader.

### The DashDotLines rprim and shader
In HdStorm, we will add the HdDashDotLines rprim for the DashDotLines primitive. The topology of the DashDotLines requires the curveVertexCounts, curveIndices and whether the pattern is screenSpaced. In dashDotLines.glslfx, we add two sections of shader code: "DashDot.Vertex" and "DashDot.Fragment".

### Other inputs for the shader and screen space pattern implementation
For a polyline, the shader need to know the sum of line lengths before each vertex. This value can be pre-calculated in CPU. To implement screen space dash-dot pattern, the sum must be based on line lengths on the screen. So to calculate the sum, we need to do matrix transformation for the lines in CPU, and this calculation must be done when camera is changed. (Maybe we can use the compute shader to do the calculation before the rendering process in each frame)

### Material to support the dash dot style
There are two different materials specially for the DashDotLines primitive, which corresponding to two different surface shaders. The LineSketchSurface shader doesn't have a color input. If the material contains LineSketchSurface shader, the line will not have patterns. The DashDotSurface shader has a color input which linked to a texture shader, and the texture shader will contain the dash-dot pattern texture. If the material contains DashDotSurface shader, the line will have dash-dot patterns.

### LineSketchSurface
The shader will decide the opacity of pixels around caps and joint. The materialTag for this material is translucent.

This surface also has these special input:
- startCapType. An int input. It can be 0, 1, or 2. 0 means the cap type is round. 1 means the cap type is square. 2 means the cap type is triangle. The default value is 0.
- endCapType. An int input. It can be 0, 1, or 2. 0 means the cap type is round. 1 means the cap type is square. 2 means the cap type is triangle. The default value is 0.
- jointType. An int input. Currently it can only be 0, which means the joint type is round.

### DashDotSurface
The shader will decide whether the pixel is within a dash or a gap, so that we can decide its opacity. It will also handle the caps and joint. The materialTag for this material is translucent.

The DashDotSurface must has a color input, which connects to another shader whose shader is DashDotTexture. The DashDotTexture shader links to a texture which saves the information of the dash-dot pattern.

This surface also has these special input:
- startCapType. An int input. It can be 0, 1, or 2. 0 means the cap type is round. 1 means the cap type is square. 2 means the cap type is triangle. The default value is 0.
- endCapType. An int input. It can be 0, 1, or 2. 0 means the cap type is round. 1 means the cap type is square. 2 means the cap type is triangle. The default value is 0.
- jointType. An int input. Currently it can only be 0, which means the joint type is round.
- patternScale. A float input. The default value is 1. You can lengthen or compress the line pattern by setting this property. For example, if patternScale is set to 2, the length of each dash and each gap will be enlarged by 2 times. This value will not impact on the line width.

### DashDotTexture
The DashDotTexture shader is quite the same as UVTexture shader. The difference is that it outputs rgba value. The default value for wrap is clamp, and the default value for min/max filter is "nearest". The shader must have a dash-dot texture input.

### The dash-dot texture
The dash-dot texture is a texture that saves a type of dash-dot pattern. In the four channels we will save if the pixel is within a dash or a gap, and the start and end position of the current dash.

# Examples
### 2 DashDotLines primitives with dash-dot patterns
```
def DashDotLines "StyledPolyline1" (
    prepend apiSchemas = ["MaterialBindingAPI"]
){
    uniform token[] xformOpOrder = ["xformOp:translate"]
    float3 xformOp:translate = (0, 0, 0)

    bool screenSpacePattern = true
    rel material:binding = </LineMat1>
    int[] curveVertexCounts = [3, 4]
    point3f[] points = [(0, 0, 0), (10, 10, 0), (10, 20, 0), (0, 30, 0), (-10, 40, 0), (-10, 50, 0), (0, 60, 0)]
    float[] widths = [5] (interpolation = "constant")
    color3f[] primvars:displayColor = [(1, 0, 0)]
}
def DashDotLines "StyledPolyline2" (
    prepend apiSchemas = ["MaterialBindingAPI"]
){
    uniform token[] xformOpOrder = ["xformOp:translate"]
    float3 xformOp:translate = (20, 0, 0)

    bool screenSpacePattern = true
    rel material:binding = </LineMat2>
    int[] curveVertexCounts = [3, 4]
    point3f[] points = [(0, 0, 0), (10, 10, 0), (10, 20, 0), (0, 30, 0), (-10, 40, 0), (-10, 50, 0), (0, 60, 0)]
    float[] widths = [10] (interpolation = "constant")
    color3f[] primvars:displayColor = [(0, 0, 1)]
}

def Shader "PatternTexture"
{
    uniform token info:id = "DashDotTexture"
    asset inputs:file = @DashDot.tif@
    float4 outputs:rgba
}

def Shader "LineShader1"
{
    uniform token info:id = "DashDotSurface"
    color4f inputs:diffuseColor.connect = </PatternTexture.outputs:rgba>
    int inputs:startCapType = 0
    int inputs:endCapType = 0
    float inputs:patternScale = 5
    token outputs:surface
}

def Shader "LineShader2"
{
    uniform token info:id = "DashDotSurface"
    color4f inputs:diffuseColor.connect = </PatternTexture.outputs:rgba>
    int inputs:startCapType = 2
    int inputs:endCapType = 2
    float inputs:patternScale = 11
    token outputs:surface
}

def Material "LineMat1"
{
    token outputs:surface.connect = </LineShader1.outputs:surface>
}

def Material "LineMat2"
{
    token outputs:surface.connect = </LineShader2.outputs:surface>
}
```
In this example, there are two DashDotLines primitives. They all have dash-dot patterns, and the pattern is defined in the DashDot.tif texture. 

The first primitive has two polylines. One polyline has 3 vertices and another has 4 vertices. The line width on screen is 5. The startCapType and endCapType are both round. The patternScale is 5 which means the dashes and gaps will be lengthened by 5 times. 

The second primitive has two polylines. One polyline has 3 vertices and another has 4 vertices. The line width on screen is 10. The startCapType and endCapType are both triangle. The patternScale is 11 which means the dashes and gaps will be lengthened by 11 times.

The image for the 2 DashDotLines primitives.

![image of Dashdotlines primitives](twoPolylines.png)

### A polyline with no pattern
```
def DashDotLines "StyledPolyline" (
){
    rel material:binding = </LineMat>
    int[] curveVertexCounts = [3]
    point3f[] points = [(0, 0, 0), (10, 10, 0), (10, 20, 0)]
    float[] widths = [5] (interpolation = "constant")
    color3f[] primvars:displayColor = [(1, 0, 0)]
}
def Material "LineMat"
{
    token outputs:surface.connect = </LineMat/LineShader.outputs:surface>

    def Shader "LineShader"
    {
        uniform token info:id = "LineSketchSurface"
        token outputs:surface
        int inputs:startCapType = 0
        int inputs:endCapType = 0
    }
}
```
In this example, there is one polyline. It has 3 vertices. The line width on screen is 5. The polyline doesn't have pattern. The startCapType and endCapType are both round.

The image for the DashDotLines primitive.

![image of Dashdotlines primitive](onePolyline.png)