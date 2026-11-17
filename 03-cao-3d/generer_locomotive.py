#!/usr/bin/env python3
"""Générateur CadQuery de la locomotive Alpha V2 — mode châssis-test (decisions-locomotive-v2.md).

Pièces :
- loco_chassis_test           : châssis (paliers fermés, aimants N52 scellés, loge capteur Hall,
                                crochet avant / anneau arrière, poteaux du bac à piles et de la cheminée)
- loco_roue_24mm              : roue Ø 24 × 3,5 mm bombée, sans boudin, gorge de pneu (×3)
- loco_roue_24mm_codeur       : même roue avec loge scellée pour aimant Ø 3 × 1 (essieu libre, ×1)
- loco_pignon_central_essieu  : pignon d'escalade 12 dents (crémaillère Funky)
- loco_engrenage_essieu       : engrenage 14 dents m1 sur l'essieu moteur
- loco_engrenage_moteur       : engrenage 20 dents m1 sur l'arbre en D du N20 (multiplie ×1,43)
- loco_support_moteur         : support du N20 à vis sans fin (cotes MOTEUR à recaler sur le moteur reçu)
- loco_bac_piles              : bac 3×AAA à contacts du commerce, sur 4 poteaux au-dessus de l'engrenage moteur
- loco_coque_vapeur           : coque soute + cabine + chaudière (lanternes LED, fenêtre ToF, opercule Push & Go,
                                logement d'interrupteur), accrochée sous le bac et vissée par la cheminée

Repère locomotive : X vers l'avant (origine au milieu des essieux), Y vers la gauche,
Z depuis la base du rail. Chaque pièce est ensuite posée à plat pour l'impression.
Usage : .venv/bin/python 03-cao-3d/generer_locomotive.py
"""

from __future__ import annotations

import math

import cadquery as cq

import cao_commun as c

# ---------------------------------------------------------------------------
# Cotes de la locomotive
# ---------------------------------------------------------------------------
Z_ESSIEU = 21.0
X_ESSIEU_AV = 23.0                  # Essieu moteur (pignon d'escalade + engrenage)
X_ESSIEU_AR = -23.0                 # Essieu libre (roue codeur)
ALESAGE_SERRE = 2.95                # Roues / engrenages emmanchés sur tige Ø 3 (à confirmer : jauge)
ALESAGE_PALIER = 3.20               # Tige libre en rotation dans le châssis

ROUE_RAYON = Z_ESSIEU - c.Z_FOND_RAINURE        # 12,0
ROUE_LARGEUR = 3.5                  # Passe en courbe R = 180 avec un empattement de 46 mm
ROUE_CHANFREIN = 0.40               # Chanfrein des bords de bande (tient lieu de bombé)
GORGE_RAYON = 10.9
GORGE_LARGEUR = 1.6
Y_ROUE_INT = c.ECARTEMENT / 2.0 - ROUE_LARGEUR / 2.0   # 11,0 : face intérieure
MOYEU_RAYON = 3.5
MOYEU_LONGUEUR = 1.0                # Entretoise vers le palier
AIMANT_CODEUR = (3.0, 1.0)          # Ø × épaisseur, scellé à r = 6 dans le moyeu
R_AIMANT_CODEUR = 6.0

Z_SOL_BAS = 12.6                    # 0,6 mm au-dessus du dessus d'un rail
EP_SOL = 3.0
Z_SOL_HAUT = Z_SOL_BAS + EP_SOL
Y_SOL = 9.8                         # Plancher central entre les roues (face intérieure à 11,0)
X_SOL = (-44.0, 42.0)
LARGE_ZONE = (-10.0, 10.0, 22.0)    # Plancher élargi entre les roues avant et arrière (x0, x1, |y|)

PALIER = (5.0, 7.0, Y_SOL, 25.5)    # Demi-longueur x, y_int, y_ext, z_haut

AIMANT = (20.0, 5.0, 3.0)           # 2 × N52 20 × 5 × 3, scellés (x, y, z), un au-dessus de chaque bande d'acier
Y_AIMANT = 6.18                     # Centre des loges d'acier des rails Funky (|y| 5,10 – 7,25)
X_AIMANT = -12.0                    # Entre les essieux, derrière le support moteur
CANAL = (2.4, 14.6)                 # Canal sous le plancher : |y| <= 2,4 libre jusqu'à z = 14,6 (crémaillère à 14)
PEAU = 0.6

# Poteaux du bac à piles (x, y, rayon) : vis M3 fraisées depuis le fond du bac
POTEAUX = [(-6.5, 17.0, 3.0), (-6.5, -17.0, 3.0), (-40.0, 7.0, 2.75), (-40.0, -7.0, 2.75)]
Z_BAC = 41.5                        # Dessous du bac : au-dessus de l'engrenage moteur (balayage jusqu'à z = 40,3 en x = 2,45)
EP_BAC = 2.5                        # Fond (fraisures des vis)
BAC_X = (-48.55, 2.45)              # Avant : 0,5 mm derrière le carter du N20
BAC_Y = 20.0
PILE = (10.5, 44.5)                 # AAA (Ø, longueur max CEI)
Y_PILES = (-11.0, 0.0, 11.0)        # 3 piles en série, sens alternés
ESPACE_PILES = 46.2                 # Entre faces des lèvres : 44,5 + ressort comprimé ~1,7
BOUT_BAC = (0.6, 0.8, 1.0)          # Lèvre, fente de contact, paroi extérieure (x)
Z_HAUT_BAC = 53.5                   # Haut des parois d'about (axe des piles à z = 49,25)

# Interrupteur à glissière SS-12D00 (corps 8,6 × 3,6 × 3,5, levier 4 mm) : cotes à vérifier
INTERRUPTEUR = {"l": 8.6, "w": 3.6, "h": 3.5, "x": 7.5, "z_bas": 32.5}

# Coque vapeur (soute + cabine + chaudière), posée sur le bac à l'arrière, vissée par la cheminée
COQUE_Y = 22.0
COQUE_EP = 1.6
Z_COQUE_BAS = 24.0                  # Au-dessus de l'anneau d'attelage (20,6) et du pion du véhicule suivant (22)
X_COQUE_AR = BAC_X[0] - 0.3 - COQUE_EP
X_COQUE_AV = 42.0
X_SOUTE_CABINE = -15.0              # Soute à charbon (toit bas) | cabine (toit haut, au-dessus du moteur)
Z_TOIT_SOUTE = 57.0
Z_TABLIER = 36.5                    # Tablier de la chaudière (au-dessus des roues avant, z = 33)
CHAUDIERE = (16.6, 40.0, 55.0)      # Rayon extérieur, axe z, plafond intérieur (méplat sous la cheminée)
X_CHEMINEE = 35.5
LEVRE = (2.25, 41.3, 8.0, 18.0)     # Lèvre arrière sous le fond du bac : longueur, z haut, |y| min, |y| max
JEU_POSE = 1.2                      # Jeu carter / façade de cabine (pose en basculant autour de la lèvre)

# Engrenages (module 1, 20°)
MODULE = 1.0
DENTS_ESSIEU = 14                   # Tête Ø 16 : bas à z = 13, au-dessus du rail
DENTS_MOTEUR = 20
EP_ENGRENAGE = 3.0
Y_ENGRENAGES = (3.0, 6.0)           # Entre le pignon d'escalade (|y| < 1,5) et le palier (7,0)
JEU_ENTRAXE = 0.15
ANGLE_ARBRE = 35.0                  # Arbre de sortie au-dessus et en arrière de l'essieu moteur

# Moteur N20 à vis sans fin : cotes SUPPOSÉES, à mesurer sur le moteur reçu.
MOTEUR = {
    "boite_x": 10.0,      # Épaisseur du réducteur (sens de la voie)
    "boite_y": 12.0,      # Largeur du réducteur, arbre de sortie sortant côté +Y
    "boite_z": 18.0,      # Longueur du réducteur (axe moteur vertical)
    "arbre_z": 5.0,       # Hauteur de l'arbre de sortie depuis le bas du réducteur
    "carter_d": 12.0,     # Moteur Ø 12 au-dessus du réducteur
    "carter_l": 15.0,
    "arbre_d": 3.0, "arbre_plat": 2.5, "arbre_l": 8.0,
}

# Attelages
ATTELAGE_PION = (46.0, 2.0, 22.0)    # x, rayon, z_haut (traverse l'anneau du véhicule suivant)
ATTELAGE_ANNEAU = (-49.0, 3.0)       # x du trou, rayon


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
def boite(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylindre_y(x, z, r, y0, y1) -> cq.Workplane:
    return cq.Workplane("XZ", origin=(0, y1, 0)).center(x, z).circle(r).extrude(y1 - y0)


def vers_axe_y(piece: cq.Workplane, y0: float, x: float, z: float) -> cq.Workplane:
    """Pièce modélisée axe Z (z ∈ [0, e]) -> axe Y monde, occupant y ∈ [y0, y0 + e], centre (x, z)."""
    return piece.rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y0, z))


def entraxe() -> float:
    return MODULE * (DENTS_ESSIEU + DENTS_MOTEUR) / 2.0 + JEU_ENTRAXE


def position_arbre_moteur() -> tuple[float, float]:
    a = math.radians(ANGLE_ARBRE)
    return X_ESSIEU_AV - entraxe() * math.cos(a), Z_ESSIEU + entraxe() * math.sin(a)


# ---------------------------------------------------------------------------
# Roues
# ---------------------------------------------------------------------------
def roue(codeur: bool = False) -> cq.Workplane:
    """Roue posée face extérieure sur le plateau ; moyeu-entretoise vers le haut (face intérieure)."""
    w, r, b = ROUE_LARGEUR, ROUE_RAYON, ROUE_CHANFREIN
    # Bande plate à R 12 (deux portées de part et d'autre de la gorge), bords chanfreinés :
    # les chanfreins jouent le rôle du bombé quand l'essieu est braqué en courbe.
    profil = [(0, 0), (r - b, 0), (r, b), (r, w - b), (r - b, w), (0, w)]
    jante = cq.Workplane("XZ").polyline(profil).close().revolve(360, (0, 0, 0), (0, 1, 0))
    gorge = boite(-20, 20, -20, 20, (w - GORGE_LARGEUR) / 2, (w + GORGE_LARGEUR) / 2).cut(
        cq.Workplane("XY").circle(GORGE_RAYON).extrude(10).translate((0, 0, -1))
    )
    moyeu = cq.Workplane("XY").workplane(offset=w - 0.1).circle(MOYEU_RAYON).extrude(MOYEU_LONGUEUR + 0.1)
    piece = jante.cut(gorge).union(moyeu)
    piece = piece.cut(cq.Workplane("XY").circle(ALESAGE_SERRE / 2).extrude(10).translate((0, 0, -1)))
    if codeur:
        d, e = AIMANT_CODEUR
        # Loge fermée à 0,6 mm sous la face intérieure (pause d'impression pour insérer l'aimant)
        z1 = w - PEAU
        loge = cq.Workplane("XY").center(R_AIMANT_CODEUR, 0).circle(d / 2 + 0.1).extrude(e + 0.1).translate((0, 0, z1 - e - 0.1))
        piece = piece.cut(loge)
    return piece


# ---------------------------------------------------------------------------
# Engrenages
# ---------------------------------------------------------------------------
def _inv(a: float) -> float:
    return math.tan(a) - a


def engrenage(dents: int, epaisseur: float, alesage: cq.Workplane | None, jeu: float = 0.05) -> cq.Workplane:
    """Engrenage droit à développante (module MODULE, angle de pression 20°)."""
    m, alpha = MODULE, math.radians(20)
    rp = m * dents / 2
    rb = rp * math.cos(alpha)
    ra = rp + m
    rf = rp - 1.25 * m
    demi = math.pi / (2 * dents) + _inv(alpha) - jeu / rp
    r_dep = max(rb, rf)
    rayons = [r_dep + (ra - r_dep) * k / 6 for k in range(7)]

    def phi(r: float) -> float:
        return demi - _inv(math.acos(min(1.0, rb / r)))

    pts = []
    for k in range(dents):
        ck = 2 * math.pi * k / dents
        flanc_g = [(r, ck - phi(r)) for r in rayons]
        flanc_d = [(r, ck + phi(r)) for r in reversed(rayons)]
        pied_g = [(rf, ck - phi(r_dep))] if rf < rb else []
        pied_d = [(rf, ck + phi(r_dep))] if rf < rb else []
        for r, a in pied_g + flanc_g + flanc_d + pied_d:
            pts.append((r * math.cos(a), r * math.sin(a)))
    roue_dentee = cq.Workplane("XY").polyline(pts).close().extrude(epaisseur)
    if alesage is not None:
        roue_dentee = roue_dentee.cut(alesage)
    return roue_dentee


def alesage_rond(d: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(d / 2).extrude(20).translate((0, 0, -5))


def alesage_d() -> cq.Workplane:
    d, plat = MOTEUR["arbre_d"] + 0.1, MOTEUR["arbre_plat"] + 0.1
    rond = cq.Workplane("XY").circle(d / 2).extrude(20).translate((0, 0, -5))
    coupe = boite(-d, d, plat - d / 2, d, -6, 16)
    return rond.cut(coupe)


def engrenage_essieu() -> cq.Workplane:
    return engrenage(DENTS_ESSIEU, EP_ENGRENAGE, alesage_rond(ALESAGE_SERRE))


def engrenage_moteur() -> cq.Workplane:
    moyeu = cq.Workplane("XY").workplane(offset=EP_ENGRENAGE - 0.1).circle(3.0).extrude(2.1)
    return engrenage(DENTS_MOTEUR, EP_ENGRENAGE, None).union(moyeu).cut(alesage_d())


def pignon() -> cq.Workplane:
    """Pignon d'escalade : profil trapézoïdal de la V1 (Ø tête 16,8, Ø pied 13,4, 12 dents)."""
    n, r_pied, r_tete = 12, 6.70, 8.40
    pas = 2 * math.pi / n
    sous = pas / 8.0
    pts = []
    for k in range(n):
        a = k * pas
        for i, r in ((2, r_pied), (3, r_tete), (5, r_tete), (6, r_pied)):
            pts.append((r * math.cos(a + i * sous), r * math.sin(a + i * sous)))
    corps = cq.Workplane("XY").polyline(pts).close().extrude(3.0)
    return corps.cut(alesage_rond(ALESAGE_SERRE))


# ---------------------------------------------------------------------------
# Châssis
# ---------------------------------------------------------------------------
def chassis_test() -> cq.Workplane:
    x0, x1 = X_SOL
    lx0, lx1, ly = LARGE_ZONE
    sol = boite(x0, x1, -Y_SOL, Y_SOL, Z_SOL_BAS, Z_SOL_HAUT).union(
        boite(lx0, lx1, -ly, ly, Z_SOL_BAS, Z_SOL_HAUT)
    )
    sol = sol.edges("|Z").fillet(1.5)

    # Passage du pignon d'escalade et de l'engrenage d'essieu
    sol = sol.cut(boite(X_ESSIEU_AV - 10, X_ESSIEU_AV + 10, -2.5, Y_ENGRENAGES[1] + 1.2, Z_SOL_BAS - 1, Z_SOL_HAUT + 1))

    # Aimants N52 scellés de part et d'autre du canal (pause d'impression à z_print = PEAU + AIMANT_z)
    ax, ay, az = AIMANT
    for sy in (1, -1):
        yc = sy * Y_AIMANT
        bossage = boite(X_AIMANT - ax / 2 - 0.8, X_AIMANT + ax / 2 + 0.8, yc - ay / 2 - 0.8, yc + ay / 2 + 0.8,
                        Z_SOL_BAS, Z_SOL_BAS + PEAU + az + 0.1 + PEAU)
        sol = sol.union(bossage)
        sol = sol.cut(boite(X_AIMANT - ax / 2 - 0.1, X_AIMANT + ax / 2 + 0.1, yc - ay / 2 - 0.1, yc + ay / 2 + 0.1,
                            Z_SOL_BAS + PEAU, Z_SOL_BAS + PEAU + az + 0.1))

    # Paliers fermés (4 blocs) avec trou de passage de la tige
    dx, yi, ye, zh = PALIER
    for xe in (X_ESSIEU_AV, X_ESSIEU_AR):
        for s in (1, -1):
            bloc = boite(xe - dx, xe + dx, yi if s > 0 else -ye, ye if s > 0 else -yi, Z_SOL_HAUT - 0.1, zh)
            if xe == X_ESSIEU_AR and s > 0:
                bloc = bloc.union(boite(xe - dx, xe + dx, yi, ye, zh - 0.1, 30.0))
            sol = sol.union(bloc.edges("|Y and >Z").fillet(1.5))
        sol = sol.cut(cylindre_y(xe, Z_ESSIEU, ALESAGE_PALIER / 2, -ye - 1, ye + 1))

    # Loge du capteur Hall (TO-92) face à l'aimant de la roue codeur (arrière gauche)
    sol = sol.cut(boite(X_ESSIEU_AR - 2.4, X_ESSIEU_AR + 2.4, ye - 1.7, ye + 0.1,
                        Z_ESSIEU + R_AIMANT_CODEUR - 2.2, 30.5))

    # Poteaux du bac à piles et poteau de la cheminée (trou Ø 2,5 pour vis M3 auto-taraudeuse)
    for px, py, pr, ph in [p + (Z_BAC,) for p in POTEAUX] + [(X_CHEMINEE, 0.0, 2.8, CHAUDIERE[2])]:
        poteau = cq.Workplane("XY").workplane(offset=Z_SOL_HAUT - 0.1).center(px, py).circle(pr).extrude(ph - Z_SOL_HAUT + 0.1)
        sol = sol.union(poteau).cut(
            cq.Workplane("XY").workplane(offset=ph - 10).center(px, py).circle(1.25).extrude(11)
        )

    # Trous de fixation du support moteur (vis M2 auto-taraudeuses)
    for hx, hy in trous_support():
        sol = sol.cut(cq.Workplane("XY").workplane(offset=Z_SOL_BAS - 1).center(hx, hy).circle(0.85).extrude(EP_SOL + 2))

    # Attelages au-dessus de la crémaillère : crochet à pion à l'avant, anneau à l'arrière
    yc_, zc_ = CANAL
    px, pr, pz = ATTELAGE_PION
    crochet = boite(x1 - 2, px + 3, -3, 3, zc_, zc_ + 3).edges("|Z and >X").fillet(2.9)
    crochet = crochet.union(boite(x1 - 4, x1, -3, 3, Z_SOL_BAS, zc_ + 0.1))
    crochet = crochet.union(cq.Workplane("XY").workplane(offset=zc_ + 2.9).center(px, 0).circle(pr).extrude(pz - zc_ - 2.9))
    ax_, ar_ = ATTELAGE_ANNEAU
    anneau = boite(ax_ - ar_ - 2.5, x0 + 2, -ar_ - 2.5, ar_ + 2.5, zc_ + 3, zc_ + 6).edges("|Z and <X").fillet(ar_ + 2.4)
    anneau = anneau.union(boite(x0, x0 + 4, -ar_ - 2.5, ar_ + 2.5, Z_SOL_BAS, zc_ + 3.1))
    anneau = anneau.cut(cq.Workplane("XY").center(ax_, 0).circle(ar_).extrude(40))
    piece = sol.union(crochet).union(anneau)
    # Canal central sous toute la longueur pour la crémaillère des rails Funky
    return piece.cut(boite(x0 - 20, x1 + 20, -yc_, yc_, Z_SOL_BAS - 1, zc_))


def trous_support() -> list[tuple[float, float]]:
    """Deux vis M2 dans la zone élargie du plancher, hors de la roue avant droite (x < 10)."""
    return [(3.0, -14.5), (7.0, -14.5)]


# ---------------------------------------------------------------------------
# Support moteur, bac à piles et coque
# ---------------------------------------------------------------------------
def boite_moteur() -> tuple[float, float, float, float, float, float]:
    """Enveloppe du réducteur (x0, x1, y0, y1, z0, z1) en repère loco, d'après MOTEUR."""
    xo, zo = position_arbre_moteur()
    bx, by, bz, hz = MOTEUR["boite_x"], MOTEUR["boite_y"], MOTEUR["boite_z"], MOTEUR["arbre_z"]
    y1 = Y_ENGRENAGES[0] - 1.0          # Face d'où sort l'arbre, 1 mm avant l'engrenage
    return xo - bx / 2, xo + bx / 2, y1 - by, y1, zo - hz, zo - hz + bz


def support_moteur() -> cq.Workplane:
    """Socle sous le réducteur + joues latérales + dos, fixé au plancher par 2 vis M2 (trous oblongs)."""
    x0, x1, y0, y1, z0, z1 = boite_moteur()
    j = 0.2
    e = 2.0
    socle = boite(x0 - e, x1 + e, y0 - e, y1, Z_SOL_HAUT, z0)
    joues = boite(x0 - e, x0 - j, y0 - e, y1, z0 - 0.1, z0 + 8).union(boite(x1 + j, x1 + e, y0 - e, y1, z0 - 0.1, z0 + 8))
    dos = boite(x0 - e, x1 + e, y0 - e, y0 - j, z0 - 0.1, z1 - 4)
    patte = boite(x0 - e, 9.5, -17.0, y0 - e + 0.1, Z_SOL_HAUT, Z_SOL_HAUT + 3)
    piece = socle.union(joues).union(dos).union(patte)
    for hx, hy in trous_support():
        oblong = cq.Workplane("XY").workplane(offset=Z_SOL_HAUT - 1).center(hx, hy).slot2D(3.0, 2.4, 0).extrude(6)
        piece = piece.cut(oblong)
    # Dégagement du pignon d'escalade et de la roue avant droite
    piece = piece.cut(cylindre_y(X_ESSIEU_AV, Z_ESSIEU, 9.4, -3.0, 3.0))
    piece = piece.cut(cylindre_y(X_ESSIEU_AV, Z_ESSIEU, ROUE_RAYON + 1.0, -Y_ROUE_INT - ROUE_LARGEUR - 1, -Y_ROUE_INT + 1.0))
    # Fente pour collier de serrage autour du réducteur
    piece = piece.cut(boite(x0 - e - 1, x1 + e + 1, y0 - e - 1, y1 + 1, z0 + 4, z0 + 6.5).cut(boite(x0 - j, x1 + j, y0 - j, y1 + 1, z0 - 1, z1)))
    return piece


def bac_piles() -> cq.Workplane:
    """Bac 3×AAA en série sur 4 poteaux : fond fraisé, nervures de calage, abouts à fentes de contact.

    Contacts du commerce (plaque, ressort, double ressort-plaque) glissés dans les fentes par le haut :
    avant = simple (pile y = -11) + double (piles 0 et +11) ; arrière = double (-11 et 0) + simple (+11).
    """
    x0, x1 = BAC_X
    z0, zf = Z_BAC, Z_BAC + EP_BAC
    lev, fen, par = BOUT_BAC
    ym = Y_PILES[-1] + PILE[0] / 2 + 1.0                    # 17,25 : demi-largeur des abouts
    bac = boite(x0, x1, -BAC_Y, BAC_Y, z0, zf).edges("|Z").fillet(2.0)
    bout = lev + fen + par
    for xa, xb in ((x0, x0 + bout), (x1 - bout, x1)):
        bac = bac.union(boite(xa, xb, -ym, ym, zf - 0.1, Z_HAUT_BAC))
    # Fentes des contacts (séparation isolante de 0,8 entre contact simple et contact double)
    yi = [y - PILE[0] / 2 for y in Y_PILES]
    sep_av, sep_ar = (yi[1] - 0.8, yi[1] - 0.1), (yi[2] - 0.6, yi[2] + 0.1)
    for xf, sep in ((x1 - par - fen, sep_av), (x0 + par, sep_ar)):
        for ya, yb in ((-ym + 0.8, sep[0]), (sep[1], ym - 0.8)):
            bac = bac.cut(boite(xf, xf + fen, ya, yb, zf, Z_HAUT_BAC + 1))
    # Fenêtres des lèvres (le ressort ou le téton du contact touche la pile)
    for xl in (x0 + par + fen - 0.1, x1 - bout - 0.1):
        for y in Y_PILES:
            bac = bac.cut(boite(xl, xl + lev + 0.2, y - 3.0, y + 3.0, zf + 1.5, Z_HAUT_BAC + 1))
    # Encoches de sortie des fils (contacts simples)
    for xw, y in ((x1 - par - 0.1, Y_PILES[0]), (x0 - 0.1, Y_PILES[2])):
        bac = bac.cut(boite(xw, xw + par + 0.2, y - 1.0, y + 1.0, Z_HAUT_BAC - 3, Z_HAUT_BAC + 1))
    # Nervures de calage entre les piles et sur les bords, interrompues aux vis
    xa, xb = x0 + bout, x1 - bout
    nervures = [(y - 0.4, y + 0.4, 1.2) for y in (-5.5, 5.5)] + [(s * 16.6, s * 17.4, 3.0) for s in (1,)] + [(-17.4, -16.6, 3.0)]
    for ya, yb, h in nervures:
        n = boite(xa, xb, ya, yb, zf - 0.1, zf + h)
        for px, py, _ in POTEAUX:
            if ya - 3.5 < py < yb + 3.5:
                n = n.cut(boite(px - 3.6, px + 3.6, ya - 1, yb + 1, zf - 1, zf + h + 1))
        bac = bac.union(n)
    # Vis M3 fraisées (90°) dans les poteaux
    for px, py, _ in POTEAUX:
        bac = bac.cut(cq.Workplane("XY").workplane(offset=z0 - 1).center(px, py).circle(1.7).extrude(EP_BAC + 2))
        cone = cq.Solid.makeCone(1.7, 3.3, 1.6, pnt=cq.Vector(px, py, zf - 1.5))
        bac = bac.cut(cq.Workplane("XY").add(cone)).cut(
            cq.Workplane("XY").workplane(offset=zf + 0.09).center(px, py).circle(3.3).extrude(4))
    return bac


def piles() -> cq.Workplane:
    """Les 3 piles AAA en place (contrôles uniquement)."""
    d, l = PILE
    xa = BAC_X[0] + sum(BOUT_BAC) + 0.6
    zc = Z_BAC + EP_BAC + d / 2 + 0.02
    p = None
    for y in Y_PILES:
        cyl = cq.Workplane("YZ", origin=(xa, 0, 0)).center(y, zc).circle(d / 2).extrude(l)
        p = cyl if p is None else p.union(cyl)
    return p


def _profil_yz(x0: float, x1: float, pts, arcs=()) -> cq.Workplane:
    """Prisme le long de X d'un polygone (y, z) ; arcs = {indice: point milieu} pour les arcs à 3 points."""
    w = cq.Workplane("YZ", origin=(x0, 0, 0)).moveTo(*pts[0])
    arcs = dict(arcs)
    for i in range(1, len(pts)):
        w = w.threePointArc(arcs[i], pts[i]) if i in arcs else w.lineTo(*pts[i])
    return w.close().extrude(x1 - x0)


def _chaudiere(x0: float, x1: float, r: float, z_bas: float) -> cq.Workplane:
    zc = CHAUDIERE[1]
    return _profil_yz(x0, x1, [(r, z_bas), (r, zc), (-r, zc), (-r, z_bas)], {2: (0, zc + r)})


def _cavite_chaudiere(x0: float, x1: float, r: float, z_bas: float) -> cq.Workplane:
    """Intérieur sans surplomb > 45° : cercle jusqu'à 45°, tangentes à 45°, méplat ponté au plafond."""
    zc, zp = CHAUDIERE[1], CHAUDIERE[2]
    a, m = r / math.sqrt(2), (r * math.cos(math.radians(22.5)), r * math.sin(math.radians(22.5)))
    f = zc + r * math.sqrt(2) - zp
    pts = [(r, z_bas), (r, zc), (a, zc + a), (f, zp), (-f, zp), (-a, zc + a), (-r, zc), (-r, z_bas)]
    return _profil_yz(x0, x1, pts, {2: (m[0], zc + m[1]), 6: (-m[0], zc + m[1])})


def _cavite_caisse(x0: float, x1: float, z_plafond: float, chanfrein: float = 4.0) -> cq.Workplane:
    w = COQUE_Y - COQUE_EP
    c_ = chanfrein
    pts = [(w, Z_COQUE_BAS - 1), (w, z_plafond - c_), (w - c_, z_plafond), (-w + c_, z_plafond), (-w, z_plafond - c_), (-w, Z_COQUE_BAS - 1)]
    return _profil_yz(x0, x1, pts)


def cotes_coque() -> dict[str, float]:
    """Cotes de la coque qui dépendent du moteur (à recaler avec MOTEUR)."""
    xo, _ = position_arbre_moteur()
    x0, x1, y0, y1, z0, z1 = boite_moteur()
    haut_carter = z1 + MOTEUR["carter_l"]
    plafond = haut_carter + 0.6
    return {
        "x_cabine_av": xo + MOTEUR["carter_d"] / 2 + JEU_POSE + COQUE_EP,
        "plafond_cabine": plafond,
        "toit": plafond + 1.5,
    }


def coque_vapeur() -> cq.Workplane:
    """Coque « vapeur stylisée » : soute (piles), cabine (moteur), chaudière à tablier et cheminée.

    Imprimée ouverture en bas (z = 24 sur le plateau), sans supports : chanfreins à 45° sous les plafonds,
    corbeaux à 45° sous le tablier, la lèvre et l'étagère de l'interrupteur ; plafonds pontés.
    Pose : accrocher la lèvre arrière sous le fond du bac, basculer le nez, visser dans la cheminée (M3).
    """
    k = cotes_coque()
    xa, xc, xs = X_COQUE_AR, k["x_cabine_av"], X_SOUTE_CABINE
    Y, e, zb = COQUE_Y, COQUE_EP, Z_COQUE_BAS
    r_ch, zc, zp = CHAUDIERE
    r_in = r_ch - e
    w = Y - e

    # --- Volumes extérieurs
    soute = boite(xa, xs + 1, -Y, Y, zb, Z_TOIT_SOUTE).edges("|Z and <X").fillet(4.0)
    cabine = boite(xs, xc, -Y, Y, zb, k["toit"]).edges(">Z").fillet(2.0)
    avant = boite(xc - 3, X_COQUE_AV, -Y, Y, zb, Z_TABLIER).edges("|Z and >X").fillet(3.0)
    chaudiere = _chaudiere(xc - 1, X_COQUE_AV, r_ch, Z_TABLIER - 0.1)
    cheminee = (cq.Workplane("XY").workplane(offset=zc).center(X_CHEMINEE, 0).circle(5.0).extrude(k["toit"] - 2.5 - zc)
                .union(cq.Workplane("XY").add(cq.Solid.makeCone(5.0, 7.0, 2.0, pnt=cq.Vector(X_CHEMINEE, 0, k["toit"] - 2.5))))
                .union(cq.Workplane("XY").workplane(offset=k["toit"] - 0.5).center(X_CHEMINEE, 0).circle(7.0).extrude(0.5)))
    coque = soute.union(cabine).union(avant).union(chaudiere).union(cheminee)
    for s in (1, -1):    # Lanternes (LED Ø 5) aux coins du tablier
        lanterne = boite(35.5, 41.0, *sorted((s * 15.5, s * 21.0)), Z_TABLIER - 0.1, Z_TABLIER + 7.5).edges(">Z").fillet(1.0)
        coque = coque.union(lanterne)

    # --- Cavités
    coque = coque.cut(_cavite_caisse(xa + e, xs + e, Z_TOIT_SOUTE - 1.7))
    coque = coque.cut(_cavite_caisse(xs + e, xc - e, k["plafond_cabine"]))
    pts = [(w, zb - 1), (w, Z_TABLIER - 1.5 - (w - r_in)), (r_in, Z_TABLIER - 1.5), (-r_in, Z_TABLIER - 1.5),
           (-w, Z_TABLIER - 1.5 - (w - r_in)), (-w, zb - 1)]
    coque = coque.cut(_profil_yz(xc - e, X_COQUE_AV - 2.5, pts))          # Sous le tablier (corbeaux à 45°)
    coque = coque.cut(_cavite_chaudiere(xc - e, X_COQUE_AV - e, r_in, zb - 1))

    # Cheminée : alésage de la tête de vis (appui sur 1,6 mm de plafond) + passage M3
    coque = coque.cut(cq.Workplane("XY").workplane(offset=zp + e).center(X_CHEMINEE, 0).circle(3.1).extrude(10))
    coque = coque.cut(cq.Workplane("XY").workplane(offset=zp - 1).center(X_CHEMINEE, 0).circle(1.7).extrude(e + 2))
    # Lanternes : trou de LED Ø 5,2 vers l'avant + passage de fils Ø 3 vers la chaudière
    for s in (1, -1):
        coque = coque.cut(cq.Workplane("YZ", origin=(35.0, 0, 0)).center(s * 18.3, Z_TABLIER + 3.6).circle(2.6).extrude(7.5))
        coque = coque.cut(cylindre_y(37.5, Z_TABLIER + 3.6, 1.5, *sorted((s * 13.5, s * 18.3))))
    # Fenêtre du capteur ToF VL53L0X dans la traverse avant (décalée à gauche du poteau de cheminée)
    coque = coque.cut(boite(X_COQUE_AV - 3, X_COQUE_AV + 1, 7.0, 13.0, 26.5, 30.5))
    # Bouton Push & Go : opercule de 0,4 mm sur le dessus de la chaudière, à percer en mode Alpha
    coque = coque.cut(cq.Workplane("XY").workplane(offset=zp - 1).center(25.0, 0).circle(3.5).extrude(r_ch + zc - zp + 1 - 0.4))
    # Fenêtres décoratives (creux de 0,8) : cabine côtés + façade de cabine au-dessus de la chaudière
    for s in (1, -1):
        for fx in ((xs + 2.5, xs + 13.5), (xs + 16.5, xc - 4.0)):
            creux = (cq.Workplane("XZ", origin=(0, s * Y + s * 0.01, 0)).center((fx[0] + fx[1]) / 2, 51.0)
                     .rect(fx[1] - fx[0], 9.0).extrude(0.81 if s > 0 else -0.81))
            coque = coque.cut(creux)
        coque = coque.cut(cq.Workplane("YZ", origin=(xc - 0.8, 0, 0)).center(s * 11.0, k["toit"] - 3.8).circle(2.5).extrude(1.0))

    # --- Lèvre arrière (sous le fond du bac), avec corbeau à 45°
    ll, lz, ly0, ly1 = LEVRE
    for s in (1, -1):
        ya, yb = sorted((s * ly0, s * ly1))
        coque = coque.union(boite(xa + e - 0.1, xa + e + ll, ya, yb, lz - 2.2, lz))
        corbeau = (cq.Workplane("XZ", origin=(0, yb, 0)).polyline(
            [(xa + e - 0.1, lz - 2.2), (xa + e + ll, lz - 2.2), (xa + e - 0.1, lz - 2.2 - ll - 0.1)]).close().extrude(yb - ya))
        coque = coque.union(corbeau)

    # --- Logement de l'interrupteur (flanc droit, cabine) : fente du levier, glissières, étagère
    i = INTERRUPTEUR
    xi, zi0 = i["x"], i["z_bas"]
    yw = -w
    coque = coque.cut(boite(xi - 1.0, xi + 1.0, -Y - 1, yw + 0.1, zi0 + i["l"] / 2 - 2.25, zi0 + i["l"] / 2 + 2.25))
    yi1 = yw + i["h"] + 0.5
    g0, g1 = i["w"] / 2 + 0.15, i["w"] / 2 + 1.35
    for s in (1, -1):
        coque = coque.union(boite(*sorted((xi + s * g0, xi + s * g1)), yw - 0.1, yi1, zi0 - 1.0, zi0 + i["l"] + 0.1))
        coque = coque.union(boite(*sorted((xi + s * g0, xi + s * (g0 - 0.6))), yi1 - 0.5, yi1, zi0 - 1.0, zi0 + i["l"] + 0.1))
    coque = coque.union(boite(xi - g1, xi + g1, yw - 0.1, yi1, zi0 - 1.0, zi0))
    corbeau = (cq.Workplane("YZ", origin=(xi - g1, 0, 0)).polyline(
        [(yw - 0.1, zi0 - 1.0), (yi1, zi0 - 1.0), (yw - 0.1, zi0 - 1.0 - (yi1 - yw))]).close().extrude(2 * g1))
    return coque.union(corbeau)


def interrupteur() -> cq.Workplane:
    """Corps de l'interrupteur en place (contrôles uniquement)."""
    i = INTERRUPTEUR
    yw = -(COQUE_Y - COQUE_EP)
    return boite(i["x"] - i["w"] / 2, i["x"] + i["w"] / 2, yw + 0.02, yw + i["h"], i["z_bas"] + 0.02, i["z_bas"] + i["l"])


PIVOT_POSE = (X_COQUE_AR + COQUE_EP + LEVRE[0], LEVRE[1])   # Arête de la lèvre, autour de laquelle on bascule la coque


# ---------------------------------------------------------------------------
# Assemblage (repère loco) — pour les contrôles
# ---------------------------------------------------------------------------
def assemblage() -> dict[str, cq.Workplane]:
    pieces: dict[str, cq.Workplane] = {"chassis": chassis_test(), "support": support_moteur(), "bac": bac_piles(),
                                       "coque": coque_vapeur(), "interrupteur": interrupteur()}
    y_ext = Y_ROUE_INT + ROUE_LARGEUR
    for nom, xe in (("av", X_ESSIEU_AV), ("ar", X_ESSIEU_AR)):
        base = roue(codeur=(nom == "ar"))
        gauche = base.rotate((0, 0, 0), (1, 0, 0), 90).translate((xe, y_ext, Z_ESSIEU))
        pieces[f"roue_{nom}_g"] = gauche
        pieces[f"roue_{nom}_d"] = gauche.mirror("XZ")
        pieces[f"tige_{nom}"] = cylindre_y(xe, Z_ESSIEU, 1.5, -y_ext, y_ext)
    pieces["pignon"] = vers_axe_y(pignon(), -1.5, X_ESSIEU_AV, Z_ESSIEU)
    pieces["engr_essieu"] = vers_axe_y(engrenage_essieu(), Y_ENGRENAGES[0], X_ESSIEU_AV, Z_ESSIEU)
    xo, zo = position_arbre_moteur()
    pieces["engr_moteur"] = vers_axe_y(engrenage_moteur(), Y_ENGRENAGES[0], xo, zo)
    x0, x1, y0, y1, z0, z1 = boite_moteur()
    moteur = boite(x0, x1, y0, y1, z0, z1).union(
        cq.Workplane("XY").workplane(offset=z1).center(xo, (y0 + y1) / 2).circle(MOTEUR["carter_d"] / 2).extrude(MOTEUR["carter_l"])
    )
    pieces["moteur"] = moteur
    pieces["arbre_moteur"] = cylindre_y(xo, zo, MOTEUR["arbre_d"] / 2, y1 - 0.01, y1 + MOTEUR["arbre_l"])
    pieces["piles"] = piles()
    return pieces


def scenes_visualiseur() -> dict:
    """Placements (repère monde, mm) des STL pour les scènes du visualiseur : t = translation,
    rx / rz = rotations en degrés (M = T · Rz · Rx), e = direction d'éclatement."""
    xo, zo = position_arbre_moteur()
    y_ext = Y_ROUE_INT + ROUE_LARGEUR
    ya, yb = Y_ENGRENAGES
    loco = [
        {"key": "loco_chassis_test.stl", "t": [0, 0, Z_SOL_BAS], "e": [0, 0, 0]},
        {"key": "loco_support_moteur.stl", "t": [0, 0, Z_SOL_HAUT], "e": [0, -12, 18]},
        {"key": "loco_bac_piles.stl", "t": [0, 0, Z_BAC], "e": [0, 0, 30]},
        {"key": "loco_coque_vapeur.stl", "t": [0, 0, Z_COQUE_BAS], "e": [0, 0, 70]},
        {"key": "loco_roue_24mm.stl", "t": [X_ESSIEU_AV, y_ext, Z_ESSIEU], "rx": 90, "e": [0, 16, 0]},
        {"key": "loco_roue_24mm.stl", "t": [X_ESSIEU_AV, -y_ext, Z_ESSIEU], "rx": -90, "e": [0, -16, 0]},
        {"key": "loco_roue_24mm_codeur.stl", "t": [X_ESSIEU_AR, y_ext, Z_ESSIEU], "rx": 90, "e": [0, 16, 0]},
        {"key": "loco_roue_24mm.stl", "t": [X_ESSIEU_AR, -y_ext, Z_ESSIEU], "rx": -90, "e": [0, -16, 0]},
        {"key": "loco_pignon_central_essieu.stl", "t": [X_ESSIEU_AV, -1.5, Z_ESSIEU], "rx": -90, "e": [0, 0, -14]},
        {"key": "loco_engrenage_essieu.stl", "t": [X_ESSIEU_AV, ya, Z_ESSIEU], "rx": -90, "e": [0, 8, -8]},
        {"key": "loco_engrenage_moteur.stl", "t": [xo, ya, zo], "rx": -90, "e": [0, 10, 10]},
    ]
    xa, ya_, _ = c.deplacement_courbe()
    voie = [
        {"key": "rail_droit_100mm_snapfit.stl", "t": [-100, 0, 0], "e": [-14, 0, 0]},
        {"key": "rail_droit_100mm_snapfit.stl", "t": [0, 0, 0], "e": [0, 0, 0]},
        {"key": "rail_funky_cremaillere_captif.stl", "t": [100, 0, 0], "e": [14, 0, 0]},
        {"key": "adaptateur_rail_bois.stl", "t": [200, 0, 0], "e": [28, 0, 0]},
    ]
    circuit = [
        {"key": "pilier_verrouillable_25mm.stl", "t": [-200, 80, 0], "e": [0, 10, 0]},
        {"key": "pilier_verrouillable_duplo.stl", "t": [-120, 80, 0], "e": [0, 10, 0]},
        {"key": "rail_droit_100mm_snapfit.stl", "t": [-300, 0, 0], "e": [-14, 0, 0]},
        {"key": "rail_cote_100mm_strie.stl", "t": [-200, 0, 0], "e": [-7, 0, 0]},
        {"key": "rail_droit_100mm_snapfit.stl", "t": [-100, 0, 0], "e": [0, 0, 0]},
        {"key": "rail_courbe_45deg_snapfit.stl", "t": [0, 0, 0], "e": [10, 0, 0]},
        {"key": "rail_courbe_45deg_snapfit.stl", "t": [xa, ya_, 0], "rz": 45, "e": [20, 10, 0]},
    ]
    # Base des rails posée sur la grille du visualiseur (z = -55)
    for inst in voie + loco + circuit:
        inst["t"][2] -= 55.0
    return {
        "assembly": {"titre": "Locomotive V2 (châssis-test + bac + coque vapeur) sur rails (droit, droit, Funky, adaptateur bois)",
                     "instances": voie + loco},
        "circuit": {"titre": "Voie V2 : droit, côte striée, droit, 2 courbes 45°, piliers 25 et 50 mm",
                    "instances": circuit},
    }


def main() -> None:
    def a_plat(piece: cq.Workplane) -> cq.Workplane:
        return piece.translate((0, 0, -piece.val().BoundingBox().zmin))

    c.exporter(a_plat(chassis_test()), "loco_chassis_test")
    c.exporter(roue(), "loco_roue_24mm")
    c.exporter(roue(codeur=True), "loco_roue_24mm_codeur")
    c.exporter(pignon(), "loco_pignon_central_essieu")
    c.exporter(engrenage_essieu(), "loco_engrenage_essieu")
    c.exporter(engrenage_moteur(), "loco_engrenage_moteur")
    c.exporter(a_plat(support_moteur()), "loco_support_moteur")
    c.exporter(a_plat(bac_piles()), "loco_bac_piles")
    c.exporter(a_plat(coque_vapeur()), "loco_coque_vapeur")
    k = cotes_coque()
    print(f"Coque : toit à z = {k['toit']:.2f} (tunnel 62,5), façade de cabine en x = {k['x_cabine_av']:.2f}")
    import json
    (c.DOSSIER_CAO / "scenes-visualiseur.json").write_text(
        json.dumps(scenes_visualiseur(), ensure_ascii=False, indent=1), encoding="utf-8"
    )
    xo, zo = position_arbre_moteur()
    print(f"Arbre moteur en x = {xo:.2f}, z = {zo:.2f} (entraxe {entraxe():.2f} mm, ×{DENTS_MOTEUR / DENTS_ESSIEU:.2f})")


if __name__ == "__main__":
    main()
