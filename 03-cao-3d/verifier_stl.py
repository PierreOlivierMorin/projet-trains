#!/usr/bin/env python3
"""Validateur géométrique et topologique automatique pour les fichiers .STL binaires.

Usage :
  python3 03-cao-3d/verifier_stl.py                  # Vérifie tous les .stl de 03-cao-3d/stl/
  python3 03-cao-3d/verifier_stl.py mon_fichier.stl  # Vérifie un ou plusieurs fichiers ciblés
  python3 03-cao-3d/verifier_stl.py --update-viewer  # Vérifie et met à jour visualiseur-assemblage.html
"""

import argparse
import math
import struct
import sys
from pathlib import Path


def inspect_binary_stl(filepath: Path) -> dict:
    """Analyse un fichier STL binaire : format, étanchéité (manifold), volume et dimensions."""
    data = filepath.read_bytes()
    if len(data) < 84:
        return {"ok": False, "error": "Fichier trop court (< 84 octets)"}

    n_tris = struct.unpack("<I", data[80:84])[0]
    expected_len = 84 + 50 * n_tris
    if len(data) != expected_len:
        return {
            "ok": False,
            "error": f"Taille incohérente ({len(data)} octets vs {expected_len} attendus ; format ASCII ?)",
        }
    if n_tris == 0:
        return {"ok": False, "error": "Maillage vide (0 triangle)"}

    vert_map: dict[tuple[int, int, int], int] = {}
    edges: dict[tuple[int, int], int] = {}

    def get_vid(x: float, y: float, z: float) -> int:
        key = (round(x * 10000), round(y * 10000), round(z * 10000))
        vid = vert_map.get(key)
        if vid is None:
            vid = len(vert_map)
            vert_map[key] = vid
        return vid

    min_x = min_y = min_z = math.inf
    max_x = max_y = max_z = -math.inf
    zero_area = 0
    vol6 = 0.0

    for i in range(n_tris):
        off = 84 + 50 * i
        _, _, _, x0, y0, z0, x1, y1, z1, x2, y2, z2, _ = struct.unpack("<12fH", data[off : off + 50])

        for x, y, z in ((x0, y0, z0), (x1, y1, z1), (x2, y2, z2)):
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            if z < min_z: min_z = z
            if z > max_z: max_z = z

        ux, uy, uz = x1 - x0, y1 - y0, z1 - z0
        vx, vy, vz = x2 - x0, y2 - y0, z2 - z0
        cx = uy * vz - uz * vy
        cy = uz * vx - ux * vz
        cz = ux * vy - uy * vx
        if cx * cx + cy * cy + cz * cz < 1e-12:
            zero_area += 1

        vol6 += (
            x0 * (y1 * z2 - y2 * z1)
            - y0 * (x1 * z2 - x2 * z1)
            + z0 * (x1 * y2 - x2 * y1)
        )

        i0 = get_vid(x0, y0, z0)
        i1 = get_vid(x1, y1, z1)
        i2 = get_vid(x2, y2, z2)
        for u, v in ((i0, i1), (i1, i2), (i2, i0)):
            edges[(u, v)] = edges.get((u, v), 0) + 1

    bad_edges = 0
    for (u, v), count in edges.items():
        if count != 1 or edges.get((v, u), 0) != 1:
            bad_edges += 1

    volume_mm3 = vol6 / 6.0
    on_bed = abs(min_z) <= 0.01

    issues = []
    if zero_area > 0:
        issues.append(f"{zero_area} triangle(s) d'aire nulle")
    if bad_edges > 0:
        issues.append(f"{bad_edges} arête(s) ouverte(s) ou non-manifold")
    if volume_mm3 <= 0.0:
        issues.append(f"volume signé invalide ({volume_mm3:.1f} mm3)")
    if not on_bed:
        issues.append(f"Z_min={min_z:.2f} mm (!= 0.00)")

    # Estimation masse FDM (PETG/PLA ~1,25 g/cm3 avec taux de remplissage effectif ~42 %)
    est_grams = (volume_mm3 / 1000.0) * 1.25 * 0.42

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "tris": n_tris,
        "verts": len(vert_map),
        "bad_edges": bad_edges,
        "zero_area": zero_area,
        "volume_cm3": volume_mm3 / 1000.0,
        "est_grams": est_grams,
        "dx": max_x - min_x,
        "dy": max_y - min_y,
        "dz": max_z - min_z,
        "z_min": min_z,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide les fichiers .STL binaires du projet.")
    parser.add_argument("files", nargs="*", help="Fichiers .stl à analyser (défaut: 03-cao-3d/stl/*.stl)")
    parser.add_argument(
        "--update-viewer",
        action="store_true",
        help="Régénère 03-cao-3d/visualiseur-assemblage.html après vérification",
    )
    args = parser.parse_args()

    stl_dir = Path(__file__).resolve().parent / "stl"
    targets = [Path(f) for f in args.files] if args.files else sorted(stl_dir.glob("*.stl"))
    if not targets:
        print("Aucun fichier .stl trouvé.", file=sys.stderr)
        return 1

    all_ok = True
    print(f"{'Statut':<7} | {'Fichier':<36} | {'Dimensions (mm)':<22} | {'Tris':>6} | {'Vol(cm3)':>8} | {'~Masse':>7}")
    print("-" * 102)

    for path in targets:
        if not path.exists():
            print(f"[FAIL]  | {path.name:<36} | Fichier introuvable")
            all_ok = False
            continue
        res = inspect_binary_stl(path)
        if "error" in res:
            print(f"[FAIL]  | {path.name:<36} | {res['error']}")
            all_ok = False
            continue
        status = "[PASS]" if res["ok"] else "[FAIL]"
        dims = f"{res['dx']:.1f}×{res['dy']:.1f}×{res['dz']:.1f}"
        print(
            f"{status:<7} | {path.name:<36} | {dims:<22} | {res['tris']:>6} | {res['volume_cm3']:>8.2f} | {res['est_grams']:>5.1f} g"
        )
        if not res["ok"]:
            all_ok = False
            print(f"        -> Problèmes : {', '.join(res['issues'])}")

    if args.update_viewer:
        import generer_visualiseur_html
        generer_visualiseur_html.main()

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
