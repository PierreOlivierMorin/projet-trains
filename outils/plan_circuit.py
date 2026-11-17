#!/usr/bin/env python3
"""Plan du circuit de test : 8 inscrit dans un ovale (decisions-cao-v2.md §5).

Compose les pièces de voie en vue de dessus, puis vérifie :
- la fermeture exacte de chaque boucle (écart de position et d'angle à chaque raccord) ;
- l'absence de chevauchement entre pièces non raccordées (axes de voie à ≥ 42 mm, sauf au croisement) ;
- le genre des jonctions (chaque tronçon entre deux nœuds doit avoir une prise femelle à un bout
  et un mâle à l'autre, sinon il faut un adaptateur F-F ou M-M) ;
et produit le plan SVG, l'encombrement et la nomenclature.

Géométrie (repère : centre du croisement à l'origine, X le long de l'ovale) :
- les extrémités de l'ovale sont partagées par le 8 et l'ovale (comme les coffrets classiques) ;
- 4 aiguillages (2 communications) sur les grands côtés, voie déviée = courbe standard 45° ;
- croisement à niveau à 90° au centre ;
- viaduc sur le grand côté haut, gare (voie de garage + butoir) et tunnel sur le grand côté bas.

Usage : .venv/bin/python outils/plan_circuit.py [--viaduc 50] [--svg chemin]
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

CAO = Path(__file__).resolve().parent.parent / "03-cao-3d"
sys.path.insert(0, str(CAO))
import cao_commun as c  # noqa: E402

R = 180.0
DX, DY, _ = c.deplacement_courbe(R, 45.0)
LARGEUR = c.RAIL_LARGEUR
ECART_MIN = LARGEUR + 2.0
RAMPE_PIECE = 100.0          # Pied, milieu et tête de rampe : 100 mm en plan
TABLIER = 100.0


# ---------------------------------------------------------------------------
# Poses et pièces
# ---------------------------------------------------------------------------
@dataclass
class Pose:
    x: float
    y: float
    a: float  # degrés

    def avance(self, dx: float, dy: float, da: float) -> "Pose":
        r = math.radians(self.a)
        return Pose(
            self.x + dx * math.cos(r) - dy * math.sin(r),
            self.y + dx * math.sin(r) + dy * math.cos(r),
            self.a + da,
        )


@dataclass
class Piece:
    type: str               # droit, courbe, aiguillage, croisement, rampe, tablier, balise, ajustement, garage
    nom: str
    axe: list[tuple[float, float]]
    entree: Pose
    sortie: Pose
    sens_g: int = 0         # +1 tourne à gauche, -1 à droite (dans le sens de parcours du tronçon)
    longueur: float = 0.0
    z: tuple[float, float] = (0.0, 0.0)
    infos: dict = field(default_factory=dict)


def droit(p: Pose, longueur: float, type_: str = "droit", nom: str | None = None, z=(0.0, 0.0)) -> Piece:
    s = p.avance(longueur, 0, 0)
    n = max(2, int(longueur // 10) + 1)
    axe = [(p.avance(longueur * k / (n - 1), 0, 0).x, p.avance(longueur * k / (n - 1), 0, 0).y) for k in range(n)]
    return Piece(type_, nom or f"droit {longueur:.0f}", axe, p, s, 0, longueur, z)


def courbe(p: Pose, sens: int) -> Piece:
    """Courbe 45° symétrique ; sens +1 = gauche, -1 = droite."""
    l0 = c.FEMELLE_LONGUEUR
    pts = [p.avance(0, 0, 0), p.avance(l0, 0, 0)]
    for k in range(1, 13):
        t = math.radians(45.0 * k / 12)
        pts.append(p.avance(l0 + R * math.sin(t), sens * R * (1 - math.cos(t)), 0))
    s = p.avance(DX, sens * DY, sens * 45.0)
    pts.append(s)
    return Piece("courbe", "courbe 45° " + ("gauche" if sens > 0 else "droite"),
                 [(q.x, q.y) for q in pts], p, s, sens, R * math.pi / 4 + 2 * l0)


# ---------------------------------------------------------------------------
# Composition du circuit
# ---------------------------------------------------------------------------
@dataclass
class Config:
    viaduc: float = 50.0         # Hauteur du tablier (0 = pas de viaduc)
    garage_droits: int = 1       # Droits de 100 mm dans la voie de garage avant le butoir


def chainer(depart: Pose, elements: list[tuple]) -> list[Piece]:
    pieces, p = [], depart
    for el in elements:
        if el[0] == "courbe":
            pc = courbe(p, el[1])
        else:
            kind, longueur = el[0], el[1]
            nom = el[2] if len(el) > 2 else None
            z = el[3] if len(el) > 3 else (0.0, 0.0)
            pc = droit(p, longueur, kind, nom, z)
        pieces.append(pc)
        p = pc.sortie
    return pieces


def viaduc_elements(h: float) -> list[tuple]:
    if h <= 0:
        return []
    n_m = int(round(h / c.MODULE_HAUTEUR)) - 1
    els, z = [], 0.0
    montee = [("rampe", RAMPE_PIECE, "rampe pied", 6.25)] + [("rampe", RAMPE_PIECE, "rampe milieu", 12.5)] * n_m \
        + [("rampe", RAMPE_PIECE, "rampe tête", 6.25)]
    for kind, l, nom, dz in montee:
        els.append((kind, l, nom, (z, z + dz)))
        z += dz
    els.append(("tablier", TABLIER, f"tablier {h:.0f} mm (2 piliers)", (h, h)))
    for kind, l, nom, dz in reversed(montee):
        els.append((kind, l, nom.replace("pied", "pied").replace("tête", "tête"), (z, z - dz)))
        z -= dz
    return els


def longueur(els: list[tuple]) -> float:
    return sum(e[1] for e in els if e[0] != "courbe")


GARE_MIN = DX + 50.0 + 100.0 + 50.0   # Aiguillage de gare + balise + tunnel + marge, sur le grand côté bas
BRAS_MIN, BRAS_MAX = 45.0, 95.0          # Demi-longueur d'un bras du croisement (pièce spéciale)
def _l_aig() -> float:
    """Voie directe de l'aiguillage : portée de la voie déviée, allongée juste assez pour que les
    grands côtés (2H - 2·DY + 2·DX - 2·L_AIG) tombent sur un multiple de 50 mm."""
    fin = demi_tour(Pose(0, 0, 0), 0)[-1].sortie
    T0 = -fin.y - 2 * DY
    return DX + (T0 % 50.0) / 2.0


AJUSTEMENT_MIN = 40.0                    # Un droit plus court ne peut pas contenir la prise femelle


def demi_tour(depart: Pose, n_droits: int) -> list[Piece]:
    return chainer(depart, [("courbe", -1), ("courbe", -1)] + [("droit", 100.0)] * n_droits + [("courbe", -1), ("courbe", -1)])


L_AIG = None  # Fixé après la définition de demi_tour


def composer(cfg: Config) -> dict:
    """Choisit le nombre de droits verticaux des extrémités pour loger le viaduc, puis en déduit
    toutes les longueurs. Les grands côtés sont à y = ±H ; aiguillages à tronc en x = ±s."""
    via = viaduc_elements(cfg.viaduc)
    l_via = longueur(via)
    besoin = max(l_via, GARE_MIN)
    n = 0
    while True:
        fin = demi_tour(Pose(0, 0, 0), n)[-1].sortie
        H = -fin.y / 2.0
        T = 2.0 * (H + DX - DY - L_AIG)    # Longueur d'un grand côté entre les sorties directes
        if T >= besoin:
            break
        n += 1
    s = H + DX - DY                        # La voie déviée vise exactement le centre
    demi_diag = math.sqrt(2.0) * (H - DY)  # De la sortie déviée au centre du croisement
    k = int((demi_diag - BRAS_MIN) // 50)
    l_diag, bras = 50.0 * k, demi_diag - 50.0 * k
    return {"H": H, "s": s, "T": T, "n_bouts": n, "l_diag": l_diag, "bras": bras, "via": via, "l_via": l_via}


L_AIG = _l_aig()


def remplir(longueur_: float, debut: list[tuple], fin: list[tuple]) -> list[tuple]:
    """Complète un tronçon droit avec des droits de 100, puis 50, puis un droit d'ajustement."""
    libre = longueur_ - longueur(debut) - longueur(fin)
    n100 = int(libre // 100)
    n50 = int((libre - 100 * n100) // 50)
    reste = libre - 100 * n100 - 50 * n50
    if 0.05 < reste < AJUSTEMENT_MIN:
        if n50 == 0:
            n100, n50 = n100 - 1, 1
        n50, reste = n50 - 1, reste + 50.0
    gauche = [("droit", 100.0)] * (n100 // 2) + [("droit", 50.0)] * n50
    droite = [("droit", 100.0)] * (n100 - n100 // 2)
    aj = [("ajustement", reste, f"droit d'ajustement {reste:.1f}")] if reste > 0.05 else []
    return gauche + debut + aj + fin + droite


def placer(cfg: Config, g: dict) -> list[Piece]:
    H, s = g["H"], g["s"]
    pieces: list[Piece] = []

    # Aiguillages : tronc côté extrémité de l'ovale, branches vers le centre.
    # Variantes de genre : « F » = tronc femelle / sorties mâles ; « M » = tronc mâle / sorties femelles.
    variantes = {"HD": "F", "HG": "M", "BG": "F", "BD": "M"}
    aig = {}
    for nom, x, y, a, sens in (("HD", s, H, 180, +1), ("HG", -s, H, 0, -1), ("BG", -s, -H, 0, +1), ("BD", s, -H, 180, -1)):
        p = Pose(x, y, a)
        directe = droit(p, L_AIG, "aiguillage")
        deviee = courbe(p, sens)
        aig[nom] = (p, directe.sortie, deviee.sortie)
        pieces.append(Piece("aiguillage", f"aiguillage {'gauche' if sens > 0 else 'droit'} {nom} (tronc {variantes[nom]})",
                            directe.axe + list(reversed(deviee.axe)), p, directe.sortie, sens, L_AIG,
                            infos={"deviee": deviee.sortie, "axe_dev": deviee.axe, "axe_dir": directe.axe,
                                   "variante": variantes[nom]}))

    # Extrémités de l'ovale (partagées par le 8)
    pieces += demi_tour(Pose(s, H, 0), g["n_bouts"])
    pieces += demi_tour(Pose(-s, -H, 180), g["n_bouts"])

    # Grand côté haut : viaduc centré
    pieces += chainer(aig["HG"][1], remplir(g["T"], g["via"], []))

    # Grand côté bas : aiguillage de gare (voie de garage vers l'extérieur), balise, tunnel
    T = g["T"]
    avant = remplir(T / 2 - L_AIG / 2, [], [])     # Gare centrée sur le grand côté
    avant = [e for e in avant if e[0] != "ajustement"]
    l_avant = longueur(avant)
    p_gare = aig["BG"][1].avance(l_avant, 0, 0)
    pieces += chainer(aig["BG"][1], avant)
    directe = droit(p_gare, L_AIG, "aiguillage")
    deviee = courbe(p_gare, -1)
    pieces.append(Piece("aiguillage", "aiguillage droit (gare, tronc F)", directe.axe + list(reversed(deviee.axe)),
                        p_gare, directe.sortie, -1, L_AIG,
                        infos={"deviee": deviee.sortie, "axe_dev": deviee.axe, "axe_dir": directe.axe, "variante": "F"}))
    pieces += chainer(deviee.sortie, [("courbe", +1)] + [("droit", 100.0, "droit (gare)")] * cfg.garage_droits
                      + [("balise", 50.0, "rail-balise rouge (arrêt)"), ("butoir", 60.0, "butoir")])
    apres = remplir(T - l_avant - L_AIG, [("balise", 50.0, "rail-balise jaune (klaxon)")], [("droit", 100.0, "droit (tunnel)")])
    pieces += chainer(directe.sortie, apres)

    # Diagonales et croisement (bras spéciaux : diagonale 1 femelle-femelle, diagonale 2 mâle-mâle)
    for depart in (aig["HD"][2], aig["BG"][2], aig["HG"][2], aig["BD"][2]):
        n100 = int(g["l_diag"] // 100)
        pieces += chainer(depart, [("droit", 100.0)] * n100 + [("droit", 50.0)] * int((g["l_diag"] - 100 * n100) // 50))
    for a, genre in ((45.0, "F-F"), (135.0, "M-M")):
        p = Pose(-g["bras"] * math.cos(math.radians(a)), -g["bras"] * math.sin(math.radians(a)), a)
        pc = droit(p, 2 * g["bras"], "croisement", f"croisement 90° (bras {g['bras']:.1f})")
        pc.infos["genre"] = genre
        pieces.append(pc)
    return pieces


# ---------------------------------------------------------------------------
# Contrôles
# ---------------------------------------------------------------------------
def controles(pieces: list[Piece], g: dict) -> list[str]:
    msgs = []
    # Fermeture : toutes les extrémités libres doivent coïncider deux à deux (sauf butoir)
    bouts = []
    for i, pc in enumerate(pieces):
        bouts.append((i, pc.entree))
        bouts.append((i, pc.sortie))
        if "deviee" in pc.infos:
            bouts.append((i, pc.infos["deviee"]))
    libres = []
    for i, b in bouts:
        appariee = any(
            j != i and math.hypot(b.x - o.x, b.y - o.y) < 0.05 for j, o in bouts
        )
        if not appariee:
            libres.append((pieces[i].nom, b))
    ecart_max = 0.0
    for i, b in bouts:
        d = min((math.hypot(b.x - o.x, b.y - o.y) for j, o in bouts if j != i), default=1e9)
        if d < 1.0:
            ecart_max = max(ecart_max, d)
    msgs.append(f"Fermeture : écart max aux raccords {ecart_max * 1000:.1f} µm")
    hors_butoir = [n for n, b in libres if "butoir" not in n]
    msgs.append("Extrémités non raccordées : " + (", ".join(hors_butoir) if hors_butoir else "aucune (hors butoir)"))

    # Chevauchements
    def axe(pc: Piece) -> list[tuple[float, float]]:
        if "axe_dir" in pc.infos:
            return pc.infos["axe_dir"] + pc.infos["axe_dev"]
        return pc.axe

    def coeur(pts: list[tuple[float, float]], marge: float = LARGEUR / 2 + 2) -> list[tuple[float, float]]:
        """Points de l'axe à plus de `marge` des deux extrémités (une pièce bout à bout n'est pas un conflit)."""
        cumul = [0.0]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            cumul.append(cumul[-1] + math.hypot(x2 - x1, y2 - y1))
        return [p for p, l in zip(pts, cumul) if marge <= l <= cumul[-1] - marge]

    conflits = []
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a, b = pieces[i], pieces[j]
            if {a.type, b.type} == {"croisement"}:
                continue
            raccordees = any(
                math.hypot(p.x - q.x, p.y - q.y) < 0.05
                for p in (a.entree, a.sortie, a.infos.get("deviee", a.entree))
                for q in (b.entree, b.sortie, b.infos.get("deviee", b.entree))
            )
            pa, pb = coeur(axe(a)), coeur(axe(b))
            if not pa or not pb:
                continue
            dmin = min(math.hypot(x1 - x2, y1 - y2) for x1, y1 in pa for x2, y2 in pb)
            croise_viaduc = (a.z[0] + a.z[1]) / 2 - (b.z[0] + b.z[1]) / 2
            if dmin < ECART_MIN and abs(croise_viaduc) < 60 and not raccordees:
                conflits.append(f"{a.nom} / {b.nom} ({dmin:.0f} mm)")
    msgs.append("Chevauchements : " + ("; ".join(conflits) if conflits else "aucun"))
    return msgs


def genres() -> list[str]:
    """Vérifie que chaque tronçon entre deux nœuds a une prise femelle à un bout et un mâle à l'autre.

    Genre présenté par le nœud au tronçon : tronc d'un aiguillage « F » = F, ses sorties = M ;
    variante « M » = l'inverse. Le tronçon doit présenter le genre opposé à chaque bout.
    Croisement : diagonale 1 (HD-BG) femelle aux deux bras, diagonale 2 (HG-BD) mâle aux deux bras.
    """
    var = {"HD": "F", "HG": "M", "BG": "F", "BD": "M", "GARE": "F"}
    inv = {"F": "M", "M": "F"}
    tronc = lambda n: var[n]
    sortie = lambda n: inv[var[n]]
    troncons = {
        "extrémité droite (tronc HD -> tronc BD)": (tronc("HD"), tronc("BD")),
        "extrémité gauche (tronc BG -> tronc HG)": (tronc("BG"), tronc("HG")),
        "grand côté haut (sortie HG -> sortie HD)": (sortie("HG"), sortie("HD")),
        "côté bas, gauche (sortie BG -> tronc gare)": (sortie("BG"), tronc("GARE")),
        "côté bas, droite (sortie gare -> sortie BD)": (sortie("GARE"), sortie("BD")),
        "diagonale 1 (sortie HD -> croisement F)": (sortie("HD"), "F"),
        "diagonale 1 (croisement F -> sortie BG)": ("F", sortie("BG")),
        "diagonale 2 (sortie HG -> croisement M)": (sortie("HG"), "M"),
        "diagonale 2 (croisement M -> sortie BD)": ("M", sortie("BD")),
    }
    out = []
    for nom, (a, b) in troncons.items():
        ok = a != b
        out.append(f"{'[OK]   ' if ok else '[ÉCHEC]'} {nom} : nœuds {a}/{b}" + ("" if ok else " -> adaptateur requis"))
    return out


# ---------------------------------------------------------------------------
# Sortie SVG et nomenclature
# ---------------------------------------------------------------------------
COULEURS = {
    "droit": "#3f9e7a", "courbe": "#2f8fa0", "aiguillage": "#e08a1e", "croisement": "#c0392b",
    "rampe": "#8e6bbf", "tablier": "#6c4fa0", "balise": "#e6c229", "ajustement": "#d35400",
    "butoir": "#7f8c8d",
}


def svg(pieces: list[Piece], titre: str, chemin: Path) -> tuple[float, float]:
    xs = [x for pc in pieces for x, _ in pc.axe]
    ys = [y for pc in pieces for _, y in pc.axe]
    m = 60
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    w, h = x1 - x0, y1 - y0
    traits = []
    for pc in pieces:
        coul = COULEURS.get(pc.type, "#555")
        axes = [pc.infos["axe_dir"], pc.infos["axe_dev"]] if "axe_dir" in pc.infos else [pc.axe]
        for ax in axes:
            pts = " ".join(f"{x:.1f},{-y:.1f}" for x, y in ax)
            traits.append(f'<polyline points="{pts}" fill="none" stroke="{coul}" stroke-width="{LARGEUR}" '
                          f'stroke-linecap="butt" stroke-linejoin="round" opacity="0.85"/>')
            traits.append(f'<polyline points="{pts}" fill="none" stroke="#fff" stroke-width="1.2" opacity="0.7"/>')
        jx, jy = pc.entree.x, pc.entree.y
        traits.append(f'<circle cx="{jx:.1f}" cy="{-jy:.1f}" r="2.5" fill="#222"/>')
        if pc.type in ("tablier", "butoir", "ajustement") or pc.nom.startswith(("aiguillage", "croisement", "rail-balise", "droit (tunnel)")):
            mx, my = pc.axe[len(pc.axe) // 2]
            traits.append(f'<text x="{mx:.1f}" y="{-my - 26:.1f}" font-size="14" text-anchor="middle" '
                          f'font-family="sans-serif" fill="#222">{pc.nom}</text>')
    legende = "".join(
        f'<rect x="{x0 + 20 + 150 * k:.0f}" y="{-y1 + 18:.0f}" width="14" height="14" fill="{col}"/>'
        f'<text x="{x0 + 40 + 150 * k:.0f}" y="{-y1 + 30:.0f}" font-size="14" font-family="sans-serif">{nom}</text>'
        for k, (nom, col) in enumerate(COULEURS.items())
    )
    contenu = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {-y1:.0f} {w:.0f} {h + 40:.0f}" '
        f'width="{w / 1.2:.0f}" height="{(h + 40) / 1.2:.0f}">'
        f'<rect x="{x0:.0f}" y="{-y1:.0f}" width="{w:.0f}" height="{h + 40:.0f}" fill="#faf8f3"/>'
        f'<text x="{x0 + 20:.0f}" y="{-y1 + h + 30:.0f}" font-size="22" font-family="sans-serif">{titre}</text>'
        + legende + "".join(traits) + "</svg>"
    )
    chemin.write_text(contenu, encoding="utf-8")
    return max(xs) - min(xs) + LARGEUR, max(ys) - min(ys) + LARGEUR


def nomenclature(pieces: list[Piece]) -> dict[str, int]:
    compte: dict[str, int] = {}
    for pc in pieces:
        cle = pc.nom
        if pc.type == "courbe":
            cle = "courbe 45° (pièce standard ; parcourue à l'envers en bout d'ovale)"
        if pc.type == "aiguillage":
            cle = "aiguillage " + ("gauche" if pc.sens_g > 0 else "droit") + f", tronc {pc.infos['variante']}"
        if pc.type == "droit" and pc.nom.startswith("droit ("):
            cle = "droit 100"
        if pc.type == "croisement":
            cle = pc.nom
        compte[cle] = compte.get(cle, 0) + 1
    if any(pc.type == "croisement" for pc in pieces):
        cle = next(pc.nom for pc in pieces if pc.type == "croisement")
        compte[cle] = 1
    return dict(sorted(compte.items()))


MASSES_G = {   # Masses FDM estimées (verifier_stl.py quand la pièce existe, sinon estimation)
    "droit 100": 14.0, "droit 50": 8.0, "courbe": 20.7, "aiguillage": 38.0, "croisement": 30.0,
    "rampe": 28.0, "tablier": 14.0, "rail-balise": 8.0, "butoir": 16.0, "ajustement": 7.0,
}
DEBIT_G_H = 18.0   # Débit moyen X1C en PETG, couche 0,2 mm


def masse(nom: str) -> float:
    for cle, m in MASSES_G.items():
        if nom.startswith(cle) or cle in nom:
            return m
    return 10.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--viaduc", type=float, default=50.0)
    ap.add_argument("--svg", default=None, help="Défaut : 03-cao-3d/plan-circuit-viaduc<h>.svg")
    args = ap.parse_args()
    cfg = Config(viaduc=args.viaduc)
    g = composer(cfg)
    pieces = placer(cfg, g)
    chemin = Path(args.svg) if args.svg else CAO / f"plan-circuit-viaduc{cfg.viaduc:.0f}.svg"
    larg, haut = svg(pieces, f"Circuit de test — viaduc {cfg.viaduc:.0f} mm", chemin)
    print(f"Grands côtés à y = ±{g['H']:.1f} (longueur {g['T']:.1f}) | {g['n_bouts']} droit(s) vertical(aux) par extrémité | "
          f"diagonales 4 × {g['l_diag']:.0f} mm + bras de croisement {g['bras']:.1f} mm | viaduc {g['l_via']:.0f} mm")
    print(f"Encombrement : {larg / 1000:.2f} × {haut / 1000:.2f} m")
    for m in controles(pieces, g):
        print(m)
    print("Genres des jonctions :")
    for m in genres():
        print("  " + m)
    print("Nomenclature :")
    total, n_tot = 0.0, 0
    for k, n in nomenclature(pieces).items():
        print(f"  {n:3d} × {k}")
        total += n * masse(k)
        n_tot += n
    n_piliers = 2 if cfg.viaduc > 0 else 0
    if n_piliers:
        print(f"  {n_piliers:3d} × pilier {cfg.viaduc:.0f} mm (sous le tablier)")
        total += n_piliers * (35.0 if cfg.viaduc >= 50 else 23.2)
        n_tot += n_piliers
    print(f"Total : {n_tot} pièces, ~{total / 1000:.2f} kg de filament, ~{total / DEBIT_G_H:.0f} h d'impression (estimation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
