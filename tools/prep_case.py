"""Contrôle (audit n° 9) : chaque préposition ou postposition des listes doit figurer dans la table des cas de l'appli
(PREP_CASE dans index.html), sinon l'appli ne peut ni afficher ni faire deviner le cas.
Ne concerne que les langues à cas (allemand).
Usage : MX_PAIR=de-fr python3 prep_case.py
"""
import os, re
from common import load, shown, REPO


def table(repo=REPO):
    src = open(os.path.join(repo, 'index.html'), encoding='utf-8').read()
    body = re.search(r'const PREP_CASE = \{(.*?)\n\};', src, re.S).group(1)
    return set(re.findall(r"""(?:^|[,{\s])'?([^\s,:'{}]+)'?\s*:""", body))


def run(repo=REPO):
    cards, _, _ = load()
    known = table()
    return [c for c in cards if c['nat'] in ('prep', 'postp') and c['w'] not in known]


if __name__ == '__main__':
    r = run()
    print(f'{len(r)} prépositions absentes de la table des cas')
    for c in r:
        print(f"{c['i']}|{c['lv']}|{shown(c)} = {c['fr']}")
