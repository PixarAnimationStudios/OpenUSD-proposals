# Phase 3A — Schema spot-check findings (2026-04-26)

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

## Category B: Schema ↔ examples divergence (DESIGN DECISION NEEDED)

The schema declares three attributes in a **packed-vector form**, but **all five examples uniformly use a split-per-axis form**. Examples are internally consistent; the schema is not consistent with what's actually in the examples.

### B1: `brep:extent`

**Schema declaration (L553):**
```
uniform double3[] brep:extent   ( doc = """ Brep_ii's bounding box corner pts {XYZmin, XYZmax}. size() = 2 * number of Breps. """ )
```

**Actual usage in all 5 examples:**
```
uniform double2[] brep:xExtent = [(0, 1)]
uniform double2[] brep:yExtent = [(0, 1)]
uniform double2[] brep:zExtent = [(0, 1)]
```

### B2: `face:range`

**Schema declaration (L591):**
```
uniform double2[] face:range   ( doc = """ face_ii's domain range corner pts {UVmin, UVmax}. size() = 2 * number of faces. """ )
```

**Actual usage in all 5 examples:**
```
uniform double2[] face:uRange = [...]
uniform double2[] face:vRange = [...]
```

### B3: `edge:range` and `wireEdge:range`

**Schema declaration (L619, L640):**
```
uniform double[]  edge:range      ( doc = """ Edge_ii's domain interval bounds {paramMin, paramMax}. size() = 2 * number of Edges. """ )
uniform double[]  wireEdge:range  ( doc = """ WireEdge_ii's domain interval bounds ... size() = 2 * number of WireEdges. """ )
```

**Actual usage in all 5 examples:**
```
uniform double2[] edge:range = [(0, 1), (0, 1), ...]
uniform double2[] wireEdge:range = []
```

Examples use `double2[]` with `size() = number of Edges`; schema declares `double[]` with `size() = 2 * number of Edges`. Semantically equivalent but represented differently.

---

### Recommendation

The **examples represent what the WG has actually authored, tested, and rendered**. They are internally consistent across all 5 examples. The schema declarations appear to be stale.

**Three options:**

1. **Conform schema to examples** (preferred): change schema to match the split-per-axis form. This is what the WG is clearly using; schema alignment means downstream tools can actually load the examples against the declared schema. Low risk.
2. **Conform examples to schema**: rewrite all 5 examples to use `brep:extent` / `face:range` / 1D `edge:range`. High churn, high error risk on hand-authored example data, and fights against what the WG already built.
3. **Document both and leave alone**: surface as an open question for the WG. Kicks the can.

**I lean (1).** Confirm before I touch either.

### Rationale for split form in practice

The split `xExtent/yExtent/zExtent` and `uRange/vRange` form has real advantages:
- Each axis is an independent `double2[]` array — simpler composition & overrides.
- Same type (`double2[]`) used for both 1D ranges (edges, faces/U, faces/V) and 2D extent components.
- Maps cleanly onto how most geometry kernels represent parameter ranges per-axis.
- Avoids the `double3[] size = 2*N` footgun (is index 0 min/X or min/Y?).

## Category C: Prose clarity (subjective, low-priority)

- L562 "binormal side" — geometrically inexact for edgeuse orientation. Readers may stumble. Candidate rewording: "the side of the face whose normal is aligned with the edgeuse's traversal direction." Optional.
- L573 `edgeuse:thisRadialEntryType` doc is a wall of text with no blank lines. Render is OK in markdown's code blocks but the USD `doc` field shows dense. Optional prose polish.

## Category D: `prelimUsdSolid` prefix audit

Appears 5 times. All consistent. Per Aaron: keep for now.

## Category E: Property namespace consistency

Checked: `BrepPointAPI`, `BrepCurve3dNurbAPI`, `BrepCurveUvNurbAPI`, `BrepSurfaceNurbAPI` all declare `propertyNamespacePrefix = "brep"` (except `BrepSurfaceNurbAPI` which uses full qualifier inline). Examples confirm composition produces `brep:<instanceName>:<property>` for multipleApply and `brep:<property>` for singleApply. Consistent with how multipleApply works in USD. OK.

---

## Plan

If Aaron approves option (1) for B-class:

**Commit 1 (Category A):** typo/doc-string fixes in the schema.
**Commit 2 (Category B):** align schema declarations to split-per-axis form to match examples.
**Commit 3 (Category C, optional):** prose polish on doc strings.

Each commit ~10–30 schema lines, low blast radius, pushes separately.
