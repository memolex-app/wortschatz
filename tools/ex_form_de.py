"""Contrôle (allemand) : la forme surlignée dans la phrase d'exemple est-elle bien le mot de la carte ?
Attrape les phrases qui illustrent un autre mot de même apparence (der Teil ← « Teilen macht Freude », verbe ;
der Laut ← « Tom spielt Laute », die Laute = le luth).
Trois signaux (spaCy de_core_news_md), un seul suffit :
  MAJ   un nom doit commencer par une majuscule ; un verbe, adjectif ou adverbe surligné avec majuscule
        hors début de phrase est un nom (nominalisation ou autre mot) ;
  NAT   la nature donnée par spaCy n'est pas compatible avec celle de la carte ;
  LEM   le lemme donné par spaCy ne correspond pas au mot de la carte (ni à une de ses formes connues).
Usage : MX_PAIR=de-fr python3 ex_form_de.py
"""
import re, sys, json, spacy
from common import load, shown, ignored

OK = {'n': {'NOUN', 'PROPN'}, 'v': {'VERB', 'AUX'}, 'adj': {'ADJ', 'ADV', 'VERB'}, 'adv': {'ADV', 'ADJ', 'PRON'},
      'adj,adv': {'ADJ', 'ADV'}, 'prep': {'ADP', 'ADV'}, 'postp': {'ADP'}, 'pron': {'PRON', 'DET'},
      'num': {'NUM', 'NOUN', 'ADJ', 'DET'}, 'conj': {'CCONJ', 'SCONJ', 'ADV'}, 'int': {'INTJ', 'ADV', 'NOUN', 'PROPN', 'X'},
      'parti': {'PART', 'ADV'}}


def low(s):
    return s.lower().replace('ß', 'ss')


def run():
    nlp = spacy.load('de_core_news_md', disable=['ner', 'parser'])
    cards, ex, _ = load()
    items = [(c, e) for c in cards for e in ex.get(c['key'], [])]
    docs = list(nlp.pipe([e[0] for _, e in items], batch_size=64))
    bad = []
    for (c, e), d in zip(items, docs):
        why = []
        toks = []
        for st, ln in e[2]:
            toks += [t for t in d if t.idx < st + ln and t.idx + len(t.text) > st]
        if not toks:
            continue
        head = toks[0]
        txt = e[0][e[2][0][0]:e[2][0][0] + e[2][0][1]]
        prev = [t for t in d[:head.i] if not t.is_punct or t.text in '.!?']
        first = not prev or prev[-1].text in ('.', '!', '?')   # début de phrase, même après une autre phrase
        if c['nat'] == 'n' and txt[:1].islower():
            why.append('MAJ:minuscule')
        if c['nat'] in ('v', 'adj', 'adv', 'adj,adv') and txt[:1].isupper() and not first:
            why.append('MAJ:majuscule')
        tags = {t.pos_ for t in toks}
        if c['nat'] in OK and not tags & OK[c['nat']]:
            why.append('NAT:' + '/'.join(sorted(tags)))
        w = low(c['w'])
        lem = {low(t.lemma_) for t in toks} | {low(t.text) for t in toks}
        joined = ''.join(low(t.text) for t in reversed(toks))   # verbe à particule séparée : stehe … auf → aufstehe
        stem = w[:max(3, len(w) - 3)]
        if not (w in lem or any(l.startswith(stem) or w.startswith(l[:max(3, len(l) - 2)]) and len(l) > 3 for l in lem)
                or joined.startswith(stem) or stem in joined):
            why.append('LEM:' + '/'.join(sorted({t.lemma_ for t in toks})))
        if why and not ignored('ex_form_de', c['w'], e[0]):
            bad.append(dict(i=c['i'], lv=c['lv'], card=shown(c), nat=c['nat'], fr=c['fr'], de=e[0], fr_s=e[1], form=txt, why=why))
    return bad, len(items)


if __name__ == '__main__':
    bad, n = run()
    print(f'{len(bad)} phrases dont la forme surlignée n\'est peut-être pas le mot de la carte, sur {n}')
    for b in bad:
        print(f"{b['i']}|{b['lv']}|{b['card']} ({b['nat']}) = {b['fr']}|{';'.join(b['why'])}|[{b['form']}] {b['de']} || {b['fr_s']}")
    if '--json' in sys.argv:
        json.dump(bad, open(sys.argv[sys.argv.index('--json') + 1], 'w'), ensure_ascii=False, indent=1)
