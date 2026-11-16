#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script : gen_jauge_calibration.py
Génère la pièce de calibration des tolérances pour les Snap‑Fit et l’axe des roues.
"""

import cadquery as cq
import cao_commun as c

# --------------------------------------------------------------------------- #
# 1. Base plate (plein) – hauteur exactement 12 mm, positionnée sur x=[0,55]
# --------------------------------------------------------------------------- #

base = (
    cq.Workplane("XY")
    .box(55, 80, 12)          # centre à l’origine
    .translate((27.5, 0, 6))   # décalage pour que minX=0 et zmin=0
)

# --------------------------------------------------------------------------- #
# 2. Arrondis avant découpes
# --------------------------------------------------------------------------- #

# Fillet des 4 arêtes verticales extérieures (r = 3.0)
base = base.edges("|Z").fillet(3.0)

# Chanfrein de l’arête basse tout autour (c.CHANFREIN_BAS)
bottom_edges = base.faces("-Z").edges()
base = bottom_edges.chamfer(c.CHANFREIN_BAS)

# --------------------------------------------------------------------------- #
# 3. Femelles Snap‑Fit ouvertes
# --------------------------------------------------------------------------- #

femelle_specs = [
    (-30, 0.10),
    (-10, 0.15),
    ( 10, 0.20),
    ( 30, 0.25),
]

for y_pos, jeu in femelle_specs:
    femelle = (
        c.cavite_femelle(jeu=jeu)
        .translate((0, y_pos, 0))   # x=0 relative à la plaque
    )
    base = base.cut(femelle)

# --------------------------------------------------------------------------- #
# 4. Trous verticaux traversants (axe des roues)
# --------------------------------------------------------------------------- #

hole_specs = [
    (-22.5, 2.95),
    ( -7.5, 3.00),
    (  7.5, 3.05),
    ( 22.5, 3.10),
]

for y_pos, dia in hole_specs:
    # Cylindre traversant de la base
    hole = (
        cq.Workplane("XY")
        .center(42, y_pos)   # x=42 relative à la plaque
        .circle(dia / 2)
        .extrude(20)                # dépasse largement le plateau (0 → 12)
        .translate((0, 0, -5))      # centrez sur la hauteur du plateau
    )
    base = base.cut(hole)

# --------------------------------------------------------------------------- #
# 5. Marquages gravés sur le dessus
# --------------------------------------------------------------------------- #

text_specs = [
    # (x, y, texte, taille)
    (26, -30, "10", 5),
    (26, -10, "15", 5),
    (26,  10, "20", 5),
    (26,  30, "25", 5),
    (50, -22.5, "95", 3.5),
    (50,  -7.5, "00", 3.5),
    (50,   7.5, "05", 3.5),
    (50,  22.5, "10", 3.5),
]

for x_pos, y_pos, txt, size in text_specs:
    mark = (
        cq.Workplane("XY")
        .workplane(offset=12)          # sur le dessus
        .center(x_pos, y_pos)
        .text(txt, size, -0.6)         # profondeur 0.6 mm vers l’intérieur
    )
    base = base.cut(mark)

# --------------------------------------------------------------------------- #
# 6. S'assurer que la pièce repose sur z = 0
# --------------------------------------------------------------------------- #

bb = base.val().BoundingBox()
if bb.zmin < 0:
    base = base.translate((0, 0, -bb.zmin))

# --------------------------------------------------------------------------- #
# 7. Exporter la pièce finale
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    c.exporter(base, "jauge_calibration_tolerances")
