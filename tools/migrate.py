"""Conversion unique : fichiers publiés lists/chunks/examples-<L>-<U>.json -> format source data/.

Usage : python3 tools/migrate.py de fr
Ne pas relancer une fois le format source édité à la main : il serait écrasé.
"""
import json, os, sys
from mxdata import ROOT, DATA, NONE, card_key, app_key, split_senses, join_senses, write_tsv


def migrate(L, U):
    load = lambda k: json.load(open(os.path.join(ROOT, f'{k}-{L}-{U}.json'), encoding='utf-8'))
    lists, chunks, examples = load('lists'), load('chunks'), load('examples')

    lex, senses, glosses, cards, ch_src, ch_tr, ex_src, ex_tr = [], [], [], [], [], [], [], []
    seen = set()
    for row in lists:
        lvl, w, pos, art, pl, fr = row[:6]
        extra = row[6] if len(row) > 6 else NONE   # italien : genre (m/f) quand l'article est élidé
        key = card_key(art, w)
        if key in seen:
            raise SystemExit(f'clé en double : {key}')
        seen.add(key)
        lex.append([key, lvl, pos, art, w, pl, extra])

        parts = split_senses(fr)
        for n, g in enumerate(parts, 1):
            sid = f'{key}#{n}'
            senses.append([sid, key])
            glosses.append([sid, g])
        if join_senses(parts) != fr:          # séparateur particulier (« ; ») : on garde la carte telle quelle
            cards.append([key, fr])

    # chunks et phrases : repris dans l'ordre des fichiers publiés (pour les reproduire à l'identique)
    by_app = {app_key(r[3], r[4]): r[0] for r in lex}
    if len(by_app) != len(lex):
        raise SystemExit('deux mots ont la même clé d\'appli (minuscules)')
    lost = [k for k in list(chunks) + list(examples) if k not in by_app]
    if lost:
        raise SystemExit(f'{len(lost)} entrées sans carte, ex. {lost[:5]}')
    for ak, (c_src, c_tr) in chunks.items():
        ch_src.append([by_app[ak], c_src])
        ch_tr.append([by_app[ak], c_tr])
    for ak, exs in examples.items():
        key = by_app[ak]
        for i, e in enumerate(exs, 1):
            sid = f'{key}@{i}'
            sent, tr, hl = e[0], e[1], e[2]
            label = e[3] if len(e) > 3 else NONE
            origin = e[4] if len(e) > 4 else 'tatoeba'
            ex_src.append([sid, key, sent, json.dumps(hl, separators=(',', ':')), origin])
            ex_tr.append([sid, tr, label])

    d, p = os.path.join(DATA, L), os.path.join(DATA, f'{L}-{U}')
    write_tsv(f'{d}/lexemes.tsv', ['key', 'level', 'pos', 'art', 'lemma', 'plural', 'extra'], lex)
    write_tsv(f'{d}/senses.tsv', ['sense', 'key'], senses)
    write_tsv(f'{d}/chunks.tsv', ['key', 'chunk'], ch_src)
    write_tsv(f'{d}/examples.tsv', ['id', 'key', 'sentence', 'highlight', 'origin'], ex_src)
    write_tsv(f'{p}/glosses.tsv', ['sense', 'gloss'], glosses)
    write_tsv(f'{p}/cards.tsv', ['key', 'translation'], cards)
    write_tsv(f'{p}/chunks.tsv', ['key', 'translation'], ch_tr)
    write_tsv(f'{p}/examples.tsv', ['id', 'translation', 'sense_label'], ex_tr)
    print(f'{L}-{U} : {len(lex)} mots, {len(senses)} sens, {len(cards)} cartes à traduction libre, '
          f'{len(ch_src)} chunks, {len(ex_src)} phrases')


if __name__ == '__main__':
    migrate(sys.argv[1], sys.argv[2])
