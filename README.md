# Projet Trains — Système Ferroviaire Modulaire & Intelligent

## Vision du produit
Concevoir et commercialiser un **système de train jouet modulaire, robuste, motorisé et intelligent**, pensé pour corriger les défauts majeurs des ensembles existants (même haut de gamme autour de 450 \$) :
- **Stabilité mécanique sans faille** : rails et piliers à verrouillage positif (ne se défont pas sur un tapis et ne basculent pas).
- **Passage des joints fluide** : aucun écart (« craque ») qui freine ou bloque les roues.
- **Puissance et contrôle en pente** : détection d'inclinaison (IMU) et régulation automatique du moteur (PID) pour conserver une vitesse constante en montée comme en descente.
- **Système « Funky / Anti-Gravité »** : locomotive prête de série (aimant néodyme scellé + pignon central + patins captifs) pour grimper à 90° et franchir des loopings à 360° sur les rails d'extension « Cascades ».
- **Sécurité anti-collision** : détection d'obstacles et d'autres locomotives par capteur laser (Time-of-Flight) et communication sans fil directe entre trains.
- **Évolutivité et contrôle** : utilisable sans écran (boutons simples / tuiles d'action sur rail), avec télécommande physique ou via application mobile.

---

## Cible et horizon temporel

| Élément | Détail |
| :--- | :--- |
| **Alpha-testeurs** | Neveux (2–4 ans aujourd'hui ; 3–6 ans pendant la phase de tests intensifs) |
| **Cible commerciale** | Enfants de **3 à 8 ans** (et parents cherchant un jouet STEM durable et évolutif) |
| **Horizon V1 (Lancement limité)** | **Noël 2027** (précommandes / Kickstarter ou petite série produite en impression 3D) |
| **Horizon V2 (Production à l'échelle)** | **Noël 2028** (distribution e-commerce / Amazon, moules pour rails de base) |

---

## Structure du projet

- [`01-etude-de-marche/`](./01-etude-de-marche/formats-et-propriete-intellectuelle.md) : Analyse des formats concurrents, dimensions standards, propriété intellectuelle et positionnement produit.
- `02-prototype-v1/` :
  - [`decisions-design-v1.md`](./02-prototype-v1/decisions-design-v1.md) : Cahier des charges verrouillé (les 12 décisions de design issues de l'architecture produit).
  - [`plan-prototypage-3d-et-electronique.md`](./02-prototype-v1/plan-prototypage-3d-et-electronique.md) : Plan de prototypage rapide (Test Zéro mécanique, architecture électronique modulaire et critères de sécurité 2–4 ans).
- `03-cao-3d/` :
  - [`visualiseur-assemblage.html`](./03-cao-3d/visualiseur-assemblage.html) : Inspecteur WebGL 3D autonome embarquant les 11 vrais fichiers `.STL` (assemblage, vue éclatée, coupes X/Y/Z, filaire).
  - [`plan-developpement-stl-benchmark.md`](./03-cao-3d/plan-developpement-stl-benchmark.md) : Plan de développement STL en 5 niveaux (prompts + contrat d'interface + grille d'évaluation) pour tester un modèle local.
  - [`guide-impression-et-assemblage-v1.md`](./03-cao-3d/guide-impression-et-assemblage-v1.md) : Inventaire des 11 fichiers `.STL`, cotes d'engrènement vérifiées, paramètres de tranchage et protocole de test.
  - [`verifier_stl.py`](./03-cao-3d/verifier_stl.py) : Validateur topologique automatique (`--update-viewer` pour rafraîchir le visualiseur).
  - [`generer_prototype_rails.py`](./03-cao-3d/generer_prototype_rails.py) : Génère les 7 pièces de circuit (`rail_droit_100mm_snapfit.stl`, `rail_courbe_45deg_snapfit.stl`, `rail_cote_100mm_strie.stl`, `adaptateur_rail_bois.stl`, `pilier_verrouillable_duplo.stl`, `tuile_action_clipsable.stl`, `rail_funky_cremaillere_captif.stl`).
  - [`generer_prototype_locomotive.py`](./03-cao-3d/generer_prototype_locomotive.py) : Génère les 4 pièces de la locomotive V1 (`loco_chassis_inferieur.stl`, `loco_coque_superieure_monobloc.stl`, `loco_roue_25_5mm.stl`, `loco_pignon_central_essieu.stl`).
  - [`generer_visualiseur_html.py`](./03-cao-3d/generer_visualiseur_html.py) : Reconstruit `visualiseur-assemblage.html` à partir des `.STL` générés.
- `04-electronique-firmware/` *(à venir)* : Schémas électroniques, routage du mini-PCB sur mesure et firmware embarqué.
- `05-business-et-certifications/` :
  - [`analyse-couts-de-production-bom.md`](./05-business-et-certifications/analyse-couts-de-production-bom.md) : Nomenclature granulaire (BOM électronique + impression 3D), coûts complets (COGS) pour 100 et 1 000 unités, et simulation de 2 configurations de kits.

---

## Feuille de route en 5 phases

1. **Phase 1 — Mécanique & Rails 3D (Mois 1 à 3)**
   - Conception et impression 3D du profil de rail propriétaire, du joint sans craque, des piliers verrouillables et des pièces d'adaptation.
   - Validation de la motricité en pente sur un châssis test simple.
2. **Phase 2 — Locomotive Alpha sur modules standards (Mois 4 à 6)**
   - Intégration de l'électronique hors PCB sur mesure (`XIAO ESP32C3`, capteur ToF `VL53L0X`, IMU, pont en H, moteur `N20`).
   - Développement du firmware de base : anti-collision, régulation PID en côte, contrôle BLE/ESP-NOW.
3. **Phase 3 — Mini-PCB sur mesure & Bêta-tests neveux (Mois 7 à 12)**
   - Conception d'un mini-PCB unique intégrant microcontrôleur pré-certifié, capteurs et gestion batterie/USB-C.
   - Tests d'endurance réels avec les neveux (chutes, tapis, assemblage par petites mains) et itérations sur l'ergonomie.
4. **Phase 4 — Pré-série & Certifications (Mois 13 à 18)**
   - Optimisation des coûts de fabrication (ferme d'impression 3D vs moulage des rails droits/courbes).
   - Préparation des dossiers de conformité sécurité jouets et radio.
5. **Phase 5 — Lancement commercial (Mois 19 à 24)**
   - Finalisation du packaging, de l'application mobile / télécommande, campagne de lancement (Noël 2027) puis déploiement Amazon (Noël 2028).
