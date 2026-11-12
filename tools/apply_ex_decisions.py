"""Retire des phrases d'exemple du format source data/ (décision sur la langue apprise : vaut pour toutes les paires).

Fichier : data/<L>/decisions/AAAA-MM-JJ-<nom>.tsv, colonnes : key · sentence · reason · new_sentence
  key           clé de la carte (« der Laut »)
  sentence      la phrase dans la langue apprise, exactement (« Tom spielt Laute. »)
  reason        motif : autre mot, autre nature, phrase fautive, traduction fausse…
  new_sentence  vide : la phrase est retirée ; sinon : la phrase est corrigée (orthographe), le surlignage recalculé
Une phrase retirée disparaît de data/<L>/examples.tsv et de toutes les traductions data/<L>-*/examples.tsv.
Réappliquer un fichier déjà appliqué est sans effet.

Usage : python3 tools/apply_ex_decisions.py de data/de/decisions/2026-11-12-phrases.tsv [--dry]
"""
import glob, json, os, sys
from mxdata import DATA, read_tsv, write_tsv


def rehighlight(old, new, hl):
    """Recalcule les positions surlignées après correction : même texte surligné, cherché dans l'ordre."""
    out, pos = [], 0
    for st, ln in hl:
        frag = old[st:st + ln]
        i = new.find(frag, pos)
        if i < 0:
            raise SystemExit(f'forme surlignée « {frag} » absente de la phrase corrigée : {new!r}')
        out.append([i, ln])
        pos = i + ln
    return out


def apply(L, path, dry=False):
    d = os.path.join(DATA, L)
    src = read_tsv(f'{d}/examples.tsv')
    dec = read_tsv(path)
    # une correction d'orthographe vaut pour la phrase sous toutes les cartes qui l'utilisent
    fix = {r['sentence']: r['new_sentence'] for r in dec if r.get('new_sentence')}
    for e in src:
        if e['sentence'] in fix:
            old = e['sentence']
            hl = rehighlight(old, fix[old], json.loads(e['highlight']))
            e['sentence'], e['highlight'] = fix[old], json.dumps(hl, separators=(',', ':'))
            print(f"corrigée ({e['key']}) : {old}  →  {e['sentence']}")
    want = {(r['key'], r['sentence']) for r in dec if not r.get('new_sentence')}
    drop = {e['id'] for e in src if (e['key'], e['sentence']) in want}
    found = {(e['key'], e['sentence']) for e in src if e['id'] in drop}
    already = want - found
    keep = [e for e in src if e['id'] not in drop]
    if not dry:
        write_tsv(f'{d}/examples.tsv', ['id', 'key', 'sentence', 'highlight', 'origin'],
                  [[e['id'], e['key'], e['sentence'], e['highlight'], e['origin']] for e in keep])
        for p in glob.glob(os.path.join(DATA, f'{L}-*', 'examples.tsv')):
            tr = [t for t in read_tsv(p) if t['id'] not in drop]
            write_tsv(p, ['id', 'translation', 'sense_label'], [[t['id'], t['translation'], t['sense_label']] for t in tr])
    print(f'{len(drop)} phrases retirées, {len(already)} déjà absentes' + (' (essai, rien écrit)' if dry else ''))
    left = {e['key'] for e in keep}
    gone = sorted({k for k, _ in found} - left)
    if gone:
        print(f'{len(gone)} cartes n\'ont plus de phrase :', ', '.join(gone))


if __name__ == '__main__':
    apply(sys.argv[1], sys.argv[2], '--dry' in sys.argv)
