# Analyse des coûts de production (BOM Électronique + Impression 3D)

Cette analyse chiffre le coût de revient unitaire (**COGS**, en dollars canadiens **CAD**) pour deux volumes réalistes de démarrage :
- **Petite série (100 unités)** : lancement initial / précommandes / fabrication en ferme d'impression 3D.
- **Série moyenne (1 000 unités)** : passage à l'échelle (composants commandés en bobines, sous-traitance PCBA optimisée).

> [!NOTE]
> L'un des leviers d'économie majeurs de votre architecture est l'utilisation d'un **Mini-PCB nu universel unique** (`~35 × 22 mm`, 2 couches) partagé entre la locomotive, la télécommande et l'aiguillage (assemblé selon 3 variantes de peuplement *DNP — Do Not Populate*). Cela divise par trois les frais de setup PCBA et simplifie l'inventaire.

---

## 1. Coût du Mini-PCB Universel & Électronique / Mécanique par module

### 1A. Locomotive intelligente complète (Électronique + Motorisation)

| Sous-système / Composant | Rôle technique | Coût 100 u (CAD) | Coût 1 000 u (CAD) |
| :--- | :--- | :---: | :---: |
| **Module `ESP32-C3-MINI-1` (pré-certifié FCC/ISED)** | Microcontrôleur + BLE + `ESP-NOW` | 2,40 \$ | 1,85 \$ |
| **Régulateur Buck-Boost (`TPS63020` ou équiv.)** | Tension constante `5 V` depuis 3×AAA (zéro perte en côte) | 1,10 \$ | 0,70 \$ |
| **Pont en H moteur (`DRV8833`)** | Contrôle vitesse PWM + freinage actif en descente | 0,65 \$ | 0,40 \$ |
| **Capteur laser ToF (`VL53L0X`)** | Détection d'obstacles et anti-collision avant | 2,20 \$ | 1,50 \$ |
| **IMU 6 axes (`LSM6DS3` / `MPU-6050`)** | Mesure de pente en temps réel (boucle PID en côte) | 1,10 \$ | 0,75 \$ |
| **Capteur couleur (`APDS-9960` / `TCS34725`)** | Lecture des tuiles d'action clipsées sur les rails | 1,30 \$ | 0,85 \$ |
| **Audio + Éclairage + Interface** | Mini-ampli + haut-parleur `20 mm`/buzzer + 2× `WS2812B` + bouton toit | 1,20 \$ | 0,80 \$ |
| **PCB nu + assemblage CMS + passifs + contacts AAA** | Fabrication carte, soudures, ressorts de piles | 2,30 \$ | 1,15 \$ |
| **Motorisation & quincaillerie** | Micro-moteur métal `N20 6V` + engrenage + 4 pneus TPU/silicone + vis M3 | 3,50 \$ | 2,20 \$ |
| **Kit « Anti-Gravité » de série** | Aimant néodyme N52 (`20 × 10 × 3 mm`) scellé + pignon central d'escalade | 0,85 \$ | 0,50 \$ |
| **Sous-total Électronique & Mécanique Locomotive** | | **16,60 \$** | **10,70 \$** |

### 1B. Télécommande physique robuste (Variante DNP du même PCB)

- Peuplée uniquement avec : `ESP32-C3-MINI-1`, régulateur, 4 boutons / levier robuste, 1 LED RGB `WS2812B`, buzzer, contacts 2×AAA, vis M3.
- **Sous-total Électronique Télécommande** : **`~5,80 \$ CAD`** (à 100 u) | **`~3,75 \$ CAD`** (à 1 000 u).

### 1C. Aiguillage motorisé intelligent — *Smart Switch* (Variante DNP du même PCB)

- Peuplée uniquement avec : `ESP32-C3-MINI-1`, régulateur, micro-servo engrenages métal `SG90`, 1 bouton poussoir, 1 LED bicolore, contacts piles AAA, vis M3.
- **Sous-total Électronique & Servo Aiguillage** : **`~7,40 \$ CAD`** (à 100 u) | **`~4,80 \$ CAD`** (à 1 000 u).

---

## 2. Coût d'impression 3D par pièce

Hypothèses réalistes pour une imprimante CoreXY rapide moderne (type Bambu Lab A1 / P1S) :
- **Filament PETG ou PLA+ qualité jouet** : `~20 \$ CAD / kg` (`0,02 \$ / g`, déchets/supports minimes inclus).
- **Électricité + usure/amortissement machine** : `~0,25 \$ CAD / heure` d'impression.

| Pièce imprimée en 3D | Poids estimé | Temps d'impression | Coût matière | Coût total (matière + machine) |
| :--- | :---: | :---: | :---: | :---: |
| **Coque + Châssis Locomotive monobloc** | `85 g` | `2 h 15` | `1,70 \$` | **`2,25 \$`** |
| **Boîtier Télécommande** | `55 g` | `1 h 30` | `1,10 \$` | **`1,50 \$`** |
| **Aiguillage motorisé complet (corps + lame + tringlerie)** *(V2 manuel mesuré : ~34 g corps + lame + levier ; boîtier servo latéral à concevoir)* | `70 g` | `1 h 50` | `1,40 \$` | **`1,85 \$`** |
| **Rail droit `150 mm` avec clip Snap-Fit** | `28 g` | `0 h 35` | `0,56 \$` | **`0,70 \$`** |
| **Rail courbe (1/8 de cercle) avec clip Snap-Fit** | `30 g` | `0 h 40` | `0,60 \$` | **`0,75 \$`** |
| **Rail en côte micro-strié** | `42 g` | `0 h 55` | `0,84 \$` | **`1,05 \$`** |
| **Pilier verrouillable (socle gros blocs `31,8 mm`)** | `25 g` | `0 h 30` | `0,50 \$` | **`0,62 \$`** |
| **Lot de 2 Adaptateurs (Bois + Gros blocs) + 8 Tuiles d'action** | `45 g` | `0 h 50` | `0,90 \$` | **`1,10 \$`** |

---

## 3. Coût de revient complet (COGS) par pièce maîtresse

En additionnant l'électronique/mécanique et le boîtier imprimé en 3D :

| Pièce maîtresse assemblée | Coût complet (100 unités) | Coût complet (1 000 unités) |
| :--- | :---: | :---: |
| **1 Locomotive intelligente complète** *(incl. aimant + pignon de série)* | **`18,85 \$ CAD`** | **`12,95 \$ CAD`** |
| **1 Télécommande physique robuste** | **`7,30 \$ CAD`** | **`5,25 \$ CAD`** |
| **1 Aiguillage motorisé sans fil** | **`9,25 \$ CAD`** | **`6,65 \$ CAD`** |

*(Note : le temps de main-d'œuvre d'assemblage interne/externe n'est pas inclus dans ces coûts pièces, ni les frais d'expédition/Amazon FBA.)*

---

## 4. Simulation de 2 configurations de Kits pour aider à définir l'offre

Les simulations ci-dessous incluent **`4,50 \$ CAD`** pour la boîte carton imprimée, le calage et le manuel illustré (`~6,00 \$ CAD` en grand format).

### Configuration A — « Kit Découverte » *(1 Locomotive)*
Contenu simulé :
- 1 Locomotive intelligente (`18,85 \$` / `12,95 \$`)
- 1 Télécommande robuste (`7,30 \$` / `5,25 \$`)
- 1 Aiguillage motorisé (`9,25 \$` / `6,65 \$`)
- 18 rails (`8 courbes` + `6 droits` + `4 côtes` = `14,40 \$` en 3D)
- 4 piliers verrouillables (`2,48 \$`)
- 1 lot Adaptateurs + 8 Tuiles d'action (`1,10 \$`)
- Boîte + manuel (`4,50 \$`)

| Indicateur | Petite série (100 u, 100 % 3D) | Série 1 000 u *(100 % 3D)* |
| :--- | :---: | :---: |
| **Coût de fabrication total (COGS)** | **`~57,88 \$ CAD`** | **`~42,00 \$ CAD`** *(avec optimisation rails/boîte)* |
| **Temps d'impression 3D total / boîte** | `~19 heures` | *(~1 boîte / jour / imprimante ; fortement réduit si rails moulés)* |
| **Marge brute indicative à 149 \$ – 169 \$ CAD** | `~61 % – 66 %` | `~72 % – 75 %` |

---

### Configuration B — « Kit Duo Anti-Collision » *(2 Locomotives)*
Contenu simulé :
- 2 Locomotives intelligentes (`37,70 \$` / `25,90 \$`)
- 2 Télécommandes robustes (`14,60 \$` / `10,50 \$`)
- 2 Aiguillages motorisés (`18,50 \$` / `13,30 \$`)
- 28 rails (`12 courbes` + `10 droits` + `6 côtes` = `22,30 \$` en 3D)
- 8 piliers verrouillables (`4,96 \$`)
- 1 lot Adaptateurs + 8 Tuiles d'action (`1,10 \$`)
- Boîte grand format + manuel (`6,00 \$`)

| Indicateur | Petite série (100 u, 100 % 3D) | Série 1 000 u *(100 % 3D)* |
| :--- | :---: | :---: |
| **Coût de fabrication total (COGS)** | **`~105,16 \$ CAD`** | **`~75,00 \$ CAD`** |
| **Temps d'impression 3D total / boîte** | `~31 heures` | *(~1,3 jour / imprimante ; idéal pour passer les rails en moulage)* |
| **Marge brute indicative à 249 \$ – 279 \$ CAD** | `~58 % – 62 %` | `~70 % – 73 %` |

---

## 5. Coût et rentabilité des Packs d'Extension « Cascades / Funky » (Looping 360° & Mur 90°)

Parce que toutes les locomotives sortent de l'usine déjà prêtes pour l'anti-gravité (aimant scellé + pignon central + patins en C + mode Turbo IMU), ces extensions ne contiennent **aucune électronique** : c'est le levier de marge le plus rentable de l'entreprise.

### Pack Extension 1 — « Looping 360° Anti-Gravité »
Contenu : `8` segments courbes verticaux à crémaillère + rainures captives en C + feuillards d'acier `10 mm` (ou double bande latérale) + `2` bases stabilisatrices.
- **Impression 3D (`~320 g` filament + ~8 h machine)** : `~8,40 \$ CAD`
- **Feuillards d'acier magnétique** : `~1,80 \$ CAD`
- **Boîte + manuel** : `~2,50 \$ CAD`
- **Coût de revient total (COGS)** : **`~12,70 \$ CAD`**
- **Prix de vente cible** : **`49,99 \$ – 59,99 \$ CAD`** → **Marge brute : `~75 % à 78 %`**

### Pack Extension 2 — « Ascension Verticale 90° (Tour / Bureau) »
Contenu : `2` courbes de transition à 90° + `4` rails verticaux à crémaillère/acier + attaches de pilier vertical.
- **Impression 3D (`~260 g` filament + ~6 h 30 machine)** : `~6,80 \$ CAD`
- **Feuillards d'acier magnétique** : `~1,40 \$ CAD`
- **Boîte + manuel** : `~2,50 \$ CAD`
- **Coût de revient total (COGS)** : **`~10,70 \$ CAD`**
- **Prix de vente cible** : **`39,99 \$ – 49,99 \$ CAD`** → **Marge brute : `~73 % à 78 %`**

---

### Conclusion stratégique sur les coûts
1. **Un ensemble complet à 249–279 \$ CAD avec 2 locomotives intelligentes** reste **~40 % moins cher** que les ensembles basiques à **450 \$** vus sur Amazon, tout en offrant anti-collision laser, régulation en côte, aiguillages sans fil et compatibilité cascades !
2. **Des extensions « Cascades » à ~75 %+ de marge sans électronique** permettent d'augmenter le panier moyen après Noël ou aux anniversaires, tout en gardant la boîte de base à un prix d'entrée très attractif.
3. **Le goulot d'étranglement à surveiller** n'est pas l'électronique (`~13 \$` à `19 \$` par locomotive), mais le **temps d'impression des rails simples** (~12 à 18 h par boîte). Dès le palier de quelques centaines de boîtes, mouler uniquement le **rail droit** et le **rail courbe** libérera massivement la capacité de vos imprimantes pour les pièces intelligentes et les packs « Cascades ».
