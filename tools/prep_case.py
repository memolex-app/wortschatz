"""Contrôle (audit n° 9) : chaque préposition ou postposition des listes doit figurer dans la table des cas de l'appli
(rubrique cases.prep de data/<L>/langue.json), sinon l'appli ne peut ni afficher ni faire deviner le cas.
Ne concerne que les langues à cas (allemand).
Usage : MX_PAIR=de-fr python3 prep_case.py
"""
import json, os, re
from common import load, shown, REPO


def table(repo=REPO):
    """Prépositions connues : rubrique « cases.prep » de la description de la langue (data/<L>/langue.json)."""
    from common import PAIR
    L = PAIR.split('-')[0]
    d = json.load(open(os.path.join(repo, 'data', L, 'langue.json'), encoding='utf-8'))
    return set((d.get('cases') or {}).get('prep', {}))


def run(repo=REPO):
    cards, _, _ = load()
    known = table()
    return [c for c in cards if c['nat'] in ('prep', 'postp') and c['w'] not in known]


if __name__ == '__main__':
    r = run()
    print(f'{len(r)} prépositions absentes de la table des cas')
    for c in r:
        print(f"{c['i']}|{c['lv']}|{shown(c)} = {c['fr']}")
