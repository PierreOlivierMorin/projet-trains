#!/usr/bin/env python3
"""Générateur CadQuery des aiguillages manuels (V2, voir decisions-cao-v2.md §5 et §11).

Aiguillage en « Y » de la nomenclature du circuit de test :
- voie directe droite de `L_DIRECTE` = 163,28 mm (valeur de outils/plan_circuit.py, qui ferme le circuit) ;
- voie déviée = courbe standard 45° / R = 180 (17,2 mm de droit à chaque bout), donc mêmes poses
  de sortie qu'une courbe ;
- deux variantes de genre : tronc femelle (sorties mâles) ou tronc mâle (sorties femelles) ;
- gauche (déviée vers +Y) ou droite (miroir).

Mécanisme : une **lame pivotante talonnable** dans la rainure intérieure, côté où les rainures se
séparent (une seule lame suffit, l'essieu rigide fait suivre l'autre roue). Pivot sur l'îlot entre
les rainures, pointe de lame vers le tronc :
- position « directe » : la face basse de la lame prolonge la paroi de la rainure droite ;
- position « déviée » (rotation de `LAME_ANGLE` autour du pivot) : la face haute épouse la paroi
  intérieure de la rainure courbe ;
- un train qui arrive par la mauvaise branche pousse la lame en biais (~8–15°) et la retourne.
La pointe est logée de `LAME_LOGEMENT` dans la paroi d'appui (pas d'arête offerte à la roue).
La lame tourne sur un tenon Ø 4 traversant le fond de rainure ; dessous, un **levier** emmanché sur
le carré du tenon sort par une lumière du flanc et se termine par une palette verticale.
Le même levier sert à gauche et à droite (pièce symétrique).

Pièces exportées (posées sur le plateau) :
- aiguillage_gauche_tronc_f, aiguillage_droit_tronc_m, aiguillage_droit_tronc_f (variantes du plan)
- aiguillage_lame_gauche, aiguillage_lame_droite (imprimées à l'envers, tenon vers le haut)
- aiguillage_levier

Repère : tronc à x = 0 (face de jonction), voie directe vers +X, déviée vers +Y (gauche).

Usage : .venv/bin/python 03-cao-3d/generer_aiguillages.py
"""

from __future__ import annotations

import math

import cadquery as cq

import cao_commun as c

R = 180.0
ANGLE = 45.0
DX, DY, _ = c.deplacement_courbe(R, ANGLE)
X_ARC = c.FEMELLE_LONGUEUR                 # Début de l'arc de la voie déviée
L_DIRECTE = 163.28291449997434             # = plan_circuit.L_AIG (contrôlé par controler_aiguillage.py)
EXTREMITE = c.FEMELLE_LONGUEUR             # Bouts droits portant les jonctions (prise ou languette)

# Rainure intérieure (gauche) : droite y ∈ [9,75 ; 15,75], courbe entre les rayons 164,25 et 170,25
R_INT_HAUT = R - c.ECARTEMENT / 2 - c.RAINURE_LARGEUR / 2   # 164,25 : paroi haute (côté +Y)
R_INT_BAS = R - c.ECARTEMENT / 2 + c.RAINURE_LARGEUR / 2    # 170,25 : paroi basse

# Lame
PIVOT = (80.0, 18.75)        # Sur l'îlot entre rainure droite et rainure courbe (îlot de 6 mm à x = 80)
LAME_ANGLE = 8.0             # Débattement (degrés, sens trigo de « directe » vers « déviée »)
LAME_EPAISSEUR_MAX = 2.5
LAME_LOGEMENT = 0.6          # Pointe noyée dans la paroi d'appui
LAME_X_MIN = 30.0           # Pointe tronquée à ~0,8 mm (2 lignes de buse 0,4) ; noyée de 0,6 dans la paroi
LAME_Z = (9.05, 11.8)        # Posée sur le fond de rainure (9,0), sous le plateau (12)
LAME_TALON_R = 3.0           # Disque autour du pivot
JEU_LAME = 0.3
TENON_D = 4.0
TENON_CARRE = 3.0
Z_LEVIER = (3.6, 6.6)        # Levier sous le plafond de l'évidement (7,0)
LEVIER_LARGEUR = 6.0
LEVIER_MOYEU_R = 4.5
LEVIER_Y_FIN = -25.0         # Palette hors du flanc (y = -20)
PALETTE = (6.0, 3.0, 12.0)   # x, y, z haut de la palette
JEU_LEVIER = 0.6


# ---------------------------------------------------------------------------
# Géométrie en plan (repère « gauche »)
# ---------------------------------------------------------------------------
def y_cercle(r: float, x: float) -> float:
    """Ordonnée d'un cercle de centre (X_ARC, R) et de rayon r, pour x ≥ X_ARC (droite avant)."""
    dx = max(0.0, x - X_ARC)
    return R - math.sqrt(r * r - dx * dx)


def y_haut(x: float) -> float:   # Paroi haute de la rainure courbe intérieure
    return y_cercle(R_INT_HAUT, x)


def y_bas(x: float) -> float:    # Paroi basse de la rainure courbe intérieure
    return y_cercle(R_INT_BAS, x)


def tourner(pts, angle_deg: float, centre=PIVOT):
    a = math.radians(angle_deg)
    cx, cy = centre
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a),
             cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


def prisme(pts, z0: float, z1: float) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


def disque(centre, r: float, z0: float, z1: float) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).center(*centre).circle(r).extrude(z1 - z0)


def _xs(x0: float, x1: float, n: int = 60) -> list[float]:
    return [x0 + (x1 - x0) * k / n for k in range(n + 1)]


def lame_plan(jeu: float = 0.0) -> list[list[tuple[float, float]]]:
    """Polygones (S, C) dont l'intersection S ∩ rot(C, -angle) donne la lame en position directe.

    S : zone permise en position directe (au-dessus de la paroi y = 15,75, noyée dans la paroi
    haute de la rainure courbe) ; C : zone permise en position déviée (sous la paroi basse de la
    rainure courbe, noyée dans la paroi basse de la rainure droite). `jeu` gonfle les deux zones
    (logement dans le corps).
    """
    y0 = c.Y_RAINURE_EXT                       # 15,75
    xs = _xs(LAME_X_MIN - jeu, PIVOT[0])
    s_haut = [(x, min(y0 + LAME_EPAISSEUR_MAX, y_haut(x) + LAME_LOGEMENT) + jeu) for x in xs]
    S = [(xs[0], y0 - jeu), (xs[-1], y0 - jeu)] + list(reversed(s_haut))
    xc = _xs(LAME_X_MIN - 15.0, PIVOT[0] + 8.0)
    c_haut = [(x, y_bas(x) + jeu) for x in xc]
    C = [(xc[0], c.Y_RAINURE_INT - LAME_LOGEMENT - jeu), (xc[-1], c.Y_RAINURE_INT - LAME_LOGEMENT - jeu)] \
        + list(reversed(c_haut))
    return [S, C]


def lame_solide(angle: float = 0.0, jeu: float = 0.0, z=LAME_Z) -> cq.Workplane:
    """Lame (sans tenon) tournée de `angle` autour du pivot (0 = directe, LAME_ANGLE = déviée)."""
    S, C = lame_plan(jeu)
    corps = prisme(S, *z).intersect(prisme(tourner(C, -LAME_ANGLE), *z))
    # Logement : disque nettement plus grand que l'îlot (un cercle qui effleure la paroi de rainure
    # donne des facettes dégénérées dans le STL)
    r = LAME_TALON_R + (1.0 if jeu else 0.0)
    corps = corps.union(disque(PIVOT, r, *z))
    return corps.rotate((*PIVOT, 0), (*PIVOT, 1), angle) if angle else corps


def lame(angle: float = 0.0) -> cq.Workplane:
    """Lame complète avec tenon (rond Ø 4 dans le fond, carré 3 × 3 pour le levier)."""
    zl0 = LAME_Z[0]
    corps = lame_solide()   # Pas de chanfrein : l'outil échoue sur la pointe effilée
    rond = disque(PIVOT, TENON_D / 2, Z_LEVIER[1], zl0 + 0.5)
    carre = (cq.Workplane("XY").workplane(offset=Z_LEVIER[0]).center(*PIVOT)
             .rect(TENON_CARRE, TENON_CARRE).extrude(Z_LEVIER[1] - Z_LEVIER[0] + 0.01))
    piece = corps.union(rond).union(carre)
    return piece.rotate((*PIVOT, 0), (*PIVOT, 1), angle) if angle else piece


def levier_plan(jeu: float = 0.0) -> list[tuple[float, float]]:
    px, py = PIVOT
    h = LEVIER_LARGEUR / 2 + jeu
    return [(px - h, py), (px - h, LEVIER_Y_FIN - jeu), (px + h, LEVIER_Y_FIN - jeu), (px + h, py)]


def levier(angle: float = 0.0) -> cq.Workplane:
    """Levier sous le corps : moyeu à trou carré sur le tenon, bras vers -Y, palette verticale."""
    z0, z1 = Z_LEVIER
    px, _ = PIVOT
    bras = prisme(levier_plan(), z0, z1).union(disque(PIVOT, LEVIER_MOYEU_R, z0, z1))
    px_, py_, pz = PALETTE
    palette = (cq.Workplane("XY").box(px_, py_, pz - z0, centered=(True, False, False))
               .translate((px, LEVIER_Y_FIN, z0)))
    palette = palette.edges("|Y and >Z").fillet(1.2)
    trou = (cq.Workplane("XY").workplane(offset=z0 - 1).center(*PIVOT)
            .rect(TENON_CARRE, TENON_CARRE).extrude(z1 - z0 + 2))
    piece = bras.union(palette).cut(trou)
    return piece.rotate((*PIVOT, 0), (*PIVOT, 1), angle) if angle else piece


def balayage(fabrique, n: int = 12) -> cq.Workplane:
    """Union des positions d'une pièce entre 0 et LAME_ANGLE (logements dans le corps)."""
    tout = None
    for k in range(n + 1):
        p = fabrique(LAME_ANGLE * k / n)
        tout = p if tout is None else tout.union(p)
    return tout


# ---------------------------------------------------------------------------
# Corps
# ---------------------------------------------------------------------------
def extremite(femelle: bool) -> cq.Workplane:
    """Bout droit de 17,2 mm sur x ∈ [-17,2 ; 0], jonction (prise ou languette) tournée vers +X."""
    if femelle:
        return c.troncon_droit(EXTREMITE, femelle=True, male=False, evide=False).rotate((0, 0, 0), (0, 0, 1), 180)
    return c.troncon_droit(EXTREMITE, femelle=False, male=True, evide=False).translate((-EXTREMITE, 0, 0))


def _rainures_droites(x0: float, x1: float) -> cq.Workplane:
    h = c.RAIL_HAUTEUR + 1 - c.Z_FOND_RAINURE
    b = cq.Workplane("XY").box(x1 - x0, c.RAINURE_LARGEUR, h, centered=(False, True, False))
    b = b.translate((x0, c.ECARTEMENT / 2, c.Z_FOND_RAINURE))
    return c.symetrique_y(b)


def _rainures_courbes() -> cq.Workplane:
    tout = None
    for yc in (c.ECARTEMENT / 2, -c.ECARTEMENT / 2):
        y0, y1 = yc - c.RAINURE_LARGEUR / 2, yc + c.RAINURE_LARGEUR / 2
        z0, z1 = c.Z_FOND_RAINURE, c.RAIL_HAUTEUR + 1
        r = (cq.Workplane("YZ", origin=(X_ARC, 0, 0)).polyline([(y0, z0), (y1, z0), (y1, z1), (y0, z1)]).close()
             .revolve(ANGLE, (R, 0, 0), (R, 1, 0)))
        tout = r if tout is None else tout.union(r)
    return tout


def _evidements(x1_droit: float, garde: cq.Workplane) -> cq.Workplane:
    """Poches à nervures sous la voie directe et sous l'arc ; nervures supprimées dans `garde`
    (débattement du levier)."""
    x0 = X_ARC + c.PAROI
    brut_d = (cq.Workplane("XY").box(x1_droit - x0, 2 * (c.DEMI_LARGEUR - c.PAROI), c.Z_PLAFOND_EVIDEMENT,
                                     centered=(False, True, False)).translate((x0, 0, -0.01)))
    nerv_d = brut_d.cut(c.evidement_nervure(x0, x1_droit))

    y_max = c.DEMI_LARGEUR - c.PAROI
    marge = math.degrees(c.PAROI / R)
    centre = (X_ARC, R, 0)
    anneau = (cq.Workplane("XY").workplane(offset=-0.01).center(X_ARC, R)
              .circle(R + y_max).circle(R - y_max).extrude(c.Z_PLAFOND_EVIDEMENT + 0.01))
    secteur = (cq.Workplane("XY").workplane(offset=-1)
               .polyline(c._secteur(centre, R + y_max + 5, marge, ANGLE - marge)).close()
               .extrude(c.Z_PLAFOND_EVIDEMENT + 2))
    brut_a = anneau.intersect(secteur)
    nerv_a = brut_a.cut(c._evidement_arc(X_ARC, R, ANGLE))

    brut = brut_d.union(brut_a)
    nervures = nerv_d.union(nerv_a).cut(garde)
    return brut.cut(nervures)


def corps(tronc_femelle: bool, droite: bool = False) -> cq.Workplane:
    """Corps d'aiguillage (repère gauche, miroir si `droite`)."""
    pts, coins = c.points_profil_rail()
    # Lèvres de rainure vives dans la partie centrale : les rainures y sont recoupées et un congé
    # recoupé de biais produit des facettes dégénérées (lèvres arrondies conservées aux extrémités)
    coins = {k: v for k, v in coins.items() if k not in (3, 6, 7, 10)}
    milieu = (c.polygone_arrondi(cq.Workplane("YZ"), pts, coins).extrude(L_DIRECTE - 2 * EXTREMITE)
              .translate((EXTREMITE, 0, 0)))
    arc = c.polygone_arrondi(cq.Workplane("YZ", origin=(X_ARC, 0, 0)), pts, coins).revolve(
        ANGLE, (R, 0, 0), (R, 1, 0))
    piece = milieu.union(arc)
    piece = piece.cut(_rainures_droites(EXTREMITE, L_DIRECTE - EXTREMITE)).cut(_rainures_courbes())

    # Évidement, logement de la lame, passage du tenon, débattement et lumière du levier
    garde = prisme(levier_plan(JEU_LEVIER), -1, c.Z_PLAFOND_EVIDEMENT + 1).union(
        disque(PIVOT, LEVIER_MOYEU_R + JEU_LEVIER, -1, c.Z_PLAFOND_EVIDEMENT + 1))
    garde = balayage(lambda a: garde.rotate((*PIVOT, 0), (*PIVOT, 1), a), 8)
    piece = piece.cut(_evidements(L_DIRECTE - EXTREMITE - c.PAROI, garde))
    lumiere = balayage(lambda a: prisme(levier_plan(JEU_LEVIER), Z_LEVIER[0] - 0.4, c.Z_PLAFOND_EVIDEMENT - 0.1)
                       .rotate((*PIVOT, 0), (*PIVOT, 1), a), 8)
    piece = piece.cut(lumiere)
    piece = piece.cut(balayage(lambda a: lame_solide(a, JEU_LAME, (c.Z_FOND_RAINURE, c.RAIL_HAUTEUR + 1))))
    piece = piece.cut(disque(PIVOT, TENON_D / 2 + 0.2, c.Z_PLAFOND_EVIDEMENT - 0.5, c.Z_FOND_RAINURE + 0.1))

    # Jonctions : tronc, sortie directe, sortie déviée
    sorties_femelles = not tronc_femelle
    piece = piece.union(extremite(tronc_femelle).rotate((0, 0, 0), (0, 0, 1), 180))
    piece = piece.union(extremite(sorties_femelles).translate((L_DIRECTE, 0, 0)))
    piece = piece.union(extremite(sorties_femelles).rotate((0, 0, 0), (0, 0, 1), ANGLE).translate((DX, DY, 0)))
    return piece.mirror("XZ") if droite else piece


def placer_lame(droite: bool, deviee: bool) -> cq.Workplane:
    p = lame(LAME_ANGLE if deviee else 0.0)
    return p.mirror("XZ") if droite else p


def placer_levier(droite: bool, deviee: bool) -> cq.Workplane:
    p = levier(LAME_ANGLE if deviee else 0.0)
    return p.mirror("XZ") if droite else p


VARIANTES = {
    "aiguillage_gauche_tronc_f": (True, False),
    "aiguillage_droit_tronc_m": (False, True),
    "aiguillage_droit_tronc_f": (True, True),
}


def main() -> None:
    for nom, (tf, droite) in VARIANTES.items():
        c.exporter(corps(tf, droite), nom)
    # Lame imprimée à l'envers (dessus sur le plateau, tenon vers le haut)
    for nom, droite in (("aiguillage_lame_gauche", False), ("aiguillage_lame_droite", True)):
        p = placer_lame(droite, False).rotate((0, 0, 0), (1, 0, 0), 180)
        c.exporter(p.translate((0, 0, -p.val().BoundingBox().zmin)), nom)
    c.exporter(levier().translate((0, 0, -Z_LEVIER[0])), "aiguillage_levier")


if __name__ == "__main__":
    main()
