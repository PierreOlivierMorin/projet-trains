# Décisions CAO V2 — Itération « pièces finies » et circuit de test (`/grill-me`, 16 nov. 2026)

Ce document consigne les décisions prises pour la deuxième itération CAO : passage à un vrai noyau de CAO, finition « jouet en bois premium » et conception d'un circuit de test complet. Il complète (sans le modifier) le cahier des charges [`decisions-design-v1.md`](../02-prototype-v1/decisions-design-v1.md).

---

### 1. Outils et organisation du code
- **CadQuery** (noyau OpenCASCADE) remplace le maillage Python pur `WatertightMesh` : vrais congés/chanfreins, booléens, export **STL + STEP** (`03-cao-3d/step/`, format destiné au futur mouliste V2).
- Environnement Python isolé propre au projet (le Python système 3.9 n'est pas modifié). `verifier_stl.py` reste en Python pur et sert de suite de tests.
- **Socle commun `cao_commun.py`** (profil de rail, Snap-Fit, constantes d'interface) + **un générateur par famille de pièces**.
- Historique : dépôt git initialisé ; la V1 Python pur reste récupérable dans le premier commit.

### 2. Délégation au modèle local
- **gpt-oss-20b** (LM Studio, serveur `localhost:1234`) reçoit les tâches de niveau 1 : **jauge de calibration** et **butoir**, avec le contrat d'interface réécrit pour CadQuery.
- Essais illimités (modèle gratuit) ; chaque résultat est validé par Claude (`verifier_stl.py` + contrôle des cotes) et noté sur la grille de [`plan-developpement-stl-benchmark.md`](./plan-developpement-stl-benchmark.md).

### 3. Style « jouet en bois premium » (valeurs de départ, à peaufiner)
| Zone | Traitement |
| :--- | :--- |
| Arêtes supérieures extérieures des rails | Congé `R = 2,0 mm` |
| Dessus des rails entre les rainures | Plat (appui des tuiles d'action) |
| Lèvres des rainures | Congé `R = 0,5 mm` |
| Arête basse sur le plateau d'impression | Chanfrein `0,6 mm` à 45° (pas de congé : porte-à-faux / patte d'éléphant) |
| Entrée des rainures à chaque jonction | Chanfrein d'entrée `0,4 mm` |
| Locomotive et wagon | Congés `R = 3,0 mm` |
| Toute arête accessible | `R ≥ 0,5 mm` (ASTM F963, bords et pointes) |

- **Rails évidés à nervures** (parois `2 mm`, nervures transversales, ~40 % de matière en moins) ; Snap-Fit et rainures restent pleins.
- **Taille maximale d'une pièce : 240 mm** (plateau Bambu Lab X1C `256 × 256 mm`).

### 4. Géométrie de voie
- Angles simples uniquement : **45°** (`R = 180 mm`, 8 pièces = cercle) aujourd'hui, **22,5°** plus tard. **Jamais de 30°.**
- La voie déviée de l'aiguillage reprend exactement la courbe standard 45° / `R = 180`.
- **Module de hauteur : 12,5 mm.** Rampes en 3 types (pied concave, milieu à pente constante, tête convexe), chacune `+12,5 mm`, pente max ~9 % (< 14 % de la décision V1 n°3) ; utilisées à l'envers pour descendre.
- **Piliers** : hauteurs fixes `25` et `50 mm` + **rehausse `12,5 mm`** verrouillable (2 étages max). Le pilier 50 mm actuel est conservé (réécrit en CadQuery).

### 5. Circuit de test
- **Forme** : 8 inscrit dans un ovale (style coffret classique), **ovale élargi à ~1,1 × 1,6 m** par des droits verticaux aux extrémités. Les extrémités sont partagées entre le 8 et l'ovale ; **4 aiguillages = 2 communications** ; **croisement central à niveau** (pièce en X à 90°).
- **Viaduc 50 mm** sur un côté droit de l'ovale (4 rampes de chaque côté + tablier sur piliers) : test en conditions réelles des transitions, joints sur piliers, PID en montée et freinage en descente.
- **Côté opposé** : **gare** (voie de garage, 1 aiguillage + **butoir** = cible du capteur ToF) et **tunnel** décoratif (dégagement ≥ 62,5 mm).
- Également présents : **tuiles d'action**, **adaptateur rail bois**.
- **Aiguillages manuels** (levier latéral), versions **gauche et droite** (miroir), logements vides réservés pour servo `SG90` et Mini-PCB `35 × 22 mm`.
- **Plan du circuit vu de dessus** généré avant les nouvelles pièces : vérification mathématique de la fermeture des boucles, nomenclature, temps et filament estimés, besoin éventuel d'un **demi-droit 50 mm**.

### 6. Banc de pente réglable (instrument de test)
- Rail droit sur support à crans (`5°`, `8°` (≈14 %), `10°`, `15°`, `20°`, `25°`, `30°`) avec butée haute.
- Mesures : pente limite (patinage/calage selon pneu TPU, rail strié ou lisse, niveau des piles), calibration de l'IMU sur angles connus, réglage du PID (même vitesse à plat et en montée).

### 7. Reporté
- **Pont central sur crémaillère « Funky »** : pièce d'extension remplaçant le croisement à niveau, après validation du Test 3.
- Transition mur 90°, segment de looping, télécommande, courbe 22,5°.

### 8. Ordre de travail
1. Socle CadQuery (`cao_commun.py`).
2. Jauge de calibration (gpt-oss) → **première impression**.
3. Refonte des 11 pièces existantes.
4. Plan du circuit vu de dessus.
5. Nouvelles pièces : butoir (gpt-oss), wagon, rampes ×3, aiguillages G/D, croisement, pilier 25 + rehausse, banc de pente, tunnel.
