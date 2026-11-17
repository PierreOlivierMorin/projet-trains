#!/usr/bin/env python3
"""Générateur CadQuery de la locomotive Alpha V2 — mode châssis-test (decisions-locomotive-v2.md).

Pièces :
- loco_chassis_test           : châssis (paliers fermés, aimant N52 scellé, loge capteur Hall,
                                crochet avant / anneau arrière, poteaux du plateau piles)
- loco_roue_24mm              : roue Ø 24 × 3,5 mm bombée, sans boudin, gorge de pneu (×3)
- loco_roue_24mm_codeur       : même roue avec loge scellée pour aimant Ø 3 × 1 (essieu libre, ×1)
- loco_pignon_central_essieu  : pignon d'escalade 12 dents (crémaillère Funky)
- loco_engrenage_essieu       : engrenage 14 dents m1 sur l'essieu moteur
- loco_engrenage_moteur       : engrenage 20 dents m1 sur l'arbre en D du N20 (multiplie ×1,43)
- loco_support_moteur         : support du N20 à vis sans fin (cotes MOTEUR à recaler sur le moteur reçu)
- loco_plateau_piles          : plateau au-dessus des roues pour un boîtier 3×AAA (fixation par sangles)

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

POTEAUX = [(-7.0, 19.0), (-7.0, -19.0), (-38.0, 6.0), (-38.0, -6.0)]
Z_PLATEAU = 35.0                    # Au-dessus du sommet des roues (z = 33)
EP_PLATEAU = 2.0

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

    # Poteaux du plateau piles (trou Ø 2,5 pour vis M3 auto-taraudeuse)
    for px, py in POTEAUX:
        poteau = cq.Workplane("XY").workplane(offset=Z_SOL_HAUT - 0.1).center(px, py).circle(3.0).extrude(Z_PLATEAU - Z_SOL_HAUT + 0.1)
        sol = sol.union(poteau).cut(
            cq.Workplane("XY").workplane(offset=Z_PLATEAU - 8).center(px, py).circle(1.25).extrude(9)
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
# Support moteur et plateau piles
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


def plateau_piles() -> cq.Workplane:
    """Plateau à z = 35 sur 4 poteaux ; fentes de sangle pour un boîtier 3×AAA ; dégagement d'engrenage."""
    p = boite(-45.0, -0.5, -22.0, 22.0, Z_PLATEAU, Z_PLATEAU + EP_PLATEAU).edges("|Z").fillet(3.0)
    for px, py in POTEAUX:
        p = p.cut(cq.Workplane("XY").workplane(offset=Z_PLATEAU - 1).center(px, py).circle(1.7).extrude(5))
    for sx in (-34.0, -14.0):
        for sy in (-20.0, 20.0):
            p = p.cut(boite(sx - 1.5, sx + 1.5, sy - 1.0, sy + 1.0, Z_PLATEAU - 1, Z_PLATEAU + 5).translate((0, 0, 0)))
    return p


# ---------------------------------------------------------------------------
# Assemblage (repère loco) — pour les contrôles
# ---------------------------------------------------------------------------
def assemblage() -> dict[str, cq.Workplane]:
    pieces: dict[str, cq.Workplane] = {"chassis": chassis_test(), "support": support_moteur(), "plateau": plateau_piles()}
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
    pieces["piles"] = boite(-44.5, -0.5, -15.75, 15.75, Z_PLATEAU + EP_PLATEAU, Z_PLATEAU + EP_PLATEAU + 10.5)
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
        {"key": "loco_plateau_piles.stl", "t": [0, 0, Z_PLATEAU], "e": [0, 0, 32]},
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
        "assembly": {"titre": "Châssis-test V2 sur rails (droit, droit, Funky, adaptateur bois)",
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
    plateau = plateau_piles()
    c.exporter(a_plat(plateau), "loco_plateau_piles")
    import json
    (c.DOSSIER_CAO / "scenes-visualiseur.json").write_text(
        json.dumps(scenes_visualiseur(), ensure_ascii=False, indent=1), encoding="utf-8"
    )
    xo, zo = position_arbre_moteur()
    print(f"Arbre moteur en x = {xo:.2f}, z = {zo:.2f} (entraxe {entraxe():.2f} mm, ×{DENTS_MOTEUR / DENTS_ESSIEU:.2f})")


if __name__ == "__main__":
    main()
