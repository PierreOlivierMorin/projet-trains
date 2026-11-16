#!/usr/bin/env python3
"""Délègue l'écriture d'un générateur CadQuery à un modèle local (LM Studio ou Ollama).

Boucle : contrat d'interface + tâche -> script Python -> exécution -> verifier_stl.py ->
en cas d'échec, l'erreur est renvoyée au modèle, jusqu'à réussite ou `--essais` atteints.
Chaque essai (prompt, réponse, sortie) est journalisé dans `--journal`.

Exemple :
  python3 outils/deleguer_modele_local.py --tache taches/jauge.txt \
      --script gen_jauge_calibration.py --stl jauge_calibration_tolerances

Serveurs compatibles OpenAI : LM Studio http://localhost:1234/v1 (défaut),
Ollama http://localhost:11434/v1.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CAO = RACINE / "03-cao-3d"
PYTHON_CAO = RACINE / ".venv" / "bin" / "python"


def appeler(url: str, modele: str, messages: list[dict], max_tokens: int) -> tuple[str, dict]:
    corps = json.dumps(
        {"model": modele, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}
    ).encode()
    req = urllib.request.Request(
        f"{url}/chat/completions", data=corps, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"] or "", d.get("usage", {})


def extraire_code(texte: str) -> str | None:
    blocs = re.findall(r"```(?:python|py)?\s*\n(.*?)```", texte, re.S)
    return max(blocs, key=len) if blocs else None


def executer(cmd: list[str], timeout: int) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=RACINE, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return 1, f"Délai dépassé ({timeout} s) : le script est trop lent ou boucle."


def queue(texte: str, n: int = 40) -> str:
    return "\n".join(texte.strip().splitlines()[-n:])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tache", required=True, help="Fichier texte décrivant la pièce")
    ap.add_argument("--script", required=True, help="Nom du script à écrire dans 03-cao-3d/")
    ap.add_argument("--stl", required=True, nargs="+", help="Nom(s) des STL attendus (sans extension)")
    ap.add_argument("--contrat", default=str(CAO / "contrat-interface-cadquery.txt"))
    ap.add_argument("--url", default="http://localhost:1234/v1")
    ap.add_argument("--modele", default="openai/gpt-oss-20b")
    ap.add_argument("--essais", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--journal", required=True, help="Dossier où journaliser chaque essai")
    ap.add_argument(
        "--controle",
        help="Script de contrôle fonctionnel (lancé avec .venv/bin/python) après verifier_stl.py ; "
        "ses échecs sont renvoyés au modèle",
    )
    args = ap.parse_args()

    journal = Path(args.journal)
    journal.mkdir(parents=True, exist_ok=True)
    messages = [
        {"role": "system", "content": Path(args.contrat).read_text(encoding="utf-8")},
        {"role": "user", "content": Path(args.tache).read_text(encoding="utf-8")},
    ]
    script = CAO / args.script

    for essai in range(1, args.essais + 1):
        t0 = time.time()
        reponse, usage = appeler(args.url, args.modele, messages, args.max_tokens)
        duree = time.time() - t0
        (journal / f"essai{essai}_reponse.md").write_text(reponse, encoding="utf-8")
        code = extraire_code(reponse)
        print(f"--- Essai {essai} : réponse en {duree:.0f} s, {usage.get('completion_tokens', '?')} jetons")

        if code is None:
            retour = "Ta réponse ne contient pas de bloc ```python. Renvoie le script complet dans un seul bloc ```python."
            statut = "pas de code"
        else:
            script.write_text(code, encoding="utf-8")
            rc, sortie = executer([str(PYTHON_CAO), str(script)], timeout=300)
            if rc != 0:
                statut = "erreur d'exécution"
                retour = f"Le script a échoué à l'exécution :\n```\n{queue(sortie)}\n```\nCorrige-le et renvoie le script complet."
            else:
                stls = [str(CAO / "stl" / f"{n}.stl") for n in args.stl]
                rc, sortie_v = executer([sys.executable, str(CAO / "verifier_stl.py"), *stls], timeout=120)
                sortie += "\n" + sortie_v
                if rc == 0 and args.controle:
                    rc, sortie_c = executer([str(PYTHON_CAO), args.controle], timeout=300)
                    sortie_v += "\n" + sortie_c
                    if rc != 0:
                        statut = "contrôle fonctionnel"
                        lignes = [
                            l for l in sortie_c.splitlines() if "ÉCHEC" in l or "INFO" in l or "Error" in l
                        ]
                        retour = (
                            "Le STL est étanche mais le contrôle fonctionnel de la pièce échoue :\n```\n"
                            + "\n".join(lignes or [queue(sortie_c)])
                            + "\n```\nRelis la spécification, corrige le script et renvoie-le complet."
                        )
                        (journal / f"essai{essai}_sortie.txt").write_text(retour, encoding="utf-8")
                        print(f"    {statut}\n{queue(retour, 12)}")
                        messages += [
                            {"role": "assistant", "content": reponse},
                            {"role": "user", "content": retour},
                        ]
                        continue
                if rc == 0:
                    (journal / f"essai{essai}_sortie.txt").write_text(sortie, encoding="utf-8")
                    print(sortie_v)
                    print(f"[RÉUSSI] en {essai} essai(s). Script : {script}")
                    return 0
                statut = "STL invalide"
                retour = f"Le script s'exécute mais le contrôle STL échoue :\n```\n{queue(sortie)}\n```\nCorrige-le et renvoie le script complet."
        (journal / f"essai{essai}_sortie.txt").write_text(retour, encoding="utf-8")
        print(f"    {statut}\n{queue(retour, 12)}")
        messages += [{"role": "assistant", "content": reponse}, {"role": "user", "content": retour}]

    print(f"[ÉCHEC] après {args.essais} essais.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
