# Guide d'impression 3D et d'assemblage — Prototype V1

Ce guide regroupe les **11 fichiers `.STL`** générés dans [`03-cao-3d/stl/`](./stl/), leurs cotes mécaniques vérifiées sans collision et la marche à suivre pour imprimer et tester votre premier circuit.

> [!TIP]
> Pour inspecter les 11 pièces et leur assemblage à l'échelle 1:1 sans installer de logiciel, ouvrez [`visualiseur-assemblage.html`](./visualiseur-assemblage.html) d'un double-clic dans Safari ou Chrome (régénérable à tout moment via `python3 03-cao-3d/generer_visualiseur_html.py`).

---

## 1. Inventaire des 11 fichiers `.STL` générés

### Pièces de circuit (script [`generer_prototype_rails.py`](./generer_prototype_rails.py))

| Fichier `.STL` | Dimensions hors-tout | Usage | Supports |
| :--- | :--- | :--- | :---: |
| [`rail_droit_100mm_snapfit.stl`](./stl/rail_droit_100mm_snapfit.stl) | `116,5 × 40,0 × 12,0 mm` | Rail droit de base à clip Snap-Fit + verrouillage vertical 45° | Non |
| [`rail_courbe_45deg_snapfit.stl`](./stl/rail_courbe_45deg_snapfit.stl) | `160,8 × 88,3 × 12,0 mm` | Rail courbe 45° (`R = 180 mm`, 8 pièces = cercle complet) | Non |
| [`rail_cote_100mm_strie.stl`](./stl/rail_cote_100mm_strie.stl) | `116,5 × 40,0 × 12,0 mm` | Rail de montée avec micro-stries antidérapantes (`0,8 mm`) | Non |
| [`adaptateur_rail_bois.stl`](./stl/adaptateur_rail_bois.stl) | `66,6 × 40,0 × 12,0 mm` | Raccord Snap-Fit femelle ↔ cheville mâle bois (`Ø 11,2 mm`) | Non |
| [`pilier_verrouillable_duplo.stl`](./stl/pilier_verrouillable_duplo.stl) | `63,6 × 47,0 × 56,0 mm` | Pilier `H = 50 mm` (rebords `56 mm`), base compatible gros blocs | Non |
| [`tuile_action_clipsable.stl`](./stl/tuile_action_clipsable.stl) | `30,0 × 19,7 × 3,2 mm` | Tuile colorée clipsable avec canal central abaissé (`0,4 mm`) | Non |
| [`rail_funky_cremaillere_captif.stl`](./stl/rail_funky_cremaillere_captif.stl) | `116,5 × 40,0 × 14,0 mm` | Rail cascade : crémaillère (`z=14 mm`), loges acier, glissières 45° | Non |

### Pièces de la Locomotive V1 (script [`generer_prototype_locomotive.py`](./generer_prototype_locomotive.py))

| Fichier `.STL` | Dimensions hors-tout | Quantité / loco | Supports |
| :--- | :--- | :---: | :---: |
| [`loco_chassis_inferieur.stl`](./stl/loco_chassis_inferieur.stl) | `94,0 × 46,0 × 22,0 mm` | `1` | Oui *(sous le plancher `10,5 mm` entre patins)* |
| [`loco_coque_superieure_monobloc.stl`](./stl/loco_coque_superieure_monobloc.stl) | `84,0 × 40,0 × 32,0 mm` | `1` | Non *(nez 39° et toit chanfreiné)* |
| [`loco_roue_25_5mm.stl`](./stl/loco_roue_25_5mm.stl) | `Ø 27,6 × 6,2 mm` | `4` | Non |
| [`loco_pignon_central_essieu.stl`](./stl/loco_pignon_central_essieu.stl) | `Ø 16,8 × 3,0 mm` | `1` | Non |

---

## 2. Cotes d'engrènement vérifiées (Zéro collision)

L'ensemble roue / pignon / crémaillère / tuile d'action a été calibré pour fonctionner sur **tous** les rails sans frottement :

- **Fond de rainure de rail** : `z = 9,0 mm` | **Plateau central normal / bois** : `z = 12,0 mm`.
- **Roue (`loco_roue_25_5mm.stl`)** : bande de roulement **`Ø 24,0 mm`** (`R = 12,0 mm`) et boudin intérieur **`Ø 27,6 mm`** → place l'axe d'essieu à **`z_essieu = 21,0 mm`**.
- **Pignon central (`loco_pignon_central_essieu.stl`)** : `12` dents, **`Ø extérieur = 16,8 mm`** (`R = 8,4 mm`) → point bas des dents à **`z = 12,6 mm`** :
  - **`+0,6 mm` de garde** au-dessus des rails standards et en bois (`12,0 mm`).
  - **`+0,2 mm` (ou `+0,6–1,0 mm` avec pneu TPU)** au-dessus du canal central abaissé des tuiles d'action (`12,4 mm`).
  - **`1,4 mm` d'engrènement** dans la crémaillère du rail Funky (`z = 14,0 mm`).
- **Capteur de couleur `APDS-9960`** : fenêtre de `8,0 × 8,2 mm` décalée à **`y = +4,7 mm`** sous le châssis pour lire directement l'aile colorée de la tuile (`y ∈ [2,2, 9,0 mm]`).

---

## 3. Paramètres de tranchage recommandés (Slicer)

Pour Bambu Studio, PrusaSlicer ou Cura :
- **Hauteur de couche** : `0,20 mm` (`0,16 mm` recommandé pour `loco_pignon_central_essieu.stl` et `loco_roue_25_5mm.stl`).
- **Périmètres (murs)** : `3` boucles (`1,2 mm` avec buse `0,4 mm`) pour la solidité des clips Snap-Fit et des patins Coaster Hooks.
- **Remplissage** : `15–20 % Gyroid` (piliers, rails) et `40–100 %` pour le pignon et les roues.
- **Matériaux** :
  - **PETG** : fortement recommandé pour les **rails à clips Snap-Fit**, les **tuiles d'action** et le **châssis** (légère souplesse élastique, ne casse pas à l'assemblage).
  - **PLA+** : parfait pour la **coque**, les **piliers** et le **pignon**.
  - **TPU 95A** (ou joints toriques caoutchouc `14 × 2 mm` / `#12`) : dans la gorge annulaire des 4 roues pour une adhérence maximale en côte.
- **Supports** : désactivés sur **10 pièces sur 11** ; activer uniquement les **supports arborescents (plateau uniquement)** sous le plancher de `loco_chassis_inferieur.stl` (faciles à retirer à la pince).

---

## 4. Protocole de validation en 3 étapes

1. **Test 1 — Jonctions Snap-Fit & Compatibilité Bois (4 pièces, ~2 h d'impression)**
   - Imprimer `2 × rail_droit_100mm_snapfit.stl`, `1 × adaptateur_rail_bois.stl` et `1 × pilier_verrouillable_duplo.stl`.
   - Vérifier le « clic » d'assemblage sur un tapis, l'absence de jeu vertical sur la jonction posée sur le pilier, l'insertion sur des gros blocs de construction à la maison et le raccord sur un rail en bois existant.
2. **Test 2 — Roulage & Tuile d'action (~2 h d'impression)**
   - Imprimer `1 × loco_chassis_inferieur.stl`, `4 × loco_roue_25_5mm.stl`, `1 × loco_pignon_central_essieu.stl` et `1 × tuile_action_clipsable.stl`.
   - Monter deux axes `Ø 3 mm` (tige acier/laiton de `40 mm`), glisser les roues + le pignon au centre de l'essieu arrière et faire rouler à la main sur les rails normaux, bois, côte striée et tuile d'action pour valider l'absence totale de frottement.
3. **Test 3 — Système « Funky / Anti-Gravité »**
   - Imprimer `1 × rail_funky_cremaillere_captif.stl` et coller deux bandes d'acier (`~2 mm × 0,8 mm × 80 mm`) dans les loges latérales.
   - Insérer un aimant néodyme `20 × 10 × 3 mm` dans la loge du châssis (puis poser la coque `loco_coque_superieure_monobloc.stl` par-dessus) et vérifier à la main que les patins 45°, le pignon et l'aimant maintiennent solidement le châssis même retourné à **180°**.
