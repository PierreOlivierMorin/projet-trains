#!/usr/bin/env python3
"""Générateur CadQuery de la famille « rails » (V2, finition jouet en bois premium).

Pièces :
- rail_droit_100mm_snapfit      : rail droit 100 mm évidé à nervures, Snap-Fit + verrou en V
- rail_cote_100mm_strie         : même rail avec micro-stries de traction au fond des rainures
- rail_courbe_45deg_snapfit     : courbe 45° à gauche, R = 180 mm (8 pièces = cercle)
- adaptateur_rail_bois          : prise Snap-Fit femelle -> cheville mâle de train en bois (Ø 11,2)
- rail_funky_cremaillere_captif : rail « Anti-Gravité » (crémaillère, loges acier, glissières captives 45°)
- pilier_verrouillable_duplo    : pilier H = 50 mm (berceau à rebords, base compatible gros blocs)
- pilier_verrouillable_25mm     : même pilier, H = 25 mm

Usage : .venv/bin/python 03-cao-3d/generer_rails.py
"""

import math

import cadquery as cq

import cao_commun as c

# ---------------------------------------------------------------------------
# Adaptateur vers rail en bois
# ---------------------------------------------------------------------------
BOIS_CORPS = 50.0
BOIS_COL_DEMI_LARGEUR = 3.0
BOIS_TETE_RAYON = 5.6        # Cheville standard Ø 11,2 mm
BOIS_TETE_X = 61.0


def adaptateur_rail_bois() -> cq.Workplane:
    corps = c.troncon_droit(BOIS_CORPS, femelle=True, male=False, evide=False)
    dx = math.sqrt(BOIS_TETE_RAYON**2 - BOIS_COL_DEMI_LARGEUR**2)
    col = (
        cq.Workplane("XY")
        .box(BOIS_TETE_X - dx - BOIS_CORPS + 1.0, 2 * BOIS_COL_DEMI_LARGEUR, c.RAIL_HAUTEUR, centered=(False, True, False))
        .translate((BOIS_CORPS - 0.5, 0, 0))
    )
    tete = cq.Workplane("XY").center(BOIS_TETE_X, 0).circle(BOIS_TETE_RAYON).extrude(c.RAIL_HAUTEUR)
    cheville = col.union(tete)
    # Bas de cheville chanfreiné (plateau) et dessus adouci pour l'insertion dans le bois
    cheville = cheville.faces(">Z").edges().fillet(0.8).faces("<Z").edges().chamfer(0.4)
    return corps.union(cheville)


# ---------------------------------------------------------------------------
# Rail Funky / Anti-Gravité
# ---------------------------------------------------------------------------
FUNKY_LONGUEUR = 100.0
FUNKY_GLISSIERE_PROF = 1.5                  # Entaille en V à 45° sur les flancs, z ∈ [4,5 ; 7,5]
FUNKY_ACIER_Y = (5.10, c.NOYAU_DEMI_LARGEUR)  # Loges des bandes d'acier, z ∈ [11 ; 12]
FUNKY_ACIER_Z = 11.0
FUNKY_ACIER_X = (18.0, 98.0)
FUNKY_DENT_DEMI_LARGEUR = 1.60
FUNKY_DENT_Z = (12.0, 14.0)                 # Crémaillère : pignon (bas à z = 12,6) engrené de 1,4 mm


def rail_funky() -> cq.Workplane:
    y_ev = c.DEMI_LARGEUR - FUNKY_GLISSIERE_PROF - c.PAROI
    rail = c.troncon_droit(FUNKY_LONGUEUR, stries=True, y_evidement=y_ev)

    # Glissières captives : entaille triangulaire sur chaque flanc, sur toute la longueur
    tri = [
        (c.DEMI_LARGEUR + 0.05, c.V_Z_BAS),
        (c.DEMI_LARGEUR - FUNKY_GLISSIERE_PROF, c.V_Z_CRETE),
        (c.DEMI_LARGEUR + 0.05, c.V_Z_HAUT),
    ]
    entaille = cq.Workplane("YZ", origin=(-1, 0, 0)).polyline(tri).close().extrude(FUNKY_LONGUEUR + 2)
    rail = rail.cut(c.symetrique_y(entaille))

    # Loges des bandes d'acier (aimant de la loco)
    x0, x1 = FUNKY_ACIER_X
    y0, y1 = FUNKY_ACIER_Y
    loge = (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, c.RAIL_HAUTEUR - FUNKY_ACIER_Z + 0.1, centered=False)
        .translate((x0, y0, FUNKY_ACIER_Z))
    )
    rail = rail.cut(c.symetrique_y(loge))

    # Crémaillère centrale : dents trapézoïdales alignées sur les stries
    za, zb = FUNKY_DENT_Z
    x = c.X_DEBUT_STRIES
    while x + c.STRIE_LONGUEUR <= FUNKY_LONGUEUR - 4.0 + 1e-9:
        profil = [(x, za - 0.1), (x + c.STRIE_LONGUEUR, za - 0.1), (x + 1.6, zb), (x + 0.4, zb)]
        dent = (
            cq.Workplane("XZ", origin=(0, FUNKY_DENT_DEMI_LARGEUR, 0))
            .polyline(profil).close()
            .extrude(2 * FUNKY_DENT_DEMI_LARGEUR)
        )
        rail = rail.union(dent)
        x += c.STRIE_PAS
    return rail


# ---------------------------------------------------------------------------
# Piliers verrouillables
# ---------------------------------------------------------------------------
PILIER_BASE = (63.6, 40.0, 12.0)       # Base pleine (x, y, z), 4 tenons gros blocs de long
PILIER_LOGE_TENONS = (28.7, 3.15, 12.8, 4.5)  # |x| <= 28,7, y ∈ [3,15 ; 12,8] (×2), z <= 4,5
PILIER_COLONNE = (32.0, 28.0)
PILIER_EVASEMENT = 12.0               # Hauteur de l'évasement vers le berceau
PILIER_BERCEAU = (40.0, 47.0)         # Dessus (x, y) ; ouverture entre rebords 40,4 pour rail de 40
PILIER_REBORD = (3.3, 6.0)            # Épaisseur, hauteur des rebords latéraux
JEU_BERCEAU = 0.2


def pilier(hauteur: float) -> cq.Workplane:
    """Pilier dont le berceau (dessous du rail) est à z = `hauteur` ; rebords jusqu'à hauteur + 6."""
    bx, by, bz = PILIER_BASE
    z_col = hauteur - PILIER_EVASEMENT
    if z_col < bz:
        raise ValueError(f"Pilier trop bas : {hauteur} mm (minimum {bz + PILIER_EVASEMENT} mm)")

    base = cq.Workplane("XY").box(bx, by, bz, centered=(True, True, False))
    base = base.edges("|Z").fillet(3.0).faces("<Z").edges().chamfer(c.CHANFREIN_BAS)
    lx, ly0, ly1, lz = PILIER_LOGE_TENONS
    for signe in (1, -1):
        loge = cq.Workplane("XY").box(2 * lx, ly1 - ly0, lz + 0.01, centered=False)
        base = base.cut(loge.translate((-lx, ly0 if signe > 0 else -ly1, -0.01)))

    cx, cy = PILIER_COLONNE
    tx, ty = PILIER_BERCEAU
    corps = cq.Workplane("XY").workplane(offset=bz - 0.01).rect(cx, cy).extrude(z_col - bz + 0.01)
    evasement = (
        cq.Workplane("XY").workplane(offset=z_col).rect(cx, cy)
        .workplane(offset=PILIER_EVASEMENT).rect(tx, ty)
        .loft()
    )
    piece = base.union(corps).union(evasement)

    ep, hr = PILIER_REBORD
    y_int = c.DEMI_LARGEUR + JEU_BERCEAU
    for signe in (1, -1):
        rebord = (
            cq.Workplane("XY").box(tx, ep, hr, centered=(True, False, False))
            .edges("|X and >Z").fillet(1.2)
            .translate((0, y_int if signe > 0 else -y_int - ep, hauteur))
        )
        piece = piece.union(rebord)
    return piece


def main() -> None:
    c.exporter(c.rail_droit(100.0), "rail_droit_100mm_snapfit")
    c.exporter(c.rail_droit(100.0, stries=True), "rail_cote_100mm_strie")
    c.exporter(c.rail_courbe(180.0, 45.0), "rail_courbe_45deg_snapfit")
    c.exporter(adaptateur_rail_bois(), "adaptateur_rail_bois")
    c.exporter(rail_funky(), "rail_funky_cremaillere_captif")
    c.exporter(pilier(50.0), "pilier_verrouillable_duplo")
    c.exporter(pilier(25.0), "pilier_verrouillable_25mm")


if __name__ == "__main__":
    main()
