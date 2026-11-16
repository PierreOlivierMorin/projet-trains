# Plan de Développement STL & Benchmark pour Modèle Local

Ce document sert de **banc d'essai progressif** pour évaluer la capacité de votre modèle local à concevoir, programmer en Python et exporter des fichiers `.STL` valides et mécaniquement compatibles avec le **Projet Trains V1**.

---

## 1. Contrat d'Interface Mécanique (Prompt Système à donner au modèle local)

Avant de demander une pièce au modèle local, donnez-lui ce bloc de contexte fixe pour garantir la compatibilité 1:1 avec vos pièces existantes :

```text
Tu développes des pièces CAO 3D en Python pur (sans dépendance externe, en important
`WatertightMesh`, `add_female_and_body`, `add_male_snapfit` depuis `03-cao-3d/generer_prototype_rails.py`)
pour le système de train modulaire Projet Trains V1.

RÈGLES MÉCANIQUES INVARIANTES (en mm) :
- Profil de rail standard : largeur = 40.0, hauteur = 12.0, plateau Z = 0.0 sur le lit.
- Rainures de roulement : largeur = 6.0, profondeur = 3.0 (fond à z = 9.0),
  espacement centre-à-centre TRACK_GAUGE = 25.5 (GROOVE_INNER_Y = 9.75, GROOVE_OUTER_Y = 15.75).
- Jonctions : prise femelle [0.0 .. 17.2] et languette mâle Snap-Fit [16.5] avec tolérance
  PRINT_CLEARANCE = 0.20 par face et verrouillage vertical V-groove 45° (z = 4.5..7.5).
- Rail Funky : crémaillère centrale y ∈ [-1.60, +1.60], z = 12.0..14.0 (pas 4.0, dent 2.0),
  loges acier y ∈ [±5.10, ±7.25] (z = 11.0..12.0), glissières captives 45° sur y = ±20.0 -> ±18.5 (z = 4.5..7.5).
- Locomotive : essieu à z_rail = 21.0, roues Ø 24.0 (boudin Ø 27.6), pignon central 12 dents Ø 16.8
  (bas des dents à z = 12.6, garde +0.6 au-dessus des rails normaux, prise 1.4 dans crémaillère 14.0).
- Gros blocs (piliers/wagons) : grille 15.9 mm, tenons Ø 9.4 mm, hauteur 4.5 mm.
- Sécurité impression : maillage 100 % étanche (verify_manifold()), Z_min == 0.0, 0 triangle dégénéré,
  surplombs <= 45° (imprimable sans supports autant que possible).
```

---

## 2. Feuille de route en 5 Niveaux (Progressif)

### Niveau 1 — Géométrie prismatique & Calibration *(Test de base)*
*Vérifie si le modèle maîtrise `WatertightMesh`, l'orientation des faces et les tolérances.*

1. **Tâche 1.1 : `jauge_calibration_tolerances.stl`**
   - Plaquette de test (`80 × 55 × 12 mm`) intégrant **4 encoches Snap-Fit femelles** avec jeux de `0,10 mm`, `0,15 mm`, `0,20 mm` et `0,25 mm` + **4 alésages verticaux** (`Ø 2,95 / 3,00 / 3,05 / 3,10 mm`) pour tester la précision de votre imprimante avec une tige d'axe `Ø 3 mm`.
2. **Tâche 1.2 : `butoir_fin_de_voie.stl`**
   - Rail court (`60 × 40 mm`) équipé d'une prise Snap-Fit femelle (`x = 0..17,2`) et d'un heurtoir vertical (`x = 45..60`, `z = 12..28 mm`) présentant une face plane frontale pour déclencher l'arrêt propre du capteur laser `VL53L0X` de la locomotive.

### Niveau 2 — Pièces roulantes & Attelages *(Intermédiaire)*
*Vérifie l'assemblage multi-contraintes et la compatibilité avec le châssis locomotive.*

3. **Tâche 2.1 : `wagon_cargo_modulaire.stl`**
   - Châssis de wagon passif (`70 × 40 × 18 mm`, `z_essieu = 21,0 mm` avec 4 paliers en U pour `Ø 3 mm`, passages de roues `loco_roue_25_5mm.stl`), un **crochet mâle à l'avant** compatible avec l'anneau arrière de la locomotive (`6 × 7 mm`), un **anneau femelle à l'arrière**, et un **plateau supérieur à 4×2 tenons format gros blocs** (`15,9 mm`, `Ø 9,4 mm`) pour empiler des blocs sur le wagon.

### Niveau 3 — Courbes 3D & Rampes progressives *(Avancé — Test mathématique)*
*Vérifie si le modèle maîtrise les transformations paramétriques 3D $C^1$ sans briser l'étanchéité.*

4. **Tâche 3.1 : `rampe_progressive_courbe_S.stl`**
   - Rail de montée de `160 mm` de long élevant la voie de `z = 0` à `z = 25 mm` selon une courbe cubique en S :
     $$z(x) = H \cdot (3t^2 - 2t^3), \quad t = \frac{x - 18}{124} \in [0, 1]$$
     garantissant des entrées/sorties **100 % horizontales** (`z'(0) = z'(160) = 0`), sans aucune cassure d'angle, avec micro-stries dans les deux rainures.
5. **Tâche 3.2 : `rail_transition_mur_90deg.stl`**
   - Courbe verticale concave de `90°` (`R_vertical = 110 mm`) embarquant la **crémaillère centrale (`z_local = 12..14 mm`)**, les deux loges d'acier et les glissières captives `45°` pour faire passer le train du sol horizontal à une ascension verticale à `90°`.
6. **Tâche 3.3 : `segment_looping_45deg.stl`**
   - Segment d'arc vertical de `45°` (`R_loop = 140 mm`, 8 segments = Looping 360° complet) intégrant un **décalage hélicoïdal latéral (`+6,0 mm` en Y par segment = `48 mm` sur 360°)** pour que la locomotive passe à côté de sa voie d'entrée sans collision en fin de boucle.

### Niveau 4 — Mécanismes articulés & Électromécanique *(Expert)*
*Vérifie la conception de pièces mobiles imbriquées et logements de composants.*

7. **Tâche 4.1 : `aiguillage_smart_switch_corps.stl` + `aiguillage_lame_mobile.stl`**
   - Bifurcation droite / courbe (`160 mm` de long, 1 entrée Snap-Fit femelle → 2 sorties mâles à `0°` et `30°`), incluant sous la voie un logement fermé pour **micro-servo `SG90` (`23,0 × 12,2 mm`)** et **Mini-PCB universel (`35,0 × 22,0 mm`)**, plus la **lame pivotante séparée** sur axe `Ø 3,0 mm`.

### Niveau 5 — Ergonomie & Boîtier électronique complet *(Maître)*
*Vérifie la conception complète d'un boîtier bipièce vissé avec ergonomie enfant.*

8. **Tâche 5.1 : `telecommande_boitier_inf.stl` + `telecommande_couvercle_sup.stl`**
   - Manette arrondie pour mains de 3–6 ans (`110 × 65 × 28 mm`), compartiment vissé pour **2×AAA**, logement du **Mini-PCB universel (`35 × 22 mm`)**, fente pour **levier de vitesse central** avant/arrière, **3 découpes de gros boutons** (Klaxon, Phares, Aiguillage) et **4 cheminées de vis M3** avec logement d'écrou/insert.

---

## 3. Prompts prêts à copier-coller pour tester votre modèle local

### Prompt Niveau 1 (`butoir_fin_de_voie.stl`)
```text
[Coller d'abord le Contrat d'Interface Mécanique ci-dessus]
Mission (Niveau 1) : Écris un script Python `03-cao-3d/gen_niveau1_butoir.py` qui génère
`03-cao-3d/stl/butoir_fin_de_voie.stl` à l'aide de `WatertightMesh`.
Spécifications :
- Rail de 60 mm de long (x = 0..60), 40 mm de large, 12 mm de haut, rainures 25,5 mm.
- Prise Snap-Fit femelle standard à x = 0..17,2 (réutilise `add_female_and_body` ou la géométrie exacte).
- À x = 44..60, érige un bloc butoir de 40 mm de large montant jusqu'à z = 28 mm, avec un panneau
  frontal plat à x = 44 mm face au train (pour le capteur laser VL53L0X).
- Appelle `mesh.verify_manifold()` avant d'écrire le fichier.
```

### Prompt Niveau 2 (`wagon_cargo_modulaire.stl`)
```text
[Coller le Contrat d'Interface Mécanique]
Mission (Niveau 2) : Écris `03-cao-3d/gen_niveau2_wagon.py` générant
`03-cao-3d/stl/wagon_cargo_modulaire.stl`.
Spécifications :
- Châssis 70 mm de long (x = 0..70) × 40 mm de large, reposant sur 2 essieux à x = 15 et x = 55
  avec paliers en U de 3,2 mm orientés pour les roues `loco_roue_25_5mm.stl` (passages de roues dégagés).
- Avant (x = 70..80) : bras d'attelage en crochet (5 × 5 mm) s'insérant dans un anneau de 6 × 7 mm.
- Arrière (x = -10..0) : anneau d'attelage femelle identique à celui de la locomotive.
- Plateau supérieur (z = 16..20,5) : 4×2 tenons cylindriques Ø 9,4 mm espacés de 15,9 mm.
- Vérifie l'étanchéité avec `mesh.verify_manifold()` et imprime Z_min = 0.
```

### Prompt Niveau 3 (`rampe_progressive_courbe_S.stl` ou `rail_transition_mur_90deg.stl`)
```text
[Coller le Contrat d'Interface Mécanique]
Mission (Niveau 3) : Écris `03-cao-3d/gen_niveau3_rampe_S.py` générant
`03-cao-3d/stl/rampe_progressive_courbe_S.stl`.
Spécifications :
- Rail droit en XY de longueur horizontale totale 160 mm (connecteur femelle horizontal à x = 0..18,
  connecteur mâle Snap-Fit horizontal à x = 142..176,5 surélevé de H = 25,0 mm).
- Entre x = 18 et x = 142 (L = 124 mm, 32 tranches), la surface inférieure reste posée ou soutenue
  par un socle plein jusqu'à z = 0, et le lit du rail suit la courbe cubique
  z_rail(t) = 25.0 * (3*t^2 - 2*t^3) pour garantir une pente nulle aux deux jonctions Snap-Fit.
- Ajoute les micro-stries de traction dans les deux rainures sur la partie montante.
- Vérifie que `mesh.verify_manifold()` passe avec 0 arête ouverte et `Z_min == 0.0`.
```

### Prompt Niveau 4 (`aiguillage_smart_switch`)
```text
[Coller le Contrat d'Interface Mécanique]
Mission (Niveau 4) : Écris `03-cao-3d/gen_niveau4_aiguillage.py` générant
`03-cao-3d/stl/aiguillage_smart_switch_corps.stl` et `03-cao-3d/stl/aiguillage_lame_mobile.stl`.
Spécifications :
- Entrée femelle Snap-Fit à x = 0..18 ; voie principale droite (x = 0..160) avec sortie mâle ;
  voie déviée se séparant à x = 35 avec une courbe de 30° et sortie mâle Snap-Fit.
- Logement inférieur évidé pour servo SG90 (23,0 × 12,2 mm) et Mini-PCB (35,0 × 22,0 mm).
- Lame d'aiguillage séparée pivotant sur un axe Ø 3,0 mm (jeu 0,25 mm) pour guider les boudins
  des roues Ø 27,6 mm vers la voie droite ou déviée.
- Vérifie l'étanchéité de chaque STL avec `mesh.verify_manifold()`.
```

### Prompt Niveau 5 (`telecommande`)
```text
[Coller le Contrat d'Interface Mécanique]
Mission (Niveau 5) : Écris `03-cao-3d/gen_niveau5_telecommande.py` générant
`03-cao-3d/stl/telecommande_boitier_inf.stl` et `03-cao-3d/stl/telecommande_couvercle_sup.stl`.
Spécifications :
- Boîtier bipièce ergonomique (110 × 65 × 28 mm hors-tout) avec bords chanfreinés à 45°.
- Boîtier inférieur : logement 2×AAA (52 × 24 × 13 mm), entretoises Mini-PCB (35 × 22 mm),
  4 cheminées d'assemblage M3 (Ø 3,2 mm).
- Couvercle supérieur : 1 fente centrale (22 × 6 mm) pour levier avant/arrière, 3 perçages Ø 12 mm
  pour gros boutons poussoirs (Klaxon, Phares, Aiguillage) et 1 fenêtre Ø 5 mm pour LED d'état.
- Les deux fichiers doivent passer `verify_manifold()` et s'imprimer sans supports.
```

---

## 4. Grille d'évaluation du modèle local (sur 100 points)

Pour chaque niveau testé, lancez `python3 03-cao-3d/verifier_stl.py --update-viewer` et notez votre modèle :

| Critère | Points | Comment vérifier |
| :--- | :---: | :--- |
| **1. Code Python autonome exécutable** | `/ 20` | Le script s'exécute sans erreur ni librairie manquante |
| **2. Étanchéité topologique (`verify_manifold`)** | `/ 30` | `verifier_stl.py` affiche `[PASS]` (`0` arête ouverte, volume `> 0`, `0` triangle nul) |
| **3. Respect des cotes d'interface V1** | `/ 30` | Visuellement aligné dans `visualiseur-assemblage.html` (écartement `25,5 mm`, `Z_min = 0`) |
| **4. Imprimabilité FDM réelle** | `/ 20` | Parois `>= 1,2 mm`, pas de porte-à-faux `> 45°` inutiles, s'imprime à plat |

> [!TIP]
> **Où s'arrêtent généralement les modèles locaux ?**
> - Les petits modèles (7B–14B) réussissent bien le **Niveau 1**, peinent au **Niveau 2** sur l'annulation des faces internes (`0` arête ouverte) et échouent souvent au **Niveau 3** (courbes 3D sans auto-intersection).
> - Les bons modèles de code (32B+ ou spécialisés) réussissent jusqu'aux **Niveaux 3–4** s'ils s'appuient proprement sur `WatertightMesh` et `add_hex`.
