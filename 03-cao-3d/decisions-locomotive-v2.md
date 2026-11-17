# Décisions Locomotive Alpha V2 (`/grill-me`, 16 nov. 2026)

La locomotive V1 ne pouvait pas être portée telle quelle (voir [`decisions-cao-v2.md`](./decisions-cao-v2.md) §8) : patins captifs en collision hors rails Funky, paliers d'essieux en collision avec la coque, transmission moteur absente, boudin sous le fond de rainure. Ce document fixe l'architecture de la locomotive Alpha reconçue.

---

### 1. Une seule locomotive, montable en deux temps
- **Mode châssis-test** : moteur + piles + interrupteur uniquement, pour le banc de pente dès l'impression.
- **Mode Alpha** : ajout des modules électroniques **sans réimpression** (tous les logements sont prévus dès le départ).

### 2. Patins captifs « Coaster Hooks » amovibles *(modifie la décision V1 n°11)*
- Deux **sabots Cascades** vissés sous le châssis, fournis avec le pack d'extension Funky.
- Sans sabots, la locomotive roule sur tous nos rails **et sur les rails en bois** (décision V1 n°1 préservée).

### 3. Motorisation et transmission
- **N20 à réducteur à vis sans fin intégré** (sortie à 90°, arbre Ø 3 en D), **~300 tr/min sous 6 V**, alimenté en 5 V par le buck-boost. Vis sans fin : la loco tient en pente moteur coupé (irréversibilité à vérifier selon le rapport et la charge).
- **Paire de pignons droits** vers **un seul essieu moteur**, celui qui porte le pignon d'escalade. Place réservée pour un renvoi vers le second essieu si le banc de pente montre un manque d'adhérence.
- Logement moteur **paramétrique**, recalé sur le moteur réellement reçu (les cotes varient selon les fournisseurs : bloc ~33 × 12 × 18 mm).

### 4. Vitesses et régulation
- **3 vitesses configurables dans l'application** : Tortue `8 cm/s`, Train `15 cm/s`, Fusée `25 cm/s`.
- Passage automatique en vitesse lente / couple max sur crémaillère (mode Funky).
- **Mesure de vitesse** : aimant scellé dans le moyeu d'une roue de l'**essieu libre** + capteur à effet Hall sur le châssis. La comparaison avec la consigne moteur détecte le **patinage**.

### 5. Roues et essieux
- Roues `Ø 24`, **largeur 3,5 mm**, bande de roulement **bombée**, sans boudin, gorge pour pneu TPU. Raison : en courbe `R = 180` avec un empattement de `46 mm`, chaque essieu est braqué de ~7,3° ; une roue enfoncée de 3 mm dans la rainure occupe alors son épaisseur + ~2,0 mm.
- **Empattement 46 mm** conservé.
- **Roues prisonnières** (ASTM F963) : emmanchées de force sur des tiges `Ø 3` à travers des **paliers fermés** ; jeu de serrage issu de la jauge de calibration.

### 6. Implantation
- **3×AAA couchées au-dessus des roues**, dans la coque ; **trappe de toit vissée** (vis M3 captive).
- Bouton **Push & Go** à l'avant du toit.
- Tout ce qui est lourd en bas : moteur, aimant N52 scellé, lest si nécessaire (à décider d'après le banc de pente).
- Hauteur visée ~`58 mm` (passe dans le tunnel, dégagement `62,5 mm`).

### 7. Coque et capteurs
- Style **vapeur stylisée** : chaudière ronde, cheminée, cabine.
- **ToF (`VL53L0X`) dans la traverse avant**, à ~`z = 20 mm` au-dessus de la base du rail : voit le butoir, l'arrière des wagons et une main posée sur la voie.
- **LED RGB** dans les lanternes.
- **Attelage** : crochet à l'avant, anneau à l'arrière.

### 8. Électronique Alpha
- Modules du commerce sur un **plateau électronique imprimé** vissé dans la coque (une loge + languette par module) ; ce plateau sert de gabarit au futur mini-PCB `35 × 22 mm`.
- **Capteur couleur `APDS-9960` supprimé**, remplacé par un **lecteur RFID 13,56 MHz `PN532` compact** (~`26 × 18 mm` antenne intégrée, ou carte + antenne déportée). Antenne sous le châssis, **éloignée de l'aimant** (le néodyme nickelé perturbe le 13,56 MHz).

### 9. Écarts constatés à la conception du châssis-test
- **Moteur plus lent que prévu** : les N20 à vis sans fin courants tournent à ~40 tr/min (300:1) et au mieux ~200 tr/min (59:1) sous 6 V. La paire d'engrenages **multiplie** donc la vitesse : 20 dents (moteur) → 14 dents (essieu), ×1,43. Moteur à commander : **~150–200 tr/min sous 6 V** (au lieu de ~300).
- **Moteur en hauteur** : l'arbre de sortie doit rester à l'écart du pignon d'escalade et l'engrenage d'essieu ne peut pas dépasser `Ø 16` (sinon il touche le rail). Le réducteur est donc vertical, arbre à `z ≈ 31`, carter du moteur jusqu'à `z ≈ 59`. Le « tout le lourd en bas » (§6) n'est tenu que pour les aimants ; à surveiller sur le banc (basculement en courbe).
- **Deux aimants `N52 20 × 5 × 3`** au lieu d'un `20 × 10 × 3` : la crémaillère Funky (`|y| ≤ 1,6`, `z = 14`) impose un canal central sous le plancher ; un aimant est placé au-dessus de chaque bande d'acier (`|y| ≈ 6,2`), à `1,2 mm` du rail.
- **Attelages relevés** (plaque du crochet à `z = 14,6`) pour passer au-dessus de la crémaillère.
- **Bande de roulement plate à chanfreins** au lieu de bombée : la gorge du pneu, au centre, supprimait le sommet du bombé. Les chanfreins de `0,4 mm` suffisent en courbe (contrôle CadQuery : 3,5 mm passe, 5 mm coince).
- **Support moteur provisoire** : cotes du N20 supposées (`MOTEUR` dans `generer_locomotive.py`) ; seule cette pièce est à régénérer après mesure du moteur reçu.
- **Antenne RFID** : emplacement pas encore réservé dans le châssis-test (pas nécessaire au banc de pente) ; à placer loin des aimants lors de la coque Alpha.

### 10. Ordre de travail
1. **Châssis-test** (châssis, roues 3,5 mm, transmission, logement piles) → *fait* (`generer_locomotive.py`, contrôlé par `outils/controler_locomotive.py`) ; reste à mesurer le moteur reçu et imprimer.
2. Coque vapeur et plateau électronique.
3. Rail-balise et logements d'étiquettes NFC dans tous les rails (voir `decisions-cao-v2.md` §10).
