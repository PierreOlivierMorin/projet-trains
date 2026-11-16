#!/usr/bin/env python3
"""Socle CAO commun (CadQuery) du Projet Trains — contrat d'interface mécanique V2.

Toutes les pièces qui s'emboîtent sur la voie importent ce module plutôt que de redéfinir
les cotes. Il fournit :
- les constantes d'interface (profil de rail, rainures, Snap-Fit, tolérances) ;
- le profil de rail arrondi « jouet en bois premium » et son extrusion droite ;
- la prise femelle et le connecteur mâle Snap-Fit (géométrie identique à la V1 Python pur) ;
- l'évidement à nervures, les chanfreins d'entrée de rainure et les micro-stries ;
- l'export STL binaire + STEP vers 03-cao-3d/stl/ et 03-cao-3d/step/.

Repère : X = sens de la voie (prise femelle à x = 0), Y = travers (centré), Z = hauteur
(dessous du rail à z = 0, posé sur le plateau d'impression).

Exécution : .venv/bin/python (CadQuery n'est pas installé dans le Python système).
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# 1. Contrat d'interface (mm) — inchangé par rapport à la V1
# ---------------------------------------------------------------------------
RAIL_LARGEUR = 40.0
RAIL_HAUTEUR = 12.0
ECARTEMENT = 25.5                 # Centre-à-centre des rainures (standard train en bois)
RAINURE_LARGEUR = 6.0
RAINURE_PROFONDEUR = 3.0
Z_FOND_RAINURE = RAIL_HAUTEUR - RAINURE_PROFONDEUR             # 9,0
Y_RAINURE_INT = ECARTEMENT / 2.0 - RAINURE_LARGEUR / 2.0         # 9,75
Y_RAINURE_EXT = ECARTEMENT / 2.0 + RAINURE_LARGEUR / 2.0         # 15,75
DEMI_LARGEUR = RAIL_LARGEUR / 2.0                                # 20,0
NOYAU_DEMI_LARGEUR = 7.25          # Noyau central qui porte la prise femelle

JEU_IMPRESSION = 0.20              # Jeu par face du Snap-Fit (à confirmer par la jauge)

FEMELLE_LONGUEUR = 17.2            # Prise femelle x ∈ [0 ; 17,2]
MALE_LONGUEUR = 16.5               # Languette mâle au-delà de la longueur utile

# Verrouillage vertical en V (45°) sur la languette et la prise : z ∈ [4,5 ; 7,5], crête 1,10 à z = 6
V_Z_BAS, V_Z_CRETE, V_Z_HAUT = 4.5, 6.0, 7.5
V_SAILLIE = 1.10

# Hauteurs de voie
MODULE_HAUTEUR = 12.5              # Rampes et rehausses de piliers

# ---------------------------------------------------------------------------
# 2. Finition « jouet en bois premium » (valeurs de départ, décision CAO V2 §3)
# ---------------------------------------------------------------------------
CONGE_ARETE_SUP = 2.0              # Arêtes supérieures extérieures du rail
CONGE_LEVRE_RAINURE = 0.5          # Lèvres des rainures
CHANFREIN_BAS = 0.6                # Arête basse sur le plateau (anti patte d'éléphant)
CHANFREIN_ENTREE_RAINURE = 0.4     # Parois de rainure aux jonctions

# Évidement du dessous
PAROI = 2.0
Z_PLAFOND_EVIDEMENT = Z_FOND_RAINURE - PAROI   # 7,0 : 2 mm sous le fond de rainure
PAS_NERVURES = 20.0
EPAISSEUR_NERVURE = 2.0

# Micro-stries de côte
STRIE_HAUTEUR = 0.8
STRIE_LONGUEUR = 2.0
STRIE_PAS = 4.0

DOSSIER_CAO = Path(__file__).resolve().parent
DOSSIER_STL = DOSSIER_CAO / "stl"
DOSSIER_STEP = DOSSIER_CAO / "step"


# ---------------------------------------------------------------------------
# 3. Outils géométriques
# ---------------------------------------------------------------------------
def polygone_arrondi(
    wp: cq.Workplane,
    points: list[tuple[float, float]],
    coins: dict[int, tuple[str, float]],
) -> cq.Workplane:
    """Trace un polygone fermé dont certains coins sont arrondis ("R", r) ou chanfreinés ("C", d).

    `points` est parcouru dans l'ordre ; `coins` associe l'indice d'un sommet à son traitement.
    Renvoie le Workplane avec le fil fermé, prêt pour extrude().
    """
    n = len(points)
    segments: list[tuple] = []  # ("L", p) ou ("A", milieu, fin)
    depart: tuple[float, float] | None = None

    def unit(dx: float, dy: float) -> tuple[float, float]:
        d = math.hypot(dx, dy)
        return dx / d, dy / d

    for i in range(n):
        p = points[i]
        a = points[i - 1]
        b = points[(i + 1) % n]
        if i not in coins:
            entree, sortie, milieu = p, p, None
        else:
            kind, val = coins[i]
            u1 = unit(a[0] - p[0], a[1] - p[1])
            u2 = unit(b[0] - p[0], b[1] - p[1])
            if kind == "C":
                entree = (p[0] + u1[0] * val, p[1] + u1[1] * val)
                sortie = (p[0] + u2[0] * val, p[1] + u2[1] * val)
                milieu = None
            else:
                cos_a = u1[0] * u2[0] + u1[1] * u2[1]
                theta = math.acos(max(-1.0, min(1.0, cos_a))) / 2.0
                t = val / math.tan(theta)
                entree = (p[0] + u1[0] * t, p[1] + u1[1] * t)
                sortie = (p[0] + u2[0] * t, p[1] + u2[1] * t)
                bx, by = unit(u1[0] + u2[0], u1[1] + u2[1])
                dc = val / math.sin(theta)
                centre = (p[0] + bx * dc, p[1] + by * dc)
                milieu = (centre[0] - bx * val, centre[1] - by * val)
        if depart is None:
            depart = entree
        else:
            segments.append(("L", entree))
        if milieu is not None:
            segments.append(("A", milieu, sortie))
        elif sortie != entree:
            segments.append(("L", sortie))

    wp = wp.moveTo(*depart)
    for seg in segments:
        if seg[0] == "L":
            wp = wp.lineTo(*seg[1])
        else:
            wp = wp.threePointArc(seg[1], seg[2])
    return wp.close()


def solide_par_sections(
    stations_x: list[float],
    demi_largeur,
    z_echantillons: list[float],
) -> cq.Solid:
    """Solide symétrique en Y défini par sa demi-largeur y = f(x, z), interpolée linéairement.

    Chaque station X donne une section YZ polygonale ; les sections sont reliées par un loft réglé,
    ce qui reproduit exactement la géométrie par morceaux linéaires de la V1.
    """
    fils = []
    for x in stations_x:
        cote_pos = [cq.Vector(x, demi_largeur(x, z), z) for z in z_echantillons]
        cote_neg = [cq.Vector(x, -demi_largeur(x, z), z) for z in reversed(z_echantillons)]
        fils.append(cq.Wire.makePolygon(cote_pos + cote_neg, close=True))
    return cq.Solid.makeLoft(fils, ruled=True)


def symetrique_y(solide: cq.Workplane) -> cq.Workplane:
    """Union d'un solide et de son miroir par rapport au plan XZ."""
    return solide.union(solide.mirror("XZ"))


# ---------------------------------------------------------------------------
# 4. Profil de rail et corps droit
# ---------------------------------------------------------------------------
def points_profil_rail() -> tuple[list[tuple[float, float]], dict[int, tuple[str, float]]]:
    """Section YZ du rail standard (sens trigonométrique vu depuis +X) et traitement des coins."""
    h, w = RAIL_HAUTEUR, DEMI_LARGEUR
    zf, yi, ye = Z_FOND_RAINURE, Y_RAINURE_INT, Y_RAINURE_EXT
    pts = [
        (-w, 0.0), (w, 0.0), (w, h),
        (ye, h), (ye, zf), (yi, zf), (yi, h),
        (-yi, h), (-yi, zf), (-ye, zf), (-ye, h),
        (-w, h),
    ]
    coins = {
        0: ("C", CHANFREIN_BAS), 1: ("C", CHANFREIN_BAS),
        2: ("R", CONGE_ARETE_SUP), 11: ("R", CONGE_ARETE_SUP),
        3: ("R", CONGE_LEVRE_RAINURE), 6: ("R", CONGE_LEVRE_RAINURE),
        7: ("R", CONGE_LEVRE_RAINURE), 10: ("R", CONGE_LEVRE_RAINURE),
    }
    return pts, coins


def corps_rail_droit(longueur: float) -> cq.Workplane:
    """Extrusion droite du profil arrondi sur x ∈ [0 ; longueur] (sans jonctions)."""
    pts, coins = points_profil_rail()
    return polygone_arrondi(cq.Workplane("YZ"), pts, coins).extrude(longueur)


# ---------------------------------------------------------------------------
# 5. Snap-Fit (géométrie V1 conservée à l'identique)
# ---------------------------------------------------------------------------
def saillie_v(z: float) -> float:
    """Profil en V à 45° du verrouillage vertical (0 hors de z ∈ [4,5 ; 7,5], 1,10 à z = 6)."""
    if z <= V_Z_BAS or z >= V_Z_HAUT:
        return 0.0
    return V_SAILLIE * (1.0 - abs(z - V_Z_CRETE) / (V_Z_HAUT - V_Z_CRETE))


def demi_largeur_cavite(x: float, z: float) -> float:
    """Demi-largeur de la prise femelle pour x ∈ [0 ; 17,2].

    Logement des bras inchangé depuis la V1. À partir de x = 10,2, la gorge épouse la languette
    à JEU_IMPRESSION près (correctif V2 : en V1, la crête en V de la languette commençait avant
    la gorge et chevauchait la prise d'environ 0,2 mm vers x = 10,9).
    """
    if x <= 3.9:
        return 5.30
    if x <= 4.4:
        return 5.30 + (x - 3.9) / 0.5 * (6.50 - 5.30)
    if x <= 9.8:
        return 6.50
    if x <= 10.2:
        return 6.50 + (x - 9.8) / 0.4 * (1.80 - 6.50)
    if x <= MALE_LONGUEUR:
        return demi_largeur_languette(x, z) + JEU_IMPRESSION
    t = (x - MALE_LONGUEUR) / (FEMELLE_LONGUEUR - MALE_LONGUEUR)
    return max((demi_largeur_languette(MALE_LONGUEUR, z) + JEU_IMPRESSION) * (1.0 - t), 0.01)


def demi_largeur_languette(x_rel: float, z: float) -> float:
    """Demi-largeur de la languette mâle pour x_rel ∈ [0 ; 16,5] depuis la face de jonction."""
    v = saillie_v(z)
    if x_rel <= 10.2:
        return 1.60
    if x_rel <= 11.5:
        t = (x_rel - 10.2) / 1.3
        return (1.60 - t * 0.10) + t * v
    if x_rel <= 15.8:
        t = (x_rel - 11.5) / 4.3
        return (1.50 - t * 0.30) + v
    t = (x_rel - 15.8) / 0.7
    return (1.20 - t * 0.70) + v * (1.0 - t * 0.73)


def contour_bras(x_rel: float) -> tuple[float, float]:
    """Limites (y_int, y_ext) du bras élastique pour x_rel ∈ [0 ; 9,5] (crochet de 6,20 à 4,5..6,0)."""
    if x_rel <= 4.0:
        return 3.50, 5.10
    if x_rel <= 4.5:
        return 3.50, 5.10 + (x_rel - 4.0) / 0.5 * (6.20 - 5.10)
    if x_rel <= 6.0:
        return 3.50, 6.20
    if x_rel <= 8.8:
        return 3.50, 6.20 - (x_rel - 6.0) / 2.8 * (6.20 - 5.10)
    t = (x_rel - 8.8) / 0.7
    return 3.50 + t * 0.40, 5.10 - t * 0.50


_Z_V = [V_Z_BAS, V_Z_CRETE, V_Z_HAUT]
_RECOUVREMENT = 0.5  # Ancrage des pièces rapportées dans le corps (union robuste)


def cavite_femelle() -> cq.Workplane:
    """Volume à soustraire au corps pour former la prise femelle à x = 0 (traverse toute la hauteur)."""
    stations = [-_RECOUVREMENT, 3.9, 4.4, 9.8, 10.2, 11.5, 15.8, MALE_LONGUEUR, FEMELLE_LONGUEUR]
    zs = [-_RECOUVREMENT] + _Z_V + [RAIL_HAUTEUR + _RECOUVREMENT]
    return cq.Workplane().add(solide_par_sections(stations, demi_largeur_cavite, zs))


def connecteur_male(x_face: float) -> cq.Workplane:
    """Languette à verrou en V + deux bras Snap-Fit, accrochés à la face de jonction x = x_face."""
    zs = [0.0] + _Z_V + [RAIL_HAUTEUR]
    stations = [-_RECOUVREMENT, 10.2, 11.5, 15.8, MALE_LONGUEUR]
    languette = solide_par_sections(stations, demi_largeur_languette, zs)

    stations_bras = [-_RECOUVREMENT, 4.0, 4.5, 6.0, 8.8, 9.5]
    ext = [(x, contour_bras(max(x, 0.0))[1]) for x in stations_bras]
    inte = [(x, contour_bras(max(x, 0.0))[0]) for x in reversed(stations_bras)]
    bras = cq.Workplane("XY").polyline(ext + inte).close().extrude(RAIL_HAUTEUR)

    male = cq.Workplane().add(languette).union(symetrique_y(bras))
    return male.translate((x_face, 0, 0))


# ---------------------------------------------------------------------------
# 6. Détails de finition et de fonction
# ---------------------------------------------------------------------------
def chanfreiner_entrees_rainures(rail: cq.Workplane, x_faces: list[float]) -> cq.Workplane:
    """Chanfrein de 0,4 mm sur les arêtes verticales des parois de rainure aux faces de jonction.

    Une roue légèrement désaxée glisse sur le chanfrein au lieu de buter contre le joint.
    """
    def selecteur(arete) -> bool:
        if arete.geomType() != "LINE":
            return False
        c = arete.Center()
        d = arete.endPoint() - arete.startPoint()
        return (
            abs(d.x) < 1e-6 and abs(d.y) < 1e-6
            and any(abs(c.x - xf) < 1e-3 for xf in x_faces)
            and any(abs(abs(c.y) - yp) < 1e-3 for yp in (Y_RAINURE_INT, Y_RAINURE_EXT))
            and c.z > Z_FOND_RAINURE
        )

    aretes = [a for a in rail.edges().vals() if selecteur(a)]
    if not aretes:
        return rail
    return rail.newObject(aretes).chamfer(CHANFREIN_ENTREE_RAINURE)


def evidement_nervure(x0: float, x1: float) -> cq.Workplane:
    """Poche ouverte par le dessous entre x0 et x1, cloisonnée par des nervures (transversales + axiale)."""
    y_max = DEMI_LARGEUR - PAROI
    poche = cq.Workplane("XY").box(x1 - x0, 2 * y_max, Z_PLAFOND_EVIDEMENT, centered=(False, True, False))
    poche = poche.translate((x0, 0, -0.01))

    n_cellules = max(1, round((x1 - x0) / PAS_NERVURES))
    pas = (x1 - x0) / n_cellules
    for k in range(1, n_cellules):
        xc = x0 + k * pas
        nervure = cq.Workplane("XY").box(EPAISSEUR_NERVURE, 2 * y_max + 2, Z_PLAFOND_EVIDEMENT + 1, centered=(True, True, False))
        poche = poche.cut(nervure.translate((xc, 0, -0.5)))
    axiale = cq.Workplane("XY").box(x1 - x0 + 2, EPAISSEUR_NERVURE, Z_PLAFOND_EVIDEMENT + 1, centered=(False, True, False))
    return poche.cut(axiale.translate((x0 - 1, 0, -0.5)))


def micro_stries(x0: float, x1: float) -> cq.Workplane:
    """Stries transversales de 0,8 mm au fond des deux rainures, de 2 mm tous les 4 mm sur [x0 ; x1]."""
    stries = None
    x = x0
    while x + STRIE_LONGUEUR <= x1 + 1e-9:
        bloc = cq.Workplane("XY").box(
            STRIE_LONGUEUR, RAINURE_LARGEUR + 0.2, STRIE_HAUTEUR + 0.1, centered=(False, True, False)
        ).translate((x, ECARTEMENT / 2.0, Z_FOND_RAINURE - 0.1))
        bloc = symetrique_y(bloc)
        stries = bloc if stries is None else stries.union(bloc)
        x += STRIE_PAS
    return stries


# ---------------------------------------------------------------------------
# 7. Assemblage d'un rail droit standard
# ---------------------------------------------------------------------------
def rail_droit(longueur: float = 100.0, stries: bool = False, evide: bool = True) -> cq.Workplane:
    """Rail droit complet : prise femelle à x = 0, connecteur mâle à x = longueur."""
    rail = corps_rail_droit(longueur)
    rail = chanfreiner_entrees_rainures(rail, [0.0, longueur])
    rail = rail.cut(cavite_femelle())
    if evide:
        x0 = FEMELLE_LONGUEUR + PAROI
        x1 = longueur - 4.0
        if x1 - x0 > PAS_NERVURES:
            rail = rail.cut(evidement_nervure(x0, x1))
    if stries:
        rail = rail.union(micro_stries(FEMELLE_LONGUEUR + 1.0, longueur - 4.0))
    return rail.union(connecteur_male(longueur))


# ---------------------------------------------------------------------------
# 8. Export
# ---------------------------------------------------------------------------
def exporter(piece: cq.Workplane, nom: str) -> tuple[Path, Path]:
    """Écrit `nom`.stl (binaire) et `nom`.step après contrôle de validité et de pose sur le plateau."""
    forme = piece.val() if len(piece.vals()) == 1 else piece.combine().val()
    if not forme.isValid():
        raise ValueError(f"{nom} : solide OpenCASCADE invalide")
    bb = forme.BoundingBox()
    if abs(bb.zmin) > 1e-3:
        raise ValueError(f"{nom} : Z_min = {bb.zmin:.3f} mm (la pièce doit reposer sur z = 0)")

    DOSSIER_STL.mkdir(parents=True, exist_ok=True)
    DOSSIER_STEP.mkdir(parents=True, exist_ok=True)
    chemin_stl = DOSSIER_STL / f"{nom}.stl"
    chemin_step = DOSSIER_STEP / f"{nom}.step"
    forme.exportStl(str(chemin_stl), tolerance=0.01, angularTolerance=0.1, ascii=False)
    cq.exporters.export(cq.Workplane().add(forme), str(chemin_step))
    print(
        f"[OK] {nom}: {bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f} mm | "
        f"volume={forme.Volume() / 1000.0:.2f} cm3"
    )
    return chemin_stl, chemin_step
