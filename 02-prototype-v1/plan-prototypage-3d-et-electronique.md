# Plan de Prototypage V1 : Impression 3D, Électronique & Sécurité

L'accès immédiat à plusieurs imprimantes 3D permet de valider **la mécanique avant l'électronique**, à très faible coût, avant d'investir dans une imprimante personnelle pour la pré-série ou dans des PCB sur mesure.

---

## Étape 1 : Le « Test Zéro » 100 % mécanique (Budget : < 5 \$ de filament PLA/PETG)

Avant d'écrire une ligne de code ou de dessiner un circuit imprimé, l'objectif est de prouver que les trois frustrations physiques observées (instabilité, craques, manque de puissance en côte) sont résolues.

### Les 4 pièces à imprimer pour valider la mécanique
1. **Deux segments de rail droit court (`100 mm`)**
   - Avec système d'alignement sans « craque » : goupilles coniques d'auto-alignement + clip de verrouillage positif empêchant toute flexion verticale ou séparation sur un tapis.
2. **Un rail en pente**
   - Intégrant des micro-stries transversales sur la bande de roulement pour maximiser l'adhérence en montée.
3. **Un pilier verrouillable**
   - Se clipse directement **sous la jonction** entre deux rails afin de transformer chaque point de raccordement en appui rigide indéformable.
4. **Un châssis-test de locomotive (sans intelligence)**
   - Simple plateforme imprimée accueillant 4 roues (écartement `25,5 mm`), un micro-moteur à engrenages `N20` et un boîtier de pile basique, afin de tester avec les neveux (2–4 ans) le passage des jonctions, l'escalade de la pente et la robustesse aux chutes.

---

## Étape 2 : Le Prototype Électronique V1 sur modules (Budget : ~25–35 \$)

Une fois la mécanique validée, on assemble une première locomotive « intelligente » avec des modules du commerce faciles à câbler (sans concevoir de PCB sur mesure tout de suite).

### Liste des composants (BOM Prototype Alpha)

| Fonction | Composant recommandé | Pourquoi ce choix |
| :--- | :--- | :--- |
| **Microcontrôleur & Radio** | `Seeed Studio XIAO ESP32C3` *(ou `ESP32-S3`)* | Format minuscule (`21 × 17,5 mm`), Wi-Fi + Bluetooth LE + `ESP-NOW` (communication directe entre locomotives) et **chargeur de batterie LiPo intégré**. |
| **Contrôle moteur (Pont en H)** | `DRV8833` ou `TB6612FNG` | Faible chute de tension (contrairement aux vieux `L298N`), très compact, gère le freinage actif en descente. |
| **Motorisation** | Micro-moteur métal `N20 6V` (`150 RPM` ou `200 RPM`) | Très fort couple grâce au réducteur métallique pour grimper les côtes sans caler. |
| **Anti-collision avant** | `VL53L0X` ou `VL53L1X` (Time-of-Flight laser) | Mesure la distance exacte devant le train (jusqu'à 50–200 cm) ; permet de ralentir et s'arrêter avant de percuter un autre train ou une main. |
| **Détection de côte (IMU)** | `MPU-6050` ou `LSM6DS3` | Mesure l'angle d'inclinaison en temps réel pour booster la puissance en montée et freiner en descente (boucle PID). |
| **Lecture de balises sur rail** | `APDS-9960` (couleur/proximité) ou capteur Hall `A3144` | Permet de déclencher des actions automatiques (klaxon, arrêt en gare, changement de vitesse) sans écran, via des tuiles colorées ou aimants noyés dans des blocs spéciaux. |

---

## Étape 3 : Critères de sécurité non négociables (Tranche 2–4 ans)

Parce que les premiers testeurs ont entre **2 et 4 ans**, le prototype doit respecter dès le jour 1 les exigences critiques de la norme jouet **ASTM F963** (notamment pour les moins de 3 ans) :

1. **Aucune petite pièce détachable**
   - Toute pièce amovible ou susceptible de se détacher doit dépasser le gabarit du cylindre d'étouffement (`31,7 mm` de diamètre × `57,1 mm` de long).
2. **Châssis monobloc verrouillé par vis**
   - Aucun accès aux composants électroniques ou à la batterie par simple clipsage : utiliser des vis M3 encastrées (ou vis prisonnières avec inserts filetés laiton) pour fermer la coque.
3. **Roues et pneus captifs**
   - Les pneus en TPU (caoutchouc imprimable) doivent être soit imprimés en bi-matière, soit bloqués mécaniquement dans une gorge profonde de la jante pour qu'un enfant ne puisse pas les arracher avec les dents ou les doigts.
4. **Aucun aimant néodyme exposé**
   - Si des attelages magnétiques sont utilisés entre wagons, les aimants doivent être **totalement encapsulés à l'intérieur du plastique** (en mettant l'impression en pause pour insérer l'aimant puis en imprimant par-dessus, ou scellés dans un logement fermé par ultrasons/vis).
5. **Protection batterie**
   - Utiliser exclusivement une cellule équipée d'un circuit de protection (BMS/PCM contre court-circuit et surcharge), idéalement logée dans un compartiment isolé thermiquement et mécaniquement.
