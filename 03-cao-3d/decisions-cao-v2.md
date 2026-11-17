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
- **Forme** : 8 inscrit dans un ovale (style coffret classique), **ovale élargi à ~1,0 × 1,5 m** (calculé avec le viaduc 25 mm, §11) par des droits verticaux aux extrémités. Les extrémités sont partagées entre le 8 et l'ovale ; **4 aiguillages = 2 communications** ; **croisement central à niveau** (pièce en X à 90°).
- **Viaduc 25 mm** *(ramené de 50 mm le 17 nov. 2026, voir §11)* sur un côté droit de l'ovale (pied + milieu + tête de chaque côté + tablier sur 2 piliers de 25 mm) : test en conditions réelles des transitions, joints sur piliers, PID en montée et freinage en descente.
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

### 8. Écarts constatés pendant le portage
- **Languette / prise femelle (corrigé)** : en V1, la crête en V de la languette commençait avant la gorge de la prise (chevauchement ~0,2 mm vers x = 10,9). En V2, la gorge épouse la languette avec `0,20 mm` de jeu à partir de x = 10,2 ; interférence entre deux rails assemblés = 0.
- **Congés des coins verticaux aux jonctions (retirés)** : leur raccord avec le congé R2 du dessus produisait des facettes défectueuses dans le STL. Coins invisibles une fois assemblés ; à reprendre lors du polissage.
- **Boudin des roues (tranché : supprimé)** : en V1, le boudin `Ø 27,6 mm` descendait à `z = 7,2 mm`, `1,8 mm` sous le fond de rainure, y compris sur rail bois. Roue V2 : `Ø 24`, `5 mm` de large, **sans boudin**, guidée par les parois de la rainure de `6 mm` (comme les trains en bois) ; gorge de pneu conservée.
- **Patins captifs « Coaster Hooks » (à trancher)** : en V1 ils s'avancent jusqu'à `|y| = 19,0` entre `z = 4,5` et `7,5`, alors que les flancs d'un rail standard et d'un rail bois sont plats à `|y| = 20` : collision de `1 mm` hors des rails Funky.
- **Paliers d'essieux / coque (à reconcevoir)** : les paliers du châssis (`|y|` 17,2–20,3) occupent le volume des parois latérales de la coque (`|y|` 17,5–20) : la coque ne peut pas se fermer.
- **Transmission absente** : le berceau du moteur N20 est longitudinal, aucun renvoi vers l'essieu n'est modélisé.
- Conséquence : châssis et coque V1 conservés tels quels en attendant une reconception de la locomotive ; roue et pignon portés en CadQuery (`generer_locomotive.py`).

- **Tuile d'action (tranché : remplacée)** : les pattes de clipsage (|y| ∈ [8,4 ; 9,85]) chevauchaient le plateau central du rail (|y| ≤ 9,75) de `1,35 mm`, et la tuile (`30 × 19,7 × 3,2 mm`) tenait dans le cylindre des petites pièces (interdite sous 3 ans). Remplacée par le rail-balise (§10).
- **Locomotive** : reconçue, voir [`decisions-locomotive-v2.md`](./decisions-locomotive-v2.md).

### 10. Identification des rails par RFID et rails-balises
- **Une étiquette NFC `NTAG213` (12–15 mm) scellée dans chaque rail** par pause d'impression, sous le plateau central ; étiquettes « on-metal » pour les rails Funky (bandes d'acier).
- **Fiche autodescriptive** écrite en fabrication (téléphone NFC ou poste d'écriture) : type de rail, angle, action, numéro de série. Reprogrammable par l'application (ex. balise klaxon → arrêt).
- Usages : la locomotive sait sur quoi elle roule (ralentit avant une courbe en mode Fusée, anticipe un aiguillage), l'application peut reconstituer la carte du circuit.
- **Rail-balise** (remplace la tuile d'action) : rail droit de `50 mm` à plateau coloré (rouge = arrêt en gare, jaune = klaxon, bleu = ralentir, vert = demi-tour). La couleur est pour l'enfant, l'étiquette commande la loco (capteur couleur supprimé).
- Coût indicatif à confirmer : `0,10–0,40 $` par étiquette, ~10–25 $ pour un circuit d'environ 70 rails.

### 11. Plan du circuit (calculé par `outils/plan_circuit.py`)
- **Courbe rendue symétrique** : 17,2 mm de droit aux deux bouts (au lieu de 17,2 / 2). Un demi-tour de 4 courbes revient exactement à son abscisse de départ, sans droit d'ajustement. Nouvelle emprise `170,5 × 98,7 mm`.
- **Aiguillage en « Y »** : voie déviée = courbe standard, voie directe `163,3 mm` (portée de la déviée + 6,6 mm pour que les grands côtés tombent sur un multiple de 50 mm).
- **Genres sans adaptateur** : aiguillages en deux variantes — *tronc femelle* (sorties mâles) et *tronc mâle* (sorties femelles) — alternées (HD et BG tronc F, HG et BD tronc M, gare tronc F), et croisement à bras **femelle-femelle** sur une diagonale, **mâle-mâle** sur l'autre. Avec des aiguillages tous identiques, il faudrait 6 adaptateurs F-F / M-M.
- **Toutes les courbes sont la même pièce** : en bout d'ovale elles sont parcourues à l'envers (virage à droite).
- **Rampes** : pièces de 100 mm en plan (pied +6,25, milieu +12,5, tête +6,25 ; pente max 12,5 %). Leurs jonctions tombent entre deux crans de pilier : elles doivent être **autoportantes** (dessous en coin évidé) ; seul le tablier repose sur 2 piliers.
- **Une seule pièce sur mesure** sur la voie principale : un droit d'ajustement de `86,7 mm` sur le grand côté bas (la gare y occupe un aiguillage). Croisement : bras de `87,2 mm` (viaduc 50) ou `54,4 mm` (viaduc 25).
- **Encombrement réel** (fermeture exacte, aucun chevauchement, genres vérifiés) :

| Viaduc | Encombrement | Pièces | Filament | Impression |
| :--- | :--- | :---: | :---: | :---: |
| 50 mm | **1,91 × 1,41 m** | 85 | ~1,55 kg | ~86 h |
| **25 mm (retenu)** | **1,51 × 1,01 m** | 61 | ~1,11 kg | ~62 h |
| sans viaduc | 1,21 × 0,71 m | — | — | — |

  Le viaduc de 50 mm dépasse le tapis de 1,2 × 1,8 m visé : la montée à 12,5 % max demande 500 mm de rampe de chaque côté, et le grand côté doit être allongé d'autant, ce qui écarte aussi les extrémités et allonge les diagonales. **Décision (17 nov. 2026) : viaduc 25 mm**, pour tenir sur le tapis ; il suffit à tester transitions, jonctions sur piliers, montée et descente, et le banc de pente couvre les pentes fortes. Le plan 50 mm reste générable (`--viaduc 50`). Plans : [`plan-circuit-viaduc50.svg`](./plan-circuit-viaduc50.svg), [`plan-circuit-viaduc25.svg`](./plan-circuit-viaduc25.svg) (nomenclatures dans les `.txt` voisins).

### 9. Ordre de travail
1. Socle CadQuery (`cao_commun.py`).
2. Jauge de calibration (gpt-oss) → **première impression**.
3. Refonte des 11 pièces existantes.
4. Plan du circuit vu de dessus.
5. Nouvelles pièces : butoir (gpt-oss), wagon, rampes ×3, aiguillages G/D, croisement, pilier 25 + rehausse, banc de pente, tunnel.
