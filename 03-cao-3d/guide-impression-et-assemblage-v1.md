# Guide d'impression 3D et d'assemblage — Prototype V2

Ce guide regroupe les fichiers `.STL` générés dans [`03-cao-3d/stl/`](./stl/) (avec leur `.step` dans [`step/`](./step/)), les cotes contrôlées sans collision et la marche à suivre pour imprimer et tester. Toutes les pièces sont générées en CadQuery (V2) ; la V1 en maillage Python pur reste consultable dans l'historique git.

> [!TIP]
> Pour inspecter les pièces et leur assemblage à l'échelle 1:1, ouvrez [`visualiseur-assemblage.html`](./visualiseur-assemblage.html) d'un double-clic (régénérable via `python3 03-cao-3d/verifier_stl.py --update-viewer`).

---

## 1. Inventaire

### À imprimer en premier

| Fichier `.STL` | Dimensions | Usage |
| :--- | :--- | :--- |
| [`jauge_calibration_tolerances.stl`](./stl/jauge_calibration_tolerances.stl) | `55,0 × 80,0 × 12,0 mm` | 4 prises Snap-Fit (jeux `0,10–0,25`, gravés « 10…25 ») + 4 perçages (`Ø 2,95–3,10`, gravés « 95…10 »). Le jeu retenu règle `JEU_IMPRESSION`, le perçage retenu règle `ALESAGE_SERRE` de la loco. |

### Voie ([`generer_rails.py`](./generer_rails.py))

Rails **évidés à nervures** (~40 % de filament en moins), arrondis « jouet en bois premium ».

| Fichier `.STL` | Dimensions hors-tout | Usage | Supports |
| :--- | :--- | :--- | :---: |
| [`rail_droit_100mm_snapfit.stl`](./stl/rail_droit_100mm_snapfit.stl) | `116,5 × 40,0 × 12,0 mm` | Rail droit Snap-Fit + verrouillage vertical 45° | Non |
| [`rail_courbe_45deg_snapfit.stl`](./stl/rail_courbe_45deg_snapfit.stl) | `159,8 × 88,0 × 12,0 mm` | Courbe 45° à gauche (`R = 180 mm`, 8 pièces = cercle ; retournée = courbe à droite) | Non |
| [`rail_cote_100mm_strie.stl`](./stl/rail_cote_100mm_strie.stl) | `116,5 × 40,0 × 12,0 mm` | Rail de montée à micro-stries (`0,8 mm`) | Non |
| [`adaptateur_rail_bois.stl`](./stl/adaptateur_rail_bois.stl) | `66,6 × 40,0 × 12,0 mm` | Prise Snap-Fit femelle ↔ cheville mâle bois (`Ø 11,2 mm`) | Non |
| [`rail_funky_cremaillere_captif.stl`](./stl/rail_funky_cremaillere_captif.stl) | `116,5 × 40,0 × 14,0 mm` | Crémaillère (`z = 14`), loges acier, glissières captives 45° | Non |
| [`pilier_verrouillable_duplo.stl`](./stl/pilier_verrouillable_duplo.stl) | `63,6 × 47,0 × 56,0 mm` | Pilier `H = 50 mm`, base compatible gros blocs | Non |
| [`pilier_verrouillable_25mm.stl`](./stl/pilier_verrouillable_25mm.stl) | `63,6 × 47,0 × 31,0 mm` | Pilier `H = 25 mm` | Non |

### Locomotive châssis-test ([`generer_locomotive.py`](./generer_locomotive.py), voir [`decisions-locomotive-v2.md`](./decisions-locomotive-v2.md))

| Fichier `.STL` | Dimensions | Qté | Notes d'impression |
| :--- | :--- | :---: | :--- |
| [`loco_chassis_test.stl`](./stl/loco_chassis_test.stl) | `103,5 × 44,0 × 22,4 mm` | 1 | **Pause** à `z = 3,6 mm` pour insérer les 2 aimants N52 `20 × 5 × 3` (même sens de pôle) |
| [`loco_roue_24mm.stl`](./stl/loco_roue_24mm.stl) | `Ø 24,0 × 4,5 mm` | 3 | Face extérieure sur le plateau |
| [`loco_roue_24mm_codeur.stl`](./stl/loco_roue_24mm_codeur.stl) | `Ø 24,0 × 4,5 mm` | 1 | **Pause** à `z = 1,8 mm` pour l'aimant `Ø 3 × 1` (roue arrière gauche) |
| [`loco_pignon_central_essieu.stl`](./stl/loco_pignon_central_essieu.stl) | `Ø 16,8 × 3,0 mm` | 1 | Couche `0,12–0,16 mm` |
| [`loco_engrenage_essieu.stl`](./stl/loco_engrenage_essieu.stl) | `Ø 16 × 3 mm` (14 dents m1) | 1 | Couche `0,12 mm`, remplissage 100 % |
| [`loco_engrenage_moteur.stl`](./stl/loco_engrenage_moteur.stl) | `Ø 22 × 5 mm` (20 dents m1, alésage en D) | 1 | Couche `0,12 mm`, remplissage 100 % |
| [`loco_support_moteur.stl`](./stl/loco_support_moteur.stl) | `14 × 19 × 24 mm` | 1 | **Provisoire** : cotes du N20 supposées, à recaler (`MOTEUR` dans le générateur) |
| [`loco_plateau_piles.stl`](./stl/loco_plateau_piles.stl) | `44,5 × 44,0 × 2,0 mm` | 1 | Boîtier 3×AAA fixé par 2 sangles |

**Quincaillerie** : motoréducteur N20 à vis sans fin ~150–200 tr/min sous 6 V (arbre `Ø 3` en D) · 2 tiges acier `Ø 3 × 30 mm` · 2 aimants N52 `20 × 5 × 3` · 1 aimant `Ø 3 × 1` · capteur Hall `A3144` (TO-92) · boîtier 3×AAA avec interrupteur · 4 vis M3 auto-taraudeuses × 8 · 2 vis M2 × 6 · 1 collier de serrage 2,5 mm · joints toriques `14 × 2` (option pneus).

---

## 2. Cotes contrôlées (CadQuery)

Contrôles automatiques : [`outils/controler_locomotive.py`](../outils/controler_locomotive.py) (loco sur droit, en courbe `R = 180`, sur Funky) et interférence nulle entre rails assemblés (droit, courbe, Funky, adaptateur, rails posés sur les piliers).

- **Rail** : fond de rainure `z = 9,0` · plateau `z = 12,0` · crémaillère Funky `z = 14,0` (|y| ≤ 1,6).
- **Roues** : `Ø 24` sur le fond de rainure → essieux à `z = 21,0` ; largeur `3,5 mm` (rainure `6 mm`). En courbe `R = 180`, empattement `46 mm`, chaque essieu est braqué de `7,3°` : une roue de 5 mm coince (vérifié), 3,5 mm passe.
- **Pignon d'escalade** : bas des dents à `z = 12,6` → `+0,6` au-dessus d'un rail standard ou bois, `1,4 mm` d'engrènement dans la crémaillère.
- **Châssis** : dessous à `z = 12,6` (`+0,6` sur le rail) ; canal central |y| ≤ 2,4 libre jusqu'à `z = 14,6` pour la crémaillère ; aimants au-dessus des bandes d'acier (|y| ≈ 6,2), `1,2 mm` au-dessus du rail.
- **Transmission** : arbre du N20 en `x = 8,95`, `z = 30,84` ; entraxe `17,15 mm` (`17,0` + `0,15` de jeu) ; ×1,43 vers l'essieu avant.
- **Hauteur** avec boîtier de piles : `~59 mm` (tunnel `62,5 mm`).

---

## 3. Paramètres de tranchage (Bambu Studio / PrusaSlicer / Cura)

- **Couche** : `0,20 mm` (`0,12–0,16 mm` pour engrenages, pignon et roues).
- **Périmètres** : `3` (`1,2 mm` avec buse `0,4`) pour les clips Snap-Fit et les paliers.
- **Remplissage** : `15–20 % gyroïde` (rails, piliers, châssis) ; `100 %` pour engrenages et pignon.
- **Matériaux** : **PETG** pour les rails (souplesse des clips) et le châssis ; **PLA+** pour piliers, roues, engrenages ; **TPU 95A** ou joints toriques dans la gorge des roues.
- **Supports** : aucun.
- **Pauses d'impression** (aimants scellés) : ajouter une pause à la hauteur indiquée dans l'inventaire, insérer, reprendre.

---

## 4. Protocole de validation

1. **Jauge** : enfoncer l'embout mâle d'un rail dans chaque prise, retenir celle qui clique sans forcer ni ballotter ; glisser une tige `Ø 3` dans les 4 trous, retenir celui où elle tourne librement sans jeu (paliers) et celui où elle tient serrée (roues). Reporter les valeurs dans `cao_commun.JEU_IMPRESSION` et `generer_locomotive.ALESAGE_SERRE` / `ALESAGE_PALIER`, puis régénérer.
2. **Voie** : `2 × rail_droit`, `1 × adaptateur_rail_bois`, `1 × pilier` — clic sur tapis, jonction rigide sur pilier, raccord sur un rail bois, pose sur gros blocs.
3. **Châssis-test** : mesurer le N20 reçu (réducteur : épaisseur, largeur, longueur, hauteur de l'arbre ; diamètre et longueur du moteur), mettre à jour `MOTEUR`, régénérer et imprimer le support. Monter, câbler moteur + piles + interrupteur, faire rouler sur droits, courbes et côte striée.
4. **Funky** : coller deux bandes d'acier (`~2 × 0,8 × 80 mm`) dans les loges du rail Funky et vérifier l'attraction des aimants et l'engrènement du pignon.
