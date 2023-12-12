
![Status:Draft](https://img.shields.io/badge/Draft-blue)
## Physical Cameras for USD

## Contents
- [Introduction](#introduction)
- [Use Cases](#use-cases)
- [Relationship to Image Plane proposal](#Relationship-to-Image-Plane-Proposal)
- [Schema](#Proposed-PhysicalCamera-schema)

## Introduction

This schema usefully bridges the description of physical cameras to USD scenes.

@TODO PBRT has complex lens model, see RealisticCamera. Consider it for
adoption here, perhaps as a secondary structure in Optics, or as a subclass.

https://github.com/mmp/pbrt-v4/blob/master/src/pbrt/cameras.h

PBRT defines Orthographic, Perspective, Spherical, and Realistic cameras.

@TODO introduce at least Orthographic, in addtion to the present model
which would be Perspective.

## Use Cases

### Interesting Looking Models

The fx company has got a set of lenses in its
library. These lenses are described by individual USD files that can be
layered into a USD scene that records details of a shoot using those lenses.

The camera and rig are composed of classes in this schema and are custom for
every shot, but the lenses are reused between shots. Every morning the lenses
are characterized, and if new values are recorded, they are added to the
individual lens files as variants, and the current variant is set to latest.

Before shots are archived, the variant in use is set appropriately, although
during the shoot, the lens variant will typically be set to "current".

### Likeable Puppets

The stop motion animation company has got a large collection of camera bodies
and lenses. These bodies and lenses travel around and are mixed and matched
all day long during shoots on multiple sets, and when images are recorded,
the combination for any given shot is constructed via layering those cameras
and bodies, and associated with the image plane data, so that the plates and
unique camera set ups always travel together.

### Bellam Blvd Previs

The previs company has got a camera kit they use in all their work. This kit
consists of a single USD file with 8 variants, including Doll House, Over The
Shoulder, and Out in the Desert. These variants are selected on a shot by shot
basis, and characteristics of the individual lenses and bodies are overridden
as needed.

### Beloved Lens Co

The Beloved Lens Co has sent us a box with it's latest offerings, Darling 16,
Darling 24, a Gamin 8, and a Super Snoot 300. They've also kindly supplied USD
files for these lenses, complete with both a custom lens model that properly
describes the unique characteristics of their lenses, and also a best match
PhysicalCameraLensModelPinhole for use in realtime previs scouting.

### Smart Stage Studios

insert LED wall scenario here

### Streaming Behemoth

Insert streamed camera metadata scenario here

## Relationship to Image Plane proposal

These should be complementary, and any information related to elements
in this proposal, should be migrated to this proposal. Otherwise, the Image
Plane proposal specifically describes the mapping of a capture image to an
image plane, and the Physical Camera schema describes the mapping of objects
in a scene to the image plane. So that's the pivot between them.

## Proposed PHysicalCamera schema

```
class PhysicalCamera "PhysicalCamera" (
    doc = """Physically modeled camera.

    The physical camera is a primitive meant to be a target for construction of
    a physical camera model through applied, and multiply applied schemas.

    The physical camera is a GeomXformable, and thus inherits the transform
    schema.  The physical camera also inherits the UsdGeomImageable schema,
    which provides facilities for controlling visibility and rendering of the
    camera.

    The physical camera provides a number of attributes that are meant to be
    authored by a user or by a DCC import process.  These attributes are
    generally meant to be authored once, and then left alone.

    The concept is that the PhysicalCamera is just like a real camera that may
    be used and measure on a real life stage, and it's attributes recorded in
    a usd file. A real camera is a body, with a lens, and a film back, all
    interchangeable.

    This base schema then, describes the body, which is little more than a
    transform, and is otherwise a target for a collection of film backs, and
    lenses, which are themselves schemas that are applied to the PhysicalCamera.

    In addition to transform properties, the base camera includes attributes 
    describing the aperture at the front of the body. The camera body currently 
    models the aperture and shutter as a non-interchangeable component.

    The aperture describes both the shape of the pupil of the aperture and also 
    the shutter, and the distance of the physical aperture from the film back.

    Currently the shape of the aperture is modeled as a straight sided polygon.
    In the future, an arbitrary mask could be specified to use in convolution
    or raytracing.

    shutter angle is the shutter duration * frame rate * 360 degrees, and not
    computed here.

    float          flange_distance;   // distance from film back to lens flange, mm
    float          shutter_open;      // offset in seconds from start of exposure
    float          shutter_duration;  // duration of exposure, in seconds

     """
)
{
    float        flange_distance = 52.0 (
        doc = '''distance from film back to lens flange, in mm'''
    )
    float         shutter_open = 0.0 (
        doc = '''offset in seconds from start of exposure'''
    )
    float         shutter_duration = 0.02 (
        doc = '''duration of exposure, in seconds, the default is 1/50th of 
                 a second'''
    )
    float iris = 6.25 (
        doc = '''the default aperture is 6.25mm, corresponding to f8 for a 
                 50mm lens'''
    )
}

class PhysicalCameraSensor "PhysicalCameraSensor" (
    doc="""
    The PhysicalCameraSensor schema describes the film back of the camera.  The
    film back is the sensor that is exposed to light, and is the primary
    determinant of the field of view of the camera, by describing the geometry 
    of the plane where an image is to be resolved.

    Since a camera may have multiple film backs, the PhysicalCameraSensor is
    a multi-apply schema, and may be applied multiple times to a PhysicalCamera.

    The sensor's coordinate system has its center at (0, 0) and its bounds 
    are -1 to 1.
    The enlarge property is a multiplicative value; and shift is an additive 
    value in the sensor's coordinate system.

    Shift and enlarge can be used to create projection matrices for
    subregions of an image. For example, if the default sensor is to be
    rendered as four tiles, a matrix for rendering the upper left quadrant
    can be computed by setting enlarge to { 2, 2 }, and
    shift to millimeters{-17.5f}, millimeters{-12.25f}.

    The default sensor aperture is as for 35mm DSLR.

    A handedness of -1 indicates a left handed camera.

    The PhysicalCameraSensor does describe the electrical or 
    photochemical characteristics of a sensor, it's geometric.
    The electrical or photochemical characteristics are to be described
    either here or in another class within this schema.

    float2 shift; // in millimeters
    float2 enlarge; // multiplicative
    float2 aperture; // in millimeters
    float handedness; // -1 for left handed, 1 for right handed
    """
)
{
    float2 shift = (0.0, 0.0) (
        doc = '''shift in millimeters'''
    )
    float2 enlarge = (1.0, 1.0) (
        doc = '''enlarge multiplicative'''
    )
    float2 aperture = (36.0, 24.0) (
        doc = '''aperture in millimeters'''
    )
    float handedness = 1.0 (
        doc = '''-1 for left handed, 1 for right handed'''
    )
}

class PhysicalCameraLens "PhysicalCameraLens" (
    doc="""
    The PhysicalCameraLens schema describes the lens of the camera.  The lens
    is the optical system that focuses light onto the film back.

    Since a camera may have multiple lenses, the PhysicalCameraLens is
    a multi-apply schema, and may be applied multiple times to a PhysicalCamera.

    Fundamentally, the lens is a mapping from a point in space to a point on
    the film back, with an associated transmittance value, and so the 
    PhysicalCameraLens provides some common measurements, but it's expected that 
    the explicit modeling will occur in a prim referenced from the PhysicalCameraLens.

    float          aperture_distance; // distance from image plane to aperture, mm
    unsigned int   shutter_blades;    // default 7

    """
)
{
    rel lensModelPrim (
        doc = '''The lens model prim'''
    )
    float iris = 6.25 (
        doc = '''The default iris corresponds to f8 for a 50mm lens'''
    )
    float aperture_distance = 50.0 (
        doc = '''distance from image plane to aperture, mm'''
    )
    unsigned int shutter_blades = 7 (
        doc = '''default 7'''
    )
    float fstop = 8.0 (
        doc = '''fstop'''
    )
    float2 clippingRange = (1, 1000000) (
        doc = '''Near and far clipping distances in scene units'''
    )
}

class PhysicalCameraLensModelPinhole "PhysicalCameraLensModelPinhole" (
    doc="""
    The PhysicalCameraLensModelPinhole schema describes a pinhole lens, and is A
    sample schema that may be refered to via the lensModelPrim relationship.

    A and B are on the sensor plane.

    There is a point at infinity, O, on the axis of the lens, whose parallel
    rays converge on B.
                                    a
        ---------------------------+---------------+ A
                                 b| |              |
        O--------------------------+---------------+ B
                                 c| |              |
        ---------------------------+---------------+
        infinity                 lens           sensor plane
        C

    h = A-B is half the sensor plane aperture.
    f = b-B is the focal length

    There is a point C at infinity, whose parallel rays through a, b, and c,
    converge on the edge of the sensor plane, at A.

    The field of view of the lens, at infinity, can therefore be approximated by

        fov = 2 atan((h/2) / f)

    Given a field of view, the assumption of a focus at infinity, and a sensor
    aperture, the focal length may be calculated accordingly:

        f = tan(fov/2) / (h/2)

    an anamorphic lens' horizontal field of view must take squeeze into account:

        fov = 2 atan((s * h/2) / f)

    The hyperfocal distance is useful for determining what ranges are in focus.

    If a camera is focused at infinity, objects from the hyperfocal distance to
    infinity are in focus.

    O----------------H----------------------------|
    Infinity       hyperfocal distance         Sensor plane

    If a camera is focussed at the hyperfocal distance, then objects
    from 1/2 H to infinity are in focus.

    O----------------H----------H/2---------------|
    Infinity       hyperfocal distance         Sensor plane

    Given a focus distance, and the hyperfocal distance, the in focus range is
    given by

        Dn = hd / (h + (d - f))
        Df = hd / (h - (d - f))

    Given a circle of confusion, such as 0.002mm as might be typical for
    35mm film, the hyperfocal distance can be determined.

        h = f^2/(fstop * CoC)

    Note that this struct does not model lens imperfections such as focus
    breathing, vignetting, distortion, flaring, spherical aberration or 
    chromatic aberration. Nor does it model field curvature or diffraction.
    """
)
{
    float focal_length = 50.0 (
        doc = '''focal length in millimeters'''
    )
    float focus_distance = 1000.0 (
        doc = '''focus distance in millimeters'''
    )
    float transmittance = 1.0 (
        doc = '''transmittance'''
    )
    float squeeze = 1.0 (
        doc = '''squeeze'''
    )
}
```
