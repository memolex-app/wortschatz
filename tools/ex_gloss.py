"""Contrôle 2 (ex-« ex_audit ») : la traduction française de la phrase d'exemple doit contenir un des sens de la carte
(ou, pour une carte à plusieurs sens, le sens affiché au-dessus de la phrase). Sinon la phrase illustre peut-être un autre mot
ou un autre sens. Un mot du sens est retrouvé s'il apparaît tel quel, par sa racine (Snowball) ou par son lemme (spaCy fr).
Limite : ne détecte pas un autre sens exprimé par le même mot français (« bouton » vêtement / appareil).
Usage : python3 ex_gloss.py [--json sortie.json]
"""
import sys, json, re, spacy, snowballstemmer
from common import load, shown, fr_senses, ignored
ST = snowballstemmer.stemmer('french')
STOP = {'de', 'du', 'des', 'd', 'à', 'au', 'aux', 'en', 'se', 's', 'ne', 'pas', 'qn', 'qch', 'un', 'une', 'le', 'la', 'les', 'l', 'ce', 'cette', 'ces', 'y', 'n'}
def words(s):
    return [w for w in re.findall(r"[\wœ]+", s.lower().replace('’', "'")) if w not in STOP]
def run(repo='..'):
    nfr = spacy.load('fr_core_news_md', disable=['ner', 'parser'])
    cards, ex, _ = load(repo)
    items = [(c, k, e) for c in cards if c['nat'] in ('n', 'v', 'adj', 'adv') for k, e in enumerate(ex.get(c['key'], []))]
    docs = list(nfr.pipe([e[1] for _, _, e in items], batch_size=64))
    lem_cache = {}
    def glemmas(w):
        if w not in lem_cache: lem_cache[w] = {t.lemma_.lower() for t in nfr(w)} | {w}
        return lem_cache[w]
    bad = []
    for (c, k, e), d in zip(items, docs):
        sense = e[3] if len(e) > 3 and e[3] else None
        glosses = fr_senses(sense) if sense else fr_senses(c['fr'])
        if not glosses: continue
        forms = {t.lower_ for t in d} | {t.lemma_.lower() for t in d} | {ST.stemWord(w) for w in words(e[1])}
        forms |= {w for w in words(e[1])}
        def found(w):
            return w in forms or ST.stemWord(w) in forms or bool(glemmas(w) & forms)
        ok = any(words(g) and all(found(w) for w in words(g)) for g in glosses)
        if not ok and not ignored('ex_gloss', c['w'], e[0]):
            bad.append(dict(i=c['i'], lv=c['lv'], card=shown(c), nat=c['nat'], fr=c['fr'], k=k, it=e[0], fr_s=e[1], sense=sense))
    return bad, len(items)
if __name__ == '__main__':
    bad, n = run()
    print(f'{len(bad)} exemples dont la traduction ne contient aucun sens de la carte, sur {n}')
    for b in bad: print(f"{b['i']}|{b['lv']}|{b['card']} ({b['nat']}) = {b['fr']}|{b['sense'] or ''}|{b['it']} || {b['fr_s']}")
    if '--json' in sys.argv: json.dump(bad, open(sys.argv[sys.argv.index('--json') + 1], 'w'), ensure_ascii=False, indent=1)
