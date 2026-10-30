"""Contrôle des chunks « À retenir » : la traduction du chunk doit contenir un sens de la carte (racine ou lemme) ;
le mot appris est marqué entre astérisques ; longueur maximale (A1-A2 : 3 mots, B1-B2 : 4, C1-C2 : 5 — mots italiens hors astérisques).
Usage : python3 chunks_check.py [--sens]"""
import re, snowballstemmer
from common import load, shown, fr_senses
ST = snowballstemmer.stemmer('french')
STOP = {'de', 'du', 'des', 'd', 'à', 'au', 'aux', 'en', 'se', 's', 'ne', 'pas', 'qn', 'qch', 'un', 'une', 'le', 'la', 'les', 'l', 'ce', 'cette', 'ces', 'y', 'n'}
def words(s): return [w for w in re.findall(r"[\wœ]+", s.lower().replace('’', "'")) if w not in STOP]
MAXW = {'A1': 3, 'A2': 3, 'B1': 4, 'B2': 4, 'C1': 5, 'C2': 5}
SENS = '--sens' in __import__('sys').argv   # contrôle de sens : informatif (les chunks sont traduits librement, ~15 % de fausses alertes)
def run(repo='..'):
    cards, _, ch = load(repo)
    seen = {}
    for c in cards: seen.setdefault(c['key'], []).append(c)
    bad = []
    for w, (it, fr) in ch.items():
        cs = seen.get(w)
        if not cs: bad.append((w, 'chunk sans carte', it, fr)); continue
        if '*' not in it: bad.append((w, 'mot non marqué', it, fr))
        n = len(re.findall(r"[\wàèéìòù']+", it.replace('*', '')))
        if n > max(MAXW[c['lv']] for c in cs): bad.append((w, f'trop long ({n} mots)', it, fr))
        stems = {ST.stemWord(x) for x in words(fr)} | set(words(fr))
        ok = False
        for c in cs:
            for g in fr_senses(c['fr']):
                gw = words(g)
                if gw and all(x in stems or ST.stemWord(x) in stems for x in gw): ok = True
        if not ok and SENS: bad.append((w, 'aucun sens de la carte dans la traduction du chunk', it, fr + '   <-- ' + ' / '.join(c['fr'] for c in cs)))
    for c in cards:
        if c['key'] not in ch: bad.append((c['w'], 'carte sans chunk', '', ''))
    return bad
if __name__ == '__main__':
    r = run()
    print(len(r), 'chunks à examiner')
    for w, why, it, fr in r: print(f'{w}|{why}|{it}|{fr}')
