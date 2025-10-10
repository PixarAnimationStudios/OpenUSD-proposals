
# Spline Animation in USD

This project aims to support spline animation on floating-point scalar USD
attributes.  The project is called **USD Anim** for short.

Spline animation means that time-varying attribute values are specified using
sparse _knots_, from which values can be _interpolated_ or _extrapolated_ at any
time coordinate.  The knots of an attribute form a _spline_, which is a function
mapping times to values.  A spline is a familiar concept in digital animation;
it is an artist-friendly mathematical representation of a value changing over
time, usually continuously.  USD already has _time samples_, which are discrete
time-varying values, interpolated linearly in the case of floating-point
scalars; splines will complement time samples and support additional uses.

## Purposes

We believe spline animation is a general-purpose tool, and we expect its usage
to exceed what we can imagine ahead of time.  But we have some specific
motivations:

**Animation interchange.** It is frequently useful to employ multiple
applications in the course of creating, editing, viewing, and consuming scene
data.  This is a basic premise of USD, which is an interchangeable system of 3D
scene description.  Since many 3D applications represent varying values with
splines, it is a natural step to add splines to USD's vocabulary.

**Gaming pipelines.** Game engines can work with spline data, and many are
already compatible with USD for geometry transfer.  Controlling animation using
splines offers runtime flexibility, aids in fetching animation data back into
authoring tools, and reduces bandwidth requirements.  This is applicable to
linear-blend skinning animation using UsdSkel, but also more generally to any
animation runtime.  A particular interest for gaming applications is fast,
iteration-free runtime evaluation of splines, which USD Anim is intended to
support.

**OpenExec.** Pixar is beginning the process of open-sourcing its fast, powerful
attribute computation engine, called OpenExec.  Spline data is a natural way to
drive OpenExec rigging, and we see it as a prerequisite for OpenExec.

## Splines Versus Time Samples

Splines and time samples will coexist in USD.  Time-varying data for
floating-point scalars may be authored in either form; if both are present on
the same attribute, time samples will take precedence.  The tradeoffs are:

|                   | Splines                     | Time Samples          |
| ----------------- | --------------------------- | --------------------- |
| **Data format**   | Curves defined by knots     | Lookup tables         |
| **Data density**  | Sparse                      | Dense                 |
| **Purpose**       | Source format               | Computed values       |
| **Lookup speed**  | Full fetch, do some math    | Highly optimized read |
| **Interpolation** | Flexible, typically Beziers | Linear                |

## High-Level Requirements

USD Anim will aim to achieve all of the following:

- **Interchange-suitable:** a universal format.

    - USD Anim splines will support a variety of features, detailed in
      subsequent sections.  All clients will be able to read all valid USD Anim
      splines, given a minimum level of feature support.  USD Anim will provide
      a set of utilities to perform _reduction_, in which splines that use
      features outside the client's feature set can be converted to splines
      within the client's feature set, using emulations.  For example, if
      clients support only Bezier segments, held and linear segments can be
      emulated using Bezier segments.

    - USD Anim will not be designed to accommodate extensions.  If the community
      discovers missing features, we would prefer to either consider their
      inclusion directly in the USD Anim core, or assist with the design of a
      layered architecture that relegates features to higher levels.

    - USD Anim will not include any arbitrary tuning parameters.  All behavior
      will be mathematically justified, and all curve parameters will be
      controllable.

- **Majority Maya compatibility:** a familiar format.

    - Most Maya animation splines will be representable in USD with minimal
      translation.  In particular, USD Anim will support most Maya spline
      features.

    - However, USD Anim will be a product-agnostic format, and will differ from
      Maya in some ways, including API, serialization format, and mathematical
      representation.

- **Majority Presto compatibility:** a pragmatic format for Pixar.

    - USD Anim will be an open-source revision of technology that already exists
      within Pixar's Presto animation system.

    - Pixar's plan is to operate Presto on top of USD Anim, with an adapter
      layer.

    - This requirement should be mostly invisible to the outside world.
      However, it may influence the decisions Pixar makes about USD Anim.

- **Fast Hermite evaluation:** a runtime-friendly format.

    - USD Anim will support cubic Bezier curve segments, which are probably the
      spline model in widest use.  Bezier curves are parametric, so evaluating a
      curve at a given time may require an iterative solving process.  Pixar has
      found the cost of the solve negligible in the context of executing complex
      rigging, but it may not be fast enough for all applications.

    - USD Anim will also support cubic Hermite curve segments.  These differ
      from Bezier curves in that they have one fewer degree of freedom: tangents
      have fixed lengths, and only their slopes may be specified.  In return,
      Hermite curves are non-parametric, and can be evaluated in constant time
      via a simple cubic polynomial.

- **General USD standards:** a contextually appropriate implementation.

    - Open-source, multi-platform, C++.
    - Low-level and simple, with no external dependencies.
    - High-quality and fast.
    - Well-organized API.
    - Extensive Python wrapping, tests, and documentation.

USD Anim will specifically **not** aim to provide:

- **High-level editing operations.** There are lots of interesting ways to
  manipulate splines, but USD Anim will not try to tackle that topic; instead,
  USD Anim will provide a minimal implementation on top of which editing
  libraries could be built.  USD Anim will include editing primitives like
  inserting and altering knots, and a few simple utilities like resampling, but
  not higher-level operations like smoothing, stretching, randomization, etc.

## Nomenclature

We use the word _animation_, and the abbreviation _anim_, to refer to values
controlled by splines.  This doesn't necessarily imply character animation; it
just means "changing over time".

When we say _curve_, we mean a function that may be curved, or may consist of
straight lines.

We use the word _spline_ to mean the animation control curve for a
floating-point value.  This is true even when curves contain held or linear
segments.  These straight-line segments are not the first example of a spline
that probably comes to mind, and they are not interpolated using spline math,
but we still call them splines.

We refer to the points where curve segments join as _knots_.  In a
character-animation context, these are typically called _keyframes_; we are
trying to be more general.

Mathematicians sometimes refer to a Bezier segment as having four knots.  We
only call the segment endpoints knots; we call the two internal control points
_tangent endpoints_ (or just tangents).  We say that the tangents belong to the
knots: if the segment has points 1, 2, 3, and 4, then 2 is one of the tangents
of 1, and 3 is one of the tangents of 4.

When something precedes or follows something else in the time dimension, we use
the prefixes _pre_ and _post_.  This is as opposed to _left_ and _right_, or
_in_ and _out_, which also frequently occur in spline APIs.  So, for example, we
have _pre-tangents_ and _post-tangents_ belonging to knots.

USD Anim will support instantaneous changes in value via _dual-valued knots_.
These knots have an ordinary value and a _pre-value_.  At precisely the knot
time, the value changes from the pre-value to the ordinary value.

There are apparently two common meanings of _Hermite curve_.  The first is the
original mathematical meaning: a class of curves that is a subset of Beziers,
with fixed-length tangents.  The second is a class of curves exactly equivalent
to Beziers, with varying tangent lengths, but using different basis functions.
In USD Anim, when we talk about Hermites, we are talking about the first
version: the restricted class of curves with fixed-length tangents.  This is
also what is meant by "Hermite" in Maya.

## Resources

[Freya Holmer's spline video](https://www.youtube.com/watch?v=jvPPXbo87ds) is a
wonderful introduction to splines.

[The Pomax Bezier page](https://pomax.github.io/bezierinfo/) is the definitive
resource for spline math in programming.

# OBJECT MODEL

Here is a summary of the proposed data fields that will make up splines and
related classes.  This is an abstract description, not a literal data structure.
However, the USD Anim API will follow this description at least partly.

```
Spline <ValueType>
    curveType : enum { bezier, hermite }
    knots : array <Knot <ValueType> >
    innerLoopParams : InnerLoopParams
    preExtrapolation, postExtrapolation : Extrapolation <ValueType>

Knot <ValueType>
    time : double
    postInterpolation : enum { held, linear, curve }
    value : ValueType
    preValue : ValueType (when dual-valued)
    preTangent, postTangent : Tangent <ValueType> (when segment is curve)
    customData : Dictionary

Tangent <ValueType>
    timeLength : double
    union
        slope : ValueType
        height : ValueType
    auto : bool

InnerLoopParams
    prototypeStartTime : double
    prototypeTimeLength : double
    numPreLoops : int
    numPostLoops : int

Extrapolation
    method : enum { held, linear, sloped, loopRepeat, loopReset, loopOscillate }
    slope : double (when sloped)
```

## Value Type Categories

Floating-point scalars - `double`, `float`, and `half` - are the attribute value
types that USD splines will support.

USD's existing time samples support time-varying values for all value types.
That includes floating-point scalars, and it includes everything else.

The "everything else" includes these value type categories:

- **Floating-point vectors.** These can be linearly interpolated.  There are two
  cases: fixed tuples like `double3`, and arrays like `doubleArray`; these can
  also combine into arrays-of-tuples like `double3Array`.  While it would be
  possible to support Bezier splines of these values, and indeed Presto does, we
  aren't aware of any need for this in USD.

- **Quaternions.** These typically encode 3D rotations.  Like floating-point
  vectors (of which they are a sub-category), quaternions aren't typically
  authored with user-controlled tangents.  We believe the only broadly useful
  interpolation behavior for quaternions is _slerp_, which time samples already
  provide.

- **All other types.** Cannot be interpolated.  These include discrete,
  non-numeric types like `bool` and `string`, and vectors of them.  They also
  include quantized numeric types like `int`, and vectors of them; quantized
  types could be interpolated with rounding, but we're not aware of any need.
  An important future case for the "all other types" category is _constraints_,
  which tie one geometric transform to another, and which will be
  `SdfPath`-valued.

Splines support several features that time samples do not.  These are the
features that will therefore be missing for non-floating-point-scalar types:

For interpolatable types:

- Curved interpolation.
- Optional held interpolation.
- Flexible extrapolation.

For all types:

- Dual values.
- Looping.
- Per-knot custom data.
- Authoring conveniences, e.g. compare, split, resample.

The door is not closed to adding spline support for additional types in the
future.  We are proposing omitting them because we have had very little need for
them at Pixar, and we don't yet have any compelling use cases from outside
Pixar.  For these types, time samples and splines would risk duplicating
functionality and increasing complexity.  See
[Question: splines of other value types](#splines-of-other-value-types).

## Value Types

Each spline holds values of a single type: `double`, `float`, and `half`.

Time, unlike values, is always typed as `double`.  This is consistent with the
rest of USD.

## Knots and Segments

A spline is primarily defined by its knots.  Each knot specifies a (time, value)
coordinate through which the spline passes.

The regions between knots are called _segments_.  There is one important field
that applies to segments rather than knots: the interpolation method.  Rather
than introduce explicit segment objects, we propose to attach the interpolation
method to knot objects.  The field is called "post-interpolation" to clarify
that the method applies to the following segment, not the preceding one.

Bezier and Hermite segments have tangents; other segments do not.  Tangents are
attached to knots.  The presence or absence of a meaningful pre-tangent on a
given knot is determined by the post-interpolation method declared on the
previous knot.

### Non-Meaningful Data

The last knot in every spline will specify a post-interpolation method that has
no effect, since there is no next segment (though there is extrapolation,
covered below).

Knots that are not adjacent to Bezier or Hermite segments may still have
tangents defined, even though those tangents will have no effect.  This includes
tangents at the first and last knots that point outside the range of all knots.

We propose that this slightly ungainly arrangement is a reasonable compromise
that allows graceful programmatic construction of splines.  It is more intuitive
to add knots one at a time, with all fields provided for each knot, than to
first create the knot structure and then fill in the details.  It is also handy,
at an interactive interpreter, to be able to make changes without starting over.

As an optimization, we may decide not to serialize these non-meaningful data.

## Segment Types

While it would be possible to support mixtures of Bezier and Hermite segments,
we do not expect this to be a common need.  We thus propose that each spline
specifies either Bezier or Hermite for its curve segments.  Any segment marked
with the interpolation mode "curve" then uses the spline-level curve type.

In **held** segments, the interpolated value is the same as the value at the
preceding knot.  There is an instantaneous value change (a "stair-step"
transition) at the following knot.

In **linear** segments, the value is interpolated linearly between the preceding
and following knot.

In **Bezier** segments, the value is determined by the Bezier curve defined by
the tangent slopes and lengths.

In **Hermite** segments, the value is determined by the Hermite curve defined by
the tangent slopes.  Hermite segments are exactly equivalent to Bezier segments
with tangent lengths that are one-third of the interval width.

![Held knots](./held.png)
![Linear knots](./linear.png)
![Bezier knots](./bezier.png)
![Hermite knots](./hermite.png)

## Tangents

Tangents in USD splines can be specified in either of two forms:

- By slope and length.  This is how Presto represents tangent vectors.
- By height and length.  This is how Maya represents tangent vectors.

The two forms are equivalent; either can be converted to the other.  But the
conversion can lose numeric precision due to rounding error from multiplication
and division.  We want to allow clients to round-trip tangents through USD Anim
and get back exactly what they put in.

### Tangent Components

![Tangent components](./tangents.png)

Tangent vectors are decomposed into _length_, in the time dimension, and
_height_, in the value dimension.

Lengths are always positive.  They are absolute offsets from the knots to which
they belong.  Their time scale is the same as the enclosing layer's time scale,
the same scale used by the knot times.

### Presto Tangents

Presto tangents are specified by _slope_ and _length_.

Slopes are "rise over run": height divided by length.  The types of slopes are
the same as the types of values; a slope specifies the value change per unit of
time.  A positive slope (regardless of whether it is a pre-slope or a
post-slope) increases in value as time increases, a negative slope decreases in
value as time increases, and a zero slope is _flat_: it does not change in value
over time.  Slopes may approach vertical, but they may never be infinite, so
they cannot quite be vertical, and they cannot invert past vertical.  This means
that slopes never cause a spline to become a non-function where the curve has
multiple values at any time.

### Maya Tangents

Maya tangents are specified by _height_ and _length_.

The units of height are the same as the units of values.

Height and length are both specified multiplied by 3; e.g. if a tangent vector
is 1.5 units in the time dimension, its length is recorded as 4.5.

Heights are positive for upward-sloping post-tangents, and negative for
upward-sloping pre-tangents.

### Continuity

Segment-to-segment continuity, as in all Beziers, depends on the alignment of a
knot's pre-tangent and post-tangent.  Continuity is not explicitly recorded as
part of spline data, and is not automatically preserved by USD editing
operations, but it may be ensured programmatically by clients, and it may be
queried from a spline.  These are the cases:

| Continuity class | Continuous value | Continuous tangents | Continuous slope | How achieved                          |
| :--------------- | :--------------: | :-----------------: | :--------------: | :------------------------------------ |
| Discontinuous    | No               | No                  | No               | Dual-valued knot                      |
| C0               | Yes              | No                  | No               | Broken tangents (mismatched slopes)   |
| G1               | Yes              | Yes                 | No               | Unequal tangents (mismatched lengths) |
| C1               | Yes              | Yes                 | Yes              | Identical tangents                    |

![Discontinuous](./discontinuous.png)
![C0](./C0.png)
![G1](./G1.png)
![C1](./C1.png)

The higher continuities G2 and C2 are sometimes useful, but for now we are
proposing omitting them from the queries supported by USD splines.  That is for
two reasons:

- For G2 and C2, there aren't intuitive rules about how tangents align.
  Instead, more abstract geometric invariants must be maintained.

- Achieving G2 and C2 requires relinquishing some degree of "local control",
  which is typically a vital benefit of Bezier splines.  Local control means
  that a knot or tangent position may be changed without affecting the curve on
  any segments other than its own.

### Automatic Tangents

Sometimes spline authors want to specify only knot values, and get a "nice"
curve that interpolates those knots smoothly.  This sacrifices some degree of
control over the shape of the curve, but allows quicker work, and guarantees
consistently styled shapes with some degree of continuity.

USD Anim will allow any tangent to be specified as "auto".  Each of the two
tangents of a knot may be specified separately, so a knot may be "pre-auto" and
"post-manual", or vice versa.

Automatic tangents are computed only when knots are first defined, and when they
are edited.  We therefore say that automatic tangents are an _edit-time
behavior_.

The exact algorithm for computing automatic tangents has yet to be specified;
most likely we will adopt one of the Maya auto-tangent algorithms.  Other
algorithms are possible, and may be available in the future.  Ideally any
automatic tangent algorithm will support both Bezier and Hermite segments, but
in theory some algorithms could be applicable only to Beziers.

Automatic tangents are arguably in tension with our stated goal of not having
any magical tuning parameters in USD Anim.  Nevertheless:

- Automatic tangents are an opt-in behavior.
- We will publish an exact specification of the algorithm.
- We believe the utility outweighs any concerns about hard-coded behavior.

### Regressive Splines

Splines encode functions: for any time, there should be exactly one value.  It
is possible (using very long tangents) to construct a spline segment that, under
the Bezier rules, travels forward in time, then backward, then forward again.
Most (all?) DCCs and evaluation engines consider this an unacceptable condition,
and alter the spline in some way, so that every spline is indeed a function.

This surprisingly complex topic is covered in a separate
[Regressive Splines](./regressive.md) document.  In summary, USD Anim proposes a
flexible anti-regression system that focuses on authoring-time limiting.
Clients will at least want to consider which of the various anti-regression
strategies they wish to use, and interactive clients may want to take advantage
of interactive limiting during edits.

## Dual-Valued Knots

Value discontinuities may be introduced to splines by means of _dual-valued
knots_.  A dual-valued knot has two values: an ordinary value, and a
_pre-value_.  The value exactly at the knot time, and at any nonzero time delta
after the knot, is the ordinary value.  The value at any nonzero time delta
before the knot is the pre-value.  There is an instantaneous change in value at
exactly the knot time.

Any knot can be dual-valued, regardless of the interpolation methods of the
adjacent segments.  However, if a dual-valued knot follows a held segment, the
pre-value is ignored, because otherwise there would be a strange case where the
pre-value was effective at only the left side of a single knot.  So in this
case, if the pre-side value is queried, the value return is the held value from
the prior knot.

### Sided Queries

The fundamental USD value resolution operation is `UsdAttribute::Get`.  This
takes a `UsdTimeCode` parameter to specify the time at which to evaluate.  USD
Anim will introduce a new "pre-time" flag to `UsdTimeCode`.  This will allow
attribute values to be determined at ordinary times, and at _pre-times_, which
mathematically are limits from the pre-side of the given time.

Usually the value at a pre-time, which is a _pre-value_, is the same as the
value at the corresponding ordinary time.  But there are some situations where
the two values will differ, because there is a value discontinuity at that
time.  These include:

- At a dual-valued spline knot.
- At a knot at the end of a held spline segment.
- At a time sample with held interpolation (e.g. for a string-valued attribute).
- At the boundary of spline loop iterations in "reset" mode.
- At "jump discontinuities" in value clips.

Pre-values and ordinary values are asymmetrical.  The pre-value is a limit value
at an infinitesimal time before the time coordinate.  The ordinary value is the
value exactly at the time coordinate, and also at an infinitesimal time after.
The transition happens between the pre-limit and the exact time.  Note that
these are true limits in the mathematical sense: the infinitesimal time delta is
smaller than any possible actual time delta.

Pre-values typically are not evaluated directly in order to render USD content.
They exist as a mechanism for shaping curves.  Querying pre-values is often
important for authoring systems, but usually not important for downstream
evaluation.

In addition to `UsdAttribute::Get`, sided queries may trickle through
higher-level APIs, such as the many interfaces in `usdGeom` that accept
`UsdTimeCode` parameters.

For `UsdAttribute::Set`, which sets time-sample values, the pre-time flag in
`UsdTimeCode` will have no effect.  We are not proposing to add explicit
pre-values to time samples.

## Looping

_Looping_ is the repeating of spline regions.  Looping will be supported in two
forms:

- _Inner loops_ come from Presto.  These specify a _prototype region_, which is
  repeated a finite number of times before and/or after the prototype region.
  The repeated portions are called the _echo region_.  Inner loops use a mode
  called _Continue_, described below.

- _Extrapolating loops_ come from Maya.  These use the entire spline (from first
   to last knot) as the prototype region, and repeat it infinitely before and/or
   after the knots.  Extrapolating loops support modes called _Repeat_, _Reset_,
   and _Oscillate_, described below.

![Inner loops](./innerLoops.png)
![Extrapolating loops](./extrapLoops.png)

It will be possible to use both systems in the same spline.  In that case, inner
loops are resolved first, and then extrapolating loops take into account the
entire spline, from first to last knot, with the inner-loop repeats included.

### Looping Modes

The two looping systems work differently:

| Mode family              | Algorithm            | Continuous splines? | Altered prototype? |
| :----------------------- | :------------------- | :-----------------: | :----------------: |
| Continue                 | Copy whole knots     | Typically yes       | Typically yes      |
| Repeat, Reset, Oscillate | Copy knots in pieces | Typically no        | No                 |

Continue mode copies any knots that fall in the prototype region.  Knots are
copied wholesale; in particular, pre-tangent / post-tangent pairs from prototype
knots are kept together.  This has the advantage that, if the knots in the
prototype region are continuous, then the curve in the echo region is continous
also, including at the joins between iterations.  In return, a disadvantage of
Continue mode is that if a spline is first authored without looping, and looping
is later enabled, the shape of the curve in the prototype region may change.  A
common example is that the prototype region has knots at the start and the end,
and the end knot is overwritten by a copy of the start knot, thus changing the
shape at the end of the prototype region.  (The prototype region includes knots
exactly at the start, but excludes those exactly at the end.)

Repeat, Reset, and Oscillate modes exactly preserve the shape of the prototype
region.  The echoed knot at a join between iterations has a pre-tangent
determined by the end of the prototype region, and a post-tangent determined by
the start of the prototype region.  These modes generally do not preserve
continuity; the cases are explained below.

![Repeat](./repeat.png)
![Reset](./reset.png)
![Oscillate](./oscillate.png)

Continue and Repeat modes both use a _value offset_ at each loop iteration.
This ensures C0 continuity at the joins between iterations.  If the value at the
end of the prototype region is not the same as the value at the start, then the
iterations _accumulate_: each iteration is offset in value from its neighbors.

In Repeat mode, the joins between iterations can be continuous, but only to the
extent that the post-tangent of the first knot is continuous with the
pre-tangent of the last knot.  Otherwise, the joins in Repeat mode have
G1-discontinuous cusps.

Reset mode is like Repeat, except that it exactly reproduces the values from the
prototype region in each iteration.  If the value at the end of the prototype
region is not the same as the value at the start, then there are C0
discontinuities (instantaneous changes) at the iteration boundaries.

Oscillate mode is like Repeat, except that the shape of the curve is
time-reversed in every other iteration.  The iterations do not accumulate,
because the time-reversed iterations return the curve to its starting value.  In
Oscillate mode, the joins between iterations are G1-continuous only if the
tangents are flat, since the tangents across joins are mirrored.

### Knots Shadowed by Inner Loops

When inner looping is in use, any knots that are authored in the echo region are
_shadowed_: effectively overwritten by the echoed curve, and ignored for
purposes of evaluation.

Shadowed knots are still recorded in the spline, and may still be accessed; see
the Looping API details below.

### Looping API

Looping works by creating echoed knots.  When clients ask for the set of knots
from a spline, they may request them in three different forms:

- Only the authored knots, without any looping applied.

- Knots after resolving inner loops (the _baked spline_).

- Knots after resolving both inner loops and extrapolating loops.  Because
  extrapolating loops repeat infinitely, clients must specify a time range, so
  that the returned set of knots is finite.

Here are the categories of knots as they relate to looping.  Note that each
query returns knots without any indication of which of these categories they
belong to.  Clients can classify knots if they need to, by examining the looping
control parameters.

![Loop regions](./loopRegions.png)

| Knot category             | Included in "authored knots" query? | Included in "baked knots" query? |
| :------------------------ | :---------------------------------: | :------------------------------: |
| Prototype knots           | Yes                                 | Yes                              |
| Echoed knots              | No                                  | Yes                              |
| Shadowed knots            | Yes                                 | No                               |
| Knots outside echo region | Yes                                 | Yes                              |

For now, we propose that USD Anim support at most one inner-loop region per
spline; that inner loops support only Continue mode; and that extrapolating
loops support only Repeat, Reset, and Oscillate modes.
See [Question: looping limitations](#looping-limitations).

## Extrapolation

Extrapolation determines spline values before the first knot and after the
last.  The available extrapolation methods are:

- **None.** Outside of the authored knots, no values are returned.  It is as
  though an `SdfValueBlock` has been authored in the extrapolating regions.

- **Held.** The extrapolated value is a constant, and is the same as the first
  or last knot.

- **Linear.** The extrapolated value is governed by a straight line that starts
  at the first or last knot, and whose slope is determined as follows:

    - If the first or last segment is held, the slope is flat.

    - If the first or last segment is linear, the slope matches that segment.

    - If the first or last segment is curved, the slope matches the tangent on
      the opposite side.  If there is a tangent on the extrapolating side, it
      has no effect (see "Non-Meaningful Data" above).

- **Sloped.** Like Linear, but with a slope that is explicitly set as part of
  the spline data.

- **Looping.** See the "Looping" section above.

## Custom Data

It is important for clients to be able to store their own data alongside USD
scene description.  USD prims and attributes have _custom data_: values meaningful
only to clients, and stored blindly by USD.

USD splines will also support custom data on individual knots.  The supported
types for custom data will be the same as those for prims and attributes,
including hierarchical types like dictionaries and arrays.

# INTEGRATION WITH USD

Splines will be integrated into USD in the following ways.

## Attribute Value Resolution

The most important function of splines will be to provide attribute values.
When clients call `UsdAttribute::Get` (or `UsdAttributeQuery::Get`), the
resulting value may come from a spline.

USD will have the following list of value categories, in priority order:

- Time samples
- Splines
- Default values
- Fallback values

When there are opinions about attribute values on multiple layers, USD will do
what it has always done: find the strongest layer with any kind of opinion, then
within that layer, take the opinion from the highest-priority value category
from the list above.  Thus, for example, a default value on a stronger layer
will override a spline value on a weaker one.

The `UsdResolveInfo` class, accessed via `UsdAttribute::GetResolveInfo`, will be
extended to include splines as a possible value source.

## Spline Access

`UsdAttribute` will have new methods called `GetSpline` and `SetSpline`.  These
will provide whole-spline-level read/write access to splines.  Finer-grained
operations can be conducted by methods on the returned objects; the API is
described below.

Note that this is different from the way time samples are integrated into
`UsdAttribute`.  Time samples do not have their own class, and are directly
accessed via `UsdAttribute` methods like `Set`, `ClearAtTime`, and `Block`.  We
believe the higher complexity of splines merits the different treatment.

We are also proposing that the time-sample-oriented methods of `UsdAttribute`
continue to address only time samples, and not splines.

## Spline Composition

The `pcp` library will need to be equipped to compose splines.  The scope of
this task is still TBD, but at a minimum, splines will need to be retimed when
crossing non-trivial layer scales and offsets, which affect the interpretation
of time.

For example, imagine layer A includes layer B as a sublayer with a layer offset,
and layer B has the strongest opinion for a given attribute.  Layer B's spline
opinion will be authored using layer B's timeline, but that timeline must be
shifted in the context of layer A.  The same thing already happens for time
samples.

## Value Blocks

USD has a special value called `SdfValueBlock` that represents the absence of a
value, causing `UsdAttribute::Get` to behave as though no value were authored,
returning either a fallback value or no value.  Value blocks may be set on a
time-varying basis, and this will be true of splines as it is for time samples.
We will treat "block knots" as held: they will affect the time region from the
knot's time until the next knot.

Value blocks will affect extrapolation when they are present as the first or
last knot in a spline.  Evaluation in the extrapolated region of such a spline
will return no value.  It will also be possible to disable _only_ extrapolation
by using the "None" extrapolation mode.

Splines will introduce an additional pattern that can block weaker opinions: an
empty spline.  As always, the presence of any spline opinions overrides weaker
layers and default values.  A spline with no knots is still a valid spline, so
it blocks weaker opinions, but it provides no values.  Like `SdfValueBlock`, an
empty spline will not block fallback values when `UsdAttribute::Get` is called.

## Serialization

Splines will become part of the Sdf data model, and thus supported in the `usda`
and `usdc` file formats.

## Scalar Transforms

As an auxiliary improvement, we will add scalar translation and scaling to
`UsdGeomXformOp`.  This will bring translation and scaling up to the level of
rotations, which can already be expressed as scalars.  This improvement will
mean that translation, for example, can be expressed as three different ops - an
X translation, a Y translation, and a Z translation - rather than only as a
single vector-valued XYZ translation.

Transforms are one of the most common cases for spline-driven animation, so we
want to make it convenient to drive transforms from scalar splines.

## Spline Utilities

There are a few utilities for spline introspection and manipulation that are
sufficiently low-level and general to merit inclusion in USD Anim.

- A **diff** utility that finds time regions that differ between two splines.
- A **simplify** utility that eliminates knots that have little effect.
- A **resample** utility that generates a simpler set of knots.

The current implementations of the simplify and resample utilities always return
all-Bezier splines.  It is TBD whether this can be improved; for example, it
seems desirable that an all-Hermite input spline should result in an all-Hermite
output spline.

## Splines in usdview

The `usdview` application will be updated to display spline values, including a
basic visualization of curves over time.

## Motion Blur

When rendering animated USD content with motion blur, we must determine the time
coordinates at which samples should be taken.  This can include both how many
different samples should be taken for a given frame, and how the samples are
distributed in time.

In existing USD content, animated values are represented with time samples.
Time samples provide clear policy about render sampling: we sample at the time
sample times.

When rendering USD content containing splines, the situation will be different.
We could potentially use knot times for sampling, but knot times don't
necessarily indicate an intent to sample; they may only have been chosen in
order to achieve a desired curve shape with sparse data.

We have not yet determined what mechanisms we will implement for motion-blur
sampling of splines, but we are aware that changes and testing will be required.
It is possible that render hints, recorded via schemas, will play a role.

## Deferred Features

When there are spline opinions on multiple layers, only the spline from the
strongest layer will be considered.  There has been some discussion of _sparse
overrides_, where spline knots could be integrated from multiple layers, but we
consider this a future feature, and not a trivial one.

We would eventually like it to be possible to include splines in value clips.
This too is deferred until future development.  For the first release of USD
Anim, splines in value clips will be silently ignored, much like default values
in value clips.

If clients want to use splines as retiming curves, it might be useful to have a
`timecode`-valued spline.  These would differ from `double`-valued splines in
just one way: in the presence of layer offsets (see "Spline Composition" above),
the spline's values would be transformed in addition to its knot times.  We
believe we can defer this for now.

# ARCHITECTURE

USD Anim will be implemented as follows.

## Libraries

Most of USD Anim will reside in a library called `pxr/base/ts`, where `ts`
stands for "time spline".  This will implement the central `TsSpline` class, and
all of its supporting infrastructure.

Everything in the "integration" section above will require changes to existing
libraries, especially `sdf`, `pcp`, and `usd`.

## Optimizations

`TsSpline` will be designed with speed in mind.  The in-memory representation
will be optimized for splines that contain only Bezier or Hermite segments.
Less-common features like dual-valued knots, per-knot custom data, and looping
will likely be side-allocated.

A simple `TsEvalCache` class will be provided.  This will allow clients to
perform repeated evaluation with cached results.

The `usdc` "crate" format is optimized for "single-frame reads", where all
time-varying data for a given time is packed together, improving locality of
access.  For now, we are proposing **not** to include splines in this system,
but instead to store splines monolithically, alongside non-time-varying data.
This is for two reasons.  First, splines are sparse: there are typically fewer
knots than expected evaluation times.  We could store, at each frame time, the
two knots from each spline that come before and after that time, but this would
cause extensive duplication that would undermine one of the advantages of
splines, which is that their data is small.  Second, we already have a great way
to store precomputed per-frame values, which is to use time samples.

## Threading Model

USD Anim will comply with the typical USD threading model: it will be safe,
without external synchronization, to have multiple readers of the same data.
Multiple writers, or writer + reader combinations, will require separate
locking.

Not much is required to meet this goal.  Some cache classes will need internal
locks.

## Feature Reduction

Two things are simultaneously true:

- Different clients will want to support different sets of spline features.
  This is already true of Presto and Maya.  We also want to ensure that clients
  can be written without supporting every spline feature.

- USD is used for interchange, and we want all splines to be readable by all
  clients.

Our proposed solution for this situation is _reduction_: an API that allows
clients to replace unsupported spline features with emulations.  Clients pass a
set of input splines (one, all in a layer, or all on a stage), a specification
of features the client supports, and in some cases parameters for emulation.
The result is a set of output splines that fall within the client's feature set,
and evaluate identically to the input splines, or nearly so.

At minimum, clients must support Bezier segments.  Most other features are
optional.

Here is a list of emulations that will be available.  This list is not
necessarily complete yet.

| Feature              | Emulation pattern    | Parameters  |
| :------------------- | :------------------- | :---------- |
| Held segments        | Equivalent Beziers   | None        |
| Linear segments      | Equivalent Beziers   | None        |
| Hermite segments     | Equivalent Beziers   | None        |
| Automatic tangents   | Non-auto tangents    | None        |
| Dual-valued knots    | Closely spaced knots | Time delta  |
| Inner loops          | Baked splines        | None        |
| Extrapolating loops  | Baked splines        | Time window |
| Extrapolating slopes | Extra knots          | Time window |

We might want to have our reduction code insert metadata to indicate where
emulations have been applied.  This would help clients recognize, for example,
extra knots that weren't part of the original data.
See [Question: reduction metadata](#reduction-metadata).

## Round-Trip Considerations

It is desirable to allow USD splines to be passed among multiple clients, with
piecemeal edits made by each, without introducing unintended changes in the
unmodified parts of the data.

This is a client responsibility; it isn't a pattern that the USD core can
enforce.  But we want Presto to work this way, so we have tried to imagine what
issues will crop up, how USD will behave, and what clients can do.

### Proprietary Custom Data

Client A creates a USD file containing splines with per-knot custom data that
are meaningful only to Client A.  Client B modifies one of these splines.
Client A reads the file again.  What should happen?

We foresee two flavors of per-knot custom data: some (like a tangent-computation
algorithm) that may become invalid when a knot is edited, and some (like a
display color) that do not.  This means there's no single policy that will
always work, and supporting an extra "self-destruct" flag on custom data seems
complex.

For now, we propose to keep per-knot custom data truly _blind_ data: USD will do
nothing except preserve it where it exists.  If a knot is edited in Client B,
and this invalidates its custom data from Client A, that is just what happens.
Client A will have to decide what to do if inconsistent custom data comes back.

See [Question: custom data edit policies](#custom-data-edit-policies).

### Local Translations

When a client reads in a USD file, it may modify splines for its own
consumption.  Reasons may include:

- Feature reduction, as described above.
- Other local modifications, such as for proprietary editing features.

Clients that do this should take care that these "read-time" modifications do
not leak back into the USD file from which the splines came.  Clients may need
to cache the original spline / layer / stage, and write modifications back to
the original only for splines that have been intentionally edited.

## Test Framework

USD Anim will include tests that verify:

- The behavior and performance of `TsSpline`.
- The compatibility of `TsSpline` with Maya.
- The integration of `TsSpline` with USD.

To support these goals, the test infrastructure will include optional components
that will be available when the supporting packages are available.  These
include:

- A way to evaluate splines in Maya, by invoking `mayapy`.
- A way to draw visualizations of splines, by invoking `matplotlib`.

# SPLINE API OVERVIEW

This section proposes some details of how clients will interact with USD splines.

## Evaluation-Only Clients

For most software that only _evaluates_ USD data, `UsdAttribute` should provide
sufficient handling of splines.  The `UsdAttribute::Get` method automatically
resolves attribute values from any source, including splines.

For clients that perform _authoring_ of USD data, or require deeper
introspection of existing data, the spline API will be relevant.

## Time Orientation

The X and Y axes of splines may, in general, have various meanings.  In the
first release of USD Anim, the X axis of a spline will always be time.  But
there are other possible uses of splines.  For example, OpenExec may support the
use of splines as dimensionless mapping curves: values in, values out.  The
underlying math will not change at all, but the meanings will be different to
clients.

There is thus a question of nomenclature: should the X axis of a spline be
called `time` in the spline API, or should it be generically called `x`?

We are proposing, for now, to keep the USD Anim API explicitly time-oriented.
That is why we have chosen the name `ts` ("time spline") for the spline library.
In our experience with Presto, we have used time-oriented splines in the vast
majority of use cases, and we are also seeking to avoid introducing generality
to USD that is not yet required.

If non-time-oriented spline usage does find its way into USD, we will have two
options, both of which are probably acceptable:

- **Generalize.** Make a copy of `ts`; rename classes, methods, and parameters
  to be more generic.  Reimplement `ts` as a header-only library that wraps the
  generic version with the original time-oriented names.  Continue referring to
  `ts` in places where time is in use, and refer to the generic library in
  places where it is not.

- **Live with it.** Hold our noses and call the `ts` API even in places where
  time is not involved.  This is what we have done in Presto.

See [Question: time-oriented API](#time-oriented-api).

## TsSpline

`TsSpline` will be the main class in the `ts` library.  It represents all the
data for one spline.  It allows splines to be defined, transferred, evaluated,
and edited.  It will be a low-level class, and will know nothing about USD.

We propose that `TsSpline` have _value semantics_, internally carrying a copy of
the data that it represents.  We propose that all spline objects be
_copy-on-write_, so that making multiple copies of a spline is cheap as long as
the copies are not modified.  It should be unnecessary to refer to spline
objects by pointer.

Splines can have different value types.  We propose that spline classes be
non-templated, for simplicity, and to avoid the need for non-templated base
classes.  We propose that typed access to values and slopes be accomplished by
means of templated accessors and mutators, and that type-erased access be
available by passing `VtValue` as an in or out parameter, instead of the value
type.  We propose that typed read access be the moral equivalent of
`VtValue::UncheckedGet`, with no guardrails for incorrect types.  Typed write
access, on the other hand, will verify that all knots in a spline use the same
type.

## Error Handling

We recognize two classes of potentially problematic data:

- **Immediately contradictory.** E.g. differently-typed knots in the same
  spline.  These situations will result in coding errors and no changes to the
  spline.

- **Eventually contradictory or non-standard.** Treatment of these situations
  varies, but they are allowed.  Interesting cases include:

| Condition         | Example                             | Behavior           |
| :---------------- | :---------------------------------- | :----------------- |
| Empty spline      | `TsSpline()`                        | No values provided |
| Omitted data      | Missing tangents for curve segments | Assumed zero       |
| Inapplicable data | Tangents for linear segments        | Ignored            |
| Degenerate data   | Zero-size loop intervals            | Ignored            |
| Non-functions     | Regression                          | Forced functions   |

Because situations from the first category are always prevented, and situations
from the second category are always tolerated, there is no such thing as an
invalid `TsSpline`, and there are no methods for validation.

Also see "Non-Meaningful Data" above.

# SPLINE API PREVIEW

The full USD Anim interface is beyond the scope of this proposal, but some
highlights follow.

Some things to note:

- This is only a preview.  It is not complete, and may change.

- Some aspects of the API are simplified for clarity.  Types and parameter lists
  may change slightly.

- The API for anti-regression is listed in the separate
  [Regressive Splines](./regressive.md) document.

## Access From UsdAttribute

Splines are data attached to `UsdAttribute`s.

```c++
class UsdAttribute
{
    // ...

    // These signatures will not change, but their implementations will.
    template <typename T> bool Get(
        T *value, UsdTimeCode time = UsdTimeCode::Default()) const;
    bool Get(
        VtValue *value, UsdTimeCode time = UsdTimeCode::Default() const;
    UsdResolveInfo GetResolveInfo(UsdTimeCode time) const;
    bool ValueMightBeTimeVarying() const;

    // Spline data.
    TsSpline GetSpline() const;
    bool SetSpline(const TsSpline &spline);

    // These methods will continue to apply only to time samples:
    // GetNumTimeSamples
    // Get[Unioned]TimeSamples[InInterval]
    // GetBracketingTimeSamples
    // Set, with non-default time
    // ClearAtTime

    // ...
};
```

Access to spline values is in bulk, not individually by knot.

- To read a spline, clients call `GetSpline`.
- To establish a spline, clients call `SetSpline`.
- To modify a spline, clients read the spline, modify it, and write it back.

## TsSpline

This is the workhorse of USD Anim, representing parameters, knots, evaluation,
queries, and editing.

```c++
class TsSpline
{
    // PARAMETERS

    // Curve type: Bezier or Hermite.  All segments with type 'curve' use this
    // interpolation method.
    void SetCurveType(TsCurveType curveType);
    TsCurveType GetCurveType() const;

    void SetPreExtrapolation(const TsExtrapolation &extrap);
    TsExtrapolation GetPreExtrapolation() const;
    void SetPostExtrapolation(const TsExtrapolation &extrap);
    TsExtrapolation GetPostExtrapolation() const;

    void SetInnerLoopParams(const TsInnerLoopParams &params);
    TsInnerLoopParams GetInnerLoopParams() const;

    // KNOTS

    void SwapKnots(TsKnotMap *knots);
    void SetKnot(const TsKnot &knot);
    void RemoveKnot(double time);

    const TsKnotMap& GetKnots() const;

    // BAKING

    // Baking creates new knots to render the effect of looping, then removes
    // looping directives.  These methods modify the spline.
    void BakeInnerLoops();
    void BakeLoops(const GfInterval &timeSpan);

    // These methods return a copy of the knots in baked form, without modifying
    // the spline.
    const TsKnotMap& GetKnotsWithInnerLoopsBaked() const;
    const TsKnotMap& GetKnotsWithLoopsBaked(const GfInterval &timeSpan) const;

    // EVALUATION

    template <typename T> bool Eval(double time, T *valueOut) const;
    bool Eval(double time, VtValue *valueOut) const;
    template <typename T> bool EvalPreValue(double time, T *valueOut) const;
    bool EvalPreValue(double time, VtValue *valueOut) const;

    template <typename T> bool EvalDerivative(double time, T *valueOut) const;
    bool EvalDerivative(double time, VtValue *valueOut) const;
    template <typename T> bool EvalPreDerivative(double time, T *valueOut) const;
    bool EvalPreDerivative(double time, VtValue *valueOut) const;

    // Return a set of samples sufficient to draw the spline piecewise-linear
    // with an error that does not exceed the specified tolerance.  This is
    // faster than repeated evaluation.
    template <typename T> bool SampleForDrawing(
        const GfInterval &timeSpan,
        double tolerance,
        TsDrawingSamples<T> *samplesOut) const;

    // QUERIES

    TfType GetValueType() const;

    template <typename T> bool GetValueRange(
        const GfInterval &timeSpan,
        std::pair<T, T> *rangeOut) const;
    bool GetValueRange(
        const GfInterval &timeSpan,
        std::pair<VtValue, VtValue> *rangeOut) const;

    bool IsC0Continuous() const;
    bool IsG1Continuous() const;
    bool IsC1Continuous() const;

    // SPLITTING

    // Insert a knot at the specified time, exactly preserving the shape of the
    // curve.  If there is already a knot at that time, do nothing.  Return
    // whether a new knot was added.
    bool Split(double time);
};

// A knot container.  Stored as a vector, but kept sorted, and has some map-like
// methods that key on knot time.
//
class TsKnotMap
{
    // Generic methods: size, empty, erase, clear
    // Vector iterators: begin, end, rbegin, rend
    // Vector methods: reserve
    // Map methods: find(time), insert(knot), lower_bound(time), upper_bound(time)
};

template <typename T>
class TsEvalCache
{
    TsEvalCache(const TsSpline &spline);
    bool Eval(double time, T *valueOut) const;
};
```

## TsKnot

This class encapsulates a single knot in a spline.  It is mostly a simple data
container.

```c++
class TsKnot
{
    void SetTime(double time);
    double GetTime() const;

    // SdfValueBlock support
    void SetBlock(bool block);
    bool IsBlock() const;

    TfType GetValueType() const;

    template <typename T> void SetValue(const T &value);
    void SetValue(const VtValue &value);
    template <typename T> bool GetValue(T *valueOut) const;
    bool GetValue(VtValue *valueOut) const;

    bool IsDualValued() const;
    template <typename T> void SetPreValue(const T &value);
    void SetPreValue(const VtValue &value);
    template <typename T> bool GetPreValue(T *valueOut) const;
    bool GetPreValue(VtValue *valueOut) const;
    void SetPreBlock(bool block);
    bool IsPreBlock() const;
    void ClearPreValueAndPreBlock();

    bool SetPostInterp(TsInterpMethod method);
    TsInterpMethod GetPostInterp() const;

    bool IsC0Continuous() const;
    bool IsG1Continuous() const;
    bool IsC1Continuous() const;

    void SetCustomData(const VtDictionary &customData);
    VtDictionary GetCustomData() const;
    void SetCustomDataByKey(const TfToken &keyPath, const VtValue &value);
    VtValue GetCustomDataByKey(const TfToken &keyPath) const;

    // The many tangent methods cover:
    // - Setting and getting
    // - Pre-tangents and post-tangents
    // - Typed and VtValue
    // - Presto and Maya forms
    // - Length and slope/height
    // - Auto-tangents
    void SetPreTanLen(double len);
    double GetPreTanLen() const;
    template <typename T> void SetPreTanSlope(const T &slope);
    template <typename T> bool GetPreTanSlope(T *slopeOut) const;
    void SetPreTanSlope(const VtValue &slope);
    bool GetPreTanSlope(VtValue *slopeOut) const;
    void SetMayaPreTanLen(double len);
    double GetMayaPreTanLen() const;
    template <typename T> void SetMayaPreTanHeight(const T &height);
    template <typename T> bool GetMayaPreTanHeight(T *heightOut) const;
    void SetMayaPreTanHeight(const VtValue &height);
    bool GetMayaPreTanHeight(VtValue *heightOut) const;
    void SetPreTanAuto(bool auto);
    bool IsPreTanAuto() const;
    void SetPostTanLen(double len);
    double GetPostTanLen() const;
    template <typename T> void SetPostTanSlope(const T &slope);
    template <typename T> bool GetPostTanSlope(T *slopeOut) const;
    void SetPostTanSlope(const VtValue &slope);
    bool GetPostTanSlope(VtValue *slopeOut) const;
    void SetMayaPostTanLen(double len);
    double GetMayaPostTanLen() const;
    template <typename T> void SetMayaPostTanHeight(const T &height);
    template <typename T> bool GetMayaPostTanHeight(T *heightOut) const;
    void SetMayaPostTanHeight(const VtValue &height);
    bool GetMayaPostTanHeight(VtValue *heightOut) const;
    void SetPostTanAuto(bool auto);
    bool IsPostTanAuto() const;
};
```

All knots in a spline must have the same value type.  Attempting to mix knot
types in the same spline is an error.  Attempting to use an unsupported value
type (something other than `double`, `float`, or `half`) is also an error.

There may only be one knot at any given time.  Calling `SetKnot` with an
existing knot time will silently overwrite the existing knot.

See [Question: time snapping](#time-snapping).

## Automatic Tangent Computation

Whenever knots change, two kinds of automatic tangent recomputation occur:

- When splines contain automatic tangents, these are recomputed based on knot
  values.

- If anti-regression is not disabled, tangents are shortened if necessary.

During bulk editing operations, tangent recomputation can be deferred in order
to avoid redundant processing.  An RAII helper class called
`TsRecomputationBlock` will be provided for this purpose.

When knots with automatic tangents are serialized, the computed tangents will be
stored with the knots.  This denormalization will avoid a speed hit when reading
splines from USD files.  As with any denormalization, this admits the
possibility of inconsistent data - but only if a .usda file is edited outside of
the USD API.

## Structs and Enums

```c++
enum TsInterpMethod
{
    TsInterpHeld,
    TsInterpLinear,
    TsInterpCurve    // Bezier or Hermite, depends on curve type
};

enum TsCurveType
{
    TsCurveTypeBezier,
    TsCurveTypeHermite
};

enum TsExtrapMethod
{
    TsExtrapNone,
    TsExtrapHeld,
    TsExtrapLinear,
    TsExtrapSloped,
    TsExtrapLoopRepeat,
    TsExtrapLoopReset,
    TsExtrapLoopOscillate
};

struct TsLoopParams
{
    // Prototype region to be copied.  Knots exactly at the start are included;
    // knots exactly at the end are excluded.
    double protoStart;
    double protoLen;

    // Number of copies to make of the prototype region.  Zero makes no copies.
    unsigned int numPreLoops;
    unsigned int numPostLoops;
};

struct TsExtrapolation
{
    TsExtrapMethod method;
    double slope;
};
```

## Reduction

See the "Feature Reduction" section above.

The basic implementation will be for individual splines:

```c++
enum TsFeatureFlag
{
    TsFeatureHeldSegments,
    TsFeatureLinearSegments,
    TsFeatureHermiteSegments,
    TsFeatureAutomaticTangents,
    TsFeatureDualValuedKnots,
    TsFeatureInnerLoops,
    TsFeatureExtrapLoops,
    TsFeatureExtrapSlopes
};
using TsFeatureFlags = int;

struct TsReductionParams
{
    TsFeatureFlags supportedFeatures;
    double dualValueTimeDelta;
    GfInterval extrapolationTimeRange;
};

// Reduces the provided spline, if necessary, to use only the specified
// features.  Returns whether any changes were made.
//
bool TsReduceSpline(
    TsSpline *spline,
    const TsReductionParams &params);
```

We will likely also want conveniences for whole layers and stages.  These might
go in `usdUtils`:

```c++
bool UsdUtilsReduceSplinesInLayer(
    const SdfLayerHandle &layer,
    const TsReductionParams &params);

bool UsdUtilsReduceSplinesOnStage(
    const UsdStagePtr &stage,
    const TsReductionParams &params,
    const UsdEditTarget &editTarget = UsdEditTarget());
```

`ReduceSplinesOnStage` is potentially problematic, because it could lead to a
mixture of reduced and unreduced opinions in various layers.  But it certainly
does seem convenient.  If clients use a topmost layer as an edit target, that
should suffice for reading.

## Utilities

The following general-purpose spline utilities will be available:

```c++
// Returns the bounding interval of regions over which the specified splines
// will evaluate to different values.  The returned interval may be infinite on
// either side when extrapolation differs.  The returned interval is a bound,
// and it is possible that there are regions within that bound where the splines
// do not differ.
//
GfInterval TsFindDifferingInterval(
    const TsSpline &s1,
    const TsSpline &s2);

// Removes as many knots as possible from the specified intervals of a spline
// without introducing error greater than maxErrorFraction * value range in
// intervals.  Extremes (high or low points) are always preserved, and they are
// detected by finding knots that are above or below their neighbors by at least
// maxExtremeFraction * value range in intervals.
//
void TsSimplifySpline(
    TsSpline *spline,
    const GfMultiInterval &intervals = GfMultiInterval::GetFullInterval(),
    double maxErrorFraction = .01,
    double maxExtremeFraction = .001);

// Finds a new set of knots that describe a similar spline, but with possibly
// fewer knots.  First densely samples the spline by adding splits quantized
// to samplingInterval (both absolutely and in spacing).  Then calls
// TsSimplifySpline on the result.  Operates only within specified intervals.
//
void TsResampleSpline(
    TsSpline *spline,
    double samplingInterval,
    const GfMultiInterval &intervals = GfMultiInterval::GetFullInterval(),
    double maxErrorFraction = .01,
    double maxExtremeFraction = .001);

```

# QUESTIONS

Feedback is welcome on the following questions (or any other aspect of this
proposal).

## Splines of other value types?

See [Value Type Categories](#value-type-categories).

Should USD Anim support splines for value types other than floating-point
scalars?

Among other things, values and tangents of vector-valued splines can't easily be
visualized in a 2D interface, making them less useful for artists.  These kinds
of splines, if they are useful at all, would presumably be used for programmatic
interpolation.

Pixar has not had much use for such splines; for nearly all of our time-varying
usage of such types, time samples would be adequate.

Our guess for now is **no**, we should not support splines of other value types.

## Looping limitations?

See [Looping](#looping).

How should USD Anim handle the following?

**Inner-loop regions.** Presto only supports one inner-loop prototype region per
spline.  An unlimited number of inner-loop regions could theoretically be
supported if that is useful; rules would have to be designed that govern
behavior where echo regions overlap.

**Modes.** Minimum support for both Presto and Maya would be:

- Only Continue mode for inner loops.
- Only Repeat, Reset, and Oscillate modes for extrapolating loops.

We could also support Continue mode in extrapolating loops, and Repeat, Reset,
and Oscillate modes in inner loops.

Our guess for now is **minimal**: at most one inner-loop region, and only the
modes required to support Presto and Maya.

## Reduction metadata?

See [Feature Reduction](#feature-reduction).

When reduction is performed, should metadata be inserted that allows clients to
introspect what has changed?

Our guess for now is **no**, we should not include such metadata.

## Custom data edit policies?

See [Round-Trip Considerations](#round-trip-considerations).

When splines are edited, and per-knot custom data is found on existing knots,
what should happen?  Some kinds of custom data become invalid when their knots
are edited, and others do not.

The minimum is for USD Anim to do nothing - simply to preserve custom data where
it exists.  But we could add other policies that could be tagged or registered
somehow, if that is important to clients.

The answer to this question will depend on both what kinds of custom data
clients store, and how important it is for that custom data to remain valid when
edited by other clients.

Our guess for now is **no**, we should not add additional policies for custom
data editing.

## Time-oriented API?

See [Time Orientation](#time-orientation).

Most spline usage is time-oriented, but more general uses of splines are
possible.  Should the initial version of USD Anim be implemented with generic
vocabulary, referring to "x" instead of "time"?

Our guess for now is **no**, we should not pursue a generic API yet.

## Time snapping?

See [Knots](#knots).

Should USD Anim perform any time snapping?  In theory, knots with tiny time
differences should be allowed to exist, and considered distinct.  But there may
be situations where the possibility of rounding errors dictates that times with
a very small difference should be considered identical.  For example, in a call
like RemoveKnot, what happens when there is a tiny numerical difference between
the specified time and the nearest knot time?  Should the call be ignored, or
should it snap to the nearby time?  If we do want some degree of snapping or
tolerance, we will need to decide epsilon values carefully, allow clients to
configure them, and possibly scale them based on the time width of the segment
under consideration.

Our guess for now is **no**, we should avoid snapping where possible.
