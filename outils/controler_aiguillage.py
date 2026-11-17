#!/usr/bin/env python3
"""Contrôle fonctionnel des aiguillages (generer_aiguillages.py).

1. Longueur de la voie directe = celle qui ferme le plan du circuit (plan_circuit.L_AIG).
2. Pour chaque variante : lame et levier, dans les deux positions, sans interférence avec le corps.
3. Jonctions : un rail standard emboîté sur le tronc et sur chaque sortie sans interférence
   (genre de chaque extrémité conforme à la variante).
4. Guidage (gauche et droite) : des roues Ø 24 × 3,5 (centrées sur l'axe des rainures, relevées
   de 0,02 mm) parcourent les deux itinéraires.
   - lame en position directe : itinéraire direct libre, itinéraire dévié bloqué par la lame ;
   - lame en position déviée : l'inverse.
   La roue extérieure (autre rainure, cœur de croisement) ne doit jamais toucher le corps.
5. Talonnage : angle sous lequel une roue arrivant par la branche fermée rencontre la lame.

Usage : .venv/bin/python outils/controler_aiguillage.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "03-cao-3d"))
sys.path.insert(0, str(RACINE / "outils"))
import cadquery as cq  # noqa: E402

import cao_commun as c  # noqa: E402
import generer_aiguillages as g  # noqa: E402
import plan_circuit as plan  # noqa: E402

ok = True
ROUE_R, ROUE_L = 12.0, 3.5
PAS = 4.0


def verdict(cond: bool, msg: str) -> None:
    global ok
    ok &= cond
    print(("[OK]    " if cond else "[ÉCHEC] ") + msg)


def vol(w) -> float:
    return sum(s.Volume() for s in w.solids().vals())


def poser(piece: cq.Workplane, x: float, y: float, a: float) -> cq.Workplane:
    return piece.rotate((0, 0, 0), (0, 0, 1), a).translate((x, y, 0))


# ---------------------------------------------------------------------------
# Itinéraires (repère gauche) : points de l'axe de voie (x, y, cap en degrés)
# ---------------------------------------------------------------------------
def itineraire_direct() -> list[tuple[float, float, float]]:
    n = int((g.L_DIRECTE - 10) // PAS)
    return [(5.0 + PAS * k, 0.0, 0.0) for k in range(n)]


def itineraire_devie() -> list[tuple[float, float, float]]:
    pts = [(x, 0.0, 0.0) for x in (5.0, 9.0, 13.0)]
    n = int(g.R * math.radians(g.ANGLE) // PAS)
    for k in range(n + 1):
        t = math.radians(g.ANGLE * k / n)
        pts.append((g.X_ARC + g.R * math.sin(t), g.R * (1 - math.cos(t)), math.degrees(t)))
    return pts


def roue(x: float, y: float, cap: float, cote: int) -> cq.Workplane:
    """Roue (cylindre) de la file `cote` (+1 intérieure/gauche, -1 extérieure) pour l'essieu en (x, y)."""
    a = math.radians(cap)
    yr = cote * c.ECARTEMENT / 2
    cx, cy = x - yr * math.sin(a), y + yr * math.cos(a)
    cyl = (cq.Workplane("XZ", origin=(0, ROUE_L / 2, 21.02)).circle(ROUE_R).extrude(ROUE_L))
    return cyl.rotate((0, 0, 0), (0, 0, 1), cap).translate((cx, cy, 0))


def parcours(obstacle: cq.Workplane, itin, cote: int, miroir: bool) -> tuple[float, float | None]:
    """Interférence max d'une file de roues avec `obstacle` et abscisse du premier contact."""
    pire, premier = 0.0, None
    for x, y, cap in itin:
        if miroir:
            y, cap = -y, -cap
        cote_reel = -cote if miroir else cote
        v = vol(obstacle.intersect(roue(x, y, cap, cote_reel)))
        if v > 1e-3 and premier is None:
            premier = x
        pire = max(pire, v)
    return pire, premier


def main() -> int:
    print("--- Cotes")
    verdict(abs(g.L_DIRECTE - plan.L_AIG) < 1e-6, f"voie directe {g.L_DIRECTE:.2f} mm = plan_circuit.L_AIG")
    verdict(abs(g.PIVOT[1] - (c.Y_RAINURE_EXT + g.y_bas(g.PIVOT[0])) / 2) < 0.05,
            f"pivot au milieu de l'îlot (îlot {g.y_bas(g.PIVOT[0]) - c.Y_RAINURE_EXT:.2f} mm à x = {g.PIVOT[0]})")

    for nom, (tronc_f, droite) in g.VARIANTES.items():
        print(f"--- {nom}")
        corps = g.corps(tronc_f, droite)
        for deviee in (False, True):
            pos = "déviée" if deviee else "directe"
            lame, levier = g.placer_lame(droite, deviee), g.placer_levier(droite, deviee)
            verdict(vol(corps.intersect(lame)) < 1e-3, f"lame en position {pos} libre dans son logement")
            verdict(vol(corps.intersect(levier)) < 1e-3, f"levier en position {pos} libre (évidement et lumière)")

        # Jonctions : rail standard emboîté sur chaque extrémité
        s = -1 if droite else 1
        rail = c.rail_droit(100.0)
        sorties = [(g.L_DIRECTE, 0.0, 0.0), (g.DX, s * g.DY, s * g.ANGLE)]
        if tronc_f:   # Tronc femelle : rail arrivant par son mâle ; sorties mâles : rail par sa prise
            raccords = [poser(rail, -100.0, 0, 0)] + [poser(rail, x, y, a) for x, y, a in sorties]
        else:
            retourne = rail.rotate((0, 0, 0), (0, 0, 1), 180)
            raccords = [retourne] + [poser(retourne.translate((100.0, 0, 0)), x, y, a) for x, y, a in sorties]
        for (lib, r) in zip(("tronc", "sortie directe", "sortie déviée"), raccords):
            v = vol(corps.intersect(r))
            verdict(v < 1e-3, f"jonction {lib} ({'F' if (lib == 'tronc') == tronc_f else 'M'}) : interférence {v:.4f} mm3")

        if nom == "aiguillage_droit_tronc_f":
            continue   # Guidage identique à aiguillage_droit_tronc_m (même partie centrale)
        for deviee in (False, True):
            lame = g.placer_lame(droite, deviee)
            ouvert, ferme = (itineraire_devie(), itineraire_direct()) if deviee else (itineraire_direct(), itineraire_devie())
            pos = "déviée" if deviee else "directe"
            for cote, lib in ((1, "intérieure"), (-1, "extérieure")):
                v, _ = parcours(corps, ouvert, cote, droite)
                verdict(v < 1e-3, f"lame {pos} : itinéraire ouvert, roue {lib} sans contact avec le corps ({v:.4f} mm3)")
            v, _ = parcours(lame, ouvert, 1, droite)
            verdict(v < 1e-3, f"lame {pos} : itinéraire ouvert, roue intérieure sans contact avec la lame")
            v, x0 = parcours(lame, ferme, 1, droite)
            verdict(v > 1.0, f"lame {pos} : itinéraire fermé bloqué par la lame "
                             f"(premier contact à x = {x0:.0f}, recouvrement {v:.1f} mm3)")
            v, _ = parcours(corps, ferme, -1, droite)
            verdict(v < 1e-3, f"lame {pos} : roue extérieure sur l'itinéraire fermé sans contact avec le corps")

    print("--- Talonnage (roue arrivant par la branche fermée)")
    # Position déviée : la face basse de la lame descend vers le tronc avec la pente de la rotation
    print(f"[INFO]  lame déviée, train venant de la sortie directe : face d'attaque inclinée de "
          f"{g.LAME_ANGLE:.0f}° sur la rainure droite -> pousse la lame vers la position directe")
    a0 = math.degrees(math.asin((g.PIVOT[0] - 22.0 - g.X_ARC) / g.R_INT_HAUT))
    a1 = math.degrees(math.asin((g.PIVOT[0] - g.X_ARC) / g.R_INT_HAUT))
    print(f"[INFO]  lame directe, train venant de la sortie déviée : la rainure courbe arrive à {a0:.0f}–{a1:.0f}° "
          f"sur la face haute de la lame -> pousse la lame vers la position déviée")

    print("AIGUILLAGES CONFORMES" if ok else "AIGUILLAGES NON CONFORMES")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
