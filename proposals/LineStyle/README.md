# Introduction
USD already has primitives to render 3D curve-like geometries, such as hair or grass. In practice, we also need curves in sketch or CAD document. The curve has uniform width, and its width will not change when we rotate or zoom the sketch. The curve may also have dash-dot patterns. We will provide a schema which could be applied to the curves primitive, and the primitive will become a uniform screen-width curve, and can have dash-dot patterns, or other type of patterns（such as waveline).

In this design, we don't consider any 3D-like curve styles, such as Blender's Grease Pencil or Tiltbrush.

Here is a picture of common curve patterns.

![image of curve patterns](linePatterns.jpg)

# Requirements

### Curve Width
The curve width is a screen-space width. It will not change when we zoom in or zoom out. The curve width is uniform across the whole curve.

### Curve Caps
The curve cap is the shape at the start or end of a curve or dash. There are different types of curve cap. The value can be different for the start and the end. But all the start caps in a curve should be the same, and all the end caps should be the same.
The curve cap will also impact the shape of the dot in a curve pattern. The start cap is the shape of the left half of the dot, and the end cap is the shape of the right half of the dot.

| cap type |   round   |  square  |  triangle  |
|:--------:|:---------:|:-----------:|:----------:|
|  figure  |![round](roundcap.png)|![square](rectanglecap.png)|![triangles](triangleoutcap.png)|

### Curve Joint
The curve joint is the shape at the joint of two curves, or at the joint of a polyline. The value is constant for the whole primitive.

![image of curve joint](roundJoint.png)

### Curve Pattern
A dash-dot pattern is a composite of dashes and dots and the composition is periodic. 

You can also define other type of patterns.

# The CurveStyle schema
A new schema called CurveStyle will be added. The schema could be applied to any curve primitives. It inherits from APISchemaBase.

The schema includes these properties:
### patternType
A string uniform, which determines the type of the pattern of the curve. Its value can be "none" or "dashDot". The default value is "none".

No matter what value the patternType is, the curve's width will not change when camera changes. And it can have caps and joint. 

If the value is "none", the curve has no patterns. If the value is "dashDot", the curve has a dash-dot pattern. 
### startCapType
### endCapType
A token uniform. It can be "round", "triangle" or "square". The default value is "round".

### jointType
A token uniform. Currently it can only be "round". 

### patternScale
A float value. Valid when the patternType is not "none". The default value is 1.

You can lengthen or compress the curve pattern by setting this property. For example, if patternScale is set to 2, the length of each dash and each gap will be enlarged by 2 times. This value will not impact on the curve width.
### screenSpacePattern
A bool uniform. Valid when the patternType is not "none". The default value is false. 

If this value is false, the pattern will be based on world unit. So if we zoom in, the pattern on the curve will not change, the dash size and the dash gap size in the screen will also be larger. If the value is true, the pattern will be based on screen unit. If we zoom in, the pattern on the curve will change so that the dash size and the dash gap size in the screen will not change.

![image of screenSpacePattern](screenSpacePattern.png)

### Shader to support the curve style
If the curve is applied with the CurveStyle schema, the curve can not bind to a normal material. Instead, we provide specific surface shader for the curve in the CurveStyle schema.

The CurveStyle must contain a surface shader. If the patternType is "none", it must contain a CurveSketchSurface Shader. If the patternType is "dashDot", it must contain a CurveDashDotSurface Shader and CurveDashDotTexture shader.

In the implementation, we will create material network and link the surface shader in CurveStyle into the shader of the curve primitive. If the curve itself binds to a material, the material will not take effect.

### CurveSketchSurface
The shader will decide the opacity of pixels around caps and joint. The materialTag for this material is translucent.

### CurveDashDotSurface
The shader will decide whether the pixel is within a dash or a gap, so that we can decide its opacity. It will also handle the caps and joint. The materialTag for this material is translucent.

The CurveDashDotSurface must has a color input, which connects to another shader whose shader is "CurveDashDotTexture". The "CurveDashDotTexture" shader links to a texture which saves the information of the dash-dot pattern.

### The curve dash-dot texture
The curve dash-dot texture is a texture that saves a type of dash-dot pattern. It has four channels for each pixel. The first channel saves the period of the dash-dot pattern. The second channel saves the type of the current pixel. The third channel saves the start point of the dash which the current pixel is on. The last channel saves the end point of the dash which the current pixel is on. 

The type of the current pixel can be:

0, the pixel is within the body of a dash.

1, the pixel is between the middle of a gap and the start of a dash (or dot).

2, the pixel is between the end of a dash (or dot) and the middle of a gap.
