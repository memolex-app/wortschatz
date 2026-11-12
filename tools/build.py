"""Génère les fichiers lus par l'appli à partir du format source data/.

Usage :
  python3 tools/build.py de fr            -> lists-, chunks-, examples-, credits-de-fr.json
  python3 tools/build.py de fr --check    -> compare au fichier publié sans rien écrire (0 différence attendue)
"""
import json, os, sys, hashlib
from mxdata import ROOT, DATA, NONE, app_key, join_senses, read_tsv, dump


INFO = {}   # paire en essai : nombre de cartes traduites, affiché par main()


def pair_status(L, U):
    """Statut de la paire : « essai » (cachée dans l'appli sauf adresse spéciale) ou None (publiée)."""
    f = os.path.join(DATA, f'{L}-{U}', 'pair.json')
    return json.load(open(f, encoding='utf-8')).get('status') if os.path.exists(f) else None


def build(L, U):
    d, p = os.path.join(DATA, L), os.path.join(DATA, f'{L}-{U}')
    lex = read_tsv(f'{d}/lexemes.tsv')
    senses = read_tsv(f'{d}/senses.tsv')
    # un sens peut avoir plusieurs traductions (synonymes : « sûr », « certain ») : lignes successives du même sens
    gl = {}
    for r in read_tsv(f'{p}/glosses.tsv'):
        gl.setdefault(r['sense'], []).append(r['gloss'])
    free = {r['key']: r['translation'] for r in read_tsv(f'{p}/cards.tsv')}

    by_key = {}
    for s in senses:
        by_key.setdefault(s['key'], []).append(s['sense'])
    # paire en essai (data/<L>-<U>/pair.json : {"status": "essai"}) : traduite par lots, seules les cartes dont tous
    # les sens sont traduits sont publiées ; une paire publiée doit être complète
    status = pair_status(L, U)
    missing = [s['sense'] for s in senses if s['sense'] not in gl and s['key'] not in free]
    if missing and status != 'essai':
        raise SystemExit(f'{L}-{U} : {len(missing)} sens sans traduction, ex. {missing[:5]}')
    done = {r['key'] for r in lex if r['key'] in free or (by_key.get(r['key']) and all(s in gl for s in by_key[r['key']]))}
    INFO[f'{L}-{U}'] = f'{L}-{U} (essai) : {len(done)} cartes traduites sur {len(lex)}' if missing else ''

    lists, app = [], {}
    for r in lex:
        k = r['key']
        app[k] = app_key(r['art'], r['lemma'])
        if k not in done:
            continue
        fr = free.get(k) or join_senses([g for s in by_key.get(k, []) for g in gl[s]])
        row = [r['level'], r['lemma'], r['pos'], r['art'], r['plural'], fr]
        if r['extra'] != NONE:
            row.append(r['extra'])
        lists.append(row)

    ch_tr = {r['key']: r['translation'] for r in read_tsv(f'{p}/chunks.tsv')}
    chunks = {}
    for r in read_tsv(f'{d}/chunks.tsv'):
        if r['key'] in ch_tr and r['key'] in done:                       # chunk sans traduction dans cette paire : non publié
            chunks[app[r['key']]] = [r['chunk'], ch_tr[r['key']]]

    ex_tr = {r['id']: r for r in read_tsv(f'{p}/examples.tsv')}
    examples = {}
    for r in read_tsv(f'{d}/examples.tsv'):
        t = ex_tr.get(r['id'])
        if not t or r['key'] not in done:           # phrase non traduite dans cette paire : non publiée
            continue
        e = [r['sentence'], t['translation'], json.loads(r['highlight'])]
        if t['sense_label'] != NONE or r['origin'] == 'mx':
            e.append('' if t['sense_label'] == NONE else t['sense_label'])
        if r['origin'] == 'mx':
            e.append('mx')
        examples.setdefault(app[r['key']], []).append(e)

    # crédits Tatoeba (CC BY 2.0 FR) : une ligne par paire phrase / traduction publiée, triée par numéro de phrase ;
    # phrase de Tatoeba traduite par Memolex : numéro 0, auteur « Memolex » (l'appli affiche « traduction Memolex »)
    tr_by_id = ex_tr
    pairs = set()
    for r in read_tsv(f'{d}/examples.tsv'):
        t = tr_by_id.get(r['id'])
        if not t or r['key'] not in done or r['origin'] == 'mx' or not r.get('tatoeba'):
            continue
        if t.get('tatoeba') and t['tatoeba'] != NONE:
            pairs.add((int(r['tatoeba']), r.get('author', ''), int(t['tatoeba']), t.get('author', '')))
        else:
            pairs.add((int(r['tatoeba']), r.get('author', ''), 0, 'Memolex'))
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
    out = build(L, U)
    if INFO.get(f'{L}-{U}'):
        print(INFO[f'{L}-{U}'])
    for name, obj in out.items():
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
