#!/usr/bin/env python3
"""Générateur CadQuery de la famille « rails » (V2, finition jouet en bois premium).

Pièces portées depuis la V1 Python pur :
- rail_droit_100mm_snapfit : rail droit 100 mm évidé à nervures, Snap-Fit + verrou en V
- rail_cote_100mm_strie    : même rail avec micro-stries de traction au fond des rainures

Usage : .venv/bin/python 03-cao-3d/generer_rails.py
"""

import cao_commun as c


def main() -> None:
    c.exporter(c.rail_droit(100.0), "rail_droit_100mm_snapfit")
    c.exporter(c.rail_droit(100.0, stries=True), "rail_cote_100mm_strie")


if __name__ == "__main__":
    main()
