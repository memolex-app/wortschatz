"""Génère les fichiers lus par l'appli à partir du format source data/.

Usage :
  python3 tools/build.py de fr            -> lists-, chunks-, examples-, credits-de-fr.json
  python3 tools/build.py de fr --check    -> compare au fichier publié sans rien écrire (0 différence attendue)
"""
import json, os, sys, hashlib
from mxdata import ROOT, DATA, NONE, app_key, join_senses, read_tsv, dump


def build(L, U):
    d, p = os.path.join(DATA, L), os.path.join(DATA, f'{L}-{U}')
    lex = read_tsv(f'{d}/lexemes.tsv')
    senses = read_tsv(f'{d}/senses.tsv')
    gl = {r['sense']: r['gloss'] for r in read_tsv(f'{p}/glosses.tsv')}
    free = {r['key']: r['translation'] for r in read_tsv(f'{p}/cards.tsv')}

    by_key = {}
    for s in senses:
        by_key.setdefault(s['key'], []).append(s['sense'])
    missing = [s['sense'] for s in senses if s['sense'] not in gl]
    if missing:
        raise SystemExit(f'{L}-{U} : {len(missing)} sens sans traduction, ex. {missing[:5]}')

    lists, app = [], {}
    for r in lex:
        k = r['key']
        fr = free.get(k) or join_senses([gl[s] for s in by_key.get(k, [])])
        row = [r['level'], r['lemma'], r['pos'], r['art'], r['plural'], fr]
        if r['extra'] != NONE:
            row.append(r['extra'])
        lists.append(row)
        app[k] = app_key(r['art'], r['lemma'])

    ch_tr = {r['key']: r['translation'] for r in read_tsv(f'{p}/chunks.tsv')}
    chunks = {}
    for r in read_tsv(f'{d}/chunks.tsv'):
        if r['key'] in ch_tr:                       # chunk sans traduction dans cette paire : non publié
            chunks[app[r['key']]] = [r['chunk'], ch_tr[r['key']]]

    ex_tr = {r['id']: r for r in read_tsv(f'{p}/examples.tsv')}
    examples = {}
    for r in read_tsv(f'{d}/examples.tsv'):
        t = ex_tr.get(r['id'])
        if not t:                                   # phrase non traduite dans cette paire : non publiée
            continue
        e = [r['sentence'], t['translation'], json.loads(r['highlight'])]
        if t['sense_label'] != NONE or r['origin'] == 'mx':
            e.append('' if t['sense_label'] == NONE else t['sense_label'])
        if r['origin'] == 'mx':
            e.append('mx')
        examples.setdefault(app[r['key']], []).append(e)

    # crédits Tatoeba (CC BY 2.0 FR) : une ligne par paire phrase / traduction publiée, triée par numéro de phrase
    tr_by_id = ex_tr
    pairs = set()
    for r in read_tsv(f'{d}/examples.tsv'):
        t = tr_by_id.get(r['id'])
        if t and r['origin'] != 'mx' and r.get('tatoeba') and t.get('tatoeba'):
            pairs.add((int(r['tatoeba']), r.get('author', ''), int(t['tatoeba']), t.get('author', '')))
    users, idx, c = [], {}, []
    for li, la, ui, ua in sorted(pairs):
        for a in (la, ua):
            if a not in idx:
                idx[a] = len(users); users.append(a)
        c.append([li, idx[la], ui, idx[ua]])
    credits = {'u': users, 'c': c}

    out = {'lists': lists, 'chunks': chunks, 'examples': examples}
    if c:                                           # paire sans numéros Tatoeba : crédits publiés laissés tels quels
        out['credits'] = credits
    return out


def main():
    L, U = sys.argv[1], sys.argv[2]
    check = '--check' in sys.argv
    ok = True
    for name, obj in build(L, U).items():
        path = os.path.join(ROOT, f'{name}-{L}-{U}.json')
        new = dump(obj).encode('utf-8')
        if check:
            old = open(path, 'rb').read()
            same = old == new
            ok &= same
            print(f'{name}-{L}-{U}.json : {"identique" if same else "DIFFÉRENT"}  '
                  f'sha256 {hashlib.sha256(new).hexdigest()[:16]}…')
        else:
            open(path, 'wb').write(new)
            print(f'{name}-{L}-{U}.json écrit')
    if check and not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
