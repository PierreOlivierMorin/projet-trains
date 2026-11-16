#!/usr/bin/env python3
"""Générateur paramétrique des 4 pièces imprimables de la Locomotive Prototype V1.

Génère et vérifie l'étanchéité de :
1. loco_chassis_inferieur.stl          : Châssis 84×46×22 mm (Coaster Hooks 45°, berceau N20,
                                         loge aimant N52 scellée, fenêtre APDS-9960 à y=+4,7 mm,
                                         paliers essieux z_rail=21,0 mm, anneau attelage)
2. loco_coque_superieure_monobloc.stl  : Carrosserie profilée 84×40×32 mm (logement 3×AAA + PCB,
                                         fenêtre VL53L0X + 2 LEDs RGB + bouton Push&Go toit)
3. loco_roue_25_5mm.stl                : Roue Ø 24,0 mm (boudin Ø 27,6 mm, gorge pneu TPU/joint)
4. loco_pignon_central_essieu.stl      : Pignon d'escalade 12 dents (Ø ext 16,8 mm, alésage 3,0 mm)

Compatibilité verticale vérifiée :
- Axe essieu à z_rail = 21,0 mm -> bas du pignon à 12,6 mm (+0,6 mm au-dessus des rails bois/normaux
  et +0,2 mm au-dessus du canal central des tuiles d'action ; engrènement 1,4 mm dans crémaillère 14,0 mm).
"""

import math
import os
from pathlib import Path

from generer_prototype_rails import WatertightMesh


def build_loco_wheel() -> WatertightMesh:
    """Roue ferroviaire Ø 24,0 mm (boudin Ø 27,6 mm) avec gorge annulaire pour pneu TPU/joint."""
    mesh = WatertightMesh()
    n_seg = 48
    r_bore = 1.50    # Alésage Ø 3,0 mm
    r_hub = 4.20     # Moyeu entretoise Ø 8,4 mm
    r_groove = 10.90 # Fond de gorge pneu Ø 21,8 mm
    r_tread = 12.00  # Bande de roulement Ø 24,0 mm
    r_flange = 13.80 # Boudin Ø 27,6 mm

    # Couches axiales Z : (z0, z1, r_max)
    axial_rings = [
        (0.0, 1.4, (r_bore, r_hub, r_groove, r_tread, r_flange)),
        (1.4, 2.2, (r_bore, r_hub, r_groove, r_tread)),
        (2.2, 4.0, (r_bore, r_hub, r_groove)),
        (4.0, 4.8, (r_bore, r_hub, r_groove, r_tread)),
        (4.8, 6.2, (r_bore, r_hub)),
    ]

    angles = [2.0 * math.pi * k / n_seg for k in range(n_seg)]
    for z0, z1, radii in axial_rings:
        for ir in range(len(radii) - 1):
            ra, rb = radii[ir], radii[ir + 1]
            for k in range(n_seg):
                a0 = angles[k]
                a1 = angles[(k + 1) % n_seg]
                c0, s0 = math.cos(a0), math.sin(a0)
                c1, s1 = math.cos(a1), math.sin(a1)
                b00 = mesh.vertex(ra * c0, ra * s0, z0)
                b10 = mesh.vertex(rb * c0, rb * s0, z0)
                b11 = mesh.vertex(rb * c1, rb * s1, z0)
                b01 = mesh.vertex(ra * c1, ra * s1, z0)
                t00 = mesh.vertex(ra * c0, ra * s0, z1)
                t10 = mesh.vertex(rb * c0, rb * s0, z1)
                t11 = mesh.vertex(rb * c1, rb * s1, z1)
                t01 = mesh.vertex(ra * c1, ra * s1, z1)
                mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)

    return mesh


def build_loco_pinion() -> WatertightMesh:
    """Pignon d'escalade 12 dents (Ø ext = 16,8 mm, Ø pied = 13,4 mm, épaisseur 3,0 mm)."""
    mesh = WatertightMesh()
    n_teeth = 12
    sub_per_tooth = 8
    total_steps = n_teeth * sub_per_tooth
    r_bore = 1.50
    r_root = 6.70
    r_tip = 8.40
    z0, z1 = 0.0, 3.0

    angles = [2.0 * math.pi * k / total_steps for k in range(total_steps)]
    # 1. Anneau central [r_bore .. r_root]
    for k in range(total_steps):
        a0 = angles[k]
        a1 = angles[(k + 1) % total_steps]
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        b00 = mesh.vertex(r_bore * c0, r_bore * s0, z0)
        b10 = mesh.vertex(r_root * c0, r_root * s0, z0)
        b11 = mesh.vertex(r_root * c1, r_root * s1, z0)
        b01 = mesh.vertex(r_bore * c1, r_bore * s1, z0)
        t00 = mesh.vertex(r_bore * c0, r_bore * s0, z1)
        t10 = mesh.vertex(r_root * c0, r_root * s0, z1)
        t11 = mesh.vertex(r_root * c1, r_root * s1, z1)
        t01 = mesh.vertex(r_bore * c1, r_bore * s1, z1)
        mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)

    # 2. Dents trapézoïdales sur les sous-secteurs [2..6] de chaque pas (partageant R_root exact)
    # Profil radial : step 2 -> root, step 3 -> tip, step 4 -> tip, step 5 -> tip, step 6 -> root
    tooth_r = {2: r_root, 3: r_tip, 4: r_tip, 5: r_tip, 6: r_root}
    for t_idx in range(n_teeth):
        base = t_idx * sub_per_tooth
        for s_off in range(2, 6):
            k0 = (base + s_off) % total_steps
            k1 = (base + s_off + 1) % total_steps
            a0, a1 = angles[k0], angles[k1]
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            r0_out = tooth_r[s_off]
            r1_out = tooth_r[s_off + 1]
            b00 = mesh.vertex(r_root * c0, r_root * s0, z0)
            b10 = mesh.vertex(r0_out * c0, r0_out * s0, z0)
            b11 = mesh.vertex(r1_out * c1, r1_out * s1, z0)
            b01 = mesh.vertex(r_root * c1, r_root * s1, z0)
            t00 = mesh.vertex(r_root * c0, r_root * s0, z1)
            t10 = mesh.vertex(r0_out * c0, r0_out * s0, z1)
            t11 = mesh.vertex(r1_out * c1, r1_out * s1, z1)
            t01 = mesh.vertex(r_root * c1, r_root * s1, z1)
            mesh.add_hex(b00, b10, b11, b01, t00, t10, t11, t01)

    return mesh


def build_loco_chassis() -> WatertightMesh:
    """Châssis inférieur 84×46×22 mm (z_print = z_rail - 4,5 mm, essieux à z_print = 16,5 mm)."""
    mesh = WatertightMesh()

    x_grid = [
        -10.0, -8.0, -2.0, 0.0,
        5.0, 10.0, 15.0, 18.4, 21.6, 25.0, 26.0, 28.0, 30.0, 35.0,
        48.4, 51.0, 56.0, 61.0, 64.4, 67.6, 71.0, 76.0, 79.0, 81.0, 84.0,
    ]
    y_grid = [
        -23.0, -20.3, -17.2, -8.8, -6.1, -5.2, -3.5, -2.5,
        0.6, 2.5, 3.5, 5.2, 6.1, 8.8, 17.2, 20.3, 23.0,
    ]
    z_grid = [0.0, 1.5, 3.0, 10.5, 11.7, 15.0, 22.0]

    def hook_inner_y(z: float) -> float:
        """Bord interne du patin Coaster Hook : s'avance à 19,0 mm à z_print=1,5 mm (z_rail=6,0)."""
        if z <= 0.0 or z >= 3.0:
            return 20.3
        return 20.3 - 1.30 * (1.0 - abs(z - 1.5) / 1.5)

    for ix in range(len(x_grid) - 1):
        x0, x1 = x_grid[ix], x_grid[ix + 1]
        xm = 0.5 * (x0 + x1)

        for iy in range(len(y_grid) - 1):
            y0, y1 = y_grid[iy], y_grid[iy + 1]
            ym = 0.5 * (y0 + y1)
            aym = abs(ym)

            for iz in range(len(z_grid) - 1):
                z0, z1 = z_grid[iz], z_grid[iz + 1]
                zm = 0.5 * (z0 + z1)

                # Zone anneau d'attelage arrière [-10 .. 0]
                if xm < 0.0:
                    if not (10.5 < zm < 15.0 and aym < 6.1):
                        continue
                    if -8.0 < xm < -2.0 and aym < 3.5:
                        continue
                    mesh.add_hex(
                        mesh.vertex(x0, y0, z0), mesh.vertex(x1, y0, z0),
                        mesh.vertex(x1, y1, z0), mesh.vertex(x0, y1, z0),
                        mesh.vertex(x0, y0, z1), mesh.vertex(x1, y0, z1),
                        mesh.vertex(x1, y1, z1), mesh.vertex(x0, y1, z1),
                    )
                    continue

                # Zone châssis principal [0 .. 84]
                if zm < 10.5:
                    # Patins Coaster Hooks uniquement sur jupes externes (|y| ∈ [20,3..23,0])
                    # en deux paires courtes (x ∈ [10..30] et [56..76]) pour passer les courbes/loopings
                    if not (aym > 20.3 and (10.0 < xm < 30.0 or 56.0 < xm < 76.0)):
                        continue
                    if ym > 0:
                        ya0, yb0 = hook_inner_y(z0), 23.0
                        ya1, yb1 = hook_inner_y(z1), 23.0
                    else:
                        ya0, yb0 = -23.0, -hook_inner_y(z0)
                        ya1, yb1 = -23.0, -hook_inner_y(z1)
                    mesh.add_hex(
                        mesh.vertex(x0, ya0, z0), mesh.vertex(x1, ya0, z0),
                        mesh.vertex(x1, yb0, z0), mesh.vertex(x0, yb0, z0),
                        mesh.vertex(x0, ya1, z1), mesh.vertex(x1, ya1, z1),
                        mesh.vertex(x1, yb1, z1), mesh.vertex(x0, yb1, z1),
                    )
                    continue

                if zm < 15.0:
                    # Plancher principal [10,5 .. 15,0]
                    is_wheel_well = (5.0 < xm < 35.0 or 51.0 < xm < 81.0) and (8.8 < aym < 17.2)
                    is_pinion_slot = (10.0 < xm < 30.0) and (aym < 2.5)
                    is_optical_win = (71.0 < xm < 79.0) and (0.6 < ym < 8.8)
                    is_magnet_pocket = (zm > 11.7) and (28.0 < xm < 48.4) and (aym < 5.2)
                    if is_wheel_well or is_pinion_slot or is_optical_win or is_magnet_pocket:
                        continue
                else:
                    # Parois supérieures [15,0 .. 22,0]
                    is_outer_wall = aym > 20.3
                    is_bearing = (17.2 < aym < 20.3) and (
                        (15.0 < xm < 18.4) or (21.6 < xm < 25.0)
                        or (61.0 < xm < 64.4) or (67.6 < xm < 71.0)
                    )
                    is_motor_cradle = (26.0 < xm < 51.0) and (6.1 < aym < 8.8)
                    if not (is_outer_wall or is_bearing or is_motor_cradle):
                        continue

                mesh.add_hex(
                    mesh.vertex(x0, y0, z0), mesh.vertex(x1, y0, z0),
                    mesh.vertex(x1, y1, z0), mesh.vertex(x0, y1, z0),
                    mesh.vertex(x0, y0, z1), mesh.vertex(x1, y0, z1),
                    mesh.vertex(x1, y1, z1), mesh.vertex(x0, y1, z1),
                )

    return mesh


def build_loco_shell() -> WatertightMesh:
    """Coque supérieure monobloc 84×40×32 mm imprimée à plat sans supports."""
    mesh = WatertightMesh()

    x_fixed = [0.0, 2.5, 24.0, 36.0, 55.0]
    y_base = [-20.0, -17.5, -14.5, -10.0, -6.0, -5.0, 5.0, 6.0, 10.0, 14.5, 17.5, 20.0]
    z_grid = [0.0, 3.0, 9.5, 11.0, 24.0, 29.5, 32.0]

    def x_front_outer(z: float) -> float:
        if z <= 11.0:
            return 84.0
        return 84.0 - 26.0 * ((z - 11.0) / 21.0)  # 84,0 -> 58,0 mm

    def x_front_inner(z: float) -> float:
        return x_front_outer(z) - 2.50

    def y_outer(z: float) -> float:
        if z <= 24.0:
            return 20.0
        return 20.0 - 2.80 * ((z - 24.0) / 8.0)   # Chanfrein 20,0 -> 17,2 mm

    def y_inner(z: float) -> float:
        return y_outer(z) - 2.50                  # Reste >= 14,7 > 14,5 mm partout

    def map_y(y_raw: float, z: float) -> float:
        if abs(y_raw) > 19.9:
            return math.copysign(y_outer(z), y_raw)
        if abs(y_raw) > 17.4:
            return math.copysign(y_inner(z), y_raw)
        return y_raw

    # 7 intervalles X : 4 fixes [0..55] + 2 nez [55..x_in..x_out]
    n_x_intervals = 6

    for ix in range(n_x_intervals):
        for iy in range(len(y_base) - 1):
            yr0, yr1 = y_base[iy], y_base[iy + 1]
            ym_raw = 0.5 * (yr0 + yr1)
            aym = abs(ym_raw)

            for iz in range(len(z_grid) - 1):
                z0, z1 = z_grid[iz], z_grid[iz + 1]
                zm = 0.5 * (z0 + z1)

                if ix < 4:
                    xa0 = xb0 = x_fixed[ix]
                    xa1 = xb1 = x_fixed[ix + 1]
                elif ix == 4:
                    xa0, xb0 = 55.0, 55.0
                    xa1, xb1 = x_front_inner(z0), x_front_inner(z1)
                else:
                    xa0, xb0 = x_front_inner(z0), x_front_inner(z1)
                    xa1, xb1 = x_front_outer(z0), x_front_outer(z1)

                is_rear_wall = ix == 0
                is_front_wall = ix == 5
                is_side_wall = iy == 0 or iy == (len(y_base) - 2)
                is_roof = zm > 29.5

                # Découpes fonctionnelles :
                # 1. Bouton Push & Go sur le toit [24..36] × [-6..+6] × [29,5..32]
                if is_roof and ix == 2 and aym < 6.0:
                    continue
                # 2. Fenêtre VL53L0X ([-5..+5]) + 2 phares LED RGB ([±10..±14,5]) sur pare-chocs [3..9,5]
                if is_front_wall and 3.0 < zm < 9.5 and (aym < 5.0 or 10.0 < aym < 14.5):
                    continue
                # 3. Cavité interne creuse sous le toit
                if not (is_rear_wall or is_front_wall or is_side_wall or is_roof):
                    continue

                y0_z0, y1_z0 = map_y(yr0, z0), map_y(yr1, z0)
                y0_z1, y1_z1 = map_y(yr0, z1), map_y(yr1, z1)

                mesh.add_hex(
                    mesh.vertex(xa0, y0_z0, z0), mesh.vertex(xa1, y0_z0, z0),
                    mesh.vertex(xa1, y1_z0, z0), mesh.vertex(xa0, y1_z0, z0),
                    mesh.vertex(xb0, y0_z1, z1), mesh.vertex(xb1, y0_z1, z1),
                    mesh.vertex(xb1, y1_z1, z1), mesh.vertex(xb0, y1_z1, z1),
                )

    return mesh


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "stl"
    # Roue et pignon : portés en CadQuery (generer_locomotive.py, V2). Châssis et coque à reconcevoir.
    specs = [
        (
            out_dir / "loco_chassis_inferieur.stl",
            build_loco_chassis(),
            "Projet Trains V1 - Chassis Inferieur Locomotive 84x46x22mm",
        ),
        (
            out_dir / "loco_coque_superieure_monobloc.stl",
            build_loco_shell(),
            "Projet Trains V1 - Coque Superieure Monobloc 84x40x32mm",
        ),
    ]

    for path, mesh, header in specs:
        n_tris, vol = mesh.write_stl(path, header)
        size_kb = os.path.getsize(path) / 1024.0
        print(f"[OK] {path.name}: {n_tris} triangles | {size_kb:.1f} Ko | volume={vol:.1f} mm3")


if __name__ == "__main__":
    main()
