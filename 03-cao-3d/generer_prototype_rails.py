#!/usr/bin/env python3
"""Générateur paramétrique de fichiers STL binaires pour les rails V1.

Génère 7 prototypes mécaniques de circuit prêts à trancher (Z=0 sur le plateau) :
1. rail_droit_100mm_snapfit.stl    : rail droit 100 mm avec jonction Snap-Fit + verrouillage vertical 45°
2. rail_cote_100mm_strie.stl       : rail de test de côte avec micro-stries de traction dans les rainures
3. adaptateur_rail_bois.stl        : adaptateur 50 mm (Snap-Fit femelle <-> cheville bois 11,2 mm)
4. rail_funky_cremaillere_captif.stl : rail 100 mm pour looping 360° / pente 90° (crémaillère z=14mm + loges acier + glissières captives 45°)
5. rail_courbe_45deg_snapfit.stl   : rail courbe 45° (R=180 mm, 8 pièces = cercle, Snap-Fit tangents)
6. pilier_verrouillable_duplo.stl  : pilier 50 mm à berceau verrouillable (compatible grille gros blocs)
7. tuile_action_clipsable.stl      : tuile d'action 30×19,2 mm clipsable avec canal central abaissé pour passage pignon

Dépendances : aucune (bibliothèque standard Python uniquement).
"""

import math
import os
import struct
from pathlib import Path

# --- Paramètres géométriques principaux (en mm) ---
RAIL_WIDTH = 40.0
RAIL_HEIGHT = 12.0
TRACK_GAUGE = 25.5        # Écartement centre-à-centre des rainures (standard bois)
GROOVE_WIDTH = 6.0
GROOVE_DEPTH = 3.0        # Fond de rainure à z = 9.0 mm
GROOVE_INNER_Y = TRACK_GAUGE / 2.0 - GROOVE_WIDTH / 2.0  # 9.75 mm
GROOVE_OUTER_Y = TRACK_GAUGE / 2.0 + GROOVE_WIDTH / 2.0  # 15.75 mm
HALF_W = RAIL_WIDTH / 2.0                                # 20.00 mm
CORE_HALF_W = 7.25        # Largeur demi-noyau central (laisse 2,5 mm jusqu'aux rainures)

# Couches verticales Z (mm) — incluent V-groove (45°), micro-stries (9,8) et loge acier (11,0)
Z_LEVELS = [0.0, 4.5, 6.0, 7.5, 9.0, 9.8, 11.0, 12.0]

# Tolérance d'impression 3D par face (mm)
PRINT_CLEARANCE = 0.20


def v_offset_profile(z: float) -> float:
    """Profil en V (45°) de verrouillage vertical sur la languette centrale (max 1,10 mm à z=6)."""
    if z <= 4.5 or z >= 7.5:
        return 0.0
    return 1.10 * (1.0 - abs(z - 6.0) / 1.5)


class WatertightMesh:
    """Constructeur de maillage triangulaire 3D garantissant l'annulation des faces internes."""

    def __init__(self) -> None:
        self._vert_map: dict[tuple[int, int, int], int] = {}
        self.vertices: list[tuple[float, float, float]] = []
        self._faces: dict[tuple[int, int, int], tuple[int, int, int]] = {}

    def vertex(self, x: float, y: float, z: float) -> int:
        key = (round(x * 10000), round(y * 10000), round(z * 10000))
        idx = self._vert_map.get(key)
        if idx is None:
            idx = len(self.vertices)
            self.vertices.append((key[0] / 10000.0, key[1] / 10000.0, key[2] / 10000.0))
            self._vert_map[key] = idx
        return idx

    @staticmethod
    def _canon(a: int, b: int, c: int) -> tuple[int, int, int]:
        if a <= b and a <= c:
            return (a, b, c)
        if b <= a and b <= c:
            return (b, c, a)
        return (c, a, b)

    def add_tri(self, a: int, b: int, c: int) -> None:
        if a == b or b == c or a == c:
            return
        rev_key = self._canon(a, c, b)
        if rev_key in self._faces:
            del self._faces[rev_key]
            return
        fwd_key = self._canon(a, b, c)
        if fwd_key in self._faces:
            raise ValueError(f"Triangle dupliqué détecté : {fwd_key}")
        self._faces[fwd_key] = (a, b, c)

    def add_quad(self, a: int, b: int, c: int, d: int) -> None:
        """Ajoute un quad (a,b,c,d) en orientation CCW avec choix déterministe de diagonale."""
        pts = [a, b, c, d]
        dedup: list[int] = []
        for p in pts:
            if not dedup or p != dedup[-1]:
                dedup.append(p)
        if len(dedup) > 1 and dedup[0] == dedup[-1]:
            dedup.pop()
        if len(dedup) < 3:
            return
        if len(dedup) == 3:
            self.add_tri(dedup[0], dedup[1], dedup[2])
            return
        m_idx = min(range(4), key=lambda i: dedup[i])
        r = dedup[m_idx:] + dedup[:m_idx]
        self.add_tri(r[0], r[1], r[2])
        self.add_tri(r[0], r[2], r[3])

    def add_hex(
        self,
        b00: int,
        b10: int,
        b11: int,
        b01: int,
        t00: int,
        t10: int,
        t11: int,
        t01: int,
    ) -> None:
        """Ajoute une cellule hexaédrique (b=bas z0, t=haut z1, CCW vue de dessus)."""
        self.add_quad(b00, b01, b11, b10)  # -Z
        self.add_quad(t00, t10, t11, t01)  # +Z
        self.add_quad(b00, b10, t10, t00)  # -Y
        self.add_quad(b11, b01, t01, t11)  # +Y
        self.add_quad(b01, b00, t00, t01)  # -X
        self.add_quad(b10, b11, t11, t10)  # +X

    def add_convex_prism(self, poly_xy: list[tuple[float, float]], z0: float, z1: float) -> None:
        """Extrude un polygone 2D convexe orienté CCW entre z0 et z1."""
        n = len(poly_xy)
        bot = [self.vertex(x, y, z0) for x, y in poly_xy]
        top = [self.vertex(x, y, z1) for x, y in poly_xy]
        for i in range(1, n - 1):
            self.add_tri(bot[0], bot[i + 1], bot[i])
            self.add_tri(top[0], top[i], top[i + 1])
        for i in range(n):
            j = (i + 1) % n
            self.add_quad(bot[i], bot[j], top[j], top[i])

    def triangles(self) -> list[tuple[int, int, int]]:
        return list(self._faces.values())

    def verify_manifold(self) -> tuple[int, float]:
        """Vérifie qu'aucune arête ouverte/non-manifold n'existe et que le volume signé > 0."""
        tris = self.triangles()
        edges: dict[tuple[int, int], int] = {}
        vol6 = 0.0
        for i0, i1, i2 in tris:
            for u, v in ((i0, i1), (i1, i2), (i2, i0)):
                edges[(u, v)] = edges.get((u, v), 0) + 1
            x0, y0, z0 = self.vertices[i0]
            x1, y1, z1 = self.vertices[i1]
            x2, y2, z2 = self.vertices[i2]
            vol6 += (
                x0 * (y1 * z2 - y2 * z1)
                - y0 * (x1 * z2 - x2 * z1)
                + z0 * (x1 * y2 - x2 * y1)
            )
        bad_edges = 0
        for (u, v), count in edges.items():
            if count != 1 or edges.get((v, u), 0) != 1:
                bad_edges += 1
        if bad_edges > 0:
            raise AssertionError(f"Maillage non étanche : {bad_edges} arêtes invalides")
        volume = vol6 / 6.0
        if volume <= 0.0:
            raise AssertionError(f"Normales inversées : volume signé = {volume:.2f}")
        return len(tris), volume

    def write_stl(self, filepath: Path, header_text: str) -> tuple[int, float]:
        n_tris, volume = self.verify_manifold()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        header = header_text.encode("ascii", errors="replace")[:80].ljust(80, b"\x00")
        with open(filepath, "wb") as f:
            f.write(header)
            f.write(struct.pack("<I", n_tris))
            for i0, i1, i2 in self.triangles():
                x0, y0, z0 = self.vertices[i0]
                x1, y1, z1 = self.vertices[i1]
                x2, y2, z2 = self.vertices[i2]
                ux, uy, uz = x1 - x0, y1 - y0, z1 - z0
                vx, vy, vz = x2 - x0, y2 - y0, z2 - z0
                nx = uy * vz - uz * vy
                ny = uz * vx - ux * vz
                nz = ux * vy - uy * vx
                norm = math.sqrt(nx * nx + ny * ny + nz * nz)
                if norm > 1e-12:
                    nx, ny, nz = nx / norm, ny / norm, nz / norm
                else:
                    nx, ny, nz = 0.0, 0.0, 0.0
                f.write(
                    struct.pack(
                        "<12fH",
                        nx, ny, nz,
                        x0, y0, z0,
                        x1, y1, z1,
                        x2, y2, z2,
                        0,
                    )
                )
        return n_tris, volume


def add_symmetric_strip(
    mesh: WatertightMesh,
    x0: float,
    x1: float,
    y0_fn,
    y1_fn,
    z0: float,
    z1: float,
) -> None:
    """Ajoute une bande symétrique (+Y et -Y) définie par y0_fn(x, z) <= y1_fn(x, z)."""
    for sign in (1.0, -1.0):
        pts: dict[tuple[int, int, int], int] = {}
        for ix, x in enumerate((x0, x1)):
            for iz, z in enumerate((z0, z1)):
                ya = sign * y0_fn(x, z)
                yb = sign * y1_fn(x, z)
                y_low, y_high = (ya, yb) if ya <= yb else (yb, ya)
                pts[(ix, 0, iz)] = mesh.vertex(x, y_low, z)
                pts[(ix, 1, iz)] = mesh.vertex(x, y_high, z)
        mesh.add_hex(
            pts[(0, 0, 0)],
            pts[(1, 0, 0)],
            pts[(1, 1, 0)],
            pts[(0, 1, 0)],
            pts[(0, 0, 1)],
            pts[(1, 0, 1)],
            pts[(1, 1, 1)],
            pts[(0, 1, 1)],
        )


def female_cavity_half_width(x: float, z: float) -> float:
    """Demi-largeur de la cavité femelle (y >= 0) pour x dans [0.0, 17.2]."""
    v_off = v_offset_profile(z)
    if x <= 3.9:
        return 5.30
    if x <= 4.4:
        t = (x - 3.9) / 0.5
        return 5.30 + t * (6.50 - 5.30)
    if x <= 9.8:
        return 6.50
    if x <= 10.8:
        t = (x - 9.8) / 1.0
        return 6.50 + t * (1.80 - 6.50)
    if x <= 11.4:
        t = (x - 10.8) / 0.6
        return (1.80 - t * 0.04) + t * v_off
    if x <= 16.5:
        t = (x - 11.4) / 5.1
        return (1.76 - t * 0.36) + v_off
    t = (x - 16.5) / 0.7
    return (1.40 + v_off) * (1.0 - t)


def male_tongue_half_width(x_rel: float, z: float) -> float:
    """Demi-largeur de la languette centrale mâle pour x_rel = x - body_len dans [0.0, 16.5]."""
    v_off = v_offset_profile(z)
    if x_rel <= 10.2:
        return 1.60
    if x_rel <= 11.5:
        t = (x_rel - 10.2) / 1.3
        return (1.60 - t * 0.10) + t * v_off
    if x_rel <= 15.8:
        t = (x_rel - 11.5) / 4.3
        return (1.50 - t * 0.30) + v_off
    t = (x_rel - 15.8) / 0.7
    return (1.20 - t * 0.70) + v_off * (1.0 - t * 0.73)


def male_arm_bounds(x_rel: float) -> tuple[float, float]:
    """Limites (y_inner, y_outer) du bras élastique Snap-Fit pour x_rel dans [0.0, 9.5]."""
    if x_rel <= 4.0:
        return (3.50, 5.10)
    if x_rel <= 4.5:
        t = (x_rel - 4.0) / 0.5
        return (3.50, 5.10 + t * (6.20 - 5.10))
    if x_rel <= 6.0:
        return (3.50, 6.20)
    if x_rel <= 8.8:
        t = (x_rel - 6.0) / 2.8
        return (3.50, 6.20 - t * (6.20 - 5.10))
    t = (x_rel - 8.8) / 0.7
    return (3.50 + t * 0.40, 5.10 - t * 0.50)


def add_female_and_body(
    mesh: WatertightMesh,
    body_len: float,
    x_body_split: float,
    rib_intervals: list[tuple[float, float]],
    split_end_at_y: list[float],
) -> None:
    """Construit la section femelle [0, 17.2] + le corps principal [17.2, body_len]."""
    female_x = [0.0, 3.9, 4.4, 9.8, 10.8, 11.4, 16.5, 17.2]
    all_x = sorted(
        set(
            female_x
            + [x_body_split, body_len]
            + [x for pair in rib_intervals for x in pair]
        )
    )

    def is_rib_x(x0: float, x1: float) -> bool:
        xm = 0.5 * (x0 + x1)
        return any(a < xm < b for a, b in rib_intervals)

    for ix in range(len(all_x) - 1):
        x0, x1 = all_x[ix], all_x[ix + 1]
        xm = 0.5 * (x0 + x1)
        has_rib = is_rib_x(x0, x1)

        for iz in range(len(Z_LEVELS) - 1):
            z0, z1 = Z_LEVELS[iz], Z_LEVELS[iz + 1]
            zm = 0.5 * (z0 + z1)

            # 1. Bandes extérieures (nervure interne, rainure, épaulement externe)
            add_symmetric_strip(mesh, x0, x1, lambda x, z: CORE_HALF_W, lambda x, z: GROOVE_INNER_Y, z0, z1)
            if zm < 9.0 or (has_rib and zm < 9.8):
                add_symmetric_strip(
                    mesh, x0, x1, lambda x, z: GROOVE_INNER_Y, lambda x, z: GROOVE_OUTER_Y, z0, z1
                )
            add_symmetric_strip(mesh, x0, x1, lambda x, z: GROOVE_OUTER_Y, lambda x, z: HALF_W, z0, z1)

            # 2. Noyau central [0.0, CORE_HALF_W]
            if xm < 17.2:
                add_symmetric_strip(
                    mesh, x0, x1, female_cavity_half_width, lambda x, z: CORE_HALF_W, z0, z1
                )
            elif xm < x_body_split:
                add_symmetric_strip(mesh, x0, x1, lambda x, z: 0.0, lambda x, z: CORE_HALF_W, z0, z1)
            elif abs(x0 - x_body_split) < 1e-6 and abs(x1 - body_len) < 1e-6:
                # Tranche de transition subdivisant [0, CORE_HALF_W] selon split_end_at_y sur x = body_len
                for sign in (1.0, -1.0):
                    pts_xy = [(x0, 0.0), (x1, 0.0)]
                    for yv in split_end_at_y:
                        pts_xy.append((x1, sign * yv))
                    pts_xy.append((x1, sign * CORE_HALF_W))
                    pts_xy.append((x0, sign * CORE_HALF_W))
                    if sign < 0:
                        pts_xy = list(reversed(pts_xy))
                    mesh.add_convex_prism(pts_xy, z0, z1)
            else:
                # Si des micro-stries découpent après x_body_split, la transition se fait exactement sur la dernière tranche
                if abs(x1 - body_len) < 1e-6:
                    for sign in (1.0, -1.0):
                        pts_xy = [(x0, 0.0), (x1, 0.0)]
                        for yv in split_end_at_y:
                            pts_xy.append((x1, sign * yv))
                        pts_xy.append((x1, sign * CORE_HALF_W))
                        pts_xy.append((x0, sign * CORE_HALF_W))
                        if sign < 0:
                            pts_xy = list(reversed(pts_xy))
                        mesh.add_convex_prism(pts_xy, z0, z1)
                else:
                    add_symmetric_strip(mesh, x0, x1, lambda x, z: 0.0, lambda x, z: CORE_HALF_W, z0, z1)


def add_male_snapfit(mesh: WatertightMesh, x_start: float) -> None:
    """Ajoute la languette centrale à rainure en V et les deux bras Snap-Fit après x_start."""
    # Stations X relatives à x_start
    male_x_rel = [0.0, 4.0, 4.5, 6.0, 8.8, 9.5, 10.2, 11.5, 15.8, 16.5]
    for ix in range(len(male_x_rel) - 1):
        xr0, xr1 = male_x_rel[ix], male_x_rel[ix + 1]
        x0, x1 = x_start + xr0, x_start + xr1
        xrm = 0.5 * (xr0 + xr1)

        for iz in range(len(Z_LEVELS) - 1):
            z0, z1 = Z_LEVELS[iz], Z_LEVELS[iz + 1]

            # Languette centrale [0.0 .. tongue_w]
            add_symmetric_strip(
                mesh,
                x0,
                x1,
                lambda x, z: 0.0,
                lambda x, z: male_tongue_half_width(x - x_start, z),
                z0,
                z1,
            )

            # Bras Snap-Fit [0.0 .. 9.5]
            if xrm < 9.5:
                add_symmetric_strip(
                    mesh,
                    x0,
                    x1,
                    lambda x, z: male_arm_bounds(x - x_start)[0],
                    lambda x, z: male_arm_bounds(x - x_start)[1],
                    z0,
                    z1,
                )


def build_straight_or_slope_rail(with_stries: bool) -> WatertightMesh:
    """Construit un rail de 100 mm (lisse ou avec micro-stries de côte)."""
    mesh = WatertightMesh()
    body_len = 100.0
    x_split = 99.0
    rib_intervals: list[tuple[float, float]] = []
    if with_stries:
        # Micro-stries de 2,0 mm tous les 4,0 mm entre x=18 et x=96
        x = 18.0
        while x + 2.0 <= 96.0:
            rib_intervals.append((x, x + 2.0))
            x += 4.0

    # Splits requis à x = 100.0 pour raccorder languette [0..1.60] et bras [3.50..5.10]
    add_female_and_body(mesh, body_len, x_split, rib_intervals, [1.60, 3.50, 5.10])
    add_male_snapfit(mesh, body_len)
    return mesh


def build_wooden_adapter() -> WatertightMesh:
    """Construit un adaptateur 50 mm : prise Snap-Fit femelle <-> cheville mâle train en bois."""
    mesh = WatertightMesh()
    body_len = 50.0
    x_split = 49.0

    # À x = 50.0, seul le col de cheville [-3.0, +3.0] continue
    add_female_and_body(mesh, body_len, x_split, [], [3.00])

    # Cheville en bois : col [50.0 .. 56.2714] de demi-largeur 3,00 mm
    peg_r = 5.60
    peg_xc = 61.0
    neck_half_w = 3.00
    dx_join = math.sqrt(peg_r * peg_r - neck_half_w * neck_half_w)
    x_join = peg_xc - dx_join  # 56.2714 mm

    for iz in range(len(Z_LEVELS) - 1):
        z0, z1 = Z_LEVELS[iz], Z_LEVELS[iz + 1]
        add_symmetric_strip(
            mesh, body_len, x_join, lambda x, z: 0.0, lambda x, z: neck_half_w, z0, z1
        )

    # Tête circulaire de la cheville (polygone convexe régulier raccordé sur (x_join, ±3.00))
    ang_start = math.atan2(-neck_half_w, -dx_join)  # angle bas-gauche (en radians négatifs)
    ang_end = math.atan2(neck_half_w, -dx_join)     # angle haut-gauche (en radians positifs)
    # Parcours CCW de ang_end -> 2*pi + ang_start ? Non : CCW part de (x_join, -3) -> droite -> (x_join, +3)
    # Angle de (x_join, -3) = -pi + 0.565 rad ; pour passer par x = +peg_r (angle 0) jusqu'à +3 (+pi - 0.565 rad) :
    n_arc = 28
    peg_poly: list[tuple[float, float]] = [(x_join, 0.0)]
    for k in range(n_arc + 1):
        t = k / n_arc
        ang = ang_start + t * (ang_end - ang_start)
        px = peg_xc + peg_r * math.cos(ang)
        py = peg_r * math.sin(ang)
        if k == 0:
            px, py = x_join, -neck_half_w
        elif k == n_arc:
            px, py = x_join, neck_half_w
        peg_poly.append((px, py))

    for iz in range(len(Z_LEVELS) - 1):
        z0, z1 = Z_LEVELS[iz], Z_LEVELS[iz + 1]
        mesh.add_convex_prism(peg_poly, z0, z1)

    return mesh


def outer_coaster_half_width(z: float) -> float:
    """Profil latéral avec rainure captive en C (45°) entre z=4,5 et z=7,5 mm."""
    if z <= 4.5 or z >= 7.5:
        return HALF_W
    return HALF_W - 1.50 * (1.0 - abs(z - 6.0) / 1.5)


def add_symmetric_rack_tooth(
    mesh: WatertightMesh,
    x0: float,
    x1: float,
    x0_top: float,
    x1_top: float,
    y_half: float,
    z_bot: float,
    z_top: float,
) -> None:
    """Ajoute une dent trapézoïdale symétrique (±Y) sur la crémaillère centrale."""
    for sign in (1.0, -1.0):
        y0, y1 = (0.0, y_half) if sign > 0 else (-y_half, 0.0)
        b00 = mesh.vertex(x0, y0, z_bot)
        b10 = mesh.vertex(x1, y0, z_bot)
        b11 = mesh.vertex(x1, y1, z_bot)
        b01 = mesh.vertex(x0, y1, z_bot)
        t00 = mesh.vertex(x0_top, y0, z_top)
        t10 = mesh.vertex(x1_top, y0, z_top)
        t11 = mesh.vertex(x1_top, y1, z_top)
        t01 = mesh.vertex(x0_top, y1, z_top)
        mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)


def build_funky_coaster_rail() -> WatertightMesh:
    """Construit un rail 'Funky / Anti-Gravité' de 100 mm :
    - Jonction Snap-Fit + V-groove compatible avec tous les rails standards
    - Rainures 25,5 mm avec micro-stries de traction
    - Crémaillère centrale dentée (z=12,0..13,5 mm, pas 4,0 mm)
    - Deux rainures latérales (y ∈ [5,10, 7,25], z=11,0..12,0) pour bandes d'acier magnétique
    - Glissières latérales captives à 45° sur les flancs (y=20 -> 18,5 -> 20 mm)
    """
    mesh = WatertightMesh()
    body_len = 100.0
    x_split = 18.0

    rib_intervals: list[tuple[float, float]] = []
    x = 18.0
    while x + 2.0 <= 96.0:
        rib_intervals.append((x, x + 2.0))
        x += 4.0

    female_x = [0.0, 3.9, 4.4, 9.8, 10.8, 11.4, 16.5, 17.2]
    all_x = sorted(
        set(
            female_x
            + [x_split, 98.0, body_len]
            + [xv for pair in rib_intervals for xv in pair]
        )
    )

    def is_rib_x(x0: float, x1: float) -> bool:
        xm = 0.5 * (x0 + x1)
        return any(a < xm < b for a, b in rib_intervals)

    core_bands = [(0.0, 1.60), (1.60, 3.50), (3.50, 5.10), (5.10, CORE_HALF_W)]

    for ix in range(len(all_x) - 1):
        x0, x1 = all_x[ix], all_x[ix + 1]
        xm = 0.5 * (x0 + x1)
        has_rib = is_rib_x(x0, x1)

        for iz in range(len(Z_LEVELS) - 1):
            z0, z1 = Z_LEVELS[iz], Z_LEVELS[iz + 1]
            zm = 0.5 * (z0 + z1)

            # 1. Bandes extérieures + glissière captive à 45° sur les flancs
            add_symmetric_strip(mesh, x0, x1, lambda x, z: CORE_HALF_W, lambda x, z: GROOVE_INNER_Y, z0, z1)
            if zm < 9.0 or (has_rib and zm < 9.8):
                add_symmetric_strip(
                    mesh, x0, x1, lambda x, z: GROOVE_INNER_Y, lambda x, z: GROOVE_OUTER_Y, z0, z1
                )
            add_symmetric_strip(
                mesh, x0, x1, lambda x, z: GROOVE_OUTER_Y, lambda x, z: outer_coaster_half_width(z), z0, z1
            )

            # 2. Noyau central [0.0, CORE_HALF_W]
            if xm < 17.2:
                add_symmetric_strip(
                    mesh, x0, x1, female_cavity_half_width, lambda x, z: CORE_HALF_W, z0, z1
                )
            elif xm < x_split:
                # Tranche de transition [17.2 .. 18.0] subdivisant en 4 bandes dès x = 18.0
                for sign in (1.0, -1.0):
                    pts_xy = [
                        (x0, 0.0),
                        (x1, 0.0),
                        (x1, sign * 1.60),
                        (x1, sign * 3.50),
                        (x1, sign * 5.10),
                        (x1, sign * CORE_HALF_W),
                        (x0, sign * CORE_HALF_W),
                    ]
                    if sign < 0:
                        pts_xy = list(reversed(pts_xy))
                    mesh.add_convex_prism(pts_xy, z0, z1)
            else:
                for y_a, y_b in core_bands:
                    # Laisser une loge de 1,0 mm (z=11..12) sur [5.10, 7.25] entre x=18 et x=98 pour la bande d'acier
                    if abs(y_a - 5.10) < 1e-6 and 18.0 < xm < 98.0 and zm > 11.0:
                        continue
                    add_symmetric_strip(mesh, x0, x1, lambda x, z, ya=y_a: ya, lambda x, z, yb=y_b: yb, z0, z1)

        # 3. Dent de crémaillère centrale (z = 12,0 .. 14,0 mm) sur [0.0, 1.60]
        if has_rib:
            add_symmetric_rack_tooth(mesh, x0, x1, x0 + 0.40, x1 - 0.40, 1.60, 12.0, 14.0)

    add_male_snapfit(mesh, body_len)
    return mesh


def build_curved_rail_45deg() -> WatertightMesh:
    """Construit un rail courbe de 45° (8 pièces = cercle complet, R_centre = 180 mm).

    Extrémités femelle [0..18] et mâle [L_arc+2..L_arc+18,5] tangentes rectilignes
    pour garantir la compatibilité totale avec les rails droits Snap-Fit.
    """
    mesh = WatertightMesh()
    s_lead = 18.0
    r_center = 180.0
    arc_angle = math.pi / 4.0
    l_arc = r_center * arc_angle
    n_arc = 24
    s_arc_end = s_lead + l_arc
    s_split = s_arc_end + 1.0
    s_body_end = s_arc_end + 2.0

    female_s = [0.0, 3.9, 4.4, 9.8, 10.8, 11.4, 16.5, 17.2]
    arc_s = [s_lead + l_arc * k / n_arc for k in range(n_arc + 1)]
    all_s = sorted(set(female_s + arc_s + [s_split, s_body_end]))

    for iseg in range(len(all_s) - 1):
        s0, s1 = all_s[iseg], all_s[iseg + 1]
        sm = 0.5 * (s0 + s1)

        for iz in range(len(Z_LEVELS) - 1):
            z0, z1 = Z_LEVELS[iz], Z_LEVELS[iz + 1]
            zm = 0.5 * (z0 + z1)

            add_symmetric_strip(mesh, s0, s1, lambda s, z: CORE_HALF_W, lambda s, z: GROOVE_INNER_Y, z0, z1)
            if zm < 9.0:
                add_symmetric_strip(
                    mesh, s0, s1, lambda s, z: GROOVE_INNER_Y, lambda s, z: GROOVE_OUTER_Y, z0, z1
                )
            add_symmetric_strip(mesh, s0, s1, lambda s, z: GROOVE_OUTER_Y, lambda s, z: HALF_W, z0, z1)

            if sm < 17.2:
                add_symmetric_strip(
                    mesh, s0, s1, female_cavity_half_width, lambda s, z: CORE_HALF_W, z0, z1
                )
            elif sm < s_split:
                add_symmetric_strip(mesh, s0, s1, lambda s, z: 0.0, lambda s, z: CORE_HALF_W, z0, z1)
            else:
                for sign in (1.0, -1.0):
                    pts_sy = [
                        (s0, 0.0),
                        (s1, 0.0),
                        (s1, sign * 1.60),
                        (s1, sign * 3.50),
                        (s1, sign * 5.10),
                        (s1, sign * CORE_HALF_W),
                        (s0, sign * CORE_HALF_W),
                    ]
                    if sign < 0:
                        pts_sy = list(reversed(pts_sy))
                    mesh.add_convex_prism(pts_sy, z0, z1)

    add_male_snapfit(mesh, s_body_end)

    # Transformation curviligne C1 : (s, y_loc, z) -> (X, Y, z)
    ca, sa = math.cos(arc_angle), math.sin(arc_angle)
    transformed: list[tuple[float, float, float]] = []
    for s, y_loc, z in mesh.vertices:
        if s <= s_lead:
            transformed.append((s, y_loc, z))
        elif s <= s_arc_end:
            alpha = (s - s_lead) / r_center
            r = r_center - y_loc
            transformed.append((s_lead + r * math.sin(alpha), r_center - r * math.cos(alpha), z))
        else:
            u = s - s_arc_end
            r = r_center - y_loc
            transformed.append(
                (s_lead + r * sa + u * ca, r_center - r * ca + u * sa, z)
            )
    mesh.vertices = transformed
    return mesh


def build_lockable_pillar_duplo() -> WatertightMesh:
    """Construit un pilier verrouillable H=50 mm (rebords 56 mm) à base compatible gros blocs."""
    mesh = WatertightMesh()

    x_base = [-31.8, -28.7, -16.0, 16.0, 28.7, 31.8]
    y_base = [-20.0, -14.0, -12.8, -3.15, 3.15, 12.8, 14.0, 20.0]

    def add_grid_hex(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
        b00 = mesh.vertex(x0, y0, z0)
        b10 = mesh.vertex(x1, y0, z0)
        b11 = mesh.vertex(x1, y1, z0)
        b01 = mesh.vertex(x0, y1, z0)
        t00 = mesh.vertex(x0, y0, z1)
        t10 = mesh.vertex(x1, y0, z1)
        t11 = mesh.vertex(x1, y1, z1)
        t01 = mesh.vertex(x0, y1, z1)
        mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)

    # 1. Base [0..4,5] avec deux logements pour rangées de tenons gros blocs (y=±7,95 mm)
    #    et [4,5..12,0] pleine largeur 63,6 x 40,0 mm
    for iz, (z0, z1) in enumerate(((0.0, 4.5), (4.5, 12.0))):
        for ix in range(len(x_base) - 1):
            for iy in range(len(y_base) - 1):
                if iz == 0 and ix in (1, 2, 3) and iy in (2, 4):
                    continue
                add_grid_hex(x_base[ix], x_base[ix + 1], y_base[iy], y_base[iy + 1], z0, z1)

    # 2. Colonne centrale rigide [12,0..38,0] (32 x 28 mm)
    y_col = [-14.0, -12.8, -3.15, 3.15, 12.8, 14.0]
    for iy in range(len(y_col) - 1):
        add_grid_hex(-16.0, 16.0, y_col[iy], y_col[iy + 1], 12.0, 38.0)

    # 3. Évasement progressif [38,0..50,0] vers le berceau supérieur (40 x 47 mm)
    y_top = [-23.5, -20.2, -10.0, 10.0, 20.2, 23.5]
    for iy in range(len(y_col) - 1):
        b00 = mesh.vertex(-16.0, y_col[iy], 38.0)
        b10 = mesh.vertex(16.0, y_col[iy], 38.0)
        b11 = mesh.vertex(16.0, y_col[iy + 1], 38.0)
        b01 = mesh.vertex(-16.0, y_col[iy + 1], 38.0)
        t00 = mesh.vertex(-20.0, y_top[iy], 50.0)
        t10 = mesh.vertex(20.0, y_top[iy], 50.0)
        t11 = mesh.vertex(20.0, y_top[iy + 1], 50.0)
        t01 = mesh.vertex(-20.0, y_top[iy + 1], 50.0)
        mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)

    # 4. Rebords latéraux de verrouillage [50,0..56,0] (ouverture 40,4 mm pour rail 40 mm)
    for iy in (0, 4):
        add_grid_hex(-20.0, 20.0, y_top[iy], y_top[iy + 1], 50.0, 56.0)

    return mesh


def build_action_tile() -> WatertightMesh:
    """Construit une tuile d'action clipsable (imprimée à l'envers sur Z=0, sans supports).

    - Dimensions : 30,0 x 19,2 mm (ergots jusqu'à ±9,85 mm)
    - Canal central abaissé (y ∈ [-2,2, +2,2], pont 0,4 mm) laissant passer le pignon central
    - Deux ailes colorées (1,8 mm) lues par le capteur APDS-9960 décalé à y = +4,5/+5,5 mm
    """
    mesh = WatertightMesh()
    x_pts = [0.0, 4.0, 26.0, 30.0]
    y_pts = [-9.6, -8.4, -2.2, 2.2, 8.4, 9.6]

    def clip_outer_y(z: float) -> float:
        if z <= 1.8:
            return 9.60
        if z <= 2.5:
            return 9.60 + ((z - 1.8) / 0.7) * 0.25
        return 9.85 - ((z - 2.5) / 0.7) * 0.45

    z_tile = [0.0, 1.4, 1.8, 2.5, 3.2]
    for ix in range(len(x_pts) - 1):
        x0, x1 = x_pts[ix], x_pts[ix + 1]
        is_clip_x = ix == 1
        for iz in range(len(z_tile) - 1):
            z0, z1 = z_tile[iz], z_tile[iz + 1]
            if iz == 0:
                # Ailes colorées uniquement (canal central évidé à z = 0..1,4 pour le pignon)
                for iy in (0, 1, 3, 4):
                    y0, y1 = y_pts[iy], y_pts[iy + 1]
                    b00, b10 = mesh.vertex(x0, y0, z0), mesh.vertex(x1, y0, z0)
                    b11, b01 = mesh.vertex(x1, y1, z0), mesh.vertex(x0, y1, z0)
                    t00, t10 = mesh.vertex(x0, y0, z1), mesh.vertex(x1, y0, z1)
                    t11, t01 = mesh.vertex(x1, y1, z1), mesh.vertex(x0, y1, z1)
                    mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)
            elif iz == 1:
                # Pont continu [z = 1,4..1,8] épaisseur 0,4 mm
                for iy in range(len(y_pts) - 1):
                    y0, y1 = y_pts[iy], y_pts[iy + 1]
                    b00, b10 = mesh.vertex(x0, y0, z0), mesh.vertex(x1, y0, z0)
                    b11, b01 = mesh.vertex(x1, y1, z0), mesh.vertex(x0, y1, z0)
                    t00, t10 = mesh.vertex(x0, y0, z1), mesh.vertex(x1, y0, z1)
                    t11, t01 = mesh.vertex(x1, y1, z1), mesh.vertex(x0, y1, z1)
                    mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)
            elif is_clip_x:
                # Deux pattes de clipsage sur [4,0..26,0], y ∈ [±8,4 .. ±clip_outer_y]
                add_symmetric_strip(
                    mesh, x0, x1, lambda x, z: 8.4, lambda x, z: clip_outer_y(z), z0, z1
                )

    return mesh


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "stl"
    # Toutes les autres pièces de voie sont portées en CadQuery (generer_rails.py, V2).
    # Seule la tuile d'action reste ici, en attendant de revoir son clipsage.
    specs = [
        (
            out_dir / "tuile_action_clipsable.stl",
            build_action_tile(),
            "Projet Trains V1 - Tuile Action Clipsable avec Canal Pignon",
        ),
    ]

    for path, mesh, header in specs:
        n_tris, vol = mesh.write_stl(path, header)
        size_kb = os.path.getsize(path) / 1024.0
        print(f"[OK] {path.name}: {n_tris} triangles | {size_kb:.1f} Ko | volume={vol:.1f} mm3")


if __name__ == "__main__":
    main()
