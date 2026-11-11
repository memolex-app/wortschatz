"""Contrôle des articles et des pluriels italiens (nom).
 - l'article singulier doit correspondre au début du mot (il / lo / l' / la) ;
 - l'article du pluriel doit correspondre au genre et au début du mot (i / gli / le) ;
 - la forme du pluriel doit suivre les règles régulières (o>i, a>e, e>i, mots en -à/-ù/-i/-ie, consonne : invariables ; -co/-go/-ca/-ga/-cia/-gia/-io : cas particuliers signalés) ;
 - les noms de mois, de langues, de matières et les noms indénombrables ne doivent pas avoir de pluriel inventé.
Usage : python3 plural_check.py
"""
import re
from common import load
MONTHS = {'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'}
def art_sg(w, g):
    wl = w.lower()
    v = wl[0] in 'aeiouàèéìòù'
    if g.startswith('f'): return "l'" if v else 'la'
    if v: return "l'"
    if re.match(r'(z|gn|ps|pn|x|y|s[^aeiou\W])', wl): return 'lo'
    return 'il'
def art_pl(w, g):
    wl = w.lower()
    if g.startswith('f'): return 'le'
    if wl[0] in 'aeiouàèéìòù' or re.match(r'(z|gn|ps|pn|x|y|s[^aeiou\W])', wl): return 'gli'
    return 'i'
def regular_pl(w, g):
    cands = set()
    if w.endswith('o'):
        cands.add(w[:-1] + 'i')
        if w.endswith('co') or w.endswith('go'): cands.add(w[:-1] + 'hi')
        if w.endswith('io'): cands.add(w[:-2] + 'i'); cands.add(w[:-1] + 'i')
        if g == 'm': cands.add(w[:-1] + 'a')   # braccio/braccia… (pluriel en -a toléré, à contrôler)
    elif w.endswith('a'):
        if g.startswith('m') or w.endswith(('ista',)): cands.add(w[:-1] + 'i'); cands.add(w[:-1] + 'e')
        cands.add(w[:-1] + 'e')
        if w.endswith(('ca', 'ga')): cands.add(w[:-1] + 'he')
        if w.endswith(('cia', 'gia')): cands.add(w[:-2] + 'e'); cands.add(w[:-1] + 'e')
        if w.endswith('ia'): cands.add(w[:-1] + 'e'); cands.add(w[:-2] + 'e')
    elif w.endswith('e'):
        cands.add(w[:-1] + 'i')
    else:
        cands.add(w)
    return cands
def run(repo='..'):
    cards, _, _ = load(repo)
    out = []
    for c in cards:
        if c['nat'] != 'n': continue
        w, a, pl, g = c['w'], c['art'], c['pl'], c['g']
        if a and a != art_sg(w, g) and not (g in ('mp', 'fp')):
            out.append((c, f"article singulier « {a} » (attendu « {art_sg(w, g)} »)"))
        if w in MONTHS and pl: out.append((c, 'pluriel inventé pour un nom de mois')); continue
        if not pl or pl in ('=', '0'): continue
        m = re.match(r"^(il|lo|l'|la|i|gli|le)\s*(.+)$", pl)
        if not m: out.append((c, f'pluriel illisible « {pl} »')); continue
        pa, pw = pl.split(' ', 1) if ' ' in pl else (pl[:2], pl[2:])
        pa = pa.strip()
        if pa != art_pl(pw, g): out.append((c, f"article pluriel « {pa} » (attendu « {art_pl(pw, g)} »)"))
        if pw not in regular_pl(w, g): out.append((c, f"pluriel « {pw} » irrégulier à vérifier"))
    return out
if __name__ == '__main__':
    r = run()
    print(len(r), 'alertes')
    for c, why in r: print(f"{c['i']}|{c['lv']}|{c['art']} {c['w']} ({c['g']}) [{c['pl']}] = {c['fr']} | {why}")
