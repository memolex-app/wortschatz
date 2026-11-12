"""Dictionnaire provisoire d'une paire en essai : dict-<L>-<U>.json construit à partir des listes de la paire.

Le dictionnaire complet (dict-de-fr.json, 46 029 mots) vient d'une source externe allemand-français et n'existe pas
pour les autres langues de l'utilisateur. En attendant, une paire en essai reçoit un dictionnaire limité aux mots déjà
traduits de ses listes (comme le dictionnaire italien) : mot, nature, genre, pluriel et traduction relue.
Genre, pluriel et fréquence d'usage (classement des résultats, niveau estimé) sont repris de l'entrée correspondante
de dict-<L>-fr.json quand elle existe ; pas de définition.
Usage : python3 tools/dict_from_lists.py de en [--check]
"""
import json, os, sys
from mxdata import ROOT, dump

GENDER = {'der': 'm', 'die': 'f', 'das': 'n'}


def build(L, U):
    lists = json.load(open(os.path.join(ROOT, f'lists-{L}-{U}.json'), encoding='utf-8'))
    ref = {}
    p = os.path.join(ROOT, f'dict-{L}-fr.json')
    if os.path.exists(p):
        for e in json.load(open(p, encoding='utf-8')):
            ref.setdefault((e[0], e[1]), e)
    out = []
    for r in lists:
        lv, w, pos, art, pl, tr = r[:6]
        p1 = pos.split(',')[0]
        e = ref.get((w, p1))
        g = GENDER.get(art, e[2] if e else '') if p1 == 'n' else ''
        z = e[5] if e and len(e) > 5 else 50
        out.append([w, p1, g, pl if pl else (e[3] if e and p1 == 'n' else ''), [[tr, '']], z])
    out.sort(key=lambda e: (e[0].lower(), e[0]))
    return out


if __name__ == '__main__':
    L, U = sys.argv[1], sys.argv[2]
    path = os.path.join(ROOT, f'dict-{L}-{U}.json')
    new = dump(build(L, U)).encode('utf-8')
    if '--check' in sys.argv:
        same = os.path.exists(path) and open(path, 'rb').read() == new
        print(f'dict-{L}-{U}.json : {"identique" if same else "DIFFÉRENT"}'); sys.exit(0 if same else 1)
    open(path, 'wb').write(new); print(f'dict-{L}-{U}.json écrit ({len(json.loads(new))} mots)')
