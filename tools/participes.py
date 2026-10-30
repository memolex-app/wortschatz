"""Contrôle 5 : lemmes douteux (formes fléchies prises pour des mots).
 (a) adjectif en -ato/-ito/-uto/-so/-to dont le verbe de base figure aussi dans les listes et dont la traduction française
     est le simple participe du verbe (« documentato » = « documenté », verbe « documentare » = « documenter ») :
     le participe n'a pas de sens propre -> candidat au retrait (règle de la procédure : « participes gardés seulement
     s'ils ont un vrai emploi d'adjectif avec un sens propre »).
Usage : python3 participes.py
"""
import re, snowballstemmer
from common import load, shown, fr_senses
ST = snowballstemmer.stemmer('french')
def base_candidates(w):
    for suf, reps in (('ato', ('are',)), ('ata', ('are',)), ('ito', ('ire', 'ere')), ('uto', ('ere',)), ('so', ('dere', 'ere')), ('sto', ('dere', 'ere')), ('to', ('re',))):
        if w.endswith(suf):
            for r in reps: yield w[:-len(suf)] + r
def run(repo='..'):
    cards, _, _ = load(repo)
    verbs = {c['w']: c for c in cards if c['nat'] == 'v'}
    out = []
    for c in cards:
        if not c['nat'].startswith('adj'): continue
        for b in base_candidates(c['w']):
            v = verbs.get(b)
            if not v: continue
            sa = [ST.stemWord(x) for x in re.findall(r"\w+", fr_senses(c['fr'])[0].lower())] if fr_senses(c['fr']) else []
            sv = [ST.stemWord(x) for x in re.findall(r"\w+", fr_senses(v['fr'])[0].lower())] if fr_senses(v['fr']) else []
            if sa and sv and sa[0][:4] == sv[0][:4]:
                out.append(('a', c, v)); break
    return out
if __name__ == '__main__':
    r = run()
    print(f'{len(r)} lemmes à examiner')
    for k, c, v in r:
        print(f"{k}|{c['i']}|{c['lv']}|{shown(c)} = {c['fr']}" + (f"  <- verbe {v['w']} = {v['fr']}" if v else '  <- participe probable'))
