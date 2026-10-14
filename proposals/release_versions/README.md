# OpenUSD Release Versions

Copyright &copy; 2026, Pixar Animation Studios, version 1.0

## Background

OpenUSD releases are commonly described using a [CalVer](https://calver.org/) scheme,
like "v26.08". However, OpenUSD internally follows a [SemVer](https://semver.org/)
scheme using major, minor, and patch version numbers and publishes these values
through its C++ and Python API. For example, for the "v26.08" release, the values
available through the API are:

| C++ API           | Value |
| ----------------- | ----- |
| PXR_MAJOR_VERSION | 0     |
| PXR_MINOR_VERSION | 26    |
| PXR_PATCH_VERSION | 8     |
| PXR_VERSION       | 2608  |

| Python API        | Value      |
| ----------------- | ---------- |
| Usd.GetVersion()  | (0, 26, 8) |

Per SemVer, the major version has been set to 0 since OpenUSD's initial open
source release to reflect its current lack of API stability guarantees across
releases. Because of this, the major version is typically ignored when spelling
OpenUSD versions outside of code. For example, the GitHub repository and
CHANGELOG.md spell versions numbers as "v26.08" instead of "v0.26.08". Note
also that the `usd-core` PyPI package uses version numbers like "26.8".

A significant drawback to this scheme is that there is no way to identify
an OpenUSD patch release like "v25.05.01" in code. This has not been reported
as a major issue, likely because patch releases are infrequent: there have been
only 5 out of 52 total releases in OpenUSD's history. However, given
continued interest in security fixes for prior releases and long-term
support branches, we anticipate the number of patch releases will grow,
making it more important to be able to identify such releases in code.

## Proposal

We propose fully adopting CalVer for OpenUSD. OpenUSD versions will be based
on when they are released, following the scheme:

`YY.0M.PATCH` 

That is, the two-digit year and zero-padded month of the release, followed by a
non-zero-padded patch version beginning at 0 for the initial release and
incrementing for each patch release. We also reserve the right to add a modifier
to the version (e.g. `27.02.0-stable`) although we currently do not have any use
cases for this.

This version will be used in documentation as well as on the GitHub repository.
For example, the first release for 26.08 would be tagged as `v26.08.0`, and the
first patch release for that line would be tagged as `v26.08.1`.

In C++, `PXR_VERSION_YEAR`, `PXR_VERSION_MONTH`, and `PXR_VERSION_PATCH` macros
would be added to represent the separate components of the version.
`PXR_VERSION_FULL` would be added to represent the version in a single integer
value, computed as:

`patch + (MM * 1000) + (YY * 100000)`

This scheme reserves three digits for the patch version, which imposes a limit
of 999 patch releases per version. We do not expect to publish anywhere near
this many patches.

The existing `PXR_MAJOR_VERSION`, `PXR_MINOR_VERSION`, and `PXR_PATCH_VERSION`
macros would be deprecated, although their values would continue to be updated
for some period to maintain backwards compatibility.

The existing `PXR_VERSION` macro would _not_ be deprecated. It still represents
the expected combination of `PXR_VERSION_YEAR` and `PXR_VERSION_MONTH` and is
simpler for clients that don't care about patch versions. Avoiding this
deprecation makes adoption easier.

In Python, a new `Usd.GetFullVersion()` function would be added that returned
a (year, month, patch) version tuple, parallel to the `PXR_VERSION_FULL` macro
in C++. The `Usd.GetVersion()` function would _not_ be deprecated, similar to
how `PXR_VERSION` is not deprecated in C++. However, the tuple it returns will
always have a "0" as the first element, for backwards compatibility. We also
choose not to include the new patch version in the tuple to be parallel with
`PXR_VERSION`, to leave the size of the tuple unchanged to ensure no behavior
change, and to encourage folks to use the new `Usd.GetFullVersion()` function
instead. The intent is to have `Usd.GetVersion()` operate this way for at
least several releases. In the future, we could consider updating it so that
it matches `Usd.GetFullVersion()`. Although that would not be a fully
backwards-compatible change, comparisons against older versions would still
work as expected since the new value produced by that function would be
strictly greater than the previous values.

This approach is appealing because it aligns the API with the version numbers
users are already familiar with. It would remove confusion about the versioning
scheme that OpenUSD uses and, for better or worse, signify that the version
number does not convey any meaning beyond chronological order. If in the future
there were releases with API stability guarantees or other semantics, those
would need to be explicitly documented somewhere (which perhaps should be done
regardless).

The versioning scheme for the `usd-core` PyPI module would remain unchanged.
Only non-zero patch versions would be included in the package version number.
For example, the package for the "v26.08.0" release would be `usd-core-26.8`,
and "v26.08.1" would be `usd-core-26.8.1`. Note that the zero-padding for the
month is dropped because it's not supported in PyPI's versioning scheme.

Since this approach deprecates the individual `PXR_*_VERSION` macros, client
code will need to be updated in the future when the old API is removed. However,
the hope is that there are few clients of these individual macros; a cursory
Google search yields relatively few hits (although this is not conclusive).

Summarizing the new version API, for "v26.08.1":

| C++ API           | Value    |
| ----------------- | -------- |
| PXR_VERSION_YEAR  | 26       |
| PXR_VERSION_MONTH | 8        |
| PXR_VERSION_PATCH | 1        |
| PXR_VERSION       | 2608     |
| PXR_VERSION_FULL  | 2608001  |
| **Deprecated**    |          |
| PXR_MAJOR_VERSION | 0        |
| PXR_MINOR_VERSION | 26       |
| PXR_PATCH_VERSION | 8        |

| Python API           | Value         |
| -------------------- | ------------- |
| Usd.GetVersion()     | (0, 26, 8)    |
| Usd.GetFullVersion() | (26, 8, 1)    |

## Alternatives

#### Add "tweak" version number

An alternative we considered was introducing a fourth version number to
OpenUSD's version API, called the "tweak" version since "patch" is already
used. The "tweak" name is adopted from the version specification used by
[CMake's `project` function](https://cmake.org/cmake/help/latest/command/project.html#command:project).

Under this alternative, the C++ API would gain a new `PXR_TWEAK_VERSION`
macro containing the tweak version, as well as a `PXR_VERSION_FULL` macro
that combines all four version numbers in a single value. The existing
`PXR_VERSION` macro would be retained for backwards compatibility and
continue to work as it does today, but clients would need to switch to
using the `PXR_VERSION_FULL` macro to distinguish between patch releases.

In Python, the `Usd.GetVersion()` function would be updated to return a
tuple containing four values instead of three. Existing code that compares
the result of this function to a tuple would continue to work as expected.

For example, for the "v26.08.1" release:

| C++ API           | Value    |
| ----------------- | -------- |
| PXR_MAJOR_VERSION | 0        |
| PXR_MINOR_VERSION | 26       |
| PXR_PATCH_VERSION | 8        |
| PXR_TWEAK_VERSION | 1        |
| PXR_VERSION       | 2608     |
| PXR_VERSION_FULL  | 2608001  |

| Python API        | Value         |
| ----------------- | ------------- |
| Usd.GetVersion()  | (0, 26, 8, 1) |

This approach is a smaller change and does not introduce the code deprecation
cost from the proposal above, although as mentioned we believe that cost to
be relatively minor.

This approach also preserves the ability per SemVer to communicate API stability
guarantees in the version number: if OpenUSD ever did provide some guarantee,
the major version could be bumped to a non-zero number.

However, there are other factors related to the CalVer/SemVer inconsistency
that could prevent us from doing this anyway. For example, let's say that
OpenUSD began to provide API stability as of the 27.02 release. This would
most obviously be represented by bumping the major version to 1, which would
then be represented in code as `(major=1, minor=27, patch=2, tweak=0)`. But
how would this be spelled outside of code? "v1.27.02" is the most obvious
answer, but this would incorrectly be considered an earlier version than
the "v26.08" release. This would also impact the `usd-core` PyPI package:
"usd-core-1.27.2" would be considered newer than "usd-core-26.8".

One way to avoid this problem would be to set the major version to 27, giving
us `(major=27, minor=2, patch=0, tweak=0)`. That would resolve the issues
above, but using the release year as the major version would require us to
only make API-breaking changes with the first release of the year, which is
too restrictive.

We could maintain our CalVer/SemVer inconsistency: we would spell this version
as "v27.02" and the PyPI package would be "usd-core-27.2".  But then we'd lose
the primary benefit of SemVer since the major version number wouldn't be visible
outside of code. And if that's the case, then there's no reason to keep using
SemVer at all.

#### Change the major and minor version numbers to the year and month

Another alternative we considered was to switch to CalVer in the code but
reuse the existing API to avoid deprecating code.

For example, for the "v26.08.1" release the version API would be:

| C++ API           | Value    |
| ----------------- | -------- |
| PXR_MAJOR_VERSION | 26       |
| PXR_MINOR_VERSION | 8        |
| PXR_PATCH_VERSION | 1        |
| PXR_VERSION       | 2608     |
| PXR_VERSION_FULL  | 2608001  |

| Python API        | Value      |
| ----------------- | ---------- |
| Usd.GetVersion()  | (26, 8, 1) |

Under this approach, the existing major/minor/patch versions would no longer
be interpreted as SemVer and would instead encode a CalVer version. Although
this avoids deprecating code, the change in values could introduce backwards
compatibility issues. Additionally, continuing to use the major/minor/patch
terminology could confuse users into thinking these values represented a
SemVer version and interpreting the major version being greater than 0 as
an API stability guarantee.
