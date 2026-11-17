# Plan d'assemblage et liste d'achats — Prototype V2

Ce document dit **quoi acheter**, **dans quel ordre imprimer** et **comment monter** les pièces disponibles. Les cotes, paramètres de tranchage et contrôles CAO sont dans le [guide d'impression](./guide-impression-et-assemblage-v1.md) ; pour voir les pièces en 3D avant d'imprimer, ouvrez le [visualiseur](./visualiseur-assemblage.html) (scène « Assemblage », curseur d'éclatement).

> [!IMPORTANT]
> **Deux pièces dépendent du moteur réellement reçu** : le support moteur et la coque, dont la hauteur de cabine suit le carter. Imprimez tout le reste, mais attendez d'avoir mesuré le N20 pour ces deux-là (étape B1).

---

## 1. Liste d'achats

### Locomotive — indispensable

| Article | Spécification | Qté | Rôle | Remarques |
| :--- | :--- | :---: | :--- | :--- |
| Motoréducteur **N20 à vis sans fin** | 6 V, **150–200 tr/min**, arbre de sortie `Ø 3` à méplat (en D), sortie à 90° | 1 (+1 de rechange) | Traction | Ne pas prendre ~300 tr/min : la paire d'engrenages multiplie déjà ×1,43 |
| Tige acier | `Ø 3 mm` rectifiée (acier ou inox), ≥ 100 mm | 1 | 2 essieux de `29 mm` | Couper à 29 mm et ébavurer |
| Aimants néodyme **N52** | `20 × 5 × 3 mm` | 2 (+2) | Adhérence sur les rails Funky | Scellés dans le châssis (pause d'impression) |
| Aimant néodyme | `Ø 3 × 1 mm` | 1 (lot) | Codeur de vitesse (mode Alpha) | Scellé dès maintenant dans la roue codeur |
| **Contacts de piles AAA** | 1 ressort simple, 1 plaque simple, **2 doubles ressort-plaque** ; largeur ≤ `10 mm`, tôle ≤ `0,6 mm` | 1 jeu | Bac à piles | Souvent vendus en assortiment « battery spring contact plates » |
| Piles **AAA** | Alcalines 1,5 V | 3 | Alimentation 4,5 V | Les NiMH (3,6 V) font rouler plus lentement |
| Interrupteur à glissière | **SS-12D00G4** (levier de 4 mm) | 1 (lot) | Marche / arrêt | Logé dans le flanc droit de la cabine |
| Vis M3 × 10 **tête fraisée** | Acier | 4 | Bac sur les poteaux | Se taraudent dans les avant-trous `Ø 2,5` |
| Vis M3 × 10 tête cylindrique | Acier | 1 | Coque, cachée dans la cheminée | |
| Vis M2 × 6 | Acier | 2 | Support moteur | |
| Collier de serrage | Largeur `2,5 mm` | 1 | Maintien du réducteur | |
| Fil souple | 26–28 AWG, rouge + noir, ~50 cm | 1 | Piles → interrupteur → moteur | + gaine thermorétractable `Ø 1,5–2` |

**En option** : 4 joints toriques NBR **`20 × 1,5 mm`** (diamètre intérieur × section) comme pneus dans la gorge des roues. Ils améliorent l'adhérence mais relèvent la loco de `0,4 mm` (engrènement Funky `1,0` au lieu de `1,4 mm`). *L'ancienne mention « 14 × 2 » était fausse : le fond de gorge est à `Ø 21,8`.*

### Voie

| Article | Spécification | Qté | Rôle |
| :--- | :--- | :---: | :--- |
| Feuillard **acier doux** | `~2 × 0,8 mm`, coupé à `80 mm` | 2 par rail Funky | Cible des aimants. **Pas d'inox 304**, qui n'est pas magnétique |
| Colle cyanoacrylate | Gel | 1 | Bandes d'acier dans leurs loges |

### Filament (Bambu X1C)

| Matière | Quantité conseillée | Pièces |
| :--- | :--- | :--- |
| **PETG** | 1 kg | Rails, aiguillages, châssis, bac à piles, coque, support moteur |
| **PLA+** | 0,5 kg | Piliers, roues, pignon, engrenages, lames et levier d'aiguillage, jauge |
| TPU 95A *(option)* | — | Pneus à la place des joints toriques |

Le kit de démarrage (§ 3.C) plus la loco et deux aiguillages consomment ~`0,4 kg`. Le circuit de test complet en demande ~`1,1 kg`.

### Outillage

**Pied à coulisse** (indispensable pour mesurer le N20 et les pièces imprimées) · fer à souder + étain · tournevis cruciforme et plat · pince coupante · petite lime et foret `Ø 3` (reprise d'un palier trop serré) · scie à métaux ou disque pour couper la tige.

### Mode Alpha — plus tard, ne pas acheter maintenant

Le plateau électronique sera dessiné quand les modules auront été achetés et mesurés (baie libre sous le bac à piles). Liste prévue :
- `XIAO ESP32C3` ;
- pont en H `DRV8833` ;
- régulateur buck-boost 5 V ;
- capteur ToF `VL53L0X` ;
- 2 LED `WS2812B` 5 mm traversantes ;
- capteur Hall `A3144` ;
- bouton poussoir ;
- buzzer ;
- lecteur RFID `PN532` compact.

---

## 2. Ordre d'impression

| Étape | Pièces | Pourquoi dans cet ordre |
| :---: | :--- | :--- |
| **0** | `jauge_calibration_tolerances` | Règle le jeu des clips et le serrage des roues avant tout le reste |
| **1** | Kit de démarrage : 8 × `rail_courbe_45deg_snapfit`, 2 × `rail_droit_100mm_snapfit`, 1 × `rail_funky_cremaillere_captif`, 1 × `rail_cote_100mm_strie` (+ `adaptateur_rail_bois`, 1 pilier si besoin) | Une boucle fermée de ~`0,6 × 0,4 m` pour essayer la loco |
| **2** | Loco : `loco_chassis_test` (**pause** aimants), 3 × `loco_roue_24mm`, 1 × `loco_roue_24mm_codeur` (**pause**), `loco_pignon_central_essieu`, `loco_engrenage_essieu`, `loco_engrenage_moteur`, `loco_bac_piles` | Ne dépendent pas des cotes du moteur |
| **3** | `loco_support_moteur`, `loco_coque_vapeur` | **Après mesure du N20** (étape B1) |
| **4** | Aiguillages : variantes au choix, `aiguillage_lame_gauche/droite`, `aiguillage_levier` | Selon le circuit visé |

---

## 3. Assemblage

### A. Calibration (jauge)

1. Enfoncer l'embout mâle d'un rail imprimé dans chacune des 4 prises de la jauge. Retenir celle qui **clique sans forcer ni ballotter** → `cao_commun.JEU_IMPRESSION`.
2. Glisser la tige `Ø 3` dans les 4 trous. Retenir celui où elle **tourne librement sans jeu** → `ALESAGE_PALIER`, et celui où elle **tient serrée** → `ALESAGE_SERRE` (dans `generer_locomotive.py`).
3. Régénérer (`generer_rails.py`, `generer_locomotive.py`, `generer_aiguillages.py`), relancer les contrôles, puis imprimer la suite.

### B. Locomotive

**Repères** : l'avant est côté chaudière. La **gauche** (`+y`) porte la roue codeur et l'engrenage. La **droite** (`−y`) porte l'interrupteur et le support moteur.

**B1. Mesurer le moteur et régénérer**
Relever au pied à coulisse :
- réducteur : épaisseur, largeur, longueur, hauteur de l'arbre depuis le bas ;
- moteur : diamètre, et longueur **cosses comprises** ;
- arbre : diamètre, cote sur plat, longueur.

Reporter ces cotes dans `MOTEUR` (`generer_locomotive.py`), puis :

```bash
.venv/bin/python 03-cao-3d/generer_locomotive.py
```

```bash
.venv/bin/python outils/controler_locomotive.py
```

Le contrôle doit afficher `LOCOMOTIVE CONFORME`, avec une hauteur ≤ `61,5 mm` (tunnel). Si le moteur est trop haut, il faut revoir `ANGLE_ARBRE` avant d'imprimer la coque.

**B2. Châssis (pendant l'impression)**
À la pause `z = 3,6 mm`, poser les **2 aimants 20 × 5 × 3** dans leurs loges, **même pôle vers le haut** : ils se repoussent, tenez-les le temps de reprendre l'impression.

**B3. Roue codeur (pendant l'impression)**
À la pause `z = 1,8 mm`, poser l'aimant `Ø 3 × 1`.

**B4. Essieu arrière (libre)**
1. Couper une tige à `29 mm` et ébavurer.
2. Emmancher la **roue codeur** sur un bout, moyeu vers l'intérieur.
3. Passer la tige dans les deux paliers arrière, roue codeur à **gauche** (face à la loge du capteur Hall).
4. Emmancher la seconde roue à droite. L'essieu doit tourner librement ; sinon, reprendre les paliers au foret `Ø 3`.

**B5. Essieu avant (moteur)**
1. Passer la tige dans le palier droit.
2. Enfiler le **pignon d'escalade**, centré sur l'axe de la loco (au-dessus du canal de crémaillère), puis l'**engrenage 14 dents**, à `3 mm` à gauche du centre.
3. Traverser le palier gauche.
4. Emmancher les deux roues, moyeux vers les paliers.
5. Contrôle : le pignon passe au-dessus d'un rail standard (`0,6 mm` de garde).

**B6. Moteur**
1. Emmancher l'**engrenage 20 dents** sur l'arbre en D, face plate côté moteur, moyeu vers l'extérieur.
2. Poser le réducteur dans le support et le serrer avec le collier.
3. Visser le support sur le plancher avec 2 vis M2 × 6. Les trous oblongs permettent de régler l'engrènement : un léger jeu, sans point dur sur un tour complet.

**B7. Bac à piles**

Glisser les contacts par le haut dans les fentes :

```
                     AVANT (côté chaudière)
   y = −11 (droite)        y = 0               y = +11 (gauche)
   [ressort −] → fil −     [plaque ═════════ ressort]   (double)
     pile A : − avant        pile B : + avant      pile C : − avant
   [plaque ═════════ ressort]  (double)        [plaque +] → fil +
                     ARRIÈRE
```

1. Les fils sortent par les encoches : `−` à l'avant droite, `+` à l'arrière gauche. Les souder **avant** de poser les piles.
2. Visser le bac sur les 4 poteaux avec les **M3 × 10 fraisées**.
3. Les piles se posent sur les nervures, dans le sens indiqué ci-dessus. Vérifier `~4,5 V` entre les fils.

**B8. Câblage**
1. Passer le **fil +** par l'interrupteur, puis vers une cosse du moteur ; le **fil −** va à l'autre cosse.
2. Laisser `~10 cm` de mou, pour pouvoir retirer la coque.
3. Isoler à la gaine thermorétractable.
4. Si la loco recule, inverser les deux fils du moteur.

**B9. Interrupteur et coque**
1. Coque retournée, glisser l'interrupteur `SS-12D00` dans les glissières du flanc droit de la cabine, levier dans la fente, jusqu'à l'étagère.
2. **Pose** : accrocher la **lèvre arrière** de la coque sous l'arrière du bac, nez relevé, puis rabattre le nez. Ce mouvement a été contrôlé de `0,5°` à `20°`, sans interférence.
3. Visser la **M3 × 10** au fond de la cheminée, dans le poteau du châssis.
4. Pour changer les piles, il suffit de retirer cette vis : il faut un outil, ce que demande la norme EN 71.

**B10. Essais (protocole n° 3 du guide)**
1. Faire rouler la loco sur le droit, puis sur la boucle de courbes `R = 180`.
2. Tester la côte striée et le rail Funky (aimants et engrènement).
3. Noter les points durs, le patinage et le bruit.

### C. Voie — kit de démarrage

1. Assembler la boucle **courbe → courbe → … (×4) → droit → droit → courbe ×4 → Funky → côte striée**.
2. Chaque rail se raccorde d'un **mâle dans un femelle** : il clique, puis se verrouille verticalement.
3. Funky : coller les 2 bandes d'acier dans les loges, au gel cyano, affleurantes.
4. Rails en bois : l'**adaptateur** se clipse sur un mâle et présente une cheville de rail bois.
5. Sur gros blocs : poser le **pilier**, puis clipser le rail sur sa tête verrouillable.

### D. Aiguillages

1. Poser la **lame** dans son logement, tenon dans le trou du fond.
2. Retourner l'aiguillage. Passer le **levier** par la lumière du flanc et l'emmancher sur le carré du tenon.
3. Contrôle (protocole n° 4) :
   - basculer le levier ;
   - faire passer la loco par les deux branches, dans les deux sens ;
   - en arrivant par la branche fermée, elle doit retourner la lame sans dérailler ;
   - la lame ne doit pas basculer seule.

---

## 4. Ce qui n'est pas encore dessiné

Pour le circuit de test complet (plan `1,51 × 1,01 m`), il manque :
- le croisement ;
- les rampes ;
- le tablier du viaduc ;
- les droits de 50 et 86,7 mm ;
- les rails-balises ;
- le butoir ;
- le plateau électronique de la loco ;
- le wagon.

Le kit de démarrage et les aiguillages suffisent pour valider la locomotive et la voie.
