"""Applique un fichier de corrections (corrections_*.json) aux JSON publiés italien-français.
Usage : python3 apply_corrections.py corrections_2026-10-30.json [--dry]
"""
import json, sys, os
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def jl(n): return json.load(open(os.path.join(REPO, n), encoding='utf-8'))
def jd(o, n):
    with open(os.path.join(REPO, n), 'w', encoding='utf-8') as f: json.dump(o, f, ensure_ascii=False, separators=(',', ':'))
def main(path, dry=False):
    R = json.load(open(path, encoding='utf-8'))
    L, D, C, X = jl('lists-it-fr.json'), jl('dict-it-fr.json'), jl('chunks-it-fr.json'), jl('examples-it-fr.json')
    log = []
    for f in R['fr']:
        n = 0
        for r in L:
            if r[1] == f['w'] and r[2] == f['nat']: log.append(f"fr  {r[1]} : {r[5]}  ->  {f['new']}"); r[5] = f['new']; n += 1
        for d in D:
            if d[0] == f['w'] and d[1] == f['nat']: d[4] = [[f['new'], '']]; n += 1
        if 'chunk_fr' in f and f['w'] in C: C[f['w']][1] = f['chunk_fr']
        if n != 2: raise SystemExit(f"{f['w']}: {n} correspondances au lieu de 2")
    for bp in R.get('blank_plural', []):
        n = 0
        for r in L:
            if r[1] == bp['w'] and r[2] == bp['nat'] and r[4]: r[4] = ''; n += 1
        for d in D:
            if d[0] == bp['w'] and d[1] == bp['nat'] and d[3]: d[3] = ''; n += 1
        if n != 2: raise SystemExit(f"plural {bp['w']}: {n} correspondances au lieu de 2")
        log.append(f"pluriel vidé : {bp['w']}")
    for rc in R.get('remove_cards', []):
        keys = [(r[3] + r[1]) if r[3] else r[1] for r in L if r[1] == rc['w'] and r[2] == rc['nat']]
        L2 = [r for r in L if not (r[1] == rc['w'] and r[2] == rc['nat'])]
        D2 = [d for d in D if not (d[0] == rc['w'] and d[1] == rc['nat'])]
        if len(L2) != len(L) - 1 or len(D2) != len(D) - 1: raise SystemExit('retrait inattendu ' + rc['w'])
        L, D = L2, D2
        for k in keys: C.pop(k, None)
        log.append(f"carte retirée : {rc['w']} ({rc['nat']})")
    for re_ in R.get('remove_examples', []):
        lst = X.get(re_['key'])
        if lst is None: raise SystemExit('clé absente ' + re_['key'])
        keep = [e for e in lst if 'match' in re_ and re_['match'] not in e[0]] if 'match' in re_ else []
        log.append(f"exemple retiré : {re_['key']} ({len(lst) - len(keep)})")
        if keep: X[re_['key']] = keep
        else: del X[re_['key']]
    print('\n'.join(log))
    if not dry:
        jd(L, 'lists-it-fr.json'); jd(D, 'dict-it-fr.json'); jd(C, 'chunks-it-fr.json'); jd(X, 'examples-it-fr.json')
if __name__ == '__main__':
    main(sys.argv[1], '--dry' in sys.argv)
