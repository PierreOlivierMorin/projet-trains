#!/usr/bin/env python3
"""Générateur CadQuery de la famille « locomotive » (V2).

Pièces portées :
- loco_roue_24mm              : roue Ø 24 SANS boudin (guidée par les parois de rainure, comme le bois),
                                gorge pour pneu TPU / joint torique, moyeu-entretoise vers le palier
- loco_pignon_central_essieu  : pignon d'escalade 12 dents (Ø tête 16,8), engrène la crémaillère Funky

Le châssis et la coque restent en V1 (generer_prototype_locomotive.py) : leur architecture est à
reconcevoir (voir decisions-cao-v2.md §8).

Repère d'impression : chaque pièce est posée à plat, axe de rotation vertical (Z).
Usage : .venv/bin/python 03-cao-3d/generer_locomotive.py
"""

import math

import cadquery as cq

import cao_commun as c

# ---------------------------------------------------------------------------
# Essieu et roue (cotes de voie : fond de rainure z = 9, essieu z = 21)
# ---------------------------------------------------------------------------
Z_ESSIEU = 21.0
ALESAGE = 3.0                      # Tige Ø 3 mm ; à ajuster d'après la jauge (trous 2,95–3,10)
ROUE_RAYON = Z_ESSIEU - c.Z_FOND_RAINURE        # 12,0 : bande de roulement sur le fond de rainure
ROUE_LARGEUR = 5.0                 # Rainure de 6 mm -> 0,5 mm de jeu de chaque côté
GORGE_RAYON = 10.9                 # Fond de gorge du pneu (joint torique 14 × 2 ou TPU)
GORGE_LARGEUR = 1.8
MOYEU_RAYON = 4.2
MOYEU_SAILLIE = 1.9                # Entretoise jusqu'à la face du palier (|y| = 17,2) côté extérieur
CONGE_ROUE = 0.5


def roue() -> cq.Workplane:
    """Roue posée face intérieure sur le plateau ; le moyeu dépasse vers le haut (côté palier)."""
    jante = (
        cq.Workplane("XY").circle(ROUE_RAYON).extrude(ROUE_LARGEUR)
        .faces(">Z").edges().fillet(CONGE_ROUE)
        .faces("<Z").edges().chamfer(0.4)
    )
    z_gorge = (ROUE_LARGEUR - GORGE_LARGEUR) / 2.0
    gorge = (
        cq.Workplane("XY").workplane(offset=z_gorge)
        .circle(ROUE_RAYON + 1).circle(GORGE_RAYON)
        .extrude(GORGE_LARGEUR)
    )
    moyeu = cq.Workplane("XY").workplane(offset=ROUE_LARGEUR - 0.1).circle(MOYEU_RAYON).extrude(MOYEU_SAILLIE + 0.1)
    piece = jante.cut(gorge).union(moyeu)
    return piece.cut(cq.Workplane("XY").circle(ALESAGE / 2.0).extrude(20).translate((0, 0, -1)))


# ---------------------------------------------------------------------------
# Pignon d'escalade
# ---------------------------------------------------------------------------
PIGNON_DENTS = 12
PIGNON_R_PIED = 6.70
PIGNON_R_TETE = 8.40               # Bas des dents à z = 21 - 8,4 = 12,6 : +0,6 au-dessus d'un rail standard
PIGNON_EPAISSEUR = 3.0


def pignon() -> cq.Workplane:
    """Pignon à dents trapézoïdales (profil V1 : flancs sur 1/8 de pas, tête sur 2/8)."""
    pas = 2 * math.pi / PIGNON_DENTS
    sous = pas / 8.0
    pts = []
    for k in range(PIGNON_DENTS):
        a = k * pas
        for i, r in ((2, PIGNON_R_PIED), (3, PIGNON_R_TETE), (5, PIGNON_R_TETE), (6, PIGNON_R_PIED)):
            pts.append((r * math.cos(a + i * sous), r * math.sin(a + i * sous)))
    corps = cq.Workplane("XY").polyline(pts).close().extrude(PIGNON_EPAISSEUR)
    return corps.cut(cq.Workplane("XY").circle(ALESAGE / 2.0).extrude(10).translate((0, 0, -1)))


def main() -> None:
    c.exporter(roue(), "loco_roue_24mm")
    c.exporter(pignon(), "loco_pignon_central_essieu")


if __name__ == "__main__":
    main()
