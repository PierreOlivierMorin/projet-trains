# Décisions de Design V1 — Cahier des charges verrouillé (`/grill-me`)

Ce document consigne les **10 décisions d'architecture produit** validées pour la version V1 avant le lancement du prototypage mécanique, électronique et commercial.

---

### 1. Standard mécanique et compatibilité
- **Écartement des roues (gauge)** : **`25,5 mm`** centre-à-centre (identique au standard universel des trains en bois).
- **Profil de rail** : Rail plastique rigide **100 % propriétaire** (`40 mm` de large × `12 mm` de haut, rainures de `6 mm` de large × `3 mm` de profondeur) optimisé pour l'impression 3D et le futur moulage.
- **Écosystème ouvert (sans violation de PI)** :
  - Notre locomotive peut rouler sur les circuits en bois existants des familles.
  - Chaque kit inclut des **adaptateurs** : rail propriétaire ↔ rail en bois standard, et socles de piliers compatibles gros blocs (`grille 31,8 mm` type DUPLO).

### 2. Jonction des rails (Zéro craque & Stabilité)
- **Système retenu** : **Clip souple auto-centrant (« Snap-Fit ») + languette centrale avec verrouillage vertical 45° (V-ridge/V-groove)**.
- **Avantages** :
  - S'imprime en une seule pièce sans aimants ni vis.
  - Les faces d'appui des rainures se touchent bord à bord (**zéro craque** bloquant les roues).
  - Résiste à la séparation et à la flexion verticale, même posé sur un tapis épais ou surélevé sur des piliers.

### 3. Franchissement des côtes
- **Architecture mécanique** :
  - Pneus souples en **TPU / silicone** sur les roues motrices.
  - **Micro-stries transversales** (`0,8 mm`) moulées/imprimées au fond des rainures des rails en côte.
  - **Pente progressive (`~14 %`)** avec courbes d'entrée/sortie douces (pas de cassure brutale en bas ou en haut de la côte).
- **Assistance électronique** : Mesure d'angle en temps réel par IMU pour compenser automatiquement la charge moteur (PID) en montée et freiner en descente.

### 4. Modes de contrôle (V1 — Hybride 3-en-1)
1. **Autonome / Sans écran (2–5 ans)** : Bouton poussoir / « Push-and-Go » sur le toit de la locomotive + **tuiles d'action colorées** clipsables sur les rails (arrêt en gare, klaxon, ralentissement, demi-tour).
2. **Télécommande physique robuste** : Incluse dans la boîte pour piloter vitesse, direction, phares, klaxon et aiguillage sans téléphone.
3. **Application mobile (BLE)** : En bonus pour les parents et enfants plus grands (contrôle multi-trains, modes de jeu, mise à jour).

### 5. Pièces intelligentes équipées d'un mini-PCB (V1)
1. **La Locomotive**
2. **La Télécommande physique**
3. **L'Aiguillage motorisé intelligent (« Smart Switch »)** : pilotable depuis la télécommande, l'app ou automatiquement par un train à l'approche via radio locale.
*(Les rails standards droits, courbes, côtes et piliers restent 100 % passifs pour maintenir un prix abordable.)*

### 6. Intelligence multi-trains & anti-collision
- **Double couche de sécurité** :
  1. **Capteur laser Time-of-Flight (`VL53L0X` / `VL53L1X`)** à l'avant : freinage adaptatif progressif derrière un train plus lent et arrêt complet avant collision (avec klaxon ludique en face-à-face).
  2. **Réseau direct sans fil `ESP-NOW`** entre locomotives et aiguillages : coordination instantanée (sans routeur Wi-Fi ni téléphone allumé) pour faire basculer un aiguillage motorisé ou réguler le trafic.

### 7. Alimentation et sécurité Amazon
- **Piles standards AAA** (compatibles piles rechargeables NiMH) dans un **compartiment vissé** (vis M3 captive / encastrée).
- **Régulateur Buck-Boost sur le PCB** : maintient une tension stable (ex. `5 V` moteur / `3,3 V` logique) même lorsque les piles faiblissent, afin d'éviter la perte de puissance en côte.
- **Raison stratégique** : Évite les lourdes certifications de transport de batteries au lithium (UN38.3) et simplifie l'entrée sur Amazon pour la V1.

### 8. Conception de la locomotive et attelage
- **Locomotive monobloc au design unique** en V1 (châssis inférieur + coque supérieure assemblée par vis) pour minimiser le nombre de pièces, le temps d'impression 3D et les risques de petites pièces détachables (norme `< 3 ans`).
- **Attelage mécanique à crochet/boucle robuste** : 100 % imprimable en 3D, sans aucun aimant néodyme exposé.

### 9. Architecture du Mini-PCB universel (Son & Lumière)
- **Un seul design de Mini-PCB nu (`~35 × 22 mm`)** partagé entre la locomotive, la télécommande et l'aiguillage (on ne soude que les composants requis pour chaque rôle — *DNP / Do Not Populate*).
- **Effets intégrés** : Phares / voyants **LED RGB (`WS2812B`)** et **haut-parleur / buzzer** (klaxon, bruits de train, signaux de confirmation).

### 10. Stratégie CAO 3D
- **Modèles paramétriques générés par scripts dans [`03-cao-3d/`](../03-cao-3d/guide-impression-et-assemblage-v1.md)** (`generer_prototype_rails.py` et `generer_prototype_locomotive.py`) exportant directement les 11 fichiers `.STL` prêts à imprimer, avec cotes d'engrènement vérifiées sans collision.

### 11. Système « Funky / Anti-Gravité » (Hybride Magnétique + Rail Captif à Crémaillère)
> **Modifiée le 16 nov. 2026** ([`decisions-locomotive-v2.md`](../03-cao-3d/decisions-locomotive-v2.md) §2) : les patins captifs deviennent des **sabots amovibles** fournis avec le pack Cascades (les patins fixes empêchaient de rouler sur les rails standards et en bois).
Pour permettre au train de grimper des pentes à **90°** et de réussir des **loopings à 360°** sans jamais patiner ni décrocher, toutes les locomotives intègrent **de série dès la boîte de base** :
1. **Aimant néodyme N52 (`20 × 10 × 3 mm`) encapsulé/scellé** à l'intérieur du châssis inférieur vissé (placé à `1,2 mm` de la surface du rail : attraction maximale sur les rails équipés d'acier, **zéro aimant exposé** pour la norme `< 3 ans` ASTM F963).
2. **Pignon central d'escalade (`12` dents, `Ø ext = 16,8 mm`, alésage `3,0 mm`)** monté au centre de l'essieu moteur (`z_essieu = 21,0 mm` avec roues `Ø 24,0 mm` / boudin `Ø 27,6 mm`) : garde au sol de **`+0,6 mm`** au-dessus des rails normaux/bois (`12,0 mm`), passe au-dessus du canal central abaissé (`12,4 mm`) des tuiles d'action, et s'engrène de `1,4 mm` dans la **crémaillère centrale (`z = 14,0 mm`)** des rails « Funky ».
3. **Patins de retenue latéraux (« Coaster Hooks »)** sous le châssis qui s'engagent dans les rainures captives à 45° sur les flancs des rails « Funky » (empêchent physiquement la locomotive de tomber, même arrêtée la tête en bas à 180°).
4. **Mode « Turbo Cascade » automatique via l'IMU** : dès que l'accéléromètre détecte une pente `> 35°` ou une inversion (looping), il pousse automatiquement la motorisation à 100 % et déclenche un effet sonore/lumineux spécial.

### 12. Stratégie de gamme pour les rails « Funky » (Looping & Ascension 90°)
- **Boîte de base classique** : ponts et côtes progressives standards (`~14 %`) pour maintenir un coût d'entrée compétitif.
- **Packs d'Extension « Cascades / Anti-Gravité »** : **Looping 360°**, **Montée verticale à 90°** et **Passage tête en bas** vendus séparément en extensions à très forte marge (zéro électronique à l'intérieur : uniquement impression 3D + feuillards d'acier).
