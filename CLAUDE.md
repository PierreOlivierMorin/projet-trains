# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A product-development workspace (not a software app) for a modular, motorised toy-train system: market study, locked design decisions, parametric 3D CAD, and cost analysis. All documents, identifiers in prose, comments and script output are in **French** — keep new content in French. The directory is a git repository (initialised 16 nov. 2026; the first commit holds the V1 pure-Python CAD).

Numbered folders follow the project phases (`01-etude-de-marche`, `02-prototype-v1`, `03-cao-3d`, `05-business-et-certifications`; `04-electronique-firmware` is planned but does not exist yet). The only code lives in `03-cao-3d/`.

## Commands

All CAD is **CadQuery** (V2, see `03-cao-3d/decisions-cao-v2.md` and `decisions-locomotive-v2.md`); the V1 pure-Python mesh generators were removed (still in git history). CadQuery lives in a project virtualenv (`.venv`, Homebrew Python 3.13; the system Python 3.9 can't run it). `verifier_stl.py` and the viewer generator stay pure stdlib.

```bash
/opt/homebrew/bin/python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time setup
.venv/bin/python 03-cao-3d/generer_rails.py         # V2 rails (CadQuery) → stl/*.stl + step/*.step
.venv/bin/python 03-cao-3d/generer_locomotive.py   # test-chassis loco parts + scenes-visualiseur.json
.venv/bin/python 03-cao-3d/gen_jauge_calibration.py # calibration gauge (written by the local model)
.venv/bin/python outils/controler_locomotive.py     # loco assembly checks: internal clashes, straight, R=180 curve, Funky rack
.venv/bin/python outils/controler_jauge.py          # functional checks of the gauge
python3 03-cao-3d/verifier_stl.py                   # validate every STL in 03-cao-3d/stl/ (exit 1 on any FAIL)
python3 03-cao-3d/verifier_stl.py path/to/one.stl   # validate specific file(s)
python3 03-cao-3d/verifier_stl.py --update-viewer   # validate, then rebuild visualiseur-assemblage.html
python3 03-cao-3d/generer_visualiseur_html.py       # rebuild the viewer only
```

`verifier_stl.py` (mesh validity) plus the `outils/controler_*.py` functional checks are the test suite: after touching a generator, regenerate, run them, and expect `[PASS]` / `CONFORME`.

## CAD pipeline architecture

`generer_*.py` → `stl/*.stl` (+ `step/*.step` for V2) → `verifier_stl.py` → `visualiseur-assemblage.html`

### V2 (CadQuery)
- **`cao_commun.py` is the interface contract**: rail constants, the rounded rail profile (2D profile with fillets/chamfers via `polygone_arrondi`, then extruded — far more robust than 3D fillets), Snap-Fit female cavity / male connector, ribbed hollow underside, groove-entry chamfers, micro-ridges, and `exporter()` (validity + `Z_min == 0` check, binary STL + STEP). Every part that mates with track must reuse it.
- Snap-Fit and V-lock geometry are z-dependent; they are built by `solide_par_sections()` — a ruled loft of YZ sections at fixed X stations, which reproduces the V1 piecewise-linear shapes exactly. Keep station lists in sync with the breakpoints of the half-width functions.
- The female cavity is defined as tongue + `JEU_IMPRESSION` from x = 10.2 (fixes a ~0.2 mm V1 overlap). After changing joint geometry, check that two rails joined end to end have zero intersection volume (`a.intersect(a.translate((L,0,0)))`).
- 3D fillets that meet the R2 top fillet (e.g. on vertical joint corners) produce non-manifold STL slivers; `verifier_stl.py` catches this. Prefer fillets in the 2D profile.
- One generator per part family (`generer_rails.py`, …); V1 scripts are retired as their parts get ported. Curved rails are a revolve of the same 2D profile around the curvature centre (`rail_courbe`), so fillets match the straights exactly; `troncon_droit` builds straight sections with optional female/male ends.
- `gen_*.py` scripts (e.g. `gen_jauge_calibration.py`) are written by the local model through `outils/deleguer_modele_local.py` (LM Studio `localhost:1234`, `openai/gpt-oss-20b`; `--url` for Ollama). The system prompt is `03-cao-3d/contrat-interface-cadquery.txt` — update it when `cao_commun` changes. Every delegated part needs a functional checker (`outils/controler_*.py`, passed via `--controle`): a watertight STL can still be wrong, and the model only self-corrects when the feedback states what is actually in the part. Record scores in section 5 of `plan-developpement-stl-benchmark.md`.

### Locomotive (`generer_locomotive.py`)
- Loco frame: X forward with origin midway between axles (front/driven axle x = +23, rear/free axle x = −23), Z from rail base (axles at z = 21). `assemblage()` returns every part placed in that frame; `outils/controler_locomotive.py` uses it to check pairwise clashes (with an allow-list for press fits and meshing gears) and to place the loco on a straight rail, on a R = 180 curve (axles on the track centreline, rigid chassis along the chord) and on Funky rails.
- Parts are exported flat for printing (`a_plat`) or in their own axis-Z frame (wheels, gears); `scenes_visualiseur()` writes `scenes-visualiseur.json` with the transforms back to the world frame, which the viewer embeds. When moving a part, update `assemblage()` and `scenes_visualiseur()` together.
- `MOTEUR` holds *assumed* N20 worm-gearmotor dimensions; only `loco_support_moteur` depends on them, so real measurements change that one part. The gear pair (14 T / 20 T, m 1) and the output-shaft position derive from `ANGLE_ARBRE` and `entraxe()`.
- Under-floor clearances are driven by the track: floor at z = 12.6 (rail top 12), centre channel |y| ≤ 2.4 up to z = 14.6 (Funky rack at 14), magnets beside the channel over the Funky steel strips.

### Shared
- **`verifier_stl.py`** re-reads the binary STLs independently of the generators and checks: manifold edges, no zero-area triangles, positive volume, and `Z_min == 0` (part sits on the print bed). It also prints bounding box and an estimated FDM mass.
- **`visualiseur-assemblage.html` is a generated artifact** — never edit it by hand. Its source is the `HTML_TEMPLATE` string in `generer_visualiseur_html.py`, into which every `stl/*.stl` is embedded as Base64 and `scenes-visualiseur.json` as the assembly/circuit scenes. `PART_META` holds a label + colour per STL. The template had a missing IIFE opener until 16 nov. 2026 — after editing it, extract the `<script>` and run `node --check` on it.

## Mechanical interface contract

Parts are only useful if they mate; these invariants (mm) are shared across generators and docs. The constants at the top of `cao_commun.py` (track) and `generer_locomotive.py` (loco) are the source of truth; `03-cao-3d/contrat-interface-cadquery.txt` restates the contract for the local model.

- Rail profile 40 × 12, grooves 6 wide × 3 deep (floor at z = 9.0), gauge 25.5 centre-to-centre (wooden-track standard).
- Snap-Fit joint with 45° V-groove vertical lock between z = 4.5 and 7.5; `JEU_IMPRESSION = 0.20` per face (to be confirmed by the printed gauge).
- Locomotive axle at z = 21.0 above rail base; wheels Ø 24.0 × 3.5 mm without flange (guided by the 6 mm groove; 5 mm binds on R = 180 curves); central pinion 12 teeth Ø 16.8, so tooth bottom is at z = 12.6: +0.6 over standard/wood rails (12.0) and 1.4 engagement into the "Funky" rack (14.0).
- Big-block compatibility: 15.9 mm grid, Ø 9.4 studs.
- Printability: overhangs ≤ 45°, no supports; max part size 240 mm (Bambu X1C bed). Sealed magnets/NFC tags use print pauses.

## Keeping documents in sync

Dimensions and part lists are duplicated across several files. When a part or a dimension changes, update all of:

- `README.md` (structure section lists every script by name),
- `03-cao-3d/guide-impression-et-assemblage-v1.md` (inventory with dimensions, print pauses, hardware list, checked clearances, test protocol),
- `03-cao-3d/decisions-cao-v2.md` / `decisions-locomotive-v2.md` (V2 decisions and the deviations found while implementing them),
- `02-prototype-v1/decisions-design-v1.md` (locked V1 design decisions — treat as the specification; do not change a decision without the user asking),
- `05-business-et-certifications/analyse-couts-de-production-bom.md` if print mass/volume or the BOM is affected,
- the generators' module docstrings, and the regenerated viewer.

Use `verifier_stl.py` output as the source for dimensions quoted in the docs.
