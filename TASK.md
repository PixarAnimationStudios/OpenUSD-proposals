# TASK.md — Proposal 2 (UsdSolid) Cleanup

**Branch:** `aluk/brep-schema-draft` (stacked on `aluk/brep-schema`)
**File:** `proposals/UsdSolid/README.md` — 1534 lines
**Status:** Phase 1 audit complete. No content changes yet.
**Relationship:** Companion to Proposal 1 (#11) at `proposals/cad_geometry/README.md`.

---

## Phase 1 — Section-by-section audit

Legend: **KEEP** · **REWRITE** · **CUT** · **DEFER** · **VERIFY**

### Front matter (lines 1–43)
- **L1** Status badge — KEEP.
- **L3–8** Title + opening paragraph — KEEP. Already frames this as a schema proposal, not a problem statement.
- **L10–37** Contents (TOC) — KEEP; will need regeneration after edits.
- **L39–46** Horizontal rule + transition — KEEP.

### § 0. Preamble (lines 47–58)
- **L47–51** Intro paragraph — KEEP.
- **L53** AOUSD WG + community feedback line — KEEP.
- **L55** "A collection of potential use cases is maintained separately" — **VERIFY**: this is the private Google Doc referenced in Appendix A.9. Either summarize inline (per A.9) or cut the dangling reference. Currently dangling.
- **L57** Images note — **KEEP but flag**: images in `images/` need to be confirmed to render once pushed to the org repo. Already flagged inline; keep the note until images verified.
- **L61–64** Brep↔Mesh deferral paragraph — KEEP. This is the scoping lock and correctly points to Proposal 1's "derive on demand" framing. ✅ Consistent with scoping decision.

### § 1. Purpose and scope (lines 69–118)
- **§1.1 Problem statement (L71–75)** — KEEP. Our dedup edit from PR branch. Points to Proposal 1 correctly.
- **§1.1 OpenUSD-stakeholders paragraph (L77–79)** — KEEP. Useful carve-out. USD Profiles link — **VERIFY** URL still resolves.
- **§1.2 Proposed approach (L81–93)** — KEEP in essence, but **REWRITE** lightly:
  - L82–85 radial edge rationale — KEEP.
  - L86 Weiler thesis URL — **VERIFY**: URL has two different hosts in the sentence (`webserver2.tecgraf.puc-rio.br` twice with different prefixes `https://` and `http://`). Pick one; prefer https.
  - L88–89 PRC / geometry types reference — KEEP.
  - L91–93 "Section 2.1 contains a catalog..." and "we intend to add them soon" — REWRITE to remove the "soon" language; sounds like an active TODO left dangling.
- **§1.3 Glossary (L95–117)** — KEEP. Thorough. **VERIFY** consistency with Proposal 1's glossary (Proposal 1 has its own BRep glossary in Appendix A). Note: Proposal 2 should be the authoritative glossary for schema-level terms (Edgeuse, Faceuse, Loopuse, radial edge), Proposal 1 glossary is for concepts (exact geometry, derive-on-demand). **Check for divergence and reconcile.**

### § 2. Overall design concerns (lines 119–142)
- **L121–127** Opening paragraph on region partitioning — KEEP. Slight duplication with §1.3 glossary ("Region", "Solid"), acceptable.
- **L128–135** "Several Brep models were considered... radial edge chosen" — KEEP. Lee 1999 citation correct.
- **L137–142** Closing paragraph introducing BrepArray + BrepAPI — KEEP. Clean transition.

### § 2.1 Shape (lines 143–193)
- **L145–148** Intro on Breps as parametric mappings — KEEP.
- **L150–156** Existing USD primitive issues — KEEP. Solid critique.
- **L158–164** "In this proposal each geometry type..." — KEEP.
- **L166–169** PRC certification + need for extensive attributes — KEEP. **VERIFY**: ISO 14739-1:2014 is correct (per my recollection; confirm against source).
- **L171–190** Curves/Surfaces/Volumes table — KEEP. **VERIFY** table rendering (markdown tables in GH should be fine).

### § 2.2 Topology and "use" (lines 195–236)
- KEEP in full. This is the expository section teaching the radial edge model. Flows cleanly. No TODOs.

### § 2.3 Brep (lines 237–274)
- KEEP in full. Same expository role as §2.2. Strong metaphor ("stain glass window").
- **L272** Object model diagram reference (`images/image0.png`) — **VERIFY**: image is in `images/` and will render on GH.

### § 2.4 USD Implementation (lines 276–341)
- **L278–283** Opening: single IsA schema + applied APIs — KEEP.
- **L285–287** Per-face properties motivation — KEEP.
- **L289–296** List of 4 required modifications — KEEP. Numbered list renders oddly (`1.`, `1.`, `1.`) — **REWRITE** to `1., 2., 3., 4.` or use markdown list.
- **§2.4.1 _UsdSolidBrepArray_ (L298–307)** — KEEP. Clear.
- **§2.4.2 Instancing (L308–310)** — KEEP. Short but sufficient at this stage.
- **§2.4.3 Brep Geometry in USD (L312–318)** — KEEP.
- **§2.4.4 Geometry type extensions (L320–327)** — KEEP. **VERIFY**: PRC spec URL (`docs.techsoft3d.com/.../SC2N570-PRC-WD.pdf`) — confirm it resolves and is the right ISO reference.
- **§2.4.5 Modeling Breps on a UsdStage (L329–332)** — KEEP. Short, flags future work.
- **§2.4.6 Trimming Curves (L334–339)** — KEEP.

### § 2.5 Flexible design possibilities (lines 341–375)
- **L343–347 TODO comment** — **RESOLVE**: this is one of the two flagged TODOs. Need to write the BrepArray rationale paragraph here (weave in the FAQ content per Appendix A.8 & A.6). The FAQ framing is clear: BrepArray is not an assembly/scenegraph hierarchy; it is a flexible list of parts; 1:1 is default; packing supports rigidly connected bodies with uniform material properties when prim count matters; sparse overrides for variants is future work.
- **L349–351** "We enumerate some of the choices here" intro — keep as transition, but ensure the new rationale paragraph precedes it.
- **§2.5.1 One Brep per BrepArray (L352–361)** — KEEP.
- **§2.5.2 One Assembly per BrepArray (L363–369)** — KEEP.
- **§2.5.3 One Model per BrepArray (L371–375)** — KEEP.

### § 2.6 Other implementations considered (lines 377–431)
- **L379–380** Intro — KEEP.
- **§2.6.1 One UsdPrim per geometry object (L382–397)** — **RESOLVE TODO**: weave in FAQ framing that the proposal supports *use* of CAD designs, not CAD *authoring* in USD. Place as opening framing before the practical performance rationale.
- **§2.6.2 One UsdPrim per Brep (L399–404)** — KEEP.
- **§2.6.3 Breps as an Applied API (L406–419)** — KEEP. Honest tradeoff discussion.
- **§2.6.4 Breps as a black box (L422–431)** — KEEP, but **VERIFY link target**. Section references `[Section 1.2](#12-why-not-use-existing-formats-like-step-or-treat-breps-as-opaque-data)` — this anchor does NOT exist in our current §1.2. In the dedup, we replaced §1.2 with the "Proposed approach" content; STEP/black-box rationale now lives in Proposal 1. **Broken link to fix.** Options: (a) point to Proposal 1's existing-mechanisms section, (b) inline a compact summary, (c) both.

### § 2.7 Assemblies (lines 433–444)
- KEEP. Flags scope exclusion clearly. **VERIFY** `kind` cross-reference doesn't need a doc link.

### § 2.8 Tolerance (lines 446–454)
- KEEP.

### § 2.9 Validation (lines 456–470)
- KEEP.
- **§2.9.1 Rules and requirements (L472–518)** — KEEP. Check list renders correctly (again `1., 1., 1.` pattern may be intentional markdown auto-numbering; renders fine on GH).

### § 3 Schema (lines 520–1000)
- **L520** Section header — KEEP. Note: header in README is `# **3 Schema**` (missing period) — TOC has `3. Schema`. **REWRITE** header to `# **3. Schema**` for consistency.
- **L521–1000** schema.usda block in `<details>` collapse — KEEP body, **VERIFY**:
  - Syntactic validity (can feed through `usdchecker` offline if pxr tools available; otherwise visual pass).
  - `libraryName = "prelimUsdSolid"` prefix — is this intentional "preliminary" marker? Check with Aaron before pushing final. Consistent in schema header and apiSchemaCanOnlyApplyTo lists (`PrelimUsdSolidBrepArray`).
  - All attribute descriptions cross-reference correctly to sections.
- No restructuring needed at this phase.

### § 4 Examples (lines ~1000–1470)
- **§4.1 Cube (L~1015)** — KEEP. Image reference `images/cube.png`.
- **§4.2 Non-manifold cubes (L~1081)** — KEEP. Image `images/cube2.png`.
- **§4.3 Cube With Internal Void (L~1148)** — KEEP. Image `images/cubevoid.png`.
- **§4.4 BrepArray with multiple Breps (L~1217)** — KEEP. Image `images/BrepArray.png`.
- **§4.5 Brep with materials applied to faces (L~1297)** — KEEP. Image `images/FaceMaterials.png`.
- **Appendix A.3 observation (already in doc):** examples lack walkthrough narration. Consider adding 1–2 sentence lead-ins, but low priority. OK to DEFER.

### § 5 References (lines ~1470–1474)
- **Only Lee 1999 cited.** — **REWRITE**: add Weiler 1986 (already URL'd in §1.2), PRC ISO 14739-1:2014, STEP ISO 10303, Kevin Weiler's thesis. Short pass, high value.

### Appendix: Notes on Potential Restructuring (lines ~1476–1534)
- **MUST CUT before PR.** Editor-notes-to-self section. Resolved items should be deleted; unresolved items should either be acted on or tracked elsewhere.
- Status of each subitem:
  - **A.1** Align with AOUSD template — partially done (problem statement + proposed approach + glossary exist). Risks section still missing. **Action:** add a brief Risks section (can be short), then cut A.1.
  - **A.2** Split design narrative — mostly addressed by dedup + Proposal 1 split. Cut.
  - **A.3** Narrate examples — low-priority improvement. DEFER to post-PR iteration; cut from appendix.
  - **A.4** Add Risks section — **ACT**: write a compact Risks section before §3. Cut A.4.
  - **A.5** Add Open Questions section — **ACT**: collect scattered questions (assembly representation, Brep↔Mesh deferred per Proposal 1, constraint systems, STEP/PRC migration, `kind` interaction). Short section before §3. Cut A.5. Note: Steve Ghee's N:1 back-reference approach is useful — preserve in the Open Questions section.
  - **A.6** Merge FAQ content — being handled by the §2.5 and §2.6.1 TODOs. Cut A.6 after resolution.
  - **A.7** Cross-industry motivation — Proposal 1 now owns this. Cut A.7.
  - **A.8** FAQ content — same as A.6. Will be resolved by §2.5 + §2.6.1 TODO work. Cut.
  - **A.9** Summarize use case doc inline — Proposal 1 already covers use cases. Cut A.9, or fold one sentence of use-case pointer into §0 Preamble ("For detailed cross-industry use cases, see the companion problem statement"). Cleanup: delete the dangling L55 "maintained separately" sentence.

### FAQ file (proposals/UsdSolid/FAQ/Brep Schema proposal FAQ.md)
- Per MEMORY: content absorbed into proposals, file still exists.
- **Decide:** delete in Phase 2, or replace body with one-line redirect: "FAQ content has been incorporated into the main proposal and companion problem statement (#11). See proposals/UsdSolid/README.md §2.5 and §2.6.1, and proposals/cad_geometry/README.md."

---

## Cross-cutting audit items

### Anonymization / naming
- Scan for person names, company names, internal stakeholder references that shouldn't ship publicly. Known inheritances:
  - Steve Ghee mention in Appendix A.5 — acceptable to cite by name in Open Questions if attribution is appropriate; cross-check with Aaron. Flag for decision.
  - "Geometry Working Group" / "AOUSD" — OK.
- **Decision needed:** name-attribution policy for Proposal 2 Open Questions.

### Brep↔Mesh correlation
- Referenced in §0 Preamble (L61–64) — defers correctly to Proposal 1's derive-on-demand framing. ✅
- Steve Ghee's N:1 back-reference idea currently only in Appendix A.5. Move to Open Questions section or leave out entirely (consistent with "defer correlation"). Lean: brief mention in Open Questions, framed as "one candidate approach raised in discussion."

### Cross-references with Proposal 1
- **§0 Preamble L63** — points to `../cad_geometry/README.md`. ✅
- **§1.1 L73** — points to `../cad_geometry/README.md`. ✅
- **§2.6.4 L428** broken anchor to old §1.2 — needs rewrite.
- **Add:** a brief "Relationship to problem statement" subsection at the top of §1, mirroring Proposal 1's "Relationship to companion proposal" pattern. Current §1.1 already does most of the work; could be promoted or given its own subheader.

### Broken / suspect URLs to verify
1. Weiler thesis (two different prefixes in same sentence — normalize)
2. PRC spec PDF at docs.techsoft3d.com
3. USD Profiles proposal URL
4. `#12-why-not-use-existing-formats-like-step-or-treat-breps-as-opaque-data` anchor (broken)

### Line-count
- Current: 1534 lines.
- Expected cuts: Appendix (~60 lines), FAQ file decision (file-level), a few editorial TODOs and redundant sentences (~20 lines).
- Expected additions: BrepArray rationale (§2.5 TODO, ~15 lines), Use-of-designs framing (§2.6.1 TODO, ~10 lines), Risks (~20 lines), Open Questions (~25 lines), Relationship-to-problem-statement (~5 lines), References expansion (~10 lines).
- **Net estimate:** ~1540 lines after cleanup — roughly neutral. Schema block (~480 lines) and examples (~470 lines) dominate; prose will shrink slightly.
- **Main-body target proposal:** ≤1200 (everything before §3 Schema). Current main body is ~520 lines. We have headroom.

---

## Phase 2 — Execution order (proposed, for approval before running)

1. **Appendix cleanup** — absorb A.1/A.4/A.5 content, cut the rest. One commit.
2. **FAQ absorption + TODO resolution** — §2.5 and §2.6.1. One commit.
3. **Broken link & editorial fixes** — §2.6.4 anchor, §2.4 numbered list, §3 header period, Weiler URL, §5 references expansion. One commit.
4. **Preamble cleanup** — resolve or cut L55 dangling "use case doc maintained separately." One commit.
5. **Glossary reconcile with Proposal 1** — check and adjust if divergent. One commit (may be empty).
6. **FAQ file disposition** — delete or redirect. One commit.
7. **Image verification** — separate pass, visual check once pushed.
8. **Checkpoint push** to `origin/aluk/brep-schema-draft`. No PR.

---

## Aaron's answers (2026-04-26) — decisions locked

1. **FAQ file**: all relevant content must land in Proposal 1 or Proposal 2; delete the FAQ file after absorption.
2. **Steve Ghee**: attribute by name in Open Questions.
3. **Private Google Doc (`AOUSD Geometry WG CAD and BIM use cases (WIP)`)**: do not reference. Inline the needed content. **Local PDF confirmed present** at `/home/horde/.openclaw/media/inbound/AOUSD_Geometry_WG_CAD_and_BIM_use_cases_WIP_.pdf---*.pdf` (v0.2, 5 Dec 2024, authors: Thorsten Hertel + Alex Fuchs). Extracted to `/tmp/usecases.txt`.
4. **Prelim prefix** in schema (`prelimUsdSolid` / `PrelimUsdSolidBrepArray`): still open — confirm before final PR. Not blocking Phase 2.
5. ~~Images verification~~ — **confirmed**: `image0.png`, `cube.png`, `cube2.png`, `cubevoid.png`, `BrepArray.png`, `FaceMaterials.png` all present in `proposals/UsdSolid/images/`. Preamble note about images not being committed can be cut during Phase 2.

## Use case doc — absorption plan

The PDF contains 13 use cases across BIM/AEC and MFG. Most of the MFG cases (which argue specifically for Brep over tessellation) are perfect for Proposal 1; the BIM/AEC cases mostly argue for USD-as-interchange and are broader than Brep-specific motivation.

**Into Proposal 1 (`proposals/cad_geometry/README.md`)** — strengthen the industry use cases section:
- MFG: Exact collision check after detecting soft clashes (Brep intersection vs mesh approximation)
- MFG: Access to precise measurement (center of a hole doesn't exist in polygonal rep)
- MFG: General LOD Handling (re-mesh Brep surfaces with control over feature tolerances)
- MFG: Re-tesselate to skip unwanted details (reversibility without data loss)
- MFG: PMI data (exact thread geometry vs cosmetic texture map)
- BIM: Clash detection across multi-trade projects (loses IP in proprietary formats today)
- Attribute v0.2, 5 Dec 2024, authors Thorsten Hertel + Alex Fuchs (AOUSD Geometry WG).

**Into Proposal 2 (`proposals/UsdSolid/README.md`)** — lighter touch; Proposal 2 is schema-focused:
- MFG: Access to constraint data — belongs in §2.7 Assemblies or Open Questions (motivates the mates/constraints transfer and reinforces why assemblies are future work).
- Cross-reference: §0 Preamble mentions `[collection of potential use cases maintained separately]` — **replace** with a single line pointing to Proposal 1's expanded use cases section (once added). Drop the dangling "contact the Geometry WG for access" sentence.

**Important:** since absorption touches Proposal 1, that's either (a) a separate commit on `aluk/exact-geometry-problem-statement` (already PR #11) or (b) folded into this branch with a separate PR conversation. Need Aaron's call before touching Proposal 1 — PR #11 is already under review. **Lean:** hold Proposal 1 edits until Phase 2 of Proposal 2 is done, then batch the use-case additions into a single follow-up commit to #11 (or a fresh PR on top).

## FAQ absorption — explicit mapping

| FAQ question | Destination |
| --- | --- |
| Why not represent Breps as black box? | Already in Proposal 1 (`existing-mechanisms` section). Nothing new to add. Delete FAQ entry. |
| BrepArray as array / scenegraph conflation | Proposal 2 §2.5 intro — resolves the existing TODO comment. |
| Can BrepArray be separated into smaller prims? | Proposal 2 §2.6.1 — resolves the existing TODO comment. |
| Why not STEP? | Already in Proposal 1. Delete FAQ entry. |
| Sparse overrides for Brep variants (buried in Q1 answer) | Proposal 2 Open Questions section. |
| Per-BrepArray/per-Brep/per-topology cross-domain annotation (buried in Q1 answer) | Already covered in Proposal 2 §2.4 opening. Verify and skip. |
