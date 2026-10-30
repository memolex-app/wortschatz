"""Contrôle 1 : la phrase d'exemple doit illustrer la bonne NATURE du mot (nom pour un nom, verbe pour un verbe…).
Corrige le défaut « trapianto » (nom) illustré par « Non li trapianto » (verbe), « scheda » par « Io non le schedo ».
Deux signaux indépendants (un seul suffit à signaler) :
  1. côté italien : la forme surlignée a la nature de la carte (spaCy it_core_news_lg) ; pour un nom, on signale aussi
     un « nom » précédé directement d'un pronom clitique (« li trapianto », « le schedo ») qui est en réalité un verbe ;
  2. côté français : le mot de la traduction de la carte, retrouvé dans la phrase française, a la même nature
     (« Je ne les greffe pas » : greffe = verbe, alors que la carte est un nom).
Usage : python3 ex_pos.py [--json sortie.json]
"""
import sys, json, re, spacy
from common import load, shown, fr_senses, ignored
OK_IT = {'n': {'NOUN', 'PROPN'}, 'v': {'VERB', 'AUX'}, 'adj': {'ADJ', 'VERB', 'NOUN', 'DET', 'NUM'}, 'adv': {'ADV', 'ADJ'},
         'prep': {'ADP', 'ADV'}, 'conj': {'CCONJ', 'SCONJ', 'ADV'}, 'pron': {'PRON', 'DET'}, 'num': {'NUM', 'NOUN', 'ADJ', 'DET'},
         'int': {'INTJ', 'ADV', 'NOUN', 'PROPN', 'ADJ'}, 'adj,adv': {'ADJ', 'ADV', 'DET'}, 'adj,prep': {'ADJ', 'ADP'}}
OK_FR = {'n': {'NOUN', 'PROPN', 'ADJ', 'NUM', 'X'}, 'v': {'VERB', 'AUX'}, 'adj': {'ADJ', 'VERB', 'NOUN', 'ADV', 'NUM'},
         'adv': {'ADV', 'ADJ'}}
CLITIC = {'mi', 'ti', 'ci', 'vi', 'li', 'ne', 'si', 'glielo', 'gliela'}   # jamais des articles
def run(repo='..'):
    nlp = spacy.load('it_core_news_lg', disable=['ner'])
    nfr = spacy.load('fr_core_news_md', disable=['ner'])
    cards, ex, _ = load(repo)
    items = [(c, k, e) for c in cards for k, e in enumerate(ex.get(c['key'], []))]
    d_it = list(nlp.pipe([e[0] for _, _, e in items], batch_size=64))
    d_fr = list(nfr.pipe([e[1] for _, _, e in items], batch_size=64))
    bad = []
    for (c, k, e), di, df in zip(items, d_it, d_fr):
        why = []
        toks = []
        for st, ln in e[2]:
            toks += [t for t in di if t.idx < st + ln and t.idx + len(t.text) > st]
        tags = [t.pos_ for t in toks]
        if tags and not (set(tags) & OK_IT.get(c['nat'], set())):
            why.append('IT:' + '/'.join(tags))
        if c['nat'] == 'n' and toks:
            t = toks[0]
            if t.i > 0 and di[t.i - 1].lower_ in CLITIC and di[t.i - 1].pos_ == 'PRON':
                why.append('IT:précédé du clitique « ' + di[t.i - 1].text + ' »')
        # phrase sans aucun verbe alors qu'elle contient un pronom sujet : le « nom » est probablement un verbe (« Io non le schedo »)
        if c['nat'] == 'n' and toks and not any(t.pos_ in ('VERB', 'AUX') for t in di) \
                and any(t.lower_ in ('io', 'tu', 'lui', 'lei', 'noi', 'voi', 'loro') for t in di):
            why.append('IT:phrase sans verbe')
        okfr = OK_FR.get(c['nat'])
        if okfr:
            sense = e[3] if len(e) > 3 and e[3] else None
            glosses = [sense] if sense else fr_senses(c['fr'])
            words = set()
            for g in glosses:
                for tk in nfr(g):
                    if tk.is_alpha: words.add(tk.lemma_.lower()); words.add(tk.text.lower())
            m = [t for t in df if t.lower_ in words or t.lemma_.lower() in words]
            if m and not any(t.pos_ in okfr for t in m):
                why.append('FR:' + '/'.join(sorted({t.pos_ for t in m})))
        if why and not ignored('ex_pos', c['w'], e[0]):
            bad.append(dict(i=c['i'], lv=c['lv'], card=shown(c), nat=c['nat'], fr=c['fr'], k=k, it=e[0], fr_s=e[1], why=why))
    return bad, len(items)
if __name__ == '__main__':
    bad, n = run()
    print(f'{len(bad)} exemples douteux sur {n}')
    for b in bad: print(f"{b['i']}|{b['lv']}|{b['card']} ({b['nat']}) = {b['fr']}|{';'.join(b['why'])}|{b['it']} || {b['fr_s']}")
    if '--json' in sys.argv: json.dump(bad, open(sys.argv[sys.argv.index('--json') + 1], 'w'), ensure_ascii=False, indent=1)
