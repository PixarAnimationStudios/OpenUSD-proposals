# Introduction

Many applications across many different industries need to be able to specify, simulate, and measure the brightness and colour of lights in absolute, physical units. 

The in-progress updates to the UsdLux documentation clarify the units used in those APIs to be units of photometric luminance, i.e. nit or candela-per-meter-squared. While this clears up current abiguity in the definition, it intentionally does not add any new parameterization to the lights.

This proposal describes:
1. An API schema for specifying the illuminant spectrum of a light 
2. Several API schema providing user-friendly controls for working in real-world absolute units. 

(1) is essential for spectral rendering, and for rendering outside of the visual spectrum where notions of "colour" as an RGB value do not apply.

While (2) is not strictly necessary for interchange of lighting information (everything ends up as radiance/luminance in the renderer after all), the conversion from units of power or irradiance/illuminance to exitant radiance/luminance on a light source can be subtle and there are many ways for an implementation to diverge. 

We propose implementing these conversions directly in OpenUSD itself, such that a renderer only has to call a `calculateRadiance()` or `calculateRgbLuminance()` method on a light to get the correctly converted values, taking into account all aspects of the light including dimensions, textures, and shaping functions. Renderers that want to do their own implementations (for example to run them on the GPU) can use the OpenUSD calculations as a reference to ensure a consistent implementation.

# Schema
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