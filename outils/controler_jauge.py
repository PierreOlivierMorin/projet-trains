#!/usr/bin/env python3
"""Contrôle fonctionnel de la jauge de calibration (au-delà de l'étanchéité du STL).

Vérifie sur le solide STEP : dimensions, un seul solide, chaque prise femelle au bon jeu
(la prise du jeu demandé est entièrement vide, une prise 0,03 mm plus large ne l'est pas),
l'embout mâle standard entre sans interférence, et le diamètre des 4 trous.

Usage : .venv/bin/python outils/controler_jauge.py
"""

import sys
from pathlib import Path

import cadquery as cq

CAO = Path(__file__).resolve().parent.parent / "03-cao-3d"
sys.path.insert(0, str(CAO))
import cao_commun as c  # noqa: E402

PRISES = {-30.0: 0.10, -10.0: 0.15, 10.0: 0.20, 30.0: 0.25}
TROUS = {-22.5: 2.95, -7.5: 3.00, 7.5: 3.05, 22.5: 3.10}


def vol(w: cq.Workplane) -> float:
    return sum(s.Volume() for s in w.solids().vals())


def main() -> int:
    chemin = sys.argv[1] if len(sys.argv) > 1 else str(CAO / "step" / "jauge_calibration_tolerances.step")
    piece = cq.importers.importStep(chemin)
    ok = True

    def verdict(cond: bool, msg: str) -> None:
        nonlocal ok
        ok &= cond
        print(("[OK]   " if cond else "[ÉCHEC] ") + msg)

    solides = piece.solids().vals()
    verdict(len(solides) == 1, f"un seul solide ({len(solides)})")
    bb = piece.val().BoundingBox()
    verdict(
        abs(bb.xlen - 55) < 0.05 and abs(bb.ylen - 80) < 0.05 and abs(bb.zlen - 12) < 0.05,
        f"dimensions {bb.xlen:.2f} × {bb.ylen:.2f} × {bb.zlen:.2f} (attendu 55 × 80 × 12)",
    )

    for y, jeu in PRISES.items():
        vide = vol(piece.intersect(c.cavite_femelle(jeu).translate((0, y, 0))))
        plus_large = c.cavite_femelle(jeu + 0.03).cut(c.cavite_femelle(jeu)).translate((0, y, 0))
        matiere = vol(piece.intersect(plus_large))
        male = vol(piece.intersect(c.connecteur_male(0.0).translate((0, y, 0))))
        verdict(
            vide < 0.01 and matiere > 0.5 and male < 0.01,
            f"prise y={y:+.0f} jeu {jeu:.2f} : reste dans la prise {vide:.3f} mm3, "
            f"matière à +0,03 {matiere:.2f} mm3, interférence embout mâle {male:.3f} mm3",
        )

    cylindres = [f for f in piece.faces().vals() if f.geomType() == "CYLINDER"]
    petits = [
        f"(x={f.Center().x:.1f}, y={f.Center().y:.1f}, Ø {2 * f._geomAdaptor().Cylinder().Radius():.2f})"
        for f in cylindres
        if f._geomAdaptor().Cylinder().Radius() < 2.0
    ]
    print(
        "[INFO] perçages réellement présents dans la pièce : "
        + (", ".join(petits) if petits else "AUCUN (le volume découpé ne traverse pas la plaque z ∈ [0, 12])")
    )
    for y, d in TROUS.items():
        trouve = [
            f for f in cylindres
            if abs(f.Center().x - 42) < 0.3 and abs(f.Center().y - y) < 0.3
        ]
        diam = 2 * trouve[0]._geomAdaptor().Cylinder().Radius() if trouve else None
        verdict(
            diam is not None and abs(diam - d) < 0.005,
            f"trou y={y:+.1f} : Ø {diam if diam is None else round(diam, 3)} (attendu {d})",
        )

    autres = [
        f for f in cylindres
        if abs(f.Center().x - 42) > 0.3 and f._geomAdaptor().Cylinder().Radius() < 2.0
    ]
    verdict(not autres, f"aucun perçage parasite ({len(autres)} trouvé(s))")

    # Gravures : de la matière doit manquer sous le dessus (z ∈ [11,4 ; 12]) à chaque marquage
    marquages = [(26.0, y, 5.0) for y in PRISES] + [(50.0, y, 3.5) for y in TROUS]
    for x, y, taille in marquages:
        zone = cq.Workplane("XY").box(taille * 2.2, taille * 1.6, 0.6, centered=(True, True, False))
        zone = zone.translate((x, y, 11.4))
        retire = zone.val().Volume() - vol(piece.intersect(zone))
        verdict(retire > 0.3, f"gravure en ({x:.0f}, {y:+.1f}) : {retire:.2f} mm3 retirés sous le dessus")

    print("JAUGE CONFORME" if ok else "JAUGE NON CONFORME")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
