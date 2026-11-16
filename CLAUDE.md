# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A product-development workspace (not a software app) for a modular, motorised toy-train system: market study, locked design decisions, parametric 3D CAD, and cost analysis. All documents, identifiers in prose, comments and script output are in **French** — keep new content in French. The directory is not a git repository.

Numbered folders follow the project phases (`01-etude-de-marche`, `02-prototype-v1`, `03-cao-3d`, `05-business-et-certifications`; `04-electronique-firmware` is planned but does not exist yet). The only code lives in `03-cao-3d/`.

## Commands

The CAD is mid-migration from pure-Python meshes (V1) to **CadQuery** (V2, see `03-cao-3d/decisions-cao-v2.md`). CadQuery lives in a project virtualenv (`.venv`, Homebrew Python 3.13; the system Python 3.9 can't run it). `verifier_stl.py`, the viewer generator and the V1 scripts stay pure stdlib.

```bash
/opt/homebrew/bin/python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time setup
.venv/bin/python 03-cao-3d/generer_rails.py         # V2 rails (CadQuery) → stl/*.stl + step/*.step
python3 03-cao-3d/generer_prototype_rails.py        # V1 track parts not yet ported (no longer writes the straight/slope rails)
python3 03-cao-3d/generer_prototype_locomotive.py   # regenerate the 4 locomotive STLs
python3 03-cao-3d/verifier_stl.py                   # validate every STL in 03-cao-3d/stl/ (exit 1 on any FAIL)
python3 03-cao-3d/verifier_stl.py path/to/one.stl   # validate specific file(s)
python3 03-cao-3d/verifier_stl.py --update-viewer   # validate, then rebuild visualiseur-assemblage.html
python3 03-cao-3d/generer_visualiseur_html.py       # rebuild the viewer only
```

`verifier_stl.py` is the project's test suite: after touching any generator, regenerate, then run it and expect `[PASS]` on all files.

## CAD pipeline architecture

`generer_*.py` → `stl/*.stl` (+ `step/*.step` for V2) → `verifier_stl.py` → `visualiseur-assemblage.html`

### V2 (CadQuery)
- **`cao_commun.py` is the interface contract**: rail constants, the rounded rail profile (2D profile with fillets/chamfers via `polygone_arrondi`, then extruded — far more robust than 3D fillets), Snap-Fit female cavity / male connector, ribbed hollow underside, groove-entry chamfers, micro-ridges, and `exporter()` (validity + `Z_min == 0` check, binary STL + STEP). Every part that mates with track must reuse it.
- Snap-Fit and V-lock geometry are z-dependent; they are built by `solide_par_sections()` — a ruled loft of YZ sections at fixed X stations, which reproduces the V1 piecewise-linear shapes exactly. Keep station lists in sync with the breakpoints of the half-width functions.
- The female cavity is defined as tongue + `JEU_IMPRESSION` from x = 10.2 (fixes a ~0.2 mm V1 overlap). After changing joint geometry, check that two rails joined end to end have zero intersection volume (`a.intersect(a.translate((L,0,0)))`).
- 3D fillets that meet the R2 top fillet (e.g. on vertical joint corners) produce non-manifold STL slivers; `verifier_stl.py` catches this. Prefer fillets in the 2D profile.
- One generator per part family (`generer_rails.py`, …); V1 scripts are retired as their parts get ported.
- `gen_*.py` scripts (e.g. `gen_jauge_calibration.py`) are written by the local model through `outils/deleguer_modele_local.py` (LM Studio `localhost:1234`, `openai/gpt-oss-20b`; `--url` for Ollama). The system prompt is `03-cao-3d/contrat-interface-cadquery.txt` — update it when `cao_commun` changes. Every delegated part needs a functional checker (`outils/controler_*.py`, passed via `--controle`): a watertight STL can still be wrong, and the model only self-corrects when the feedback states what is actually in the part. Record scores in section 5 of `plan-developpement-stl-benchmark.md`.

### V1 (pure Python, being retired)

- **`WatertightMesh`** (in `generer_prototype_rails.py`) is the core of everything. Geometry is built additively from cells (`add_hex`, `add_convex_prism`, `add_quad`, `add_tri`) on vertices snapped to 0.0001 mm. Adding a triangle whose reverse already exists **deletes both** — that is how internal faces between adjacent cells cancel, so solids are unioned by making neighbouring cells share exactly coincident faces. Consequences:
  - Adjacent cells must use identical vertex coordinates on shared faces (same X/Y breakpoints, same `Z_LEVELS`), otherwise the faces do not cancel and the mesh is non-manifold.
  - Adding the same oriented triangle twice raises `ValueError` (overlapping cells).
  - `write_stl()` calls `verify_manifold()` first and refuses to write an open mesh or one with negative signed volume (inverted winding). Faces are CCW seen from outside.
- **`generer_prototype_locomotive.py` imports `WatertightMesh` from `generer_prototype_rails.py`**; the benchmark plan also expects new parts to import `add_female_and_body` / `add_male_snapfit` from it. Treat the rails script as the shared library, and reuse those two helpers for any part that must mate with existing track rather than re-deriving the Snap-Fit geometry.
- Each script has a `build_*()` function per part and a `specs` list in `main()` mapping output filename → mesh → 80-byte ASCII STL header. Adding a part means adding a builder and a `specs` entry.
- **`verifier_stl.py`** re-reads the binary STLs independently of the generators and checks: manifold edges, no zero-area triangles, positive volume, and `Z_min == 0` (part sits on the print bed). It also prints bounding box and an estimated FDM mass.
- **`visualiseur-assemblage.html` is a generated artifact** — never edit it by hand. Its source is the `HTML_TEMPLATE` string in `generer_visualiseur_html.py`, into which every `stl/*.stl` is embedded as Base64 (so it opens by double-click with no server). The template's JavaScript holds a `PART_META` map (label + colour per STL filename) and hand-placed assembly/exploded-view transforms (`makeModelMat(...)`), so a new or renamed STL also needs entries there.

## Mechanical interface contract

Parts are only useful if they mate; these invariants (mm) are shared across both generators and the docs. The module-level constants at the top of `generer_prototype_rails.py` are the source of truth, and section 1 of `03-cao-3d/plan-developpement-stl-benchmark.md` restates the full contract.

- Rail profile 40 × 12, grooves 6 wide × 3 deep (floor at z = 9.0), gauge 25.5 centre-to-centre (wooden-track standard).
- Snap-Fit joint with 45° V-groove vertical lock between z = 4.5 and 7.5; `PRINT_CLEARANCE = 0.20` per face.
- Locomotive axle at z = 21.0 above rail base; wheels Ø 24.0 (flange Ø 27.6); central pinion 12 teeth Ø 16.8, so tooth bottom is at z = 12.6: +0.6 clearance over normal rails (12.0), over the action-tile lowered channel (12.4), and 1.4 engagement into the "Funky" rack (14.0).
- Big-block compatibility: 15.9 mm grid, Ø 9.4 studs.
- Printability: overhangs ≤ 45°, supports avoided (only `loco_chassis_inferieur.stl` needs them).

## Keeping documents in sync

Dimensions and part lists are duplicated across several files. When a part or a dimension changes, update all of:

- `README.md` (structure section lists every script and STL by name, and the "11 STL" count),
- `03-cao-3d/guide-impression-et-assemblage-v1.md` (inventory table with overall dimensions, mesh clearances, test protocol),
- `02-prototype-v1/decisions-design-v1.md` (locked V1 design decisions — treat as the specification; do not change a decision without the user asking),
- `05-business-et-certifications/analyse-couts-de-production-bom.md` if print mass/volume or the BOM is affected,
- the generators' module docstrings, and the regenerated viewer.

Use `verifier_stl.py` output as the source for dimensions quoted in the docs.
