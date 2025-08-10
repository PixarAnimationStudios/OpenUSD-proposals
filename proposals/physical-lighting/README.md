# Introduction

Many applications across many different industries need to be able to specify, simulate, and measure the brightness and color of lights in absolute, physical units. 

The updates to the UsdLux documentation in OpenUSD 25.05 clarify the units used in those APIs to be units of photometric luminance, i.e. nit or candela-per-meter-squared. While this clears up current ambiguity in the definition, it intentionally does not add any new parameterization to the lights.

This proposal describes:
1. An API schema for specifying the illuminant spectrum of a light 
2. Several API schema providing user-friendly controls for working in real-world absolute units. 
3. API schema for specifying the responsivity of camera sensors to light

The schema here are relatively lightweight. The majority of the implementation falls on the renderer side, which while not particularly difficult, can be slightly fiddly and nuanced, making it easy for implementations to diverge. The good news is that all of the required functionality could be implemented in Hydra, with renderers just calling `Compute...()` methods to get the necessary factors to multiply in to an existing conforming UsdLux implementation.

## Demo
This demo video walks through a prototype implementation in Omniverse, showing how to use photometric lighting controls to create physically realistic lighting:

https://drive.google.com/file/d/15afllixoq29Fjkltq9gv8sKrc7za_Xn2/view?usp=sharing

# 1. PhysicalLightIlluminantAPI

This schema allows specifying the wavelength-dependent emission spectrum for a lightsource. This is essential for spectral rendering, and for rendering outside of the visual spectrum where notions of color as an RGB value do not apply. For RGB renderers it is essentially a better version of the current "color temperature" controls.

## Schema

```python
class PhysicalLightIlluminantAPI (
    inherits = </APISchemaBase>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["RectLight, SphereLight, DiskLight, CylinderLight", "DomeLight", "DistantLight" ]
    }
)
{
    token physical:illuminant = "white" (
        doc = """The illuminant spectrum of the light in spectral radiance. The default of "white" specifies that the spectrum
                 matches the whitepoint of the rendering color space. "blackbody" specifies a blackbody spectrum of temperature
                 defined by "colorTemperature", and "custom" specifies that the spectrum in "physical:customIlluminant" should
                 be used. "white" and "blackbody" are defined at 5nm intervals over the domain [380nm, 780nm]."""
        allowedTokens = ["white", "blackbody", "custom"]
        displayName = "Illuminant"
    )

    float2[] physical:customIlluminant = [] (
        doc = """An array of (nanometer, radiance) pairs specifying the emission spectrum of the light. The pairs must be ordered
                 such that the wavelength values are monotonically increasing. The wavelengths of the first and last pair in the
                 array define the bounds of the emission range, outside of which emission is zero. The illuminant may be specified
                 at arbitrary intervals, and will be resampled to 5nm intervals according to ASTM-E308."""
        displayName = "Custom illuminant"
    )
}
```

## Implementation

HdLight should provide:

### `HdLight::ComputeIlluminantRGB()` 

Converts the illuminant spectrum to an RGB color in the rendering color space using CIE 1931 Standard Observer. If `PhysicalLightIlluminantAPI` is not applied to the light, then if `enableColorTemperature` is true, it should convert `colorTemperature` to an RGB color according to the [UsdLuxLightAPI documentation](https://openusd.org/dev/api/class_usd_lux_light_a_p_i.html#ad990b3360a3c172c5340ce4e7af463a6). If `enableColorTemperature` is false, then it should return white.

# 2. Photo/Radiometric Light APIs
While this is not strictly necessary for interchange of lighting information (everything ends up as radiance/luminance in the renderer after all), the conversion from units of power or irradiance/illuminance to exitant radiance/luminance on a light source can be subtle and there are many ways for an implementation to diverge.

## Schema

```python
class PhotometricAreaLightAPI (
    inherits = </PhysicalLightIlluminantAPI>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["RectLight", "SphereLight", "DiskLight", "CylinderLight"]
    }
)
{
    float photometric:power = 1600 (
        doc = """Photometric power of the light in lumens."""
        displayName = "Power"
    )
}

class RadiometricAreaLightAPI (
    inherits = </PhysicalLightIlluminantAPI>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["RectLight", "SphereLight", "DiskLight", "CylinderLight"]
    }
)
{
    float radiometric:power = 2.34 (
        doc = """Radiometric power of the light, in Watts, integrated over the domain of the light's illuminant spectrum."""
        displayName = "Power"
    )
}

class PhotometricDomeLightAPI (
    inherits = </PhysicalLightIlluminantAPI>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["DomeLight"]
    }
)
{
    float photometric:illuminance = 10000 (
        doc = """Illuminance, in lux, received by an upward-facing patch from this light."""
        displayName = "Illuminance"
    )
}

class RadiometricDomeLightAPI (
    inherits = </PhysicalLightIlluminantAPI>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["DomeLight"]
    }
)
{
    float radiometric:irradiance = 14.64 (
        doc = """Irradiance, in Watts per meter squared, received by an upward-facing patch from this light, integrated over the domain of the the light's illuminant spectrum."""
        displayName = "Irradiance"
    )
}

class PhotometricDistantLightAPI (
    inherits = </PhysicalLightIlluminantAPI>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["DistantLight"]
    }
)
{
    float photometric:illuminance = 10000 (
        doc = """Illuminance, in lux, received by a patch facing perpendicular to this light."""
        displayName = "Illuminance"
    )
}

class RadiometricDistantLightAPI (
    inherits = </PhysicalLightIlluminantAPI>
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["DistantLight"]
    }
)
{
    float radiometric:irradiance = 14.64 (
        doc = """Irradiance, in Watts per meter squared, received by a patch facing this light, integrated over the domain of the the light's illuminant spectrum."""
        displayName = "Irradiance"
    )
}
```

## Implementation

If both photometric and radiometric schema are applied to a light, the photometric schema takes precedence.

HdLight should provide:

### `HdLight::ComputePowerScaleFactor()`

This should integrate the power emitted by a Rect, Sphere, Cylinder or DiskLight given all the other attributes of the light (intensity, color, texture, shaping etc.) and return the reciprocal of that integrated power such that the user can simply multiply the emitted luminance/radiance by that value in order that the emitted power of the light is exactly that specified by `photometric:power` or `radiometric:power`.

If this method is called on a DomeLight or DistantLight then it should return 1.0.

The renderer should then multiply the exitant radiance/luminance of the lightsource by the user-specified power, $\Phi$ and the power scale factor returned by `ComputePowerScaleFactor()`, $k_\phi$, to obtain the power-adjusted exitant radiance/luminance, $L_e$, which is used in place of $L$:

```math
\begin{align}
L_e &= L \Phi k_\phi \\ \notag
k_\phi &= \frac{1}{L(\lambda) T(\lambda) D(\omega) A} \\ \notag
L &= luminance(\mathtt{inputs:color}) \cdot \mathtt{inputs:intensity} \cdot 2^{\mathtt{inputs:exposure}}
\end{align}
```

$L(\lambda)$ is the luminance integral of the light's illuminant distribution scaled by $L$, the product of the luminance of the light's color, its intensity and exposure. In the photometric case, this is weighted by CIE $\bar{Y}$, while for the radiometric case this is unweighted.

$T(\lambda)$ is the integral of the pixel luminance (defined by the rendering color space) of the texture applied to the light in uv space. If no texture is applied, or the source is point-like, this is 1.

$D(\omega)$ is the integral of the shaping functions (including cone, focus and IES terms) over the sphere of directions around the light's origin

$A$ is the surface area of the light source in meters squared. In the case of a point source, this is 1.

### `HdLight::ComputeIlluminanceScaleFactor()`

This should integrate the illuminance emitted by a Dome or DistantLight given all the other attributes of the light (intensity, color, texture etc.) and return the reciprocal of that integrated illuminance such that the user can simply multiply the emitted luminance/radiance by that value in order that the emitted illuminance of the light is exactly that specified by `photometric:illuminance` or `radiometric:irradiance`.

For a DomeLight, this method computes the illuminance at an upward-facing patch (relative to the stage up-axis). For a distant light it computes the illuminance at a patch facing the light.

If this method is called on a Rect, Sphere, Cylinder or DiskLight then it should return 1.0.

The renderer should then multiply the exitant radiance/luminance of the lightsource by the user-specified illuminance, $E$ and the illuminance scale factor returned by `ComputeIlluminanceScaleFactor()`, $k_E$, to obtain the illuminance-adjusted exitant radiance/luminance, $L_e$, which is used in place of $L$:

```math
\begin{align}
L_e &= L E k_E \\ \notag
k_E &= \frac{1}{L(\lambda) T(\omega, \lambda)} \\ \notag
L &= luminance(\mathtt{inputs:color}) \cdot \mathtt{inputs:intensity} \cdot 2^{\mathtt{inputs:exposure}} \\ \notag
\end{align}
```

$L(\lambda)$ is the luminance integral of the light's illuminant distribution scaled by $L$, the product of the luminance of the light's color, its intensity and exposure. In the photometric case, this is weighted by CIE $\bar{Y}$, while for the radiometric case this is unweighted.

$T(\lambda)$ is the integral of the pixel luminance (defined by the rendering color space) of the texture applied to the light over the upward-facing hemisphere (according to the stage up-axis) in spherical coordinates. If no texture is applied, or the source is point-like, this is 1.

# 3. PhysicalCamera APIs
This consists of two schema: `PhysicalCameraResponsivityAPI` and `PhysicalColorFilterArrayAPI`, which both describe the same concept but with different parameterizations that are suited to different use cases.

Both schema describe the relationship between light incident upon the sensor and the output signal generated by that sensor. 

While this is mostly relevant to spectral renderers, it can still add value to RGB renderers by clearly defining the native color space of a camera.

## `PhysicalCameraResponsivityAPI`

`PhysicalCameraResponsivityAPI` is intended for cameras that are generating RGB images in the camera-native color space and is parameterized by three dimensionless functions, one each for R, G and B, that map between spectral exposure at the sensor and a resulting RGB pixel value in camera-native color space.

This is the model proposed in [Weta's Physlight work](https://github.com/wetadigital/physlight). That repository also contains example responsivity functions for a variety of DSLR cameras. The [rawtoaces repository](https://github.com/AcademySoftwareFoundation/rawtoaces) also has a selection of camera responsivity data.

## `PhysicalColorFilterArrayAPI`

`PhysicalColorFilterArrayAPI` is intended for camera sensors that are generating raw images and is parameterized by up to eight functions, one for each of the color filters in the sensor's matrix, describing the ratio of electrons generated by the sensor for each photon arriving at a given wavelength. The API also specifies the pattern of color filters in the sensor matrix, e.g. "RGGB"

## Schema

```python
class PhysicalCameraResponsivityAPI (
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["Camera"]
    }
)
{
    float2[] physical:responsivity:r = [
        (380, 0.0354000000000),
        # default to e.g. 5D mk II
        (780, 0.0027000000000)
    ] (
        doc = """Responsivity of the camera's red channel to light."""
        displayName = "R"
    )

    float2[] physical:responsivity:g = [
        (380, 0.0359000000000),
        # default to e.g. 5D mk II
        (780, 0.0027000000000)
    ] (
        doc = """Responsivity of the camera's green channel to light."""
        displayName = "G"
    )

    float2[] physical:responsivity:b = [
        (380, 0.0334000000000),
        # default to e.g. 5D mk II
        (780, 0.0027000000000)
    ] (
        doc = """Responsivity of the camera's blue channel to light."""
        displayName = "B"
    )
}

class PhysicalColorFilterArrayAPI (
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["Camera"]
    }
)
{
    string physical:colorFilterArray:pattern = "RGGB" (
        doc = """The pattern of the sensor's CFA. This string dictates which the order and inclusion of the 
        filterN attributes. Specifying less than eight characters means that the missing filter attributes will be ignored.
        For example, specifying 'GG' would mean that only filter1 and filter2 would be used."""
        displayName = "Color Filter Array Pattern"
    )

    float2[] physical:colorFilterArray:filter1 = [
        # some sensible default
    ] (
        doc = """Responsivity of the camera's first filter to light."""
        displayName = "Filter 1"
    )

    float2[] physical:colorFilterArray:filter2 = [
        # some sensible default
    ] (
        doc = """Responsivity of the camera's second filter to light."""
        displayName = "Filter 2"
    )

    float2[] physical:colorFilterArray:filter3 = [
        # some sensible default
    ] (
        doc = """Responsivity of the camera's third filter to light."""
        displayName = "Filter 3"
    )

    float2[] physical:colorFilterArray:filter4 = [
        # some sensible default
    ] (
        doc = """Responsivity of the camera's fourth filter to light."""
        displayName = "Filter 4"
    )

    float2[] physical:colorFilterArray:filter5 = [] (
        doc = """Responsivity of the camera's fifth filter to light."""
        displayName = "Filter 5"
    )

    float2[] physical:colorFilterArray:filter6 = [] (
        doc = """Responsivity of the camera's sixth filter to light."""
        displayName = "Filter 6"
    )

    float2[] physical:colorFilterArray:filter7 = [] (
        doc = """Responsivity of the camera's seventh filter to light."""
        displayName = "Filter 7"
    )

    float2[] physical:colorFilterArray:filter8 = [] (
        doc = """Responsivity of the camera's eighth filter to light."""
        displayName = "Filter 8"
    )

}

```

### Alternative PhysicalColorFilterArrayAPI

An alternative formulation for the CFA schema is to represent the filter QE curves as a 2D array of values, rather than (up to) eight separate filter arrays. This has the advantage of being extendable if we ever need more than eight filters (such sensors exist but are not common in practical usage) and avoiding having extra, unused attributes.

```python

class PhysicalColorFilterArrayAPI (
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["Camera"]
    }
)
{
    string physical:colorFilterArray:pattern = "RGGB" (
        doc = """The pattern of the sensor's CFA. This string dictates the order and size of the filters attribute.
        For example, specifying 'GG' would mean that filters must be a 2 * len(wavelengths) size array."""
        displayName = "Color Filter Array Pattern"
    )

    float[] physical:colorFilterArray:wavelengths = [
        380.0,
        # ...
        780.0
    ] (
        doc = """Wavelengths corresponding to each 'row" of entries in the filters array."""
        displayName = "Filter 1"
    )

    float[] physical:colorFilterArray:filters = [
        # some sensible default
    ] (
        doc = """Responsitivity of the camera's filters to light. This is an NxM 2-dimensional array of values flattened to a 1-d array, where the fastest-changing index is the index of the filter in the pattern specified by `physical:colorFilterArray:pattern`, and the slowest-changing index is the wavelength. Thus the array is M filters by N wavelengths, where M is the length of the filter pattern string and N is the length of the `physical:colorFilterArray:wavelengths` array."""
        displayName = "Filters"
    )
}

```

## Implementation

HdCamera should provide:

### `HdCamera::ComputeCameraToXYZMatrix()`
Returns the 3x3 matrix that transforms from camera-native RGB to CIE XYZ.
