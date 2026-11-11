"""Contrôle 4 : registre. Une traduction française familière, vulgaire ou argotique doit porter son étiquette
(« (familier) », « (vulgaire) », …) ; sinon l'apprenant croit apprendre un mot courant (« picchiare = tabasser »).
Catalogue de départ de mots familiers français, à enrichir à chaque erreur trouvée par un relecteur.
Usage : python3 register.py
"""
import re
import os
from common import load, shown, fr_senses, PAIR
# exceptions vérifiées (une clé de carte par ligne, # = commentaire) : ignore_register_<paire>.txt
_IG = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'ignore_register_{PAIR}.txt')
IGNORE = {l.split('#')[0].strip() for l in open(_IG, encoding='utf-8')} - {''} if os.path.exists(_IG) else set()
FAMILIERS = set("""tabasser caser costaud bouffer bouffe boulot fric flic gosse mec nana bagnole chiper fiche-moi foutre foutu
bosser bidule machin truc zigouiller trimer pote fringues frusques godasses clope baratin pépère flinguer piger déglinguer
clébard bécane fauché pognon oseille thune moche chouette chiant emmerder emmerdant merde putain pisser clamser canasson
gonzesse rigoler marrant vachement""".split())
MARK = re.compile(r'\((?:[^)]*\b)?(familier|vulgaire|argot|populaire|trivial|fam\.)\b', re.I)
def run(repo='..'):
    cards, _, _ = load(repo)
    out = []
    for c in cards:
        if MARK.search(c['fr']) or shown(c) in IGNORE: continue
        for g in fr_senses(c['fr']):
            if set(re.findall(r"[\wéèêàâîïôûç-]+", g.lower())) & FAMILIERS:
                out.append((c, g)); break
    return out
if __name__ == '__main__':
    r = run()
    print(f'{len(r)} cartes avec un mot familier sans étiquette de registre')
    for c, g in r: print(f"{c['i']}|{c['lv']}|{shown(c)} = {c['fr']}  [{g}]")
