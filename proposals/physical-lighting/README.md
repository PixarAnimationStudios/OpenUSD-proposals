# Introduction

Many applications across many different industries need to be able to specify, simulate, and measure the brightness and colour of lights in absolute, physical units. 

The updates to the UsdLux documentation in OpenUSD 25.05 clarify the units used in those APIs to be units of photometric luminance, i.e. nit or candela-per-meter-squared. While this clears up current abiguity in the definition, it intentionally does not add any new parameterization to the lights.

This proposal describes:
1. An API schema for specifying the illuminant spectrum of a light 
2. Several API schema providing user-friendly controls for working in real-world absolute units. 
3. API schema for specifying the responsivity of camera sensors to light

The schema here are relatively lightweight. The majority of the implementation falls on the renderer side, which while not particularly difficult, can be slightly fiddly and nuanced, making it easy for implementations to diverge. The good news is that all of the required functionality could be implemented in Hydra, with renderers just calling `Compute...()` methods to get the necessary factors to multiply in to an existing conforming UsdLux implementation.

# 1. PhysicalLightIlluminantAPI

This schema allows specifying the wavelength-dependent emission spectrum for a lightsource. This is essential for spectral rendering, and for rendering outside of the visual spectrum where notions of colour as an RGB value do not apply. For RGB renderers it is essentially a better version of the current "color temperature" controls.

## Schema

> [!IMPORTANT]
> Specify the interpolation method to use
> Specify the range of the visual spectrum

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
        doc = """The illuminant spectrum of the light in spectral radiance. The default of "white" specifies that the spectrum matches the whitepoint of the rendering colour space. "blackbody" specifies a blackbody spectrum of temperature defined by "colorTemperature", and "custom" specifies that the spectrum in "physical:customIlluminant" should be used.
        "white" and "blackbody" are defined over the domain [380nm, 780nm]."""
        allowedTokens = ["white", "blackbody", "custom"]
        displayName = "Illuminant"
    )

    float2[] physical:customIlluminant = [] (
        doc = """An array of (nanometer, radiance) pairs specifying the emission spectrum of the light. The pairs must be ordered such that the wavelength values are monotonically increasing. The wavelengths of the first and last pair in the array define the bounds of the emission range, outside of which emission is zero."""
        displayName = "Custom illuminant"
    )
}
```

## Implementation

HdLight should provide:

### `HdLight::ComputeIlluminantRGB()` 

Converts the illuminant spectrum to an RGB colour in the rendering colour space. If `PhysicalLightIlluminantAPI` is not applied to the light, then if `enableColorTemperature` is true, it should convert `colorTemperature` to an RGB colour according to the [UsdLuxLightAPI documentation](https://openusd.org/dev/api/class_usd_lux_light_a_p_i.html#ad990b3360a3c172c5340ce4e7af463a6). If `enableColorTemperature` is false, then it should return white.

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
        doc = """Photometric power of the light in lumen."""
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
        doc = """Radiometric power of the light, in Watt, integrated over the domain of the light's illuminant spectrum."""
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
        doc = """Irradiance, in Watt per meter squared, received by an upward-facing patch from this light, integrated over the domain of the the light's illuminant spectrum."""
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
        doc = """Irradiance, in Watt per meter squared, received by a patch facing this light, integrated over the domain of the the light's illuminant spectrum."""
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

> [!IMPORTANT]
> Formulae

### `HdLight::ComputeIlluminanceScaleFactor()`

This should integrate the illuminance emitted by a Dome or DistantLight given all the other attributes of the light (intensity, color, texture, shaping etc.) and return the reciprocal of that integrated illuminance such that the user can simply multiply the emitted luminance/radiance by that value in order that the emitted illuminance of the light is exactly that specified by `photometric:illuminance` or `radiometric:illuminance`.

For a DomeLight, this method computes the illuminance at an upward-facing patch (relative to the stage up-axis). For a distant light it computes the illuminance at a patch facing the light.

If this method is called on a Rect, Sphere, Cylinder or DiskLight then it should return 1.0.

> [!IMPORTANT]
> Formulae


# 3. PhysicalCamera APIs
This consists of two schema: `PhysicalCameraResponsivityAPI` and `PhysicalColorFilterArrayAPI`, which both describe the same concept but with different parameterizations that are suited to different use cases.

Both schema describe the relationship between light incident upon the sensor and the output signal generated by that sensor. 

While this is mostly relevant to spectral renderers, it can still add value to RGB renderers by clearly defining the native color space of a camera.

## `PhysicalCameraResponsivityAPI`

`PhysicalCameraResponsivityAPI` is intended for cameras that are generating RGB images in the camera-native colour space and is parameterized by three dimensionless functions, one each for R, G and B, that map between spectral exposure at the sensor and a resulting RGB pixel value in camera-native colour space.

This is the model proposed in [Weta's Physlight work](https://github.com/wetadigital/physlight). That repository also contains example responsivity functions for a variety of DSLR cameras. The [rawtoaces repository](https://github.com/AcademySoftwareFoundation/rawtoaces) also has a selection of camera responsivity data.

## `PhysicalColorFilterArrayAPI`

`PhysicalColorFilterArrayAPI` is intended for camera sensors that are generating raw images and is parameterized by four functions, one for each of the four colour filters in the sensor's matrix, describing the ratio of electrons generated by the sensor for each photon arriving at a given wavelength. The API also specifies the pattern of colour filters in the sensor matrix, e.g. "RGGB"

> [!IMPORTANT]
> How do we specify an arbitrary number of curves here?

## Schema

> [!IMPORTANT]
> Specify the interpolation method to use
> Specify the range of the visual spectrum

```python
class PhysicalCameraResponsivityAPI (
    customData = {
        token apiSchemaType = "singleApply"
        token[] apiSchemaCanOnlyApplyTo = ["Camera"]
    }
)
{
    float2[] physical:responsivity:r = [(380, 1), (780, 1)] (
        doc = """Responsivity of the camera's red channel to light."""
        displayName = "R"
    )

    float2[] physical:responsivity:g = [(380, 1), (780, 1)] (
        doc = """Responsivity of the camera's green channel to light."""
        displayName = "G"
    )

    float2[] physical:responsivity:b = [(380, 1), (780, 1)] (
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
        doc = """The pattern of the sensor's CFA. This four-character string dictates which the order and inclusion of the 
        filterN attributes. Specifying less than four characters means that the missing filter attributes will be ignored.
        For example, specifying 'GG' would mean that only filter1 and filter2 would be used."""
        displayName = "Color Filter Array Pattern"
    )

    float2[] physical:colorFilterArray:filter1 = [(380, 1), (780, 1)] (
        doc = """Responsivity of the camera's first filter to light."""
        displayName = "Filter 1"
    )

    float2[] physical:colorFilterArray:filter2 = [(380, 1), (780, 1)] (
        doc = """Responsivity of the camera's second filter to light."""
        displayName = "Filter 2"
    )

    float2[] physical:colorFilterArray:filter3 = [(380, 1), (780, 1)] (
        doc = """Responsivity of the camera's third filter to light."""
        displayName = "Filter 3"
    )

    float2[] physical:colorFilterArray:filter4 = [(380, 1), (780, 1)] (
        doc = """Responsivity of the camera's fourth filter to light."""
        displayName = "Filter 4"
    )

}

```

## Implementation

HdCamera should provide:

### `HdCamera::ComputeCameraToXYZMatrix()`
Returns the 3x3 matrix that transforms from camera-native RGB to CIE XYZ.