# Proposal to Remove TsSpline Inner Looping

## Context

The `TsSpline` class supports two independent looping mechanisms: **inner
looping** and **extrapolation looping**. Inner looping is a feature of Pixar’s
internal animation software. Extrapolation looping is a feature from Maya.
After careful review of the actual use of inner looping at Pixar, the feature
is rarely used and most of the uses can be replaced with extrapolation looping
instead. Given the complexity of the interaction between these two looping
mechanisms, we’ve decided to remove inner looping.

## Background

Inner looping is defined by a prototype region defined by a start and end
times, counts of the number of times the prototype is repeated before/after
itself, and a value offset for each iteration. These parameters are contained
in a `TsLoopParams` object stored in a `TsSpline`. In order to be active, inner
looping requires an existing knot in the spline at exactly the start time and
one or both of the loop counts must be positive. If these requirements are met,
the starting knot will be duplicated at the end time (with its value offset)
and again at the end of each iteration of the prototype. Any knots that are
stored in the `TsSpline` in the looped regions will be overridden by inner
looping and ignored. Because the start knot will be simply copied to the end of
each iteration, the shape of the spline may change when inner looping is
enabled.

Extrapolation looping is relatively straightforward in concept. When the last
knot is reached, the spline starts over again. We have extended extrapolation
looping to allow looping of a prefix or suffix of the spline rather than the
entire set of knots, but that just makes inner looping even less relevant.

Based on the complexity of supporting both inner and extrapolation looping, the
fact that inner looping only exists today inside Pixar, and the rarity of its
use within Pixar, we’ve decided to deprecate and remove the feature from
`TsSpline`. We recognize that USD files are being used as an archival format as
well as a data transfer format so we will preserve the ability to parse older
scenes that include splines with inner looping but we will ignore and discard
the inner looping information.

## Proposal

We propose a two phase process for removing inner looping. First, deprecate the
inner looping feature and issue warnings when it is used. Second, remove the
feature API completely, retaining just enough internals to bake out inner
looping when reading it from an older file.

### Phase 1 \- Deprecate Inner Looping

First we will deprecate the `TsLoopParams` class as well as the `TsSpline`
methods `SetInnerLoopParams`, `GetInnerLoopParams`, `BakeInnerLoops`,
`GetKnotsWithInnerLoopsBaked`, and `HasInnerLoops`. Use of the class or methods
will generate compiler warnings. Invocation of the methods will generate
runtime warnings (just one warning per method). Inner looping, however, will
continue to work despite the warnings.

### Phase 2 \- Remove Inner Looping

In order to ensure that existing layers can continue to be read, any inner
looping specification that is found will be parsed, but ignored. Splines will
be deserialized as if no inner looping was provided. If the layer is saved, no
inner looping will be serialized. Note that this will change the shape of any
splines that did us inner looping. Warning messages will be generated
identifying any splines that are affected. 

All other public API affordances for inner looping will be removed. This
includes all the deprecated items from Phase 1 as well as all the methods that
deal with inner looping internally. It will no longer be possible to create a
`TsSpline` that uses inner looping. Documentation, and error messages will be
updated to remove references to inner looping, tests will be updated, and
internal classes and methods (e.g. `Ts_SegmentIterator` or
`TsSpline::Breakdown`) will remove inner looping support.

Phase 1 and Phase 2 will be in different OpenUSD release versions so there will
be at least one released version where inner looping is deprecated but not
removed.  
