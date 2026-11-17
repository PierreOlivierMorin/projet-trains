#!/usr/bin/env python3
"""Contrôle d'assemblage de la locomotive châssis-test (repère loco de generer_locomotive.py).

1. Interférences entre pièces (hors emmanchements voulus : tiges dans roues/engrenages/pignon,
   engrenages entre eux, arbre moteur dans son engrenage et son réducteur).
2. Entraxe des engrenages et dégagements au-dessus du rail.
3. Loco posée sur un rail droit, puis sur une courbe R = 180 (essieux sur la ligne de voie,
   châssis rigide orienté selon la corde) : aucune pièce ne doit toucher le rail, sauf le contact
   roue / fond de rainure (vérifié en relevant la loco de 0,02 mm).
4. Même test en courbe avec des roues de 5 mm, pour confirmer le coincement qui a motivé 3,5 mm.

Usage : .venv/bin/python outils/controler_locomotive.py
"""

import itertools
import math
import sys
from pathlib import Path

CAO = Path(__file__).resolve().parent.parent / "03-cao-3d"
sys.path.insert(0, str(CAO))
import cao_commun as c  # noqa: E402
import generer_locomotive as g  # noqa: E402
import generer_rails as gr  # noqa: E402

PERMIS = {
    frozenset(p) for p in [
        ("tige_av", "roue_av_g"), ("tige_av", "roue_av_d"), ("tige_ar", "roue_ar_g"), ("tige_ar", "roue_ar_d"),
        ("tige_av", "pignon"), ("tige_av", "engr_essieu"), ("engr_essieu", "engr_moteur"),
        ("arbre_moteur", "engr_moteur"), ("arbre_moteur", "moteur"), ("moteur", "support"),
        ("plateau", "chassis"),
    ]
}
ok = True


def vol(w) -> float:
    return sum(s.Volume() for s in w.solids().vals())


def verdict(cond: bool, msg: str) -> None:
    global ok
    ok &= cond
    print(("[OK]    " if cond else "[ÉCHEC] ") + msg)


def poser(pieces: dict, angle_deg: float, x: float, y: float, dz: float = 0.0) -> dict:
    return {
        k: v.rotate((0, 0, 0), (0, 0, 1), angle_deg).translate((x, y, dz)) for k, v in pieces.items()
    }


def contre_voie(pieces: dict, voie, titre: str) -> None:
    touches = {k: vol(voie.intersect(v)) for k, v in pieces.items()}
    hors_roues = {k: t for k, t in touches.items() if t > 1e-3 and not k.startswith("roue")}
    roues = {k: t for k, t in touches.items() if k.startswith("roue")}
    verdict(not hors_roues, f"{titre} : aucune pièce hors roues ne touche la voie {hors_roues or ''}")
    verdict(max(roues.values()) < 1e-3, f"{titre} : roues sans interférence (max {max(roues.values()):.4f} mm3)")


def main() -> int:
    pieces = g.assemblage()

    print("--- Interférences internes")
    for (a, pa), (b, pb) in itertools.combinations(pieces.items(), 2):
        if frozenset((a, b)) in PERMIS:
            continue
        v = vol(pa.intersect(pb))
        if v > 1e-3:
            verdict(False, f"{a} / {b} : {v:.3f} mm3")
    verdict(True, "contrôle des paires terminé")

    print("--- Cotes")
    e = g.entraxe()
    attendu = g.MODULE * (g.DENTS_ESSIEU + g.DENTS_MOTEUR) / 2
    verdict(abs(e - attendu - g.JEU_ENTRAXE) < 1e-6, f"entraxe {e:.2f} mm (primitif {attendu:.1f} + jeu {g.JEU_ENTRAXE})")
    z_min = {k: v.val().BoundingBox().zmin for k, v in pieces.items() if not k.startswith(("roue", "tige"))}
    bas = min(z_min, key=z_min.get)
    verdict(z_min[bas] >= c.RAIL_HAUTEUR + 0.5, f"point le plus bas hors roues : {bas} à z = {z_min[bas]:.2f} (rail à 12)")
    z_max = max(v.val().BoundingBox().zmax for v in pieces.values())
    print(f"[INFO]  hauteur totale (piles comprises) : {z_max:.1f} mm")

    print("--- Sur rail droit")
    droit = c.rail_droit(100).union(c.rail_droit(100).translate((100, 0, 0))).translate((-100, 0, 0))
    contre_voie(poser(pieces, 0, 0, 0, 0.02), droit, "droit")

    print("--- En courbe R = 180")
    courbe = c.rail_courbe()
    a_mid = 22.5
    phi = math.degrees(math.asin(-g.X_ESSIEU_AR / 180.0))
    cx, cy = c.FEMELLE_LONGUEUR, 180.0
    rc = 180.0 * math.cos(math.radians(phi))
    mx = cx + rc * math.sin(math.radians(a_mid))
    my = cy - rc * math.cos(math.radians(a_mid))
    contre_voie(poser(pieces, a_mid, mx, my, 0.02), courbe, f"courbe (braquage {phi:.1f}°)")

    print("--- Sur rail Funky (crémaillère)")
    funky = gr.rail_funky().union(gr.rail_funky().translate((100, 0, 0))).translate((-100, 0, 0))
    posee = poser(pieces, 0, 0, 0, 0.02)
    touches = {k: vol(funky.intersect(v)) for k, v in posee.items()}
    autres = {k: round(t, 3) for k, t in touches.items() if t > 1e-3 and not k.startswith("roue") and k != "pignon"}
    verdict(not autres, f"Funky : seul le pignon touche la crémaillère {autres or ''}")
    prof = gr.FUNKY_DENT_Z[1] - (g.Z_ESSIEU - 8.4)
    verdict(prof >= 1.0, f"Funky : engrènement du pignon {prof:.1f} mm sous le sommet de la crémaillère (z = 14)")
    print(f"[INFO]  recouvrement de denture dans cette position : {touches['pignon']:.2f} mm3 (dent dans un creux = 0)")

    print("--- Contre-épreuve : roues de 5 mm en courbe")
    g.ROUE_LARGEUR = 5.0
    g.Y_ROUE_INT = c.ECARTEMENT / 2.0 - 2.5
    larges = {k: v for k, v in g.assemblage().items() if k.startswith("roue")}
    t = max(vol(courbe.intersect(v)) for v in poser(larges, a_mid, mx, my, 0.02).values())
    print(f"[INFO]  roues de 5 mm : interférence max avec la courbe {t:.3f} mm3 "
          f"({'coince, confirme le choix de 3,5 mm' if t > 1e-3 else 'ne coince pas'})")

    print("LOCOMOTIVE CONFORME" if ok else "LOCOMOTIVE NON CONFORME")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
