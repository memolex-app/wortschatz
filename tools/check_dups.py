"""Contrôle des traductions identiques et des cartes ambiguës (reconstitué à partir de procedure-controle.md, § 1 ter et 4.4-4.5).
 - doublon : deux cartes de même nature avec exactement la même traduction (article ignoré, nuance comprise) ;
 - ambiguë : carte SANS nuance dont toutes les traductions (sans article) figurent parmi celles d'une autre carte de même nature.
Usage : python3 check_dups.py     -> doit afficher 0 et 0
"""
import re, collections
import os
from common import load, shown, strip_note, PAIR
# exceptions vérifiées à la main (une clé de carte par ligne, # = commentaire) : ignore_check_dups_<paire>.txt
def ignored_keys():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'ignore_check_dups_{PAIR}.txt')
    return {l.split('#')[0].strip() for l in open(p, encoding='utf-8')} - {''} if os.path.exists(p) else set()
from common import user_art_re
ART = user_art_re()          # articles de la langue de l'utilisateur (français : le, la, les, un, une, des, l')
def norm_full(s):
    return [ART.sub('', p.strip()).lower() for p in re.split(r'[;,](?![^(]*\))', s) if p.strip()]
def key_nat(c): return c['nat']
def run(repo='..', cards=None):
    if cards is None: cards, _, _ = load(repo)
    seen = collections.defaultdict(list)
    for c in cards: seen[(key_nat(c), ';'.join(norm_full(c['fr'])))].append(c)
    dups = [v for v in seen.values() if len(v) > 1]
    bysense = collections.defaultdict(set)
    for c in cards:
        for s in norm_full(strip_note(c['fr'])): bysense[(key_nat(c), s)].add(c['i'])
    amb = []
    skip = ignored_keys()
    for c in cards:
        if '(' in c['fr'] or shown(c) in skip: continue
        senses = norm_full(c['fr'])
        if not senses: continue
        others = None
        for s in senses:
            o = bysense[(key_nat(c), s)] - {c['i']}
            others = o if others is None else others & o
        if others: amb.append((c, sorted(others)))
    return dups, amb
if __name__ == '__main__':
    dups, amb = run()
    print(f'{len(dups)} groupes de traductions identiques ; {len(amb)} cartes ambiguës')
    for v in dups: print('  dup:', ' / '.join(f"{shown(c)} = {c['fr']}" for c in v))
    by = {c['i']: c for c in load('..')[0]}
    for c, o in amb[:40]: print('  amb:', f"{shown(c)} = {c['fr']}  ~ ", ', '.join(shown(by[i]) + ' = ' + by[i]['fr'] for i in o[:3]))
