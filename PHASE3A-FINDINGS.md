# Phase 3A — Schema spot-check findings (2026-04-26, updated 2026-04-27)

Review of `§3 Schema` (`schema.usda` block, lines 536–944) against `§4 Examples` and `§2.4` prose.

## Category A: Typos and doc-string fixes (uncontroversial, will land without checking)

| Line | Issue | Fix |
| --- | --- | --- |
| 563 | `binormal side connecting to a face..` | Drop double period |
| 620 | `brep:facuseCount` in doc | → `brep:faceuseCount` |
| 678 | Doc references `BrepEdgeCurveNurbAPI` (does not exist) | → `BrepCurve3dNurbAPI` |
| 733 | `geometrty` | → `geometry` |
| 759 | `geomtery` | → `geometry` |
| 813 | `connetions` | → `connections` |
| 882 | `analagous` | → `analogous` |
| 921 | `wireEdge:vertexIndices` doc copy-pasted from edge: references `Edge_ii:Curve(Edge:Range(...))` | → `WireEdge_ii:Curve(WireEdge:Range(...))` |
| 926 | `size() = number of Edges.` in `wireEdge:vertexIndices` doc | → `number of WireEdges` |

## Category B: Schema ↔ examples divergence — examples are stale, schema is current

The schema declares three attributes in a **packed-vector form**; all five examples use the older **split-per-axis form**. Examples are internally consistent with each other but inconsistent with the current schema.

### Provenance (from git log on `origin/SolidModels-editorial0`)

Commit [`44fb3c1`](https://github.com/aousd/Geom-WG-OpenUSD-Proposals/commit/44fb3c1) — **"small schema updates"** by Joe Umhoefer on 2026-04-03 — flipped these three attributes from split-per-axis to packed form **on the schema side only**. The examples were not updated in the same commit, leaving them stale.

Direction of the change in `44fb3c1`:

```
-    uniform double2[] brep:xExtent         ( doc = "{Xmin, Xmax} for brep_ii's bounding extent. size() = number of Breps." )
-    uniform double2[] brep:yExtent         ( doc = "{Ymin, Ymax} for brep_ii's bounding extent. size() = number of Breps." )
-    uniform double2[] brep:zExtent         ( doc = "{Zmin, Zmax} for brep_ii's bounding extent. size() = number of Breps." )
+    uniform double3[] brep:extent          ( doc = "Brep_ii's bounding box corner pts {XYZmin, XYZmax}. size() = 2 * number of Breps." )

-    uniform double2[] face:uRange          ( doc = "{Umin, Umax} for face_ii's u domain bounding interval. size() = number of faces." )
-    uniform double2[] face:vRange          ( doc = "{Vmin, Vmax} for face_ii's v domain bounding interval. size() = number of faces." )
+    uniform double2[] face:range           ( doc = "face_ii's domain range corner pts {UVmin, UVmax}. size() = 2 * number of faces." )

-    uniform double2[] edge:range           ( doc = "{min, max} for edge_ii's domain interval. size() = number of Edges." )
+    uniform double[]  edge:range           ( doc = "Edge_ii's domain interval bounds {paramMin, paramMax}. size() = 2 * number of Edges." )

-    uniform double2[] wireEdge:range       ( doc = "{min, max} for wireEdge_ii's domain interval. size() = number of Edges." )
+    uniform double[]  wireEdge:range       ( doc = "WireEdge_ii's domain interval bounds {paramMin, paramMax}. size() = 2 * number of WireEdges." )
```

### B1: `brep:extent`

**Schema (current, post-`44fb3c1`):**
```
uniform double3[] brep:extent   ( doc = """ Brep_ii's bounding box corner pts {XYZmin, XYZmax}. size() = 2 * number of Breps. """ )
```

**Examples (stale, pre-`44fb3c1` form):**
```
uniform double2[] brep:xExtent = [(0, 1)]
uniform double2[] brep:yExtent = [(0, 1)]
uniform double2[] brep:zExtent = [(0, 1)]
```

### B2: `face:range`

**Schema (current):**
```
uniform double2[] face:range   ( doc = """ face_ii's domain range corner pts {UVmin, UVmax}. size() = 2 * number of faces. """ )
```

**Examples (stale):**
```
uniform double2[] face:uRange = [...]
uniform double2[] face:vRange = [...]
```

### B3: `edge:range` and `wireEdge:range`

**Schema (current):**
```
uniform double[]  edge:range      ( doc = """ Edge_ii's domain interval bounds {paramMin, paramMax}. size() = 2 * number of Edges. """ )
uniform double[]  wireEdge:range  ( doc = """ WireEdge_ii's domain interval bounds ... size() = 2 * number of WireEdges. """ )
```

**Examples (stale):**
```
uniform double2[] edge:range = [(0, 1), (0, 1), ...]
uniform double2[] wireEdge:range = []
```

---

### Recommendation

**Update the examples to match the current schema.** The `44fb3c1` intent is clear: consolidate from three split-per-axis attributes to one packed `brep:extent`; consolidate `uRange`/`vRange` into one `face:range`; flatten `edge:range` from a `double2[]` of pairs to a `double[]` with size = 2·n. Examples simply didn't get updated alongside.

**Action on branch (pending Joe/Martin confirmation):**

1. Rewrite each of the five examples' top-level extent/range attribute blocks to match the current schema:
   - `brep:xExtent/yExtent/zExtent` trio → single `brep:extent = [(Xmin, Ymin, Zmin), (Xmax, Ymax, Zmax)]` with `size = 2·nBreps`.
   - `face:uRange/vRange` pair → single `face:range = [(Umin, Vmin), (Umax, Vmax), ...]` with `size = 2·nFaces`.
   - `edge:range` from `double2[]` of `(min, max)` pairs → `double[]` of `[min, max, min, max, ...]` with `size = 2·nEdges`. Same for `wireEdge:range`.

2. Verify topology indices after the rewrite (the values themselves don't change, just the layout).

## Category C: Prose clarity (subjective, low-priority)

- L562 "binormal side" in `edgeuse:orientationType.same` — geometrically imprecise for a 1D curve's side relative to a face. Ask Joe/Martin for the term they actually want ("face's normal direction", "Frenet binormal", or something radial-edge-specific).
- L573 `edgeuse:thisRadialEntryType` doc is a wall of text with no blank lines — content is correct, rendering dense. Optional prose polish.

## Category D: `prelimUsdSolid` prefix audit

Appears 5 times. All consistent. Per Aaron: keep for now.

## Category E: Property namespace consistency

Checked: `BrepPointAPI`, `BrepCurve3dNurbAPI`, `BrepCurveUvNurbAPI`, `BrepSurfaceNurbAPI` all declare `propertyNamespacePrefix = "brep"`. Examples confirm composition produces `brep:<instanceName>:<property>` for multipleApply and `brep:<property>` for singleApply. Consistent with how multipleApply works in USD. OK.

---

## Plan

Awaiting Joe/Martin confirmation via Aaron that `44fb3c1` is intentional (expected outcome).

**Commit 1 (Category A):** typo/doc-string fixes in the schema.
**Commit 2 (Category B):** rewrite the 5 examples' `brep:*Extent`, `face:*Range`, `edge:range`, `wireEdge:range` attributes to match the current schema.
**Commit 3 (Category C, optional):** prose polish on doc strings after Joe/Martin weigh in on the "binormal" wording.

Each commit low blast radius, pushes separately.
